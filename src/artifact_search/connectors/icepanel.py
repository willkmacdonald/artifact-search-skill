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

            # Fetch diagrams first to build a lookup for model object deep links
            diagrams_response = await client.get(
                f"/landscapes/{landscape_id}/versions/latest/diagrams"
            )
            diagram_handle_map: dict[str, str] = {}
            diagrams_list: list[dict] = []
            if diagrams_response.status_code == 200:
                diagrams_list = diagrams_response.json().get("diagrams", [])
                for d in diagrams_list:
                    diagram_handle_map[d["id"]] = d.get("handleId", d["id"])

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
                        url = self._build_object_url(
                            landscape_id, obj, diagram_handle_map
                        )
                        artifact = Artifact(
                            id=obj.get("id", ""),
                            source=AppSource.ICEPANEL,
                            artifact_type=ArtifactType.ARCHITECTURE,
                            title=obj_name,
                            content=obj_description or f"C4 {obj_type}: {obj_name}",
                            url=url,
                            metadata={
                                "object_type": obj_type,
                                "landscape_id": landscape_id,
                                "tags": obj.get("tags", []),
                                "technology": obj.get("technology"),
                            },
                            updated_at=self._parse_date(obj.get("updatedAt")),
                        )
                        artifacts.append(artifact)

            # Also search diagrams
            for view in diagrams_list:
                view_name = view.get("name", "")
                view_description = view.get("description", "")

                searchable = f"{view_name} {view_description}".lower()
                if any(term in searchable for term in search_terms_lower):
                    handle_id = view.get("handleId", view.get("id", ""))
                    artifact = Artifact(
                        id=view.get("id", ""),
                        source=AppSource.ICEPANEL,
                        artifact_type=ArtifactType.ARCHITECTURE,
                        title=f"Diagram: {view_name}",
                        content=view_description
                        or f"Architecture diagram: {view_name}",
                        url=f"https://app.icepanel.io/landscapes/{landscape_id}/versions/latest/diagrams/editor?diagram={handle_id}",
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
            logger.error(f"Ice Panel search failed: {type(e).__name__}: {e}", exc_info=True)
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

            # Build diagram handle map for deep linking
            diagrams_response = await client.get(
                f"/landscapes/{landscape_id}/versions/latest/diagrams"
            )
            diagram_handle_map: dict[str, str] = {}
            if diagrams_response.status_code == 200:
                for d in diagrams_response.json().get("diagrams", []):
                    diagram_handle_map[d["id"]] = d.get("handleId", d["id"])

            url = self._build_object_url(landscape_id, obj, diagram_handle_map)

            return Artifact(
                id=obj.get("id", ""),
                source=AppSource.ICEPANEL,
                artifact_type=ArtifactType.ARCHITECTURE,
                title=obj.get("name", ""),
                content=obj.get("description", ""),
                url=url,
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

    def _build_object_url(
        self,
        landscape_id: str,
        obj: dict,
        diagram_handle_map: dict[str, str],
    ) -> str:
        """Build the best deep link URL for a model object.

        Prefers linking to the first diagram the object appears in (with the
        object focused), falling back to the model objects detail view.
        """
        base = f"https://app.icepanel.io/landscapes/{landscape_id}/versions/latest"
        handle_id = obj.get("handleId", obj.get("id", ""))

        # Try to find a diagram this object appears in
        obj_diagrams = obj.get("diagrams", {})
        if obj_diagrams:
            first_diagram_id = next(iter(obj_diagrams))
            diagram_handle = diagram_handle_map.get(first_diagram_id)
            if diagram_handle:
                return (
                    f"{base}/diagrams/editor?diagram={diagram_handle}&model={handle_id}"
                )

        # Fallback to model objects detail view
        return f"{base}/model/objects?object_tab=details&object={handle_id}"

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
