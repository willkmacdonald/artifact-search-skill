# Production Bill of Materials — Artifact Search Skill

## Current State (Hobby/Demo)

Today this runs on shared "dev" resources (Container Apps Environment, ACR, Resource Group all prefixed `factory-agent-dev-*`), no user authentication, no WAF, scale 0-1, API keys as Container App env vars.

---

## 1. Compute

| Component | Current | Production | Notes |
|-----------|---------|-----------|-------|
| Backend API | Azure Container Apps (0.25 CPU, 0.5Gi, scale 0-1) | Azure Container Apps (0.5 CPU, 1Gi, scale 1-3) | Min 1 to eliminate cold starts |
| Frontend | Azure Static Web Apps (Free tier) | Azure Static Web Apps (Standard tier) | Custom domain, SLA, staging environments |
| Container Registry | Shared ACR (Basic) | Dedicated ACR (Standard) | Geo-replication optional, vulnerability scanning |

## 2. Networking & Ingress

| Component | Current | Production | Notes |
|-----------|---------|-----------|-------|
| Custom domain (frontend) | artifact-search.willmacdonald.com | Same or org domain | Already configured with managed TLS |
| Custom domain (backend) | Default .azurecontainerapps.io FQDN | Custom domain with managed cert | Professional URL, independent of Azure naming |
| Azure Front Door / WAF | None | Azure Front Door (Standard) + WAF policy | DDoS protection, rate limiting, geo-filtering, bot protection |
| Private networking | Public ingress | VNET-integrated Container Apps Environment | Backend not directly internet-exposed; traffic routed through Front Door |
| DNS | External DNS provider | Azure DNS zone (or existing) | Centralized DNS management, easy cert validation |
| CORS policy | Env var (ALLOWED_ORIGINS) | Same, but locked to production domain only | Remove localhost origins |

## 3. Identity & Authentication

| Component | Current | Production | Notes |
|-----------|---------|-----------|-------|
| User authentication | None (public) | Azure AD / Entra ID (MSAL) | SSO for internal users; block public access |
| Backend auth | None | API requires valid JWT from Azure AD | Protects search/chat endpoints |
| Frontend auth | None | Static Web Apps built-in auth (Azure AD provider) | Or custom MSAL.js integration |
| Managed Identity | User-assigned (ACR pull only) | System-assigned MI for all Azure service access | Replaces API keys wherever possible |
| Service Principal | AZURE_CREDENTIALS secret in GitHub | Same, but with minimum-privilege role | Scoped to resource group only |

## 4. Secrets & Configuration Management

| Component | Current | Production | Notes |
|-----------|---------|-----------|-------|
| API keys/tokens | Container App environment variables (plaintext) | Azure Key Vault | All secrets stored in Key Vault, referenced via managed identity |
| Key Vault | Does not exist | Azure Key Vault (Standard) | Store: ADO PAT, Figma token, Notion key, IcePanel key, Azure AI key |
| Config management | .env file / Container App env vars | Key Vault refs + Container App env vars (non-sensitive only) | Separation of secrets from config |
| Secret rotation | Manual | Key Vault rotation policy + alerts | Automated rotation where APIs support it |

## 5. Observability & Monitoring

| Component | Current | Production | Notes |
|-----------|---------|-----------|-------|
| Application monitoring | None (logs only) | Azure Application Insights | Request tracing, dependency tracking, failure alerts |
| Log aggregation | Container Apps system logs | Azure Log Analytics Workspace | Centralized log queries, retention policy |
| OpenTelemetry | Not implemented | Add opentelemetry-sdk + Azure exporter | Distributed tracing across connectors |
| Alerts | None | Azure Monitor alert rules | P1: health check failures, 5xx spike, high latency (>10s), connector failures |
| Dashboard | None | Azure Dashboard or Grafana | Key metrics: request rate, latency P50/P95, error rate, connector health |
| Uptime monitoring | None | Azure Availability Test (or external like Pingdom) | Synthetic /health pings every 5 min |

## 6. CI/CD & Release Management

