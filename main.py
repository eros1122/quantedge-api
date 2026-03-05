from fastapi import FastAPI
from fastapi.responses import FileResponse
import yfinance as yf
from fpdf import FPDF
import os

app = FastAPI()

def fetch_stock_logic(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        # Try to get data
        hist = stock.history(period="1d")
        info = stock.info
        
        if hist.empty:
            return {"price": 0.0, "trend": "Data Unavailable", "news": [], "beta": 1.0, "sector": "N/A"}

        return {
            "price": round(hist['Close'].iloc[-1], 2),
            "trend": "Bullish" if hist['Close'].iloc[-1] > info.get('fiftyDayAverage', 0) else "Bearish",
            "news": [{"title": n['title'], "publisher": n['publisher']} for n in stock.news[:5]],
            "beta": info.get("beta", 1.0),
            "sector": info.get("sector", "Unknown")
        }
    except Exception as e:
        # If Yahoo blocks us (Rate Limit), return this instead of crashing
        print(f"Error fetching data: {e}")
        return {
            "price": "Rate Limited",
            "trend": "Try again in 5 mins",
            "news": [{"title": "Yahoo Finance is rate-limiting this server. Please wait.", "publisher": "System"}],
            "beta": 0,
            "sector": "N/A"
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



