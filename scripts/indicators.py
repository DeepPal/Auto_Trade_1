"""
Technical Indicators for Options Trading Strategy
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import talib

class TechnicalIndicators:
    """Calculate technical indicators for trading signals"""
    
    def __init__(self, symbol: str, timeframe: str = '15min'):
        self.symbol = symbol
        self.timeframe = timeframe
        
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        return talib.RSI(prices, timeperiod=period).iloc[-1]
    
    def calculate_macd(self, prices: pd.Series) -> Dict[str, float]:
        """Calculate MACD indicator"""
        macd, signal, histogram = talib.MACD(prices, 
                                             fastperiod=12, 
                                             slowperiod=26, 
                                             signalperiod=9)
        return {
            'macd': macd.iloc[-1],
            'signal': signal.iloc[-1],
            'histogram': histogram.iloc[-1]
        }
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20) -> Dict[str, float]:
        """Calculate Bollinger Bands"""
        upper, middle, lower = talib.BBANDS(prices, 
                                           timeperiod=period,
                                           nbdevup=2,
                                           nbdevdn=2)
        current_price = prices.iloc[-1]
        return {
            'upper': upper.iloc[-1],
            'middle': middle.iloc[-1],
            'lower': lower.iloc[-1],
            'position': (current_price - lower.iloc[-1]) / (upper.iloc[-1] - lower.iloc[-1])
        }
    
    def calculate_supertrend(self, high: pd.Series, low: pd.Series, close: pd.Series,
                           period: int = 10, multiplier: float = 3) -> Dict[str, any]:
        """Calculate Supertrend indicator"""
        hl_avg = (high + low) / 2
        atr = talib.ATR(high, low, close, timeperiod=period)
        
        upper_band = hl_avg + (multiplier * atr)
        lower_band = hl_avg - (multiplier * atr)
        
        supertrend = pd.Series(index=close.index)
        direction = pd.Series(index=close.index)
        
        for i in range(period, len(close)):
            if close.iloc[i] <= upper_band.iloc[i]:
                supertrend.iloc[i] = upper_band.iloc[i]
                direction.iloc[i] = -1
            else:
                supertrend.iloc[i] = lower_band.iloc[i]
                direction.iloc[i] = 1
                
        return {
            'value': supertrend.iloc[-1],
            'direction': direction.iloc[-1],
            'signal': 'BUY' if direction.iloc[-1] == 1 else 'SELL'
        }
    
    def calculate_ema_crossover(self, prices: pd.Series, fast: int = 9, slow: int = 21) -> Dict[str, any]:
        """Calculate EMA crossover"""
        ema_fast = talib.EMA(prices, timeperiod=fast)
        ema_slow = talib.EMA(prices, timeperiod=slow)
        
        crossover = ema_fast.iloc[-1] > ema_slow.iloc[-1]
        prev_crossover = ema_fast.iloc[-2] > ema_slow.iloc[-2]
        
        signal = 'NEUTRAL'
        if crossover and not prev_crossover:
            signal = 'BUY'
        elif not crossover and prev_crossover:
            signal = 'SELL'
            
        return {
            'ema_fast': ema_fast.iloc[-1],
            'ema_slow': ema_slow.iloc[-1],
            'crossover': crossover,
            'signal': signal
        }
    
    def calculate_volume_profile(self, prices: pd.Series, volumes: pd.Series, bins: int = 20) -> Dict:
        """Calculate volume profile and identify high volume nodes"""
        price_bins = pd.cut(prices, bins=bins)
        volume_profile = volumes.groupby(price_bins).sum()
        
        poc_idx = volume_profile.idxmax()  # Point of Control
        vah = volume_profile.quantile(0.7)  # Value Area High
        val = volume_profile.quantile(0.3)  # Value Area Low
        
        return {
            'poc': poc_idx.mid if poc_idx else 0,
            'vah': vah,
            'val': val,
            'current_position': self._get_position_in_profile(prices.iloc[-1], poc_idx, vah, val)
        }
    
    def _get_position_in_profile(self, price: float, poc: float, vah: float, val: float) -> str:
        """Determine price position relative to volume profile"""
        if price > vah:
            return 'ABOVE_VALUE'
        elif price < val:
            return 'BELOW_VALUE'
        else:
            return 'IN_VALUE'
    
    def generate_composite_signal(self, price_data: pd.DataFrame) -> Dict[str, any]:
        """Generate composite signal from all indicators"""
        signals = []
        weights = {
            'rsi': 0.20,
            'macd': 0.25,
            'bollinger': 0.15,
            'supertrend': 0.20,
            'ema': 0.20
        }
        
        # RSI Signal
        rsi = self.calculate_rsi(price_data['close'])
        if rsi < 30:
            signals.append(('rsi', 100, 'OVERSOLD'))
        elif rsi > 70:
            signals.append(('rsi', -100, 'OVERBOUGHT'))
        else:
            signals.append(('rsi', 0, 'NEUTRAL'))
        
        # MACD Signal
        macd = self.calculate_macd(price_data['close'])
        if macd['histogram'] > 0 and macd['macd'] > macd['signal']:
            signals.append(('macd', 80, 'BULLISH'))
        elif macd['histogram'] < 0 and macd['macd'] < macd['signal']:
            signals.append(('macd', -80, 'BEARISH'))
        else:
            signals.append(('macd', 0, 'NEUTRAL'))
        
        # Bollinger Bands
        bb = self.calculate_bollinger_bands(price_data['close'])
        if bb['position'] < 0.2:
            signals.append(('bollinger', 70, 'OVERSOLD'))
        elif bb['position'] > 0.8:
            signals.append(('bollinger', -70, 'OVERBOUGHT'))
        else:
            signals.append(('bollinger', 0, 'NEUTRAL'))
        
        # Supertrend
        st = self.calculate_supertrend(price_data['high'], price_data['low'], price_data['close'])
        if st['direction'] == 1:
            signals.append(('supertrend', 90, 'BUY'))
        else:
            signals.append(('supertrend', -90, 'SELL'))
        
        # EMA Crossover
        ema = self.calculate_ema_crossover(price_data['close'])
        if ema['signal'] == 'BUY':
            signals.append(('ema', 85, 'BUY'))
        elif ema['signal'] == 'SELL':
            signals.append(('ema', -85, 'SELL'))
        else:
            signals.append(('ema', 0, 'NEUTRAL'))
        
        # Calculate weighted score
        total_score = sum(score * weights.get(indicator, 0) for indicator, score, _ in signals)
        
        # Determine action
        if total_score >= 50:
            action = 'BUY'
            confidence = min(total_score, 100)
        elif total_score <= -50:
            action = 'SELL'
            confidence = min(abs(total_score), 100)
        else:
            action = 'NEUTRAL'
            confidence = 100 - abs(total_score)
        
        return {
            'signals': signals,
            'total_score': total_score,
            'action': action,
            'confidence': confidence,
            'timestamp': pd.Timestamp.now()
        }


class OptionsGreeksAnalyzer:
    """Analyze options Greeks for strategy selection"""
    
    def __init__(self, spot_price: float):
        self.spot = spot_price
        
    def calculate_greeks(self, strike: float, premium: float, expiry_days: int, 
                        option_type: str = 'CE', iv: float = 0.15) -> Dict[str, float]:
        """Calculate option Greeks using Black-Scholes model"""
        from scipy.stats import norm
        
        r = 0.06  # Risk-free rate (6%)
        t = expiry_days / 365
        
        # Black-Scholes calculations
        d1 = (np.log(self.spot / strike) + (r + iv**2 / 2) * t) / (iv * np.sqrt(t))
        d2 = d1 - iv * np.sqrt(t)
        
        if option_type == 'CE':
            delta = norm.cdf(d1)
            theta = (-self.spot * norm.pdf(d1) * iv / (2 * np.sqrt(t)) 
                    - r * strike * np.exp(-r * t) * norm.cdf(d2)) / 365
        else:  # PE
            delta = norm.cdf(d1) - 1
            theta = (-self.spot * norm.pdf(d1) * iv / (2 * np.sqrt(t)) 
                    + r * strike * np.exp(-r * t) * norm.cdf(-d2)) / 365
        
        gamma = norm.pdf(d1) / (self.spot * iv * np.sqrt(t))
        vega = self.spot * norm.pdf(d1) * np.sqrt(t) / 100
        
        return {
            'delta': round(delta, 4),
            'gamma': round(gamma, 4),
            'theta': round(theta, 2),
            'vega': round(vega, 2),
            'iv': round(iv * 100, 2)
        }
    
    def evaluate_strategy(self, strategy_type: str, strikes: Dict, greeks: Dict) -> Dict:
        """Evaluate options strategy based on Greeks"""
        score = 0
        analysis = []
        
        if strategy_type == 'iron_condor':
            # Check for ideal Greeks range
            total_delta = sum(g['delta'] for g in greeks.values())
            total_theta = sum(g['theta'] for g in greeks.values())
            
            if abs(total_delta) < 0.05:
                score += 30
                analysis.append('Delta neutral ✓')
            
            if total_theta > 50:
                score += 30
                analysis.append('Good theta decay ✓')
                
            # Check IV percentile
            avg_iv = np.mean([g['iv'] for g in greeks.values()])
            if avg_iv > 18:
                score += 20
                analysis.append('High IV environment ✓')
                
        elif strategy_type == 'short_strangle':
            # Different evaluation for strangles
            ce_delta = greeks.get('sell_ce', {}).get('delta', 0)
            pe_delta = abs(greeks.get('sell_pe', {}).get('delta', 0))
            
            if 0.25 <= ce_delta <= 0.35 and 0.25 <= pe_delta <= 0.35:
                score += 40
                analysis.append('Optimal delta range ✓')
                
        return {
            'score': score,
            'max_score': 100,
            'analysis': analysis,
            'recommendation': 'EXECUTE' if score >= 70 else 'WAIT'
        }


def backtest_strategy(data: pd.DataFrame, initial_capital: float = 1000000) -> Dict:
    """Backtest the options trading strategy"""
    indicators = TechnicalIndicators('NIFTY')
    
    trades = []
    capital = initial_capital
    positions = []
    
    for i in range(100, len(data)):
        # Get price slice
        price_slice = data.iloc[i-100:i]
        
        # Generate signal
        signal = indicators.generate_composite_signal(price_slice)
        
        if signal['action'] == 'BUY' and signal['confidence'] > 70:
            # Simulate option trade
            trade = {
                'entry_date': data.index[i],
                'entry_price': data['close'].iloc[i],
                'position_size': min(capital * 0.02, 100000),  # 2% risk
                'signal_confidence': signal['confidence']
            }
            positions.append(trade)
            
        elif signal['action'] == 'SELL' and positions:
            # Exit positions
            for position in positions:
                exit_price = data['close'].iloc[i]
                pnl = (exit_price - position['entry_price']) / position['entry_price']
                trade_pnl = position['position_size'] * pnl
                
                capital += trade_pnl
                trades.append({
                    **position,
                    'exit_date': data.index[i],
                    'exit_price': exit_price,
                    'pnl': trade_pnl,
                    'return_pct': pnl * 100
                })
            positions = []
    
    # Calculate metrics
    if trades:
        returns = pd.Series([t['pnl'] for t in trades])
        win_rate = len([t for t in trades if t['pnl'] > 0]) / len(trades)
        
        metrics = {
            'total_trades': len(trades),
            'win_rate': win_rate,
            'total_return': (capital - initial_capital) / initial_capital,
            'sharpe_ratio': returns.mean() / returns.std() if returns.std() > 0 else 0,
            'max_drawdown': (returns.cumsum().max() - returns.cumsum().min()) / initial_capital,
            'avg_win': returns[returns > 0].mean() if len(returns[returns > 0]) > 0 else 0,
            'avg_loss': returns[returns < 0].mean() if len(returns[returns < 0]) > 0 else 0
        }
    else:
        metrics = {'error': 'No trades executed'}
    
    return {
        'trades': trades,
        'metrics': metrics,
        'final_capital': capital
    }


if __name__ == "__main__":
    # Example usage
    print("Options Trading Technical Indicators Module")
    print("=" * 50)
    
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=500, freq='15min')
    sample_data = pd.DataFrame({
        'open': np.random.randn(500).cumsum() + 21000,
        'high': np.random.randn(500).cumsum() + 21050,
        'low': np.random.randn(500).cumsum() + 20950,
        'close': np.random.randn(500).cumsum() + 21000,
        'volume': np.random.randint(1000, 10000, 500)
    }, index=dates)
    
    # Test indicators
    ti = TechnicalIndicators('NIFTY')
    signal = ti.generate_composite_signal(sample_data.tail(100))
    
    print(f"Composite Signal: {signal['action']}")
    print(f"Confidence: {signal['confidence']:.1f}%")
    print(f"Total Score: {signal['total_score']:.1f}")
    
    # Test Greeks
    greeks = OptionsGreeksAnalyzer(21500)
    sample_greeks = greeks.calculate_greeks(21600, 150, 7, 'CE', 0.18)
    print(f"\nSample Greeks for 21600 CE:")
    for key, value in sample_greeks.items():
        print(f"  {key}: {value}")
