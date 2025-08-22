import strawberry
from typing import List, Optional
from datetime import datetime
from enum import Enum

@strawberry.enum
class ProjectStatus(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"

@strawberry.enum
class ProjectPriority(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@strawberry.enum
class UserRole(Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    DEVELOPER = "developer"
    VIEWER = "viewer"

@strawberry.type
class User:
    id: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

@strawberry.type
class Project:
    id: str
    project_id: str
    name: str
    description: Optional[str]
    status: ProjectStatus
    priority: ProjectPriority
    tags: List[str]
    owner_id: str
    budget: Optional[float]
    created_at: datetime
    updated_at: datetime
    
    @strawberry.field
    async def owner(self, info) -> Optional[User]:
        # This will be implemented with a data loader to avoid N+1 queries
        from app.database.connection import get_user_by_id
        return await get_user_by_id(self.owner_id)

@strawberry.input
class ProjectFilter:
    status: Optional[ProjectStatus] = None
    priority: Optional[ProjectPriority] = None
    owner_id: Optional[str] = None
    tags: Optional[List[str]] = None
    search: Optional[str] = None  # Search in name and description

@strawberry.input
class CreateProjectInput:
    project_id: str = strawberry.field(description="Unique project identifier")
    name: str = strawberry.field(description="Project name")
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    priority: ProjectPriority = ProjectPriority.MEDIUM
    tags: Optional[List[str]] = strawberry.field(default_factory=list)
    owner_id: str = strawberry.field(description="Project owner ID")
    budget: Optional[float] = None

@strawberry.input
class ProjectUpdateInput:
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    priority: Optional[ProjectPriority] = None
    tags: Optional[List[str]] = None
    budget: Optional[float] = None

@strawberry.type
class PaginationInfo:
    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[str]
    end_cursor: Optional[str]
    total_count: int

@strawberry.type
class ProjectEdge:
    node: Project
    cursor: str

@strawberry.type
class ProjectConnection:
    edges: List[ProjectEdge]
    page_info: PaginationInfo