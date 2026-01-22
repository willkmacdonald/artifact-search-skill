#!/usr/bin/env bash
#
# Deploy backend image to Azure Container Registry
#
# Usage:
#   ./scripts/deploy-backend.sh           # Build and push
#   ./scripts/deploy-backend.sh --push-only  # Push existing image only
#

set -euo pipefail

# Configuration
ACR_NAME="factoryagent4u4zqkacr"
ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"
IMAGE_NAME="artifact-search-api"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse arguments
PUSH_ONLY=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --push-only)
            PUSH_ONLY=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--push-only]"
            echo ""
            echo "Options:"
            echo "  --push-only  Skip build, only push existing image"
            echo "  -h, --help   Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Get git SHA for tagging
GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
log_info "Git SHA: $GIT_SHA"

# Build image
if [[ "$PUSH_ONLY" == "false" ]]; then
    log_info "Building Docker image..."
    cd "$PROJECT_ROOT"
    docker build -t "${IMAGE_NAME}:latest" .
    log_info "Build complete"
else
    log_info "Skipping build (--push-only)"
fi

# Tag for ACR
log_info "Tagging image for ACR..."
docker tag "${IMAGE_NAME}:latest" "${ACR_LOGIN_SERVER}/${IMAGE_NAME}:latest"
docker tag "${IMAGE_NAME}:latest" "${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${GIT_SHA}"

# Login to ACR
log_info "Logging into ACR..."
az acr login --name "$ACR_NAME"

# Push images
log_info "Pushing ${ACR_LOGIN_SERVER}/${IMAGE_NAME}:latest..."
docker push "${ACR_LOGIN_SERVER}/${IMAGE_NAME}:latest"

log_info "Pushing ${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${GIT_SHA}..."
docker push "${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${GIT_SHA}"

# Verify
log_info "Verifying upload..."
az acr repository show-tags --name "$ACR_NAME" --repository "$IMAGE_NAME" --output table

log_info "Deployment complete!"
echo ""
echo "Image pushed:"
echo "  ${ACR_LOGIN_SERVER}/${IMAGE_NAME}:latest"
echo "  ${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${GIT_SHA}"
