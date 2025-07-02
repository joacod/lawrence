"""
Main API router that combines all route modules.
This provides a single entry point for all API endpoints with proper organization.
"""
from fastapi import APIRouter
from . import health_routes, session_routes, feature_routes

# Create the main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(health_routes.router)
api_router.include_router(session_routes.router)
api_router.include_router(feature_routes.router) 