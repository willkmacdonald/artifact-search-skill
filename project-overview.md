# Artifact Search Skill - Project Overview

This document provides a detailed walkthrough of the key modules in the artifact-search-skill project. Use it as a guide when demoing or explaining the architecture.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           User Query                                     │
│                  "What are the risks related to alerts?"                 │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         router.py                                        │
│                                                                          │
│   Uses Azure AI (GPT-4o) to analyze the query and determine:            │
│   • Which apps to search (azure_devops, notion, figma, icepanel)        │
│   • What artifact types to look for (risk, requirement, design, etc.)   │
│   • Key search terms to extract                                          │
│                                                                          │
│   Output: RoutedQuery { target_apps, artifact_types, search_terms }     │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         search.py                                        │
│                    (ArtifactSearchEngine)                                │
│                                                                          │
│   Orchestrates parallel searches across all target apps:                │
│   • Filters to only configured connectors                               │
│   • Executes searches concurrently with asyncio.gather()                │
│   • Aggregates and sorts results                                        │
│   • Generates AI-powered summary                                        │
└───────┬─────────────────┬─────────────────┬─────────────────┬───────────┘
        │                 │                 │                 │
        ▼                 ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Azure DevOps  │ │    Figma      │ │    Notion     │ │   Ice Panel   │
│  Connector    │ │  Connector    │ │  Connector    │ │  Connector    │
│               │ │               │ │               │ │               │
│ Work items,   │ │ UI designs,   │ │ Documents,    │ │ C4 diagrams,  │
│ requirements, │ │ wireframes,   │ │ knowledge     │ │ architecture  │
│ risks         │ │ components    │ │ base, SOPs    │ │ components    │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
```

---

## 1. config.py - Configuration Management

**Location:** `src/artifact_search/config.py`

**Purpose:** Centralized configuration management using Pydantic Settings. Loads all credentials and settings from environment variables (`.env` file).

### Key Components

```python
class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
```

### Configuration Groups

| Group | Environment Variables | Purpose |
|-------|----------------------|---------|
| Azure DevOps | `AZURE_DEVOPS_ORG_URL`, `AZURE_DEVOPS_PAT`, `AZURE_DEVOPS_PROJECT` | Work item tracking |
| Figma | `FIGMA_ACCESS_TOKEN`, `FIGMA_FILE_KEY` | Design files |
| Notion | `NOTION_API_KEY`, `NOTION_DATABASE_ID` | Documentation |
| Ice Panel | `ICEPANEL_API_KEY`, `ICEPANEL_LANDSCAPE_ID` | Architecture diagrams |
| Azure AI | `AZURE_AI_ENDPOINT`, `AZURE_AI_API_KEY`, `AZURE_AI_DEPLOYMENT` | Query routing & summaries |

### Configuration Check Methods

Each connector has a corresponding check method:

```python
def is_azure_devops_configured(self) -> bool:
    """Check if Azure DevOps is configured."""
    return bool(self.azure_devops_org_url and self.azure_devops_pat)

def is_figma_configured(self) -> bool:
    return bool(self.figma_access_token and self.figma_file_key)

def is_notion_configured(self) -> bool:
    return bool(self.notion_api_key and self.notion_database_id)

def is_icepanel_configured(self) -> bool:
    return bool(self.icepanel_api_key and self.icepanel_landscape_id)

def is_azure_ai_configured(self) -> bool:
    # Either API key or AD auth (az login) works
    return bool(self.azure_ai_endpoint and (self.azure_ai_api_key or self.azure_ai_use_ad_auth))
```

### Usage Pattern

```python
from artifact_search.config import get_settings

settings = get_settings()
if settings.is_figma_configured():
    # Initialize Figma connector
```

---

## 2. router.py - AI Query Routing

**Location:** `src/artifact_search/router.py`

**Purpose:** Uses Azure AI (GPT-4o) to intelligently route user queries to the appropriate applications. This is the "brain" that understands natural language and decides where to search.

### Main Function

```python
async def route_query(query: SearchQuery, settings: Settings) -> RoutedQuery:
    """Use Azure AI to route a query to appropriate apps."""
```

### How It Works

1. **Receives** a natural language query (e.g., "What are the risks related to alerts?")

2. **Sends to Azure AI** with a system prompt that explains:
   - Available applications and their purposes
   - Artifact types (risk, mitigation, requirement, design, etc.)
   - MedTech-specific routing rules

3. **AI responds** with structured JSON:
   ```json
   {
     "target_apps": ["azure_devops", "notion"],
     "artifact_types": ["risk"],
     "search_terms": ["alerts", "risk"]
   }
   ```

4. **Returns** a `RoutedQuery` object for the search engine

### The System Prompt

The AI is given domain-specific knowledge about MedTech risk management:

```
Available applications and their purposes:
- azure_devops: Work items, tasks, bugs, user stories, requirements tracking
- figma: UI/UX designs, wireframes, mockups, design components
- notion: Documentation, knowledge base, meeting notes, policies, SOPs
- icepanel: Architecture diagrams, C4 models, system components

