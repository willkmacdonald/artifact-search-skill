"""Ice Panel connector for architecture diagrams."""

import logging
from datetime import datetime

import httpx

from artifact_search.config import Settings
from artifact_search.connectors.base import BaseConnector
from artifact_search.models import AppSource, Artifact, ArtifactType, RoutedQuery

logger = logging.getLogger(__name__)


class IcePanelConnector(BaseConnector):
    """Connector for Ice Panel C4 architecture diagrams."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: httpx.AsyncClient | None = None

    @property
    def source(self) -> AppSource:
        return AppSource.ICEPANEL

    def is_configured(self) -> bool:
        return self._settings.is_icepanel_configured()

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create authenticated HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url="https://api.icepanel.io/v1",
                headers={
                    "Authorization": f"ApiKey {self._settings.icepanel_api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def test_connection(self) -> bool:
        """Test connection to Ice Panel."""
        if not self.is_configured():
            return False
        try:
            client = await self._get_client()
            landscape_id = self._settings.icepanel_landscape_id
            response = await client.get(f"/landscapes/{landscape_id}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ice Panel connection test failed: {e}")
            return False

    async def search(self, query: RoutedQuery) -> list[Artifact]:
        """Search Ice Panel for architecture components and diagrams."""
        if not self.is_configured():
            logger.warning("Ice Panel not configured, skipping search")
            return []

        try:
            client = await self._get_client()
            landscape_id = self._settings.icepanel_landscape_id

            artifacts = []
            search_terms_lower = [term.lower() for term in query.search_terms]

            # Get model objects (components, systems, etc.)
            objects_response = await client.get(
                f"/landscapes/{landscape_id}/versions/latest/model/objects"
            )

            if objects_response.status_code == 200:
                objects = objects_response.json()

                for obj in objects.get("modelObjects", []):
                    obj_name = obj.get("name", "")
                    obj_description = obj.get("description", "")
                    obj_type = obj.get("type", "")

                    # Check if matches search terms
                    searchable = f"{obj_name} {obj_description}".lower()
                    if any(term in searchable for term in search_terms_lower):
                        artifact = Artifact(
                            id=obj.get("id", ""),
                            source=AppSource.ICEPANEL,
                            artifact_type=ArtifactType.ARCHITECTURE,
                            title=obj_name,
                            content=obj_description or f"C4 {obj_type}: {obj_name}",
                            url=f"https://app.icepanel.io/landscapes/{landscape_id}",
                            metadata={
                                "object_type": obj_type,
                                "landscape_id": landscape_id,
                                "tags": obj.get("tags", []),
                                "technology": obj.get("technology"),
                            },
                            updated_at=self._parse_date(obj.get("updatedAt")),
                        )
                        artifacts.append(artifact)

            # Also search diagrams/views
            views_response = await client.get(
                f"/landscapes/{landscape_id}/versions/latest/diagrams"
            )
            if views_response.status_code == 200:
                views = views_response.json()

                for view in views.get("data", []):
                    view_name = view.get("name", "")
                    view_description = view.get("description", "")

                    searchable = f"{view_name} {view_description}".lower()
                    if any(term in searchable for term in search_terms_lower):
                        artifact = Artifact(
                            id=view.get("id", ""),
                            source=AppSource.ICEPANEL,
                            artifact_type=ArtifactType.ARCHITECTURE,
                            title=f"Diagram: {view_name}",
                            content=view_description
                            or f"Architecture diagram: {view_name}",
                            url=f"https://app.icepanel.io/landscapes/{landscape_id}/diagrams/{view.get('id')}",
                            metadata={
                                "object_type": "diagram",
                                "view_type": view.get("type"),
                                "landscape_id": landscape_id,
                            },
                            updated_at=self._parse_date(view.get("updatedAt")),
                        )
                        artifacts.append(artifact)

            return artifacts[:20]  # Limit results

        except Exception as e:
            logger.error(f"Ice Panel search failed: {e}")
            return []

    async def get_by_id(self, artifact_id: str) -> Artifact | None:
        """Get a specific Ice Panel object by ID."""
        if not self.is_configured():
            return None

        try:
            client = await self._get_client()
            landscape_id = self._settings.icepanel_landscape_id

            response = await client.get(
                f"/landscapes/{landscape_id}/model-objects/{artifact_id}"
            )
            if response.status_code != 200:
                return None

            obj = response.json().get("data", {})

            return Artifact(
                id=obj.get("id", ""),
                source=AppSource.ICEPANEL,
                artifact_type=ArtifactType.ARCHITECTURE,
                title=obj.get("name", ""),
                content=obj.get("description", ""),
                url=f"https://app.icepanel.io/landscapes/{landscape_id}",
                metadata={
                    "object_type": obj.get("type"),
                    "tags": obj.get("tags", []),
                    "technology": obj.get("technology"),
                },
                updated_at=self._parse_date(obj.get("updatedAt")),
            )
        except Exception as e:
            logger.error(f"Ice Panel get_by_id failed: {e}")
            return None

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Parse Ice Panel date string."""
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
