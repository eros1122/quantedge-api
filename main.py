from fastapi import FastAPI
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta

app = FastAPI()

@app.get("/api/analyze/{ticker}")
def get_stock_data(ticker: str):
    # 1. Fetch live data from Yahoo Finance
    stock = yf.Ticker(ticker)
    hist = stock.history(period="6mo")
    info = stock.info
    
    # 2. Calculate Technicals (e.g., Simple Moving Averages)
    hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
    current_price = hist['Close'].iloc[-1]
    sma_50 = hist['SMA_50'].iloc[-1]
    
    trend = "Bullish" if current_price > sma_50 else "Bearish"

    # 3. Structure the Pro-Tier JSON Payload automatically
    payload = {
        "asset_metadata": {
            "ticker": ticker.upper(),
            "sector": info.get("sector", "Unknown"),
            "market_cap_tier": "Mega Cap" if info.get("marketCap", 0) > 200e9 else "Large/Mid Cap",
            "liquidity": "High" if info.get("volume", 0) > 5e6 else "Moderate"
        },
        "quantitative_risk_metrics": {
            "volatility": {
                "beta": info.get("beta", 1.0),
                "implied_volatility_rank": round(np.random.uniform(20, 80), 1), # Placeholder for paid options data
                "historical_volatility_30d": round(hist['Close'].pct_change().std() * np.sqrt(252), 2)
            },
            "technical_confluence": {
                "trend": trend,
                "distance_from_50sma_percent": round(((current_price - sma_50) / sma_50) * 100, 2),
            }
        },
        "advanced_fundamentals": {
            "valuation": {
                "ev_to_ebitda": info.get("enterpriseToEbitda", "N/A"),
                "fcf_yield_percent": round((info.get("freeCashflow", 0) / info.get("marketCap", 1)) * 100, 2) if info.get("marketCap") else "N/A",
                "peg_ratio": info.get("pegRatio", "N/A")
            },
            "capital_efficiency": {
                "return_on_equity_percent": round(info.get("returnOnEquity", 0) * 100, 2),
                "profit_margin_percent": round(info.get("profitMargins", 0) * 100, 2)
            }
        },
        # These fields require premium APIs (like Polygon.io or Unusual Whales), using placeholders for the MVP
        "institutional_order_flow": {
            "options_sentiment": "Awaiting Premium API Integration",
            "dark_pool_index": "Awaiting Premium API Integration"
        },
        "macro_and_alt_catalysts": {
            "yield_curve_impact": "Neutral (Requires Macro API)",
            "supply_chain_alt_data": "Awaiting Alt-Data Integration"
        }
    }
    
    return payload

# To run this locally, you would save it as main.py and run: uvicorn main:app --reload