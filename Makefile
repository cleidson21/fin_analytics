PYTHON ?= python
VENV := .venv

ifeq ($(OS),Windows_NT)
VENV_BIN := $(VENV)/Scripts
PYTHON_BIN := $(VENV_BIN)/python.exe
PIP_BIN := $(VENV_BIN)/pip.exe
FIN_BIN := $(VENV_BIN)/fin.exe
else
VENV_BIN := $(VENV)/bin
PYTHON_BIN := $(VENV_BIN)/python
PIP_BIN := $(VENV_BIN)/pip
FIN_BIN := $(VENV_BIN)/fin
endif

ARGS ?=

.DEFAULT_GOAL := help

.PHONY: help setup install install-dev run test lint format typecheck check clean distclean

help:
	@printf "fin_analytics - available targets\n\n"
	@printf "  make setup        Create the virtual environment and install dev dependencies\n"
	@printf "  make install      Install runtime dependencies only\n"
	@printf "  make install-dev  Install runtime + dev dependencies\n\n"
	@printf "  make run          Run the application entry point (use ARGS=\"...\")\n"
	@printf "  make test         Run the test suite with coverage\n"
	@printf "  make lint         Lint the codebase with Ruff\n"
	@printf "  make format       Format the codebase with Ruff\n"
	@printf "  make typecheck    Run mypy in strict mode\n"
	@printf "  make check        Run lint, typecheck, then test\n\n"
	@printf "  make clean        Remove caches and generated artefacts\n"
	@printf "  make distclean    Remove the virtual environment\n"

$(VENV):
	@printf "Creating virtual environment...\n"
	$(PYTHON) -m venv $(VENV)
	$(PYTHON_BIN) -m pip install --upgrade pip

setup: $(VENV)
	@printf "Installing development dependencies...\n"
	$(PIP_BIN) install -e ".[dev]"
	@printf "Setup complete.\n"

install: $(VENV)
	@printf "Installing runtime dependencies...\n"
	$(PIP_BIN) install .
	@printf "Installation complete.\n"

install-dev: $(VENV)
	@printf "Installing development dependencies...\n"
	$(PIP_BIN) install -e ".[dev]"
	@printf "Installation complete.\n"

run: $(VENV)
	@printf "Running fin_analytics...\n"
	$(FIN_BIN) $(ARGS)

test: $(VENV)
	@printf "Running tests...\n"
	$(PYTHON_BIN) -m pytest tests

lint: $(VENV)
	@printf "Running Ruff lint...\n"
	$(PYTHON_BIN) -m ruff check src tests

format: $(VENV)
	@printf "Formatting with Ruff...\n"
	$(PYTHON_BIN) -m ruff format src tests
	$(PYTHON_BIN) -m ruff check --fix src tests

typecheck: $(VENV)
	@printf "Running mypy...\n"
	$(PYTHON_BIN) -m mypy src

check: lint typecheck test
	@printf "All checks passed.\n"

clean:
	@printf "Cleaning generated artefacts...\n"
	$(PYTHON) -c "from pathlib import Path; import shutil; root = Path('.'); [shutil.rmtree(path, ignore_errors=True) for path in root.rglob('__pycache__') if path.is_dir()]; [shutil.rmtree(path, ignore_errors=True) for path in root.rglob('.pytest_cache') if path.is_dir()]; [shutil.rmtree(path, ignore_errors=True) for path in root.rglob('.mypy_cache') if path.is_dir()]; [shutil.rmtree(path, ignore_errors=True) for path in root.rglob('.ruff_cache') if path.is_dir()]; [shutil.rmtree(path, ignore_errors=True) for path in root.rglob('build') if path.is_dir()]; [shutil.rmtree(path, ignore_errors=True) for path in root.rglob('dist') if path.is_dir()]; [shutil.rmtree(path, ignore_errors=True) for path in root.rglob('htmlcov') if path.is_dir()]; [shutil.rmtree(path, ignore_errors=True) for path in root.rglob('*.egg-info') if path.is_dir()]; [path.unlink(missing_ok=True) for path in root.rglob('.coverage') if path.is_file()]; [path.unlink(missing_ok=True) for pattern in ('*.pyc', '*.pyo') for path in root.rglob(pattern) if path.is_file()]"
	@printf "Clean complete.\n"

distclean: clean
	@printf "Removing virtual environment...\n"
	$(PYTHON) -c "from pathlib import Path; import shutil; shutil.rmtree(Path('.venv'), ignore_errors=True)"
	@printf "Virtual environment removed.\n"
