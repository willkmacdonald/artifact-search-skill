"""Figma connector for design artifacts with caching and retry logic."""

import asyncio
import logging
from datetime import datetime, timezone
from time import time

import httpx

from artifact_search.config import Settings
from artifact_search.connectors.base import BaseConnector
from artifact_search.models import AppSource, Artifact, ArtifactType, RoutedQuery

logger = logging.getLogger(__name__)

# Simple in-memory cache for file data
_file_cache: dict[str, tuple[float, dict]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes


class FigmaConnector(BaseConnector):
    """Connector for Figma design files with caching and retry."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: httpx.AsyncClient | None = None

    @property
    def source(self) -> AppSource:
        return AppSource.FIGMA

    def is_configured(self) -> bool:
        return self._settings.is_figma_configured()

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create authenticated HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url="https://api.figma.com/v1",
                headers={
                    "X-Figma-Token": self._settings.figma_access_token,
                },
                timeout=30.0,
            )
        return self._client

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        max_retries: int = 3,
        **kwargs,
    ) -> httpx.Response:
        """Make HTTP request with exponential backoff retry on rate limits."""
        client = await self._get_client()
        last_exception = None

        for attempt in range(max_retries):
            try:
                response = await client.request(method, url, **kwargs)

                # Success
                if response.status_code == 200:
                    return response

                # Rate limited - wait and retry
                if response.status_code == 429:
                    wait_time = 2 ** attempt  # 1, 2, 4 seconds
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        wait_time = max(wait_time, int(retry_after))
                    logger.warning(
                        f"Figma rate limited, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(wait_time)
                    continue

                # Server error - wait and retry
                if response.status_code >= 500:
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"Figma server error {response.status_code}, waiting {wait_time}s"
                    )
                    await asyncio.sleep(wait_time)
                    continue

                # Other error - don't retry
                response.raise_for_status()

            except httpx.TimeoutException as e:
                last_exception = e
                wait_time = 2 ** attempt
                logger.warning(f"Figma timeout, waiting {wait_time}s")
                await asyncio.sleep(wait_time)
                continue

        # All retries exhausted
        if last_exception:
            raise last_exception
        raise httpx.HTTPStatusError(
            f"Failed after {max_retries} retries",
            request=response.request,
            response=response,
        )

    async def _get_file_data(self, file_key: str) -> dict:
        """Get file data with caching."""
        now = time()

        # Check cache
        if file_key in _file_cache:
            cached_time, cached_data = _file_cache[file_key]
            if now - cached_time < CACHE_TTL_SECONDS:
                logger.debug(f"Using cached Figma file data for {file_key}")
                return cached_data

        # Fetch fresh data
        response = await self._request_with_retry("GET", f"/files/{file_key}")
        file_data = response.json()

        # Update cache
        _file_cache[file_key] = (now, file_data)
        logger.debug(f"Cached Figma file data for {file_key}")

        return file_data

    async def test_connection(self) -> bool:
        """Test connection to Figma."""
        if not self.is_configured():
            return False
        try:
            client = await self._get_client()
            response = await client.get("/me")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Figma connection test failed: {e}")
            return False

    async def search(self, query: RoutedQuery) -> list[Artifact]:
        """Search Figma file for components and frames matching query."""
        if not self.is_configured():
            logger.warning("Figma not configured, skipping search")
            return []

        try:
            file_key = self._settings.figma_file_key
            file_data = await self._get_file_data(file_key)

            # Search through document tree for matching nodes
            artifacts = []
            search_terms_lower = [term.lower() for term in query.search_terms]

            def search_nodes(node: dict, path: str = "") -> None:
                """Recursively search through Figma node tree."""
                node_name = node.get("name", "")
                node_type = node.get("type", "")
                current_path = f"{path}/{node_name}" if path else node_name

                # Check if node matches search terms
                name_lower = node_name.lower()
                matches = any(term in name_lower for term in search_terms_lower)

                if matches and node_type in (
                    "FRAME",
                    "COMPONENT",
                    "COMPONENT_SET",
                    "SECTION",
                ):
                    artifact = Artifact(
                        id=node.get("id", ""),
                        source=AppSource.FIGMA,
                        artifact_type=ArtifactType.DESIGN,
                        title=node_name,
                        content=f"Figma {node_type}: {current_path}",
                        url=f"https://www.figma.com/file/{file_key}?node-id={node.get('id', '')}",
                        metadata={
                            "node_type": node_type,
                            "path": current_path,
                            "file_key": file_key,
                            "file_name": file_data.get("name", ""),
                        },
                        updated_at=self._parse_date(file_data.get("lastModified")),
                    )
                    artifacts.append(artifact)

                # Recurse into children
                for child in node.get("children", []):
                    search_nodes(child, current_path)

            # Start search from document root
            document = file_data.get("document", {})
            search_nodes(document)

            return artifacts[:20]  # Limit results

        except Exception as e:
            logger.error(f"Figma search failed: {e}")
            return []

    async def get_by_id(self, artifact_id: str) -> Artifact | None:
        """Get a specific Figma node by ID."""
        if not self.is_configured():
            return None

        try:
            file_key = self._settings.figma_file_key

            response = await self._request_with_retry(
                "GET",
                f"/files/{file_key}/nodes",
                params={"ids": artifact_id},
            )
            data = response.json()

            nodes = data.get("nodes", {})
            node_data = nodes.get(artifact_id, {})
            node = node_data.get("document", {})

            if not node:
                return None

            return Artifact(
                id=artifact_id,
                source=AppSource.FIGMA,
                artifact_type=ArtifactType.DESIGN,
                title=node.get("name", ""),
                content=f"Figma {node.get('type', '')}: {node.get('name', '')}",
                url=f"https://www.figma.com/file/{file_key}?node-id={artifact_id}",
                metadata={
                    "node_type": node.get("type"),
                    "file_key": file_key,
                },
                updated_at=self._parse_date(data.get("lastModified")),
            )
        except Exception as e:
            logger.error(f"Figma get_by_id failed: {e}")
            return None

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Parse Figma date string."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            return None

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
