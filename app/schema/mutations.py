import strawberry
from typing import Optional, List
from app.schema.types import Project, User, UserRole
from app.database.connection import create_project, update_project, delete_project, get_project_by_id
from app.models.project import ProjectCreate, ProjectUpdate
from app.schema.types import CreateProjectInput
from strawberry.types import Info


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
    @strawberry.mutation
    async def create_project(
        self, 
        info: Info, 
        input: CreateProjectInput
    ) -> Project:
        """Create a new project"""
        try:
            # Convert input to ProjectCreate model
            project_data = ProjectCreate(
                project_id=input.project_id,
                name=input.name,
                description=input.description,
                status=input.status or "ACTIVE",
                priority=input.priority or "MEDIUM",
                tags=input.tags or [],
                owner_id=input.owner_id,
                budget=input.budget
            )
            
            return await create_project(project_data)
        except Exception as e:
            raise Exception(f"Failed to create project: {str(e)}")
    
    @strawberry.mutation
    async def update_project(
        self, 
        info: Info, 
        id: str, 
        input: UpdateProjectInput
    ) -> Optional[Project]:
        """Update an existing project"""
        try:
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
        except Exception as e:
            raise Exception(f"Failed to update project: {str(e)}")
    
    @strawberry.mutation
    async def delete_project(self, info: Info, id: str) -> bool:
        """Delete a project"""
        try:
            return await delete_project(id)
        except Exception as e:
            raise Exception(f"Failed to delete project: {str(e)}")
    
    @strawberry.mutation
    async def seed_test_data(self, info: Info) -> str:
        """Seed test data for development"""
        try:
            from app.database.connection import seed_test_data
            await seed_test_data()
            return "Test data seeded successfully"
        except Exception as e:
            raise Exception(f"Failed to seed test data: {str(e)}")