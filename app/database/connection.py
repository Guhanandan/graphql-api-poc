import os
import uuid
import urllib3
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from decouple import config
import logging

from app.models.project import Project, ProjectCreate, ProjectUpdate
from app.models.user import User
from app.schema.types import ProjectConnection, ProjectEdge, PaginationInfo, ProjectFilter
from app.utils.pagination import encode_cursor, decode_cursor

urllib3.disable_warnings()

logger = logging.getLogger(__name__)

# Cosmos DB Configuration
COSMOS_URL = config('COSMOS_URL')
COSMOS_KEY = config('COSMOS_KEY') 
COSMOS_DATABASE_NAME = config('COSMOS_DATABASE_NAME', default='ProjectsDB')

class CosmosDBClient:
    def __init__(self):
        self.client = CosmosClient(
            url="https://127.0.0.1:8081/",
            credential="C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
            connection_verify=False
        )
        #self.client = CosmosClient(COSMOS_URL, credential=COSMOS_KEY, connection_verify=False)
        self.database = None
        self.projects_container = None
        self.users_container = None
    
    async def initialize(self):
        """Initialize database and containers"""
        try:
            # Create database if it doesn't exist
            self.database = self.client.create_database_if_not_exists(
                id=COSMOS_DATABASE_NAME
            )
            
            # Create containers if they don't exist
            self.projects_container = self.database.create_container_if_not_exists(
                id="projects",
                partition_key=PartitionKey(path="/owner_id"),
                offer_throughput=400
            )
            
            self.users_container = self.database.create_container_if_not_exists(
                id="users",
                partition_key=PartitionKey(path="/id"),
                offer_throughput=400
            )
            
            logger.info("Cosmos DB initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB: {e}")
            raise

# Global database instance
db_client = CosmosDBClient()

dbs = list(db_client.client.list_databases())
print("Databases:", dbs)

# async def init_database():
#     """Initialize database connection"""
#     await db_client.initialize()

# def build_filter_query(filter: Optional[ProjectFilter]) -> tuple[str, Dict[str, Any]]:
#     """Build SQL query and parameters from filter"""
#     where_clauses = []
#     parameters = {}
    
#     if not filter:
#         return "", {}
    
#     if filter.status:
#         where_clauses.append("c.status = @status")
#         parameters["@status"] = filter.status.value
    
#     if filter.priority:
#         where_clauses.append("c.priority = @priority") 
#         parameters["@priority"] = filter.priority.value
    
#     if filter.owner_id:
#         where_clauses.append("c.owner_id = @owner_id")
#         parameters["@owner_id"] = filter.owner_id
    
#     if filter.tags:
#         # Check if project has any of the specified tags
#         tag_conditions = []
#         for i, tag in enumerate(filter.tags):
#             param_name = f"@tag{i}"
#             tag_conditions.append(f"ARRAY_CONTAINS(c.tags, {param_name})")
#             parameters[param_name] = tag
        
#         if tag_conditions:
#             where_clauses.append(f"({' OR '.join(tag_conditions)})")
    
#     if filter.search:
#         where_clauses.append(
#             "(CONTAINS(LOWER(c.name), LOWER(@search)) OR CONTAINS(LOWER(c.description), LOWER(@search)))"
#         )
#         parameters["@search"] = filter.search
    
#     where_clause = " AND ".join(where_clauses) if where_clauses else ""
#     return where_clause, parameters

# # Project CRUD Operations
# async def get_projects(
#     first: int = 10, 
#     after: Optional[str] = None,
#     filter: Optional[ProjectFilter] = None
# ) -> ProjectConnection:
#     """Get paginated projects with filtering"""
#     try:
#         # Build filter query
#         where_clause, parameters = build_filter_query(filter)
        
#         # Base query
#         base_query = "SELECT * FROM c"
#         if where_clause:
#             base_query += f" WHERE {where_clause}"
        
#         # Add ordering
#         base_query += " ORDER BY c.created_at DESC"
        
#         # Handle pagination cursor
#         skip = 0
#         if after:
#             skip = decode_cursor(after)
        
#         # Get total count for pagination info
#         count_query = "SELECT VALUE COUNT(1) FROM c"
#         if where_clause:
#             count_query += f" WHERE {where_clause}"
        
