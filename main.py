from __future__ import annotations

import json

import streamlit as st
from dotenv import load_dotenv

from app.extractor import analyze_documents
from app.parser import build_document_bundle
from app.utils import ensure_supported_file

load_dotenv()

ALLOWED_TYPES = ["pdf", "pptx"]


def _source_badge(source: str | None) -> str:
    if source:
        return f"<span class='source-pill'>{source}</span>"
    return "<span class='source-pill source-pill-muted'>Source not explicit</span>"


def _render_attributed_value(title: str, item: dict) -> None:
    st.markdown(
        f"""
        <div class="overview-card">
            <div class="card-label">{title}</div>
            <div class="card-value">{item.get("value", "N/A")}</div>
            <div class="card-source">{_source_badge(item.get("source"))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_list_cards(items: list[dict], tone: str, columns_count: int = 2) -> None:
    display_items = items or [{"value": "No items returned.", "source": None}]
    columns = st.columns(min(columns_count, len(display_items)))
    for index, item in enumerate(display_items):
        with columns[index % len(columns)]:
            st.markdown(
                f"""
                <div class="insight-card {tone}">
                    <div class="insight-value">{item.get("value", "")}</div>
                    <div class="card-source">{_source_badge(item.get("source"))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_warning_list(items: list[dict]) -> None:
    for item in items:
        st.markdown(
            f"""
            <div class="warning-card">
                <div class="warning-icon">!</div>
                <div>
                    <div class="warning-text">{item.get("value", "")}</div>
                    <div class="card-source">{_source_badge(item.get("source"))}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )





def _build_report_text(result: dict) -> str:
    strengths = "\n".join(f"- {item['value']}" for item in result.get("strengths", [])) or "- None"
    concerns = "\n".join(f"- {item['value']}" for item in result.get("concerns", [])) or "- None"
    red_flags = "\n".join(f"- {item['value']}" for item in result.get("red_flags", [])) or "- None"
    traction = "\n".join(f"- {item['value']}" for item in result.get("traction_stats", [])) or "- None"
    return f"""Founder Submission Triage Agent

Company: {result['company_name']['value']}
Sector: {result['sector']['value']}
Stage: {result['stage']['value']}
Funding Ask: {result['funding_ask']['value']}
Readiness Score: {result['investment_readiness_score']}/100

Business Model
{result['business_model']['value']}

Traction Metrics
{traction}

Strengths
{strengths}

Concerns
{concerns}

Red Flags
{red_flags}
"""


st.set_page_config(page_title="Founder Submission Triage Agent", page_icon="📈", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    :root {
        --sage: #98A68E;
        --sage-deep: #5E6A56;
        --blush: #D9B4B0;
        --cream: #EAE7DC;
        --neutral: #8E918B;
        --ink: #2F3A31;
        --paper: #FBFAF6;
        --white: rgba(255, 255, 255, 0.86);
        --border: rgba(94, 106, 86, 0.16);
        --shadow: 0 18px 40px rgba(86, 94, 80, 0.10);
    }

    html, body, [class*="css"]  {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at 18% 18%, rgba(152, 166, 142, 0.12), transparent 28%),
            radial-gradient(circle at 86% 16%, rgba(217, 180, 176, 0.18), transparent 24%),
            linear-gradient(135deg, #f9f8f2 0%, #fcfbf7 58%, #fbf2ee 100%);
        color: var(--ink);
    }

    .block-container {
        max-width: 1180px;
        padding-top: 2.2rem;
        padding-bottom: 3.2rem;
    }

    .hero-shell {
        display: grid;
        grid-template-columns: 1.45fr 0.9fr;
        gap: 1.2rem;
        align-items: stretch;
        margin-bottom: 1.6rem;
    }

    .hero-panel, .hero-side, .upload-panel, .summary-shell {
        background: var(--white);
        border: 1px solid var(--border);
        border-radius: 30px;
        box-shadow: var(--shadow);
        backdrop-filter: blur(10px);
    }

    .hero-panel {
        padding: 2.4rem 2.5rem;
    }

    .eyebrow {
        color: var(--sage-deep);
        text-transform: uppercase;
        letter-spacing: 0.16em;
        font-size: 0.72rem;
        margin-bottom: 0.8rem;
        font-weight: 700;
    }

    .hero-title {
        font-family: 'Manrope', sans-serif;
        font-weight: 300;
        font-size: 4.2rem;
        line-height: 0.95;
        color: var(--sage-deep);
        margin: 0;
        letter-spacing: -0.05em;
    }

    .hero-subtitle {
        margin-top: 1rem;
        max-width: 760px;
        font-size: 1.05rem;
        line-height: 1.8;
        color: #586257;
    }

    .workflow {
        display: flex;
        gap: 0.75rem;
        align-items: center;
        flex-wrap: wrap;
        margin-top: 1.3rem;
    }

    .workflow-step {
        padding: 0.78rem 1.1rem;
        border-radius: 999px;
        background: rgba(152, 166, 142, 0.12);
        color: var(--sage-deep);
        border: 1px solid rgba(152, 166, 142, 0.25);
        font-weight: 600;
        font-size: 0.92rem;
    }

    .workflow-sep {
        color: var(--neutral);
        font-size: 1rem;
    }

    .hero-side {
        padding: 1.25rem;
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 0.95rem;
    }

    .side-card {
        border-radius: 24px;
        padding: 1rem;
        min-height: 138px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        border: 1px solid rgba(94, 106, 86, 0.08);
        background: rgba(255,255,255,0.7);
    }

    .side-card.sage {
        background: linear-gradient(180deg, rgba(152,166,142,0.18) 0%, rgba(255,255,255,0.78) 100%);
    }

    .side-card.blush {
        background: linear-gradient(180deg, rgba(217,180,176,0.24) 0%, rgba(255,255,255,0.82) 100%);
    }

    .side-kicker {
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-size: 0.7rem;
        color: #6e7767;
        font-weight: 700;
    }

    .side-value {
        font-family: 'Manrope', sans-serif;
        font-size: 2rem;
        line-height: 1;
        color: var(--sage-deep);
        font-weight: 400;
    }

    .side-note {
        color: #697365;
        font-size: 0.88rem;
        line-height: 1.5;
    }

    .upload-panel, .summary-shell {
        padding: 1.5rem;
        margin-bottom: 1.35rem;
    }

    .section-title {
        font-family: 'Manrope', sans-serif;
        font-size: 2.1rem;
        line-height: 1;
        letter-spacing: -0.04em;
        color: var(--sage-deep);
        margin: 0 0 0.8rem 0;
    }

    .subtle-copy {
        color: #6a7467;
        font-size: 0.95rem;
        line-height: 1.75;
        margin-bottom: 0.7rem;
    }

    .overview-card, .insight-card, .score-card, .summary-card, .metric-card {
        background: rgba(255,255,255,0.72);
        border: 1px solid var(--border);
        border-radius: 28px;
        padding: 1.1rem;
        box-shadow: 0 10px 24px rgba(86, 94, 80, 0.06);
        height: 100%;
    }

    .metric-card {
        min-height: 138px;
        background: linear-gradient(180deg, rgba(255,255,255,0.86) 0%, rgba(234,231,220,0.56) 100%);
    }

    .card-label {
        text-transform: uppercase;
        letter-spacing: 0.16em;
        font-size: 0.7rem;
        color: #73806d;
        margin-bottom: 0.55rem;
        font-weight: 700;
    }

    .card-value {
        font-size: 1.08rem;
        font-weight: 700;
        color: var(--ink);
        line-height: 1.45;
    }

    .metric-value {
        font-family: 'Manrope', sans-serif;
        font-size: 2.2rem;
        line-height: 0.95;
        font-weight: 400;
        color: var(--sage-deep);
    }

    .metric-note {
        color: #74806e;
        font-size: 0.87rem;
        margin-top: 0.35rem;
        line-height: 1.55;
    }

    .card-source {
        margin-top: 0.85rem;
    }

    .source-pill {
        display: inline-block;
        padding: 0.27rem 0.65rem;
        border-radius: 999px;
        background: rgba(152, 166, 142, 0.16);
        color: var(--sage-deep);
        font-size: 0.74rem;
        font-weight: 600;
    }

    .source-pill-muted {
        background: rgba(142, 145, 139, 0.14);
        color: #6e756e;
    }

    .insight-card.good {
        border-left: 4px solid var(--sage);
    }

    .insight-card.caution {
        border-left: 4px solid var(--blush);
    }

    .insight-value {
        font-size: 0.98rem;
        font-weight: 600;
        color: var(--ink);
        line-height: 1.55;
    }

    .warning-card {
        display: flex;
        gap: 0.85rem;
        align-items: flex-start;
        background: linear-gradient(180deg, rgba(217,180,176,0.22) 0%, rgba(255,255,255,0.72) 100%);
        border: 1px solid rgba(217,180,176,0.48);
        border-left: 5px solid var(--blush);
        border-radius: 24px;
        padding: 1rem;
        margin-bottom: 0.85rem;
    }

    .warning-icon {
        width: 1.8rem;
        height: 1.8rem;
        border-radius: 999px;
        background: var(--blush);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        flex-shrink: 0;
    }

    .warning-text {
        font-weight: 700;
        color: #5d5451;
        line-height: 1.5;
    }

    .stButton > button, .stDownloadButton > button {
        border-radius: 999px;
        min-height: 3.1rem;
        font-weight: 700;
        border: 1px solid rgba(94, 106, 86, 0.16);
        box-shadow: none;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(180deg, var(--sage) 0%, #8a997f 100%);
        color: #f9faf5;
    }

    .stDownloadButton > button {
        background: rgba(255,255,255,0.82);
        color: var(--sage-deep);
    }

    .stProgress > div > div > div > div {
        background-color: var(--sage);
    }

    @media (max-width: 980px) {
        .hero-shell {
            grid-template-columns: 1fr;
        }
        .hero-title {
            font-size: 3.15rem;
        }
        .hero-side {
            grid-template-columns: 1fr 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-shell">
        <div class="hero-panel">
            <div class="eyebrow">Internal VC Workflow</div>
            <h1 class="hero-title">Founder Submission Triage Agent</h1>
            <div class="hero-subtitle">
                AI-powered startup screening and investment analysis for venture teams, angel networks, and accredited investor platforms.
            </div>
            <div class="workflow">
                <div class="workflow-step">Upload Documents</div>
                <div class="workflow-sep">&darr;</div>
                <div class="workflow-step">AI Analysis</div>
                <div class="workflow-sep">&darr;</div>
                <div class="workflow-step">Investment Summary</div>
            </div>
        </div>
        <div class="hero-side">
            <div class="side-card sage">
                <div class="side-kicker">Coverage</div>
                <div class="side-value">4</div>
                <div class="side-note">Pitch deck, financials, cap table, and legal materials in one intake flow.</div>
            </div>
            <div class="side-card blush">
                <div class="side-kicker">Decision Aid</div>
                <div class="side-value">Fast</div>
                <div class="side-note">Standardized first-pass screening for partner review and follow-up diligence.</div>
            </div>
            <div class="side-card">
                <div class="side-kicker">Evidence</div>
                <div class="side-value">JSON</div>
                <div class="side-note">Structured output with attributed findings when source support is explicit.</div>
            </div>
            <div class="side-card">
                <div class="side-kicker">Model</div>
                <div class="side-value">Gemini</div>
                <div class="side-note">Validated AI analysis designed for internal investor workflow consistency.</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='upload-panel'>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>Upload Documents</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='subtle-copy'>Drag and drop founder materials to generate a consistent first-pass investment summary. The sage and blush styling is intentional, but the structure remains desktop-first and analyst-friendly.</div>",
    unsafe_allow_html=True,
)

pitch_deck_files = st.file_uploader("Pitch Deck", type=ALLOWED_TYPES, accept_multiple_files=True, key="pitch_deck")
financial_statement_files = st.file_uploader("Financial Statements", type=ALLOWED_TYPES, accept_multiple_files=True, key="financial_statements")
cap_table_files = st.file_uploader("Cap Table", type=ALLOWED_TYPES, accept_multiple_files=True, key="cap_table")
legal_document_files = st.file_uploader("Legal Documents", type=ALLOWED_TYPES, accept_multiple_files=True, key="legal_documents")
st.markdown("</div>", unsafe_allow_html=True)

uploads = {
    "pitch_deck": pitch_deck_files,
    "financial_statements": financial_statement_files,
    "cap_table": cap_table_files,
    "legal_documents": legal_document_files,
}

if st.button("Analyze", type="primary", use_container_width=True, disabled=not any(uploads.values())):
    try:
        with st.spinner("Analyzing founder materials with Gemini..."):
            parsed_inputs = {
                "pitch_deck": [],
                "financials": [],
                "cap_table": [],
                "legal_docs": [],
            }
            # Map frontend upload keys to backend parser keys
            category_mapping = {
                "pitch_deck": "pitch_deck",
                "financial_statements": "financials",
                "cap_table": "cap_table",
                "legal_documents": "legal_docs",
            }
            
            for frontend_key, uploaded_files in uploads.items():
                backend_key = category_mapping[frontend_key]
                if uploaded_files:
                    for upload in uploaded_files:
                        ensure_supported_file(upload.name)
                        parsed_inputs[backend_key].append((upload.name, upload.getvalue()))

            bundle = build_document_bundle(parsed_inputs)
            
            if not any(bundle.model_dump().values()):
                st.error("No extractable text found in the uploaded documents.")
            else:
                response = analyze_documents(bundle)
                st.session_state["analysis_result"] = response.model_dump()
                st.toast("Analysis completed successfully.", icon="✅")
                st.success("Investment summary ready.")
    except ValueError as exc:
        st.error(f"Validation Error: {exc}")
    except Exception as exc:
        st.error(f"Analysis failed: {exc}")


result = st.session_state.get("analysis_result")

if result:
    st.markdown("<div class='summary-shell'>", unsafe_allow_html=True)
    metric_cols = st.columns(4)
    metrics = [
        ("Readiness Score", f"{result['investment_readiness_score']}/100", "Internal screening confidence"),
        ("Strength Signals", str(len(result.get("strengths", []))), "Positive investor-facing indicators"),
        ("Concern Signals", str(len(result.get("concerns", []))), "Questions for deeper diligence"),
        ("Red Flags", str(len(result.get("red_flags", []))), "Highest-priority screening risks"),
    ]
    for column, (label, value, note) in zip(metric_cols, metrics):
        with column:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="card-label">{label}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-note">{note}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div class='section-title'>Company Overview</div>", unsafe_allow_html=True)
    overview_columns = st.columns([1.25, 1.25, 1.0, 1.15])
    with overview_columns[0]:
        _render_attributed_value("Company Name", result["company_name"])
    with overview_columns[1]:
        _render_attributed_value("Sector", result["sector"])
    with overview_columns[2]:
        _render_attributed_value("Stage", result["stage"])
    with overview_columns[3]:
        _render_attributed_value("Funding Ask", result["funding_ask"])

    score_col, summary_col = st.columns([0.95, 2.05])
    with score_col:
        st.markdown("<div class='section-title'>Investment Summary</div>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="score-card">
                <div class="card-label">Readiness Score</div>
                <div class="metric-value">{result['investment_readiness_score']}/100</div>
                <div class="metric-note">Use as a triage aid for partner review, not a final investment decision.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(int(result["investment_readiness_score"]) / 100)
    with summary_col:
        st.markdown("<div class='section-title'>Business Model</div>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="summary-card">
                <div class="insight-value">{result['business_model']['value']}</div>
                <div class="card-source">{_source_badge(result['business_model'].get('source'))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div class='section-title'>Traction Metrics</div>", unsafe_allow_html=True)
    _render_list_cards(result.get("traction_stats", []), tone="good", columns_count=3)

    strengths_col, concerns_col = st.columns(2)
    with strengths_col:
        st.markdown("<div class='section-title'>Strengths</div>", unsafe_allow_html=True)
        st.markdown("<div class='subtle-copy'>Signals that support deeper diligence or partner review.</div>", unsafe_allow_html=True)
        _render_list_cards(result.get("strengths", []), tone="good", columns_count=2)
    with concerns_col:
        st.markdown("<div class='section-title'>Concerns</div>", unsafe_allow_html=True)
        st.markdown("<div class='subtle-copy'>Questions or gaps that may affect investor conviction.</div>", unsafe_allow_html=True)
        _render_list_cards(result.get("concerns", []), tone="caution", columns_count=2)

    st.markdown("<div class='section-title'>Red Flags</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtle-copy'>Highest-priority risks for early investment screening.</div>", unsafe_allow_html=True)
    _render_warning_list(result.get("red_flags", []))

    with st.expander("Raw JSON"):
        st.code(json.dumps(result, indent=2, ensure_ascii=False), language="json")

    download_cols = st.columns(2)
    with download_cols[0]:
        st.download_button(
            "Download JSON",
            data=json.dumps(result, indent=2, ensure_ascii=False),
            file_name="investment_summary.json",
            mime="application/json",
            use_container_width=True,
        )
    with download_cols[1]:
        st.download_button(
            "Download Report",
            data=_build_report_text(result),
            file_name="investment_summary_report.txt",
            mime="text/plain",
            use_container_width=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)
