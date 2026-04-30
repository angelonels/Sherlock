# Sherlock

Sherlock is an AI data analyst SaaS for investigating CSV and Excel data with evidence-backed answers, charts, tables, KPI cards, and data-quality warnings.

## Repository Structure

```text
sherlock/
  apps/
    web/        Next.js App Router frontend
    api/        FastAPI backend
  infra/
    nginx/      reverse-proxy configuration
  scripts/      local and deployment scripts
  docs/         architecture, API contracts, phases, deployment notes
  .github/
    workflows/ CI
```

## Prerequisites

- Python 3.11+
- uv
- Node.js 24+
- pnpm 10+
- Docker and Docker Compose

## Local Setup

Start PostgreSQL:

```bash
docker compose -f docker-compose.dev.yml up -d
```

Set up the backend:

```bash
cd apps/api
cp .env.example .env
uv sync
uv run pytest
uv run uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`. The health route is `http://localhost:8000/api/v1/health`.

Set up the frontend:

```bash
cd apps/web
cp .env.example .env.local
pnpm install
pnpm lint
pnpm typecheck
pnpm test
pnpm dev
```

The web app runs at `http://localhost:3000`.

## Phase Regression Commands

Run these after Phase 3 changes:

```bash
cd apps/web
pnpm lint
pnpm typecheck
pnpm test
```

```bash
cd apps/api
uv sync
uv run pytest
```

## Auth Setup

The frontend renders local auth placeholders until Clerk keys are configured. To enable Clerk locally,
fill in `apps/web/.env.local`:

```env
NEXT_PUBLIC_APP_NAME=Sherlock
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL=/app
NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL=/app
NEXT_PUBLIC_CLERK_SIGN_IN_FORCE_REDIRECT_URL=/app
NEXT_PUBLIC_CLERK_SIGN_UP_FORCE_REDIRECT_URL=/app
```

Enable Google OAuth and email link verification in the Clerk Dashboard. The local `/sign-in` and
`/sign-up` routes render Clerk's hosted flow and show the enabled methods automatically.

The backend accepts Clerk session tokens after `apps/api/.env` contains:

```env
APP_ENV=development
APP_NAME=Sherlock
API_PREFIX=/api/v1
FRONTEND_ORIGIN=http://localhost:3000
DATABASE_URL=postgresql+psycopg://sherlock_admin:change_me@localhost:5432/sherlock_db
READONLY_DATABASE_URL=postgresql+psycopg://sherlock_readonly:change_me@localhost:5432/sherlock_db
CLERK_SECRET_KEY=
CLERK_JWKS_URL=https://your-clerk-frontend-api/.well-known/jwks.json
CLERK_AUTHORIZED_PARTIES=http://localhost:3000
CLERK_JWT_KEY=
```

Use either `CLERK_JWKS_URL` or `CLERK_JWT_KEY` for JWT verification. `CLERK_JWT_KEY` is optional
and should only be placed in local or deployment secrets, never in source control.
