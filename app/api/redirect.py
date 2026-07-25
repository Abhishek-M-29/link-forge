from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from app.database.session import get_db
from app.models.url import Url

router = APIRouter(tags=["redirect"])

@router.get("/{short_code}")
def redirect_to_original(short_code: str, request: Request, db: Session = Depends(get_db)):
    url_row = db.scalar(select(Url).where(Url.short_code == short_code))
    if url_row is None:
        raise HTTPException(status_code=404, detail="Short URL not found")
    if not url_row.is_active:
        raise HTTPException(status_code=410, detail="This link has been deactivated")
    if url_row.expires_at and url_row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="This link has expired")
        
    # Increment click count (see Chapter 21 for full analytics capture)
    db.execute(update(Url).where(Url.id == url_row.id).values(click_count=Url.click_count + 1))
    db.commit()
    
    return RedirectResponse(url=url_row.original_url, status_code=302)
