# Devcontainer Setup for Gemini REPL

This devcontainer configuration provides a ready-to-use development environment for the Gemini REPL project.

## Features

- **Base Image**: Python 3.11 on Debian Bullseye
- **Package Manager**: UV (installed automatically)
- **Shell**: Zsh with Oh My Zsh
- **VS Code Extensions**: Python, Pylance, Ruff, TOML support

## Automatic Setup

When the container starts, it will automatically:

1. Install UV package manager
2. Run `make setup` to install all dependencies
3. Configure shell to activate the virtual environment

## Usage

### GitHub Codespaces
1. Click "Code" → "Create codespace on main"
2. Wait for the container to build and setup to complete
3. Open a terminal and verify with: `scripts/validate_setup.sh`

### VS Code Dev Containers
1. Install the "Dev Containers" extension
2. Open the project folder
3. Click "Reopen in Container" when prompted
4. Wait for setup to complete

## Post-Setup

After the container is ready:

1. Copy and configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

2. Run the validation script:
   ```bash
   ./scripts/validate_setup.sh
   ```

3. Start the REPL:
   ```bash
   make run
   ```

## Troubleshooting

If the automatic setup fails:

1. Open a terminal in the container
2. Run the setup manually:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source $HOME/.cargo/env
   make setup
   source .venv/bin/activate
   ```

3. Verify with the validation script
