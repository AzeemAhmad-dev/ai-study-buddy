"""Shared Gemini client helpers and error handling."""

from __future__ import annotations

import json
import logging
from typing import Any, TypeVar

import httpx
from fastapi import HTTPException, status
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, ValidationError

from app.config import Settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def create_gemini_client(settings: Settings) -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key)


def build_http_options(settings: Settings) -> types.HttpOptions:
    return types.HttpOptions(timeout=settings.gemini_request_timeout_ms)


def generate_text(
    client: genai.Client,
    *,
    model: str,
    contents: Any,
    settings: Settings,
    system_instruction: str | None = None,
    temperature: float | None = None,
    thinking_level: str | None = None,
) -> str:
    """Generate unstructured text from Gemini with centralized error handling."""
    config_kwargs: dict[str, Any] = {
        "http_options": build_http_options(settings),
    }
    if system_instruction:
        config_kwargs["system_instruction"] = system_instruction
    if temperature is not None:
        config_kwargs["temperature"] = temperature
    if thinking_level:
        config_kwargs["thinking_config"] = {"thinking_level": thinking_level}

    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(**config_kwargs),
        )
    except genai_errors.ClientError as exc:
        logger.exception("Gemini client error during text generation")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini API error: {exc}",
        ) from exc
    except genai_errors.ServerError as exc:
        logger.exception("Gemini server error during text generation")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini service is temporarily unavailable.",
        ) from exc
    except (httpx.TimeoutException, TimeoutError) as exc:
        logger.exception("Gemini request timed out during text generation")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Gemini request timed out. Try again with shorter input.",
        ) from exc
    except genai_errors.APIError as exc:
        logger.exception("Gemini API error during text generation")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini API error: {exc}",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during Gemini text generation")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating content.",
        ) from exc

    text = (response.text or "").strip()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini returned an empty response.",
        )
    return text


def generate_structured_content(
    client: genai.Client,
    *,
    model: str,
    contents: Any,
    settings: Settings,
    response_schema: type[T],
    system_instruction: str | None = None,
    temperature: float | None = None,
    thinking_level: str | None = None,
) -> T:
    """Generate JSON content constrained by a Pydantic response schema."""
    config_kwargs: dict[str, Any] = {
        "http_options": build_http_options(settings),
        "response_mime_type": "application/json",
        "response_schema": response_schema,
    }
    if system_instruction:
        config_kwargs["system_instruction"] = system_instruction
    if temperature is not None:
        config_kwargs["temperature"] = temperature
    if thinking_level:
        config_kwargs["thinking_config"] = {"thinking_level": thinking_level}

    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(**config_kwargs),
        )
    except genai_errors.ClientError as exc:
        logger.exception("Gemini client error during structured generation")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini API error: {exc}",
        ) from exc
    except genai_errors.ServerError as exc:
        logger.exception("Gemini server error during structured generation")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini service is temporarily unavailable.",
        ) from exc
    except (httpx.TimeoutException, TimeoutError) as exc:
        logger.exception("Gemini request timed out during structured generation")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Gemini request timed out. Try again with shorter input.",
        ) from exc
    except genai_errors.APIError as exc:
        logger.exception("Gemini API error during structured generation")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini API error: {exc}",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during Gemini structured generation")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating structured content.",
        ) from exc

    if isinstance(response.parsed, response_schema):
        return response.parsed

    raw_text = (response.text or "").strip()
    if not raw_text:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini returned an empty structured response.",
        )

    try:
        payload = json.loads(raw_text)
        return response_schema.model_validate(payload)
    except json.JSONDecodeError as exc:
        logger.exception("Failed to decode Gemini JSON response")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini returned malformed JSON that could not be parsed.",
        ) from exc
    except ValidationError as exc:
        logger.exception("Gemini JSON failed schema validation")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini response did not match the expected schema.",
        ) from exc
