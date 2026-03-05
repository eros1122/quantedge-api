from fastapi import FastAPI
from fastapi.responses import FileResponse
import yfinance as yf
import numpy as np
from fpdf import FPDF
import os

app = FastAPI()

@app.get("/api/analyze/{ticker}")
def get_stock_data(ticker: str):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="6mo")
    info = stock.info
    raw_news = stock.news[:5]
    formatted_news = [{"title": n['title'], "publisher": n['publisher']} for n in raw_news]
    
    hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
    current_price = hist['Close'].iloc[-1]
    sma_50 = hist['SMA_50'].iloc[-1]
    trend = "Bullish" if current_price > sma_50 else "Bearish"

    return {
        "asset_metadata": {"ticker": ticker.upper(), "sector": info.get("sector", "Unknown")},
        "quantitative_risk_metrics": {"volatility": {"beta": info.get("beta", 1.0)}},
        "sentiment_and_macro": {"key_headlines": formatted_news}
    }

@app.get("/api/download/{ticker}")
def download_report(ticker: str):
    # This creates the actual PDF file
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"QuantEdge Institutional Research: {ticker.upper()}", ln=True, align='C')
    
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Report Generated on: 2026-03-05", ln=True)
    pdf.cell(200, 10, txt="Status: Final Institutional Grade Analysis", ln=True)

    file_path = f"{ticker}_report.pdf"
    pdf.output(file_path)
    
    return FileResponse(file_path, media_type='application/pdf', filename=file_path)

