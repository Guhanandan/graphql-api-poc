# test_graphql_api.py

import pytest
import httpx
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import json


class GraphQLTestClient:
    """Helper class for making GraphQL requests"""
    
    def __init__(self, base_url: str = "http://localhost:8000", auth_token: Optional[str] = None):
        self.base_url = base_url
        self.graphql_endpoint = f"{base_url}/graphql"
        self.auth_token = auth_token
        
    def get_headers(self) -> Dict[str, str]:
        """Get headers with authentication if token is provided"""
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers
    
    async def execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL query or mutation"""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.graphql_endpoint,
                json=payload,
                headers=self.get_headers(),
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()


@pytest.fixture
async def graphql_client():
    """Fixture to provide GraphQL client with authentication"""
    # You can modify this to get auth token from your authentication system
    auth_token = "your-auth-token-here"  # Replace with actual token
    return GraphQLTestClient(auth_token=auth_token)


@pytest.fixture
async def seed_data(graphql_client):
    """Fixture to seed test data before running tests"""
    mutation = """
        mutation SeedTestData {
            seedTestData
        }
    """
    result = await graphql_client.execute_query(mutation)
    assert "errors" not in result
    return result


class TestGraphQLAPI:
    """Test suite for GraphQL API"""
    
    @pytest.mark.asyncio
    async def test_seed_test_data(self, graphql_client):
        """Test 1: Seed test data"""
        mutation = """
            mutation SeedTestData {
                seedTestData
            }
        """
        result = await graphql_client.execute_query(mutation)
        assert "errors" not in result
        assert result["data"]["seedTestData"] is not None
    
    @pytest.mark.asyncio
    async def test_get_all_projects_with_pagination(self, graphql_client, seed_data):
        """Test 2: Get all projects with pagination"""
        query = """
            query GetProjects {
                projects(first: 10) {
                    edges {
                        node {
                            id
                            projectId
                            name
                            description
                            status
                            priority
                            tags
                            budget
                            ownerId
                            createdAt
                            updatedAt
                        }
                        cursor
                    }
                    pageInfo {
                        hasNextPage
                        hasPreviousPage
                        startCursor
                        endCursor
                        totalCount
                    }
                }
            }
        """
        result = await graphql_client.execute_query(query)
        assert "errors" not in result
        assert "projects" in result["data"]
        assert "edges" in result["data"]["projects"]
        assert "pageInfo" in result["data"]["projects"]
        
        # Validate pagination info
        page_info = result["data"]["projects"]["pageInfo"]
        assert isinstance(page_info["totalCount"], int)
        assert isinstance(page_info["hasNextPage"], bool)
        assert isinstance(page_info["hasPreviousPage"], bool)
    
    @pytest.mark.asyncio
    async def test_get_filtered_projects(self, graphql_client, seed_data):
        """Test 3: Get projects with filtering"""
        query = """
            query GetFilteredProjects {
                projects(
                    first: 5,
                    filter: {
                        status: ACTIVE,
                        priority: HIGH
                    }
                ) {
                    edges {
                        node {
                            id
                            projectId
                            name
                            status
                            priority
                            budget
                        }
                    }
                    pageInfo {
                        totalCount
                    }
                }
            }
        """
        result = await graphql_client.execute_query(query)
        assert "errors" not in result
        
        # Verify all returned projects match the filter criteria
        edges = result["data"]["projects"]["edges"]
        for edge in edges:
            node = edge["node"]
            assert node["status"] == "ACTIVE"
            assert node["priority"] == "HIGH"
    
    @pytest.mark.asyncio
    async def test_get_specific_project(self, graphql_client, seed_data):
        """Test 4: Get a specific project by ID"""
        query = """
            query GetProject {
                project(id: "ECOM-2024-001") {
                    id
                    projectId
                    name
                    description
                    status
                    priority
                    tags
                    budget
                    ownerId
                    createdAt
                    updatedAt
                    owner {
                        id
                        email
                        fullName
                        role
                    }
                }
            }
        """
        result = await graphql_client.execute_query(query)
        assert "errors" not in result
        assert result["data"]["project"] is not None
        
        project = result["data"]["project"]
        assert project["projectId"] == "ECOM-2024-001"
        assert "owner" in project
        assert project["owner"] is not None
    
    @pytest.mark.asyncio
    async def test_create_new_project(self, graphql_client):
        """Test 5: Create a new project"""
        mutation = """
            mutation CreateProject {
                createProject(input: {
                    projectId: "API-2024-001"
                    name: "GraphQL API Development"
                    description: "Building a robust GraphQL API with FastAPI and Strawberry"
                    status: ACTIVE
                    priority: HIGH
                    tags: ["api", "graphql", "fastapi"]
                    ownerId: "test-user-123"
                    budget: 30000.0
                }) {
                    id
                    projectId
                    name
                    description
                    status
                    priority
                    tags
                    budget
                    createdAt
                }
            }
        """
        result = await graphql_client.execute_query(mutation)
        assert "errors" not in result
        
        created_project = result["data"]["createProject"]
        assert created_project["projectId"] == "API-2024-001"
        assert created_project["name"] == "GraphQL API Development"
        assert created_project["priority"] == "HIGH"
        assert created_project["budget"] == 30000.0
        assert "api" in created_project["tags"]
    
    @pytest.mark.asyncio
    async def test_update_project(self, graphql_client):
        """Test 6: Update an existing project"""
        # First create a project to update
        create_mutation = """
            mutation CreateProject {
                createProject(input: {
                    projectId: "UPDATE-TEST-001"
                    name: "Original Name"
                    description: "Original Description"
                    status: ACTIVE
                    priority: LOW
                    tags: ["test"]
                    ownerId: "test-user-123"
                    budget: 10000.0
                }) {
                    id
                    projectId
                }
            }
        """
        await graphql_client.execute_query(create_mutation)
        
        # Now update it
        update_mutation = """
            mutation UpdateProject {
                updateProject(
                    id: "UPDATE-TEST-001",
                    input: {
                        name: "Advanced GraphQL API Development"
                        description: "Building a robust GraphQL API with advanced features"
                        priority: "CRITICAL"
                        budget: 45000.0
                    }
                ) {
                    id
                    projectId
                    name
                    description
                    priority
                    budget
                    updatedAt
                }
            }
        """
        result = await graphql_client.execute_query(update_mutation)
        assert "errors" not in result
        
        updated_project = result["data"]["updateProject"]
        assert updated_project["name"] == "Advanced GraphQL API Development"
        assert updated_project["priority"] == "CRITICAL"
        assert updated_project["budget"] == 45000.0
    
    @pytest.mark.asyncio
    async def test_delete_project(self, graphql_client):
        """Test 7: Delete a project"""
        # First create a project to delete
        create_mutation = """
            mutation CreateProject {
                createProject(input: {
                    projectId: "DELETE-TEST-001"
                    name: "To Be Deleted"
                    description: "This project will be deleted"
                    status: ACTIVE
                    priority: LOW
                    tags: ["test"]
                    ownerId: "test-user-123"
                    budget: 5000.0
                }) {
                    id
                    projectId
                }
            }
        """
        await graphql_client.execute_query(create_mutation)
        
        # Now delete it
        delete_mutation = """
            mutation DeleteProject {
                deleteProject(id: "DELETE-TEST-001")
            }
        """
        result = await graphql_client.execute_query(delete_mutation)
        assert "errors" not in result
        assert result["data"]["deleteProject"] is True
        
        # Verify it's deleted
        verify_query = """
            query GetProject {
                project(id: "DELETE-TEST-001") {
                    id
                    projectId
                }
            }
        """
        verify_result = await graphql_client.execute_query(verify_query)
        assert verify_result["data"]["project"] is None
    
    @pytest.mark.asyncio
    async def test_get_all_users(self, graphql_client, seed_data):
        """Test 8: Get all users"""
        query = """
            query GetUsers {
                users {
                    id
                    email
                    fullName
                    role
                    isActive
                    createdAt
                }
            }
        """
        result = await graphql_client.execute_query(query)
        assert "errors" not in result
        assert isinstance(result["data"]["users"], list)
        assert len(result["data"]["users"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_specific_user(self, graphql_client, seed_data):
        """Test 9: Get a specific user"""
        query = """
            query GetUser {
                user(id: "test-user-123") {
                    id
                    email
                    fullName
                    role
                    isActive
                }
            }
        """
        result = await graphql_client.execute_query(query)
        assert "errors" not in result
        assert result["data"]["user"] is not None
        assert result["data"]["user"]["id"] == "test-user-123"
    
    @pytest.mark.asyncio
    async def test_complex_query(self, graphql_client, seed_data):
        """Test 10: Complex query with multiple operations"""
        query = """
            query ComplexQuery {
                activeProjects: projects(
                    first: 5,
                    filter: { status: ACTIVE }
                ) {
                    edges {
                        node {
                            projectId
                            name
                            priority
                            budget
                        }
                    }
                    pageInfo {
                        totalCount
                    }
                }
                
                users {
                    id
                    email
                    fullName
                    role
                }
                
                specificProject: project(id: "ECOM-2024-001") {
                    name
                    status
                    owner {
                        fullName
                        email
                    }
                }
            }
        """
        result = await graphql_client.execute_query(query)
        assert "errors" not in result
        assert "activeProjects" in result["data"]
        assert "users" in result["data"]
        assert "specificProject" in result["data"]
    
    @pytest.mark.asyncio
    async def test_search_projects(self, graphql_client, seed_data):
        """Test 11: Search projects by name/description"""
        query = """
            query SearchProjects {
                projects(
                    first: 10,
                    filter: {
                        search: "mobile"
                    }
                ) {
                    edges {
                        node {
                            projectId
                            name
                            description
                            tags
                        }
                    }
                    pageInfo {
                        totalCount
                    }
                }
            }
        """
        result = await graphql_client.execute_query(query)
        assert "errors" not in result
        
        # Verify search results contain "mobile" in name or description
        edges = result["data"]["projects"]["edges"]
        for edge in edges:
            node = edge["node"]
            assert ("mobile" in node["name"].lower() or 
                    "mobile" in node["description"].lower())
    
    @pytest.mark.asyncio
    async def test_filter_by_tags(self, graphql_client, seed_data):
        """Test 12: Filter by tags"""
        query = """
            query ProjectsByTags {
                projects(
                    first: 10,
                    filter: {
                        tags: ["web", "api"]
                    }
                ) {
                    edges {
                        node {
                            projectId
                            name
                            tags
                            status
                        }
                    }
                    pageInfo {
                        totalCount
                    }
                }
            }
        """
        result = await graphql_client.execute_query(query)
        assert "errors" not in result
        
        # Verify filtered projects have at least one of the specified tags
        edges = result["data"]["projects"]["edges"]
        for edge in edges:
            node = edge["node"]
            assert any(tag in node["tags"] for tag in ["web", "api"])
    
    @pytest.mark.asyncio
    async def test_projects_by_owner(self, graphql_client, seed_data):
        """Test 13: Get projects by owner"""
        query = """
            query ProjectsByOwner {
                projects(
                    first: 10,
                    filter: {
                        ownerId: "test-user-123"
                    }
                ) {
                    edges {
                        node {
                            projectId
                            name
                            ownerId
                            owner {
                                fullName
                                email
                            }
                        }
                    }
                    pageInfo {
                        totalCount
                    }
                }
            }
        """
        result = await graphql_client.execute_query(query)
        assert "errors" not in result
        
        # Verify all projects belong to the specified owner
        edges = result["data"]["projects"]["edges"]
        for edge in edges:
            node = edge["node"]
            assert node["ownerId"] == "test-user-123"
    
    @pytest.mark.asyncio
    async def test_pagination_next_page(self, graphql_client, seed_data):
        """Test 14: Pagination example (get next page)"""
        # First get initial page
        first_query = """
            query GetFirstPage {
                projects(first: 3) {
                    edges {
                        node {
                            projectId
                            name
                        }
                        cursor
                    }
                    pageInfo {
                        hasNextPage
                        endCursor
                        totalCount
                    }
                }
            }
        """

        first_result = await graphql_client.execute_query(first_query)
        assert "errors" not in first_result
        
        page_info = first_result["data"]["projects"]["pageInfo"]
        if page_info["hasNextPage"]:
            # Get next page using endCursor
            next_query = f"""
                query GetNextPage {{
                    projects(
                        first: 3,
                        after: "{page_info['endCursor']}"
                    ) {{
                        edges {{
                            node {{
                                projectId
                                name
                            }}
                            cursor
                        }}
                        pageInfo {{
                            hasNextPage
                            hasPreviousPage
                            startCursor
                            endCursor
                            totalCount
                        }}
                    }}
                }}
            """
            next_result = await graphql_client.execute_query(next_query)
            assert "errors" not in next_result
            assert next_result["data"]["projects"]["pageInfo"]["hasPreviousPage"] is True
    
    @pytest.mark.asyncio
    async def test_create_multiple_projects(self, graphql_client):
        """Test 15: Create multiple projects in sequence"""
        mutation = """
            mutation CreateMultipleProjects {
                project1: createProject(input: {
                    projectId: "WEB-2024-001"
                    name: "Website Redesign"
                    description: "Complete website overhaul"
                    status: "ACTIVE"
                    priority: "MEDIUM"
                    tags: ["web", "design", "ui"]
                    ownerId: "test-user-123"
                    budget: 20000.0
                }) {
                    projectId
                    name
                }
                
                project2: createProject(input: {
                    projectId: "SECURITY-2024-001"
                    name: "Security Audit"
                    description: "Comprehensive security review"
                    status: "ACTIVE"
                    priority: "CRITICAL"
                    tags: ["security", "audit"]
                    ownerId: "test-user-123"
                    budget: 15000.0
                }) {
                    projectId
                    name
                }
            }
        """
        result = await graphql_client.execute_query(mutation)
        assert "errors" not in result
        assert result["data"]["project1"]["projectId"] == "WEB-2024-001"
        assert result["data"]["project2"]["projectId"] == "SECURITY-2024-001"


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_invalid_project_id(self, graphql_client):
        """Test querying non-existent project"""
        query = """
            query GetInvalidProject {
                project(id: "NON-EXISTENT-ID") {
                    id
                    name
                }
            }
        """
        result = await graphql_client.execute_query(query)
        assert result["data"]["project"] is None
    
    @pytest.mark.asyncio
    async def test_duplicate_project_id(self, graphql_client):
        """Test creating project with duplicate ID"""
        # Create first project
        mutation = """
            mutation CreateProject {
                createProject(input: {
                    projectId: "DUPLICATE-001"
                    name: "First Project"
                    description: "Original project"
                    status: ACTIVE
                    priority: MEDIUM
                    tags: ["test"]
                    ownerId: "test-user-123"
                    budget: 10000.0
                }) {
                    projectId
                }
            }
        """
        await graphql_client.execute_query(mutation)
        
        # Try to create duplicate
        result = await graphql_client.execute_query(mutation)
        assert "errors" in result
    
    @pytest.mark.asyncio
    async def test_invalid_filter_values(self, graphql_client):
        """Test with invalid filter values"""
        query = """
            query GetProjectsInvalidFilter {
                projects(
                    first: -1
                ) {
                    edges {
                        node {
                            id
                        }
                    }
                }
            }
        """
        result = await graphql_client.execute_query(query)
        assert "errors" in result


class TestPerformance:
    """Performance and load testing"""
    
    @pytest.mark.asyncio
    async def test_bulk_query_performance(self, graphql_client, seed_data):
        """Test performance with large result sets"""
        import time
        
        query = """
            query GetLargeDataset {
                projects(first: 100) {
                    edges {
                        node {
                            id
                            projectId
                            name
                            description
                            status
                            priority
                            tags
                            budget
                            ownerId
                            createdAt
                            updatedAt
                            owner {
                                id
                                email
                                fullName
                                role
                            }
                        }
                    }
                    pageInfo {
                        totalCount
                    }
                }
            }
        """
        
        start_time = time.time()
        result = await graphql_client.execute_query(query)
        end_time = time.time()
        
        assert "errors" not in result
        execution_time = end_time - start_time
        assert execution_time < 5.0  # Should complete within 5 seconds
        print(f"Query execution time: {execution_time:.2f} seconds")
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, graphql_client, seed_data):
        """Test handling concurrent requests"""
        queries = []
        for i in range(10):
            query = f"""
                query GetProject{{i}} {{
                    project(id: "ECOM-2024-001") {{
                        id
                        name
                        status
                    }}
                }}
            """
            queries.append(graphql_client.execute_query(query))
        
        results = await asyncio.gather(*queries)
        
        for result in results:
            assert "errors" not in result
            assert result["data"]["project"] is not None


# Utility functions for test data management
class TestDataManager:
    """Helper class for managing test data"""
    
    @staticmethod
    async def cleanup_test_projects(graphql_client, project_ids: list):
        """Clean up test projects after tests"""
        for project_id in project_ids:
            mutation = f"""
                mutation DeleteProject {{
                    deleteProject(id: "{project_id}")
                }}
            """
            try:
                await graphql_client.execute_query(mutation)
            except Exception:
                pass  # Ignore errors during cleanup
    
    @staticmethod
    async def create_test_user(graphql_client, user_data: dict):
        """Create a test user"""
        mutation = """
            mutation CreateUser($input: UserInput!) {
                createUser(input: $input) {
                    id
                    email
                    fullName
                    role
                }
            }
        """
        return await graphql_client.execute_query(mutation, {"input": user_data})


# Configuration for pytest
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


# Test runner script
if __name__ == "__main__":
    """Run tests with different configurations"""
    import subprocess
    import sys
    
    # Run all tests
    print("Running all tests...")
    subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"])
    
    # Run only fast tests
    print("\nRunning fast tests only...")
    subprocess.run([sys.executable, "-m", "pytest", __file__, "-v", "-m", "not slow"])
    
    # Run with coverage
    print("\nRunning tests with coverage...")
    subprocess.run([
        sys.executable, "-m", "pytest", __file__, 
        "--cov=.", "--cov-report=html", "-v"
    ])
