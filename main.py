from fastapi import FastAPI
from fastapi.responses import FileResponse
import yfinance as yf
from fpdf import FPDF
import os

app = FastAPI()

def fetch_stock_logic(ticker: str):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="6mo")
    info = stock.info
    raw_news = stock.news[:5]
    formatted_news = [{"title": n['title'], "publisher": n['publisher']} for n in raw_news]
    
    current_price = hist['Close'].iloc[-1]
    sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1]
    trend = "Bullish" if current_price > sma_50 else "Bearish"
    
    return {
        "price": round(current_price, 2),
        "trend": trend,
        "news": formatted_news,
        "beta": info.get("beta", "N/A"),
        "sector": info.get("sector", "Unknown")
    }

@app.get("/api/analyze/{ticker}")
def analyze(ticker: str):
    data = fetch_stock_logic(ticker)
    return {
        "asset_metadata": {"ticker": ticker.upper(), "sector": data["sector"]},
        "quantitative_risk_metrics": {"volatility": {"beta": data["beta"]}, "trend": data["trend"]},
        "sentiment_and_macro": {"key_headlines": data["news"]}
    }

@app.get("/api/download/{ticker}")
def download_report(ticker: str):
    data = fetch_stock_logic(ticker)
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(200, 10, txt="QUANTEDGE INSTITUTIONAL REPORT", ln=True, align='C')
    pdf.ln(10)
    
    # Data Table Style
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(100, 10, txt=f"Ticker: {ticker.upper()}", border=1)
    pdf.cell(100, 10, txt=f"Current Price: ${data['price']}", border=1, ln=True)
    pdf.cell(100, 10, txt=f"Market Trend: {data['trend']}", border=1)
    pdf.cell(100, 10, txt=f"Sector: {data['sector']}", border=1, ln=True)
    
    # News Section
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Key Market Catalysts:", ln=True)
    pdf.set_font("Arial", size=10)
    for item in data['news']:
        pdf.multi_cell(0, 8, txt=f"- {item['title']} ({item['publisher']})")
    
    file_path = f"{ticker}_report.pdf"
    pdf.output(file_path)
    return FileResponse(file_path, media_type='application/pdf', filename=file_path)


