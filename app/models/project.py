from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class ProjectStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"

class ProjectPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

# Pydantic models for data validation
class ProjectBase(BaseModel):
    project_id: Optional[str] = Field(None, min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: ProjectStatus = ProjectStatus.ACTIVE
    priority: ProjectPriority = ProjectPriority.MEDIUM
    tags: List[str] = Field(default_factory=list)
    owner_id: str = Field(..., min_length=1)
    budget: Optional[float] = Field(None, ge=0)

class ProjectCreate(ProjectBase):
    project_id: str = Field(..., min_length=1, max_length=100)

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[ProjectStatus] = None
    priority: Optional[ProjectPriority] = None
    tags: Optional[List[str]] = None
    budget: Optional[float] = Field(None, ge=0)

class Project(ProjectBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True