# Financial Research AI Agent

An AI-powered Financial Research Assistant for Indian stock markets. It uses Streamlit, Plotly, yfinance, NewsAPI, SQLite, LangChain, and Gemini to analyze stocks, news sentiment, technical indicators, watchlists, portfolios, comparisons, and PDF reports.

> Educational purposes only. This is not financial advice.

## Complete Folder Structure

```text
financial-research-ai/
├── app.py
├── agents/
│   ├── __init__.py
│   ├── financial_agent.py
│   └── report_generator.py
├── services/
│   ├── __init__.py
│   ├── stock_service.py
│   ├── sentiment_service.py
│   ├── news_service.py
│   ├── portfolio_service.py
│   └── watchlist_service.py
├── database/
│   ├── __init__.py
│   ├── db.py
│   ├── models.py
│   └── schema.sql
├── utils/
│   ├── __init__.py
│   ├── indicators.py
│   ├── helpers.py
│   └── validations.py
├── reports/
│   └── .gitkeep
├── tests/
│   ├── __init__.py
│   ├── test_indicators.py
│   ├── test_sentiment_service.py
│   └── test_validations.py
├── .env.example
├── requirements.txt
├── README.md
└── setup.sh
```

## Features

- AI stock research agent for Indian market symbols such as `RELIANCE.NS`, `TCS.NS`, `INFY.NS`, and `HDFCBANK.NS`
- Current quote dashboard with price, open, high, low, volume, and market cap
- Plotly charts for price, SMA 20, SMA 50, and RSI
- Technical indicators: SMA 20, SMA 50, RSI, volatility, and daily returns
- News sentiment analysis with TextBlob and VADER
- Gemini-powered research report using LangChain
- Two-stock comparison for returns, volatility, volume, RSI, and sentiment
- SQLite watchlist system
- SQLite portfolio tracker with profit/loss calculations
- PDF report export

## Installation

```bash
cd financial-research-ai
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

On macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## API Keys

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Add your keys:

```text
GOOGLE_API_KEY=your_gemini_api_key
NEWS_API_KEY=your_newsapi_key
```

Gemini API key: create one from Google AI Studio.

NewsAPI key: create one from NewsAPI.

The app still runs without keys. Without `GOOGLE_API_KEY`, it uses a local deterministic research summary. Without `NEWS_API_KEY`, the news sentiment panel returns neutral empty sentiment.

## Running Project

```bash
streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal.

## Testing

```bash
pytest
```

## Streamlit Cloud Deployment

1. Push this project to GitHub.
2. Create a new Streamlit Cloud app.
3. Set the main file path to `app.py`.
4. Add secrets in Streamlit Cloud:

```toml
GOOGLE_API_KEY = "your_gemini_api_key"
NEWS_API_KEY = "your_newsapi_key"
```

5. Deploy the app.

## Screenshots

Add screenshots after running the app locally:

- Research tab
- Dashboard tab
- Stock comparison
- Watchlist
- Portfolio tracker
- PDF export

## Notes

- Use NSE symbols with `.NS` and BSE symbols with `.BO`.
- yfinance market data can be delayed and may occasionally fail due to upstream rate limits.
- All reports must be interpreted as educational research only, not investment advice.
