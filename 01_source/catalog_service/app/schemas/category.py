from __future__ import annotations

from pydantic import BaseModel


class CategoryOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    is_active: bool
