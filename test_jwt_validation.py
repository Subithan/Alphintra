#!/usr/bin/env python3
import jwt
import base64
import json

# The JWT token from auth service
token = "eyJhbGciOiJIUzUxMiJ9.eyJyb2xlcyI6WyJVU0VSIl0sInN1YiI6InRlc3QxMCIsImlhdCI6MTc2MDg1NTUwMywiZXhwIjoxNzYwOTQxOTAzfQ.9e3hNIZ_Crka5lTJS9RogfCzrpw0xr_H6cLqhi900-Rxdd-rKT6U1FDimNilreN7WxmvaPAR7TBahqh10ozZig"

# The base64-encoded secret (same as in Kubernetes secrets)
secret_b64 = "U29tZVZlcnlTdHJvbmdTZWNyZXRLZXlXaXRoRW5vdWdoQnl0ZXNGb3JFUjUxMkFsZ29yaXRobS0xMjM0NTY3ODkwYWJjZGVmZ2hpams="

# Decode the base64 secret
secret = base64.b64decode(secret_b64)

print(f"Secret (base64): {secret_b64}")
print(f"Secret (decoded): {secret}")
print(f"Secret length: {len(secret)} bytes")
print()

# Decode the token header
header = jwt.get_unverified_header(token)
print(f"Token Header: {json.dumps(header, indent=2)}")
print()

# Decode the token payload
payload = jwt.decode(token, options={"verify_signature": False})
print(f"Token Payload: {json.dumps(payload, indent=2)}")
print()

# Try to verify the token
try:
    decoded = jwt.decode(token, secret, algorithms=["HS512"])
    print("✅ TOKEN VERIFICATION SUCCESSFUL!")
    print(f"Decoded payload: {json.dumps(decoded, indent=2)}")
except jwt.InvalidSignatureError as e:
    print(f"❌ SIGNATURE VERIFICATION FAILED: {e}")
except jwt.ExpiredSignatureError as e:
    print(f"❌ TOKEN EXPIRED: {e}")
except jwt.DecodeError as e:
    print(f"❌ DECODE ERROR: {e}")
except Exception as e:
    print(f"❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")
