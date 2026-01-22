# Current Sprint: Figma Rate Limit Mitigation

## Goal
Improve Figma connector reliability by implementing persistent caching to minimize API calls.

## Context
- Figma API has strict rate limits (as low as 6 requests/month for View seats on Starter plan)
- Current in-memory cache resets when server restarts
- Need persistent cache to survive restarts and reduce API calls
- **UPDATE**: User upgraded to Dev seat on Professional plan (10 req/min) - rate limits no longer blocking

## Tasks

### PR 1: Persistent File Cache for Figma
- [ ] Add file-based cache for Figma file data (JSON on disk)
- [ ] Cache invalidation based on `lastModified` timestamp
- [ ] Only fetch from API if cache is missing or stale
- [ ] Add cache TTL configuration via environment variable

### PR 2: Startup Cache Warming (Optional)
- [ ] Pre-fetch Figma file data on server startup
- [ ] Store in persistent cache before any searches
- [ ] Reduces chance of hitting rate limits during demo

### PR 3: Consider Figma MCP Alternative
- [ ] Research Figma MCP server rate limits
- [ ] Evaluate if MCP provides better access than REST API
- [ ] Document findings for future decision

## Notes
- Current in-memory cache TTL: 5 minutes
- User upgraded to Figma Dev seat (Professional) - now has 10 req/min for Tier 1 endpoints
- Persistent caching still valuable to reduce API calls and improve reliability
- All 4 connectors now working: Azure DevOps, Figma, Ice Panel, Notion

## Session 2 Accomplishments (2026-01-21)
- [x] Fixed all 4 connectors (Azure DevOps, Figma, Ice Panel, Notion)
- [x] Added retry/caching to Figma connector
- [x] Fixed Ice Panel API paths
- [x] Fixed Notion title property detection
- [x] Ran pr-reviewer and fixed CRITICAL/IMPORTANT issues
- [x] Pushed all code to GitHub
