"""Data models for artifact search skill."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AppSource(str, Enum):
    """Supported application sources for artifact search."""

    AZURE_DEVOPS = "azure_devops"
    FIGMA = "figma"
    NOTION = "notion"
    ICEPANEL = "icepanel"


class ArtifactType(str, Enum):
    """Types of artifacts that can be searched."""

    REQUIREMENT = "requirement"
    RISK = "risk"
    MITIGATION = "mitigation"
    DESIGN = "design"
    ARCHITECTURE = "architecture"
    WORK_ITEM = "work_item"
    TEST_CASE = "test_case"
    DOCUMENT = "document"


class SearchQuery(BaseModel):
    """Incoming search query from user."""

    query: str = Field(..., description="Natural language query from user")
    context: dict[str, Any] | None = Field(
        default=None, description="Additional context for the search"
    )


class RoutedQuery(BaseModel):
    """Query after routing to specific app(s)."""

    original_query: str
    target_apps: list[AppSource]
    artifact_types: list[ArtifactType]
    search_terms: list[str]
    filters: dict[str, Any] = Field(default_factory=dict)


class Artifact(BaseModel):
    """A retrieved artifact from any source."""

    id: str
    source: AppSource
    artifact_type: ArtifactType
    title: str
    content: str
    url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SearchResult(BaseModel):
    """Complete search result with artifacts and metadata."""

    query: str
    artifacts: list[Artifact]
    sources_searched: list[AppSource]
    total_results: int
    search_duration_ms: float
    summary: str | None = None


# MedTech Risk Management specific models


class RiskSeverity(str, Enum):
    """Risk severity levels per ISO 14971."""

    NEGLIGIBLE = "negligible"
    MINOR = "minor"
    SERIOUS = "serious"
    CRITICAL = "critical"
    CATASTROPHIC = "catastrophic"


class RiskProbability(str, Enum):
    """Risk probability levels."""

    IMPROBABLE = "improbable"
    REMOTE = "remote"
    OCCASIONAL = "occasional"
    PROBABLE = "probable"
    FREQUENT = "frequent"


class RiskItem(BaseModel):
    """A risk item in the risk management system."""

    risk_id: str
    title: str
    description: str
    hazard: str
    harm: str
    severity: RiskSeverity
    probability_before: RiskProbability
    probability_after: RiskProbability | None = None
    risk_control_measures: list[str] = Field(default_factory=list)
    related_requirements: list[str] = Field(default_factory=list)
    status: str = "open"


class Mitigation(BaseModel):
    """A mitigation/risk control measure."""

    mitigation_id: str
    title: str
    description: str
    mitigation_type: str  # inherent safety, protective measure, information for safety
    risk_ids: list[str]
    verification_method: str
    status: str = "proposed"
