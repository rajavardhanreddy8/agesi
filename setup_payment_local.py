"""
Razorpay Payment Gateway - Local Setup Helper Script

This script helps you set up Razorpay payment gateway locally by:
1. Checking if Razorpay credentials are configured
2. Testing the connection to Razorpay
3. Validating the payment flow
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_env_variables():
    """Check if required environment variables are set"""
    print("=" * 60)
    print("STEP 1: Checking Environment Variables")
    print("=" * 60)
    
    key_id = os.getenv('RAZORPAY_KEY_ID')
    key_secret = os.getenv('RAZORPAY_KEY_SECRET')
    
    if not key_id:
        print("❌ RAZORPAY_KEY_ID not found in environment variables")
        print("\n📝 To fix:")
        print("   1. Create a .env file in the project root")
        print("   2. Add: RAZORPAY_KEY_ID=your_key_id_here")
        print("   3. Get your key from: https://dashboard.razorpay.com/app/keys")
        return False
    else:
        print(f"✅ RAZORPAY_KEY_ID found: {key_id[:15]}...")
        if key_id.startswith('rzp_test_'):
            print("   (Test mode detected)")
        elif key_id.startswith('rzp_live_'):
            print("   ⚠️  LIVE mode detected - Be careful!")
    
    if not key_secret:
        print("❌ RAZORPAY_KEY_SECRET not found in environment variables")
        print("\n📝 To fix:")
        print("   1. Add to .env file: RAZORPAY_KEY_SECRET=your_key_secret_here")
        print("   2. Get your secret from: https://dashboard.razorpay.com/app/keys")
        return False
    else:
        print(f"✅ RAZORPAY_KEY_SECRET found: {'*' * 20}")
    
    print()
    return True

def test_razorpay_connection():
    """Test connection to Razorpay API"""
    print("=" * 60)
    print("STEP 2: Testing Razorpay Connection")
    print("=" * 60)
    
    try:
        import razorpay
    except ImportError:
        print("❌ razorpay package not installed")
        print("\n📝 To fix: pip install razorpay")
        return False
    
    try:
        key_id = os.getenv('RAZORPAY_KEY_ID')
        key_secret = os.getenv('RAZORPAY_KEY_SECRET')
        
        client = razorpay.Client(auth=(key_id, key_secret))
        
        # Try to create a test order
        print("Creating test order...")
        order_data = {
            'amount': 100,  # ₹1 in paise
            'currency': 'INR',
            'payment_capture': 1
        }
        order = client.order.create(data=order_data)
        
        print(f"✅ Connection successful!")
        print(f"   Test order created: {order['id']}")
        print(f"   Amount: ₹{order['amount'] / 100}")
        print(f"   Status: {order['status']}")
        print()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print("\n📝 Common issues:")
        print("   - Invalid API credentials")
        print("   - Network connectivity issues")
        print("   - API keys don't match (test vs live)")
        return False

def check_database():
    """Check if database tables exist"""
    print("=" * 60)
    print("STEP 3: Checking Database Schema")
    print("=" * 60)
    
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            print("❌ DATABASE_URL not found")
            return False
        
        # Parse connection string
        result = urlparse(db_url)
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        
        cur = conn.cursor()
        
        # Check for payments table
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'payments'
            );
        """)
        
        if cur.fetchone()[0]:
            print("✅ 'payments' table exists")
        else:
            print("❌ 'payments' table not found")
            print("   Run database migration: database/schema_supabase.sql")
        
        # Check for subscriptions table
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'subscriptions'
            );
        """)
        
        if cur.fetchone()[0]:
            print("✅ 'subscriptions' table exists")
        else:
            print("❌ 'subscriptions' table not found")
        
        conn.close()
        print()
        return True
        
    except Exception as e:
        print(f"⚠️  Could not verify database: {str(e)}")
        print("   (This is optional - payment gateway will work without DB check)")
        print()
        return True

def print_next_steps():
    """Print next steps for the user"""
    print("=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print()
    print("🎉 Your payment gateway setup is ready!")
    print()
    print("📋 To test the payment flow:")
    print("   1. Run: python test_payment.py")
    print("   2. This will create a test user and initiate payment")
    print("   3. Check the output for 'SUCCESS: Payment Gateway Order Created!'")
    print()
    print("🌐 To test with frontend:")
    print("   1. Start backend: python form_filler/api.py")
    print("   2. Open your frontend application")
    print("   3. Navigate to subscription/upgrade page")
    print("   4. Complete a test payment")
    print()
    print("🚀 For production deployment:")
    print("   1. Complete Razorpay KYC verification")
    print("   2. Get live API keys from Razorpay dashboard")
    print("   3. Update Azure environment variables")
    print("   4. Test with a small real payment")
    print()
    print("📚 Full documentation: implementation_plan.md")
    print()

def main():
    """Main setup verification function"""
    print("\n")
    print("🔧 RAZORPAY PAYMENT GATEWAY - LOCAL SETUP VERIFICATION")
    print()
    
    # Check environment
    if not check_env_variables():
        print("\n❌ Setup incomplete. Please configure environment variables first.")
        sys.exit(1)
    
    # Test connection
    if not test_razorpay_connection():
        print("\n❌ Setup incomplete. Please fix Razorpay connection issues.")
        sys.exit(1)
    
    # Check database (optional)
    check_database()
    
    # Print next steps
    print_next_steps()
    
    print("=" * 60)
    print("✅ LOCAL SETUP VERIFICATION COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    main()
