# Sherlock

Sherlock is an AI agent that acts as an autonomous data scientist, built using FastAPI and a Next.js frontend.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- [Python 3.14+](https://www.python.org/) (for the backend)
- [Node.js 18+](https://nodejs.org/) (for the Next.js frontend)

## Quick Start (Local Development)

### 1. Clone & configure

```bash
git clone https://github.com/your-username/sherlock.git
cd sherlock
cp backend/.env.example backend/.env   # then fill in your credentials
```

### 2. Start the database

We use Docker to run PostgreSQL with the `pgvector` extension locally.

```bash
docker compose up -d
```

This runs **PostgreSQL 17 + pgvector** on `localhost:5432`. Its port is exposed to the host machine so your local FastAPI app and Jupyter notebooks can easily connect to it.

### 3. Set up the backend

Run FastAPI in your local Python environment:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run the API

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload
```

FastAPI runs on `http://localhost:8000`.

### 5. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Next.js runs on `http://localhost:3000`.

### 6. Verify

```bash
curl http://localhost:8000/health
# → {"status": "ok"}
```

## Jupyter Notebooks (Agent Playground)

We maintain a mirrored Python environment in `notebooks/` designed as a sandbox for prototyping AI agents before finalizing them in the `backend/`. 

### Initial Setup

```bash
cd notebooks
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Symlink the backend environment variables so they stay beautifully synced
ln -sf ../backend/.env .env
```

### Running in VS Code / Cursor (Recommended)

You do not need to run a server in your terminal to write notebook code. To run `.ipynb` files directly inside your IDE seamlessly:

1. Open `notebooks/modelinvoking.ipynb` in your editor.
2. In the top right corner of the notebook, click **Select Kernel**.
3. Choose **Python Environments** (or "Select Another Kernel..." -> "Python Environments").
4. If your IDE doesn't automatically detect the `notebooks/.venv` folder, click the **Refresh** icon or choose **+ Enter interpreter path...** and paste:
   `notebooks/.venv/bin/python`

Once selected, your IDE will remember this, and you will have full access to the cloned API environment inside the notebook!

### Running in the Browser (Classic)

If you prefer the web-based Jupyter UI, run:

```bash
cd notebooks
source .venv/bin/activate
jupyter lab
```

## Production (Docker)

For production, the Docker setup provisions both our internal services - the **FastAPI application** and **PostgreSQL**. They run together on an isolated Docker network.

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

## Stopping

```bash
# Development (DB only)
docker compose down          # stop DB container
docker compose down -v       # stop + delete database volume

# Production (full stack)
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml down -v
```

## Project Structure

```text
sherlock/
├── backend/
│   ├── main.py             # FastAPI app entry point
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile          # Production image (used by docker-compose.prod.yml)
│   ├── .env.example        # Template for local .env
│   └── .env.docker         # Production Docker overrides
├── frontend/               # Next.js application
├── notebooks/              # Jupyter playground for AI agent development
├── docker-compose.yml      # Dev: PostgreSQL only
└── docker-compose.prod.yml # Prod: PostgreSQL + FastAPI
```