# GPU Connect — Project Makefile
# Usage:
#   make agent    — Build the standalone agent executable
#   make clean    — Remove build artifacts
#   make dev      — Start backend + frontend dev servers
#   make test     — Run backend test suite

.PHONY: agent clean dev test

# ─── Agent Build ──────────────────────────────────────────
agent:
	@echo "Building GPU Connect Agent..."
	cd agent && pyinstaller --clean --onefile --name gpu-connect-agent agent_ollama.py --distpath . --noconfirm
	@copy agent\gpu-connect-agent.exe frontend\public\downloads\gpu-connect.exe >nul 2>&1 || true
	@cd agent && if exist build rmdir /s /q build
	@cd agent && if exist gpu-connect-agent.spec del gpu-connect-agent.spec
	@echo "✅ Agent built: agent/gpu-connect-agent.exe"

# ─── Cleanup ─────────────────────────────────────────────
clean:
	@cd agent && if exist build rmdir /s /q build
	@cd agent && if exist dist rmdir /s /q dist
	@cd agent && if exist gpu-connect-agent.spec del gpu-connect-agent.spec
	@cd agent && if exist __pycache__ rmdir /s /q __pycache__
	@echo "🧹 Cleaned build artifacts"

# ─── Dev Servers ─────────────────────────────────────────
dev:
	@echo "Starting backend..."
	start cmd /k "cd backend && uv run python manage.py runserver 0.0.0.0:8000"
	@echo "Starting frontend..."
	start cmd /k "cd frontend && npm run dev"
	@echo "🚀 Dev servers started"

# ─── Tests ───────────────────────────────────────────────
test:
	cd backend && uv run pytest -v
