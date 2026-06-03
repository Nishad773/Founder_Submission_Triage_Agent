from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.extractor import analyze_documents
from app.parser import build_document_bundle
from app.schemas import AnalysisResponse
from app.utils import ensure_supported_file, load_environment


load_environment()


app = FastAPI(
    title="Founder Submission Triage Agent",
    description="Upload founder materials in PDF or PPTX format and receive structured investment analysis.",
    version="2.0.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


async def _read_upload(upload: UploadFile) -> tuple[str, bytes]:
    if not upload.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    try:
        ensure_supported_file(upload.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    file_bytes = await upload.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail=f"Uploaded file is empty: {upload.filename}")

    return upload.filename, file_bytes


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    file: UploadFile | None = File(default=None),
    pitch_deck: list[UploadFile] | None = File(default=None),
    financial_statements: list[UploadFile] | None = File(default=None),
    cap_table: list[UploadFile] | None = File(default=None),
    legal_documents: list[UploadFile] | None = File(default=None),
) -> AnalysisResponse:
    uploads_by_category = {
        "pitch_deck": list(pitch_deck or []),
        "financials": list(financial_statements or []),
        "cap_table": list(cap_table or []),
        "legal_docs": list(legal_documents or []),
    }

    if file is not None:
        uploads_by_category["pitch_deck"].append(file)

    if not any(uploads_by_category.values()):
        raise HTTPException(status_code=400, detail="Upload at least one PDF or PPTX document.")

    parsed_inputs: dict[str, list[tuple[str, bytes]]] = {key: [] for key in uploads_by_category}
    for category, uploads in uploads_by_category.items():
        for upload in uploads:
            parsed_inputs[category].append(await _read_upload(upload))

    try:
        bundle = build_document_bundle(parsed_inputs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to extract text: {exc}") from exc

    if not any(bundle.model_dump().values()):
        raise HTTPException(status_code=400, detail="No extractable text found in the uploaded documents.")

    return analyze_documents(bundle)
