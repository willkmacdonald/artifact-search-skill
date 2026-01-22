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

## Phase 2: Deploy Backend to Azure (Current Sprint)

**Goal**: Deploy containerized backend to existing Container Apps Environment.

### PR 2.1: Push Image to ACR
- Document manual deployment steps
- Create deployment script (`scripts/deploy-backend.sh`)
- Push first image to existing ACR
- Test: Image visible in ACR portal

### PR 2.2: Create Container App
- Create Container App with environment variables
- Configure secrets for API keys
- Set scale-to-zero (min replicas: 0)
- Test: `/health` endpoint accessible from internet

### PR 2.3: Add GitHub Actions CI/CD
- Create `.github/workflows/deploy-backend.yml`
- Build image on push to main
- Deploy to Container Apps automatically
- Test: Push to main triggers deployment

---

## Phase 3: Deploy Frontend to Azure

**Goal**: Deploy Next.js frontend to Azure Static Web Apps.

### PR 3.1: Configure Static Export
- Add `output: 'export'` to `next.config.js`
- Add `NEXT_PUBLIC_API_URL` environment variable
- Update API calls to use configurable base URL
- Test: `npm run build` produces static files in `out/`

### PR 3.2: Create Static Web App
- Create SWA resource linked to GitHub repo
- Configure environment variable for API URL
- Update backend CORS for SWA domain
- Test: Frontend loads, connects to backend

### PR 3.3: Add Frontend CI/CD (Auto via SWA)
- SWA automatically deploys on push (GitHub integration)
- Verify workflow file created by Azure
- Test: Push to main deploys frontend

---

## Phase 4: Production Hardening (Optional)

**Goal**: Add observability and improve reliability for ongoing demos.

### PR 4.1: Add Application Insights
- Integrate OpenTelemetry with Azure Monitor
- Add request tracing and error logging
- Test: View traces in Azure Portal

### PR 4.2: Add Custom Domain (Optional)
- Configure custom domain for SWA
- Add SSL certificate
- Update CORS for new domain

### PR 4.3: Documentation Update
- Update README with deployment instructions
- Add architecture diagram
- Document environment variables

---

## Phase Summary

| Phase | Focus | PRs | Priority |
|-------|-------|-----|----------|
| 1 | Containerize Backend | 3 | Required |
| 2 | Deploy Backend | 3 | Required |
| 3 | Deploy Frontend | 3 | Required |
| 4 | Production Hardening | 3 | Optional |

**Minimum Viable Deployment**: Phases 1-3 (9 PRs)

---

## Dependencies

### Existing Azure Resources (Required)
- Container Apps Environment
- Azure Container Registry (Basic tier)
- Resource Group

### New Azure Resources
- Container App (artifact-search-api)
- Static Web App (artifact-search-frontend)

### GitHub Configuration
- `AZURE_CREDENTIALS` secret for GitHub Actions
- Repository access for SWA deployment

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Cold start latency (scale-to-zero) | Acceptable for demo; document expected 5-15s delay |
| ACR storage limits (Basic tier) | Configure image retention policy (7 days) |
| Secret management | Use Container Apps secrets (sufficient for demo) |
| CORS misconfiguration | Test end-to-end before marking complete |

---

## Success Criteria

1. Backend accessible at `https://artifact-search-api.<env>.azurecontainerapps.io`
2. Frontend accessible at `https://<app>.azurestaticapps.net`
3. End-to-end search works (frontend → backend → connectors)
4. Scales to zero when idle (verify in Azure Portal)
5. Push to main triggers automatic deployment
