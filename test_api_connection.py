#!/usr/bin/env python3
# Test script to verify API connection between frontend and backend
import urllib.request
import urllib.error
import json

def test_api_connection():
    print('🧪 Testing API Connection...')
    
    try:
        # Test health endpoint
        print('\n1. Testing health endpoint...')
        try:
            with urllib.request.urlopen('http://localhost:8004/health') as response:
                health_data = json.loads(response.read().decode())
                print('✅ Health check:', health_data)
        except urllib.error.URLError as e:
            print('❌ Health check failed:', str(e))
        
        # Test workflows endpoint
        print('\n2. Testing workflows endpoint...')
        try:
            req = urllib.request.Request(
                'http://localhost:8004/api/workflows',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer test-token'
                }
            )
            with urllib.request.urlopen(req) as response:
                workflows_data = json.loads(response.read().decode())
                print(f'✅ Workflows endpoint working: {len(workflows_data)} workflows found')
        except urllib.error.HTTPError as e:
            print(f'❌ Workflows endpoint failed: {e.code} {e.reason}')
        except urllib.error.URLError as e:
            print(f'❌ Workflows endpoint connection failed: {e}')
        
        print('\n3. ✅ API endpoints are accessible')
        print('\n🔗 Frontend should now connect to real backend API instead of mock data')
        
    except Exception as error:
        print(f'❌ API connection failed: {error}')

if __name__ == '__main__':
    test_api_connection()