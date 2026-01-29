# Artifact Search Skill - MedTech Risk Management

AI-powered multi-app artifact search for MedTech risk management. Ask natural language questions and get relevant results from Azure DevOps, Figma, Notion, and Ice Panel.

## Demo

**Live**: https://artifact-search.willmacdonald.com

Ask questions like:
- "What are the risks related to alerts?"
- "Show me the system architecture for CardioWatch"
- "Find UI designs for the risk dashboard"
- "What mitigations exist for arrhythmia detection?"

The AI routes your query to the appropriate apps, searches for relevant artifacts, and returns a summarized response.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  React/Next.js  │────▶│   FastAPI       │────▶│  Azure AI       │
│  Frontend       │     │   Backend       │     │  (Routing)      │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │  Azure   │ │  Figma   │ │  Notion  │ ...
              │  DevOps  │ │          │ │          │
              └──────────┘ └──────────┘ └──────────┘
```

## Quick Start

### 1. Clone and Install

```bash
cd artifact-search-skill

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -e .

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your credentials
```

### 3. Run the Backend

```bash
# From project root, with venv activated
python -m artifact_search
```

Backend runs at http://localhost:8000

### 4. Run the Frontend

```bash
# In a new terminal
cd frontend
npm run dev
```

Frontend runs at http://localhost:3000

## Configuration

### Required: Azure AI Foundry

Used for query routing and response summarization.

```env
AZURE_AI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_AI_API_KEY=your-azure-ai-key
AZURE_AI_DEPLOYMENT=gpt-4o
```

### App Connectors (Configure the ones you need)

#### Azure DevOps
```env
AZURE_DEVOPS_ORG_URL=https://dev.azure.com/your-org
AZURE_DEVOPS_PAT=your-personal-access-token
AZURE_DEVOPS_PROJECT=RiskManagement
```

#### Figma
```env
FIGMA_ACCESS_TOKEN=your-personal-access-token
FIGMA_FILE_KEY=your-file-key
```

#### Notion
```env
NOTION_API_KEY=secret_your-integration-token
NOTION_DATABASE_ID=your-database-id
```

#### Ice Panel
```env
ICEPANEL_API_KEY=your-api-key
ICEPANEL_WORKSPACE_ID=your-workspace-id
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Check API health and connected sources |
| `/search` | POST | Search for artifacts |
| `/chat` | POST | Chat-style search with conversation context |
| `/sources` | GET | List configured sources |
| `/artifact/{source}/{id}` | GET | Get specific artifact |

## Sample Data

The `sample_data/` directory contains example data structures for each app:

- `azure_devops_work_items.json` - Risk and mitigation work items
- `notion_structure.md` - Risk register and documentation databases
- `figma_frames.md` - UI/UX design frame specifications
- `icepanel_architecture.md` - C4 architecture model definitions

Use these as templates to create demo data in your actual app instances.

## Development

### Project Structure

```
artifact-search-skill/
├── src/artifact_search/
│   ├── __init__.py
│   ├── api.py              # FastAPI endpoints
│   ├── config.py           # Settings management
│   ├── models.py           # Pydantic models
│   ├── router.py           # AI query routing
│   ├── search.py           # Search orchestration
│   └── connectors/         # App-specific connectors
│       ├── azure_devops.py
│       ├── figma.py
│       ├── notion.py
│       └── icepanel.py
├── frontend/               # Next.js frontend
├── sample_data/           # Example data templates
└── tests/                 # Test suite
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
ruff check --fix .
ruff format .
```

## License

MIT

