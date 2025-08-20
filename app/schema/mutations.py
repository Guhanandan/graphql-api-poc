import strawberry
from typing import Optional, List
from app.schema.types import Project, User, UserRole
from app.database.connection import create_project, update_project, delete_project
from app.models.project import ProjectCreate, ProjectUpdate
# from app.auth.azure_ad import get_current_user
# from strawberry.permission import BasePermission
from strawberry.types import Info

# Commented out for now - will use later
# class IsAuthenticated(BasePermission):
#     message = "User is not authenticated"
#     
#     async def has_permission(self, source, info: Info, **kwargs) -> bool:
#         request = info.context["request"]
#         try:
#             user = await get_current_user(request)
#             info.context["current_user"] = user
#             return user is not None
#         except:
#             return False

@strawberry.input
class CreateProjectInput:
    name: str
    description: Optional[str] = None
    status: Optional[str] = "active"
    priority: Optional[str] = "medium"
    tags: Optional[List[str]] = strawberry.field(default_factory=list)
    owner_id: str
    budget: Optional[float] = None

@strawberry.input
class UpdateProjectInput:
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[List[str]] = None
    budget: Optional[float] = None

@strawberry.type
class Mutation:
    # @strawberry.mutation(permission_classes=[IsAuthenticated])
    @strawberry.mutation
    async def create_project(
        self, 
        info: Info, 
        input: CreateProjectInput
    ) -> Project:
        """Create a new project"""
        # Authentication disabled for now
        # current_user = info.context["current_user"]
        
        # # Only allow creating projects for self unless admin/manager
        # if (current_user.role not in [UserRole.ADMIN, UserRole.MANAGER] and 
        #     input.owner_id != current_user.id):
        #     raise Exception("Cannot create projects for other users")
        
        # Convert input to ProjectCreate model
        project_data = ProjectCreate(
            name=input.name,
            description=input.description,
            status=input.status,
            priority=input.priority,
            tags=input.tags or [],
            owner_id=input.owner_id,
            budget=input.budget
        )
        
        return await create_project(project_data)
    
    # @strawberry.mutation(permission_classes=[IsAuthenticated])
    @strawberry.mutation
    async def update_project(
        self, 
        info: Info, 
        id: str, 
        input: UpdateProjectInput
    ) -> Optional[Project]:
        """Update an existing project"""
        # Authentication disabled for now
        # current_user = info.context["current_user"]
        
        # # Check if project exists and user has permission
        # project = await get_project_by_id(id)
        # if not project:
        #     return None
        
        # if (current_user.role not in [UserRole.ADMIN, UserRole.MANAGER] and 
        #     project.owner_id != current_user.id):
        #     raise Exception("Insufficient permissions to update this project")
        
        # Convert input to ProjectUpdate model
        project_data = ProjectUpdate(
            name=input.name,
            description=input.description,
            status=input.status,
            priority=input.priority,
            tags=input.tags,
            budget=input.budget
        )
        
        return await update_project(id, project_data)
    
    # @strawberry.mutation(permission_classes=[IsAuthenticated])
    @strawberry.mutation
    async def delete_project(self, info: Info, id: str) -> bool:
        """Delete a project"""
        # Authentication disabled for now
        # current_user = info.context["current_user"]
        
        # # Check if project exists and user has permission
        # project = await get_project_by_id(id)
        # if not project:
        #     return False
        
        # if (current_user.role not in [UserRole.ADMIN, UserRole.MANAGER] and 
        #     project.owner_id != current_user.id):
        #     raise Exception("Insufficient permissions to delete this project")
        
        return await delete_project(id)