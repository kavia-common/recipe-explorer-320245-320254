from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.core.security import get_current_user
from api.db.models import Rating, Recipe, User
from api.db.session import get_db
from api.schemas import RatingOut, RatingUpsertIn

router = APIRouter(prefix="/ratings", tags=["ratings"])


@router.put(
    "/{recipe_id}",
    response_model=RatingOut,
    summary="Create or update rating",
    description="Upserts the authenticated user's rating for a recipe.",
)
def upsert_rating(
    recipe_id: int,
    payload: RatingUpsertIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RatingOut:
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    rating = db.execute(
        select(Rating).where((Rating.user_id == current_user.id) & (Rating.recipe_id == recipe_id))
    ).scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if not rating:
        rating = Rating(user_id=current_user.id, recipe_id=recipe_id, rating=payload.rating, comment=payload.comment)
        db.add(rating)
    else:
        rating.rating = payload.rating
        rating.comment = payload.comment
        rating.updated_at = now

    db.commit()
    db.refresh(rating)
    return rating
