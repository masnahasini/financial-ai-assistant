import math
import re
from typing import Any

import pandas as pd


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def format_currency(value: Any) -> str:
    amount = safe_float(value)
    return f"INR {amount:,.2f}"


def format_large_number(value: Any) -> str:
    number = safe_float(value)
    abs_number = abs(number)
    if abs_number >= 10_000_000:
        return f"{number / 10_000_000:.2f} Cr"
    if abs_number >= 100_000:
        return f"{number / 100_000:.2f} L"
    return f"{number:,.0f}"


def clean_text_for_pdf(text: str) -> str:
    text = re.sub(r"[^\x00-\x7F]+", " ", text or "")
    return text.replace("###", "").replace("**", "").strip()


def dataframe_to_records(frame: pd.DataFrame) -> list[dict]:
    if frame.empty:
        return []
    return frame.fillna("").to_dict(orient="records")
