# GPU-For-Everyone — Implementation Plan

**Last Updated**: 2026-02-14

## 🎯 Vision
A decentralized GPU sharing platform where **Consumers** rent GPU compute from **Providers** using a credit-based system. The system connects consumers needing LLM inference to providers running local GPU nodes (via Ollama), orchestrated through a Django backend with WebSocket communication.

---

## 📐 Architecture

```
┌─────────────┐     REST API      ┌──────────────┐     WebSocket     ┌──────────────┐
│   Frontend   │ ◄────────────► │   Backend      │ ◄──────────────► │   GPU Agent    │
│  (React/TS)  │                 │  (Django/DRF)  │                 │  (Python/WS)   │
│  Port: 5173  │                 │  Port: 8000    │                 │  Ollama Local  │
└─────────────┘                 └──────────────┘                 └──────────────┘
                                        │
                                   ┌────┴────┐
                                   │ SQLite  │ (PoC)
                                   │ (→ PG)  │
                                   └─────────┘
```

---

## 🗂 Project Structure

```
GPU-For-Everyone/
├── backend/                  # Django 6 + DRF + Channels
│   ├── config/               # Settings, URLs, ASGI
│   ├── core/                 # User model, Auth (JWT), Profile
│   ├── computing/            # Nodes, Jobs, WebSocket consumers
│   ├── payments/             # Transactions, Credit logs, CreditService
│   └── pyproject.toml        # Dependencies (managed by uv)
├── agent/                    # GPU Provider Agent
│   └── agent_ollama.py       # Connects to backend WS, runs Ollama tasks
├── frontend/                 # React + TypeScript + Vite
│   ├── src/
│   │   ├── pages/            # Login, Register, Dashboard, Landing
│   │   ├── components/       # JobSubmitter, etc.
│   │   └── context/          # AuthContext
│   └── tests/features/       # BDD feature files
└── docker-compose.yml        # PostgreSQL + Redis (production)
```

---

## ✅ Completed (Phase 1 — PoC)

### Backend
- [x] Custom User model with `wallet_balance` (Decimal), `role` (USER/PROVIDER)
- [x] JWT authentication (SimpleJWT)
- [x] Registration API (`POST /api/core/register/`)
- [x] Login API (`POST /api/core/token/`)
- [x] Profile API (`GET /api/core/profile/`)
- [x] Job Submission API (`POST /api/computing/submit-job/`)
  - Credit check & deduction (1.00 per job)
  - Job dispatched to agents via Channel Layer
- [x] Job Detail API (`GET /api/computing/jobs/<id>/`)
  - Owner-only access (403 for strangers)
- [x] WebSocket Consumer (`GPUConsumer`) for agent communication
- [x] Payment system: Transaction, CreditLog, CreditService
  - Deposit flow with mock webhook
  - Credit transfer between consumer & provider
- [x] Wallet Balance API (`GET /api/payments/wallet/`)
- [x] All URL routes wired: `/api/core/`, `/api/computing/`, `/api/payments/`

### Frontend
- [x] React + TypeScript + Vite setup
- [x] Auth flow: Login, Register, AuthContext with JWT
- [x] Dashboard with sidebar, wallet card, active jobs, nodes list
- [x] Job submission component (JobSubmitter)
- [x] Royal dark theme with glassmorphism

### Agent
- [x] `agent_ollama.py`: WebSocket client, Ollama integration, job processing

### Testing (64 passing tests)
- [x] `core/tests/test_models.py` — User defaults, wallet operations
- [x] `core/tests/test_auth.py` — Registration, login, profile (13 tests)
- [x] `computing/tests/test_flow.py` — Job submission flow (13 tests)
- [x] `computing/tests/test_lifecycle.py` — Job status transitions, detail API security (10 tests)
- [x] `computing/tests/test_models.py` — All model integrity (14 tests)
- [x] `computing/tests/test_computing.py` — Matchmaking logic
- [x] `payments/tests/test_payments.py` — Credit service, deposits, webhooks (9 tests)
- [x] BDD feature files for frontend flows

---

## 🔨 Phase 2 — Enhanced PoC (Next Steps)

### Priority 1: Core Improvements
- [ ] **Job result storage**: Agent sends result back → update Job.result & status via WS
- [ ] **Job listing endpoint**: `GET /api/computing/jobs/` — list user's jobs with pagination
- [ ] **Node registration via WS**: Persist node info to DB from WebSocket register message
- [ ] **Job assignment logic**: Round-robin or best-fit node selection
- [ ] **Heartbeat monitoring**: Track node liveliness, mark offline nodes

### Priority 2: Security & Robustness
- [ ] **Password validation**: Enforce strong passwords on registration
- [ ] **Rate limiting**: Prevent job submission spam
- [ ] **Token refresh flow**: Frontend auto-refreshes expired tokens
- [ ] **CSRF/CORS tightening**: Move from `CORS_ALLOW_ALL_ORIGINS=True` to whitelist
- [ ] **WebSocket auth**: Validate JWT tokens on WebSocket connections

### Priority 3: Frontend
- [ ] **Job history page**: Show past jobs with status and results
- [ ] **Wallet page**: Show transaction history, deposit/withdraw UI
- [ ] **Node management**: Register/deregister GPU nodes from dashboard
- [ ] **Real-time updates**: WebSocket subscription for job status changes
- [ ] **Loading states & error handling**: Better UX for API failures

### Priority 4: Infrastructure
- [ ] **Switch to PostgreSQL**: Use docker-compose for DB
- [ ] **Redis Channel Layer**: Replace InMemoryChannelLayer
- [ ] **Celery integration**: Background tasks for job scheduling
- [ ] **Docker deployment**: Full containerization

---

## 📊 API Endpoints Summary

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/core/register/` | ❌ | Register new user |
| POST | `/api/core/token/` | ❌ | Get JWT access + refresh |
| POST | `/api/core/token/refresh/` | ❌ | Refresh JWT |
| GET | `/api/core/profile/` | ✅ | Get user profile |
| POST | `/api/computing/submit-job/` | ✅ | Submit inference job |
| GET | `/api/computing/jobs/<id>/` | ✅ | Get job details (owner only) |
| GET | `/api/payments/wallet/` | ✅ | Get wallet balance + logs |
| POST | `/api/payments/deposit/` | ✅ | Create deposit transaction |
| POST | `/api/payments/webhook/mock/<id>/` | ❌ | Mock payment confirmation |
| WS | `/ws/computing/` | 🔌 | Agent WebSocket connection |

---

## 🧪 Test Coverage Summary

| File | Tests | Scope |
|------|-------|-------|
| `core/tests/test_models.py` | 3 | User creation, wallet ops |
| `core/tests/test_auth.py` | 13 | Registration, JWT, profile |
| `computing/tests/test_flow.py` | 13 | Job submission, credits, validation |
| `computing/tests/test_lifecycle.py` | 10 | Status transitions, detail API |
| `computing/tests/test_models.py` | 14 | Model constraints, defaults |
| `computing/tests/test_computing.py` | 4 | Matchmaking |
| `payments/tests/test_payments.py` | 9 | Credits, deposits, webhooks |
| **TOTAL** | **66** | |
