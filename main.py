from kiteconnect import KiteConnect
from config import API_KEY, API_SECRET, ACCESS_TOKEN
import webbrowser
import time

def authenticate():
    """
    Authenticate with Zerodha Kite API.
    This will open a browser for login and generate access token.
    """
    kite = KiteConnect(api_key=API_KEY)

    # Get login URL
    login_url = kite.login_url()

    print(f"Opening browser for Zerodha login: {login_url}")
    webbrowser.open(login_url)

    # Wait for user to complete login and get request token
    request_token = input("After logging in, copy the 'request_token' from the URL and paste it here: ")

    # Generate session
    try:
        data = kite.generate_session(request_token, api_secret=API_SECRET)
        kite.set_access_token(data["access_token"])

        # Update config.py with new access token
        update_config_access_token(data["access_token"])

        print("Authentication successful!")
        return kite
    except Exception as e:
        print(f"Authentication failed: {e}")
        return None

def update_config_access_token(access_token):
    """Update the ACCESS_TOKEN in config.py"""
    with open('config.py', 'r') as f:
        content = f.read()

    # Replace the ACCESS_TOKEN line
    old_line = "ACCESS_TOKEN = 'your_access_token_here'"
    new_line = f"ACCESS_TOKEN = '{access_token}'"

    updated_content = content.replace(old_line, new_line)

    with open('config.py', 'w') as f:
        f.write(updated_content)

def get_authenticated_kite():
    """Get authenticated KiteConnect instance"""
    kite = KiteConnect(api_key=API_KEY)
    kite.set_access_token(ACCESS_TOKEN)
    return kite

def get_instruments(kite):
    """Get list of available instruments"""
    try:
        instruments = kite.instruments()
        print(f"Retrieved {len(instruments)} instruments")
        return instruments
    except Exception as e:
        print(f"Error getting instruments: {e}")
        return []

def place_order(kite, tradingsymbol, transaction_type, quantity, order_type="MARKET", product="CNC"):
    """
    Place a trading order

    Parameters:
    - tradingsymbol: e.g., 'INFY'
    - transaction_type: 'BUY' or 'SELL'
    - quantity: number of shares
    - order_type: 'MARKET', 'LIMIT', etc.
    - product: 'CNC', 'MIS', etc.
    """
    try:
        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_NSE,
            tradingsymbol=tradingsymbol,
            transaction_type=transaction_type,
            quantity=quantity,
            order_type=order_type,
            product=product
        )
        print(f"Order placed successfully. Order ID: {order_id}")
        return order_id
    except Exception as e:
        print(f"Error placing order: {e}")
        return None

def get_positions(kite):
    """Get current positions"""
    try:
        positions = kite.positions()
        return positions
    except Exception as e:
        print(f"Error getting positions: {e}")
        return None

def main():
    # Check if access token exists
    if ACCESS_TOKEN == 'your_access_token_here':
        print("Access token not set. Starting authentication...")
        kite = authenticate()
        if not kite:
            return
    else:
        print("Using existing access token...")
        kite = get_authenticated_kite()

    # Test connection
    try:
        user = kite.profile()
        print(f"Connected to Zerodha as: {user['user_name']}")
    except Exception as e:
        print(f"Connection failed: {e}")
        print("Please check your credentials and try again.")
        return

    # Example: Get some instruments
    instruments = get_instruments(kite)
    if instruments:
        print("First 5 instruments:")
        for i in range(min(5, len(instruments))):
            print(f"- {instruments[i]['tradingsymbol']}: {instruments[i]['name']}")

    # Example: Get positions
    positions = get_positions(kite)
    if positions:
        print(f"Current positions: {len(positions['net'])}")

    print("Ready for algorithmic trading!")

if __name__ == "__main__":
    main()
