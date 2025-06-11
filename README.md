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

## Testing with Postman

Test the API using Postman or similar.

1. **Create a POST request** in Postman:
   - **URL**: `http://localhost:8000/process_feature`
   - **Body** (raw JSON):
     ```json
     {
         "session_id": null,
         "feature": "I want a login system with email and password"
     }
     ```
2. **Send the request**.
3. **Expected response**:
   ```json
   {
       "session_id": "abc123...",
       "response": "Got it. Questions: 1) Should it include two-factor authentication? 2) Is password recovery needed? 3) What frameworks or languages does the backend use?",
       "markdown": "# Feature: Login System\n\n## Details\n- Login with email and password.\n## Pending Questions\n- Should 2FA be included?\n- Is password recovery needed?\n- What is the backend framework?"
   }
   ```
4. **Iterate**:
   - Use the returned `session_id` in a new POST request to continue the conversation:
     ```json
     {
         "session_id": "abc123...",
         "feature": "Yes, include password recovery. Backend in Node.js."
     }
     ```
5. **Clear session** (optional):
   - **URL**: `DELETE http://localhost:8000/clear_session/{session_id}`
   - Example: `DELETE http://localhost:8000/clear_session/abc123...`
