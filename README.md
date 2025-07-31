<div align="center">

# Lawrence Backend

[![GitHub](https://img.shields.io/github/license/mashape/apistatus.svg)](https://github.com/joacod/lawrence/blob/main/LICENSE)

[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)

</div>

## Introduction

Lawrence is a co‑pilot that automates the _requirements‑engineering_ workflow for software Product Owners and managers.

It uses AI to transform vague feature ideas into well‑structured specifications, and generates helpful documentation.

<p align="center">
  <img width="45%" src="https://github.com/joacod/lawrence/blob/main/readme-pics/app-example.webp" alt="App Thumbnail">
  <img width="45%" src="https://github.com/joacod/lawrence/blob/main/readme-pics/feature-overview.webp" alt="Feature Overview Thumbnail">
</p>

## Project Overview

This project provides a REST API that:

- Accepts a software feature description.
- Generates clarifying questions if the feature is vague.
- Updates the feature details and pending questions.
- Maintains conversation context for iterative refinement.
- Generates a feature overview including:
  - Feature description
  - Acceptance criteria
  - Backend tickets needed
  - Frontend tickets needed
- Endpoint to export the complete feature overview documentation as Markdown or PDF.

## Lawrence Frontend

The frontend is a separate project that provides a user interface for interacting with the Lawrence backend. It allows users to submit feature descriptions, view generated questions, and manage feature specifications.

You can find the frontend project here: [Lawrence UI](https://github.com/joacod/lawrence-ui)

## Prerequisites

- **Python**: 3.12
- **Ollama**: Installed and running with the follwing models:
  - `mistral:latest` (Advanced 7B model with enhanced reasoning)
  - `phi3:latest` (Lightweight 3B fast model for quick responses)

## Setup Instructions

Follow these steps to set up and run Lawrence locally.

### 1. Create a Virtual Environment

```bash
python3.12 -m venv venv
```

**Expected output**: Creates an isolated Python environment in `/lawrence/venv`.

### 2. Activate the Virtual Environment

Activates the virtual environment, updating your shell to use the isolated Python.

```bash
source venv/bin/activate
```

**Expected output**: Prompt changes to `(venv) user@machine:~/lawrence$`.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**What it does**: Installs project dependencies (FastAPI, LangChain, etc.) listed in `requirements.txt`.

### 4. Run the Service

```bash
python -m src.main
```

**What it does**: Starts the FastAPI server on `http://localhost:8000`.

## Testing

Lawrence uses a comprehensive testing framework to ensure code quality and reliability.

### Testing Libraries

- **pytest**: Main testing framework
- **pytest-asyncio**: Async test support
- **pytest-mock**: Mocking utilities
- **pytest-cov**: Code coverage reporting
- **httpx**: HTTP client for API testing
- **factory-boy**: Test data factories

### Running Tests

#### Run All Tests with Coverage

```bash
PYTHONPATH=. python run_tests.py
```

**What it does**: Runs the complete test suite with coverage reporting.

#### Run Only Unit Tests

```bash
PYTHONPATH=. python run_tests.py unit
```

**What it does**: Runs only unit tests for faster feedback during development.

#### Run Only Integration Tests

```bash
PYTHONPATH=. python run_tests.py integration
```

**What it does**: Runs only integration tests to verify API endpoints and service interactions.

#### Run Tests with Pytest Directly

```bash
PYTHONPATH=. pytest tests/ -v
```

**What it does**: Runs all tests with verbose output using pytest directly.

#### Run Tests with Coverage Reports

```bash
PYTHONPATH=. pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html:htmlcov
```

**What it does**: Runs tests with detailed coverage reporting in terminal and HTML format.

### Test Structure

- **Unit Tests** (`tests/unit/`): Test individual functions and classes
- **Integration Tests** (`tests/integration/`): Test API endpoints and service interactions
- **Fixtures** (`tests/conftest.py`): Shared test data and mocks

### Coverage Reports

After running tests, coverage reports are generated in:

- `htmlcov/`: HTML coverage report
- `coverage.xml`: XML coverage report for CI tools

## ☕️ Did you like the project?

You can collaborate with me giving a star ⭐️ to the project or

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/joacod)

Thanks! 😃
