# GPU Connect - Peer-to-Peer AI Compute Platform

**GPU Connect** is a decentralized marketplace that democratizes access to high-performance AI compute. It allows users to monetize their idle GPUs (Providers) and enables researchers/developers to rent compute power (Consumers) for AI training and inference at a fraction of the cost of centralized cloud providers.

![Frontend Preview](https://via.placeholder.com/800x400?text=GPU+Connect+Dashboard+Preview)

## 🚀 Key Features

*   **Peer-to-Peer Architecture**: Direct connection between Consumers and GPU Providers via a central Broker.
*   **Real-Time Dispatch**: Low-latency Job dispatch using WebSockets and Celery.
*   **Secure Financials**: Robust Double-Entry Ledger system for handling "Compute Credits". credits are transferred atomically upon job completion.
*   **Premium UI**: A "Royal" themed frontend (Ivory/Gold) designed for a high-end user experience.
*   **Scalable Backend**: Built on Django + Channels (ASGI) for handling thousands of concurrent node connections.

## 🛠️ Tech Stack

### Backend (The Brain)
*   **Framework**: Python Django 5.0 + Django REST Framework
*   **Real-time**: Django Channels (WebSockets)
*   **Async Tasks**: Celery + Redis
*   **Database**: PostgreSQL
*   **Auth**: JWT (SimpleJWT)

### Frontend (The Face)
*   **Framework**: React + TypeScript + Vite
*   **Styling**: Custom CSS (Glassmorphism, Royal Theme)
*   **State**: React Hooks + Context

### Agent (The Muscle)
*   **Language**: Python
*   **Communication**: WebSockets (Secure WSS)
*   **Runtime**: Docker (Planned: gVisor Sandboxing)

## 🏃‍♂️ Local Setup

### Prerequisites
*   Python 3.11+
*   Node.js 18+
*   Docker & Docker Compose
*   `uv` (Python Package Manager)

### 1. Clone & Environment
```bash
git clone https://github.com/Himesh-29/GPU-For-Everyone.git
cd GPU-For-Everyone
```

### 2. Backend Setup
```bash
# Create virtual env
uv venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
uv pip install -r backend/requirements.txt
uv pip install pytest-django djangorestframework-simplejwt uvicorn[standard] channels-redis

# Run Migrations
cd backend
python manage.py migrate
```

### 3. Start Services
Ensure Docker Desktop is running for Redis/Postgres.
```bash
# Start Redis/DB (or use docker-compose)
docker-compose up -d redis db

# Run Backend Server
python manage.py runserver
```

### 4. Start Frontend
```bash
cd frontend
npm install
npm run dev
```
Visit `http://localhost:5173` to see the application.

## 🧪 Testing

We utilize `pytest` for the backend suite.
```bash
cd backend
uv run pytest
```

## 📜 License
MIT License.
