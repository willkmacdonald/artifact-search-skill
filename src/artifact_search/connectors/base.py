"""Base connector interface for all app integrations."""

from abc import ABC, abstractmethod

from artifact_search.models import AppSource, Artifact, RoutedQuery


class BaseConnector(ABC):
    """Abstract base class for app connectors."""

    @property
    @abstractmethod
    def source(self) -> AppSource:
        """Return the app source identifier."""
        ...

    @abstractmethod
    async def search(self, query: RoutedQuery) -> list[Artifact]:
        """Search for artifacts matching the query."""
        ...

    @abstractmethod
    async def get_by_id(self, artifact_id: str) -> Artifact | None:
        """Retrieve a specific artifact by ID."""
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the connector is properly configured."""
        ...

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test the connection to the app."""
        ...
