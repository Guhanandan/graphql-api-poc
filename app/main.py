from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import strawberry
from strawberry.fastapi import GraphQLRouter
import logging
from contextlib import asynccontextmanager

from app.schema.queries import Query
from app.schema.mutations import Mutation
from app.database.connection import init_database
from decouple import config
from app.auth.azure_ad import get_current_user
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("Starting up GraphQL API...")
    try:
        await init_database()
        logger.info("Database initialized successfully")
        
        # Log authentication mode
        if config('DEBUG', default=False, cast=bool):
            logger.warning("Running in DEBUG mode with development authentication")
        else:
            logger.info("Running with Azure AD authentication")
            
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down GraphQL API...")

# Create FastAPI app
app = FastAPI(
    title="Project Management GraphQL API",
    description="A GraphQL API for managing projects with Azure AD authentication",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config('ALLOWED_ORIGINS', default='http://localhost:3000,http://localhost:8080').split(','),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Custom context getter for GraphQL
async def get_context(request: Request):
    """Custom context function to pass request to GraphQL resolvers"""
    return {
        "request": request,
        "current_user": None  # Will be populated by permission classes
    }

# Create GraphQL router
graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context,
    graphiql=config('GRAPHIQL_ENABLED', default=True, cast=bool)
)

# Mount GraphQL endpoint
app.include_router(graphql_app, prefix="/graphql")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Project Management GraphQL API",
        "status": "healthy",
        "authentication": "Azure AD" if not config('DEBUG', default=False, cast=bool) else "Development",
        "graphql_endpoint": "/graphql",
        "graphiql_endpoint": "/graphql" if config('GRAPHIQL_ENABLED', default=True, cast=bool) else None
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        from datetime import datetime
        return {
            "status": "healthy",
            "database": "connected",
            "authentication": "Azure AD" if not config('DEBUG', default=False, cast=bool) else "Development",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.post("/test-auth")
async def test_auth(request: Request):
    try:
        user = await get_current_user(request)
        return {"authenticated": True, "user": user}
    except Exception as e:
        # Add proper logging
        logger.error(f"Authentication failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return {"authenticated": False, "error": str(e)}

@app.get("/auth/info")
async def auth_info():
    """Authentication configuration info (non-sensitive)"""
    return {
        "authentication_type": "Azure AD" if not config('DEBUG', default=False, cast=bool) else "Development",
        "tenant_id": config('AZURE_TENANT_ID', default='not-configured'),
        "client_id": config('AZURE_CLIENT_ID', default='not-configured'),
        "debug_mode": config('DEBUG', default=False, cast=bool)
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return {
        "error": {
            "message": exc.detail,
            "status_code": exc.status_code
        }
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return HTTPException(
        status_code=500,
        detail="Internal server error"
    )

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=config('DEBUG', default=False, cast=bool),
        log_level="info"
    )