#         count_items = list(db_client.projects_container.query_items(
#             query=count_query,
#             parameters=parameters,
#             enable_cross_partition_query=True
#         ))
#         total_count = count_items[0] if count_items else 0
        
#         # Get items with pagination
#         query = f"{base_query} OFFSET {skip} LIMIT {first + 1}"
        
#         items = list(db_client.projects_container.query_items(
#             query=query,
#             parameters=parameters,
#             enable_cross_partition_query=True
#         ))
        
#         # Check if there are more items
#         has_next_page = len(items) > first
#         if has_next_page:
#             items = items[:-1]  # Remove the extra item
        
#         # Convert to Project objects and create edges
#         edges = []
#         for i, item in enumerate(items):
#             project = Project(**item)
#             cursor = encode_cursor(skip + i)
#             edges.append(ProjectEdge(node=project, cursor=cursor))
        
#         # Create pagination info
#         page_info = PaginationInfo(
#             has_next_page=has_next_page,
#             has_previous_page=skip > 0,
#             start_cursor=edges[0].cursor if edges else None,
#             end_cursor=edges[-1].cursor if edges else None,
#             total_count=total_count
#         )
        
#         return ProjectConnection(edges=edges, page_info=page_info)
        
#     except Exception as e:
#         logger.error(f"Error getting projects: {e}")
#         raise

# async def get_project_by_id(project_id: str) -> Optional[Project]:
#     """Get project by ID"""
#     try:
#         query = "SELECT * FROM c WHERE c.id = @id"
#         parameters = {"@id": project_id}
        
#         items = list(db_client.projects_container.query_items(
#             query=query,
#             parameters=parameters,
#             enable_cross_partition_query=True
#         ))
        
#         if items:
#             return Project(**items[0])
#         return None
        
#     except Exception as e:
#         logger.error(f"Error getting project {project_id}: {e}")
#         return None

# async def create_project(project_data: ProjectCreate) -> Project:
#     """Create a new project"""
#     try:
#         project_dict = project_data.model_dump()
#         project_dict.update({
#             "id": str(uuid.uuid4()),
#             "created_at": datetime.now(timezone.utc),
#             "updated_at": datetime.now(timezone.utc)
#         })
        
#         # Create in Cosmos DB
#         created_item = db_client.projects_container.create_item(body=project_dict)
        
#         return Project(**created_item)
        
#     except Exception as e:
#         logger.error(f"Error creating project: {e}")
#         raise

# async def update_project(project_id: str, project_data: ProjectUpdate) -> Optional[Project]:
#     """Update an existing project"""
#     try:
#         # First get the existing project
#         existing = await get_project_by_id(project_id)
#         if not existing:
#             return None
        
#         # Update only provided fields
#         update_data = project_data.model_dump(exclude_unset=True)
#         update_data["updated_at"] = datetime.now(timezone.utc)
        
#         # Get current item from database
#         current_item = db_client.projects_container.read_item(
#             item=project_id, 
#             partition_key=existing.owner_id
#         )
        
#         # Merge updates
#         current_item.update(update_data)
        
#         # Update in Cosmos DB
#         updated_item = db_client.projects_container.replace_item(
#             item=project_id,
#             body=current_item
#         )
        
#         return Project(**updated_item)
        
#     except CosmosResourceNotFoundError:
#         return None
#     except Exception as e:
#         logger.error(f"Error updating project {project_id}: {e}")
#         raise

# async def delete_project(project_id: str) -> bool:
#     """Delete a project"""
#     try:
#         # Get project to get partition key
#         existing = await get_project_by_id(project_id)
#         if not existing:
#             return False
        
#         # Delete from Cosmos DB
#         db_client.projects_container.delete_item(
#             item=project_id,
#             partition_key=existing.owner_id
#         )
        
#         return True
        
#     except CosmosResourceNotFoundError:
#         return False
#     except Exception as e:
#         logger.error(f"Error deleting project {project_id}: {e}")
#         return False

# # User operations (simplified for this PoC)
# async def get_users() -> List[User]:
#     """Get all users"""
#     try:
#         query = "SELECT * FROM c ORDER BY c.created_at DESC"
        
#         items = list(db_client.users_container.query_items(
#             query=query,
#             enable_cross_partition_query=True
#         ))
        
#         return [User(**item) for item in items]
        
#     except Exception as e:
#         logger.error(f"Error getting users: {e}")
#         return []

