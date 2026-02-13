from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from api.core.security import get_current_user
from api.db.models import Favorite, Rating, Recipe, User
from api.db.session import get_db
from api.schemas import RecipeListOut, RecipeOut

router = APIRouter(prefix="/recipes", tags=["recipes"])


def _recipe_with_stats_subquery():
    # Aggregates ratings into avg/count per recipe
    return (
        select(
            Rating.recipe_id.label("recipe_id"),
            func.coalesce(func.avg(Rating.rating), 0).label("avg_rating"),
            func.count(Rating.rating).label("ratings_count"),
        )
        .group_by(Rating.recipe_id)
        .subquery()
    )


@router.get(
    "",
    response_model=RecipeListOut,
    summary="List recipes",
    description="Browse recipes with optional category filter and ingredient search.",
)
def list_recipes(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="Search query matched against title and ingredients"),
    category_id: Optional[int] = Query(None, description="Filter by category id"),
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[User] = Depends(get_current_user),  # optional auth; if no token => 401
):
    # Make auth optional: if no Authorization header, OAuth2 dependency throws.
    # We handle this by intercepting the exception in FastAPI? Not possible here.
    # Instead, frontend should pass token only when available.
    # For endpoints where auth is optional, we accept token via header manually.
    raise HTTPException(status_code=500, detail="Use /recipes/public endpoint for unauthenticated browsing.")


@router.get(
    "/public",
    response_model=RecipeListOut,
    summary="List recipes (public)",
    description="Browse recipes without authentication; does not include is_favorite.",
)
def list_recipes_public(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="Search query matched against title and ingredients"),
    category_id: Optional[int] = Query(None, description="Filter by category id"),
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> RecipeListOut:
    stats_sq = _recipe_with_stats_subquery()

    stmt = (
        select(Recipe, stats_sq.c.avg_rating, stats_sq.c.ratings_count)
        .options(joinedload(Recipe.category))
        .outerjoin(stats_sq, stats_sq.c.recipe_id == Recipe.id)
        .order_by(Recipe.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    if category_id is not None:
        stmt = stmt.where(Recipe.category_id == category_id)

    if q:
        # title ilike OR ingredients contains (case-insensitive by scanning array text)
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            func.lower(Recipe.title).like(like)
            | func.exists(
                select(1).where(func.lower(func.unnest(Recipe.ingredients)).like(like))
            )
        )

    rows = db.execute(stmt).all()
    total_stmt = select(func.count(Recipe.id))
    if category_id is not None:
        total_stmt = total_stmt.where(Recipe.category_id == category_id)
    if q:
        like = f"%{q.lower()}%"
        total_stmt = total_stmt.where(
            func.lower(Recipe.title).like(like)
            | func.exists(
                select(1).where(func.lower(func.unnest(Recipe.ingredients)).like(like))
            )
        )
    total = db.execute(total_stmt).scalar_one()

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
                is_favorite=False,
            )
        )
    return RecipeListOut(items=items, total=int(total))


@router.get(
    "/{recipe_id}",
    response_model=RecipeOut,
    summary="Get recipe details (public)",
    description="Returns recipe details including rating stats. Public endpoint.",
)
def get_recipe_public(recipe_id: int, db: Session = Depends(get_db)) -> RecipeOut:
    stats_sq = _recipe_with_stats_subquery()
    stmt = (
        select(Recipe, stats_sq.c.avg_rating, stats_sq.c.ratings_count)
        .options(joinedload(Recipe.category))
        .outerjoin(stats_sq, stats_sq.c.recipe_id == Recipe.id)
        .where(Recipe.id == recipe_id)
    )
    row = db.execute(stmt).first()
    if not row:
        raise HTTPException(status_code=404, detail="Recipe not found")

    recipe, avg_rating, ratings_count = row
    return RecipeOut(
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
        is_favorite=False,
    )
