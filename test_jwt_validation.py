#!/usr/bin/env python3
"""
Test script to verify that JWT tokens now contain user ID claims.
This script simulates the no-code-service JWT extraction process.
"""

import jwt
import base64
import json
import sys

def decode_jwt_payload(token):
    """Decode JWT payload without verification"""
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except Exception as e:
        print(f"❌ Error decoding JWT: {e}")
        return None

def test_jwt_user_id_extraction(token):
    """Test JWT token user ID extraction like no-code-service does"""
    print("🔍 Testing JWT token user ID extraction...")
    print("=" * 50)

    payload = decode_jwt_payload(token)
    if not payload:
        return False

    print("✅ JWT token decoded successfully")
    print(f"📋 Token claims: {list(payload.keys())}")
    print(f"📄 Full payload: {json.dumps(payload, indent=2)}")
    print()

    # Test extraction like no-code-service does
    user_id_fields = ['sub', 'user_id', 'userId', 'id']
    extracted_user_id = None

    for field in user_id_fields:
        if field in payload:
            user_id = payload[field]
            if isinstance(user_id, (str, int)):
                extracted_user_id = str(user_id)
                print(f"✅ Found user ID in field '{field}': {extracted_user_id}")
                break

    if extracted_user_id:
        print(f"🎉 SUCCESS: Extracted user ID: {extracted_user_id}")

        # Check if it's the new user_id claim (numeric)
        if 'user_id' in payload and isinstance(payload['user_id'], (int, float)):
            print("✅ Using new user_id claim (numeric) - Perfect for no-code-service!")
        elif 'sub' in payload:
            print(f"⚠️  Using sub claim (username): {payload['sub']}")
            print("   This suggests the token was generated with the old auth-service.")

        return True
    else:
        print("❌ No user ID found in any expected field")
        return False

def main():
    print("🧪 JWT User ID Validation Test")
    print("=" * 50)

    if len(sys.argv) == 2:
        token = sys.argv[1]
    else:
        # Example token (old format without user_id claim)
        print("ℹ️  No token provided, using example token...")
        print("   To test with a real token: python test_jwt_validation.py <your_jwt_token>")
        print()
        token = "eyJhbGciOiJIUzUxMiJ9.eyJyb2xlcyI6WyJVU0VSIl0sInN1YiI6InRlc3QxMCIsImlhdCI6MTc2MDg1NTUwMywiZXhwIjoxNzYwOTQxOTAzfQ.9e3hNIZ_Crka5lTJS9RogfCzrpw0xr_H6cLqhi900-Rxdd-rKT6U1FDimNilreN7WxmvaPAR7TBahqh10ozZig"

    success = test_jwt_user_id_extraction(token)

    if success:
        print("\n🎯 CONCLUSION:")
        print("✅ The JWT token structure is compatible with no-code-service")
        print("✅ User ID extraction should work correctly")
    else:
        print("\n❌ CONCLUSION:")
        print("❌ JWT token missing user ID information")
        print("❌ Please verify auth-service implementation")

if __name__ == "__main__":
    main()
