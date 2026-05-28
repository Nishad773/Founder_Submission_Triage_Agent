# Founder Submission Triage Agent

Minimal FastAPI service that accepts a startup pitch deck in `PDF` or `PPTX`, extracts the most relevant text, sends a compact prompt to the OpenAI API, validates the response with Pydantic, and returns clean structured JSON.

## Stack

- Python
- FastAPI
- OpenAI API
- PyMuPDF
- python-pptx
- Pydantic

## Project Structure

```text
app/
  main.py
  parser.py
  extractor.py
  schemas.py
  utils.py
requirements.txt
README.md
.env.example
sample_output/
  output.json
sample_files/
  placeholder.txt
```

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy environment variables:

```bash
cp .env.example .env
```

4. Start the API:

```bash
uvicorn app.main:app --reload
```

5. Open Swagger docs:

`http://127.0.0.1:8000/docs`

## Environment Variables

- `OPENAI_API_KEY`: required API key for OpenAI.
- `OPENAI_MODEL`: optional model name. Defaults to `gpt-4o-mini`.

## Architecture

- `app/main.py`: FastAPI entrypoint and request handling.
- `app/parser.py`: PDF/PPTX extraction and deck-text preparation.
- `app/extractor.py`: OpenAI request logic, schema validation, and retry flow.
- `app/schemas.py`: response schema and Swagger examples.
- `app/utils.py`: normalization, prioritization, env loading, and shared helpers.

## Design Decisions

- Keep the stack small: FastAPI, OpenAI SDK, PyMuPDF, python-pptx, Pydantic.
- No agents, vector database, queues, or persistence for the MVP.
- Preserve headings, metrics, and slide/page boundaries because those are often the highest-signal parts of a deck.
- Strip repeated short footer/header noise before the LLM call to reduce wasted tokens.
- Prioritize lines with metrics and fundraising/business keywords so large decks fit into a smaller context window.
- Use strict `json_schema` output plus Pydantic validation to reduce malformed responses.

## API

### `POST /analyze`

Accepts multipart form-data with one file field named `file`.

Supported file types:

- `.pdf`
- `.pptx`

## curl Example

```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample-deck.pdf"
```

## Sample Output

```json
{
  "company_name": "Acme Robotics",
  "sector": "Industrial automation",
  "stage": "Seed",
  "funding_ask": "$2M",
  "traction_stats": [
    "$420k ARR",
    "18 enterprise customers",
    "22% month-over-month revenue growth"
  ],
  "business_model": "Annual SaaS contracts sold to warehouse operators.",
  "red_flags": [
    "Customer concentration is high.",
    "Gross margin trend is not clearly shown.",
    "Go-to-market hiring plan is underspecified."
  ]
}
```

A sample JSON file is included at [sample_output/output.json](/D:/Founder%20Submission%20Triage%20%20Agent/sample_output/output.json:1).

## Error Handling

The API returns clear `4xx` and `5xx` responses for:

- unsupported file types
- empty uploads
- empty text extraction
- extraction failures
- malformed or schema-invalid LLM responses
- missing OpenAI credentials
- invalid or unauthorized API keys
- exhausted OpenAI quota

## Hallucination Mitigation

- Only extracted deck text is sent to the model.
- The prompt is intentionally narrow and field-specific.
- The extraction step keeps numeric metrics and section headings whenever possible.
- The output is constrained by JSON schema and validated again in application code.
- A single retry is used only when the model output is malformed or schema-invalid.

## Limitations

- Image-only PDFs without OCR will usually return little or no text.
- Very large decks are prioritized and truncated before the LLM call to keep token usage low.
- The output quality depends on how much useful text exists in the source deck.

## Future Improvements

- Add OCR fallback for image-based PDFs.
- Add optional confidence notes per field.
- Add lightweight caching by file hash.
- Add async background processing for very large decks.