# async def get_user_by_id(user_id: str) -> Optional[User]:
#     """Get user by ID"""
#     try:
#         query = "SELECT * FROM c WHERE c.id = @id"
#         parameters = {"@id": user_id}
        
#         items = list(db_client.users_container.query_items(
#             query=query,
#             parameters=parameters,
#             enable_cross_partition_query=True
#         ))
        
#         if items:
#             return User(**items[0])
#         return None
        
#     except Exception as e:
#         logger.error(f"Error getting user {user_id}: {e}")
#         return None

# async def create_user_if_not_exists(user_data: dict) -> User:
#     """Create user if doesn't exist (for Azure AD integration)"""
#     try:
#         # Check if user exists
#         existing = await get_user_by_id(user_data["id"])
#         if existing:
#             return existing
        
#         # Create new user
#         user_dict = {
#             "id": user_data["id"],
#             "email": user_data["email"],
#             "full_name": user_data["full_name"],
#             "role": user_data["role"],
#             "is_active": True,
#             "created_at": datetime.now(timezone.utc),
#             "updated_at": datetime.now(timezone.utc)
#         }
        
#         created_item = db_client.users_container.create_item(body=user_dict)
#         return User(**created_item)
        
#     except Exception as e:
#         logger.error(f"Error creating user: {e}")
#         raise

async def init_database():
    """Initialize database connection"""
    await db_client.initialize()
    
    # Log available databases if in debug mode
    if config('DEBUG', default=False, cast=bool):
        try:
            dbs = list(db_client.client.list_databases())
            logger.debug(f"Available databases: {[db['id'] for db in dbs]}")
        except Exception as e:
            logger.debug(f"Could not list databases: {e}")

def build_filter_query(filter: Optional[ProjectFilter]) -> tuple[str, Dict[str, Any]]:
    """Build SQL query and parameters from filter"""
    where_clauses = []
    parameters = {}
    
    if not filter:
        return "", {}
    
    if filter.status:
        where_clauses.append("c.status = @status")
        parameters["@status"] = filter.status.value
    
    if filter.priority:
        where_clauses.append("c.priority = @priority") 
        parameters["@priority"] = filter.priority.value
    
    if filter.owner_id:
        where_clauses.append("c.owner_id = @owner_id")
        parameters["@owner_id"] = filter.owner_id
    
    if filter.tags:
        # Check if project has any of the specified tags
        tag_conditions = []
        for i, tag in enumerate(filter.tags):
            param_name = f"@tag{i}"
            tag_conditions.append(f"ARRAY_CONTAINS(c.tags, {param_name})")
            parameters[param_name] = tag
        
        if tag_conditions:
            where_clauses.append(f"({' OR '.join(tag_conditions)})")
    
    if filter.search:
        where_clauses.append(
            "(CONTAINS(LOWER(c.name), LOWER(@search)) OR CONTAINS(LOWER(c.description), LOWER(@search)))"
        )
        parameters["@search"] = filter.search
    
    where_clause = " AND ".join(where_clauses) if where_clauses else ""
    return where_clause, parameters

