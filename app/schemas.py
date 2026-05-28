from pydantic import BaseModel, Field


EXAMPLE_RESPONSE = {
    "company_name": "Accred AI",
    "sector": "EdTech",
    "stage": "Pre-seed",
    "funding_ask": "$500k",
    "traction_stats": [
        "8 college pilots",
        "1,200 student signups",
        "18% month-over-month activation growth",
    ],
    "business_model": "B2B SaaS sold to universities with annual platform licenses.",
    "red_flags": [
        "Proof of paid retention is limited.",
        "Buyer budget ownership is unclear.",
        "Competitive differentiation needs more evidence.",
    ],
}


class AnalysisResponse(BaseModel):
    company_name: str = Field(..., min_length=1, examples=["Accred AI"])
    sector: str = Field(..., min_length=1, examples=["EdTech"])
    stage: str = Field(..., min_length=1, examples=["Pre-seed"])
    funding_ask: str = Field(..., min_length=1, examples=["$500k"])
    traction_stats: list[str] = Field(
        ...,
        examples=[["8 college pilots", "1,200 student signups", "18% MoM growth"]],
    )
    business_model: str = Field(
        ...,
        min_length=1,
        examples=["B2B SaaS sold to universities with annual licenses."],
    )
    red_flags: list[str] = Field(
        ...,
        min_length=3,
        max_length=3,
        examples=[["Proof of paid retention is limited.", "Buyer budget is unclear.", "Differentiation needs more evidence."]],
    )

    model_config = {
        "json_schema_extra": {
            "example": EXAMPLE_RESPONSE,
        }
    }
