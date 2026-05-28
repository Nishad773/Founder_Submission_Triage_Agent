from __future__ import annotations

import json
import re
from pathlib import Path

from dotenv import load_dotenv


SUPPORTED_EXTENSIONS = {".pdf", ".pptx"}
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
MAX_LLM_CHARS = 12000
PRIORITY_KEYWORDS = {
    "company",
    "problem",
    "solution",
    "product",
    "market",
    "traction",
    "revenue",
    "customers",
    "growth",
    "business model",
    "pricing",
    "funding",
    "raise",
    "ask",
    "team",
    "go-to-market",
    "gtm",
    "competition",
}


def get_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def ensure_supported_file(filename: str) -> str:
    extension = get_extension(filename)
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("Unsupported file type. Only PDF and PPTX are allowed.")
    return extension


def normalize_line(line: str) -> str:
    line = (line or "").replace("\x00", " ").replace("\t", " ")
    line = re.sub(r"\s+", " ", line).strip(" -|")
    return line


def normalize_lines(lines: list[str]) -> list[str]:
    return [line for raw in lines if (line := normalize_line(raw))]


def is_metric_line(line: str) -> bool:
    return bool(re.search(r"(\$|₹|%|\bARR\b|\bMRR\b|\bCAC\b|\bLTV\b|\bGMV\b|\bROI\b|\bYoY\b|\bMoM\b|\b\d[\d,\.]*\b)", line, re.IGNORECASE))


def is_heading_line(line: str) -> bool:
    words = line.split()
    if not words or len(words) > 10:
        return False
    if line.endswith(":"):
        return True
    uppercase_ratio = sum(word.isupper() for word in words) / max(len(words), 1)
    return uppercase_ratio >= 0.5 or all(len(word) <= 18 for word in words[:4] if word[:1].isalpha())


def is_probable_noise(line: str, repeated_count: int) -> bool:
    if repeated_count < 3:
        return False
    if is_metric_line(line):
        return False
    words = line.split()
    return len(words) <= 8 and len(line) <= 60


def strip_repeated_noise(lines: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    for line in lines:
        counts[line] = counts.get(line, 0) + 1
    return [line for line in lines if not is_probable_noise(line, counts[line])]


def clean_text(text: str) -> str:
    return normalize_line(text)


def score_line(line: str) -> int:
    score = 0
    lower = line.lower()
    if is_heading_line(line):
        score += 3
    if is_metric_line(line):
        score += 4
    if any(keyword in lower for keyword in PRIORITY_KEYWORDS):
        score += 3
    if len(line) > 120:
        score -= 1
    return score


def prioritize_text(lines: list[str], max_chars: int = MAX_LLM_CHARS) -> str:
    ranked = sorted(
        enumerate(lines),
        key=lambda item: (score_line(item[1]), -item[0]),
        reverse=True,
    )
    chosen: list[tuple[int, str]] = []
    total = 0

    for index, line in ranked:
        addition = len(line) + 1
        if total + addition > max_chars:
            continue
        chosen.append((index, line))
        total += addition

    if not chosen:
        fallback = "\n".join(lines)
        return fallback[:max_chars]

    chosen.sort(key=lambda item: item[0])
    return "\n".join(line for _, line in chosen)


def prepare_text_for_llm(lines: list[str], max_chars: int = MAX_LLM_CHARS) -> str:
    cleaned = strip_repeated_noise(normalize_lines(lines))
    return prioritize_text(cleaned, max_chars=max_chars)


def parse_json_content(content: str) -> dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("Malformed JSON returned by model.") from exc


def load_environment() -> None:
    load_dotenv(dotenv_path=ENV_PATH, override=False)
