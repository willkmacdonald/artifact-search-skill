# Backend Architecture Specification

## Overview

The artifact-search-skill backend is a FastAPI application that provides AI-powered multi-app artifact search for MedTech risk management. It searches across Azure DevOps, Figma, Notion, and Ice Panel, using Azure AI Foundry for intelligent query routing and response summarization.

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | FastAPI 0.109+ | Async web API |
| Server | Uvicorn | ASGI server |
| HTTP Client | httpx | Async HTTP for connector APIs |
| AI | Azure OpenAI (AsyncAzureOpenAI) | Query routing, summarization |
| Auth | azure-identity | Azure AD authentication |
| Validation | Pydantic | Request/response models |
| Config | pydantic-settings | Environment-based settings |

## Architecture Diagram

```
                    ┌─────────────────────────────────────────────┐
                    │                  FastAPI App                 │
                    │                   (api.py)                   │
                    └─────────────────────┬───────────────────────┘
                                          │
                    ┌─────────────────────▼───────────────────────┐
                    │            ArtifactSearchEngine              │
                    │                 (search.py)                  │
                    │  - Orchestrates parallel connector searches  │
                    │  - Generates AI-powered result summaries     │
                    └─────────────────────┬───────────────────────┘
                                          │
              ┌───────────────────────────┼───────────────────────────┐
              │                           │                           │
              ▼                           ▼                           ▼
┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐
│      Query Router       │ │      Connectors         │ │     Azure AI Client     │
│      (router.py)        │ │    (connectors/*.py)    │ │   (AsyncAzureOpenAI)    │
│  - AI-powered routing   │ │  - AzureDevOpsConnector │ │  - Summary generation   │
│  - Fallback keywords    │ │  - FigmaConnector       │ │  - Response synthesis   │
└─────────────────────────┘ │  - NotionConnector      │ └─────────────────────────┘
                            │  - IcePanelConnector    │
                            └─────────────────────────┘
```

## Module Structure

```
src/artifact_search/
├── __init__.py           # Package exports
├── __main__.py           # Entry point (uvicorn runner)
├── api.py                # FastAPI app, routes, middleware
├── config.py             # Settings (pydantic-settings)
├── models.py             # Pydantic data models
├── router.py             # AI query routing
├── search.py             # Search orchestration
└── connectors/
    ├── __init__.py       # Connector exports
    ├── base.py           # BaseConnector ABC
    ├── azure_devops.py   # Azure DevOps work items
    ├── figma.py          # Figma design files
    ├── notion.py         # Notion pages/databases
    └── icepanel.py       # Ice Panel C4 diagrams
```

## API Endpoints

### GET /health
Returns API health status and connection state for all configured sources.

```json
{
  "status": "healthy",
  "configured_sources": ["azure_devops", "figma", "notion", "icepanel"],
  "connections": {
    "azure_devops": true,
    "figma": true,
    "notion": true,
    "icepanel": true
  }
}
```

### POST /search
Searches configured sources and returns artifacts with AI-generated summary.

**Request:**
```json
{
  "query": "What are the risks related to arrhythmia detection?",
  "context": {}
}
```

**Response:**
```json
{
  "query": "What are the risks related to arrhythmia detection?",
  "artifacts": [
    {
      "id": "12345",
      "source": "azure_devops",
      "artifact_type": "risk",
      "title": "RISK-001: False negative arrhythmia detection",
      "content": "...",
      "url": "https://dev.azure.com/...",
      "metadata": {},
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "sources_searched": ["azure_devops", "notion"],
  "total_results": 5,
  "search_duration_ms": 1250.5,
  "summary": "Found 5 risk items related to arrhythmia detection..."
}
```

### POST /chat
Chat-style endpoint with conversation context (for future stateful chat).

### GET /artifact/{source}/{artifact_id}
Retrieves a specific artifact by source and ID.

### GET /sources
Lists configured and available sources.

## Data Models

