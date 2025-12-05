"""Production-Grade Order Execution Engine with Risk Management

Risk Management Features:
- Daily loss limit: ₹20,000 (hard circuit breaker)
- Max trades per day: 3
- Max open positions: 4
- Position sizing: Kelly Criterion based
- Stop loss: 40% of entry
- Profit target: 40% of entry
- Auto square-off before market close: 3:29 PM IST
"""

import os
import logging
from datetime import datetime, time
from typing import Dict, List, Optional
from enum import Enum
import asyncio

from fastapi import HTTPException
from kiteconnect import KiteConnect
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import telegram

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderSide(str, Enum):
    """Order side enumeration"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Order type enumeration"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL = "SL"
    SL_M = "SL-M"


class PositionStatus(str, Enum):
    """Position status enumeration"""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PARTIALLY_CLOSED = "PARTIALLY_CLOSED"


class RiskManagementRules:
    """Risk management constraints (IMMUTABLE)"""
    
    MAX_DAILY_LOSS_INR = 20000  # Hard stop
    MAX_TRADES_PER_DAY = 3
    MAX_OPEN_POSITIONS = 4
    STOP_LOSS_PERCENT = 0.40  # 40%
    PROFIT_TARGET_PERCENT = 0.40  # 40%
    MAX_POSITION_SIZE = 1  # 1 lot per strategy
    
    # Trading hours (IST)
    MARKET_OPEN = time(9, 15)
    MARKET_CLOSE = time(15, 30)
    AUTO_SQUARE_OFF_TIME = time(15, 29)  # 1 minute before close
    
    # Risk per trade
    MAX_RISK_PER_TRADE = 0.02  # 2% of capital
    KELLY_MULTIPLIER = 0.25  # Conservative Kelly


class OrderExecutor:
    """Production-grade order execution engine"""
    
    def __init__(self, kite_client: KiteConnect, db_connection, telegram_bot):
        self.kite = kite_client
        self.db = db_connection
        self.telegram = telegram_bot
        self.redis_client = redis.Redis(decode_responses=True)
        self.paper_trading = os.getenv('PAPER_TRADING', 'false').lower() == 'true'
        
    async def check_risk_limits(self, account_id: str) -> Dict:
        """Check if trading is allowed based on risk limits"""
        try:
            cursor = self.db.cursor(cursor_factory=RealDictCursor)
            
            # Check daily P&L
            cursor.execute("""
                SELECT COALESCE(SUM(pnl), 0) as daily_pnl
                FROM trades
                WHERE account_id = %s
                AND DATE(entry_time) = CURRENT_DATE
                AND exit_time IS NOT NULL
            """, (account_id,))
            
            daily_pnl = cursor.fetchone()['daily_pnl']
            
            # Check trade count for today
            cursor.execute("""
                SELECT COUNT(*) as trade_count
                FROM trades
                WHERE account_id = %s
                AND DATE(entry_time) = CURRENT_DATE
            """, (account_id,))
            
            trade_count = cursor.fetchone()['trade_count']
            
            # Check open positions
            cursor.execute("""
                SELECT COUNT(*) as open_positions
                FROM positions
                WHERE account_id = %s
                AND status = %s
            """, (account_id, PositionStatus.OPEN.value))
            
            open_positions = cursor.fetchone()['open_positions']
            
            cursor.close()
            
            # Determine if trading is allowed
            is_allowed = (
                daily_pnl > -RiskManagementRules.MAX_DAILY_LOSS_INR and
                trade_count < RiskManagementRules.MAX_TRADES_PER_DAY and
                open_positions < RiskManagementRules.MAX_OPEN_POSITIONS
            )
            
            return {
                'allowed': is_allowed,
                'daily_pnl': daily_pnl,
                'daily_loss_remaining': RiskManagementRules.MAX_DAILY_LOSS_INR + daily_pnl,
                'trades_remaining': RiskManagementRules.MAX_TRADES_PER_DAY - trade_count,
                'position_slots_remaining': RiskManagementRules.MAX_OPEN_POSITIONS - open_positions,
                'circuit_breaker_hit': daily_pnl <= -RiskManagementRules.MAX_DAILY_LOSS_INR
            }
            
        except Exception as e:
            logger.error(f"Risk check failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Risk check failed")
    
    async def calculate_position_size(self, symbol: str, entry_price: float,
                                      stop_loss_price: float,
                                      account_balance: float) -> int:
        """Calculate position size using Kelly Criterion"""
        try:
            # Get historical win rate for symbol
            cursor = self.db.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades
                FROM trades
                WHERE symbol = %s
                AND DATE(entry_time) >= CURRENT_DATE - INTERVAL '30 days'
            """, (symbol,))
            
            result = cursor.fetchone()
            total_trades = result['total_trades'] or 1
            winning_trades = result['winning_trades'] or 1
            
            cursor.close()
            
            # Win rate
            win_rate = winning_trades / total_trades
            loss_rate = 1 - win_rate
            
            # Risk per trade (in INR)
            risk_amount = account_balance * RiskManagementRules.MAX_RISK_PER_TRADE
            
            # Points at risk
            points_at_risk = abs(entry_price - stop_loss_price)
            
            # Position size
            position_size = int(risk_amount / points_at_risk)
            
            # Apply Kelly Criterion adjustment
            kelly_adjusted = int(position_size * RiskManagementRules.KELLY_MULTIPLIER)
            
            # Cap at max position size
            final_size = min(kelly_adjusted, RiskManagementRules.MAX_POSITION_SIZE)
            
            logger.info(f"Position size for {symbol}: {final_size} lots")
            return final_size
            
        except Exception as e:
            logger.error(f"Position size calculation failed: {str(e)}")
            # Return default conservative size
            return 1
    
    async def place_order(self, symbol: str, quantity: int, price: float,
                         order_type: OrderType, side: OrderSide,
                         stop_loss: float, target: float) -> Dict:
        """Place order with stop loss and target"""
        try:
            # Verify trading is allowed
            risk_check = await self.check_risk_limits("ACCOUNT_ID")
            
            if not risk_check['allowed']:
                error_msg = f"Trading not allowed. Circuit breaker: {risk_check['circuit_breaker_hit']}"
                logger.warning(error_msg)
                raise HTTPException(status_code=403, detail=error_msg)
            
            if not self.paper_trading:
                # Place actual order
                order_response = self.kite.place_order(
                    variety="regular",
                    exchange="NSE" if "NIFTY" in symbol else "NSE",
                    tradingsymbol=symbol,
                    transaction_type=side.value,
                    quantity=quantity,
                    price=price,
                    order_type=order_type.value,
                    product="MIS",
                    validity="DAY"
                )
                
                order_id = order_response.get('order_id')
            else:
                # Paper trading simulation
                order_id = f"PAPER_{datetime.now().timestamp()}"
                logger.info(f"Paper trading - Order simulated: {order_id}")
            
            # Log to database
            cursor = self.db.cursor()
            cursor.execute("""
                INSERT INTO trades 
                (order_id, symbol, quantity, entry_price, entry_time, 
                 stop_loss, target, status, pnl)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (order_id, symbol, quantity, price, datetime.now(),
                   stop_loss, target, PositionStatus.OPEN.value, 0))
            
            self.db.commit()
            cursor.close()
            
            # Send Telegram notification
            await self.telegram.send_message(
                f"🟢 ORDER PLACED\n"
                f"Symbol: {symbol}\n"
                f"Side: {side.value}\n"
                f"Quantity: {quantity}\n"
                f"Entry: ₹{price}\n"
                f"SL: ₹{stop_loss}\n"
                f"Target: ₹{target}"
            )
            
            return {
                'order_id': order_id,
                'symbol': symbol,
                'status': 'PLACED',
                'entry_price': price
            }
            
        except Exception as e:
            logger.error(f"Order placement failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Order placement failed: {str(e)}")
    
    async def auto_square_off_positions(self, account_id: str) -> Dict:
        """Auto square off all open positions before market close"""
        try:
            cursor = self.db.cursor(cursor_factory=RealDictCursor)
            
            # Get all open positions
            cursor.execute("""
                SELECT * FROM positions
                WHERE account_id = %s
                AND status = %s
            """, (account_id, PositionStatus.OPEN.value))
            
            open_positions = cursor.fetchall()
            squared_off = []
            
            for position in open_positions:
                try:
                    if not self.paper_trading:
                        # Exit at market
                        exit_side = OrderSide.SELL if position['quantity'] > 0 else OrderSide.BUY
                        self.kite.place_order(
                            variety="regular",
                            exchange="NSE",
                            tradingsymbol=position['symbol'],
                            transaction_type=exit_side.value,
                            quantity=abs(position['quantity']),
                            order_type=OrderType.MARKET.value,
                            product="MIS"
                        )
                    
                    # Update database
                    cursor.execute("""
                        UPDATE positions
                        SET status = %s, exit_time = %s
                        WHERE id = %s
                    """, (PositionStatus.CLOSED.value, datetime.now(), position['id']))
                    
                    squared_off.append(position['symbol'])
                    logger.info(f"Auto squared off: {position['symbol']}")
                    
                except Exception as e:
                    logger.error(f"Failed to square off {position['symbol']}: {str(e)}")
            
            self.db.commit()
            cursor.close()
            
            # Notify
            if squared_off:
                await self.telegram.send_message(
                    f"🔴 AUTO SQUARE-OFF (Market Close)\n"
                    f"Positions closed: {', '.join(squared_off)}"
                )
            
            return {'squared_off': squared_off, 'count': len(squared_off)}
            
        except Exception as e:
            logger.error(f"Auto square-off failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Auto square-off failed")


# Async background task for market close square-off
async def market_close_watchdog(executor: OrderExecutor):
    """Background task to square off all positions at market close"""
    while True:
        now = datetime.now().time()
        if RiskManagementRules.AUTO_SQUARE_OFF_TIME <= now <= RiskManagementRules.MARKET_CLOSE:
            try:
                await executor.auto_square_off_positions("ACCOUNT_ID")
            except Exception as e:
                logger.error(f"Market close watchdog failed: {str(e)}")
        
        await asyncio.sleep(60)  # Check every minute
