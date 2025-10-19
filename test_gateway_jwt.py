import jwt
import base64
import time
import hashlib
import hmac

# The secret key from the gateway configuration
secret_b64 = "U29tZVZlcnlTdHJvbmdTZWNyZXRLZXlXaXRoRW5vdWdoQnl0ZXNGb3JFUjUxMkFsZ29yaXRobS0xMjM0NTY3ODkwYWJjZGVmZ2hpams="
secret = base64.b64decode(secret_b64)

# The token to test
token = "eyJhbGciOiJIUzUxMiJ9.eyJyb2xlcyI6WyJVU0VSIl0sInN1YiI6InRlc3QxMCIsImlhdCI6MTc2MDgxNzk5MSwiZXhwIjoxNzYwOTA0MzkxfQ.jC5YHdGYQFbXWRXOTugYoK_lWBApLft9eTUk9Ut_k4woismozhezKhAsf3egtgSfPjzcRomr77i46LZsiww9MA"

print("=== JWT Token Analysis ===")
print(f"Secret (b64): {secret_b64}")
print(f"Secret length: {len(secret)} bytes")
print(f"Algorithm: HS512")
print()

try:
    # Decode without verification first
    decoded = jwt.decode(token, options={"verify_signature": False})
    print("✅ Token structure is valid")
    print(f"Contents: {decoded}")
    print()
    
    # Check expiration
    current_time = int(time.time())
    exp_time = decoded['exp']
    iat_time = decoded['iat']
    
    print(f"Current time: {current_time} ({time.ctime(current_time)})")
    print(f"Issued at: {iat_time} ({time.ctime(iat_time)})")
    print(f"Expires at: {exp_time} ({time.ctime(exp_time)})")
    print(f"Time until expiry: {(exp_time - current_time) // 60} minutes")
    print()
    
    if current_time > exp_time:
        print("❌ TOKEN IS EXPIRED")
    else:
        print("✅ Token is within valid time range")
    
    # Now try verification with HS512
    print("\n=== Testing Signature Verification ===")
    
    # Manually verify signature
    parts = token.split('.')
    header = parts[0]
    payload = parts[1]
    signature = parts[2]
    
    # Recreate signature
    message = f"{header}.{payload}".encode()
    expected_sig = hmac.new(secret, message, hashlib.sha512).digest()
    expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip('=')
    
    print(f"Expected signature: {expected_sig_b64}")
    print(f"Actual signature:   {signature}")
    print(f"Signatures match: {expected_sig_b64 == signature}")
    
    # Use PyJWT for verification
    try:
        verified = jwt.decode(token, secret, algorithms=["HS512"], leeway=60)
        print("✅ Token signature verification SUCCESSFUL")
        print(f"Verified payload: {verified}")
    except jwt.InvalidSignatureError as e:
        print(f"❌ Signature verification failed: {e}")
    except jwt.ExpiredSignatureError as e:
        print(f"❌ Token expired: {e}")
    except jwt.InvalidTokenError as e:
        print(f"❌ Invalid token: {e}")
        
except Exception as e:
    print(f"❌ Token decode failed: {e}")
