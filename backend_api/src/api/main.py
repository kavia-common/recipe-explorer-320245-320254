from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.config import get_settings
from api.routers.auth import router as auth_router
from api.routers.categories import router as categories_router
from api.routers.favorites import router as favorites_router
from api.routers.ratings import router as ratings_router
from api.routers.recipes import router as recipes_router

settings = get_settings()

openapi_tags = [
    {"name": "auth", "description": "User registration and login."},
    {"name": "categories", "description": "Recipe categories for browsing."},
    {"name": "recipes", "description": "Recipe browsing and search."},
    {"name": "favorites", "description": "User favorites (requires authentication)."},
    {"name": "ratings", "description": "User ratings (requires authentication)."},
]

app = FastAPI(
    title="Recipe Explorer API",
    description="Backend API for browsing, searching, favoriting, and rating recipes.",
    version="0.1.0",
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"], summary="Health check", description="Simple health check endpoint.")
def health_check():
    """Health check endpoint.

    Returns:
        JSON payload { "message": "Healthy" }
    """
    return {"message": "Healthy"}


app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(recipes_router)
app.include_router(favorites_router)
app.include_router(ratings_router)
