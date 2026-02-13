from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CategoryOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class RecipeOut(BaseModel):
    id: int
    title: str
    description: str
    image_url: Optional[str] = None
    category: Optional[CategoryOut] = None
    ingredients: list[str]
    instructions: list[str]
    created_at: datetime

    avg_rating: float = Field(..., description="Average rating (1-5), 0 if no ratings")
    ratings_count: int = Field(..., description="Number of ratings for the recipe")

    is_favorite: bool = Field(False, description="Whether current user has favorited this recipe (if authenticated)")

    class Config:
        from_attributes = True


class RecipeListOut(BaseModel):
    items: list[RecipeOut]
    total: int


class RegisterIn(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password (min 6 characters)")
    display_name: str = Field(..., description="Public display name")


class LoginIn(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class FavoriteOut(BaseModel):
    recipe_id: int
    created_at: datetime


class RatingUpsertIn(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: str = Field("", description="Optional review comment")


class RatingOut(BaseModel):
    user_id: int
    recipe_id: int
    rating: int
    comment: str
    created_at: datetime
    updated_at: datetime
