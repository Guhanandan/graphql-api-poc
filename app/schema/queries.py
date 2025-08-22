import strawberry
from typing import List, Optional
from app.schema.types import Project, ProjectConnection, ProjectFilter, User, UserRole
from app.database.connection import (
    get_projects, 
    get_project_by_id, 
    get_users,
    get_user_by_id
)
from app.auth.permissions import IsAuthenticated
from strawberry.types import Info
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

@strawberry.type
class Query:
    @strawberry.field(permission_classes=[IsAuthenticated])
    async def projects(
        self,
        info: Info,
        first: Optional[int] = 10,
        after: Optional[str] = None,
        filter: Optional[ProjectFilter] = None
    ) -> ProjectConnection:
        """Get paginated list of projects with optional filtering"""
        # All authenticated users can see all projects
        return await get_projects(
            first=first,
            after=after,
            filter=filter
        )
    
    @strawberry.field(permission_classes=[IsAuthenticated])
    async def project(self, info: Info, id: str) -> Optional[Project]:
        """Get a single project by ID"""
        # All authenticated users can see all projects
        project = await get_project_by_id(id)
        
        if not project:
            return None
        
        return project
    
    @strawberry.field(permission_classes=[IsAuthenticated])
    async def users(self, info: Info) -> List[User]:
        """Get list of users"""
        # All authenticated users can see all users
        return await get_users()
    
    @strawberry.field(permission_classes=[IsAuthenticated])
    async def user(self, info: Info, id: str) -> Optional[User]:
        """Get a single user by ID"""
        # All authenticated users can see all users
        return await get_user_by_id(id)
    
    @strawberry.field(permission_classes=[IsAuthenticated])
    async def me(self, info: Info) -> User:
        """Get current user information"""
        current_user = info.context["current_user"]
        
        # Convert the auth user dict to User type
        user = User(
            id=current_user["id"],
            email=current_user["email"],
            full_name=current_user["full_name"],
            role=UserRole.VIEWER,  # Default role for all users
            is_active=current_user["is_active"]
        )
        
        return user