# Project CRUD Operations
async def get_projects(
    first: int = 10, 
    after: Optional[str] = None,
    filter: Optional[ProjectFilter] = None
) -> ProjectConnection:
    """Get paginated projects with filtering"""
    try:
        # Build filter query
        where_clause, parameters = build_filter_query(filter)
        
        # Base query
        base_query = "SELECT * FROM c"
        if where_clause:
            base_query += f" WHERE {where_clause}"
        
        # Add ordering
        base_query += " ORDER BY c.created_at DESC"
        
        # Handle pagination cursor
        skip = 0
        if after:
            skip = decode_cursor(after)
        
        # Get total count for pagination info
        count_query = "SELECT VALUE COUNT(1) FROM c"
        if where_clause:
            count_query += f" WHERE {where_clause}"
        
        count_items = list(db_client.projects_container.query_items(
            query=count_query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        total_count = count_items[0] if count_items else 0
        
        # Get items with pagination
        query = f"{base_query} OFFSET {skip} LIMIT {first + 1}"
        
        items = list(db_client.projects_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        # Check if there are more items
        has_next_page = len(items) > first
        if has_next_page:
            items = items[:-1]  # Remove the extra item
        
        # Convert to Project objects and create edges
        edges = []
        for i, item in enumerate(items):
            # Convert datetime strings to datetime objects if needed
            if isinstance(item.get('created_at'), str):
                item['created_at'] = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
            if isinstance(item.get('updated_at'), str):
                item['updated_at'] = datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
            
            project = Project(**item)
            cursor = encode_cursor(skip + i)
            edges.append(ProjectEdge(node=project, cursor=cursor))
        
        # Create pagination info
        page_info = PaginationInfo(
            has_next_page=has_next_page,
            has_previous_page=skip > 0,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
            total_count=total_count
        )
        
        return ProjectConnection(edges=edges, page_info=page_info)
        
    except Exception as e:
        logger.error(f"Error getting projects: {e}")
        raise

async def get_project_by_id(project_id: str) -> Optional[Project]:
    """Get project by ID"""
    try:
        query = "SELECT * FROM c WHERE c.id = @id"
        parameters = {"@id": project_id}
        
        items = list(db_client.projects_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if items:
            item = items[0]
            # Convert datetime strings to datetime objects if needed
            if isinstance(item.get('created_at'), str):
                item['created_at'] = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
            if isinstance(item.get('updated_at'), str):
                item['updated_at'] = datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
            
            return Project(**item)
        return None
        
    except Exception as e:
        logger.error(f"Error getting project {project_id}: {e}")
        return None

async def create_project(project_data: ProjectCreate) -> Project:
    """Create a new project"""
    try:
        project_dict = project_data.model_dump()
        project_dict.update({
            "id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Create in Cosmos DB
        created_item = db_client.projects_container.create_item(body=project_dict)
        
        # Convert back to datetime objects
        created_item['created_at'] = datetime.fromisoformat(created_item['created_at'].replace('Z', '+00:00'))
        created_item['updated_at'] = datetime.fromisoformat(created_item['updated_at'].replace('Z', '+00:00'))
        
        # Convert string status and priority to enums for the GraphQL type
        from app.schema.types import ProjectStatus, ProjectPriority
        created_item['status'] = ProjectStatus(created_item['status'])
        created_item['priority'] = ProjectPriority(created_item['priority'])
        
        return Project(**created_item)
        
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise

async def update_project(project_id: str, project_data: ProjectUpdate) -> Optional[Project]:
    """Update an existing project"""
    try:
        # First get the existing project
        existing = await get_project_by_id(project_id)
        if not existing:
            return None
        
        # Update only provided fields
        update_data = project_data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Get current item from database
        current_item = db_client.projects_container.read_item(
            item=project_id, 
            partition_key=existing.owner_id
        )
        
        # Merge updates
        current_item.update(update_data)
        
        # Update in Cosmos DB
        updated_item = db_client.projects_container.replace_item(
            item=project_id,
            body=current_item
        )
        
        # Convert datetime strings back to objects
        if isinstance(updated_item.get('created_at'), str):
            updated_item['created_at'] = datetime.fromisoformat(updated_item['created_at'].replace('Z', '+00:00'))
        if isinstance(updated_item.get('updated_at'), str):
            updated_item['updated_at'] = datetime.fromisoformat(updated_item['updated_at'].replace('Z', '+00:00'))
        
        return Project(**updated_item)
        
    except CosmosResourceNotFoundError:
        return None
    except Exception as e:
        logger.error(f"Error updating project {project_id}: {e}")
        raise

async def delete_project(project_id: str) -> bool:
    """Delete a project"""
    try:
        # Get project to get partition key
        existing = await get_project_by_id(project_id)
        if not existing:
            return False
        
        # Delete from Cosmos DB
        db_client.projects_container.delete_item(
            item=project_id,
            partition_key=existing.owner_id
        )
        
        return True
        
    except CosmosResourceNotFoundError:
                return False
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {e}")
        return False

# User operations (simplified for this PoC)
async def get_users() -> List[User]:
    """Get all users"""
    try:
        query = "SELECT * FROM c ORDER BY c.created_at DESC"
        
        items = list(db_client.users_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        users = []
        for item in items:
            # Convert datetime strings to datetime objects if needed
            if isinstance(item.get('created_at'), str):
                item['created_at'] = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
            if isinstance(item.get('updated_at'), str):
                item['updated_at'] = datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
            
            users.append(User(**item))
        
        return users
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return []

async def get_user_by_id(user_id: str) -> Optional[User]:
    """Get user by ID"""
    try:
        query = "SELECT * FROM c WHERE c.id = @id"
        parameters = {"@id": user_id}
        
        items = list(db_client.users_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if items:
            item = items[0]
            # Convert datetime strings to datetime objects if needed
            if isinstance(item.get('created_at'), str):
                item['created_at'] = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
            if isinstance(item.get('updated_at'), str):
                item['updated_at'] = datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
            
            return User(**item)
        return None
        
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        return None

async def create_user_if_not_exists(user_data: dict) -> User:
    """Create user if doesn't exist (for Azure AD integration)"""
    try:
        # Check if user exists
        existing = await get_user_by_id(user_data["id"])
        if existing:
            return existing
        
        # Create new user
        user_dict = {
            "id": user_data["id"],
            "email": user_data["email"],
            "full_name": user_data["full_name"],
            "role": user_data.get("role", "viewer"),
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        created_item = db_client.users_container.create_item(body=user_dict)
        
        # Convert datetime strings back to objects
        created_item['created_at'] = datetime.fromisoformat(created_item['created_at'].replace('Z', '+00:00'))
        created_item['updated_at'] = datetime.fromisoformat(created_item['updated_at'].replace('Z', '+00:00'))
        
        return User(**created_item)
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise

# Utility functions for testing
async def seed_test_data():
    """Seed additional test data if needed"""
    try:
        # Check if we need more test data
        projects_count = list(db_client.projects_container.query_items(
            query="SELECT VALUE COUNT(1) FROM c",
            enable_cross_partition_query=True
        ))[0]
        
        if projects_count < 10:
            logger.info("Seeding additional test data...")
            
            # Create more test projects
            test_projects = [
                {
                    "name": "Mobile App Development",
                    "description": "Cross-platform mobile application",
                    "status": "active",
                    "priority": "high",
                    "tags": ["mobile", "react-native", "app"],
                    "budget": 35000.0
                },
                {
                    "name": "Data Analytics Platform",
                    "description": "Real-time data processing and visualization",
                    "status": "active",
                    "priority": "critical",
                    "tags": ["data", "analytics", "bi"],
                    "budget": 75000.0
                },
                {
                    "name": "Security Audit",
                    "description": "Comprehensive security assessment",
                    "status": "completed",
                    "priority": "high",
                    "tags": ["security", "audit", "compliance"],
                    "budget": 20000.0
                },
                {
                    "name": "Cloud Migration",
                    "description": "Migrate on-premise infrastructure to Azure",
                    "status": "inactive",
                    "priority": "medium",
                    "tags": ["cloud", "migration", "azure"],
                    "budget": 50000.0
                },
                {
                    "name": "AI/ML Integration",
                    "description": "Integrate machine learning models",
                    "status": "active",
                    "priority": "medium",
                    "tags": ["ai", "ml", "integration"],
                    "budget": 40000.0
                }
            ]
            
            for project_data in test_projects:
                project = ProjectCreate(
                    name=project_data["name"],
                    description=project_data["description"],
                    status=project_data["status"],
                    priority=project_data["priority"],
                    tags=project_data["tags"],
                    owner_id="test-user-123",
                    budget=project_data["budget"]
                )
                await create_project(project)
            
            logger.info(f"Created {len(test_projects)} additional test projects")
            
    except Exception as e:
        logger.warning(f"Could not seed test data: {e}")

# Health check function
async def check_database_health() -> dict:
    """Check database connectivity and health"""
    try:
        # Try to query the database
        databases = list(db_client.client.list_databases())
        
        # Check containers
        containers_exist = (
            db_client.projects_container is not None and 
            db_client.users_container is not None
        )
        
        # Count items
        projects_count = 0
        users_count = 0
        
        if containers_exist:
            projects_count = list(db_client.projects_container.query_items(
                query="SELECT VALUE COUNT(1) FROM c",
                enable_cross_partition_query=True
            ))[0]
            
            users_count = list(db_client.users_container.query_items(
                query="SELECT VALUE COUNT(1) FROM c",
                enable_cross_partition_query=True
            ))[0]
        
        return {
            "status": "healthy",
            "database_connected": True,
            "containers_ready": containers_exist,
            "projects_count": projects_count,
            "users_count": users_count,
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "database_connected": False,
            "error": str(e),
        }