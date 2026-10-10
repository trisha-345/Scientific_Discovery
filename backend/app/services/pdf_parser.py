import fitz
import re


def extract_text(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    text = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(text)


def clean_text(text: str) -> str:
    text = re.sub(r"-\n", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def extract_title(text: str) -> str:
    for line in text.split("\n"):
        line = line.strip()
        if 5 < len(line) < 300:
            return line
    return "Untitled"


def extract_abstract(text: str) -> str:
    m = re.search(
        r"abstract\b(.*?)(?:\n\s*(?:keywords|1\.?\s*introduction|introduction)\b)",
        text, re.IGNORECASE | re.DOTALL
    )
    return m.group(1).strip()[:3000] if m else ""


def parse_pdf(pdf_path: str) -> dict:
    raw = extract_text(pdf_path)
    clean = clean_text(raw)
    return {
        "full_text": clean,
        "title": extract_title(clean),
        "abstract": extract_abstract(clean),
    }
