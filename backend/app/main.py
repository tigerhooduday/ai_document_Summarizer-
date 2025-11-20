# backend/app/main.py
import os
import logging
from typing import List

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn
from dotenv import load_dotenv

# Load environment variables from backend/.env if present (development convenience)
env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=env_path)

# Basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("summarizer-backend")

# Import the router (ensure this file exists)
try:
    from app.api.summarize import router as summarize_router
except Exception as e:
    logger.exception("Failed to import summarize router. Ensure app/api/summarize.py exists.")
    raise

# Config
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
_allowed = os.getenv("FRONTEND_ALLOW_ORIGINS", "http://localhost:5173")
ALLOWED_ORIGINS: List[str] = [o.strip() for o in _allowed.split(",") if o.strip()]

app = FastAPI(
    title="Document Summarization Service",
    version="0.1.0",
    description="Simple service that accepts text or .txt file and returns an LLM-generated summary."
)

# CORS middleware so frontend can call us
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS or ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", summary="Service status")
async def root():
    return {"status": "ok", "service": "document-summarizer", "version": app.version}

# Include the summarization router under /api
app.include_router(summarize_router, prefix="/api")

# Error handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning("HTTP exception: %s %s -> %s", request.method, request.url, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error: %s %s -> %s", request.method, request.url, exc.errors())
    return JSONResponse(
        status_code=422,
        content={"detail": "Request validation failed", "errors": exc.errors()},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception for request %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=BACKEND_HOST, port=BACKEND_PORT, reload=True)
