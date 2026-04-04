# Sherlock

Autonomous Data Scientist — non-deterministic reasoning engine bounded by a deterministic state machine. Built with FastAPI, LangGraph, Amazon Bedrock, PostgreSQL + pgvector, and Next.js.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- [Node.js](https://nodejs.org/) (v18+)
- Python 3.14+ (for local development only)

## Setup

### 1. Clone & configure environment

```bash
git clone https://github.com/your-username/sherlock.git
cd sherlock
cp backend/.env.example backend/.env  # then edit with your credentials
```

> The `.env` file contains database credentials and AWS keys.

### 2. Start the backend (API + Database)

```bash
docker compose up --build
```

This spins up:
- **PostgreSQL 17** with pgvector on `localhost:5432`
- **FastAPI** on `http://localhost:8000`

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Next.js dev server runs on `http://localhost:3000`.

### 4. Verify

```bash
curl http://localhost:8000/health
# → {"status": "ok"}
```

## Stopping

```bash
docker compose down      # stop containers
docker compose down -v   # stop + delete database volume
```