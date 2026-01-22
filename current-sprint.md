# Current Sprint: Phase 1 - Containerize Backend

## Goal
Get the FastAPI backend running in a Docker container, ready for Azure deployment.

## Context
- Migrating artifact-search-skill to Azure for demo hosting
- Reusing existing Container Apps Environment and ACR to minimize costs
- See `docs/specs/implementation-plan.md` for full migration plan

---

## Tasks

### PR 1.1: Create Dockerfile and .dockerignore
**Branch**: `feature/dockerfile`

- [ ] Create `Dockerfile` (multi-stage: builder + runtime)
  - Python 3.11-slim base image
  - Install dependencies in builder stage
  - Copy only `src/` to runtime stage
  - Non-root user for security
  - Health check command
  - CMD: uvicorn with `--host 0.0.0.0`
- [ ] Create `.dockerignore`
  - Exclude: `.git`, `venv/`, `.env`, `frontend/`, `tests/`, `*.md`, `sample_data/`
- [ ] Test locally: `docker build -t artifact-search-api .`
- [ ] Test locally: `docker run -p 8000:8000 --env-file .env artifact-search-api`
- [ ] Verify `/health` endpoint works

**Files**:
- `Dockerfile` (create)
- `.dockerignore` (create)

---

### PR 1.2: Make CORS Configurable
**Branch**: `feature/configurable-cors`

- [ ] Add `ALLOWED_ORIGINS` env var support to `api.py`
- [ ] Default to `http://localhost:3000,http://127.0.0.1:3000`
- [ ] Parse comma-separated string into list
- [ ] Test: Frontend still works with default config
- [ ] Test: Can override via environment variable

**Files**:
- `src/artifact_search/api.py` (modify lines 40-47)

---

### PR 1.3: Container-Ready Logging and Health
**Branch**: `feature/container-ready`

- [ ] Add startup banner log with version/config info
- [ ] Ensure `/health` is fast (no slow operations)
- [ ] Add `close()` method cleanup logging
- [ ] Test: Container logs show startup info
- [ ] Test: Health check responds < 1 second

**Files**:
- `src/artifact_search/api.py` (modify)
- `src/artifact_search/__init__.py` (add version if needed)

---

## Definition of Done
- [ ] All 3 PRs merged to main
- [ ] Docker container builds successfully
- [ ] Container runs locally with all connectors working
- [ ] Frontend connects to containerized backend
- [ ] Ready to push image to Azure Container Registry

---

## Notes
- Previous sprint work (Figma caching) deprioritized - rate limits no longer blocking
- Focus is on deployment infrastructure, not feature development
- Keep changes minimal to reduce risk

## Session 3 Accomplishments (2026-01-21)
- [x] Created Azure migration plan (`docs/specs/implementation-plan.md`)
- [x] Created backend architecture spec (`docs/specs/backend-design.md`)
- [x] Created frontend architecture spec (`docs/specs/frontend-design.md`)
- [x] Created project-local `/load-context` skill (`.claude/skills/load-context.md`)
- [x] Broke Phase 1 into 3 PR-sized tasks
- [ ] **Next**: Start PR 1.1 (Dockerfile)

## Previous Sprint Accomplishments
- [x] Fixed all 4 connectors (Azure DevOps, Figma, Ice Panel, Notion)
- [x] Added retry/caching to Figma connector
- [x] Ran pr-reviewer and fixed CRITICAL/IMPORTANT issues
- [x] Pushed all code to GitHub