### Core Enums

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
```

### Query Flow Models

1. **SearchQuery** → User's natural language query
2. **RoutedQuery** → Query after AI routing (target apps, types, search terms)
3. **Artifact** → Individual search result
4. **SearchResult** → Complete response with artifacts and metadata

### MedTech Domain Models

- **RiskItem**: ISO 14971 risk with severity, probability, hazard/harm
- **Mitigation**: Risk control measure with verification method
- **RiskSeverity/RiskProbability**: Enums for risk assessment

## Connector Pattern

All connectors implement `BaseConnector` (abstract base class):

```python
class BaseConnector(ABC):
    @property
    @abstractmethod
    def source(self) -> AppSource: ...

    @abstractmethod
    async def search(self, query: RoutedQuery) -> list[Artifact]: ...

    @abstractmethod
    async def get_by_id(self, artifact_id: str) -> Artifact | None: ...

    @abstractmethod
    def is_configured(self) -> bool: ...

    @abstractmethod
    async def test_connection(self) -> bool: ...
```

### Connector Implementations

| Connector | API | Auth | Features |
|-----------|-----|------|----------|
| AzureDevOpsConnector | REST + WIQL | Basic (PAT) | Work item queries, linked items |
| FigmaConnector | REST | Bearer token | Node tree search, caching, retry |
| NotionConnector | REST | Bearer token | Database queries, page search |
| IcePanelConnector | REST | API key | Objects, diagrams, flows |

## Query Routing

### AI-Powered Routing (router.py)

Uses Azure OpenAI to analyze queries and determine:
- Target applications to search
- Artifact types to look for
- Search terms to extract

**System Prompt Context:**
- MedTech risk management domain knowledge
- App-to-artifact-type mappings
- ISO 14971 terminology

### Fallback Routing

When Azure AI is unavailable, uses keyword matching:
- "design", "ui", "wireframe" → Figma
- "architecture", "system", "c4" → Ice Panel
- "risk", "hazard", "harm" → Azure DevOps + Notion
- "mitigation", "control" → Azure DevOps + Notion

## Search Orchestration (search.py)

### ArtifactSearchEngine

1. **Initialize connectors** based on configuration
2. **Route query** via AI or fallback
3. **Execute parallel searches** across target connectors
4. **Aggregate results** and sort by timestamp
5. **Generate AI summary** of findings
6. **Return SearchResult** with metadata

### Parallel Execution

```python
search_tasks = [connector.search(routed) for connector in target_connectors]
results = await asyncio.gather(*search_tasks, return_exceptions=True)
```

## Configuration (config.py)

Settings loaded from environment variables via pydantic-settings:

```python
class Settings(BaseSettings):
    # Azure DevOps
    azure_devops_org_url: str
    azure_devops_pat: str
    azure_devops_project: str = "RiskManagement"

    # Figma
    figma_access_token: str
    figma_file_key: str

    # Notion
    notion_api_key: str
    notion_database_id: str

    # Ice Panel
    icepanel_api_key: str
    icepanel_landscape_id: str

    # Azure AI Foundry
    azure_ai_endpoint: str
    azure_ai_api_key: str  # Optional if using az login
    azure_ai_deployment: str = "gpt-4o"
    azure_ai_use_ad_auth: bool = True
```

### Authentication Options

- **Azure AI**: API key OR Azure AD (`az login` + DefaultAzureCredential)
- **Azure DevOps**: Personal Access Token (Basic auth)
- **Figma/Notion/Ice Panel**: API tokens (Bearer/header)

## Caching Strategy

### Current: In-Memory (Figma only)

```python
_file_cache: dict[str, tuple[float, dict]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes
```

### Planned: Persistent File Cache

See `current-sprint.md` for Figma persistent cache implementation plan.

## Error Handling

- **Connector failures**: Logged, search continues with other connectors
- **AI unavailable**: Falls back to keyword-based routing
- **Rate limits**: Exponential backoff retry (Figma connector)
- **Timeouts**: 30-second timeout per connector request

## Security Considerations

- All credentials in `.env` (never committed)
- Input validation via Pydantic models
- CORS restricted to localhost (configurable for deployment)
- No authentication on API endpoints (demo/PoC scope)

## Lifecycle Management

FastAPI lifespan context manager handles:
- **Startup**: Initialize ArtifactSearchEngine and connectors
- **Shutdown**: Close all HTTP client connections

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _search_engine
    _search_engine = ArtifactSearchEngine()
    yield
    await _search_engine.close()
```
