# Makefile for org-mode tangling and Python REPL
.PHONY: help install test lint run dev clean setup tangle detangle

help:
	@echo "Available targets:"
	@echo "  make tangle   - Extract code from org files"
	@echo "  make setup    - Initial setup and directory creation"
	@echo "  make install  - Install dependencies"
	@echo "  make test     - Run tests"
	@echo "  make lint     - Run linter"
	@echo "  make run      - Run the REPL"
	@echo "  make dev      - Run in development mode"
	@echo "  make clean    - Clean up generated files"
	@echo "  make detangle - Update org files from code (manual process)"

# Tangle org files to extract code
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

# Detangle - update org files from code changes
detangle:
	@echo "Detangling is not fully automated in org-mode."
	@echo "To update org files from code changes:"
	@echo "1. Open the org file in Emacs"
	@echo "2. Use org-babel-detangle (C-c C-v C-d) on code blocks"
	@echo "3. Or manually update the code blocks"

setup:
	@echo "Setting up project structure..."
	chmod +x setup.sh
	./setup.sh
	@echo "Creating virtual environment..."
	python3 -m venv venv
	@echo "Setup complete. Run 'source venv/bin/activate' then 'make install'"

install:
	pip install --upgrade pip
	pip install google-generativeai tiktoken pytest flake8 black

test:
	python -m pytest tests/ -v

lint:
	flake8 src/ --max-line-length=100 --ignore=E402
	black --check src/

format:
	black src/

run:
	python -m gemini_repl

dev:
	@echo "Starting in development mode..."
	LOG_LEVEL=DEBUG python -m gemini_repl

clean:
	rm -rf __pycache__ .pytest_cache
	rm -rf logs/*.log
	rm -f conversation.json
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	# Clean tangled files
	rm -rf src/ tests/ .github/
	rm -f setup.sh .env.example .envrc requirements.txt Dockerfile README.md
	rm -f architecture.mmd flow.mmd
