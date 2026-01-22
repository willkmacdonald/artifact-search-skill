# Current Sprint: Phase 2 - Deploy Backend to Azure

## Goal
Deploy containerized backend to existing Container Apps Environment.

## Context
- Phase 1 complete: Backend containerized and tested locally
- Reusing existing Container Apps Environment and ACR to minimize costs
- See `docs/specs/implementation-plan.md` for full migration plan

---

## Tasks

### PR 2.1: Push Image to ACR
**Branch**: `feature/acr-push`

- [ ] Document manual deployment steps in `docs/deployment.md`
- [ ] Create deployment script (`scripts/deploy-backend.sh`)
  - Build and tag image
  - Login to ACR
  - Push image
- [ ] Push first image to existing ACR
- [ ] Test: Image visible in ACR portal

**Files**:
- `docs/deployment.md` (create)
- `scripts/deploy-backend.sh` (create)

---

### PR 2.2: Create Container App
**Branch**: `feature/container-app`

- [ ] Create Container App via Azure CLI or Portal
- [ ] Configure environment variables from `.env`
- [ ] Configure secrets for API keys (ADO PAT, Figma token, etc.)
- [ ] Set scale-to-zero (min replicas: 0, max replicas: 1)
- [ ] Update `ALLOWED_ORIGINS` for Container App URL
- [ ] Test: `/health` endpoint accessible from internet
- [ ] Test: `/health/details` shows all connectors working

**Files**:
- `docs/deployment.md` (update with Container App setup)

---

### PR 2.3: Add GitHub Actions CI/CD
**Branch**: `feature/backend-cicd`

- [ ] Create `.github/workflows/deploy-backend.yml`
  - Trigger on push to main (paths: `src/**`, `Dockerfile`)
  - Build Docker image
  - Push to ACR
  - Deploy to Container Apps
- [ ] Add `AZURE_CREDENTIALS` secret to GitHub repo
- [ ] Test: Push to main triggers deployment
- [ ] Test: New code deploys automatically

**Files**:
- `.github/workflows/deploy-backend.yml` (create)
- `docs/deployment.md` (update with CI/CD info)

---

## Definition of Done
- [ ] All 3 PRs merged to main
- [ ] Backend accessible at `https://artifact-search-api.<env>.azurecontainerapps.io`
- [ ] `/health` endpoint responds from internet
- [ ] All 4 connectors working (check `/health/details`)
- [ ] Push to main triggers automatic deployment

---

## Notes
- Need existing ACR name and Container Apps Environment name before starting
- API keys will be configured as Container Apps secrets
- Scale-to-zero means 5-15s cold start delay (acceptable for demo)

## Phase 1 Accomplishments (Complete)
- [x] PR 1.1: Dockerfile and .dockerignore
- [x] PR 1.2: Configurable CORS (`ALLOWED_ORIGINS` env var)
- [x] PR 1.3: Container-ready logging and fast health check
- [x] Container builds and runs locally with all connectors
- [x] `/health` responds in ~10ms (fast for probes)
- [x] `/health/details` provides full connection status

## Session 5 Accomplishments (2026-01-21)
- [x] Completed PR 1.2: Configurable CORS
- [x] Completed PR 1.3: Container-ready logging and fast health check
- [x] Phase 1 complete - ready for Azure deployment
- [ ] **Next**: PR 2.1 (Push Image to ACR)
