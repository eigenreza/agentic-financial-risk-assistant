# AKS Extension Note

This document explains how the Kubernetes manifests in `deployment/kubernetes/` map directly to Azure Kubernetes Service (AKS) and what AKS-specific steps are needed to deploy the application.

---

## What AKS is

Azure Kubernetes Service (AKS) is Microsoft's managed Kubernetes offering. It handles the Kubernetes control plane (API server, etcd, scheduler) as a fully managed Azure service — you provision and manage only the worker nodes. The Kubernetes manifests in `deployment/kubernetes/` work on AKS without modification.

---

## Step-by-step: deploy to AKS

### 1. Create AKS cluster

```bash
RESOURCE_GROUP="financial-risk-rg"
CLUSTER_NAME="financial-risk-aks"
LOCATION="norwayeast"
ACR_NAME="financialriskacr"

az group create --name $RESOURCE_GROUP --location $LOCATION

az aks create \
  --name $CLUSTER_NAME \
  --resource-group $RESOURCE_GROUP \
  --node-count 2 \
  --node-vm-size Standard_D2s_v3 \
  --generate-ssh-keys \
  --attach-acr $ACR_NAME      # grants AKS pull access to your ACR
```

### 2. Get credentials

```bash
az aks get-credentials \
  --name $CLUSTER_NAME \
  --resource-group $RESOURCE_GROUP

kubectl get nodes   # verify cluster is reachable
```

### 3. Build and push image to ACR

```bash
az acr build \
  --registry $ACR_NAME \
  --image financial-risk-assistant:1.0 \
  .
```

### 4. Install nginx Ingress controller

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
```

AKS automatically provisions an Azure Load Balancer and assigns a public IP when this is applied.

### 5. Create the API key Secret

```bash
kubectl create secret generic anthropic-api-key \
  --from-literal=api-key=<your-anthropic-api-key>
```

### 6. Update image reference in deployment.yaml

```yaml
# deployment/kubernetes/deployment.yaml
image: financialriskacr.azurecr.io/financial-risk-assistant:1.0
imagePullPolicy: Always
```

### 7. Apply manifests

```bash
kubectl apply -f deployment/kubernetes/
kubectl rollout status deployment/financial-risk-assistant
```

### 8. Get the external IP

```bash
kubectl get svc -n ingress-nginx ingress-nginx-controller
# EXTERNAL-IP is your Azure Load Balancer public IP
```

Update your DNS to point `risk-assistant.yourdomain.com` at this IP, then HTTPS will be handled by cert-manager or Azure-managed certificates.

---

## AKS-specific enhancements

### Attach ACR with managed identity (no password needed)

```bash
az aks update \
  --name $CLUSTER_NAME \
  --resource-group $RESOURCE_GROUP \
  --attach-acr $ACR_NAME
```

Remove `registry-username` / `registry-password` from the deployment — AKS uses its managed identity to pull from ACR automatically.

### Use Azure Key Vault for secrets (Secrets Store CSI Driver)

```bash
# Enable the add-on
az aks enable-addons \
  --name $CLUSTER_NAME \
  --resource-group $RESOURCE_GROUP \
  --addons azure-keyvault-secrets-provider

# Grant AKS managed identity access to Key Vault
az keyvault set-policy \
  --name $KEY_VAULT_NAME \
  --object-id $(az aks show -n $CLUSTER_NAME -g $RESOURCE_GROUP \
      --query addonProfiles.azureKeyvaultSecretsProvider.identity.objectId -o tsv) \
  --secret-permissions get
```

Then reference the secret via a `SecretProviderClass` instead of a Kubernetes Secret.

### Enable Azure Monitor for containers

```bash
az aks enable-addons \
  --name $CLUSTER_NAME \
  --resource-group $RESOURCE_GROUP \
  --addons monitoring
```

This streams container logs, pod metrics, and node metrics to Azure Log Analytics — visible in the Azure Portal under the cluster's "Insights" tab.

### Enable cluster autoscaler

```bash
az aks update \
  --name $CLUSTER_NAME \
  --resource-group $RESOURCE_GROUP \
  --enable-cluster-autoscaler \
  --min-count 1 \
  --max-count 5
```

The cluster autoscaler adds or removes nodes in response to the HPA scaling pods. Together they provide full vertical and horizontal auto-scaling.

---

## How the Kubernetes manifests map to AKS

| Manifest element | AKS equivalent |
|---|---|
| `Deployment` + `HPA` | Standard Kubernetes on AKS — no changes needed |
| `Service` (ClusterIP) | Internal cluster service — no changes needed |
| `Ingress` (nginx) | Azure Load Balancer + nginx Ingress controller |
| `ANTHROPIC_API_KEY` Secret | Azure Key Vault via Secrets Store CSI Driver (recommended) or plain Kubernetes Secret |
| `emptyDir` FAISS volume | Azure Files PVC (persistent) or Azure Disk PVC for single-replica |
| Image reference | ACR image path: `acrname.azurecr.io/financial-risk-assistant:1.0` |
| Registry pull | AKS managed identity attached to ACR — no `imagePullSecrets` needed |

---

## Teardown

```bash
az group delete --name $RESOURCE_GROUP --yes --no-wait
```

This deletes the AKS cluster, ACR, all nodes, load balancers, and associated resources.
