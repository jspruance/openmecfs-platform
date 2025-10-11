# 🧠 Open ME/CFS API — Makefile
# Common developer commands for running, testing, and maintaining the FastAPI backend.

# === VARIABLES ===
PYTHON := python
PIP := pip
APP := main:app
VENV := venv

# === COMMANDS ===

# 🔧 Create or update virtual environment and install dependencies
install:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/Scripts/activate && $(PIP) install --upgrade pip
	$(VENV)/Scripts/activate && $(PIP) install -r requirements.txt

# 🚀 Run FastAPI development server
run:
	$(VENV)/Scripts/activate && uvicorn $(APP) --reload

# 🧪 Run tests
test:
	$(VENV)/Scripts/activate && pytest -v

# 🧹 Format + lint code
format:
	$(VENV)/Scripts/activate && black . && flake8 .

# 🗑️ Clean caches and temporary files
clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache *.log

# 🤖 (Optional) Run summarizer script manually
summarize:
	$(VENV)/Scripts/activate && python ../summarizer.py

# 📦 (Optional) Future deployment command placeholder
deploy:
	echo "🚀 Deploy script placeholder — add Render, Railway, or Supabase deploy here."

# === HELP ===
help:
	@echo "Available commands:"
	@echo "  make install    → Set up venv and install dependencies"
	@echo "  make run        → Start FastAPI server (http://127.0.0.1:8000)"
	@echo "  make test       → Run pytest suite"
	@echo "  make format     → Format and lint code"
	@echo "  make clean      → Remove cache files"
	@echo "  make summarize  → Run summarizer script (Phase 2)"
	@echo "  make deploy     → Placeholder for deployment"
