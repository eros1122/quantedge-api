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
        "version": "3.0.0",
        "sentiment_engine": "Active",
        "endpoints": {"analyze": "/api/analyze/{ticker}", "download": "/api/download/{ticker}"}
    }

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window, min_periods=1).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_sentiment(headlines):
    bullish_words = ['surge', 'growth', 'buy', 'profit', 'beat', 'upgrade', 'expansion']
    bearish_words = ['drop', 'fall', 'lawsuit', 'miss', 'cut', 'downgrade', 'risk', 'debt']
    
    score = 0
    for h in headlines:
        text = h['title'].lower()
        if any(word in text for word in bullish_words): score += 1
        if any(word in text for word in bearish_words): score -= 1
    
    if score > 1: return "Strong Bullish", (0, 128, 0)
    if score < -1: return "Strong Bearish", (255, 0, 0)
    return "Neutral / Mixed", (128, 128, 128)

def fetch_stock_logic(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        info = stock.info
        
        if hist.empty or len(hist) < 14:
            return {"price": 0.0, "trend": "Data Insufficient", "news": [], "beta": 1.0, "rsi": "N/A"}

        # Calculate Momentum & Sentiment
        current_rsi = calculate_rsi(hist['Close']).iloc[-1]
        
        news_data = stock.news[:5] if stock.news else []
        formatted_news = []
        for n in news_data:
            formatted_news.append({
                "title": n.get('title', 'Headline Unavailable'),
                "publisher": n.get('publisher', 'Unknown Source')
            })
            
        sentiment_text, sentiment_color = calculate_sentiment(formatted_news)

        return {
            "price": round(hist['Close'].iloc[-1], 2),
            "trend": "Bullish" if hist['Close'].iloc[-1] > info.get('fiftyDayAverage', 0) else "Bearish",
            "news": formatted_news,
            "beta": info.get("beta", 1.0),
            "sector": info.get("sector", "Unknown"),
            "rsi": round(current_rsi, 2),
            "sentiment": sentiment_text,
            "sentiment_color": sentiment_color
        }
    except Exception as e:
        print(f"Error: {e}")
        return {"price": "Rate Limited", "trend": "Cooldown", "news": [], "beta": 0, "rsi": "N/A", "sentiment": "N/A"}

@app.get("/api/analyze/{ticker}")
def analyze(ticker: str):
    data = fetch_stock_logic(ticker)
    return {
        "asset_metadata": {"ticker": ticker.upper(), "sector": data.get("sector")},
        "quantitative_risk_metrics": {
            "momentum": {"rsi": data.get("rsi"), "trend": data.get("trend")},
            "sentiment": {"score": data.get("sentiment")}
        },
        "sentiment_and_macro": {"key_headlines": data.get("news")}
    }

@app.get("/api/download/{ticker}")
def download_report(ticker: str):
    data = fetch_stock_logic(ticker)
    pdf = FPDF()
    pdf.add_page()
    
    # Sentiment Banner
    r, g, b = data.get('sentiment_color', (128, 128, 128))
    pdf.set_fill_color(r, g, b)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 12, txt=f"MARKET SENTIMENT: {data.get('sentiment', 'N/A')}", ln=True, align='C', fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(95, 10, txt=f"Price: ${data['price']}", border=1)
    pdf.cell(95, 10, txt=f"RSI: {data['rsi']}", border=1, ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Key Market Catalysts:", ln=True)
    pdf.set_font("Arial", size=10)
    for item in data['news']:
        pdf.multi_cell(0, 8, txt=f"- {item['title']} ({item['publisher']})")
    
    file_path = f"{ticker}_report.pdf"
    pdf.output(file_path)
    return FileResponse(file_path, media_type='application/pdf', filename=file_path)





