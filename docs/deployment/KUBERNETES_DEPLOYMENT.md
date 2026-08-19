# CodeFlow Engine - Kubernetes Deployment Guide

This guide covers deploying CodeFlow Engine to Kubernetes, including Azure Kubernetes Service (AKS), Google Kubernetes Engine (GKE), and Amazon EKS.

---

## Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured and connected to cluster
- Docker image built and pushed to container registry
- PostgreSQL database (managed or in-cluster)
- Redis cache (managed or in-cluster)
- Helm 3.x (optional, for Helm deployment)

---

## Architecture

```text
┌─────────────────────────────────────────┐
│         Kubernetes Cluster              │
│                                         │
│  ┌──────────────┐  ┌──────────────┐   │
│  │   Service    │  │   Ingress    │   │
│  │  (LoadBal)   │  │  (NGINX/ALB) │   │
│  └──────┬───────┘  └──────┬───────┘   │
│         │                 │            │
│  ┌──────▼─────────────────▼──────┐   │
│  │   Deployment (codeflow-engine) │   │
│  │   Replicas: 3                  │   │
│  └──────┬─────────────────────────┘   │
│         │                              │
│  ┌──────▼──────────┐  ┌─────────────┐│
│  │  ConfigMap      │  │   Secrets   ││
│  │  (non-sensitive)│  │  (sensitive)││
│  └─────────────────┘  └─────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │  Worker Deployment (codeflow-worker)││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
         │                    │
    ┌────▼────┐          ┌────▼────┐
    │PostgreSQL│          │  Redis  │
    │(External)│          │(External)│
    └─────────┘          └─────────┘
```

---

## Quick Deployment (15 minutes)

### Step 1: Prepare Kubernetes Resources

```bash
# Clone infrastructure repository
git clone https://github.com/JustAGhosT/codeflow-infrastructure.git
cd codeflow-infrastructure/kubernetes
```

### Step 2: Create Namespace

```bash
kubectl create namespace codeflow
kubectl config set-context --current --namespace=codeflow
```

### Step 3: Create Secrets

```bash
# Create secrets file
cat > secrets.yaml <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: codeflow-secrets
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:password@postgres-host:5432/codeflow"
  REDIS_URL: "redis://redis-host:6379/0"
  GITHUB_TOKEN: "your_github_token"
  OPENAI_API_KEY: "your_openai_key"
  ANTHROPIC_API_KEY: "your_anthropic_key"
EOF

# Apply secrets
kubectl apply -f secrets.yaml
```

### Step 4: Update ConfigMap

```bash
# Edit configmap.yaml
kubectl edit configmap codeflow-config -n codeflow
```

Set environment variables:

- `CODEFLOW_ENV`: production
- `CODEFLOW_LOG_LEVEL`: INFO

### Step 5: Deploy

```bash
# Deploy using kubectl
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# Or use kustomize
kubectl apply -k .
```

### Step 6: Verify Deployment

```bash
# Check pods
kubectl get pods -n codeflow

# Check service
kubectl get svc -n codeflow

# Check logs
kubectl logs -f deployment/codeflow-engine -n codeflow
```

---

## Detailed Deployment Steps

### 1. Container Registry Setup

#### Azure Container Registry (ACR)

```bash
# Login to ACR
az acr login --name codeflowacr

# Build and push image
docker build -t codeflowacr.azurecr.io/codeflow-engine:1.0.1 .
docker push codeflowacr.azurecr.io/codeflow-engine:1.0.1

# Create Kubernetes secret for ACR
kubectl create secret docker-registry acr-secret \
  --docker-server=codeflowacr.azurecr.io \
  --docker-username=<service-principal-id> \
  --docker-password=<service-principal-password> \
  --namespace=codeflow
```

#### Docker Hub

```bash
# Build and push
docker build -t yourusername/codeflow-engine:1.0.1 .
docker push yourusername/codeflow-engine:1.0.1

# Update deployment.yaml image
sed -i 's|codeflowacr.azurecr.io/codeflow-engine|yourusername/codeflow-engine|g' deployment.yaml
```

### 2. Database Setup

#### External PostgreSQL

```bash
# Update DATABASE_URL in secrets.yaml
DATABASE_URL: "postgresql://user:password@postgres.example.com:5432/codeflow"
```

#### In-Cluster PostgreSQL (PostgreSQL Operator)

```bash
# Install PostgreSQL operator (example)
kubectl apply -f https://raw.githubusercontent.com/zalando/postgres-operator/master/manifests/postgresql.crd.yaml

# Create PostgreSQL instance
cat > postgres.yaml <<EOF
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: codeflow-postgres
spec:
  instances: 3
  postgresql:
    parameters:
      max_connections: "200"
  storage:
    size: 20Gi
EOF

kubectl apply -f postgres.yaml
```

### 3. Redis Setup

#### External Redis

```bash
# Update REDIS_URL in secrets.yaml
REDIS_URL: "redis://redis.example.com:6379/0"
```

#### In-Cluster Redis (Redis Operator)

```bash
# Install Redis operator
kubectl apply -f https://raw.githubusercontent.com/spotahome/redis-operator/master/example/operator/all-redis-operator-resources.yaml

# Create Redis instance
cat > redis.yaml <<EOF
apiVersion: databases.spotahome.com/v1
kind: RedisFailover
metadata:
  name: codeflow-redis
spec:
  sentinel:
    replicas: 3
  redis:
    replicas: 3
    storage:
      persistentVolumeClaim:
        metadata:
          name: redis-data
        spec:
          accessModes:
            - ReadWriteOnce
          resources:
            requests:
              storage: 10Gi
EOF

kubectl apply -f redis.yaml
```

### 4. Configuration Management

#### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: codeflow-config
  namespace: codeflow
