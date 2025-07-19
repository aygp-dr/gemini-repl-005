# Makefile for Gemini REPL - Simplified with script delegation

.PHONY: help setup lint test build run clean tangle detangle all repl gemini-repl test-expect monitor dev-repl

# Default target
all: setup lint test

help:
	@echo "Gemini REPL Development Commands:"
	@echo "  make setup    - Set up development environment with uv"
	@echo "  make lint     - Run linters (ruff, mypy)"
	@echo "  make test     - Run test suite with coverage"
	@echo "  make build    - Build distribution packages"
	@echo "  make run      - Run the REPL"
	@echo "  make repl     - Run the REPL (alias for 'uv run python -m gemini_repl')"
	@echo "  make monitor  - Show commands for monitoring REPL logs"
	@echo "  make dev-repl - Run REPL in development mode (logs to logs/)"
	@echo "  make clean    - Clean generated files"
	@echo ""
	@echo "Org-mode Commands:"
	@echo "  make tangle   - Extract code from PYTHON-GEMINI-REPL.org"
	@echo "  make detangle - Update org from code (manual process)"

# Development commands - delegate to scripts
setup:
	@./scripts/setup.sh

lint:
	@./scripts/lint.sh

test:
	@./scripts/test.sh

build:
	@./scripts/build.sh

run:
	@./scripts/run.sh

# Org-mode tangling
tangle:
	@echo "Tangling org files..."
	@if command -v emacs >/dev/null 2>&1; then \
		emacs --batch --eval "(require 'org)" \
			--eval "(setq org-src-preserve-indentation t)" \
			--eval "(setq org-babel-default-header-args '((:mkdirp . \"yes\") (:comments . \"both\")))" \
			--eval "(org-babel-tangle-file \"PYTHON-GEMINI-REPL.org\")" \
			--eval "(kill-emacs)"; \
		echo "✓ Tangled PYTHON-GEMINI-REPL.org"; \
	else \
		echo "Error: Emacs not found. Please install Emacs to use org-babel-tangle."; \
		exit 1; \
	fi

detangle:
	@echo "Detangling requires manual Emacs interaction:"
	@echo "1. Open PYTHON-GEMINI-REPL.org in Emacs"
	@echo "2. Use C-c C-v C-d on code blocks to update from source files"

# Clean up
clean:
	@echo "Cleaning generated files..."
	@rm -rf __pycache__ .pytest_cache build/ dist/ *.egg-info
	@rm -rf logs/*.log
	@rm -f conversation.json
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@echo "✓ Clean complete"

# Clean tangled files
clean-tangled:
	@echo "Cleaning tangled files..."
	@rm -rf src/ tests/ .github/
	@rm -f setup.sh .env.example .envrc requirements.txt Dockerfile README.md
	@rm -f architecture.mmd flow.mmd
	@rm -f Makefile.tangled
	@echo "✓ Cleaned all tangled files"

# Quick commands
dev: setup
	@echo "Development environment ready. Activate with: source .venv/bin/activate"

check: lint test
	@echo "✓ All checks passed"

# Run the REPL
repl gemini-repl:
	@uv run python -m gemini_repl

# Run expect tests
test-expect:
	@echo "Running expect tests..."
	@cd experiments/repl-testing && \
		for test in test_*.exp; do \
			if [ -x "$$test" ]; then \
				echo "\n--- Running $$test ---"; \
				timeout 30 ./$$test || echo "FAILED: $$test"; \
			fi \
		done

# Monitor REPL logs via tail
monitor:
	@echo "Monitoring REPL logs..."
	@echo "Use: tail -f ~/.gemini/gemini-repl.log"
	@echo "Or for development: tail -f logs/gemini.log"

# Development mode (logs to logs/ instead of ~/.gemini)
dev-repl:
	@echo "Running REPL in development mode..."
	@GEMINI_DEV_MODE=true uv run python -m gemini_repl

# Install pre-commit hooks
hooks: .venv/bin/activate
	@echo "Installing pre-commit hooks..."
	@source .venv/bin/activate && \
		pip install pre-commit && \
		pre-commit install
	@echo "✓ Pre-commit hooks installed"

# Generate README.md from README.org
README.md: README.org
	@echo "Generating $@ from $<..."
	@emacs --batch --eval "(require 'org)" \
		--eval "(find-file \"$<\")" \
		--eval "(org-md-export-to-markdown)" \
		--eval "(kill-emacs)"
	@echo "✓ $@ generated"
