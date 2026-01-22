# Current Sprint: Figma Rate Limit Mitigation

## Goal
Improve Figma connector reliability by implementing persistent caching to minimize API calls.

## Context
- Figma API has strict rate limits (as low as 6 requests/month for View seats on Starter plan)
- Current in-memory cache resets when server restarts
- Need persistent cache to survive restarts and reduce API calls

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
- Figma `Retry-After` returned 391867 seconds (~4.5 days) indicating monthly limit hit
- Dev/Full seats have much higher limits (10-150 req/min vs 6/month)
