from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SourceLabel = Literal["Pitch Deck", "Financial Statements", "Cap Table", "Legal Documents"]


class AttributedValue(BaseModel):
    value: str = Field(..., min_length=1)
    source: SourceLabel | None = None


class InsightItem(BaseModel):
    value: str = Field(..., min_length=1)
    source: SourceLabel | None = None


class DocumentBundle(BaseModel):
    pitch_deck: str = ""
    financials: str = ""
    cap_table: str = ""
    legal_docs: str = ""


EXAMPLE_RESPONSE = {
    "company_name": {"value": "Accred AI", "source": "Pitch Deck"},
    "sector": {"value": "Private markets / investment platform", "source": "Pitch Deck"},
    "stage": {"value": "Early stage", "source": "Pitch Deck"},
    "funding_ask": {"value": "Not explicitly stated", "source": None},
    "traction_stats": [
        {"value": "Live product", "source": "Pitch Deck"},
        {"value": "Active members", "source": "Pitch Deck"},
        {"value": "Real deals", "source": "Pitch Deck"},
    ],
    "business_model": {
        "value": "Membership-led private market platform for accredited investors with AI-assisted discovery, diligence, and matching.",
        "source": "Pitch Deck",
    },
    "red_flags": [
        {"value": "Funding ask is not clearly stated.", "source": None},
        {"value": "Evidence of revenue scale is limited in the supplied materials.", "source": "Pitch Deck"},
        {"value": "Regulatory execution complexity appears high.", "source": "Pitch Deck"},
    ],
    "investment_readiness_score": 78,
    "strengths": [
        {"value": "Clear problem-solution framing for accredited investors.", "source": "Pitch Deck"},
        {"value": "Compliance workflow is highlighted as a core capability.", "source": "Pitch Deck"},
    ],
    "concerns": [
        {"value": "Commercial traction is still lightly evidenced.", "source": "Pitch Deck"},
        {"value": "Some critical investment facts may require corroboration outside the deck.", "source": None},
    ],
}


class AnalysisResponse(BaseModel):
    company_name: AttributedValue
    sector: AttributedValue
    stage: AttributedValue
    funding_ask: AttributedValue
    traction_stats: list[InsightItem] = Field(default_factory=list)
    business_model: AttributedValue
    red_flags: list[InsightItem] = Field(..., min_length=3, max_length=3)
    investment_readiness_score: int = Field(..., ge=0, le=100)
    strengths: list[InsightItem] = Field(default_factory=list)
    concerns: list[InsightItem] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "example": EXAMPLE_RESPONSE,
        }
    }
