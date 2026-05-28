from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.extractor import analyze_pitch_deck
from app.parser import extract_text
from app.schemas import AnalysisResponse
from app.utils import ensure_supported_file, load_environment

load_environment()


app = FastAPI(
    title="Founder Submission Triage Agent",
    description="Upload a startup pitch deck in PDF or PPTX format and receive structured JSON.",
    version="1.0.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(file: UploadFile = File(...)) -> AnalysisResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    try:
        extension = ensure_supported_file(file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        extracted_text = extract_text(file_bytes, extension)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to extract text: {exc}") from exc

    if not extracted_text:
        raise HTTPException(status_code=400, detail="No extractable text found in the uploaded file.")

    return analyze_pitch_deck(extracted_text)
