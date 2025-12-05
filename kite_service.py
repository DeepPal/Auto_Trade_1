"""Production-Grade Zerodha Kite Authentication Microservice

This service handles:
- Token generation and validation
- Session management with automatic refresh
- Multi-layer error handling with retry logic
- Real-time market data access
- Options chain data fetching
- Greeks calculation for position management
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from functools import wraps
import time

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
import redis
from kiteconnect import KiteConnect
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Zerodha Kite Trading Service", version="2.0")

# Configuration from environment
KITE_API_KEY = os.getenv('KITE_API_KEY')
KITE_API_SECRET = os.getenv('KITE_API_SECRET')
KITE_USER_ID = os.getenv('KITE_USER_ID')
KITE_PASSWORD = os.getenv('KITE_PASSWORD')

# Redis connection for caching
redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'),
                           port=int(os.getenv('REDIS_PORT', 6379)),
                           decode_responses=True)


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    message: str


class OrderRequest(BaseModel):
    """Order placement request model"""
    symbol: str
    quantity: int
    price: float
    order_type: str  # MARKET, LIMIT, SL, SL-M
    side: str  # BUY, SELL
    product: str = "MIS"  # MIS, CNC, NRML
    validity: str = "DAY"
    tag: Optional[str] = None


class PositionData(BaseModel):
    """Position data model"""
    symbol: str
    quantity: int
    average_price: float
    current_price: float
    pnl: float
    pnl_percent: float


class KiteAuthenticationService:
    """Production-grade Kite authentication and trading service"""

    def __init__(self):
        self.kite = KiteConnect(api_key=KITE_API_KEY)
        self.token = None
        self.session_start = None
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    def retry_on_failure(self, max_retries=3, delay=1):
        """Decorator for retry logic"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if attempt < max_retries - 1:
                            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")
                            time.sleep(delay)
                        else:
                            logger.error(f"All {max_retries} attempts failed")
                            raise
            return wrapper
        return decorator

    @retry_on_failure(max_retries=3, delay=2)
    def generate_token(self) -> str:
        """Generate new authentication token"""
        try:
            # Generate request token
            request_token_data = self.kite.get_login_url()  # Returns URL
            logger.info(f"Login URL generated: {request_token_data}")

            # In production, this would be obtained from user login
            # For now, using stored credentials
            kite = KiteConnect(api_key=KITE_API_KEY)
            data = kite.generate_session(KITE_USER_ID, KITE_PASSWORD, "")

            if data and 'access_token' in data:
                self.token = data['access_token']
                self.session_start = datetime.now()

                # Cache token
                redis_client.setex(
                    'kite_access_token',
                    3600,  # 1 hour expiry
                    self.token
                )

                logger.info("Access token generated successfully")
                return self.token
            else:
                raise Exception("Failed to generate access token")

        except Exception as e:
            logger.error(f"Token generation failed: {str(e)}")
            raise HTTPException(status_code=401, detail=str(e))

    def get_valid_token(self) -> str:
        """Get valid token, refresh if needed"""
        # Check cache first
        cached_token = redis_client.get('kite_access_token')
        if cached_token:
            return cached_token

        # Generate new token
        return self.generate_token()

    def get_market_data(self, symbols: List[str]) -> Dict:
        """Fetch market data for symbols"""
        try:
            token = self.get_valid_token()
            self.kite.set_access_token(token)

            # Fetch quote data
            quote_data = self.kite.quote(symbols)

            # Cache market data
            redis_client.setex(
                f"market_data:{','.join(symbols)}",
                60,  # 1 minute cache
                json.dumps(quote_data)
            )

            return quote_data

        except Exception as e:
            logger.error(f"Market data fetch failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Market data fetch failed")

    def get_nifty_options_chain(self, strike_distance: int = 100) -> Dict:
        """Fetch NIFTY options chain data"""
        try:
            token = self.get_valid_token()
            self.kite.set_access_token(token)

            # Get current NIFTY price
            nifty_quote = self.kite.quote('NSE:NIFTY50')
            current_price = nifty_quote['NSE:NIFTY50']['last_price']

            # Calculate ATM strike
            atm_strike = int(round(current_price / 100) * 100)

            # Get option symbols for strikes
            options_data = {}
            for strike in range(atm_strike - strike_distance, atm_strike + strike_distance + 100, 100):
                call_symbol = f"NFO:NIFTY{datetime.now().strftime('%d%b%y').upper()}C{strike}"
                put_symbol = f"NFO:NIFTY{datetime.now().strftime('%d%b%y').upper()}P{strike}"

                try:
                    call_data = self.kite.quote(call_symbol)
                    put_data = self.kite.quote(put_symbol)

                    options_data[strike] = {
                        'call': call_data.get(call_symbol, {}),
                        'put': put_data.get(put_symbol, {})
                    }
                except Exception as e:
                    logger.warning(f"Could not fetch {call_symbol}: {str(e)}")

            # Cache options chain
            redis_client.setex(
                'nifty_options_chain',
                30,  # 30 second cache
                json.dumps(options_data)
            )

            return {
                'atm_strike': atm_strike,
                'current_price': current_price,
                'options': options_data
            }

        except Exception as e:
            logger.error(f"Options chain fetch failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Options chain fetch failed")

    def calculate_greeks(self, symbol: str, option_type: str, strike: float,
                         spot_price: float, days_to_expiry: int,
                         volatility: float = 0.25, risk_free_rate: float = 0.06) -> Dict:
        """Calculate Greeks for options"""
        try:
            from scipy.stats import norm

            # Convert to required format
            S = float(spot_price)
            K = float(strike)
            T = days_to_expiry / 365.0
            r = risk_free_rate
            sigma = volatility

            # Black-Scholes calculations
            d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)

            if option_type.upper() == 'CALL':
                delta = norm.cdf(d1)
                gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
                vega = S * norm.pdf(d1) * np.sqrt(T) / 100
                theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) -
                         r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
            else:
                delta = norm.cdf(d1) - 1
                gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
                vega = S * norm.pdf(d1) * np.sqrt(T) / 100
                theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) +
                         r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365

            return {
                'delta': round(delta, 4),
                'gamma': round(gamma, 6),
                'vega': round(vega, 4),
                'theta': round(theta, 4)
            }

        except Exception as e:
            logger.error(f"Greeks calculation failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Greeks calculation failed")


# Initialize service
kite_service = KiteAuthenticationService()


# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/token", response_model=TokenResponse)
async def get_token():
    """Generate or retrieve valid access token"""
    token = kite_service.get_valid_token()
    return TokenResponse(
        access_token=token,
        expires_in=3600,
        message="Token generated successfully"
    )


@app.get("/market-data/{symbols}")
async def fetch_market_data(symbols: str):
    """Fetch market data for given symbols"""
    symbol_list = symbols.split(',')
    return kite_service.get_market_data(symbol_list)


@app.get("/options-chain")
async def fetch_options_chain(strike_distance: int = 100):
    """Fetch NIFTY options chain"""
    return kite_service.get_nifty_options_chain(strike_distance)


@app.get("/greeks")
async def get_greeks(symbol: str, option_type: str, strike: float,
                     spot_price: float, days_to_expiry: int):
    """Calculate Greeks for options"""
    return kite_service.calculate_greeks(
        symbol, option_type, strike, spot_price, days_to_expiry
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
