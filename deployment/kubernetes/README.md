# Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the Agentic Financial Risk Assistant. The manifests are production-ready templates, substitute your container registry, domain name, and namespace before applying.

---

## Files

| File | Kind | Purpose |
|---|---|---|
| `deployment.yaml` | `Deployment` | 2-replica app deployment with resource limits, health probes, rolling update strategy, and security context |
| `service.yaml` | `Service` | `ClusterIP` service mapping port 80 → container port 8501 |
| `ingress.yaml` | `Ingress` | nginx Ingress with WebSocket support (required for Streamlit), HTTPS redirect, optional TLS via cert-manager |
| `hpa.yaml` | `HorizontalPodAutoscaler` | Auto-scales 2–8 replicas based on CPU (70%) and memory (80%) |

---

## Prerequisites

- Kubernetes cluster (local: `minikube` / `kind`, cloud: AKS, EKS, GKE)
- `kubectl` configured against the target cluster
- Container image pushed to a registry accessible from the cluster
- nginx Ingress controller installed (`kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml`)
- (Optional) `cert-manager` for automatic TLS

---

## Quick start

### 1. Build and push the image

```bash
# Build
docker build -t agentic-financial-risk-assistant:1.0 .

# Tag and push to your registry (example: Docker Hub)
docker tag agentic-financial-risk-assistant:1.0 yourusername/financial-risk-assistant:1.0
docker push yourusername/financial-risk-assistant:1.0

# Or push to Azure Container Registry
az acr build --registry <acrname> --image financial-risk-assistant:1.0 .
```

### 2. Create the API key Secret

```bash
kubectl create secret generic llm-api-key \
  --from-literal=api-key=your_llm_api_key_here
```

The app runs in deterministic fallback mode if this Secret is absent.

### 3. Update the image reference

In `deployment.yaml`, replace:
```yaml
image: agentic-financial-risk-assistant:latest
```
with your registry path:
```yaml
image: yourusername/financial-risk-assistant:1.0
# or:
image: acrname.azurecr.io/financial-risk-assistant:1.0
```

### 4. Update the Ingress hostname

In `ingress.yaml`, replace:
```yaml
host: risk-assistant.yourdomain.com
```
with your actual domain.

### 5. Apply all manifests

```bash
kubectl apply -f deployment/kubernetes/
```

### 6. Check rollout status

```bash
kubectl rollout status deployment/financial-risk-assistant
kubectl get pods -l app=financial-risk-assistant
kubectl get svc financial-risk-assistant
kubectl get ingress financial-risk-assistant
```

---

## Checking the HPA

```bash
# View current scaling state
kubectl get hpa financial-risk-assistant

# Watch live
kubectl get hpa financial-risk-assistant --watch
```

The HPA scales between 2 and 8 replicas based on CPU (target 70%) and memory (target 80%). Scale-up is capped at 2 pods/minute; scale-down at 1 pod/2 minutes with a 5-minute stabilisation window to prevent flapping.

---

## Tearing down

```bash
kubectl delete -f deployment/kubernetes/
kubectl delete secret llm-api-key
```

---

## Mapping to Azure Kubernetes Service (AKS)

These manifests apply directly to an AKS cluster with no changes. AKS-specific extensions:

| Feature | AKS approach |
|---|---|
| Container registry | Azure Container Registry (ACR), attach to AKS with `az aks update --attach-acr` |
| Ingress | Application Gateway Ingress Controller (AGIC) or nginx on AKS |
| TLS | cert-manager with Let's Encrypt, or Azure-managed certificates via AGIC |
| Secrets | Azure Key Vault + Secrets Store CSI Driver (replaces Kubernetes Secret) |
| Scaling | KEDA for event-driven scaling; Cluster Autoscaler for node-level scaling |
| Monitoring | Azure Monitor + Container Insights (`az aks enable-addons --addons monitoring`) |
| Identity | Azure Workload Identity for pod-level access to ACR and Key Vault |

See `deployment/azure/aks_extension_note.md` for step-by-step AKS deployment instructions.

---

## Production extensions

- **PersistentVolumeClaim for FAISS index**, replace `emptyDir` in `deployment.yaml` with a PVC backed by Azure Files or Azure Disk so the index survives pod restarts without rebuilding
- **NetworkPolicy**, restrict pod-to-pod traffic to only what is needed
- **PodDisruptionBudget**, ensure at least 1 pod stays available during node maintenance
- **Resource quotas**, apply namespace-level quotas to prevent resource starvation
- **Multi-region deployment**, use Azure Traffic Manager or Azure Front Door to distribute across regions
