# Deployment Guide

This guide covers deploying the artifact-search-skill backend to Azure Container Apps.

## Prerequisites

- Azure CLI installed and logged in (`az login`)
- Docker installed and running
- Access to the Azure subscription with these resources:
  - Resource Group: `factory-agent-dev-rg`
  - Container Registry: `factoryagent4u4zqkacr`
  - Container Apps Environment: `factory-agent-dev-env`

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│              Container Apps Environment                      │
│              (factory-agent-dev-env)                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ artifact-search-api                                  │   │
│  │ FastAPI backend, scale 0-1 replicas                 │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────┐
│  Azure Container Registry   │                               │
│  (factoryagent4u4zqkacr)   │                               │
│  - artifact-search-api:latest                               │
│  - artifact-search-api:<git-sha>                           │
└─────────────────────────────────────────────────────────────┘
```

## Manual Deployment Steps

### 1. Build the Docker Image

From the project root:

```bash
docker build -t artifact-search-api:latest .
```

### 2. Tag for ACR

```bash
docker tag artifact-search-api:latest factoryagent4u4zqkacr.azurecr.io/artifact-search-api:latest
```

Optionally tag with git SHA for versioning:

```bash
GIT_SHA=$(git rev-parse --short HEAD)
docker tag artifact-search-api:latest factoryagent4u4zqkacr.azurecr.io/artifact-search-api:$GIT_SHA
```

### 3. Login to ACR

```bash
az acr login --name factoryagent4u4zqkacr
```

### 4. Push to ACR

```bash
docker push factoryagent4u4zqkacr.azurecr.io/artifact-search-api:latest
docker push factoryagent4u4zqkacr.azurecr.io/artifact-search-api:$GIT_SHA
```

### 5. Verify Upload

```bash
az acr repository show-tags --name factoryagent4u4zqkacr --repository artifact-search-api --output table
```

## Using the Deployment Script

For convenience, use the provided script:

```bash
./scripts/deploy-backend.sh
```

The script will:
1. Build the Docker image
2. Tag with `latest` and current git SHA
3. Login to ACR
4. Push both tags

### Script Options

```bash
# Build and push (default)
./scripts/deploy-backend.sh

# Skip build, just push existing image
./scripts/deploy-backend.sh --push-only
```

## Environment Variables

The Container App requires these environment variables (configured in PR 2.2):

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_DEVOPS_ORG_URL` | Azure DevOps organization URL | Yes |
| `AZURE_DEVOPS_PAT` | Personal Access Token (secret) | Yes |
| `AZURE_DEVOPS_PROJECT` | Project name | Yes |
| `FIGMA_ACCESS_TOKEN` | Figma API token (secret) | Yes |
| `FIGMA_FILE_KEY` | Figma file key | Yes |
| `NOTION_API_KEY` | Notion integration token (secret) | Yes |
| `NOTION_DATABASE_ID` | Notion database ID | Yes |
| `ICEPANEL_API_KEY` | Ice Panel API key (secret) | Yes |
| `ICEPANEL_LANDSCAPE_ID` | Ice Panel landscape ID | Yes |
| `AZURE_AI_ENDPOINT` | Azure OpenAI endpoint | Yes |
| `AZURE_AI_API_KEY` | Azure OpenAI key (secret) | If not using AD auth |
| `AZURE_AI_DEPLOYMENT` | Deployment name (default: gpt-4o) | No |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) | Yes |

## Troubleshooting

### ACR Login Fails

Ensure you're logged into Azure CLI:

```bash
az login
az account show
```

### Push Fails with 401

Re-authenticate to ACR:

```bash
az acr login --name factoryagent4u4zqkacr --expose-token
```

### Image Not Found in ACR

List repositories to verify:

```bash
az acr repository list --name factoryagent4u4zqkacr --output table
```
