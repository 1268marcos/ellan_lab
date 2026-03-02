# Dependência de header interno (2:A)
import os
from fastapi import Header, HTTPException

INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "")

def require_internal_token(x_internal_token: str = Header(default="", alias="X-Internal-Token")):
    if not INTERNAL_TOKEN:
        raise HTTPException(status_code=500, detail="INTERNAL_TOKEN not configured")
    if x_internal_token != INTERNAL_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid internal token")
    return True