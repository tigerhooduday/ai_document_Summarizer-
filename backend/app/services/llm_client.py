# backend/app/services/llm_client.py
import os
import logging
import re
import time
from typing import Optional

# Attempt to import providers' SDKs; allow them to be missing.
try:
    import openai
except Exception:
    openai = None

try:
    from groq import Groq
except Exception:
    Groq = None

# Load .env if present
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger("llm-client")
logger.setLevel(os.getenv("LLM_LOG_LEVEL", "INFO"))

# -------------------------
# Configuration from env
# -------------------------
USE_STUB_ENV = os.getenv("USE_STUB", "false").lower() in ("1", "true", "yes")
USE_GROQ_ENV = os.getenv("USE_GROQ", "false").lower() in ("1", "true", "yes")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
# Timeout for groq requests in seconds (tunable)
GROQ_TIMEOUT = float(os.getenv("GROQ_TIMEOUT_SEC", "10.0"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
DEFAULT_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))

# Determine provider order
TRY_GROQ_FIRST = USE_GROQ_ENV or bool(GROQ_API_KEY)

# Exceptions placeholders
OpenAIError = Exception
OpenAIRateLimitError = Exception
try:
    from openai.error import OpenAIError as _OpenAIError, RateLimitError as _OpenAIRateLimitError  # type: ignore
    OpenAIError = _OpenAIError
    OpenAIRateLimitError = _OpenAIRateLimitError
except Exception:
    if openai is not None:
        OpenAIError = getattr(openai, "OpenAIError", Exception)
        OpenAIRateLimitError = getattr(openai, "RateLimitError", Exception)

# Groq exception placeholders (SDK varies). We'll inspect messages.
class GroqRateLimitError(Exception):
    pass

# Prompt templates
_PROMPTS = {
    "brief": "Summarize the following text in 2-4 concise sentences, focusing on main points and outcomes.",
    "detailed": (
        "Provide a detailed summary of the following text. Explain the main points, context, "
        "and any implications. Use clear paragraphs and make sure key facts are included."
    ),
    "bullets": "Summarize the following text as concise bullet points. Each bullet should be short and focus on one idea."
}


class LLMError(RuntimeError):
    """Generic wrapper for LLM-related errors."""


def build_prompt(style: str, text: str) -> str:
    header = _PROMPTS.get(style, _PROMPTS["brief"])
    return f"{header}\n\nText to summarize:\n\"\"\"\n{text}\n\"\"\"\n\nSummary:"


# ---------------------------
# Local dev stub
# ---------------------------
def _stub_summary(text: str, style: str) -> str:
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    if not sentences:
        return "[STUB] (no usable sentences found in text)"

    if style == "brief":
        take = 2
        out = " ".join(sentences[:take])
        return f"[STUB - brief] {out}"

    if style == "detailed":
        take = 4
        joined = " ".join(sentences[:take])
        words = joined.split()
        if len(words) > 120:
            joined = " ".join(words[:120]) + "..."
        return f"[STUB - detailed] {joined}"

    bullets = []
    for s in sentences[:10]:
        w = s.split()
        snippet = " ".join(w[:12])
        if len(w) > 12:
            snippet = snippet + "..."
        bullets.append(f"- {snippet}")
        if len(bullets) >= 5:
            break
    return "[STUB - bullets]\n" + "\n".join(bullets)


