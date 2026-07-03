import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from fpdf import FPDF

from utils.helpers import clean_text_for_pdf, format_currency, format_large_number


logger = logging.getLogger(__name__)


class PDFReportGenerator:
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_stock_report(self, research: dict[str, Any]) -> str:
        symbol = research["symbol"]
        filename = f"{symbol.replace('.', '_')}_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        path = self.output_dir / filename

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"Financial Research Report: {symbol}", ln=True)
        self._section(pdf, "Stock Details")
        quote = research.get("quote", {})
        details = {
            "Current Price": format_currency(quote.get("current_price")),
            "Open": format_currency(quote.get("open")),
            "High": format_currency(quote.get("day_high")),
            "Low": format_currency(quote.get("day_low")),
            "Volume": format_large_number(quote.get("volume")),
            "Market Cap": format_large_number(quote.get("market_cap")),
        }
        self._key_values(pdf, details)

        self._section(pdf, "Technical Indicators")
        indicators = research.get("indicators", {})
        self._key_values(pdf, {k: str(v) for k, v in indicators.items()})

        self._section(pdf, "Trade Signal")
        trade_signal = research.get("trade_signal", {})
        self._key_values(
            pdf,
            {
                "Action": trade_signal.get("action", "Hold"),
                "Buy View": trade_signal.get("buy_view", ""),
                "Sell View": trade_signal.get("sell_view", ""),
                "Rationale": trade_signal.get("rationale", ""),
            },
        )

        self._section(pdf, "Sentiment Analysis")
        sentiment = research.get("sentiment", {})
        self._key_values(
            pdf,
            {
                "Overall Sentiment": sentiment.get("overall_sentiment", "Neutral"),
                "Average TextBlob": str(sentiment.get("average_textblob", 0)),
                "Average VADER": str(sentiment.get("average_vader", 0)),
                "Counts": str(sentiment.get("sentiment_counts", {})),
            },
        )

        self._section(pdf, "AI Research Summary")
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 6, clean_text_for_pdf(research.get("ai_summary", "")))

        pdf.output(str(path))
        logger.info("Generated PDF report at %s", path)
        return str(path)

    def _section(self, pdf: FPDF, title: str):
        pdf.ln(4)
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 8, title, ln=True)
        pdf.set_font("Arial", "", 10)

    def _key_values(self, pdf: FPDF, data: dict[str, str]):
        pdf.set_font("Arial", "", 10)
        for key, value in data.items():
            pdf.set_font("Arial", "B", 10)
            pdf.cell(0, 7, clean_text_for_pdf(str(key)), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Arial", "", 10)
            pdf.multi_cell(0, 6, self._wrap_pdf_text(clean_text_for_pdf(str(value))))
            pdf.ln(1)

    @staticmethod
    def _wrap_pdf_text(text: str, chunk_size: int = 40) -> str:
        words = []
        for token in (text or "").split():
            if len(token) <= chunk_size:
                words.append(token)
                continue
            chunks = [token[i : i + chunk_size] for i in range(0, len(token), chunk_size)]
            words.append(" ".join(chunks))
        return " ".join(words)
