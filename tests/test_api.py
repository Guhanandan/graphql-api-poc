"""Test script to verify local setup is working"""

import asyncio
import httpx
from datetime import datetime

async def test_api():
    """Test the GraphQL API"""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # Test health endpoint
        print("Testing health endpoint...")
        response = await client.get(f"{base_url}/health")
        print(f"Health check: {response.json()}\n")
        
        # Test GraphQL endpoint
        print("Testing GraphQL endpoint...")
        
        # 1. Query all projects
        query_all = """
        query {
            projects(first: 5) {
                edges {
                    node {
                        id
                        name
                        status
                        priority
                        tags
                    }
                }
                pageInfo {
                    totalCount
                    hasNextPage
                }
            }
        }
        """
        
        response = await client.post(
            f"{base_url}/graphql",
            json={"query": query_all}
        )
        print("All projects:", response.json(), "\n")
        
        # 2. Create a new project
        create_mutation = """
        mutation {
            createProject(input: {
                name: "Test Project from Script"
                description: "Created via test script"
                status: "active"
                priority: "high"
                tags: ["test", "script"]
                ownerId: "test-user-123"
                budget: 5000.0
            }) {
                id
                name
                description
                createdAt
            }
        }
        """
        
        response = await client.post(
            f"{base_url}/graphql",
            json={"query": create_mutation}
        )
        result = response.json()
        print("Created project:", result, "\n")
        
        # Extract project ID if creation was successful
        if "data" in result and result["data"]["createProject"]:
            project_id = result["data"]["createProject"]["id"]
            
            # 3. Query single project
            query_single = f"""
            query {{
                project(id: "{project_id}") {{
                    id
                    name
                    description
                    status
                    priority
                    budget
                }}
            }}
            """
            
            response = await client.post(
                f"{base_url}/graphql",
                json={"query": query_single}
            )
            print("Single project:", response.json(), "\n")
            
            # 4. Update project
            update_mutation = f"""
            mutation {{
                updateProject(id: "{project_id}", input: {{
                    name: "Updated Test Project"
                    priority: "medium"
                }}) {{
                    id
                    name
                    priority
                    updatedAt
                }}
            }}
            """
            
            response = await client.post(
                f"{base_url}/graphql",
                json={"query": update_mutation}
            )
            print("Updated project:", response.json(), "\n")
            
            # 5. Test filtering
            filter_query = """
            query {
                projects(
                    first: 10
                    filter: {
                        status: ACTIVE
                        priority: HIGH
                    }
                ) {
                    edges {
                        node {
                            name
                            status
                            priority
                        }
                    }
                    pageInfo {
                        totalCount
                    }
                }
            }
            """
            
            response = await client.post(
                f"{base_url}/graphql",
                json={"query": filter_query}
            )
            print("Filtered projects:", response.json(), "\n")

if __name__ == "__main__":
    print(f"Starting API test at {datetime.now()}\n")
    asyncio.run(test_api())