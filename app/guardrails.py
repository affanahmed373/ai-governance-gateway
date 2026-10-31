import re

INJECTION_PATTERNS = [
    r"ignore (all|any|previous|prior) (instructions|rules)",
    r"disregard (the )?(system|previous) prompt",
    r"reveal (your )?(system prompt|instructions)",
    r"you are now (in )?developer mode",
]

PII_PATTERNS = {
    "EMAIL": r"[\w.+-]+@[\w-]+\.[\w.-]+",
    "IBAN": r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b",
    "PHONE": r"\+?\d[\d ()/-]{8,}\d",
}


def detect_prompt_injection(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(p, lowered) for p in INJECTION_PATTERNS)


def mask_pii(text: str) -> str:
    for label, pattern in PII_PATTERNS.items():
        text = re.sub(pattern, f"[{label}]", text)
    return text
