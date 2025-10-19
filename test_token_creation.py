import jwt
import base64
import time

# Use the exact same secret as the gateway
secret_b64 = "U29tZVZlcnlTdHJvbmdTZWNyZXRLZXlXaXRoRW5vdWdoQnl0ZXNGb3JFUjUxMkFsZ29yaXRobS0xMjM0NTY3ODkwYWJjZGVmZ2hpams="
secret = base64.b64decode(secret_b64)

# Create a token with the exact same payload structure
payload = {
    "roles": ["USER"],
    "sub": "test10", 
    "iat": int(time.time()),
    "exp": int(time.time()) + 3600  # 1 hour expiry
}

# Generate token with HS512
token = jwt.encode(payload, secret, algorithm="HS512")
print("Generated JWT token:")
print(token)
print()
print("Verification test:")
try:
    decoded = jwt.decode(token, secret, algorithms=["HS512"])
    print("✅ Token verification successful")
    print("Payload:", decoded)
except Exception as e:
    print("❌ Token verification failed:", e)
