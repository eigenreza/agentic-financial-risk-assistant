# Azure Container Apps Deployment

This document describes how to deploy the Agentic Financial Risk Assistant to Azure Container Apps, the preferred Azure deployment path for this project. Container Apps provides serverless container hosting with built-in scaling, HTTPS, and managed identity support without requiring you to manage Kubernetes nodes directly.

---

## Required Azure services

| Service | Purpose |
|---|---|
| Azure Container Registry (ACR) | Store and serve the container image |
| Azure Container Apps Environment | Managed Kubernetes-based runtime for containers |
| Azure Container App | The running instance of the Streamlit application |
| Azure Key Vault | Store the `LLM_API_KEY` secret securely |
| Azure Log Analytics Workspace | Container logs and monitoring (created automatically) |

**Estimated cost (consumption plan, low traffic):** < $10/month. Scale to zero when idle. Always use `az group delete` to clean up when done.

---

## Prerequisites

```bash
# Install or update the Azure CLI
winget install Microsoft.AzureCLI          # Windows
# brew install azure-cli                   # macOS

# Install the Container Apps extension
az extension add --name containerapp --upgrade

# Log in
az login
az account set --subscription "<your-subscription-id>"
```

---

## Step-by-step deployment

### 1. Set variables

```bash
RESOURCE_GROUP="financial-risk-rg"
LOCATION="norwayeast"          # or westeurope, eastus, etc.
ACR_NAME="financialriskacr"    # must be globally unique, lowercase, alphanumeric
ENVIRONMENT="financial-risk-env"
APP_NAME="financial-risk-assistant"
IMAGE_TAG="1.0"
KEY_VAULT_NAME="financial-risk-kv"
```

### 2. Create resource group

```bash
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION
```

### 3. Create Azure Container Registry and build image

```bash
az acr create \
  --name $ACR_NAME \
  --resource-group $RESOURCE_GROUP \
  --sku Basic \
  --admin-enabled true

# Build and push directly from source (no local Docker required)
az acr build \
  --registry $ACR_NAME \
  --image financial-risk-assistant:$IMAGE_TAG \
  .
```

### 4. Create Key Vault and store API key

```bash
az keyvault create \
  --name $KEY_VAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name llm-api-key \
  --value "<your-llm-api-key>"
```

### 5. Create Container Apps environment

```bash
az containerapp env create \
  --name $ENVIRONMENT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION
```

### 6. Deploy the Container App

```bash
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)
API_KEY=$(az keyvault secret show --vault-name $KEY_VAULT_NAME --name llm-api-key --query value -o tsv)

az containerapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT \
  --image "$ACR_NAME.azurecr.io/financial-risk-assistant:$IMAGE_TAG" \
  --registry-server "$ACR_NAME.azurecr.io" \
  --registry-username $ACR_NAME \
  --registry-password $ACR_PASSWORD \
  --target-port 8501 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --env-vars \
      LLM_API_KEY="$API_KEY" \
      STREAMLIT_SERVER_HEADLESS=true \
      STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

### 7. Retrieve the public URL

```bash
az containerapp show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn \
  -o tsv
```

The app will be available at `https://<fqdn>` with a free Azure-managed TLS certificate.

---

## Scaling configuration

The deployment above uses the consumption plan with:

- **Min replicas: 0**, scales to zero when idle (no traffic = no cost)
- **Max replicas: 3**, scales up under load
- **CPU: 0.5 vCPU, Memory: 1 Gi**, sufficient for the Streamlit app with FAISS and sentence-transformers

To keep the app always warm (avoid cold start):

```bash
az containerapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --min-replicas 1
```

---

## Updating the deployment

```bash
# Build and push new image
az acr build --registry $ACR_NAME --image financial-risk-assistant:1.1 .

# Update the running app
az containerapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --image "$ACR_NAME.azurecr.io/financial-risk-assistant:1.1"
```

Container Apps performs a zero-downtime rolling update automatically.

---

## Viewing logs

```bash
az containerapp logs show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --follow
```

---

## Cleanup, important

```bash
az group delete --name $RESOURCE_GROUP --yes --no-wait
```

This deletes all resources including the ACR, Key Vault, Container Apps environment, and the app itself.

---

## Production hardening checklist

- [ ] Use managed identity instead of ACR admin credentials
- [ ] Reference Key Vault secrets via managed identity (not raw env var)
- [ ] Enable Azure Monitor alerts on HTTP 5xx errors
- [ ] Set up Azure Front Door or CDN if global latency matters
- [ ] Pin the image tag (not `latest`) in production
- [ ] Enable Container Apps Dapr sidecar if adding service-to-service communication
- [ ] Set `--revision-suffix` on each update to keep a rollback target
