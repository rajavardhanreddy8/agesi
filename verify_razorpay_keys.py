
import razorpay
import os

# Credentials currently in Azure Env (verified via CLI)
KEY_ID = 'rzp_live_SHeEYfTnpJisHO'
KEY_SECRET = 'a1q4hxQ8sqCFmJY0C2GT7yzf'

print(f"Testing Keys: {KEY_ID} / {KEY_SECRET[:4]}...{KEY_SECRET[-4:]}")

try:
    client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))
    
    # Try to fetch orders (lightweight auth check)
    # or create a dummy order
    print("Attempting to create a test order...")
    order = client.order.create({
        'amount': 100, # 1 Rupee
        'currency': 'INR',
        'payment_capture': 1
    })
    print("SUCCESS! Keys are valid.")
    print(f"Order ID: {order['id']}")
    
except Exception as e:
    print("\nFAILURE! Keys are invalid or permissions missing.")
    print(f"Error: {e}")
