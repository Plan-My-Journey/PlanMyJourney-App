# Plan My Journey — Application Repository

Organization: [Plan-My-Journey](https://github.com/orgs/Plan-My-Journey)

## Contents

- `frontend/` — React + Vite SPA (Cognito OAuth + API integration)
- `services/` — FastAPI microservices (user, travel, ai, utility)
- `docker/` — Multistage production Dockerfiles (non-root)
- `nginx/` — Local reverse proxy config

## Related Repositories

| Repository | Purpose |
|---|---|
| [planmyjourney-terraform](https://github.com/Plan-My-Journey/planmyjourney-terraform) | VPC, EKS, RDS, Cognito, CloudFront, IRSA |
| [planmyjourney-gitops](https://github.com/Plan-My-Journey/planmyjourney-gitops) | Helm, Kustomize, Flux manifests |
| [planmyjourney-workflows](https://github.com/Plan-My-Journey/planmyjourney-workflows) | Reusable GitHub Actions |

## Local Development

```bash
docker compose up --build
cd frontend && npm ci && npm run dev
```

## Cognito Environment Variables (frontend)

```env
VITE_COGNITO_REGION=us-east-1
VITE_COGNITO_USER_POOL_ID=
VITE_COGNITO_CLIENT_ID=
VITE_COGNITO_DOMAIN=planmyjourney.auth.us-east-1.amazoncognito.com
VITE_COGNITO_REDIRECT_URI=https://invest-iq.online/callback
```

## CI/CD

- `build.yml` — lint, test, Trivy scan, ECR push
- `deploy.yml` — updates GitOps repo image tags (Flux reconciles)
