# Project Management GraphQL API - PoC

## Overview

This is a comprehensive GraphQL API built with FastAPI and Strawberry GraphQL, designed to demonstrate enterprise-level API development with Azure integration, authentication, and modern development practices.

## Features

- **GraphQL API** with full CRUD operations for projects
- **Azure AD Authentication** with role-based access control
- **Azure Cosmos DB** integration for data persistence
- **Pagination and Filtering** with cursor-based pagination
- **Comprehensive Testing** with pytest and mocking
- **Docker Support** for containerized deployment
- **Role-based Security** (Admin, Manager, Developer, Viewer)
- **Comprehensive Documentation** with GraphiQL interface

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client App    │───▶│   FastAPI App    │───▶│  Azure Cosmos   │
│  (GraphiQL/UI)  │    │  (GraphQL API)   │    │       DB        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │    Azure AD      │
                        │ (Authentication) │
                        └──────────────────┘
```

## Prerequisites

- Python 3.11+
- Azure Account with:
  - Azure AD App Registration
  - Cosmos DB Account
- Docker (for containerization)
- Git

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd graphql-api-poc

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your Azure credentials
```

Required environment variables:
```env
# Azure AD
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# Cosmos DB
COSMOS_URL=https://your-account.documents.azure.com:443/
COSMOS_KEY=your-primary-key
COSMOS_DATABASE_NAME=ProjectsDB

# App Config
DEBUG=true
GRAPHIQL_ENABLED=true
ALLOWED_ORIGINS=http://localhost:3000
```

### 3. Azure Setup

#### Azure AD App Registration:
1. Go to Azure Portal → Azure Active Directory → App registrations
2. Create new registration:
   - Name: `Project Management API`
   - Redirect URI: `http://localhost:8000/auth/callback`
3. Note down:
   - Application (client) ID
   - Directory (tenant) ID
4. Create client secret:
   - Certificates & secrets → New client secret
   - Note down the secret value
5. API permissions:
   - Add `Microsoft Graph` → `User.Read`
   - Grant admin consent

#### Cosmos DB Setup:
1. Create Cosmos DB account
2. Choose Core (SQL) API
3. Note down:
   - URI
   - Primary Key
4. Database and containers will be created automatically

### 4. Run the Application

```bash
# Development mode
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the script
python app/main.py
```

### 5. Access the API

- **API Endpoint**: http://localhost:8000/graphql
- **GraphiQL Interface**: http://localhost:8000/graphql (interactive playground)
- **Health Check**: http://localhost:8000/health

## API Usage

### Authentication

Include Azure AD bearer token in requests:
```http
Authorization: Bearer <your-azure-ad-token>
```

For development/testing, you can use:
```http
Authorization: Bearer dev-token
```

Excellent! Your application is now running successfully. Let me guide you through testing all the GraphQL endpoints with detailed explanations.

## Access GraphQL Playground

First, open your browser and navigate to: **http://localhost:8000/graphql**

You'll see the GraphQL Playground interface with:
- Left panel: Where you write queries/mutations
- Middle panel: Results
- Right panel: Schema documentation

## 1. Test READ Operations (Queries)

### A. Get All Projects (with Pagination)

```graphql
query GetAllProjects {
  projects(first: 5) {
    edges {
      node {
        id
        name
        description
        status
        priority
        tags
        ownerId
        budget
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
```

**Explanation:**
- `first: 5` - Get first 5 projects
- `edges` - Contains the actual project data and cursor for pagination
- `pageInfo` - Contains pagination metadata

### B. Get Projects with Filtering

```graphql
query GetFilteredProjects {
  projects(
    first: 10
    filter: {
      status: ACTIVE
      priority: HIGH
      tags: ["api", "graphql"]
    }
  ) {
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
    }
  }
}
```

**Explanation:**
- Filters projects by status, priority, and tags
- Multiple filters are combined with AND logic

### C. Search Projects

```graphql
query SearchProjects {
  projects(
    first: 10
    filter: {
      search: "API"
    }
  ) {
    edges {
      node {
        id
        name
        description
      }
    }
  }
}
```

**Explanation:**
- Searches in both name and description fields
- Case-insensitive search

### D. Get Single Project by ID

First, get an ID from the previous queries, then:

```graphql
query GetSingleProject {
  project(id: "YOUR-PROJECT-ID-HERE") {
    id
    name
    description
    status
    priority
    tags
    ownerId
    budget
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
```

**Explanation:**
- Replace `YOUR-PROJECT-ID-HERE` with an actual project ID
- Notice the `owner` field - it demonstrates relationship resolution

### E. Pagination Example

```graphql
# First page
query FirstPage {
  projects(first: 2) {
    edges {
      node {
        name
      }
      cursor
    }
    pageInfo {
      endCursor
      hasNextPage
    }
  }
}

# Next page (use endCursor from previous query)
query NextPage {
  projects(first: 2, after: "CURSOR-FROM-PREVIOUS-QUERY") {
    edges {
      node {
        name
      }
    }
    pageInfo {
      endCursor
      hasNextPage
    }
  }
}
```

### F. Get All Users

```graphql
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
```

## 2. Test CREATE Operations (Mutations)

### A. Create a New Project

```graphql
mutation CreateNewProject {
  createProject(input: {
    name: "E-commerce Platform"
    description: "Building a modern e-commerce platform with microservices"
    status: "active"
    priority: "high"
    tags: ["e-commerce", "microservices", "api"]
    ownerId: "test-user-123"
    budget: 75000.0
  }) {
    id
    name
    description
    status
    priority
    tags
    budget
    createdAt
  }
}
```

