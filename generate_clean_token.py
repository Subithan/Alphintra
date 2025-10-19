import jwt
import base64
import time
import json

# Use the exact same secret as the gateway
secret_b64 = "U29tZVZlcnlTdHJvbmdTZWNyZXRLZXlXaXRoRW5vdWdoQnl0ZXNGb3JFUjUxMkFsZ29yaXRobS0xMjM0NTY3ODkwYWJjZGVmZ2hpams="
secret = base64.b64decode(secret_b64)

# Create a clean payload
payload = {
    "roles": ["USER"],
    "sub": "test10", 
    "iat": int(time.time()),
    "exp": int(time.time()) + 3600
}

print("Payload (clean):")
print(json.dumps(payload, indent=2))

# Generate token with HS512
token = jwt.encode(payload, secret, algorithm="HS512")
print("\nGenerated JWT token:")
print(token)
print()

# Verify it's correct
try:
    decoded = jwt.decode(token, secret, algorithms=["HS512"])
    print("✅ Token verification successful")
    print("Decoded payload:")
    print(json.dumps(decoded, indent=2))
except Exception as e:
    print("❌ Token verification failed:", e)

# Save to file for safe copying
with open('/tmp/clean_jwt_token.txt', 'w') as f:
    f.write(token)
print(f"\nToken saved to /tmp/clean_jwt_token.txt for safe copying")
