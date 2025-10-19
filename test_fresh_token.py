import jwt
import base64
import time
import subprocess

# Use the exact same secret as the gateway
secret_b64 = "U29tZVZlcnlTdHJvbmdTZWNyZXRLZXlXaXRoRW5vdWdoQnl0ZXNGb3JFUjUxMkFsZ29yaXRobS0xMjM0NTY3ODkwYWJjZGVmZ2hpams="
secret = base64.b64decode(secret_b64)

# Create a clean payload with current timestamp
payload = {
    "roles": ["USER"],
    "sub": "test10", 
    "iat": int(time.time()),
    "exp": int(time.time()) + 3600
}

# Generate token with HS512
token = jwt.encode(payload, secret, algorithm="HS512")
print("Freshly generated token:")
print(token)

# Test immediately with curl
cmd = [
    "curl", "-s", "-w", "Status: %{http_code}\\n",
    "-H", f"Authorization: Bearer {token}",
    "https://api.alphintra.com/api/workflows"
]

print("\nTesting immediately:")
result = subprocess.run(cmd, capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