**Explanation:**
- All fields except `name` and `ownerId` are optional
- The response includes the newly created project with generated ID

### B. Create Multiple Projects (Run these one by one)

```graphql
# Project 2
mutation CreateMobileApp {
  createProject(input: {
    name: "Mobile Banking App"
    description: "Secure mobile banking application for iOS and Android"
    status: "active"
    priority: "critical"
    tags: ["mobile", "banking", "security"]
    ownerId: "test-user-123"
    budget: 120000.0
  }) {
    id
    name
    status
    priority
  }
}

# Project 3
mutation CreateDataPipeline {
  createProject(input: {
    name: "Real-time Data Pipeline"
    description: "Building data pipeline for real-time analytics"
    status: "active"
    priority: "medium"
    tags: ["data", "analytics", "real-time"]
    ownerId: "test-user-123"
    budget: 45000.0
  }) {
    id
    name
    tags
  }
}

# Project 4 - Minimal example
mutation CreateMinimalProject {
  createProject(input: {
    name: "Quick POC Project"
    ownerId: "test-user-123"
  }) {
    id
    name
    status
    priority
  }
}
```

## 3. Test UPDATE Operations

### A. Update Project Details

First, get a project ID from previous queries, then:

```graphql
mutation UpdateProjectDetails {
  updateProject(
    id: "YOUR-PROJECT-ID-HERE"
    input: {
      name: "Updated E-commerce Platform v2"
      description: "Enhanced platform with AI recommendations"
      priority: "critical"
      budget: 95000.0
    }
  ) {
    id
    name
    description
    priority
    budget
    updatedAt
  }
}
```

### B. Update Project Status

```graphql
mutation UpdateProjectStatus {
  updateProject(
    id: "YOUR-PROJECT-ID-HERE"
    input: {
      status: "completed"
    }
  ) {
    id
    name
    status
    updatedAt
  }
}
```

### C. Update Project Tags

```graphql
mutation UpdateProjectTags {
  updateProject(
    id: "YOUR-PROJECT-ID-HERE"
    input: {
      tags: ["updated", "v2", "enhanced"]
    }
  ) {
    id
    name
    tags
    updatedAt
  }
}
```

## 4. Test DELETE Operations

```graphql
mutation DeleteProject {
  deleteProject(id: "YOUR-PROJECT-ID-HERE")
}
```

**Explanation:**
- Returns `true` if deletion was successful
- Returns `false` if project doesn't exist

## 5. Complex Query Examples

### A. Combined Operations

```graphql
query ComplexProjectQuery {
  # Get active high-priority projects
  activeHighPriority: projects(
    first: 5
    filter: {
      status: ACTIVE
      priority: HIGH
    }
  ) {
    edges {
      node {
        id
        name
        priority
        budget
      }
    }
    pageInfo {
      totalCount
    }
  }
  
  # Get completed projects
  completedProjects: projects(
    first: 5
    filter: {
      status: COMPLETED
    }
  ) {
    edges {
      node {
        id
        name
        status
      }
    }
  }
  
  # Get all users
  allUsers: users {
    id
    fullName
    role
  }
}
```

### B. Project with Owner Details

```graphql
query ProjectWithOwner {
  project(id: "YOUR-PROJECT-ID-HERE") {
    id
    name
    description
    owner {
      id
      email
      fullName
      role
    }
    status
    priority
    tags
    budget
  }
}
```

## 6. Testing with Variables

GraphQL Playground supports variables. Here's how to use them:

**Query:**
```graphql
query GetProjectById($projectId: String!) {
  project(id: $projectId) {
    id
    name
    description
    status
  }
}

mutation CreateProjectWithVars(
  $name: String!
  $description: String
  $ownerId: String!
  $budget: Float
) {
  createProject(input: {
    name: $name
    description: $description
    ownerId: $ownerId
    budget: $budget
  }) {
    id
    name
    budget
  }
}
```

**Variables (in the bottom panel):**
```json
{
  "projectId": "YOUR-PROJECT-ID",
  "name": "New Project with Variables",
  "description": "Created using GraphQL variables",
  "ownerId": "test-user-123",
  "budget": 50000
}
```

## 7. Test Error Handling

### A. Invalid Project ID
```graphql
query InvalidProject {
  project(id: "invalid-id-12345") {
    id
    name
  }
}
```

### B. Missing Required Fields
```graphql
mutation InvalidCreate {
  createProject(input: {
    description: "This will fail - missing name"
    ownerId: "test-user-123"
  }) {
    id
  }
}
```

## 8. Performance Testing

### A. Large Dataset Query
```graphql
query LargeDataset {
  projects(first: 50) {
    edges {
      node {
        id
        name
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
```

## Testing Tips:

1. **Use the Schema Explorer**: Click "DOCS" in the playground to explore available queries, mutations, and types

2. **Auto-completion**: Press Ctrl+Space for auto-completion suggestions

3. **Query History**: The playground saves your query history

4. **Multiple Tabs**: You can open multiple query tabs for different operations

5. **HTTP Headers**: Add authentication headers when you implement auth:
   ```json
   {
     "Authorization": "Bearer YOUR-TOKEN"
   }
   ```

## Verify in Cosmos DB Data Explorer

After running these operations, verify the data:
1. Go to https://localhost:8081/_explorer/index.html
2. Navigate to ProjectsDB > projects
3. You should see all your created projects

This comprehensive testing covers all CRUD operations and demonstrates the full capabilities of your GraphQL API!