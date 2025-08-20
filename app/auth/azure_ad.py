# import jwt
# from typing import Optional
# from fastapi import HTTPException, Request
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from azure.identity import DefaultAzureCredential
# from msal import ConfidentialClientApplication
# import httpx
# from decouple import config
# import logging

# logger = logging.getLogger(__name__)

# # Azure AD Configuration
# AZURE_CLIENT_ID = config('AZURE_CLIENT_ID')
# AZURE_CLIENT_SECRET = config('AZURE_CLIENT_SECRET', default='')
# AZURE_TENANT_ID = config('AZURE_TENANT_ID')
# AZURE_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"
# AZURE_SCOPE = ["https://graph.microsoft.com/.default"]

# # JWT Configuration
# JWT_ALGORITHM = "RS256"
# AZURE_JWKS_URL = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/discovery/v2.0/keys"

# class AzureADAuth:
#     def __init__(self):
#         self.app = ConfidentialClientApplication(
#             AZURE_CLIENT_ID,
#             authority=AZURE_AUTHORITY,
#             client_credential=AZURE_CLIENT_SECRET,
#         )
#         self.jwks_client = None
#         self._jwks_cache = None
    
#     async def get_jwks(self):
#         """Get JSON Web Key Set from Azure AD"""
#         if self._jwks_cache is None:
#             async with httpx.AsyncClient() as client:
#                 response = await client.get(AZURE_JWKS_URL)
#                 response.raise_for_status()
#                 self._jwks_cache = response.json()
#         return self._jwks_cache
    
#     async def get_signing_key(self, kid: str):
#         """Get signing key for JWT verification"""
#         jwks = await self.get_jwks()
        
#         for key in jwks["keys"]:
#             if key["kid"] == kid:
#                 return jwt.algorithms.RSAAlgorithm.from_jwk(key)
        
#         raise HTTPException(
#             status_code=401,
#             detail="Unable to find appropriate signing key"
#         )
    
#     async def verify_token(self, token: str) -> dict:
#         """Verify and decode JWT token from Azure AD"""
#         try:
#             # Decode header to get key ID
#             unverified_header = jwt.get_unverified_header(token)
#             kid = unverified_header["kid"]
            
#             # Get signing key
#             signing_key = await self.get_signing_key(kid)
            
#             # Verify and decode token
#             payload = jwt.decode(
#                 token,
#                 signing_key,
#                 algorithms=[JWT_ALGORITHM],
#                 audience=AZURE_CLIENT_ID,
#                 issuer=f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/v2.0"
#             )
            
#             return payload
            
#         except jwt.ExpiredSignatureError:
#             raise HTTPException(status_code=401, detail="Token expired")
#         except jwt.InvalidTokenError as e:
#             logger.error(f"Token validation error: {e}")
#             raise HTTPException(status_code=401, detail="Invalid token")
    
#     async def get_user_info(self, token: str) -> dict:
#         """Get user information from Microsoft Graph API"""
#         headers = {"Authorization": f"Bearer {token}"}
        
#         async with httpx.AsyncClient() as client:
#             response = await client.get(
#                 "https://graph.microsoft.com/v1.0/me",
#                 headers=headers
#             )
            
#             if response.status_code != 200:
#                 raise HTTPException(
#                     status_code=401,
#                     detail="Failed to get user information"
#                 )
            
#             return response.json()

# # Global auth instance
# azure_auth = AzureADAuth()
# security = HTTPBearer()

# async def get_current_user(request: Request) -> Optional[dict]:
#     """Extract and validate user from JWT token"""
#     try:
#         # Get token from Authorization header
#         authorization = request.headers.get("Authorization")
#         if not authorization or not authorization.startswith("Bearer "):
#             raise HTTPException(
#                 status_code=401,
#                 detail="Missing or invalid authorization header"
#             )
        
#         token = authorization.split(" ")[1]
        
#         # Verify token and get payload
#         payload = await azure_auth.verify_token(token)
        
#         # Extract user information from token
#         user_info = {
#             "id": payload.get("oid"),  # Object ID
#             "email": payload.get("preferred_username") or payload.get("email"),
#             "full_name": payload.get("name", ""),
#             "role": determine_user_role(payload),
#             "is_active": True,
#             "azure_payload": payload
#         }
        
#         return user_info
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Authentication error: {e}")
#         raise HTTPException(status_code=401, detail="Authentication failed")

# def determine_user_role(payload: dict) -> str:
#     """Determine user role based on Azure AD groups or claims"""
#     # Check for roles in the token
#     roles = payload.get("roles", [])
#     groups = payload.get("groups", [])
    
#     # Define your role mapping based on Azure AD groups/roles
#     # This is just an example - adjust based on your Azure AD setup
#     admin_groups = [config('AZURE_ADMIN_GROUP_ID', default='')]
#     manager_groups = [config('AZURE_MANAGER_GROUP_ID', default='')]
#     developer_groups = [config('AZURE_DEVELOPER_GROUP_ID', default='')]
    
#     if any(group in admin_groups for group in groups) or "Admin" in roles:
#         return "admin"
#     elif any(group in manager_groups for group in groups) or "Manager" in roles:
#         return "manager"
#     elif any(group in developer_groups for group in groups) or "Developer" in roles:
#         return "developer"
#     else:
#         return "viewer"

# # Alternative simple authentication for development/testing
# async def get_current_user_simple(request: Request) -> Optional[dict]:
#     """Simple authentication for development (not for production!)"""
#     authorization = request.headers.get("Authorization")
#     if not authorization or not authorization.startswith("Bearer "):
#         raise HTTPException(
#             status_code=401,
#             detail="Missing authorization header"
#         )
    
#     token = authorization.split(" ")[1]
    
#     # Simple token validation (for development only)
#     if token == "dev-token":
#         return {
#             "id": "dev-user-1",
#             "email": "developer@company.com",
#             "full_name": "Development User",
#             "role": "admin",
#             "is_active": True
#         }
    
#     raise HTTPException(status_code=401, detail="Invalid token")