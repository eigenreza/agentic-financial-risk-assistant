#!/usr/bin/env bash
# =============================================================================
# Azure CLI deployment script, Agentic Financial Risk Assistant
# Deploys to Azure Container Apps (consumption plan)
#
# Usage:
#   chmod +x azure_cli_commands.sh
#   ./azure_cli_commands.sh
#
# Prerequisites:
#   - Azure CLI installed and logged in (az login)
#   - Container Apps extension: az extension add --name containerapp --upgrade
#   - LLM_API_KEY set in environment, or edit the variable below
# =============================================================================

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
RESOURCE_GROUP="financial-risk-rg"
LOCATION="norwayeast"
ACR_NAME="financialriskacr"        # must be globally unique, lowercase, alphanumeric
ENVIRONMENT="financial-risk-env"
APP_NAME="financial-risk-assistant"
IMAGE_TAG="1.0"
KEY_VAULT_NAME="financial-risk-kv"

# Read API key from environment, never hardcode it here
: "${LLM_API_KEY:?ERROR: LLM_API_KEY environment variable is not set}"

echo "=== Azure Financial Risk Assistant Deployment ==="
echo "Resource group : $RESOURCE_GROUP"
echo "Location       : $LOCATION"
echo "ACR name       : $ACR_NAME"
echo "App name       : $APP_NAME"
echo ""

# ── 1. Resource group ─────────────────────────────────────────────────────────
echo "--- Creating resource group ---"
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --output table

# ── 2. Azure Container Registry ───────────────────────────────────────────────
echo "--- Creating Azure Container Registry ---"
az acr create \
  --name "$ACR_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --sku Basic \
  --admin-enabled true \
  --output table

echo "--- Building and pushing image (runs in Azure, no local Docker required) ---"
# Run from the project root (two levels up from this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

az acr build \
  --registry "$ACR_NAME" \
  --image "financial-risk-assistant:$IMAGE_TAG" \
  "$PROJECT_ROOT"

# ── 3. Key Vault ──────────────────────────────────────────────────────────────
echo "--- Creating Key Vault ---"
az keyvault create \
  --name "$KEY_VAULT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --output table

echo "--- Storing API key in Key Vault ---"
az keyvault secret set \
  --vault-name "$KEY_VAULT_NAME" \
  --name "llm-api-key" \
  --value "$LLM_API_KEY" \
  --output none

echo "API key stored. It will never appear in logs or shell history after this point."

# ── 4. Container Apps environment ─────────────────────────────────────────────
echo "--- Creating Container Apps environment ---"
az containerapp env create \
  --name "$ENVIRONMENT" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --output table

# ── 5. Deploy Container App ───────────────────────────────────────────────────
echo "--- Deploying Container App ---"
ACR_PASSWORD=$(az acr credential show \
  --name "$ACR_NAME" \
  --query "passwords[0].value" \
  --output tsv)

STORED_API_KEY=$(az keyvault secret show \
  --vault-name "$KEY_VAULT_NAME" \
  --name "llm-api-key" \
  --query "value" \
  --output tsv)

az containerapp create \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --environment "$ENVIRONMENT" \
  --image "$ACR_NAME.azurecr.io/financial-risk-assistant:$IMAGE_TAG" \
  --registry-server "$ACR_NAME.azurecr.io" \
  --registry-username "$ACR_NAME" \
  --registry-password "$ACR_PASSWORD" \
  --target-port 8501 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --env-vars \
      "LLM_API_KEY=$STORED_API_KEY" \
      "STREAMLIT_SERVER_HEADLESS=true" \
      "STREAMLIT_BROWSER_GATHER_USAGE_STATS=false" \
  --output table

# ── 6. Retrieve URL ───────────────────────────────────────────────────────────
echo ""
echo "=== Deployment complete ==="
FQDN=$(az containerapp show \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.configuration.ingress.fqdn" \
  --output tsv)

echo "App URL: https://$FQDN"
echo ""
echo "To stream logs:"
echo "  az containerapp logs show --name $APP_NAME --resource-group $RESOURCE_GROUP --follow"
echo ""
echo "To clean up ALL resources:"
echo "  az group delete --name $RESOURCE_GROUP --yes --no-wait"
