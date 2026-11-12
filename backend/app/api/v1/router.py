"""
API v1 Master Router for DukaanAI.
Aggregates authentication, business management, user profile, and health routes.
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .businesses import router as businesses_router
from .catalogue import router as catalogue_router
from .health import router as health_router
from .users import router as users_router

api_v1_router = APIRouter()

# Include versioned routers
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(businesses_router)
api_v1_router.include_router(catalogue_router)
api_v1_router.include_router(users_router)
