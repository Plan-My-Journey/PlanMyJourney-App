# SonarCloud Fix Report

This document records all changes made to resolve SonarCloud findings across the Plan My Journey repositories. Application behavior, CI/CD pipeline structure, and AWS/EKS/Helm/ArgoCD/CloudFront/Terraform integrations are unchanged.

---

## Summary by Finding Category

| # | SonarCloud Rule / Finding | Files Changed | Resolution |
|---|---------------------------|---------------|------------|
| 1 | GitHub Actions must use pinned commit SHAs | 17 workflow files | Replaced `@v*` / `@master` tags with immutable full SHAs |
| 2 | Hardcoded credentials in docker-compose | 3 files | Moved DB/JWT secrets to `.env`; removed inline defaults |
| 3 | Container runs as root (nginx) | 3 files | Added `USER nginx`, port 8080, ownership setup |
| 4 | Merge consecutive Dockerfile `RUN` | 4 production Dockerfiles | Combined dependency prep + `pip install` layers |
| 5 | Prefer `globalThis` over `window` | 3 TypeScript files | Replaced browser global references |
| 6 | React props should be readonly | 7 TypeScript/TSX files | Added `readonly` to component prop types |

---

## 1. Pin GitHub Actions to Full Commit SHAs

**Why:** SonarCloud flags floating version tags (`@v4`, `@master`) because they can change without review, enabling supply-chain risk. Pinning to a full commit SHA makes workflow dependencies immutable and auditable.

**Pinned action reference:**

| Action | Previous Tag | Pinned SHA | Version |
|--------|--------------|------------|---------|
| `actions/checkout` | `@v4` | `11bd71901bbe5b1630ceea73d27597364c9af683` | v4.2.2 |
| `actions/setup-python` | `@v5` | `42375524e23c412d93fb67b49958b491fce71c38` | v5.4.0 |
| `actions/setup-node` | `@v4` | `49933ea5288caeca8642d1e84afbd3f7d6820020` | v4.4.0 |
| `aws-actions/configure-aws-credentials` | `@v4` | `ececac1a45f3b08a01d2dd070d28d111c5fe6722` | v4.1.0 |
| `aws-actions/amazon-ecr-login` | `@v2` | `4625ce35226a7557230889aae2f52eb50ec3dcda` | v2.0.1 |
| `hashicorp/setup-terraform` | `@v3` | `b9cd54a3c349d3f38e8881555d616ced269862dd` | v3.1.2 |
| `actions/upload-artifact` | `@v4` | `ea165f8d65b6e75b540449e92b4886f43607fa02` | v4.6.2 |
| `actions/download-artifact` | `@v4` | `cc203385981b70ca67e1cc392babf9cc229d5806` | v4.1.9 |
| `actions/github-script` | `@v7` | `60a0d83039c74a4aee543508d2ffcb1c3799cdea` | v7.0.1 |
| `peter-evans/create-pull-request` | `@v6` | `c5a7806660adbe173f04e3e038b0ccdcd758773c` | v6.1.0 |
| `SonarSource/sonarcloud-github-action` | `@master` | `ffc3010689be73b8e5ae0c57ce35968afd7909e8` | v5.0.0 |

### Modified workflow files