data:
  CODEFLOW_ENV: "production"
  CODEFLOW_LOG_LEVEL: "INFO"
  CODEFLOW_HOST: "0.0.0.0"
  CODEFLOW_PORT: "8080"
```

#### Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: codeflow-secrets
  namespace: codeflow
type: Opaque
stringData:
  DATABASE_URL: "postgresql://..."
  REDIS_URL: "redis://..."
  GITHUB_TOKEN: "..."
  OPENAI_API_KEY: "..."
  ANTHROPIC_API_KEY: "..."
```

**Best Practice:** Use external secret management:

- Azure Key Vault (via Secrets Store CSI Driver)
- AWS Secrets Manager
- HashiCorp Vault
- Sealed Secrets

### 5. Deployment Configuration

#### Main Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: codeflow-engine
  namespace: codeflow
spec:
  replicas: 3
  selector:
    matchLabels:
      app: codeflow-engine
  template:
    metadata:
      labels:
        app: codeflow-engine
    spec:
      containers:
        - name: codeflow-engine
          image: codeflowacr.azurecr.io/codeflow-engine:1.0.1
          ports:
            - containerPort: 8080
          envFrom:
            - configMapRef:
                name: codeflow-config
            - secretRef:
                name: codeflow-secrets
          resources:
            requests:
              cpu: "250m"
              memory: "512Mi"
            limits:
              cpu: "1000m"
              memory: "2Gi"
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 5
```

#### Worker Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: codeflow-worker
  namespace: codeflow
spec:
  replicas: 2
  selector:
    matchLabels:
      app: codeflow-worker
  template:
    metadata:
      labels:
        app: codeflow-worker
    spec:
      containers:
        - name: codeflow-worker
          image: codeflowacr.azurecr.io/codeflow-engine:1.0.1
          command: ["codeflow-worker"]
          envFrom:
            - configMapRef:
                name: codeflow-config
            - secretRef:
                name: codeflow-secrets
          resources:
            requests:
              cpu: "250m"
              memory: "512Mi"
            limits:
              cpu: "500m"
              memory: "1Gi"
```

### 6. Service Configuration

```yaml
apiVersion: v1
kind: Service
metadata:
  name: codeflow-engine
  namespace: codeflow
spec:
  type: LoadBalancer
  selector:
    app: codeflow-engine
  ports:
    - port: 80
      targetPort: 8080
      protocol: TCP
```

### 7. Ingress Configuration

#### NGINX Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: codeflow-ingress
  namespace: codeflow
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
    - hosts:
        - app.codeflow.celladoresystems.com
      secretName: codeflow-tls
  rules:
    - host: app.codeflow.celladoresystems.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: codeflow-engine
                port:
                  number: 80
```

---

## Scaling

### Horizontal Pod Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: codeflow-engine-hpa
  namespace: codeflow
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: codeflow-engine
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

### Vertical Pod Autoscaling (GKE)

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: codeflow-engine-vpa
  namespace: codeflow
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: codeflow-engine
  updatePolicy:
    updateMode: "Auto"
```

---

## Monitoring

### Prometheus Metrics

```yaml
apiVersion: v1
kind: Service
metadata:
  name: codeflow-engine-metrics
  namespace: codeflow
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/metrics"
spec:
  selector:
    app: codeflow-engine
  ports:
    - port: 8080
      targetPort: 8080
```

### ServiceMonitor (Prometheus Operator)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: codeflow-engine
  namespace: codeflow
spec:
  selector:
    matchLabels:
      app: codeflow-engine
  endpoints:
    - port: http
      path: /metrics
      interval: 30s
```

---

## Troubleshooting

### Pod Won't Start

```bash
# Check pod status
kubectl describe pod <pod-name> -n codeflow

# Check logs
kubectl logs <pod-name> -n codeflow

# Check events
kubectl get events -n codeflow --sort-by='.lastTimestamp'
```

### Database Connection Issues

```bash
# Test database connectivity from pod
kubectl exec -it <pod-name> -n codeflow -- \
  psql $DATABASE_URL -c "SELECT 1"

# Check secrets
kubectl get secret codeflow-secrets -n codeflow -o yaml
```

### High Resource Usage

```bash
# Check resource usage
kubectl top pods -n codeflow

# Check HPA status
kubectl get hpa -n codeflow

# Adjust resource limits
kubectl edit deployment codeflow-engine -n codeflow
```

---

## Rollback

### Rollback to Previous Version

```bash
# List deployment history
kubectl rollout history deployment/codeflow-engine -n codeflow

# Rollback to previous version
kubectl rollout undo deployment/codeflow-engine -n codeflow

# Rollback to specific revision
kubectl rollout undo deployment/codeflow-engine -n codeflow --to-revision=2
```

---

## Best Practices

1. **Use ConfigMaps for non-sensitive config**
2. **Use Secrets for sensitive data** (or external secret management)
3. **Set resource requests and limits**
4. **Use health checks** (liveness and readiness probes)
5. **Enable horizontal pod autoscaling**
6. **Use namespaces** for environment isolation
7. **Implement network policies** for security
8. **Use persistent volumes** for stateful data
9. **Monitor with Prometheus/Grafana**
10. **Use GitOps** (ArgoCD, Flux) for deployment

---

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Azure Kubernetes Service](https://docs.microsoft.com/azure/aks/)
- [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine/docs/)
- [Amazon EKS](https://docs.aws.amazon.com/eks/)
- [Full Deployment Guide](./DEPLOYMENT_GUIDE.md)

---

## Support

For issues or questions:

- GitHub Issues: [codeflow-engine/issues](https://github.com/JustAGhosT/codeflow-engine/issues)
- Kubernetes Documentation: [kubernetes.io](https://kubernetes.io/docs/)
