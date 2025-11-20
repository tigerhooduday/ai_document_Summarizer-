# Backend README — Document Summarization Service

This backend is a FastAPI application that exposes an endpoint to summarize text using an LLM (OpenAI by default).

## Files
- `app/main.py` - FastAPI app entrypoint, CORS, error handlers.
- `app/api/summarize.py` - Router with `/api/summarize` endpoint. Supports JSON body or multipart/form-data with file upload.
- `app/services/llm_client.py` - LLM wrapper exposing `summarize_text`.
- `app/models/schemas.py` - Pydantic request and response models.

## Environment variables
Create `backend/.env` (do NOT commit) with at least:

OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
BACKEND_PORT=8000
FRONTEND_ALLOW_ORIGINS=http://localhost:5173