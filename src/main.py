from fastapi import FastAPI
from src.api.routes import feature_routes
from src.config.settings import settings

# Initialize FastAPI application
app = FastAPI(title=settings.APP_NAME)

# Include routers
app.include_router(feature_routes.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)