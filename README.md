# Ollive — LLM Inference Logging System

A full-stack LLM chatbot with a lightweight inference logging SDK, ingestion pipeline, and observability dashboard.

---

## Demo

<img width="1912" height="917" alt="image" src="https://github.com/user-attachments/assets/e621a59f-df58-4589-be8c-ed5c9cf3008d" />

---
<img width="1901" height="916" alt="image" src="https://github.com/user-attachments/assets/152a80f2-38c7-4fe0-8dba-ffb55d75d75f" />


## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy |
| LLM | Gemini 2.5 Flash (Google AI) |
| Database | PostgreSQL (Docker) / SQLite (local dev) |
| Infra | Docker Compose |

---

## Quick Start (One Command)

### Prerequisites
- Docker Desktop running
- A Gemini API key from [aistudio.google.com](https://aistudio.google.com/apikey)

### Setup

```bash
git clone https://github.com/524himanshu/ollive-assignment
cd ollive-assignment

# Copy env template and add your Gemini key
cp .env.example .env
# Edit .env and set GEMINI_API_KEY=your_key_here

# Start everything
docker compose up
```

Open [http://localhost:3000](http://localhost:3000)

That's it. Docker Compose spins up Postgres, the FastAPI backend, and the Next.js frontend in the correct order with health checks.

---

## Local Development (Without Docker)

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

pip install -r requirements.txt

cp .env.example .env
# Edit .env — set GEMINI_API_KEY, USE_SQLITE=true

uvicorn main:app --reload --port 8000
```

API docs available at [http://localhost:8000/docs](http://localhost:8000/docs)

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## Architecture Overview

```
Browser
  │
  ├── GET/POST http://localhost:3000
  │     │
  │   Next.js (Frontend)
  │     │
  │     └── Direct API calls to http://localhost:8000
  │
  └── FastAPI (Backend)
        │
        ├── /api/v1/chat/          → Gemini SDK wrapper → Gemini API
        │                                    │
        │                          Fire-and-forget log
        │                                    │
        ├── /api/v1/logs/ingest    → PII redaction → PostgreSQL
        ├── /api/v1/logs/dashboard → Aggregated stats from DB
        ├── /api/v1/logs/recent    → Recent inference logs
        │
        └── /api/v1/conversations/ → Conversation CRUD
```

### Ingestion Flow

1. User sends a message via the chat UI
2. Frontend calls `POST /api/v1/chat/`
3. Backend calls Gemini API via the SDK wrapper
4. SDK records `started_at`, `ended_at`, token counts, and status
5. After Gemini responds (non-blocking), SDK fires a `POST /api/v1/logs/ingest`
6. Ingestion endpoint validates the payload, runs PII redaction on input/output previews
7. Cleaned log is written to `inference_logs` table
8. Chat response is returned to the user — logging never adds latency

### Logging Strategy

The SDK (`GeminiSDK` class in `backend/app/services/gemini_service.py`) wraps every Gemini call and captures:

- `model` and `provider`
- `started_at` / `ended_at` timestamps
- `latency_ms` (wall clock, using `time.perf_counter`)
- `input_tokens` / `output_tokens` / `total_tokens` from Gemini's usage metadata
- `status` — success or error
- `error_message` if the call failed
- `input_preview` / `output_preview` — first 200 chars, PII-redacted before storage

Logs are sent fire-and-forget in a separate `httpx` call. If logging fails, the chat response is unaffected. The `except Exception: pass` in `_ship_log` is intentional — observability infrastructure must never take down the product.

### PII Redaction

The ingestion endpoint runs regex-based redaction before writing to the database. Patterns covered:

- Email addresses → `[EMAIL]`
- Phone numbers → `[PHONE]`
- Social security numbers → `[SSN]`
- Credit card numbers → `[CARD]`
- IP addresses → `[IP]`

PII is redacted from `input_preview` and `output_preview` before storage. The `pii_detected` boolean flag is set server-side (not trusted from the client) and surfaced in the dashboard.

**Production note:** For production, [Microsoft Presidio](https://microsoft.github.io/presidio/) would replace regex — it handles names, addresses, and entity recognition using NLP. Regex was chosen here for startup speed and zero ML model loading time.

---

## Schema Design

### Tables

**`conversations`**
```
id          UUID (PK)
title       VARCHAR(255)
status      VARCHAR(20)  -- "active" | "cancelled"
created_at  TIMESTAMP
updated_at  TIMESTAMP
```

**`messages`**
```
id                UUID (PK)
conversation_id   UUID (FK → conversations)
role              VARCHAR(20)  -- "user" | "assistant"
content           TEXT
created_at        TIMESTAMP
```

**`inference_logs`**
```
id                UUID (PK)
conversation_id   UUID (FK → conversations, nullable)
model             VARCHAR(100)
provider          VARCHAR(50)
started_at        TIMESTAMP
ended_at          TIMESTAMP
latency_ms        FLOAT
input_tokens      INTEGER
output_tokens     INTEGER
total_tokens      INTEGER
status            VARCHAR(20)  -- "success" | "error"
error_message     TEXT
input_preview     TEXT         -- max 200 chars, PII-redacted
output_preview    TEXT         -- max 200 chars, PII-redacted
pii_detected      BOOLEAN
created_at        TIMESTAMP
```

### Design Decisions

**Why 3 separate tables?**
`messages` and `inference_logs` are different concerns. Messages are UX data — what the user said. Inference logs are operational telemetry — how the API performed. Mixing them would make querying either harder and couple unrelated data.

**Why UUIDs over auto-increment IDs?**
UUIDs are safe to expose in URLs and APIs. Auto-increment integers leak information about record counts and are harder to shard in distributed systems.

**Why separate `input_preview` from `content`?**
Full message content lives in `messages`. The inference log only stores a 200-char preview for debugging purposes. Storing full content in both tables would be redundant and double the storage.

**Why `pii_detected` as a boolean flag?**
Fast aggregation without parsing log content. The dashboard can run `COUNT WHERE pii_detected = true` in one SQL query rather than scanning text fields.

**SQLite for local dev, Postgres in Docker**
SQLite requires zero configuration for local development. `USE_SQLITE=true` in `.env` switches the driver automatically. Docker Compose sets `USE_SQLITE=false` and provides a real Postgres instance. The schema is identical across both.

---

## Tradeoffs

| Decision | Why | Alternative |
|---|---|---|
| Synchronous logging (httpx) | Simple, no queue needed at this scale | Kafka/Redis queue for high throughput |
| Regex PII redaction | Zero startup time, covers common cases | Microsoft Presidio for production |
| SQLite locally | Zero config for reviewers running locally | Docker-only Postgres setup |
| Fire-and-forget logs | Logging never blocks chat response | Guaranteed delivery with retry queue |
| Short context window (10 msgs) | Keeps token costs low | Sliding window with summarization |

---

## What I'd Improve With More Time

**Streaming responses**
Gemini supports streaming via `stream=True`. The frontend would use `EventSource` or chunked fetch to render tokens as they arrive. Currently the full response waits for completion.

**Event-based architecture**
Replace the direct HTTP log call with a Redis queue. The SDK publishes to a queue, a separate consumer handles ingestion. This decouples the chat latency from logging completely and allows retries on failure.

**Latency/Throughput/Error charts**
The dashboard has stats cards but no time-series charts. Recharts with a `/logs/timeseries` endpoint returning bucketed data by hour/day would show trends rather than just totals.

**Multi-provider support**
The `GeminiSDK` class is provider-specific. A `BaseLLMProvider` abstract class with `GeminiProvider`, `OpenAIProvider`, and `GroqProvider` implementations would allow provider switching via config.

**Authentication**
No auth currently. JWTs with FastAPI's `Depends` system would scope conversations and logs to individual users.

**Alembic migrations**
Currently using `create_all` for table creation. Alembic would handle schema changes in production without dropping and recreating tables.

**Deploy to Kubernetes**
Docker Compose works for single-node. A Helm chart with separate deployments for backend and frontend, a managed Postgres (RDS/CloudSQL), and a Redis queue would be the production path.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/chat/` | Send a message, get a response |
| GET | `/api/v1/conversations/` | List all conversations |
| GET | `/api/v1/conversations/{id}/` | Get conversation with messages |
| PATCH | `/api/v1/conversations/{id}/cancel/` | Cancel a conversation |
| PATCH | `/api/v1/conversations/{id}/resume/` | Resume a cancelled conversation |
| POST | `/api/v1/logs/ingest/` | Ingest an inference log (SDK use) |
| GET | `/api/v1/logs/dashboard/` | Aggregated stats |
| GET | `/api/v1/logs/recent/` | Recent inference logs |
| GET | `/health` | Health check |

Full interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Project Structure

```
ollive-assignment/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   │   ├── chat.py           # Chat endpoint
│   │   │   ├── conversations.py  # Conversation CRUD
│   │   │   └── logs.py           # Ingestion + dashboard
│   │   ├── core/
│   │   │   └── config.py         # Settings from .env
│   │   ├── db/
│   │   │   └── database.py       # SQLAlchemy engine + session
│   │   ├── models/
│   │   │   └── models.py         # DB table definitions
│   │   ├── schemas/
│   │   │   └── schemas.py        # Pydantic request/response models
│   │   └── services/
│   │       ├── gemini_service.py # SDK wrapper + log shipping
│   │       └── pii_service.py    # PII redaction
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── page.tsx              # Main chat + dashboard UI
│   │   └── layout.tsx
│   ├── lib/
│   │   └── api.ts                # Axios API client
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```