# ---------------------------
# Groq caller (with timeout handling)
# ---------------------------
def _call_groq(prompt: str, max_tokens: Optional[int]) -> str:
    """
    Call Groq with a timeout. The Groq SDK has varied signatures across versions,
    so we attempt several ways to pass a timeout. If Groq raises network/timeout/quota errors,
    we surface them in a way the caller can detect and fallback.
    """
    if Groq is None:
        raise LLMError("Groq SDK is not installed. Please `pip install groq` to use Groq provider.")

    logger.info("Attempting Groq call (model=%s, timeout=%ss)", GROQ_MODEL, GROQ_TIMEOUT)

    # Instantiate client while trying common timeout param names.
    client = None
    inst_errors = []
    try_kwargs = [
        {"api_key": GROQ_API_KEY, "timeout": GROQ_TIMEOUT},
        {"api_key": GROQ_API_KEY, "request_timeout": GROQ_TIMEOUT},
        {"api_key": GROQ_API_KEY},
        {},
    ]
    for kw in try_kwargs:
        try:
            # Only pass api_key if value present to avoid passing None
            kw_clean = {k: v for k, v in kw.items() if v is not None}
            client = Groq(**kw_clean) if kw_clean else Groq()
            logger.debug("Groq client instantiated with kwargs: %s", kw_clean)
            break
        except TypeError as te:
            inst_errors.append(("TypeError", str(te)))
            continue
        except Exception as e:
            inst_errors.append(("Exception", str(e)))
            continue

    if client is None:
        logger.error("Failed to instantiate Groq client. Attempts: %s", inst_errors)
        raise LLMError("Failed to instantiate Groq client.")

    # Prepare messages and call. We'll implement our own timeout guard via time checks
    messages = [
        {"role": "system", "content": "You are a helpful summarization assistant."},
        {"role": "user", "content": prompt},
    ]
    # Some Groq client versions accept a timeout param on the method call; try that first.
    call_attempts = []
    start = time.time()
    try:
        try:
            resp = client.chat.completions.create(messages=messages, model=os.getenv("GROQ_MODEL", GROQ_MODEL), timeout=GROQ_TIMEOUT)
            call_attempts.append("create(timeout)")
        except TypeError:
            # method may not accept timeout kw; try without and rely on client-level timeout
            resp = client.chat.completions.create(messages=messages, model=os.getenv("GROQ_MODEL", GROQ_MODEL))
            call_attempts.append("create()")
    except Exception as e:
        # inspect message for quota/rate/timeout hints
        elapsed = time.time() - start
        msg = str(e).lower()
        logger.exception("Groq call failed after %.2fs. attempts=%s error=%s", elapsed, call_attempts, e)
        if "quota" in msg or "rate" in msg or "429" in msg or "timeout" in msg or "timed out" in msg:
            # treat as rate/timeout so caller may fallback
            raise GroqRateLimitError(e)
        raise LLMError(f"Groq API error: {e}")

    # Parse response generically (object-like or dict-like)
    choices = getattr(resp, "choices", None) or resp.get("choices", [])
    if not choices:
        raise LLMError("Groq returned no choices.")
    first = choices[0]
    message = getattr(first, "message", None) or first.get("message", {})
    content = getattr(message, "content", None) or message.get("content", "") or first.get("text", "")
    return content.strip()


# ---------------------------
# OpenAI callers (v2 and v1)
# ---------------------------
def _call_openai_v2(prompt: str, max_tokens: Optional[int]) -> str:
    if openai is None:
        raise LLMError("OpenAI SDK is not installed (v2 path).")

    OpenAI = getattr(openai, "OpenAI", None)
    if OpenAI is None:
        raise LLMError("OpenAI v2 client class not present in installed SDK.")

    # Provide credentials via environment for compatibility
    if OPENAI_API_KEY:
        os.environ.setdefault("OPENAI_API_KEY", OPENAI_API_KEY)
    if OPENAI_API_BASE:
        os.environ.setdefault("OPENAI_API_BASE", OPENAI_API_BASE)
        os.environ.setdefault("OPENAI_API_BASE_URL", OPENAI_API_BASE)

    try:
        client = OpenAI()
    except Exception as e:
        logger.exception("Failed to instantiate OpenAI client: %s", e)
        raise LLMError(f"Failed to instantiate OpenAI client: {e}")

    messages = [
        {"role": "system", "content": "You are a helpful summarization assistant."},
        {"role": "user", "content": prompt},
    ]
    create_args = {"model": OPENAI_MODEL, "messages": messages, "temperature": float(DEFAULT_TEMPERATURE)}
    if max_tokens:
        create_args["max_tokens"] = int(max_tokens)

    try:
        resp = client.chat.completions.create(**create_args)
        choices = getattr(resp, "choices", None) or resp.get("choices", [])
        if not choices:
            raise LLMError("LLM returned no choices (openai v2).")
        first = choices[0]
        message = getattr(first, "message", None) or first.get("message", {})
        content = getattr(message, "content", None) or message.get("content", "") or first.get("text", "")
        return content.strip()
    except OpenAIRateLimitError as e:
        logger.warning("OpenAI v2 rate/quotas: %s", e)
        raise
    except OpenAIError as e:
        logger.exception("OpenAI v2 API error: %s", e)
        raise LLMError(f"OpenAI API error: {e}")
    except Exception as e:
        logger.exception("OpenAI v2 unexpected error: %s", e)
        raise LLMError(f"OpenAI v2 unexpected error: {e}")


