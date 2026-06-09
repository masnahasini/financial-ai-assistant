import re


SYMBOL_PATTERN = re.compile(r"^[A-Z0-9&-]{1,20}\.(NS|BO)$")


def normalize_indian_symbol(symbol: str) -> str:
    normalized = (symbol or "").strip().upper()
    if normalized and "." not in normalized:
        normalized = f"{normalized}.NS"
    return normalized


def validate_symbol(symbol: str) -> bool:
    return bool(SYMBOL_PATTERN.match((symbol or "").strip().upper()))
