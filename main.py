from fastapi import FastAPI
from fastapi.responses import FileResponse
import yfinance as yf
from fpdf import FPDF
import os
import pandas as pd

app = FastAPI()

@app.get("/")
def home():
    return {
        "status": "QuantEdge Institutional Engine Online",
        "version": "2.0.0",
        "endpoints": {
            "analyze": "/api/analyze/{ticker}",
            "download": "/api/download/{ticker}"
        }
    }

def calculate_rsi(data, window=14):
    delta = data.diff()
    # Adding min_periods=1 ensures we get a value even if data is slightly thin
    gain = (delta.where(delta > 0, 0)).rolling(window=window, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window, min_periods=1).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def fetch_stock_logic(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        # Fetching 1 month of data to ensure we have enough for a 14-day RSI
        hist = stock.history(period="1mo")
        info = stock.info
        
        if hist.empty or len(hist) < 14:
            return {"price": 0.0, "trend": "Data Insufficient", "news": [], "beta": 1.0, "rsi": "N/A"}

        # Calculate Momentum (RSI)
        current_rsi = calculate_rsi(hist['Close']).iloc[-1]
        momentum = "Overbought" if current_rsi > 70 else "Oversold" if current_rsi < 30 else "Neutral"

        # Extract news safely
        news_data = stock.news[:5] if stock.news else []
        formatted_news = []
        for n in news_data:
            formatted_news.append({
                "title": n.get('title', 'Headline Unavailable'),
                "publisher": n.get('publisher', 'Unknown Source')
            })

        return {
            "price": round(hist['Close'].iloc[-1], 2),
            "trend": "Bullish" if hist['Close'].iloc[-1] > info.get('fiftyDayAverage', 0) else "Bearish",
            "news": formatted_news,
            "beta": info.get("beta", 1.0),
            "sector": info.get("sector", "Unknown"),
            "rsi": round(current_rsi, 2),
            "momentum": momentum
        }
    except Exception as e:
        print(f"Error fetching data: {e}")
        return {"price": "Rate Limited", "trend": "Cooldown", "news": [], "beta": 0, "rsi": "N/A"}

@app.get("/api/analyze/{ticker}")
def analyze(ticker: str):
    data = fetch_stock_logic(ticker)
    return {
        "asset_metadata": {"ticker": ticker.upper(), "sector": data.get("sector")},
        "quantitative_risk_metrics": {
            "volatility": {"beta": data.get("beta")},
            "trend": data.get("trend"),
            "momentum": {"rsi": data.get("rsi"), "status": data.get("momentum")}
        },
        "sentiment_and_macro": {"key_headlines": data.get("news")}
    }

@app.get("/api/download/{ticker}")
def download_report(ticker: str):
    data = fetch_stock_logic(ticker)
    pdf = FPDF()
    pdf.add_page()
    
    # Custom Header
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(200, 15, txt="QUANTEDGE INSTITUTIONAL INTELLIGENCE", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 5, txt=f"Ticker: {ticker.upper()} | Momentum Analysis v2.0", ln=True, align='C')
    pdf.ln(10)
    
    # Core Data Table
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(95, 10, txt=f"Current Price: ${data['price']}", border=1, fill=True)
    pdf.cell(95, 10, txt=f"Market Trend: {data['trend']}", border=1, fill=True, ln=True)
    pdf.cell(95, 10, txt=f"RSI (14-Day): {data['rsi']}", border=1)
    pdf.cell(95, 10, txt=f"Momentum: {data.get('momentum', 'N/A')}", border=1, ln=True)
    
    # News Section
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Institutional Catalysts:", ln=True)
    pdf.set_font("Arial", size=10)
    for item in data['news']:
        pdf.multi_cell(0, 8, txt=f"- {item['title']} ({item['publisher']})")
    
    file_path = f"{ticker}_report.pdf"
    pdf.output(file_path)
    return FileResponse(file_path, media_type='application/pdf', filename=file_path)




