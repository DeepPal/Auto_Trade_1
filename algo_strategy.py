# algo_strategy.py - Simple algorithmic trading strategies

from main import get_authenticated_kite, place_order
import time
import random  # For demo purposes only - replace with real strategy

def simple_momentum_strategy(kite, symbol="INFY", quantity=1):
    """
    Simple momentum strategy example
    This is for demonstration only - NOT for real trading
    """
    print(f"Running momentum strategy for {symbol}")

    try:
        # Get current price (simplified)
        quote = kite.quote(f"NSE:{symbol}")
        current_price = quote[f"NSE:{symbol}"]["last_price"]
        print(f"Current price of {symbol}: {current_price}")

        # Random decision for demo (replace with real logic)
        if random.choice([True, False]):
            print("Buying...")
            order_id = place_order(kite, symbol, "BUY", quantity)
        else:
            print("Selling...")
            order_id = place_order(kite, symbol, "SELL", quantity)

        return order_id

    except Exception as e:
        print(f"Strategy error: {e}")
        return None

def moving_average_crossover_strategy(kite, symbol="INFY", short_window=5, long_window=20):
    """
    Moving average crossover strategy
    This is a basic example - enhance with real data
    """
    print(f"Running MA crossover strategy for {symbol}")

    try:
        # Get historical data
        historical_data = kite.historical_data(
            instrument_token=kite.instruments("NSE")[symbol]["instrument_token"],
            from_date="2024-01-01",
            to_date="2024-01-10",
            interval="day"
        )

        if len(historical_data) < long_window:
            print("Not enough data for strategy")
            return None

        # Calculate moving averages (simplified)
        prices = [candle["close"] for candle in historical_data]
        short_ma = sum(prices[-short_window:]) / short_window
        long_ma = sum(prices[-long_window:]) / long_window

        print(f"Short MA: {short_ma}, Long MA: {long_ma}")

        # Simple crossover logic
        if short_ma > long_ma:
            print("Short MA above Long MA - Buying signal")
            order_id = place_order(kite, symbol, "BUY", 1)
        else:
            print("Short MA below Long MA - Selling signal")
            order_id = place_order(kite, symbol, "SELL", 1)

        return order_id

    except Exception as e:
        print(f"Strategy error: {e}")
        return None

def run_automated_trading():
    """Run automated trading with multiple strategies"""
    kite = get_authenticated_kite()

    if not kite:
        print("Authentication failed")
        return

    print("Starting automated trading...")

    # Run strategies in a loop (with delays for demo)
    strategies = [simple_momentum_strategy, moving_average_crossover_strategy]
    symbols = ["INFY", "TCS", "RELIANCE"]

    for i in range(3):  # Run 3 cycles
        strategy = random.choice(strategies)
        symbol = random.choice(symbols)

        strategy(kite, symbol)

        # Wait before next trade (demo delay)
        print("Waiting 10 seconds before next trade...")
        time.sleep(10)

    print("Automated trading session completed")

if __name__ == "__main__":
    run_automated_trading()
