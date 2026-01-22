# Current Sprint: Phase 4 - Production Hardening (Optional)

## Goal
Add observability and improve reliability for ongoing demos.

## Context
- Phases 1-3 complete: Full deployment pipeline working
- Frontend: https://artifact-search.willmacdonald.com
- Backend: https://artifact-search-api.mangotree-f82b3c1f.eastus.azurecontainerapps.io
- CI/CD: Push to main auto-deploys both frontend and backend

---

## Tasks

### PR 4.1: Add Application Insights
- [ ] Integrate OpenTelemetry with Azure Monitor
- [ ] Add request tracing and error logging
- [ ] Test: View traces in Azure Portal

**Files**:
- `src/artifact_search/telemetry.py` (create)
- `src/artifact_search/api.py` (update with tracing)
- `requirements.txt` (add opentelemetry packages)

---

### PR 4.2: Documentation Update
- [ ] Update README with deployment instructions
- [ ] Add architecture diagram
- [ ] Document environment variables

**Files**:
- `README.md` (update)
- `docs/deployment.md` (update)

---

## Definition of Done
- [ ] Both PRs merged to main
- [ ] Traces visible in Azure Portal
- [ ] README has current deployment info

---

## Notes
- This phase is optional - the app is fully functional
- Application Insights helps debug issues in production
- Documentation helps future maintenance

## Previous Phase Accomplishments

### Session 6 (2026-01-22): Phases 2 & 3 Complete
- [x] Fixed GitHub Actions auth (azure/login@v1 for JSON credentials)
- [x] Created new Service Principal with contributor role
- [x] Backend CI/CD working - push to main deploys automatically
- [x] Configured Next.js for static export
- [x] Created Azure Static Web App
- [x] Frontend CI/CD working via SWA GitHub integration
- [x] Custom domain configured: artifact-search.willmacdonald.com
- [x] CORS configured for all domains
