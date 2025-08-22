import jwt
import httpx
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer
from decouple import config
from datetime import datetime, timezone
import asyncio
from functools import lru_cache

logger = logging.getLogger(__name__)

AZURE_CLIENT_ID = config('AZURE_CLIENT_ID')
AZURE_TENANT_ID = config('AZURE_TENANT_ID')
AZURE_AUDIENCE = config('AZURE_AUDIENCE')
AZURE_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"
AZURE_JWKS_URL = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/discovery/v2.0/keys"
JWT_ALGORITHM = "RS256"

class AzureADAuth:
    def __init__(self):
        self._jwks_cache = None
        self._cache_expiry = None
        self._cache_lock = asyncio.Lock()
    
    async def get_jwks(self) -> Dict[str, Any]:
        """Get JSON Web Key Set from Azure AD with caching"""
        async with self._cache_lock:
            now = datetime.now(timezone.utc)
            
            # Check if cache is valid (refresh every hour)
            if (self._jwks_cache is None or 
                self._cache_expiry is None or 
                now > self._cache_expiry):
                
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(AZURE_JWKS_URL, timeout=10.0)
                        response.raise_for_status()
                        self._jwks_cache = response.json()
                        # Cache for 1 hour
                        from datetime import timedelta
                        self._cache_expiry = now + timedelta(hours=1)
                        logger.info("JWKS cache refreshed")
                        
                except Exception as e:
                    logger.error(f"Failed to fetch JWKS: {e}")
                    if self._jwks_cache is None:
                        raise HTTPException(
                            status_code=503,
                            detail="Unable to fetch authentication keys"
                        )
            
            return self._jwks_cache
    
    async def get_signing_key(self, kid: str):
        """Get signing key for JWT verification"""
        jwks = await self.get_jwks()
        
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return jwt.algorithms.RSAAlgorithm.from_jwk(key)
        
        raise HTTPException(
            status_code=401,
            detail="Unable to find appropriate signing key"
        )
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token from Azure AD"""
        try:
            # Decode header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            logger.info(f"Token kid: {kid}")
            
            if not kid:
                raise HTTPException(
                    status_code=401,
                    detail="Token missing key ID"
                )
            
            signing_key = await self.get_signing_key(kid)
            logger.info(f"Signing key obtained successfully")
            
            # Accept both formats for audience
            valid_audiences = [AZURE_AUDIENCE] if AZURE_AUDIENCE else [
                AZURE_CLIENT_ID,
                f"api://{AZURE_CLIENT_ID}"
            ]
            
            logger.info(f"Valid audiences: {valid_audiences}")
            
            # Verify and decode token
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=[JWT_ALGORITHM],
                audience=valid_audiences,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True,
                    "require": ["exp", "iat", "aud", "iss"]
                }
            )
            
            logger.info(f"Token decoded successfully")
            return payload
        
        except jwt.ExpiredSignatureError as e:
            logger.error(f"Token expired: {e}")
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidAudienceError as e:
            logger.error(f"Invalid audience: {e}")
            raise HTTPException(status_code=401, detail="Invalid token audience")
        except jwt.InvalidIssuerError as e:
            logger.error(f"Invalid issuer: {e}")
            raise HTTPException(status_code=401, detail="Invalid token issuer")
        except jwt.InvalidTokenError as e:
            logger.error(f"Token validation error: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            logger.error(f"Unexpected authentication error: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=401, detail="Authentication failed")

azure_auth = AzureADAuth()
security = HTTPBearer()

async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Extract and verify the current user from the request"""
    try:
        # Extract token from Authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            logger.warning("No Authorization header found")
            raise HTTPException(
                status_code=401,
                detail="Authorization header missing"
            )
        
        if not authorization.startswith("Bearer "):
            logger.warning("Invalid Authorization header format")
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization header format"
            )
        
        token = authorization.split(" ")[1]
        
        payload = await azure_auth.verify_token(token)
        logger.info(f"Token verified successfully for app: {payload.get('appid')}")
        
        user_info = {
            "id": payload.get("oid") or payload.get("sub"),  
            "email": payload.get("upn") or payload.get("unique_name") or f"app-{payload.get('appid')}@tenant",
            "full_name": payload.get("name") or f"Application {payload.get('appid')}",
            "tenant_id": payload.get("tid"),
            "app_id": payload.get("appid"),
            "is_active": True,
            "roles": payload.get("roles", []),
            "scopes": payload.get("scp", "").split(" ") if payload.get("scp") else [],
            "token_type": "client_credentials" if payload.get("appidacr") == "1" else "user"
        }
        
        logger.info(f"User info extracted: {user_info}")
        return user_info
        
    except HTTPException:
        
        raise
    except Exception as e:
        logger.error(f"Error extracting user from request: {e}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed"
        )

async def get_current_user_dependency(request: Request) -> Dict[str, Any]:
    """FastAPI dependency for getting current user"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not authenticated"
        )
    return user