For MedTech risk management queries:
- Requirements related to risks → search azure_devops, notion
- Risk items and hazards → search azure_devops, notion
- Design specifications → search figma
- Architecture questions → search icepanel
```

### Fallback Routing

When Azure AI is unavailable, a keyword-based fallback kicks in:

```python
def _fallback_route(query: SearchQuery) -> RoutedQuery:
    """Fallback routing when AI is not available."""
    query_lower = query.query.lower()

    # Simple keyword-based routing
    if any(word in query_lower for word in ["design", "ui", "ux", "wireframe"]):
        target_apps.append(AppSource.FIGMA)
        artifact_types.append(ArtifactType.DESIGN)

    if any(word in query_lower for word in ["risk", "hazard", "harm"]):
        target_apps.extend([AppSource.AZURE_DEVOPS, AppSource.NOTION])
        artifact_types.append(ArtifactType.RISK)
    # ... more keyword rules
```

---

## 3. search.py - Search Orchestration

**Location:** `src/artifact_search/search.py`

**Purpose:** The central orchestrator that coordinates searches across multiple applications in parallel, aggregates results, and generates AI-powered summaries.

### Key Class: ArtifactSearchEngine

```python
class ArtifactSearchEngine:
    """Orchestrates searches across multiple applications."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._connectors: dict[AppSource, BaseConnector] = {}
        self._initialize_connectors()
```

### Initialization Flow

On startup, the engine:
1. Creates instances of all connector classes
2. Checks which ones are configured (have valid credentials)
3. Only keeps the configured connectors

```python
def _initialize_connectors(self) -> None:
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
```

### Search Flow

```python
async def search(self, query: str | SearchQuery) -> SearchResult:
```

**Step 1: Route the query**
```python
routed = await route_query(search_query, self._settings)
# Returns: RoutedQuery with target_apps, artifact_types, search_terms
```

**Step 2: Filter to configured connectors**
```python
target_connectors = [
    self._connectors[app]
    for app in routed.target_apps
    if app in self._connectors
]
```

**Step 3: Execute searches in parallel**
```python
search_tasks = [connector.search(routed) for connector in target_connectors]
results = await asyncio.gather(*search_tasks, return_exceptions=True)
```

**Step 4: Aggregate results**
```python
for connector, result in zip(target_connectors, results, strict=True):
    if isinstance(result, Exception):
        logger.error(f"Search failed for {connector.source.value}: {result}")
    else:
        all_artifacts.extend(result)
        sources_searched.append(connector.source)
```

**Step 5: Sort by recency**
```python
all_artifacts.sort(
    key=lambda a: a.updated_at or a.created_at or min_datetime,
    reverse=True,
)
```

**Step 6: Generate AI summary**
```python
summary = await self._generate_summary(search_query.query, all_artifacts)
```

### Summary Generation

The engine uses Azure AI to create a human-readable summary:

```python
async def _generate_summary(self, query: str, artifacts: list[Artifact]) -> str | None:
    # Prepare top 10 artifacts as context
    artifact_summaries = []
    for artifact in artifacts[:10]:
        artifact_summaries.append(
            f"- [{artifact.source.value}] {artifact.title}: {artifact.content[:200]}..."
        )

    # Ask AI to summarize
    response = await client.chat.completions.create(
        model=self._settings.azure_ai_deployment,
        messages=[
            {"role": "system", "content": "Summarize search results for MedTech professionals..."},
            {"role": "user", "content": f"Query: {query}\n\nResults:\n{artifacts_text}"},
        ],
    )
```

---

## 4. connectors/ - App Integration Layer

**Location:** `src/artifact_search/connectors/`

**Purpose:** Provides a consistent interface for searching and retrieving artifacts from each external application.

### Base Connector Interface

All connectors inherit from `BaseConnector`:

```python
class BaseConnector(ABC):
    """Abstract base class for app connectors."""

    @property
    @abstractmethod
    def source(self) -> AppSource:
        """Return the app source identifier."""

    @abstractmethod
    async def search(self, query: RoutedQuery) -> list[Artifact]:
        """Search for artifacts matching the query."""

    @abstractmethod
    async def get_by_id(self, artifact_id: str) -> Artifact | None:
        """Retrieve a specific artifact by ID."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the connector is properly configured."""

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test the connection to the app."""

    @abstractmethod
    async def close(self) -> None:
        """Close any open connections."""
```

### Connector Implementations

| Connector | File | API Used | Key Features |
|-----------|------|----------|--------------|
| **AzureDevOpsConnector** | `azure_devops.py` | REST API with WIQL | Searches work items using WIQL queries, maps work item types to artifact types |
| **FigmaConnector** | `figma.py` | REST API | Recursively searches node tree, includes retry logic with exponential backoff, caches file data |
| **NotionConnector** | `notion.py` | REST API | Uses Notion's search API, parses page properties, determines artifact type from property names |
| **IcePanelConnector** | `icepanel.py` | REST API | Searches model objects and diagrams, returns C4 architecture components |

### Example: Azure DevOps Connector

```python
class AzureDevOpsConnector(BaseConnector):

    async def search(self, query: RoutedQuery) -> list[Artifact]:
        # Build WIQL query from search terms
        search_terms = " OR ".join(
            f"[System.Title] CONTAINS '{term}' OR "
            f"[System.Description] CONTAINS '{term}'"
            for term in query.search_terms
        )

        wiql = {
            "query": f"""
            SELECT [System.Id], [System.Title], [System.Description]
            FROM WorkItems
            WHERE [System.TeamProject] = '{project}'
            AND ({search_terms})
            ORDER BY [System.ChangedDate] DESC
            """
        }

        # Execute WIQL query
        response = await client.post("/_apis/wit/wiql", json=wiql)

        # Fetch full work item details
        # Map to Artifact objects
        return artifacts
```

### Common Patterns Across Connectors

1. **Lazy HTTP Client Initialization**
   ```python
   async def _get_client(self) -> httpx.AsyncClient:
       if self._client is None:
           self._client = httpx.AsyncClient(
               base_url="https://api.example.com",
               headers={"Authorization": f"Bearer {token}"},
               timeout=30.0,
           )
       return self._client
   ```

2. **Configuration Check**
   ```python
   def is_configured(self) -> bool:
       return self._settings.is_<app>_configured()
   ```

3. **Graceful Failure**
   ```python
   async def search(self, query: RoutedQuery) -> list[Artifact]:
       if not self.is_configured():
           logger.warning("Not configured, skipping search")
           return []
       try:
           # ... search logic
       except Exception as e:
           logger.error(f"Search failed: {e}")
           return []  # Return empty list, don't crash
   ```

4. **Artifact Mapping**
   ```python
   artifact = Artifact(
       id=str(item_id),
       source=AppSource.AZURE_DEVOPS,
       artifact_type=self._map_type(item_type),
       title=item["title"],
       content=item["description"],
       url=f"https://app.example.com/item/{item_id}",
       metadata={...},
       created_at=self._parse_date(item["created"]),
       updated_at=self._parse_date(item["updated"]),
   )
   ```

---

## Data Models (models.py)

For reference, here are the key data models used throughout:

```python
class AppSource(str, Enum):
    AZURE_DEVOPS = "azure_devops"
    FIGMA = "figma"
    NOTION = "notion"
    ICEPANEL = "icepanel"

class ArtifactType(str, Enum):
    REQUIREMENT = "requirement"
    RISK = "risk"
    MITIGATION = "mitigation"
    DESIGN = "design"
    ARCHITECTURE = "architecture"
    WORK_ITEM = "work_item"
    TEST_CASE = "test_case"
    DOCUMENT = "document"

class RoutedQuery(BaseModel):
    original_query: str
    target_apps: list[AppSource]
    artifact_types: list[ArtifactType]
    search_terms: list[str]

class Artifact(BaseModel):
    id: str
    source: AppSource
    artifact_type: ArtifactType
    title: str
    content: str
    url: str | None
    metadata: dict[str, Any]
    created_at: datetime | None
    updated_at: datetime | None

class SearchResult(BaseModel):
    query: str
    artifacts: list[Artifact]
    sources_searched: list[AppSource]
    total_results: int
    search_duration_ms: float
    summary: str | None
```

---

## Summary

| Module | Responsibility | Key Pattern |
|--------|---------------|-------------|
| `config.py` | Load credentials from env vars | Pydantic Settings with `is_*_configured()` checks |
| `router.py` | Understand user intent | AI-powered routing with keyword fallback |
| `search.py` | Orchestrate parallel searches | `asyncio.gather()` + AI summary generation |
| `connectors/` | Talk to external APIs | Abstract base class with consistent interface |

The architecture follows a clean separation of concerns:
- **Configuration** is isolated and testable
- **Routing** is pluggable (AI or keyword-based)
- **Search** handles orchestration without knowing API details
- **Connectors** encapsulate all app-specific logic