**planmyjourney-workflows/.github/workflows/**
- `_artifact-validation.yml`
- `_cd.yml`
- `_docker-build.yml`
- `_docker-promote.yml`
- `_docker-publish.yml`
- `_frontend-build.yml`
- `_frontend-s3-deploy.yml`
- `_frontend-s3-promote.yml`
- `_lint.yml`
- `_pr-comment.yml`
- `_read-gitops-image-tag.yml`
- `_record-artifact-validation.yml`
- `_sast.yml`
- `_sca.yml`
- `_tag.yml`
- `_terraform.yml`
- `_version-check.yml`

**planmyjourney-gitops/.github/workflows/**
- `argocd-sync-on-merge.yml`

**CI/CD impact:** None. Reusable workflow call paths (`Plan-My-Journey/PlanMyJourney-Workflows/...@main`) are unchanged. Only third-party action references were pinned.

---

## 2. Remove Hardcoded PostgreSQL Passwords from docker-compose

**Why:** SonarCloud detects hardcoded/default database passwords as credential exposure, even in local compose files checked into source control.

**Changes:**
- Removed `${USER_DB_PASSWORD:-user_password}` and `${TRAVEL_DB_PASSWORD:-travel_password}` fallback defaults from `docker-compose.yml`
- Removed `${JWT_SECRET_KEY:-change-this-local-dev-secret}` fallback default
- Added `env_file: .env` to database and application services
- Credentials are now supplied exclusively via `.env` (from `.env.example`)

### Modified files
- `planmyjourney-app/docker-compose.yml`
- `planmyjourney-app/.env.example`
- `planmyjourney-app/README.md`

**Local setup (updated):**
```bash
cp .env.example .env
# Set USER_DB_PASSWORD, TRAVEL_DB_PASSWORD, JWT_SECRET_KEY in .env
docker compose up --build
```

**Runtime impact:** Same behavior when `.env` is present. Compose fails fast if required secrets are missing (safer default).

---

## 3. Run Frontend Nginx as Non-Root User

**Why:** SonarCloud flags containers that run processes as root (`docker:S6470`). Nginx must drop privileges and bind to a non-privileged port.

**Changes:**
- Set `listen 8080` in `frontend/nginx.conf` (non-privileged port)
- Added `USER nginx` after ownership setup in both frontend Dockerfiles
- Set file ownership for nginx paths (`/usr/share/nginx/html`, cache, logs, pid)
- Updated `docker-compose.yml` port mapping to `5173:8080`
- Updated health checks to probe port `8080`

### Modified files
- `planmyjourney-app/frontend/nginx.conf`
- `planmyjourney-app/frontend/Dockerfile`
- `planmyjourney-app/docker/frontend/Dockerfile`
- `planmyjourney-app/docker-compose.yml` (port mapping + healthcheck)

**Production impact:** None. Production frontend uses S3 + CloudFront, not these Docker images. EKS/Helm frontend charts are unchanged.

---

## 4. Merge Consecutive RUN Instructions in Dockerfiles

**Why:** SonarCloud rule `docker:S7031` recommends merging consecutive `RUN` layers to reduce image size and attack surface.

**Changes:** In production Dockerfiles under `planmyjourney-app/docker/*/`, merged the requirements-file preparation step and `pip install` into a single `RUN` instruction per service builder stage.

### Modified files
- `planmyjourney-app/docker/ai-service/Dockerfile`
- `planmyjourney-app/docker/user-service/Dockerfile`
- `planmyjourney-app/docker/travel-service/Dockerfile`
- `planmyjourney-app/docker/utility-service/Dockerfile`

**Runtime impact:** Identical installed packages and startup commands. Fewer intermediate image layers only.

---

## 5. Replace `window` with `globalThis`

**Why:** SonarCloud TypeScript rule prefers `globalThis` for cross-environment global access (browser, worker, Node) and avoids implicit `window` coupling.

**Replacements:**
| Location | Before | After |
|----------|--------|-------|
| Cognito redirect/logout URIs | `window.location.origin` | `globalThis.location.origin` |
| Cognito login/logout navigation | `window.location.href` | `globalThis.location.href` |
| Autocomplete debounce timers | `window.setTimeout` / `window.clearTimeout` | `globalThis.setTimeout` / `globalThis.clearTimeout` |

### Modified files
- `planmyjourney-app/frontend/src/auth/cognito.ts`
- `planmyjourney-app/frontend/src/context/AuthContext.tsx`
- `planmyjourney-app/frontend/src/components/DestinationAutocomplete.tsx`

**Runtime impact:** None in browser context. `globalThis.location` and timer APIs behave identically to `window.*`.

---

## 6. Mark React Component Props as Readonly

**Why:** SonarCloud rule `typescript:S6759` requires functional component props to be immutable, preventing accidental in-place mutation of props objects.

**Changes:** Added `readonly` to inline prop types and `Readonly<>` where appropriate.

### Modified files
- `planmyjourney-app/frontend/src/context/AuthContext.tsx` — `AuthProvider` children prop
- `planmyjourney-app/frontend/src/components/DestinationAutocomplete.tsx` — `Props` type
- `planmyjourney-app/frontend/src/components/PageHeader.tsx`
- `planmyjourney-app/frontend/src/components/EmptyState.tsx`
- `planmyjourney-app/frontend/src/components/Layout.tsx` — `SidebarContent`, `PageShell`
- `planmyjourney-app/frontend/src/pages/Dashboard.tsx` — `StatCard`
- `planmyjourney-app/frontend/src/pages/DestinationComparison.tsx` — `ComparisonBlock`

**Runtime impact:** Type-level only; no JavaScript output change.

---

## Complete Modified File List

```
SONAR_FIX_REPORT.md

