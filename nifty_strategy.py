"""NIFTY Options Trading Strategy Engine

Implements multiple strategies:
1. ATM Call Buying (directional)
2. Iron Condor (delta neutral)
3. Short Strangle (premium collection)
4. Calendar Spread (theta decay)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)


class Strategy(str, Enum):
    """Trading strategy enumeration"""
    ATM_CALL = "ATM_CALL"
    IRON_CONDOR = "IRON_CONDOR"
    SHORT_STRANGLE = "SHORT_STRANGLE"
    CALENDAR_SPREAD = "CALENDAR_SPREAD"


class StrategySignal:
    """Encapsulates a strategy signal for execution"""
    
    def __init__(self, strategy: Strategy, symbol: str, signal_score: float,
                 entry_price: float, stop_loss: float, target: float,
                 signal_reasons: List[str]):
        self.strategy = strategy
        self.symbol = symbol
        self.signal_score = signal_score  # 0-100
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.target = target
        self.signal_reasons = signal_reasons
        self.timestamp = datetime.now()


class NIFTYStrategyEngine:
    """Production NIFTY options strategy engine"""
    
    def __init__(self, min_signal_score: float = 70):
        self.min_signal_score = min_signal_score
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI for given prices"""
        if len(prices) < period + 1:
            return 50.0
            
        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_macd(self, prices: List[float]) -> Tuple[float, float, float]:
        """Calculate MACD, Signal, Histogram"""
        if len(prices) < self.macd_slow:
            return 0, 0, 0
            
        ema_fast = self._calculate_ema(prices, self.macd_fast)
        ema_slow = self._calculate_ema(prices, self.macd_slow)
        macd_line = ema_fast - ema_slow
        
        macd_values = []
        for i in range(len(prices)):
            ema_f = self._calculate_ema(prices[:i+1], self.macd_fast)
            ema_s = self._calculate_ema(prices[:i+1], self.macd_slow)
            macd_values.append(ema_f - ema_s)
        
        signal_line = self._calculate_ema(macd_values, self.macd_signal)
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) == 0:
            return 0
        if len(prices) == 1:
            return prices[0]
            
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = price * multiplier + ema * (1 - multiplier)
        
        return ema
    
    def generate_atm_call_signal(self, nifty_price: float,
                                 prices_history: List[float],
                                 rsi: float, macd_line: float,
                                 macd_signal: float) -> Optional[StrategySignal]:
        """Generate ATM call buying signal"""
        reasons = []
        score = 0
        
        # RSI bullish signal
        if 30 < rsi < 70:  # Not oversold or overbought
            score += 25
            reasons.append(f"RSI {rsi:.1f} in neutral zone")
        elif rsi < 30:
            score += 35
            reasons.append(f"RSI {rsi:.1f} oversold - bullish signal")
        
        # MACD bullish crossover
        if macd_line > macd_signal and macd_line > 0:
            score += 25
            reasons.append("MACD bullish crossover")
        elif macd_line > macd_signal:
            score += 15
            reasons.append("MACD above signal line")
        
        # Price momentum
        if len(prices_history) >= 5:
            recent_trend = np.polyfit(range(5), prices_history[-5:], 1)[0]
            if recent_trend > 0:
                score += 25
                reasons.append(f"Uptrend confirmed: {recent_trend:.4f} slope")
            elif recent_trend < -0.1:
                score -= 15
                reasons.append("Downtrend - skip signal")
        
        if score >= self.min_signal_score:
            # Calculate entry, SL, and target
            atm_strike = int(round(nifty_price / 100) * 100)
            entry = nifty_price * 1.01  # 1% above current
            sl = atm_strike - 200  # 200 points below ATM
            target = atm_strike + 300  # 300 points above ATM
            
            return StrategySignal(
                strategy=Strategy.ATM_CALL,
                symbol="NIFTY",
                signal_score=score,
                entry_price=entry,
                stop_loss=sl,
                target=target,
                signal_reasons=reasons
            )
        
        return None
    
    def generate_iron_condor_signal(self, nifty_price: float,
                                   iv_percentile: float) -> Optional[StrategySignal]:
        """Generate Iron Condor signal (delta neutral)"""
        reasons = []
        score = 0
        
        # Suitable in moderate volatility
        if 30 < iv_percentile < 70:
            score += 50
            reasons.append(f"IV Percentile {iv_percentile:.1f} ideal for IC")
        elif iv_percentile > 50:
            score += 30
            reasons.append(f"IV Percentile {iv_percentile:.1f} acceptable")
        else:
            score -= 20
            reasons.append(f"IV Percentile {iv_percentile:.1f} too low for IC")
        
        if score >= self.min_signal_score:
            atm_strike = int(round(nifty_price / 100) * 100)
            entry = nifty_price
            sl = atm_strike  # Neutral SL
            target = atm_strike  # Delta neutral target
            
            return StrategySignal(
                strategy=Strategy.IRON_CONDOR,
                symbol="NIFTY",
                signal_score=score,
                entry_price=entry,
                stop_loss=sl,
                target=target,
                signal_reasons=reasons
            )
        
        return None
    
    def validate_signal(self, signal: StrategySignal, market_context: Dict) -> bool:
        """Validate signal against market context"""
        # Don't trade within 30 minutes of market open/close
        now = datetime.now().time()
        market_open = datetime.strptime("09:15", "%H:%M").time()
        market_close = datetime.strptime("15:30", "%H:%M").time()
        
        if (datetime.strptime(str(now), "%H:%M:%S") - 
            datetime.strptime(str(market_open), "%H:%M:%S")).total_seconds() < 1800:
            logger.warning("Too close to market open")
            return False
        
        if abs((datetime.strptime(str(market_close), "%H:%M:%S") -
                datetime.strptime(str(now), "%H:%M:%S")).total_seconds()) < 1800:
            logger.warning("Too close to market close")
            return False
        
        # Validate SL and target
        if signal.strategy == Strategy.ATM_CALL:
            if signal.target <= signal.entry_price:
                logger.warning("Target must be above entry")
                return False
        
        logger.info(f"Signal validated: {signal.strategy}")
        return True
