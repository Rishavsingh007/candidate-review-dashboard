# Candidate Review Dashboard

Internal candidate scoring and review dashboard for recruitment teams. Reviewers score candidates across categories and view AI-generated summaries. Admins have full visibility including internal notes and all reviewer scores.

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy, SQLite, JWT auth
- **Frontend:** React 18, Vite, TanStack Query, Axios
- **Infrastructure:** Docker Compose

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose, **or**
- Python 3.12+ and Node.js 20+ for local development

## Quick Start (Docker)

```bash
# From the repository root
docker compose up --build
```

| Service  | URL                        |
|----------|----------------------------|
| Frontend | http://localhost:5173    |
| Backend  | http://localhost:8000      |
| API docs (Swagger) | http://localhost:8000/docs |
| API docs (ReDoc)   | http://localhost:8000/redoc  |

Copy [`.env.example`](.env.example) to `.env` and adjust values if needed. **Do not commit a real `.env` file**, only dummy values belong in the repo. Docker Compose reads `JWT_SECRET` from the environment (defaults to a dev placeholder).

### Smoke test

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok"}`

## Features

- **Candidate list** — filter by status, role, skill, keyword; offset pagination (default 20, max 50)
- **Candidate detail** — profile, role-aware scores, scoring form, mock AI summary (loading + error states)
- **RBAC** — reviewers see only their scores; admins see all scores and internal notes
- **Auth** — JWT login/register (registration always creates `reviewer`, never `admin`)
- **Soft delete** — admins archive candidates (`status = archived`); never hard-deleted

## Demo Credentials

> **Demo credentials are for local evaluation only.** 

Seeded on first startup (also shown on the login page):

| Role     | Email                 | Password         |
|----------|-----------------------|------------------|
| Admin    | admin@tech.com        | adminpass123     |
| Reviewer | reviewer1@tech.com    | reviewerpass123  |
| Reviewer | reviewer2@tech.com    | reviewerpass123  |

New accounts can be registered via the UI; registration always creates a **reviewer** role (never admin). Open registration is enabled for the demo only, production would disable or gate it.

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL=http://localhost:8000` (see `.env.example`).

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest
```

## Example API Calls

### Register a reviewer

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "newreviewer@example.com", "password": "password123"}'
```

### Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "reviewer1@tech.com", "password": "reviewerpass123"}'
```

Save the `access_token` from the response.

### List candidates (with filters and pagination)

```bash
curl "http://localhost:8000/candidates?status=new&limit=20&offset=0" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Get candidate detail

```bash
curl http://localhost:8000/candidates/CANDIDATE_ID \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Submit a score

```bash
curl -X POST http://localhost:8000/candidates/CANDIDATE_ID/scores \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"category": "technical", "score": 4, "note": "Strong fundamentals"}'
```

### Generate AI summary (mock, ~2s delay)

```bash
curl -X POST "http://localhost:8000/candidates/CANDIDATE_ID/summary?force=false" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Architecture Decision Records

### ADR-1: FastAPI for the backend

**Context:**  
The project needed an async-capable Python backend with built-in validation and auto-generated API documentation, all within a tight development timeframe.

**Decision:**  
I chose FastAPI with Pydantic and SQLAlchemy.

**Trade-off:**  
Compared to Flask, FastAPI adds more structure, but it gives strong async support (used for the mocked LLM call), automatic OpenAPI documentation, and strict typed validation. This also helped catch issues like invalid score ranges and role spoofing at the API boundary.

---

### ADR-2: SQLite with a serverless-friendly schema

**Context:**  
The assignment allowed either DynamoDB-style storage or SQLite, and the goal was to keep setup as simple and zero-configuration as possible.

**Decision:**  
I used SQLite through SQLAlchemy, adding explicit indexes on fields like `status`, `role_applied`, and `candidate_id`.

**Trade-off:**  
SQLite is not designed for horizontal scaling, but all database access is routed through a service layer. This keeps the system flexible, so the underlying database can be swapped later without changing the API routes.

---

### ADR-3: Role-based response schemas

**Context:**  
Reviewers should not be able to access other reviewers’ scores or internal notes.

**Decision:**  
I enforced access control at the service layer and used separate Pydantic schemas like `CandidateDetailReviewer` and `CandidateDetailAdmin`.

**Trade-off:**  
This introduces some duplication in schema definitions, but it ensures security is handled server-side and cannot be bypassed by the client.

## Debugging Signal

The assignment's planted bug loads every candidate into memory, filters in Python, then paginates:

```python
all_candidates = db.execute("SELECT * FROM candidates").fetchall()
filtered = [c for c in all_candidates if c["status"] == status]
offset = (page - 1) * page_size
return filtered[offset : offset + page_size]
```

**What's wrong:**

1. **Full-table scan into memory**: O(N) memory and network; the database is bypassed entirely.
2. **Indexes are wasted**: `status` and `role_applied` indexes are never used when filtering in Python.
3. **Keyword filtering in Python** compounds the same problem.

**Why it matters at scale:** With thousands of candidates, every search loads the full table into the app process. Memory, latency, and cost grow linearly; the DB cannot optimize or paginate.

**Correct approach:** Push filtering, sorting, and pagination into SQL:

```sql
SELECT * FROM candidates
WHERE status = :status
  AND (name LIKE :kw OR email LIKE :kw)
  AND status != 'archived'
ORDER BY created_at DESC
LIMIT :limit OFFSET :offset;
```

This is how `candidate_service.list_candidates` is implemented.

## Learning Reflection

One thing I did for the first time was use role-based Pydantic response schemas as a security measure. Instead of relying on the frontend to hide sensitive information, the API returns only the data each role (e.g., reviewers or admins) is allowed to see.

I also improved performance by moving candidate filtering and pagination directly into SQLAlchemy queries. This avoided the full table scans that were showing up during debugging and made the application more efficient.

If I had more time, I would add Server-Sent Events (SSE) to provide real-time score updates as part of the stretch goals. I’d also improve security by moving authentication tokens from localStorage to httpOnly cookies.

## Known Limitations

- Real-time score updates via SSE (`GET /candidates/{id}/stream`) were part of the stretch goals and are not implemented yet. Scores currently update when a submission is made or the page is refreshed.
- The demo credentials included in the seed data and shown on the login page are intended only for local testing and evaluation.
- User registration is intentionally left open for demonstration purposes. In a production environment, registration would be restricted or protected behind an approval process.
- Authentication tokens are stored in `localStorage`, which is acceptable for this demo SPA. For production, I would move them to secure httpOnly cookies to reduce security risks.
- The application uses SQLite, which works well for development and evaluation but is not designed for large-scale production deployments.
- The AI candidate summary feature is currently mocked using `asyncio.sleep(2)` to simulate processing time and does not integrate with a real LLM.
- Refresh tokens are not implemented. Access tokens expire after 60 minutes, requiring users to log in again.

## Project Structure

```
/
├── README.md
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── auth.py
│   │   ├── routers/
│   │   └── services/
│   └── tests/
└── frontend/
    └── src/
        ├── pages/
        ├── components/
        └── api/
```



