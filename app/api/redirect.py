import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from app.database.session import get_db
from app.models.url import Url
from app.analytics.service import record_click
from app.cache.redis_client import redis_client

CACHE_TTL_SECONDS = 300
router = APIRouter(tags=["redirect"])

@router.get("/{short_code}")
def redirect_to_original(short_code: str, request: Request, db: Session = Depends(get_db)):
    cache_key = f"url:{short_code}"
    cached = redis_client.get(cache_key)
    
    if cached:
        data = json.loads(cached)
        if data["is_active"] is False:
            raise HTTPException(status_code=410, detail="This link has been deactivated")
            
        # cache-only fast path (keeping click writes synchronous for now)
        db.execute(update(Url).where(Url.id == data["id"]).values(click_count=Url.click_count + 1))
        record_click(db, data["id"], request)
        db.commit()
        return RedirectResponse(url=data["original_url"], status_code=302)
        
    url_row = db.scalar(select(Url).where(Url.short_code == short_code))
    if url_row is None:
        raise HTTPException(status_code=404, detail="Short URL not found")
    if not url_row.is_active:
        raise HTTPException(status_code=410, detail="This link has been deactivated")
    if url_row.expires_at and url_row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="This link has expired")
        
    redis_client.setex(cache_key, CACHE_TTL_SECONDS, json.dumps({
        "id": str(url_row.id),
        "original_url": url_row.original_url,
        "is_active": url_row.is_active,
    }))
    
    db.execute(update(Url).where(Url.id == url_row.id).values(click_count=Url.click_count + 1))
    record_click(db, url_row.id, request)
    db.commit()
    
    return RedirectResponse(url=url_row.original_url, status_code=302)
