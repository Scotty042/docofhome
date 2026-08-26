import json
from datetime import UTC, datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.recipe import Recipe
from app.schemas.recipe import RecipeRead, RecipeWrite

router = APIRouter(prefix="/recipes", tags=["recipes"])

def read_model(row: Recipe) -> RecipeRead:
    return RecipeRead(id=row.id, title=row.title, category=row.category,
        tags=json.loads(row.tags_json), preparation_minutes=row.preparation_minutes,
        cooking_minutes=row.cooking_minutes, servings=row.servings, favorite=row.favorite,
        image_url=row.image_url, ingredients=json.loads(row.ingredients_json),
        steps=json.loads(row.steps_json), notes=row.notes, source_url=row.source_url,
        attachments=json.loads(row.attachments_json), created_at=row.created_at, updated_at=row.updated_at)

def apply(row: Recipe, data: RecipeWrite) -> None:
    for key in ("title", "category", "preparation_minutes", "cooking_minutes", "servings", "favorite", "notes"):
        setattr(row, key, getattr(data, key))
    row.image_url = str(data.image_url) if data.image_url else None
    row.source_url = str(data.source_url) if data.source_url else None
    row.tags_json = json.dumps(list(dict.fromkeys(tag.strip() for tag in data.tags if tag.strip())), ensure_ascii=False)
    row.ingredients_json = json.dumps([item.model_dump() for item in data.ingredients], ensure_ascii=False)
    row.steps_json = json.dumps([step.strip() for step in data.steps if step.strip()], ensure_ascii=False)
    row.attachments_json = json.dumps(data.attachments, ensure_ascii=False)
    row.updated_at = datetime.now(UTC)

@router.get("", response_model=list[RecipeRead])
def list_recipes(q: str = Query(default="", max_length=200), category: str = "", tag: str = "", session: Session = Depends(get_session)):
    statement = select(Recipe)
    if q.strip():
        needle = f"%{q.strip()}%"
        statement = statement.where(or_(Recipe.title.ilike(needle), Recipe.ingredients_json.ilike(needle)))
    if category.strip(): statement = statement.where(Recipe.category == category.strip())
    if tag.strip(): statement = statement.where(Recipe.tags_json.ilike(f'%"{tag.strip()}"%'))
    return [read_model(row) for row in session.exec(statement.order_by(Recipe.favorite.desc(), Recipe.title)).all()]

@router.post("", response_model=RecipeRead, status_code=status.HTTP_201_CREATED)
def create_recipe(data: RecipeWrite, session: Session = Depends(get_session)):
    row = Recipe(title=data.title); apply(row, data); session.add(row); session.commit(); session.refresh(row); return read_model(row)

@router.get("/{recipe_id}", response_model=RecipeRead)
def get_recipe(recipe_id: UUID, session: Session = Depends(get_session)):
    row = session.get(Recipe, recipe_id)
    if not row: raise HTTPException(404, "Rezept nicht gefunden")
    return read_model(row)

@router.put("/{recipe_id}", response_model=RecipeRead)
def update_recipe(recipe_id: UUID, data: RecipeWrite, session: Session = Depends(get_session)):
    row = session.get(Recipe, recipe_id)
    if not row: raise HTTPException(404, "Rezept nicht gefunden")
    apply(row, data); session.add(row); session.commit(); session.refresh(row); return read_model(row)

@router.post("/{recipe_id}/duplicate", response_model=RecipeRead, status_code=status.HTTP_201_CREATED)
def duplicate_recipe(recipe_id: UUID, session: Session = Depends(get_session)):
    source = session.get(Recipe, recipe_id)
    if not source: raise HTTPException(404, "Rezept nicht gefunden")
    data = read_model(source).model_dump(exclude={"id", "created_at", "updated_at"}); data["title"] = f'{source.title} (Kopie)'
    row = Recipe(title=data["title"]); apply(row, RecipeWrite.model_validate(data)); session.add(row); session.commit(); session.refresh(row); return read_model(row)

@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(recipe_id: UUID, session: Session = Depends(get_session)):
    row = session.get(Recipe, recipe_id)
    if not row: raise HTTPException(404, "Rezept nicht gefunden")
    session.delete(row); session.commit()
