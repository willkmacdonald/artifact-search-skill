"""Azure DevOps connector for work items and requirements."""

import logging
from datetime import datetime, timezone

import httpx

from artifact_search.config import Settings
from artifact_search.connectors.base import BaseConnector
from artifact_search.models import AppSource, Artifact, ArtifactType, RoutedQuery

logger = logging.getLogger(__name__)


class AzureDevOpsConnector(BaseConnector):
    """Connector for Azure DevOps work items."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: httpx.AsyncClient | None = None

    @property
    def source(self) -> AppSource:
        return AppSource.AZURE_DEVOPS

    def is_configured(self) -> bool:
        return self._settings.is_azure_devops_configured()

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with auth."""
        if self._client is None:
            import base64

            pat = self._settings.azure_devops_pat
            auth_str = base64.b64encode(f":{pat}".encode()).decode()
            self._client = httpx.AsyncClient(
                base_url=self._settings.azure_devops_org_url,
                headers={
                    "Authorization": f"Basic {auth_str}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def test_connection(self) -> bool:
        """Test connection to Azure DevOps."""
        if not self.is_configured():
            return False
        try:
            client = await self._get_client()
            project = self._settings.azure_devops_project
            response = await client.get(f"/{project}/_apis/wit/workitems?api-version=7.0")
            return response.status_code in (200, 404)  # 404 is ok, means no items
        except Exception as e:
            logger.error(f"Azure DevOps connection test failed: {e}")
            return False

    async def search(self, query: RoutedQuery) -> list[Artifact]:
        """Search Azure DevOps work items using WIQL."""
        if not self.is_configured():
            logger.warning("Azure DevOps not configured, skipping search")
            return []

        try:
            client = await self._get_client()
            project = self._settings.azure_devops_project

            # Build WIQL query
            search_terms = " OR ".join(
                f"[System.Title] CONTAINS '{term}' OR [System.Description] CONTAINS '{term}'"
                for term in query.search_terms
            )

            wiql = {
                "query": f"""
                SELECT [System.Id], [System.Title], [System.Description],
                       [System.WorkItemType], [System.State], [System.CreatedDate]
                FROM WorkItems
                WHERE [System.TeamProject] = '{project}'
                AND ({search_terms})
                ORDER BY [System.ChangedDate] DESC
                """
            }

            response = await client.post(
                f"/{project}/_apis/wit/wiql?api-version=7.0",
                json=wiql,
            )
            response.raise_for_status()
            result = response.json()

            # Fetch work item details
            work_items = result.get("workItems", [])
            if not work_items:
                return []

            ids = [str(wi["id"]) for wi in work_items[:20]]  # Limit to 20
            ids_param = ",".join(ids)

            details_response = await client.get(
                f"/{project}/_apis/wit/workitems?ids={ids_param}&api-version=7.0"
            )
            details_response.raise_for_status()
            details = details_response.json()

            artifacts = []
            for item in details.get("value", []):
                fields = item.get("fields", {})
                work_item_id = item["id"]
                # Generate web UI URL (not API URL)
                web_url = f"{self._settings.azure_devops_org_url}/{project}/_workitems/edit/{work_item_id}"
                artifact = Artifact(
                    id=str(work_item_id),
                    source=AppSource.AZURE_DEVOPS,
                    artifact_type=self._map_work_item_type(
                        fields.get("System.WorkItemType", "")
                    ),
                    title=fields.get("System.Title", ""),
                    content=fields.get("System.Description", ""),
                    url=web_url,
                    metadata={
                        "work_item_type": fields.get("System.WorkItemType"),
                        "state": fields.get("System.State"),
                        "assigned_to": fields.get("System.AssignedTo", {}).get(
                            "displayName"
                        ),
                        "tags": fields.get("System.Tags", ""),
                    },
                    created_at=self._parse_date(fields.get("System.CreatedDate")),
                    updated_at=self._parse_date(fields.get("System.ChangedDate")),
                )
                artifacts.append(artifact)

            return artifacts

        except Exception as e:
            logger.error(f"Azure DevOps search failed: {e}")
            return []

    async def get_by_id(self, artifact_id: str) -> Artifact | None:
        """Get a specific work item by ID."""
        if not self.is_configured():
            return None

        try:
            client = await self._get_client()
            project = self._settings.azure_devops_project

            response = await client.get(
                f"/{project}/_apis/wit/workitems/{artifact_id}?api-version=7.0"
            )
            response.raise_for_status()
            item = response.json()

            fields = item.get("fields", {})
            work_item_id = item["id"]
            web_url = f"{self._settings.azure_devops_org_url}/{project}/_workitems/edit/{work_item_id}"
            return Artifact(
                id=str(work_item_id),
                source=AppSource.AZURE_DEVOPS,
                artifact_type=self._map_work_item_type(
                    fields.get("System.WorkItemType", "")
                ),
                title=fields.get("System.Title", ""),
                content=fields.get("System.Description", ""),
                url=web_url,
                metadata={
                    "work_item_type": fields.get("System.WorkItemType"),
                    "state": fields.get("System.State"),
                },
                created_at=self._parse_date(fields.get("System.CreatedDate")),
                updated_at=self._parse_date(fields.get("System.ChangedDate")),
            )
        except Exception as e:
            logger.error(f"Azure DevOps get_by_id failed: {e}")
            return None

    def _map_work_item_type(self, wit_type: str) -> ArtifactType:
        """Map Azure DevOps work item type to artifact type."""
        mapping = {
            "Bug": ArtifactType.WORK_ITEM,
            "Task": ArtifactType.WORK_ITEM,
            "User Story": ArtifactType.REQUIREMENT,
            "Feature": ArtifactType.REQUIREMENT,
            "Epic": ArtifactType.REQUIREMENT,
            "Test Case": ArtifactType.TEST_CASE,
            "Risk": ArtifactType.RISK,
            "Mitigation": ArtifactType.MITIGATION,
        }
        return mapping.get(wit_type, ArtifactType.WORK_ITEM)

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Parse Azure DevOps date string."""
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
