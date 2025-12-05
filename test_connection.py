#!/usr/bin/env python3
"""
Test script to verify all connections for the trading setup
"""
import os
import sys
import requests
import psycopg2
import redis
from datetime import datetime
from dotenv import load_dotenv
from kiteconnect import KiteConnect

# Load environment variables
load_dotenv()

def test_kite_connection():
    """Test Zerodha Kite API connection"""
    print("Testing Kite API connection...")
    try:
        api_key = os.getenv('KITE_API_KEY')
        api_secret = os.getenv('KITE_API_SECRET')
        access_token = os.getenv('KITE_ACCESS_TOKEN')
        
        if not all([api_key, api_secret]):
            print("  ❌ Kite API credentials not found in .env")
            return False
            
        kite = KiteConnect(api_key=api_key)
        
        if access_token:
            kite.set_access_token(access_token)
            profile = kite.profile()
            print(f"  ✅ Connected to Kite as: {profile['user_name']}")
            return True
        else:
            print("  ⚠️  Access token not set. Generate it daily at market open.")
            return False
            
    except Exception as e:
        print(f"  ❌ Kite connection failed: {str(e)}")
        return False

def test_n8n_connection():
    """Test n8n server connection"""
    print("Testing n8n connection...")
    try:
        response = requests.get('http://localhost:5678/healthz', timeout=5)
        if response.status_code == 200:
            print("  ✅ n8n is running")
            return True
        else:
            print(f"  ❌ n8n returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ n8n connection failed: {str(e)}")
        return False

def test_postgres_connection():
    """Test PostgreSQL connection"""
    print("Testing PostgreSQL connection...")
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', 5432),
            database=os.getenv('POSTGRES_DB', 'trading_db'),
            user=os.getenv('POSTGRES_USER', 'trader'),
            password=os.getenv('POSTGRES_PASSWORD', 'secure_password')
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"  ✅ PostgreSQL connected: {version[:30]}...")
        
        # Check if trading schema exists
        cursor.execute("""
            SELECT EXISTS(
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = 'trading'
            );
        """)
        schema_exists = cursor.fetchone()[0]
        
        if schema_exists:
            print("  ✅ Trading schema exists")
            
            # Check tables
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'trading';
            """)
            table_count = cursor.fetchone()[0]
            print(f"  ✅ Found {table_count} tables in trading schema")
        else:
            print("  ⚠️  Trading schema not found. Run database initialization.")
            
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ PostgreSQL connection failed: {str(e)}")
        return False

def test_redis_connection():
    """Test Redis connection"""
    print("Testing Redis connection...")
    try:
        r = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            password=os.getenv('REDIS_PASSWORD', None),
            decode_responses=True
        )
        
        # Test ping
        if r.ping():
            print("  ✅ Redis is running")
            
            # Set and get test value
            test_key = f"test_connection_{datetime.now().timestamp()}"
            r.set(test_key, "test_value", ex=10)
            value = r.get(test_key)
            
            if value == "test_value":
                print("  ✅ Redis read/write test passed")
                r.delete(test_key)
                return True
        
        return False
        
    except Exception as e:
        print(f"  ❌ Redis connection failed: {str(e)}")
        return False

def test_mcp_endpoint():
    """Test MCP endpoint for n8n"""
    print("Testing MCP endpoint...")
    try:
        # Test if MCP endpoint is accessible
        headers = {
            'Authorization': f"Bearer {os.getenv('KITE_ACCESS_TOKEN', 'test_token')}"
        }
        response = requests.get(
            'http://localhost:5678/mcp-server/http',
            headers=headers,
            timeout=5
        )
        
        if response.status_code in [200, 401, 403]:
            print("  ✅ MCP endpoint is responding")
            return True
        else:
            print(f"  ⚠️  MCP endpoint returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ⚠️  MCP endpoint test failed: {str(e)}")
        print("     This is normal if MCP workflows aren't imported yet")
        return False

def check_market_hours():
    """Check if current time is within market hours"""
    print("Checking market hours...")
    try:
        from pytz import timezone
        import datetime
        
        ist = timezone('Asia/Kolkata')
        now = datetime.datetime.now(ist)
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        if now.weekday() >= 5:
            print("  ℹ️  Weekend - Markets closed")
            return False
        elif market_open <= now <= market_close:
            print("  ✅ Market is OPEN")
            return True
        else:
            print(f"  ℹ️  Market is CLOSED (Opens at 9:15 AM IST)")
            return False
            
    except Exception as e:
        print(f"  ⚠️  Could not check market hours: {str(e)}")
        return False

def main():
    """Run all connection tests"""
    print("="*50)
    print("Options Trading Setup - Connection Test")
    print("="*50)
    print()
    
    results = {
        'Kite API': test_kite_connection(),
        'n8n': test_n8n_connection(),
        'PostgreSQL': test_postgres_connection(),
        'Redis': test_redis_connection(),
        'MCP Endpoint': test_mcp_endpoint(),
        'Market Hours': check_market_hours()
    }
    
    print()
    print("="*50)
    print("Test Summary:")
    print("-"*50)
    
    all_passed = True
    critical_services = ['n8n', 'PostgreSQL', 'Redis']
    
    for service, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {service}")
        if service in critical_services and not status:
            all_passed = False
    
    print("="*50)
    
    if all_passed:
        print("\n🎉 All critical services are running!")
        print("You can now:")
        print("1. Import n8n workflows")
        print("2. Configure your strategies")
        print("3. Start paper trading")
    else:
        print("\n⚠️  Some critical services are not running.")
        print("Please check the errors above and:")
        print("1. Ensure Docker containers are running: docker-compose ps")
        print("2. Check logs: docker-compose logs [service_name]")
        print("3. Verify .env configuration")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
