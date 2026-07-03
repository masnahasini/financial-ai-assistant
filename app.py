import logging
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from agents.financial_agent import FinancialResearchAgent
from agents.report_generator import PDFReportGenerator
from database.db import init_db
from services.news_service import NewsService
from services.portfolio_service import PortfolioService
from services.sentiment_service import SentimentService
from services.stock_service import StockService
from services.watchlist_service import WatchlistService
from utils.helpers import format_currency, format_large_number, safe_float
from utils.validations import normalize_indian_symbol, validate_symbol


load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
logging.getLogger("yfinance").setLevel(logging.CRITICAL)


st.set_page_config(
    page_title="Financial Research AI Agent",
    page_icon="IN",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def bootstrap_services():
    init_db()
    stock_service = StockService()
    news_service = NewsService()
    sentiment_service = SentimentService()
    agent = FinancialResearchAgent(stock_service, news_service, sentiment_service)
    return {
        "stock": stock_service,
        "news": news_service,
        "sentiment": sentiment_service,
        "agent": agent,
        "watchlist": WatchlistService(),
        "portfolio": PortfolioService(stock_service),
        "report": PDFReportGenerator(),
    }


services = bootstrap_services()


def metric_card(label: str, value: str, delta: str | None = None):
    st.metric(label=label, value=value, delta=delta)


def plot_stock_chart(history: pd.DataFrame, symbol: str):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=history.index,
            y=history["Close"],
            mode="lines",
            name="Close",
            line=dict(color="#2563eb", width=2),
        )
    )
    if "SMA_20" in history:
        fig.add_trace(
            go.Scatter(
                x=history.index,
                y=history["SMA_20"],
                mode="lines",
                name="SMA 20",
                line=dict(color="#16a34a", width=1.5),
            )
        )
    if "SMA_50" in history:
        fig.add_trace(
            go.Scatter(
                x=history.index,
                y=history["SMA_50"],
                mode="lines",
                name="SMA 50",
                line=dict(color="#f97316", width=1.5),
            )
        )
    fig.update_layout(
        title=f"{symbol} Price and Moving Averages",
        xaxis_title="Date",
        yaxis_title="Price (INR)",
        template="plotly_white",
        height=460,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_rsi(history: pd.DataFrame, symbol: str):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=history.index,
            y=history["RSI"],
            mode="lines",
            name="RSI",
            line=dict(color="#7c3aed", width=2),
        )
    )
    fig.add_hline(y=70, line_dash="dash", line_color="#dc2626", annotation_text="Overbought")
    fig.add_hline(y=30, line_dash="dash", line_color="#16a34a", annotation_text="Oversold")
    fig.update_layout(
        title=f"{symbol} RSI",
        xaxis_title="Date",
        yaxis_title="RSI",
        template="plotly_white",
        height=320,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_sentiment(sentiment: dict):
    counts = sentiment.get("sentiment_counts", {"Positive": 0, "Neutral": 0, "Negative": 0})
    fig = go.Figure(
        data=[
            go.Pie(
                labels=list(counts.keys()),
                values=list(counts.values()),
                hole=0.45,
                marker=dict(colors=["#16a34a", "#64748b", "#dc2626"]),
            )
        ]
    )
    fig.update_layout(title="News Sentiment Mix", height=320, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)


def render_research_tab():
    st.subheader("AI Stock Research Agent")
    symbol = st.text_input("Stock symbol", value="RELIANCE.NS", help="Examples: RELIANCE.NS, TCS.NS, INFY.NS")
    period = st.selectbox("Historical period", ["3mo", "6mo", "1y", "2y"], index=2)

    if st.button("Generate Research", type="primary"):
        normalized = normalize_indian_symbol(symbol)
        if not validate_symbol(normalized):
            st.error("Enter a valid NSE/BSE stock symbol, for example RELIANCE.NS.")
            return
        with st.spinner("Fetching market data, news, indicators, and AI summary..."):
            result = services["agent"].research_stock(normalized, period=period)
        if result.get("error"):
            st.error(result["error"])
            return
        st.session_state["latest_research"] = result

    result = st.session_state.get("latest_research")
    if result:
        normalized = result["symbol"]
        quote = result["quote"]
        indicators = result["indicators"]
        sentiment = result["sentiment"]
        history = result["history"]
        trade_signal = result.get("trade_signal", {})

        cols = st.columns(6)
        cols[0].metric("Current Price", format_currency(quote.get("current_price")))
        cols[1].metric("Open", format_currency(quote.get("open")))
        cols[2].metric("High", format_currency(quote.get("day_high")))
        cols[3].metric("Low", format_currency(quote.get("day_low")))
        cols[4].metric("Volume", format_large_number(quote.get("volume")))
        cols[5].metric("Market Cap", format_large_number(quote.get("market_cap")))

        chart_col, sentiment_col = st.columns([2, 1])
        with chart_col:
            plot_stock_chart(history, normalized)
            plot_rsi(history, normalized)
        with sentiment_col:
            render_sentiment(sentiment)
            st.write("Technical Snapshot")
            st.dataframe(pd.DataFrame([indicators]).T.rename(columns={0: "Value"}), use_container_width=True)

        st.write("Trade Option")
        trade_cols = st.columns(3)
        trade_cols[0].metric("Signal", trade_signal.get("action", "Hold"))
        trade_cols[1].markdown(f"**Buy View**\n\n{trade_signal.get('buy_view', 'No buy setup available.')}")
        trade_cols[2].markdown(f"**Sell View**\n\n{trade_signal.get('sell_view', 'No sell setup available.')}")
        st.caption(trade_signal.get("rationale", ""))

        st.write("AI Research Report")
        st.markdown(result["ai_summary"])

        if st.button("Export PDF Report"):
            report_path = services["report"].create_stock_report(result)
            with open(report_path, "rb") as report_file:
                st.download_button(
                    "Download PDF",
                    report_file,
                    file_name=Path(report_path).name,
                    mime="application/pdf",
                )
            st.success(f"Report generated: {report_path}")


def render_comparison_tab():
    st.subheader("Stock Comparison")
    left, right = st.columns(2)
    symbol_a = left.text_input("First stock", value="RELIANCE.NS")
    symbol_b = right.text_input("Second stock", value="TCS.NS")

    if st.button("Compare Stocks", type="primary"):
        symbol_a = normalize_indian_symbol(symbol_a)
        symbol_b = normalize_indian_symbol(symbol_b)
        if not validate_symbol(symbol_a) or not validate_symbol(symbol_b):
            st.error("Enter valid NSE/BSE symbols such as RELIANCE.NS and TCS.NS.")
            return
        with st.spinner("Comparing stocks..."):
            comparison = services["agent"].compare_stocks(symbol_a, symbol_b)
        if comparison.get("error"):
            st.error(comparison["error"])
            return
        st.dataframe(comparison["table"], use_container_width=True)

        fig = go.Figure()
        for symbol, history in comparison["histories"].items():
            normalized_close = history["Close"] / history["Close"].iloc[0] * 100
            fig.add_trace(go.Scatter(x=history.index, y=normalized_close, mode="lines", name=symbol))
        fig.update_layout(
            title="Normalized Price Performance",
            xaxis_title="Date",
            yaxis_title="Indexed Price",
            template="plotly_white",
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)


def render_watchlist_tab():
    st.subheader("Watchlist")
    col_a, col_b = st.columns([2, 1])
    symbol = col_a.text_input("Add stock to watchlist", value="INFY.NS")
    if col_b.button("Add"):
        normalized = normalize_indian_symbol(symbol)
        if validate_symbol(normalized):
            services["watchlist"].add_stock(normalized)
            st.success(f"Added {normalized}")
        else:
            st.error("Invalid symbol.")

    watchlist = services["watchlist"].list_stocks()
    if not watchlist:
        st.info("Your watchlist is empty.")
        return

    rows = []
    for item in watchlist:
        try:
            quote = services["stock"].get_quote(item.symbol)
        except RuntimeError:
            quote = {"current_price": None, "change_percent": None, "volume": None}
        rows.append(
            {
                "Symbol": item.symbol,
                "Current Price": quote.get("current_price"),
                "Change %": quote.get("change_percent"),
                "Volume": quote.get("volume"),
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
    remove_symbol = st.selectbox("Remove stock", [item.symbol for item in watchlist])
    if st.button("Remove"):
        services["watchlist"].remove_stock(remove_symbol)
        st.success(f"Removed {remove_symbol}")
        st.rerun()


def render_portfolio_tab():
    st.subheader("Portfolio Tracker")
    with st.form("portfolio_form", clear_on_submit=True):
        cols = st.columns(3)
        symbol = cols[0].text_input("Stock", value="HDFCBANK.NS")
        quantity = cols[1].number_input("Quantity", min_value=0.0, value=10.0, step=1.0)
        purchase_price = cols[2].number_input("Purchase Price", min_value=0.0, value=1500.0, step=1.0)
        submitted = st.form_submit_button("Add Holding")
    if submitted:
        normalized = normalize_indian_symbol(symbol)
        if validate_symbol(normalized) and quantity > 0 and purchase_price > 0:
            services["portfolio"].add_holding(normalized, quantity, purchase_price)
            st.success(f"Added {normalized}")
        else:
            st.error("Enter a valid symbol, quantity, and purchase price.")

    try:
        holdings = services["portfolio"].get_portfolio_summary()
    except RuntimeError as exc:
        st.error(str(exc))
        return
    if holdings.empty:
        st.info("No portfolio holdings yet.")
        return
    st.dataframe(holdings, use_container_width=True)
    totals = services["portfolio"].calculate_totals(holdings)
    cols = st.columns(3)
    cols[0].metric("Investment Value", format_currency(totals["investment_value"]))
    cols[1].metric("Current Value", format_currency(totals["current_value"]))
    cols[2].metric("Profit/Loss", format_currency(totals["profit_loss"]), f"{totals['profit_loss_percent']:.2f}%")

    remove_options = holdings["Symbol"].tolist()
    remove_symbol = st.selectbox("Remove holding", remove_options)
    if st.button("Delete Holding"):
        services["portfolio"].remove_holding(remove_symbol)
        st.success(f"Removed {remove_symbol}")
        st.rerun()


def render_dashboard_tab():
    st.subheader("Stock Dashboard")
    symbol = normalize_indian_symbol(st.text_input("Dashboard symbol", value="TCS.NS"))
    if st.button("Load Dashboard", type="primary"):
        if not validate_symbol(symbol):
            st.error("Enter a valid NSE/BSE symbol.")
            return
        try:
            history = services["stock"].get_history(symbol, period="1y")
            if history.empty:
                st.error(
                    "Market data is temporarily unavailable for this symbol. "
                    "Yahoo Finance may be rate-limiting requests. Wait a minute and try again."
                )
                return
            quote = services["stock"].get_quote(symbol, history=history.tail(5))
            indicators = services["stock"].get_technical_indicators(history)
        except (RuntimeError, ValueError) as exc:
            st.error(
                f"{exc}. This usually means Yahoo Finance is temporarily rate-limiting requests. "
                "Wait a minute and try again."
            )
            return
        history = history.assign(**{k: v for k, v in indicators.get("series", {}).items()})

        cols = st.columns(6)
        cols[0].metric("Current Price", format_currency(quote.get("current_price")))
        cols[1].metric("Open", format_currency(quote.get("open")))
        cols[2].metric("High", format_currency(quote.get("day_high")))
        cols[3].metric("Low", format_currency(quote.get("day_low")))
        cols[4].metric("Volume", format_large_number(quote.get("volume")))
        cols[5].metric("Market Cap", format_large_number(quote.get("market_cap")))
        plot_stock_chart(history, symbol)
        plot_rsi(history, symbol)


st.title("Financial Research AI Agent")
st.caption("Indian stock market research assistant.")

tabs = st.tabs(["Research", "Dashboard", "Compare", "Watchlist", "Portfolio"])
with tabs[0]:
    render_research_tab()
with tabs[1]:
    render_dashboard_tab()
with tabs[2]:
    render_comparison_tab()
with tabs[3]:
    render_watchlist_tab()
with tabs[4]:
    render_portfolio_tab()
