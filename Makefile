# Makefile


# [[file:PYTHON-GEMINI-REPL.org::*Makefile][Makefile:1]]
.PHONY: help install test lint run dev clean setup

help:
	@echo "Available targets:"
	@echo "  make setup    - Initial setup and directory creation"
	@echo "  make install  - Install dependencies"
	@echo "  make test     - Run tests"
	@echo "  make lint     - Run linter"
	@echo "  make run      - Run the REPL"
	@echo "  make dev      - Run in development mode"
	@echo "  make clean    - Clean up generated files"

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
# Makefile:1 ends here