| Component | Current | Production | Notes |
|-----------|---------|-----------|-------|
| Pipeline | GitHub Actions (build + deploy on push to main) | Same, but with staged deployment | Add: lint, test, build, deploy-staging, smoke-test, deploy-prod |
| Environments | Single (prod) | Staging + Production | Separate Container Apps, separate config |
| Test gate | None | pytest + coverage gate in CI | Block deploy if tests fail or coverage drops |
| Image scanning | None | ACR vulnerability scanning (Defender for Containers) or Trivy in CI | Block deploy on critical CVEs |
| Rollback | Manual (az containerapp update to previous image) | Container Apps revision management | Keep last 3 revisions, traffic splitting for canary |
| Branch protection | Bypassed (solo dev) | Require PR + passing checks for main | Even solo, prevents accidental force-pushes |

## 7. Data Security & Compliance

| Component | Current | Production | Notes |
|-----------|---------|-----------|-------|
| Data classification | Not documented | Document data flows - search queries, artifact metadata | MedTech context may involve regulated data |
| Encryption at rest | Azure defaults (platform-managed keys) | Sufficient for most cases; CMK if compliance requires | Container Apps + Key Vault already encrypted at rest |
| Encryption in transit | TLS (managed certs) | TLS 1.2+ enforced (already default on Azure) | Verify no HTTP fallback |
| Audit logging | None | Azure Activity Log + Key Vault diagnostic logs | Who accessed what, when |
| Data residency | East US | Confirm region meets compliance needs | All resources in same region |
| PII/PHI handling | Search queries could contain sensitive terms | Add query sanitization/logging policy | Don't log full queries if they contain patient data |

## 8. External Service Hardening

| Service | Current Auth | Production Auth | Additional Hardening |
|---------|-------------|----------------|---------------------|
| Azure DevOps | PAT (personal) | PAT scoped to read-only, or Managed Identity with Azure AD | Rotate PAT every 90 days; use service account, not personal |
| Figma | Personal access token | Same (no service accounts available) | Rotate token; monitor API usage |
| Notion | Integration token | Same (Notion doesn't support MI) | Scope integration to specific database only |
| Ice Panel | API key | Same | Rotate regularly |
| Azure OpenAI | API key or AD auth | Managed Identity only (drop API key) | Remove AZURE_AI_API_KEY; use MI with Cognitive Services OpenAI User role |

## 9. Disaster Recovery & Reliability

| Component | Current | Production | Notes |
|-----------|---------|-----------|-------|
| Availability target | Best-effort | 99.5% (Container Apps SLA) | Documented SLA for internal users |
| Backup | N/A (stateless) | N/A - no persistent state to back up | Advantage of stateless architecture |
| Multi-region | Single region (East US) | Not required unless >99.9% SLA needed | Could add Front Door with failover |
| Incident response | None | Alert - on-call - runbook | Basic runbook for common failures (connector down, cold start, etc.) |
| Health probes | /health endpoint | Same + per-connector circuit breakers | Prevent cascading failures if one source is down |

## 10. Cost Estimate (Monthly, USD)

| Resource | Tier | Est. Cost/month |
|----------|------|-----------------|
| Container Apps (0.5 CPU, 1Gi, always-on) | Consumption | $15-30 |
| Container Registry (Standard) | Standard | $5 |
| Static Web Apps | Standard | $9 |
| Azure Front Door + WAF | Standard | $35 |
| Key Vault | Standard | $1 |
| Application Insights | Pay-as-you-go | $5-10 |
| Log Analytics | 5GB/month free, then $2.76/GB | $0-5 |
| Azure OpenAI (GPT-4o) | Pay-per-token | $10-50 |
| DNS Zone | Per zone + queries | $1 |
| Staging environment | Duplicate of compute | $25-40 |
| **Total estimate** | | **$100-190** |

Current cost is likely ~$15-25/month with scale-to-zero and free tiers.

## 11. Priority Order for Implementation

| Priority | Item | Rationale |
|----------|------|-----------|
| 1 | Key Vault | Get secrets out of plaintext env vars (highest security impact, lowest effort) |
| 2 | User authentication | Azure AD on frontend + backend (blocks unauthorized access) |
| 3 | Application Insights + alerts | Visibility into failures before users report them |
| 4 | Staging environment | Stop deploying untested changes directly to prod |
| 5 | Tests + CI gate | Prevent regressions |
| 6 | Front Door + WAF | Network-level protection |
| 7 | VNET integration | Defense in depth |
| 8 | Image scanning | Supply chain security |
| 9 | Audit logging + compliance docs | If MedTech regulatory requirements apply |
