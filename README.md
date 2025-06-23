# Lawrence MVP

Lawrence is a minimal viable product (MVP) designed to automate and streamline the workflow of software product owners. It uses AI to clarify feature requirements and generate documentation. 

## Project Overview

The Lawrence MVP provides a REST API that:
- Accepts a software feature description.
- Generates clarifying questions if the feature is vague.
- Updates a Markdown document with feature details and pending questions.
- Maintains conversation context for iterative refinement.

## Prerequisites

- **Python**: 3.12
- **Ollama**: Installed and running with the `llama3:latest` model.

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

```bash
# Run all tests with coverage
python run_tests.py

# Run only unit tests
python run_tests.py unit

# Run only integration tests
python run_tests.py integration

# Run tests with pytest directly
pytest tests/ -v
```

### Test Structure

- **Unit Tests** (`tests/unit/`): Test individual functions and classes
- **Integration Tests** (`tests/integration/`): Test API endpoints and service interactions
- **Fixtures** (`tests/conftest.py`): Shared test data and mocks

### Coverage Reports

After running tests, coverage reports are generated in:
- `htmlcov/`: HTML coverage report
- `coverage.xml`: XML coverage report for CI tools
