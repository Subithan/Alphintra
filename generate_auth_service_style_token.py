import jwt
import base64
import time
from datetime import datetime, timedelta

# Use the exact same secret as the gateway
secret_b64 = "U29tZVZlcnlTdHJvbmdTZWNyZXRLZXlXaXRoRW5vdWdoQnl0ZXNGb3JFUjUxMkFsZ29yaXRobS0xMjM0NTY3ODkwYWJjZGVmZ2hpams="
secret = base64.b64decode(secret_b64)

# Mimic auth-service token generation exactly
def build_token(subject, roles):
    now = datetime.utcnow()
    claims = {
        "roles": [role for role in roles],
    }
    
    # This mimics the auth-service buildToken method
    token = jwt.encode(
        claims,
        secret,
        algorithm="HS512",
        headers={"alg": "HS512", "typ": "JWT"}
    )
    return token

# Generate token
token = build_token("test10", ["USER"])
print("Auth-service style token:")
print(token)
print()

# Test it locally first
try:
    decoded = jwt.decode(token, secret, algorithms=["HS512"])
    print("✅ Local verification successful")
    print("Decoded payload:", decoded)
except Exception as e:
    print("❌ Local verification failed:", e)

# Save to file for shell testing
with open('/tmp/auth_style_token.txt', 'w') as f:
    f.write(token)
print("Token saved to /tmp/auth_style_token.txt")
