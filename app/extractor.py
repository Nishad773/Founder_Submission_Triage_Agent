from __future__ import annotations

import os

from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from app.schemas import AnalysisResponse, DocumentBundle
from app.utils import MODEL_NAME, compact_json, load_environment


SYSTEM_PROMPT = (
    "You are an investment analyst assistant. "
    "Return strict JSON matching the schema. "
    "Use only supplied evidence. "
    "Set source to null when a field is not directly supported by the provided documents."
)


def _build_user_prompt(bundle: DocumentBundle, retry: bool = False) -> str:
    retry_note = "Previous output failed validation. Fix the JSON and schema exactly.\n" if retry else ""
    return (
        "Analyze the startup submission and produce an investment screening summary.\n"
        "Rules:\n"
        "- Use only these source labels when justified: Pitch Deck, Financial Statements, Cap Table, Legal Documents.\n"
        "- Do not fabricate source attribution.\n"
        "- red_flags must contain exactly 3 items.\n"
        "- investment_readiness_score must be an integer from 0 to 100.\n"
        "- strengths and concerns should be concise investor-facing points.\n"
        f"{retry_note}"
        "Document bundle:\n"
        f"{compact_json(bundle.model_dump())}"
    )


def _get_client() -> genai.Client:
    load_environment()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured.")
    return genai.Client(api_key=api_key)


def _request_analysis(client: genai.Client, bundle: DocumentBundle, retry: bool = False) -> AnalysisResponse:
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=_build_user_prompt(bundle, retry=retry),
        config=types.GenerateContentConfig(
            temperature=0.2,
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=AnalysisResponse,
        ),
    )

    if response.parsed is not None:
        return AnalysisResponse.model_validate(response.parsed)

    response_text = getattr(response, "text", "") or ""
    if not response_text:
        raise RuntimeError("Model returned an empty response.")

    return AnalysisResponse.model_validate_json(response_text)


def _map_gemini_error(exc: errors.APIError) -> Exception:
    detail = "Gemini API request failed."
    if exc.code == 400:
        detail = "Gemini rejected the request. Check prompt size or payload shape."
    elif exc.code == 401:
        detail = "GEMINI_API_KEY is invalid or unauthorized."
    elif exc.code == 429:
        detail = "Gemini quota exceeded. Check billing, credits, or project limits for this API key."
    elif exc.code and exc.code >= 500:
        detail = "Gemini service is temporarily unavailable."
    return RuntimeError(detail)


def analyze_documents(bundle: DocumentBundle) -> AnalysisResponse:
    client = _get_client()

    try:
        return _request_analysis(client, bundle)
    except (ValidationError, ValueError):
        try:
            return _request_analysis(client, bundle, retry=True)
        except errors.APIError as exc:
            raise _map_gemini_error(exc) from exc
        except (ValidationError, ValueError) as exc:
            raise RuntimeError(f"Model returned invalid structured JSON: {exc}") from exc
        except Exception as exc:
            raise RuntimeError(f"Gemini API error: {exc}") from exc
    except errors.APIError as exc:
        raise _map_gemini_error(exc) from exc
    except Exception as exc:
        raise RuntimeError(f"Gemini API error: {exc}") from exc
