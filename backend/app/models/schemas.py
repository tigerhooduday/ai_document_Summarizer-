# backend/app/models/schemas.py
from typing import Optional, Literal
from pydantic import BaseModel, Field, validator

ALLOWED_STYLES = ("brief", "detailed", "bullets")

class SummarizeRequest(BaseModel):
    text: Optional[str] = Field(None, description="Text to summarize (if not uploading a file).")
    style: Optional[Literal["brief", "detailed", "bullets"]] = Field(
        "brief", description="Summarization style: brief | detailed | bullets"
    )
    max_tokens: Optional[int] = Field(
        None, description="Optional max tokens limit for the LLM response."
    )

    @validator("text")
    def text_not_empty(cls, v):
        if v is not None:
            trimmed = v.strip()
            if trimmed == "":
                raise ValueError("text must not be empty")
            return trimmed
        return v

    @validator("max_tokens")
    def max_tokens_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("max_tokens must be a positive integer")
        return v

class SummarizeResponse(BaseModel):
    summary: str
    style: Literal["brief", "detailed", "bullets"]
