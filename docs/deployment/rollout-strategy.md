# Rollout Strategy

## Promotion Flow

1. **Dev** – automatic updates from `main` via GitHub Actions Cloud Build triggers. Validate with smoke tests and the `test-gateway` page.
2. **Staging** – tagged releases (`v*`) trigger ArgoCD sync (see `infra/gitops/argocd/service-gateway-auth.yaml`). Enable 20/80 canary with Istio subsets.
3. **Prod** – promote images by updating the ArgoCD `Application` image tags. Require:
 - Grafana gateway latency < 600ms p95
 - Auth HTTP 5xx < 1%
 - Alertmanager quiet for 30 minutes
- Run `.github/workflows/security-scan.yml` (Trivy/Snyk job) prior to promoting images.

## Canary / Blue-Green

- Use Istio `DestinationRule` subsets with labels `version=stable` and `version=canary`.
- Define VirtualService weights (80/20 canary, promoted to 100/0 after validation).
- Roll back by flipping weights and restarting the canary deployment.

## Rollback Checklist

1. `kubectl rollout undo deploy/service-gateway -n gateway`
2. Scale down impacted canary pods.
3. Confirm gateway health via `/actuator/health` and Grafana dashboards.
4. Document incident in `docs/observability/runbooks.md`.

## Post-Deployment Review

After each production rollout:

- Capture metrics screenshots (latency, error rate).
- Note outstanding issues and create tasks in `tasks.md` backlog.
- Update `plan.md` with learnings for the corresponding phase.
