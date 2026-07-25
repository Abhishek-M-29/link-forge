from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.database.session import get_db
from app.auth.dependencies import get_current_user
from app.models.url import Url
from app.models.click import Click
from app.schemas.analytics import AnalyticsSummary, DailyClicks

router = APIRouter(prefix="/api/v1/urls", tags=["analytics"])

@router.get("/{url_id}/analytics", response_model=AnalyticsSummary)
def get_analytics(url_id: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    url_row = db.get(Url, url_id)
    if url_row is None or url_row.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="URL not found")
        
    total = db.scalar(select(func.count()).select_from(Click).where(Click.url_id == url_id))
    
    daily_rows = db.execute(
        select(func.date(Click.clicked_at), func.count())
        .where(Click.url_id == url_id)
        .group_by(func.date(Click.clicked_at))
        .order_by(func.date(Click.clicked_at))
    ).all()
    
    def top_n(column):
        rows = db.execute(
            select(column, func.count()).where(Click.url_id == url_id).group_by(column)
        ).all()
        return {str(k or "unknown"): v for k, v in rows}
        
    return AnalyticsSummary(
        total_clicks=total or 0,
        daily_clicks=[DailyClicks(date=str(d), clicks=c) for d, c in daily_rows],
        top_browsers=top_n(Click.browser),
        top_devices=top_n(Click.device),
        top_referrers=top_n(Click.referrer),
    )
