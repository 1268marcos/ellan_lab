from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.template import Template

router = APIRouter(prefix="/api/v1", tags=["templates"])


class TemplateIn(BaseModel):
    name: str
    body: str = Field(min_length=1)


@router.post("/templates", status_code=status.HTTP_201_CREATED)
def post_template(body: TemplateIn, db: Session = Depends(get_db)) -> dict:
    t = Template(name=body.name, body=body.body)
    db.add(t)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail="duplicate_name") from e
    db.refresh(t)
    return {"id": t.id, "name": t.name}
