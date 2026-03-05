from fastapi import FastAPI
from fastapi.responses import FileResponse
import yfinance as yf
from fpdf import FPDF
import os

app = FastAPI()

def fetch_stock_logic(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        info = stock.info
        
        if hist.empty:
            return {"price": 0.0, "trend": "Data Unavailable", "news": [], "beta": 1.0, "sector": "N/A"}

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
            "sector": info.get("sector", "Unknown")
        }
    except Exception as e:
        print(f"Error fetching data: {e}")
        return {"price": "Rate Limited", "trend": "Cooldown", "news": [], "beta": 0, "sector": "N/A"}

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
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"QUANTEDGE REPORT: {ticker.upper()}", ln=True, align='C')
    
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Price: ${data['price']} | Trend: {data['trend']}", ln=True)
    pdf.cell(200, 10, txt=f"Sector: {data['sector']} | Beta: {data['beta']}", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Recent Catalysts:", ln=True)
    pdf.set_font("Arial", size=10)
    for item in data['news']:
        pdf.multi_cell(0, 10, txt=f"- {item['title']} ({item['publisher']})")
    
    file_path = f"{ticker}_report.pdf"
    pdf.output(file_path)
    return FileResponse(file_path, media_type='application/pdf', filename=file_path)



