import jwt
import base64
import time

# Use the exact same secret
secret_b64 = "U29tZVZlcnlTdHJvbmdTZWNyZXRLZXlXaXRoRW5vdWdoQnl0ZXNGb3JFUjUxMkFsZ29yaXRobS0xMjM0NTY3ODkwYWJjZGVmZ2hpams="
secret = base64.b64decode(secret_b64)

# Create the exact same payload structure that's failing
current_time = 1760823146  # One of the timestamps from the error logs
payload = {
    "roles": ["USER"],
    "sub": "test10",
    "iat": current_time,
    "exp": current_time + 3600
}

print("Target payload:")
print(payload)
print()

# Generate token
token = jwt.encode(payload, secret, algorithm="HS512")
print("Generated token:")
print(token)
print()

# Verify locally
try:
    decoded = jwt.decode(token, secret, algorithms=["HS512"])
    print("✅ Local verification successful")
    print("Decoded payload:", decoded)
except Exception as e:
    print("❌ Local verification failed:", e)

# Check the exact Base64 encoded payload
import base64
parts = token.split('.')
payload_decoded = base64.urlsafe_b64decode(parts[1] + '==')
print("Raw payload bytes:", payload_decoded)
print("Payload as string:", payload_decoded.decode('utf-8'))