planmyjourney-workflows/.github/workflows/_artifact-validation.yml
planmyjourney-workflows/.github/workflows/_cd.yml
planmyjourney-workflows/.github/workflows/_docker-build.yml
planmyjourney-workflows/.github/workflows/_docker-promote.yml
planmyjourney-workflows/.github/workflows/_docker-publish.yml
planmyjourney-workflows/.github/workflows/_frontend-build.yml
planmyjourney-workflows/.github/workflows/_frontend-s3-deploy.yml
planmyjourney-workflows/.github/workflows/_frontend-s3-promote.yml
planmyjourney-workflows/.github/workflows/_lint.yml
planmyjourney-workflows/.github/workflows/_pr-comment.yml
planmyjourney-workflows/.github/workflows/_read-gitops-image-tag.yml
planmyjourney-workflows/.github/workflows/_record-artifact-validation.yml
planmyjourney-workflows/.github/workflows/_sast.yml
planmyjourney-workflows/.github/workflows/_sca.yml
planmyjourney-workflows/.github/workflows/_tag.yml
planmyjourney-workflows/.github/workflows/_terraform.yml
planmyjourney-workflows/.github/workflows/_version-check.yml

planmyjourney-gitops/.github/workflows/argocd-sync-on-merge.yml

planmyjourney-app/docker-compose.yml
planmyjourney-app/.env.example
planmyjourney-app/README.md
planmyjourney-app/docker/ai-service/Dockerfile
planmyjourney-app/docker/travel-service/Dockerfile
planmyjourney-app/docker/user-service/Dockerfile
planmyjourney-app/docker/utility-service/Dockerfile
planmyjourney-app/docker/frontend/Dockerfile
planmyjourney-app/frontend/Dockerfile
planmyjourney-app/frontend/nginx.conf
planmyjourney-app/frontend/src/auth/cognito.ts
planmyjourney-app/frontend/src/context/AuthContext.tsx
planmyjourney-app/frontend/src/components/DestinationAutocomplete.tsx
planmyjourney-app/frontend/src/components/EmptyState.tsx
planmyjourney-app/frontend/src/components/Layout.tsx
planmyjourney-app/frontend/src/components/PageHeader.tsx
planmyjourney-app/frontend/src/pages/Dashboard.tsx
planmyjourney-app/frontend/src/pages/DestinationComparison.tsx
```

**Total: 38 files** (37 modified + this report)

---

## Verification Checklist

- [ ] Push `planmyjourney-workflows` changes to `main` (reusable workflows consumed by App repo)
- [ ] Push `planmyjourney-app` and `planmyjourney-gitops` changes
- [ ] Re-run SonarCloud analysis on `Plan-My-Journey/PlanMyJourney-App`
- [ ] Local smoke test: `cp .env.example .env && docker compose up --build`
- [ ] Confirm frontend reachable at `http://localhost:5173` (maps to nginx:8080)

---

## Out of Scope (Unchanged)

- EKS Helm charts and ArgoCD manifests (`planmyjourney-gitops/helm-charts/**`)
- Terraform modules and state (`planmyjourney-terraform/**`)
- CloudFront/S3 production frontend deployment workflows (logic unchanged; only action SHAs pinned)
- Legacy reference folders (`_ref/**`, root `frontend/`, `services/` duplicates outside `planmyjourney-app/`)
