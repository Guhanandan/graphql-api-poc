import strawberry
from strawberry.permission import BasePermission
from strawberry.types import Info
from app.auth.azure_ad import get_current_user
from typing import Any
import logging

logger = logging.getLogger(__name__)

class IsAuthenticated(BasePermission):
    message = "User is not authenticated"
    
    async def has_permission(self, source: Any, info: Info, **kwargs) -> bool:
        request = info.context["request"]
        try:
            user = await get_current_user(request)
            if user:
                # Log different info based on token type
                if user.get("token_type") == "client_credentials":
                    logger.info(f"Application authenticated: {user.get('app_id', 'Unknown')}")
                else:
                    logger.info(f"User authenticated: {user.get('email', 'Unknown')}")
                
                info.context["current_user"] = user
                return True
            else:
                logger.warning("No user returned from authentication")
                return False
                
        except Exception as e:
            logger.error(f"Authentication check failed: {str(e)}")
            # Log the full exception for debugging
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False