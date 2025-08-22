import asyncio
import httpx
import json
import jwt
from decouple import config

async def debug_authentication():
    """Debug authentication step by step"""
    
    print("🔍 Debugging Azure AD Authentication...")
    print("=" * 50)
    
    # Your configuration
    tenant_id = config('AZURE_TENANT_ID')
    api_client_id = config('AZURE_CLIENT_ID')
    api_client_secret = config('AZURE_CLIENT_SECRET')
    audience = config('AZURE_AUDIENCE', default=f"api://{api_client_id}")
    
    print(f"Tenant ID: {tenant_id}")
    print(f"API Client ID: {api_client_id}")
    print(f"Expected Audience: {audience}")
    print()
    
    # Step 1: Get access token
    async def get_and_analyze_token():
        """Get service-to-service token and analyze it"""
        url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        
        data = {
            "grant_type": "client_credentials",
            "client_id": api_client_id,
            "client_secret": api_client_secret,
            "scope": f"{audience}/.default"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, data=data, timeout=10.0)
                response.raise_for_status()
                token_data = response.json()
                
                access_token = token_data["access_token"]
                print(access_token)
                print("✅ Successfully obtained access token from Azure AD")
                
                # Decode and analyze the token
                print("\n📋 Token Analysis:")
                print("-" * 30)
                
                # Decode without verification to see contents
                payload = jwt.decode(access_token, options={"verify_signature": False})
                
                print(f"Token Type: {payload.get('typ', 'Unknown')}")
                print(f"Algorithm: {payload.get('alg', 'Unknown')}")
                print(f"Issuer: {payload.get('iss', 'Unknown')}")
                print(f"Audience: {payload.get('aud', 'Unknown')}")
                print(f"App ID: {payload.get('appid', 'Unknown')}")
                print(f"Object ID: {payload.get('oid', 'Unknown')}")
                print(f"Subject: {payload.get('sub', 'Unknown')}")
                print(f"Tenant ID: {payload.get('tid', 'Unknown')}")
                print(f"App ID ACR: {payload.get('appidacr', 'Unknown')}")
                
                # Check expiration
                import datetime
                exp = payload.get('exp')
                if exp:
                    exp_time = datetime.datetime.fromtimestamp(exp)
                    print(f"Expires at: {exp_time}")
                    print(f"Time until expiry: {exp_time - datetime.datetime.now()}")
                
                print(f"\n📄 Full Token Payload:")
                print(json.dumps(payload, indent=2))
                
                return access_token, payload
                
            except httpx.HTTPStatusError as e:
                print(f"❌ HTTP Error getting token: {e.response.status_code}")
                print(f"Response: {e.response.text}")
                return None, None
            except Exception as e:
                print(f"❌ Error getting token: {e}")
                return None, None
    
    # Step 2: Test token verification manually
    async def test_token_verification(token, payload):
        """Test manual token verification"""
        print(f"\n🔐 Testing Token Verification:")
        print("-" * 40)
        
        try:
            # Import your auth module
            from app.auth.azure_ad import azure_auth
            
            # Test token verification
            verified_payload = await azure_auth.verify_token(token)
            print("✅ Token verification successful!")
            print(f"Verified payload keys: {list(verified_payload.keys())}")
            
            return verified_payload
            
        except Exception as e:
            print(f"❌ Token verification failed: {e}")
            print(f"Error type: {type(e)}")
            return None
    
    # Step 3: Test user extraction
    async def test_user_extraction(token):
        """Test user extraction from token"""
        print(f"\n👤 Testing User Extraction:")
        print("-" * 35)
        
        try:
            # Create a mock request object
            class MockRequest:
                def __init__(self, token):
                    self.headers = {"Authorization": f"Bearer {token}"}
            
            mock_request = MockRequest(token)
            
            from app.auth.azure_ad import get_current_user
            user = await get_current_user(mock_request)
            
            if user:
                print("✅ User extraction successful!")
                print(f"User info: {json.dumps(user, indent=2)}")
                return user
            else:
                print("❌ User extraction returned None")
                return None
                
        except Exception as e:
            print(f"❌ User extraction failed: {e}")
            print(f"Error type: {type(e)}")
            return None
    
    # Step 4: Test API endpoint
    async def test_api_endpoint(token):
        """Test your GraphQL API with the token"""
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Simple health check first
        try:
            async with httpx.AsyncClient() as client:
                health_response = await client.get("http://localhost:8000/health")
                print(f"✅ API Health Check: {health_response.status_code}")
        except Exception as e:
            print(f"❌ API not accessible: {e}")
            return False
        
        # Test GraphQL with authentication
        graphql_query = {
            "query": """
                query GetProject {
                    project(id: "WEB-2024-001") {
                        id
                        projectId
                        name
                        description
                        status
                        priority
                        tags
                        budget
                        ownerId
                        createdAt
                        updatedAt
                        owner {
                            id
                            email
                            fullName
                            role
                        }
                    }
                }
            """
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/graphql",
                    json=graphql_query,
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "errors" in result:
                        print(f"❌ GraphQL Errors: {result['errors']}")
                        return False
                    else:
                        print("✅ GraphQL authentication successful!")
                        print(f"User info: {json.dumps(result['data'], indent=2)}")
                        return True
                else:
                    print(f"❌ GraphQL request failed: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ GraphQL request error: {e}")
            return False
    
    # Run all tests
    token, payload = await get_and_analyze_token()
    if token:
        verified_payload = await test_token_verification(token, payload)
        user = await test_user_extraction(token)
        api_success = await test_api_endpoint(token)
        
        print(f"\n📊 Summary:")
        print("=" * 20)
        print(f"Token obtained: ✅")
        print(f"Token verified: {'✅' if verified_payload else '❌'}")
        print(f"User extracted: {'✅' if user else '❌'}")
        print(f"API endpoint: {'✅' if api_success else '❌'}")
        
        if not api_success:
            print(f"\n💡 Debugging Tips:")
            print("1. Check that your FastAPI server is running on port 8000")
            print("2. Verify your get_current_user function is correctly implemented")
            print("3. Check the server logs for detailed error messages")
            print("4. Ensure the /test-auth endpoint is properly configured")
    else:
        print(f"\n❌ Could not obtain access token. Check your Azure AD configuration.")

if __name__ == "__main__":
    asyncio.run(debug_authentication())