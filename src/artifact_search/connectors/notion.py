"""Notion connector for documentation and knowledge base."""

import logging
from datetime import datetime

import httpx

from artifact_search.config import Settings
from artifact_search.connectors.base import BaseConnector
from artifact_search.models import AppSource, Artifact, ArtifactType, RoutedQuery

logger = logging.getLogger(__name__)


class NotionConnector(BaseConnector):
    """Connector for Notion databases and pages."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: httpx.AsyncClient | None = None

    @property
    def source(self) -> AppSource:
        return AppSource.NOTION

    def is_configured(self) -> bool:
        return self._settings.is_notion_configured()

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create authenticated HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url="https://api.notion.com/v1",
                headers={
                    "Authorization": f"Bearer {self._settings.notion_api_key}",
                    "Notion-Version": "2022-06-28",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def test_connection(self) -> bool:
        """Test connection to Notion."""
        if not self.is_configured():
            return False
        try:
            client = await self._get_client()
            response = await client.get("/users/me")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Notion connection test failed: {e}")
            return False

    async def search(self, query: RoutedQuery) -> list[Artifact]:
        """Search Notion pages and database entries."""
        if not self.is_configured():
            logger.warning("Notion not configured, skipping search")
            return []

        try:
            client = await self._get_client()

            # Use Notion's search API
            search_text = " ".join(query.search_terms)
            search_payload = {
                "query": search_text,
                "page_size": 20,
            }

            response = await client.post("/search", json=search_payload)
            response.raise_for_status()
            data = response.json()

            artifacts = []
            for result in data.get("results", []):
                object_type = result.get("object")

                if object_type == "page":
                    artifact = self._parse_page(result)
                elif object_type == "database":
                    artifact = self._parse_database(result)
                else:
                    continue

                if artifact:
                    artifacts.append(artifact)

            return artifacts

        except Exception as e:
            logger.error(f"Notion search failed: {e}")
            return []

    async def get_by_id(self, artifact_id: str) -> Artifact | None:
        """Get a specific Notion page by ID."""
        if not self.is_configured():
            return None

        try:
            client = await self._get_client()
            response = await client.get(f"/pages/{artifact_id}")
            response.raise_for_status()
            page = response.json()

            return self._parse_page(page)
        except Exception as e:
            logger.error(f"Notion get_by_id failed: {e}")
            return None

    async def query_database(self, filter_obj: dict | None = None) -> list[Artifact]:
        """Query the configured Notion database."""
        if not self.is_configured():
            return []

        try:
            client = await self._get_client()
            database_id = self._settings.notion_database_id

            payload = {"page_size": 100}
            if filter_obj:
                payload["filter"] = filter_obj

            response = await client.post(
                f"/databases/{database_id}/query", json=payload
            )
            response.raise_for_status()
            data = response.json()

            artifacts = []
            for page in data.get("results", []):
                artifact = self._parse_page(page)
                if artifact:
                    artifacts.append(artifact)

            return artifacts

        except Exception as e:
            logger.error(f"Notion database query failed: {e}")
            return []

    def _parse_page(self, page: dict) -> Artifact | None:
        """Parse a Notion page into an Artifact."""
        try:
            page_id = page.get("id", "")
            properties = page.get("properties", {})

            # Extract title - find whichever property has type "title"
            title = ""
            for _prop_name, prop_value in properties.items():
                if prop_value.get("type") == "title":
                    title_items = prop_value.get("title", [])
                    title = "".join(
                        item.get("plain_text", "") for item in title_items
                    )
                    break

            # Extract content preview from other properties
            content_parts = []
            for prop_name, prop_value in properties.items():
                prop_type = prop_value.get("type")
                if prop_type == "rich_text":
                    text_items = prop_value.get("rich_text", [])
                    text = "".join(item.get("plain_text", "") for item in text_items)
                    if text:
                        content_parts.append(f"{prop_name}: {text}")
                elif prop_type == "select":
                    select = prop_value.get("select")
                    if select:
                        content_parts.append(f"{prop_name}: {select.get('name', '')}")
                elif prop_type == "multi_select":
                    selects = prop_value.get("multi_select", [])
                    names = [s.get("name", "") for s in selects]
                    if names:
                        content_parts.append(f"{prop_name}: {', '.join(names)}")

            content = "\n".join(content_parts)

            # Determine artifact type based on properties
            artifact_type = self._determine_artifact_type(properties)

            return Artifact(
                id=page_id,
                source=AppSource.NOTION,
                artifact_type=artifact_type,
                title=title or "Untitled",
                content=content,
                url=page.get("url"),
                metadata={
                    "parent_type": page.get("parent", {}).get("type"),
                    "parent_id": page.get("parent", {}).get("database_id")
                    or page.get("parent", {}).get("page_id"),
                    "properties": properties,
                },
                created_at=self._parse_date(page.get("created_time")),
                updated_at=self._parse_date(page.get("last_edited_time")),
            )
        except Exception as e:
            logger.error(f"Failed to parse Notion page: {e}")
            return None

    def _parse_database(self, database: dict) -> Artifact | None:
        """Parse a Notion database into an Artifact."""
        try:
            db_id = database.get("id", "")
            title_items = database.get("title", [])
            title = "".join(item.get("plain_text", "") for item in title_items)

            description_items = database.get("description", [])
            description = "".join(
                item.get("plain_text", "") for item in description_items
            )

            return Artifact(
                id=db_id,
                source=AppSource.NOTION,
                artifact_type=ArtifactType.DOCUMENT,
                title=title or "Untitled Database",
                content=description or f"Notion database: {title}",
                url=database.get("url"),
                metadata={
                    "object": "database",
                    "properties": list(database.get("properties", {}).keys()),
                },
                created_at=self._parse_date(database.get("created_time")),
                updated_at=self._parse_date(database.get("last_edited_time")),
            )
        except Exception as e:
            logger.error(f"Failed to parse Notion database: {e}")
            return None

    def _determine_artifact_type(self, properties: dict) -> ArtifactType:
        """Determine artifact type based on Notion page properties."""
        prop_names_lower = [name.lower() for name in properties.keys()]

        if any("risk" in name for name in prop_names_lower):
            return ArtifactType.RISK
        elif any("mitigation" in name or "control" in name for name in prop_names_lower):
            return ArtifactType.MITIGATION
        elif any("requirement" in name or "req" in name for name in prop_names_lower):
            return ArtifactType.REQUIREMENT
        elif any("test" in name for name in prop_names_lower):
            return ArtifactType.TEST_CASE
        else:
            return ArtifactType.DOCUMENT

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Parse Notion date string."""
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
