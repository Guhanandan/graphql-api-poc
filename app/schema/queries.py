import strawberry
from typing import List, Optional
from app.schema.types import Project, ProjectConnection, ProjectFilter, User, UserRole
from app.database.connection import (
    get_projects, 
    get_project_by_id, 
    get_users,
    get_user_by_id
)
from strawberry.types import Info

@strawberry.type
class Query:
    @strawberry.field
    async def projects(
        self,
        info: Info,
        first: Optional[int] = 10,
        after: Optional[str] = None,
        filter: Optional[ProjectFilter] = None
    ) -> ProjectConnection:
        """Get paginated list of projects with optional filtering"""
        
        return await get_projects(
            first=first,
            after=after,
            filter=filter
        )
    
    @strawberry.field
    async def project(self, info: Info, id: str) -> Optional[Project]:
        """Get a single project by ID"""
        project = await get_project_by_id(id)
        
        if not project:
            return None  
        return project
    
    @strawberry.field
    async def users(self, info: Info) -> List[User]:
        """Get list of users"""
        return await get_users()
    
    @strawberry.field
    async def user(self, info: Info, id: str) -> Optional[User]:
        """Get a single user by ID"""
        return await get_user_by_id(id)
    