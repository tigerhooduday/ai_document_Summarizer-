# backend/app/api/summarize.py
import os
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Request
from pydantic import ValidationError

from app.models.schemas import SummarizeRequest, SummarizeResponse
from app.services.llm_client import summarize_text, LLMError

# File parsing libraries (import at module level; if missing, raise helpful error when used)
try:
    import PyPDF2
except Exception:
    PyPDF2 = None

try:
    import docx  # python-docx
except Exception:
    docx = None

try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None

try:
    from striprtf.striprtf import rtf_to_text
except Exception:
    rtf_to_text = None

router = APIRouter()
logger = logging.getLogger("summarize-router")
logger.setLevel(os.getenv("API_LOG_LEVEL", "INFO"))

# Default max upload size: 2 MB (you can override via env MAX_UPLOAD_BYTES)
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(2 * 1024 * 1024)))


def _extract_text_from_pdf_bytes(data: bytes) -> str:
    if PyPDF2 is None:
        raise RuntimeError("PyPDF2 is not installed. Please `pip install PyPDF2` to parse PDF files.")
    try:
        reader = PyPDF2.PdfReader(io_bytes := data)
        # PyPDF2 accepts a stream or bytes? Construct from bytes using PdfReader(io.BytesIO(data))
    except Exception:
        # Some PyPDF2 versions want a file-like object
        pass

    # Use BytesIO approach for broad compatibility
    from io import BytesIO

    try:
        stream = BytesIO(data)
        reader = PyPDF2.PdfReader(stream)
        texts = []
        for p in reader.pages:
            try:
                texts.append(p.extract_text() or "")
            except Exception:
                continue
        return "\n".join(texts).strip()
    except Exception as e:
        raise RuntimeError(f"Failed to parse PDF: {e}")


def _extract_text_from_docx_bytes(data: bytes) -> str:
    if docx is None:
        raise RuntimeError("python-docx is not installed. Please `pip install python-docx` to parse .docx files.")
    from io import BytesIO
    try:
        doc = docx.Document(BytesIO(data))
        paragraphs = [p.text for p in doc.paragraphs if p.text]
        return "\n".join(paragraphs).strip()
    except Exception as e:
        raise RuntimeError(f"Failed to parse DOCX: {e}")


def _extract_text_from_html_bytes(data: bytes) -> str:
    if BeautifulSoup is None:
        raise RuntimeError("beautifulsoup4 is not installed. Please `pip install beautifulsoup4` to parse HTML files.")
    try:
        text = data.decode("utf-8", errors="ignore")
        soup = BeautifulSoup(text, "html.parser")
        return soup.get_text(separator="\n").strip()
    except Exception as e:
        raise RuntimeError(f"Failed to parse HTML: {e}")


def _extract_text_from_rtf_bytes(data: bytes) -> str:
    if rtf_to_text is None:
        raise RuntimeError("striprtf is not installed. Please `pip install striprtf` to parse RTF files.")
    try:
        text = data.decode("utf-8", errors="ignore")
        return rtf_to_text(text).strip()
    except Exception as e:
        raise RuntimeError(f"Failed to parse RTF: {e}")


def _extract_text_from_bytes_guess(data: bytes, filename: Optional[str] = None, content_type: Optional[str] = None) -> str:
    """
    Try to extract text from uploaded bytes by checking extension, content-type, and falling back to utf-8 decode.
    """
    # check filename extension
    ext = (filename or "").lower().split(".")[-1] if filename and "." in filename else ""

    # Use content-type when available for hint (e.g., application/pdf)
    ct = (content_type or "").lower()

    # PDF detection
    if ext == "pdf" or "pdf" in ct:
        return _extract_text_from_pdf_bytes(data)

    # DOCX
    if ext in ("docx", "doc") or "word" in ct:
        # note: .doc (binary) not supported by python-docx; will likely fail
        return _extract_text_from_docx_bytes(data)

    # HTML
    if ext in ("html", "htm") or "html" in ct:
        return _extract_text_from_html_bytes(data)

    # RTF
    if ext == "rtf" or "rtf" in ct:
        return _extract_text_from_rtf_bytes(data)

    # Plain text / markdown
    if ext in ("txt", "md", "markdown") or ct.startswith("text/"):
        try:
            return data.decode("utf-8").strip()
        except Exception:
            return data.decode("latin-1", errors="ignore").strip()

    # Heuristic: try PDF magic bytes
    if len(data) > 4 and data[:4] == b"%PDF":
        return _extract_text_from_pdf_bytes(data)

    # As last resort try UTF-8 decode
    try:
        return data.decode("utf-8", errors="ignore").strip()
    except Exception:
        return data.decode("latin-1", errors="ignore").strip()


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_endpoint(
    request: Request,
    text: Optional[str] = Form(None),
    style: Optional[str] = Form("brief"),
    max_tokens: Optional[int] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """
    Summarize text provided either by `text` or by uploading a file. Supports many file types.
    """
    parsed_text = text

    # If JSON body provided, use it (application/json)
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        try:
            body = await request.json()
            parsed_text = body.get("text", parsed_text)
            style = body.get("style", style)
            max_tokens = body.get("max_tokens", max_tokens)
        except Exception:
            pass

    # If file uploaded and text not given, try to extract text from file
    if file and (parsed_text is None or parsed_text.strip() == ""):
        filename = file.filename or "uploaded"
        # Read bytes (enforce size)
        contents = await file.read()
        if len(contents) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail=f"Uploaded file is too large. Max {MAX_UPLOAD_BYTES} bytes allowed.")
        # Determine content-type header from UploadFile if possible
        ctype = getattr(file, "content_type", None)
        # Try to extract
        try:
            parsed_text = _extract_text_from_bytes_guess(contents, filename=filename, content_type=ctype)
        except RuntimeError as e:
            # parsing failed for that file type
            raise HTTPException(status_code=400, detail=str(e))

    # Final validation
    if parsed_text is None or parsed_text.strip() == "":
        raise HTTPException(status_code=400, detail="No text provided. Provide 'text' or upload a file with readable text.")

    # Validate style
    if style not in ("brief", "detailed", "bullets"):
        raise HTTPException(status_code=400, detail=f"Invalid style '{style}'. Allowed: brief | detailed | bullets")

    # Validate request model (Pydantic)
    try:
        req = SummarizeRequest(text=parsed_text, style=style, max_tokens=max_tokens)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Call LLM client
    try:
        summary = summarize_text(req.text, req.style, req.max_tokens)
        return SummarizeResponse(summary=summary, style=req.style)
    except LLMError as e:
        logger.warning("LLM error: %s", e)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error during summarization: %s", e)
        raise HTTPException(status_code=500, detail="Unexpected server error while summarizing text.")
