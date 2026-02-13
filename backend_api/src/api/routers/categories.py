from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.models import Category
from api.db.session import get_db
from api.schemas import CategoryOut

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get(
    "",
    response_model=list[CategoryOut],
    summary="List categories",
    description="Returns all recipe categories.",
)
def list_categories(db: Session = Depends(get_db)) -> list[CategoryOut]:
    categories = db.execute(select(Category).order_by(Category.name.asc())).scalars().all()
    return categories
