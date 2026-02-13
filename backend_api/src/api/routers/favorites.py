from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from api.core.security import get_current_user
from api.db.models import Favorite, Rating, Recipe, User
from api.db.session import get_db
from api.schemas import RecipeListOut, RecipeOut

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get(
    "",
    response_model=RecipeListOut,
    summary="List favorite recipes",
    description="Returns the authenticated user's favorited recipes.",
)
def list_favorites(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> RecipeListOut:
    stats_sq = (
        select(
            Rating.recipe_id.label("recipe_id"),
            (select(Rating.rating).where((Rating.user_id == current_user.id) & (Rating.recipe_id == Rating.recipe_id)))
        )
        .subquery()
    )

    # Use simpler aggregation for favorites listing.
    agg_sq = (
        select(
            Rating.recipe_id.label("recipe_id"),
            func.coalesce(func.avg(Rating.rating), 0).label("avg_rating"),
            func.count(Rating.rating).label("ratings_count"),
        )
        .group_by(Rating.recipe_id)
        .subquery()
    )

    stmt = (
        select(Recipe, agg_sq.c.avg_rating, agg_sq.c.ratings_count)
        .join(Favorite, Favorite.recipe_id == Recipe.id)
        .outerjoin(agg_sq, agg_sq.c.recipe_id == Recipe.id)
        .options(joinedload(Recipe.category))
        .where(Favorite.user_id == current_user.id)
        .order_by(Favorite.created_at.desc())
    )
    rows = db.execute(stmt).all()

    items: list[RecipeOut] = []
    for recipe, avg_rating, ratings_count in rows:
        items.append(
            RecipeOut(
                id=recipe.id,
                title=recipe.title,
                description=recipe.description,
                image_url=recipe.image_url,
                category=recipe.category,
                ingredients=recipe.ingredients,
                instructions=recipe.instructions,
                created_at=recipe.created_at,
                avg_rating=float(avg_rating or 0),
                ratings_count=int(ratings_count or 0),
                is_favorite=True,
            )
        )

    return RecipeListOut(items=items, total=len(items))


@router.post(
    "/{recipe_id}",
    summary="Add favorite",
    description="Favorites a recipe for the authenticated user.",
)
def add_favorite(recipe_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    existing = db.execute(
        select(Favorite).where((Favorite.user_id == current_user.id) & (Favorite.recipe_id == recipe_id))
    ).scalar_one_or_none()
    if existing:
        return {"status": "ok"}

    fav = Favorite(user_id=current_user.id, recipe_id=recipe_id)
    db.add(fav)
    db.commit()
    return {"status": "ok"}


@router.delete(
    "/{recipe_id}",
    summary="Remove favorite",
    description="Unfavorites a recipe for the authenticated user.",
)
def remove_favorite(recipe_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    fav = db.execute(
        select(Favorite).where((Favorite.user_id == current_user.id) & (Favorite.recipe_id == recipe_id))
    ).scalar_one_or_none()
    if not fav:
        return {"status": "ok"}

    db.delete(fav)
    db.commit()
    return {"status": "ok"}