def _call_openai_v1(prompt: str, max_tokens: Optional[int]) -> str:
    if openai is None:
        raise LLMError("OpenAI SDK is not installed (v1 path).")

    if OPENAI_API_KEY:
        try:
            openai.api_key = OPENAI_API_KEY  # type: ignore
        except Exception:
            pass
    if OPENAI_API_BASE:
        try:
            openai.api_base = OPENAI_API_BASE  # type: ignore
        except Exception:
            pass

    params = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful summarization assistant."},
            {"role": "user", "content": prompt},
        ],
        "temperature": DEFAULT_TEMPERATURE,
    }
    if max_tokens:
        params["max_tokens"] = int(max_tokens)

    try:
        resp = openai.ChatCompletion.create(**params)  # type: ignore
        choices = resp.get("choices", [])
        if not choices:
            raise LLMError("LLM returned no choices (openai v1).")
        first = choices[0]
        message = first.get("message") or {}
        content = message.get("content") or first.get("text") or ""
        return content.strip()
    except OpenAIRateLimitError as e:
        logger.warning("OpenAI v1 rate/quotas: %s", e)
        raise
    except OpenAIError as e:
        logger.exception("OpenAI v1 API error: %s", e)
        raise LLMError(f"OpenAI API error: {e}")
    except Exception as e:
        logger.exception("OpenAI v1 unexpected error: %s", e)
        raise LLMError(f"OpenAI v1 unexpected error: {e}")


# ---------------------------
# Public summarization function with provider selection and fallback logic
# ---------------------------
def summarize_text(text: str, style: str = "brief", max_tokens: Optional[int] = None) -> str:
    """
    Summarize text with provider selection:
      - If USE_STUB is true -> return local stub
      - If TRY_GROQ_FIRST -> attempt Groq (with timeout), then OpenAI v2/v1, then stub on quota/errors
      - Else -> attempt OpenAI (v2 then v1), then Groq if configured, then stub
    """
    # Stub override
    use_stub = USE_STUB_ENV or (os.getenv("USE_STUB", "false").lower() in ("1", "true", "yes"))
    if use_stub:
        logger.info("USE_STUB is enabled — returning local stub summary (no LLM call).")
        return _stub_summary(text, style)

    if style not in _PROMPTS:
        raise ValueError("Unsupported style")

    prompt = build_prompt(style, text)

    # Helper to try provider and fall back to stub on rate/quota or timeout errors
    def try_provider(fn, provider_name: str):
        try:
            return fn(prompt, max_tokens)
        except (GroqRateLimitError, OpenAIRateLimitError) as e:
            logger.warning("%s reported rate/quota error: %s — falling back to stub.", provider_name, e)
            return _stub_summary(text, style)
        except LLMError:
            # propagate provider-side application errors
            raise
        except Exception as e:
            # Inspect for timeout/quota keywords, fallback to stub if detected
            msg = str(e).lower()
            if "timeout" in msg or "timed out" in msg or "quota" in msg or "rate" in msg or "429" in msg:
                logger.warning("%s error suggests timeout/quota: %s — falling back to stub.", provider_name, e)
                return _stub_summary(text, style)
            logger.exception("%s unexpected error: %s", provider_name, e)
            # wrap as LLMError
            raise LLMError(f"{provider_name} unexpected error: {e}")

    # Provider order
    providers_tried = []

    if TRY_GROQ_FIRST:
        providers_tried.append("groq")
        try:
            logger.info("Trying Groq as primary provider.")
            return try_provider(_call_groq, "Groq")
        except LLMError:
            raise
        except Exception:
            logger.exception("Groq attempt failed; will try OpenAI if configured.")

    # Try OpenAI first (v2 then v1)
    if openai is not None:
        providers_tried.append("openai_v2")
        try:
            if hasattr(openai, "OpenAI"):
                logger.info("Trying OpenAI v2.")
                return try_provider(_call_openai_v2, "OpenAI v2")
        except LLMError:
            raise
        except Exception:
            logger.exception("OpenAI v2 failed; trying v1 if available.")

        try:
            logger.info("Trying OpenAI v1.")
            return try_provider(_call_openai_v1, "OpenAI v1")
        except LLMError:
            raise
        except Exception:
            logger.exception("OpenAI v1 failed; will try Groq if configured.")

    # If not tried Groq yet and Groq is configured, try Groq now
    if not TRY_GROQ_FIRST and (Groq is not None or GROQ_API_KEY):
        try:
            logger.info("Trying Groq as secondary provider.")
            return try_provider(_call_groq, "Groq")
        except LLMError:
            raise
        except Exception:
            logger.exception("Groq attempt failed; falling back to stub.")

    logger.warning("No provider succeeded (tried: %s). Returning stub summary.", providers_tried)
    return _stub_summary(text, style)
