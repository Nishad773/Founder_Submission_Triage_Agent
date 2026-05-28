from __future__ import annotations

import os

from fastapi import HTTPException
from openai import APIStatusError, OpenAI
from pydantic import ValidationError

from app.schemas import AnalysisResponse
from app.utils import load_environment, parse_json_content


SYSTEM_PROMPT = (
    "Extract startup deck facts. Return strict JSON only."
)


def _build_user_prompt(deck_text: str, retry: bool = False) -> str:
    retry_note = "\nPrevious output failed validation. Fix the JSON and schema exactly.\n" if retry else ""
    return (
        "Return these fields: company_name, sector, stage, funding_ask, traction_stats, business_model, red_flags.\n"
        "Rules: exactly 3 red_flags, concise strings, preserve metrics and currency, no markdown.\n"
        f"{retry_note}\nDeck text:\n{deck_text}"
    )


def _get_client() -> tuple[OpenAI, str]:
    load_environment()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured.")
    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return client, model


def _request_analysis(client: OpenAI, model: str, deck_text: str, retry: bool = False) -> str:
    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(deck_text, retry=retry)},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "founder_submission_triage",
                "strict": True,
                "schema": AnalysisResponse.model_json_schema(),
            },
        },
    )
    content = response.choices[0].message.content
    if not content:
        raise HTTPException(status_code=502, detail="Model returned an empty response.")
    return content


def _validate_model_output(content: str) -> AnalysisResponse:
    payload = parse_json_content(content)
    return AnalysisResponse.model_validate(payload)


def _map_openai_error(exc: APIStatusError) -> HTTPException:
    detail = "OpenAI API request failed."
    if exc.status_code == 401:
        detail = "OpenAI API key is invalid or unauthorized."
    elif exc.status_code == 429:
        detail = "OpenAI quota exceeded. Check billing, credits, or project limits for this API key."
    elif exc.status_code >= 500:
        detail = "OpenAI service is temporarily unavailable."
    return HTTPException(status_code=exc.status_code, detail=detail)


def analyze_pitch_deck(deck_text: str) -> AnalysisResponse:
    client, model = _get_client()

    try:
        content = _request_analysis(client, model, deck_text)
    except APIStatusError as exc:
        raise _map_openai_error(exc) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI API error: {exc}") from exc

    try:
        return _validate_model_output(content)
    except (ValueError, ValidationError):
        try:
            retry_content = _request_analysis(client, model, deck_text, retry=True)
            return _validate_model_output(retry_content)
        except APIStatusError as exc:
            raise _map_openai_error(exc) from exc
        except (ValueError, ValidationError) as exc:
            raise HTTPException(status_code=502, detail=f"Model returned invalid structured JSON: {exc}") from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"OpenAI API error: {exc}") from exc
