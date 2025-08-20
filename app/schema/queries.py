import strawberry
from typing import List, Optional
from app.schema.types import Project, ProjectConnection, ProjectFilter, User
from app.database.connection import (
    get_projects, 
    get_project_by_id, 
    get_users,
    get_user_by_id
)
# from app.auth.azure_ad import get_current_user
from strawberry.permission import BasePermission
from strawberry.types import Info

# class IsAuthenticated(BasePermission):
#     message = "User is not authenticated"
    
#     async def has_permission(self, source, info: Info, **kwargs) -> bool:
#         request = info.context["request"]
#         try:
#             user = await get_current_user(request)
#             info.context["current_user"] = user
#             return user is not None
#         except:
#             return False

@strawberry.type
class Query:
    # @strawberry.field(permission_classes=[IsAuthenticated])
    @strawberry.field
    async def projects(
        self,
        info: Info,
        first: Optional[int] = 10,
        after: Optional[str] = None,
        filter: Optional[ProjectFilter] = None
    ) -> ProjectConnection:
        """Get paginated list of projects with optional filtering"""
        # current_user = info.context["current_user"]
        
        # # Apply role-based filtering
        # if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        #     # Non-admin users can only see their own projects
        #     if filter is None:
        #         filter = ProjectFilter(owner_id=current_user.id)
        #     else:
        #         filter.owner_id = current_user.id
        
        return await get_projects(
            first=first,
            after=after,
            filter=filter
        )
    
    # @strawberry.field(permission_classes=[IsAuthenticated])
    @strawberry.field
    async def project(self, info: Info, id: str) -> Optional[Project]:
        """Get a single project by ID"""
        # current_user = info.context["current_user"]
        project = await get_project_by_id(id)
        
        if not project:
            return None
        
        # # Check if user has permission to view this project
        # if (current_user.role not in [UserRole.ADMIN, UserRole.MANAGER] and 
        #     project.owner_id != current_user.id):
        #     return None
        
        return project
    
    # @strawberry.field(permission_classes=[IsAuthenticated])
    @strawberry.field
    async def users(self, info: Info) -> List[User]:
        """Get list of users (admin/manager only)"""
        # current_user = info.context["current_user"]
        
        # if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        #     raise Exception("Insufficient permissions")
        
        return await get_users()
    
    # @strawberry.field(permission_classes=[IsAuthenticated])
    # async def me(self, info: Info) -> User:
    #     """Get current user information"""
    #     return info.context["current_user"]