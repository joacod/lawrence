from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import feature_routes
from src.config.settings import settings

# Initialize FastAPI application
app = FastAPI(title=settings.APP_NAME)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(feature_routes.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)