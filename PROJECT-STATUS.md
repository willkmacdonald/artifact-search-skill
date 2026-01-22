# Artifact Search Skill - Project Status

## Session Summary (2026-01-21)

Built a complete multi-app artifact search skill for MedTech risk management from scratch.

### What Was Accomplished

- [x] Created FastAPI backend with multi-app search orchestration
- [x] Built AI-powered query router using Azure AI Foundry (via `az login`)
- [x] Implemented connectors for 4 apps:
  - **Azure DevOps** - ✅ Working (15 sample work items created)
  - **Figma** - ✅ Connected (empty file, ready for designs)
  - **Ice Panel** - ✅ Connected (empty landscape, ready for C4 diagrams)
  - **Notion** - ❌ Skipped (complex auth setup)
- [x] Created React/Next.js Copilot-style frontend
- [x] Added direct deep-links to source artifacts (click to open in Azure DevOps)
- [x] Seeded Azure DevOps with MedTech risk management data:
  - 5 Risks (RISK-001 to RISK-005)
  - 5 Mitigations (MIT-001 to MIT-005)
  - 3 Requirements (REQ-101 to REQ-103)
  - 2 Test Cases (TC-001, TC-002)

### Running the Demo

```bash
# Terminal 1: Backend
cd /Users/willmacdonald/Documents/Code/skills/artifact-search-skill
source venv/bin/activate
python -m artifact_search

# Terminal 2: Frontend
cd frontend
npm run dev
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3001 (or 3000 if available)

### Sample Queries to Try

- "What are the risks related to arrhythmia detection?"
- "Show me mitigations for patient data security"
- "Find requirements for emergency alerts"
- "What test cases verify alert delivery?"

### What's Next

1. **Add content to Figma** - Create frames like "Risk Dashboard", "Alert Settings"
2. **Add content to Ice Panel** - Create C4 components for CardioWatch architecture
3. **Optional: Set up Notion** - If you want documentation search
4. **Polish for demo** - Add more sample data, refine UI

### Configuration

All credentials in `.env` file:
- `AZURE_DEVOPS_ORG_URL`, `AZURE_DEVOPS_PAT`, `AZURE_DEVOPS_PROJECT`
- `AZURE_AI_ENDPOINT`, `AZURE_AI_DEPLOYMENT` (using `az login` for auth)
- `FIGMA_ACCESS_TOKEN`, `FIGMA_FILE_KEY`
- `ICEPANEL_API_KEY`, `ICEPANEL_LANDSCAPE_ID`
