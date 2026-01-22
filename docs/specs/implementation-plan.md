# Implementation Plan: Azure Migration

## Overview

Migrate artifact-search-skill from local development to Azure for demo/PoC hosting. The plan minimizes costs by reusing existing Azure resources (Container Apps Environment, ACR) and leveraging free tiers where available.

## Target Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Existing Container Apps Environment             │
│  ┌─────────────────────┐    ┌─────────────────────────────┐ │
│  │ Your existing app   │    │ artifact-search-api         │ │
│  └─────────────────────┘    │ FastAPI, scale 0-1          │ │
│                              └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────┐
│  Existing ACR (Basic)       │                               │
│  - artifact-search-api:latest                               │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────┐
│  Azure Static Web Apps (Free Tier)                          │
│  - Next.js frontend (static export)                         │
└─────────────────────────────────────────────────────────────┘
```

**Estimated Cost**: ~$0-5/mo (scale-to-zero compute, shared ACR, free SWA)

---

## Phase 1: Containerize Backend ✅ COMPLETE

**Goal**: Get the FastAPI backend running in a Docker container locally.

### PR 1.1: Create Dockerfile and .dockerignore ✅
- Created multi-stage Dockerfile (builder + runtime)
- Created .dockerignore to exclude dev files
- Configured uvicorn to bind to `0.0.0.0`
- Added `PYTHONUNBUFFERED=1` for container logging

### PR 1.2: Make CORS Configurable ✅
- Added `ALLOWED_ORIGINS` environment variable to `api.py`
- Defaults to `http://localhost:3000,http://127.0.0.1:3000`
- Parses comma-separated string into list

### PR 1.3: Add Health Check Endpoint Improvements ✅
- `/health` responds in ~10ms (fast for container probes)
- `/health/details` provides full connection testing
- Added startup banner with version, CORS, and configured sources
- Added shutdown logging for debugging

---

## Phase 2: Deploy Backend to Azure ✅ COMPLETE

**Goal**: Deploy containerized backend to existing Container Apps Environment.

### PR 2.1: Push Image to ACR ✅
- Documented manual deployment steps
- Created deployment script (`scripts/deploy-backend.sh`)
- Pushed first image to existing ACR
- Image visible in ACR portal

### PR 2.2: Create Container App ✅
- Created Container App with environment variables
- Configured secrets for API keys
- Set scale-to-zero (min replicas: 0)
- `/health` endpoint accessible from internet

### PR 2.3: Add GitHub Actions CI/CD ✅
- Created `.github/workflows/deploy-backend.yml`
- Build image on push to main
- Deploy to Container Apps automatically
- Push to main triggers deployment
- Fixed: Use `azure/login@v1` for JSON credentials compatibility

**Backend URL**: https://artifact-search-api.mangotree-f82b3c1f.eastus.azurecontainerapps.io

---

## Phase 3: Deploy Frontend to Azure ✅ COMPLETE

**Goal**: Deploy Next.js frontend to Azure Static Web Apps.

### PR 3.1: Configure Static Export ✅
- Added `output: 'export'` to `next.config.js`
- Added `NEXT_PUBLIC_API_URL` environment variable
- Updated API calls to use configurable base URL
- `npm run build` produces static files in `out/`

### PR 3.2: Create Static Web App ✅
- Created SWA resource linked to GitHub repo
- Configured environment variable for API URL
- Updated backend CORS for SWA domain
- Frontend loads, connects to backend

### PR 3.3: Add Frontend CI/CD ✅
- SWA automatically deploys on push (GitHub integration)
- Workflow file created by Azure
- Push to main deploys frontend

### PR 3.4: Custom Domain ✅
- Configured custom domain: artifact-search.willmacdonald.com
- SSL certificate auto-provisioned
- Updated CORS for custom domain

**Frontend URL**: https://artifact-search.willmacdonald.com

---

## Phase 4: Production Hardening (Optional)

**Goal**: Add observability and improve reliability for ongoing demos.

### PR 4.1: Add Application Insights
- Integrate OpenTelemetry with Azure Monitor
- Add request tracing and error logging
- Test: View traces in Azure Portal

### PR 4.2: Documentation Update
- Update README with deployment instructions
- Add architecture diagram
- Document environment variables

---

## Phase Summary

| Phase | Focus | PRs | Status |
|-------|-------|-----|--------|
| 1 | Containerize Backend | 3 | ✅ Complete |
| 2 | Deploy Backend | 3 | ✅ Complete |
| 3 | Deploy Frontend | 4 | ✅ Complete |
| 4 | Production Hardening | 2 | Optional |

**Minimum Viable Deployment**: Phases 1-3 ✅ COMPLETE

---

## Deployed Resources

### URLs
- **Frontend**: https://artifact-search.willmacdonald.com
- **Backend**: https://artifact-search-api.mangotree-f82b3c1f.eastus.azurecontainerapps.io

### Azure Resources
- Container App: `artifact-search-api` in `factory-agent-dev-rg`
- Static Web App: `artifact-search-frontend` in `factory-agent-dev-rg`
- ACR: `factoryagent4u4zqkacr`

### GitHub Secrets Required
- `AZURE_CREDENTIALS`: Service Principal JSON for Azure login
- `AZURE_STATIC_WEB_APPS_API_TOKEN_PURPLE_FOREST_08206B80F`: SWA deployment token (auto-created)

---

## Success Criteria ✅ ALL MET

1. ✅ Backend accessible at `https://artifact-search-api.mangotree-f82b3c1f.eastus.azurecontainerapps.io`
2. ✅ Frontend accessible at `https://artifact-search.willmacdonald.com`
3. ✅ End-to-end search works (frontend → backend → connectors)
4. ✅ Scales to zero when idle
5. ✅ Push to main triggers automatic deployment
