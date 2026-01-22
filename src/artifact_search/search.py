"""Main search orchestrator that coordinates searches across all apps."""

import asyncio
import logging
import time

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI

from artifact_search.config import Settings, get_settings
from artifact_search.connectors import (
    AzureDevOpsConnector,
    FigmaConnector,
    IcePanelConnector,
    NotionConnector,
)
from artifact_search.connectors.base import BaseConnector
from artifact_search.models import AppSource, Artifact, RoutedQuery, SearchQuery, SearchResult
from artifact_search.router import route_query

logger = logging.getLogger(__name__)


class ArtifactSearchEngine:
    """Orchestrates searches across multiple applications."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._connectors: dict[AppSource, BaseConnector] = {}
        self._initialize_connectors()

    def _initialize_connectors(self) -> None:
        """Initialize all configured connectors."""
        connector_classes = {
            AppSource.AZURE_DEVOPS: AzureDevOpsConnector,
            AppSource.FIGMA: FigmaConnector,
            AppSource.NOTION: NotionConnector,
            AppSource.ICEPANEL: IcePanelConnector,
        }

        for source, connector_class in connector_classes.items():
            connector = connector_class(self._settings)
            if connector.is_configured():
                self._connectors[source] = connector
                logger.info(f"Initialized connector for {source.value}")
            else:
                logger.warning(f"Connector {source.value} not configured, skipping")

    async def search(self, query: str | SearchQuery) -> SearchResult:
        """Execute a search across configured applications."""
        start_time = time.time()

        # Normalize query
        if isinstance(query, str):
            search_query = SearchQuery(query=query)
        else:
            search_query = query

        # Route query to appropriate apps
        routed = await route_query(search_query, self._settings)
        logger.info(
            f"Routed query to apps: {[a.value for a in routed.target_apps]}, "
            f"types: {[t.value for t in routed.artifact_types]}"
        )

        # Filter to only configured connectors
        target_connectors = [
            self._connectors[app]
            for app in routed.target_apps
            if app in self._connectors
        ]

        if not target_connectors:
            logger.warning("No configured connectors match the routed apps")
            return SearchResult(
                query=search_query.query,
                artifacts=[],
                sources_searched=[],
                total_results=0,
                search_duration_ms=(time.time() - start_time) * 1000,
                summary="No configured data sources available for this query.",
            )

        # Execute searches in parallel
        search_tasks = [connector.search(routed) for connector in target_connectors]
        results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # Collect artifacts from successful searches
        all_artifacts: list[Artifact] = []
        sources_searched: list[AppSource] = []

        for connector, result in zip(target_connectors, results):
            if isinstance(result, Exception):
                logger.error(f"Search failed for {connector.source.value}: {result}")
            else:
                all_artifacts.extend(result)
                sources_searched.append(connector.source)

        # Sort by relevance (for now, just by updated_at)
        all_artifacts.sort(
            key=lambda a: a.updated_at or a.created_at or "",
            reverse=True,
        )

        # Generate summary using Azure AI
        summary = await self._generate_summary(search_query.query, all_artifacts)

        duration_ms = (time.time() - start_time) * 1000

        return SearchResult(
            query=search_query.query,
            artifacts=all_artifacts,
            sources_searched=sources_searched,
            total_results=len(all_artifacts),
            search_duration_ms=duration_ms,
            summary=summary,
        )

    async def _generate_summary(
        self, query: str, artifacts: list[Artifact]
    ) -> str | None:
        """Generate a summary of search results using Azure AI."""
        if not artifacts:
            return "No matching artifacts found."

        if not self._settings.is_azure_ai_configured():
            return f"Found {len(artifacts)} artifacts across multiple sources."

        try:
            # Use DefaultAzureCredential (az login) or API key
            if self._settings.azure_ai_use_ad_auth and not self._settings.azure_ai_api_key:
                token_provider = get_bearer_token_provider(
                    DefaultAzureCredential(),
                    "https://cognitiveservices.azure.com/.default"
                )
                client = AsyncAzureOpenAI(
                    azure_endpoint=self._settings.azure_ai_endpoint,
                    azure_ad_token_provider=token_provider,
                    api_version="2024-02-01",
                )
            else:
                client = AsyncAzureOpenAI(
                    azure_endpoint=self._settings.azure_ai_endpoint,
                    api_key=self._settings.azure_ai_api_key,
                    api_version="2024-02-01",
                )

            # Prepare artifact summaries for context
            artifact_summaries = []
            for artifact in artifacts[:10]:  # Limit to top 10
                artifact_summaries.append(
                    f"- [{artifact.source.value}] {artifact.title}: {artifact.content[:200]}..."
                )

            artifacts_text = "\n".join(artifact_summaries)

            response = await client.chat.completions.create(
                model=self._settings.azure_ai_deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant summarizing search results for MedTech risk management professionals. Provide a concise 2-3 sentence summary of what was found.",
                    },
                    {
                        "role": "user",
                        "content": f"Query: {query}\n\nResults found:\n{artifacts_text}\n\nProvide a brief summary of these results.",
                    },
                ],
                temperature=0.3,
                max_tokens=200,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return f"Found {len(artifacts)} artifacts across multiple sources."

    async def get_artifact(self, source: AppSource, artifact_id: str) -> Artifact | None:
        """Retrieve a specific artifact by source and ID."""
        if source not in self._connectors:
            logger.warning(f"Connector {source.value} not available")
            return None

        return await self._connectors[source].get_by_id(artifact_id)

    async def test_connections(self) -> dict[str, bool]:
        """Test connections to all configured apps."""
        results = {}
        for source, connector in self._connectors.items():
            try:
                results[source.value] = await connector.test_connection()
            except Exception as e:
                logger.error(f"Connection test failed for {source.value}: {e}")
                results[source.value] = False
        return results

    def get_configured_sources(self) -> list[AppSource]:
        """Get list of configured and available sources."""
        return list(self._connectors.keys())

    async def close(self) -> None:
        """Close all connector connections."""
        for connector in self._connectors.values():
            await connector.close()
