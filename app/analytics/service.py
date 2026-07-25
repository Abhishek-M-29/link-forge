from sqlalchemy.orm import Session
from app.models.click import Click
from app.analytics.parser import extract_browser_and_device

def record_click(db: Session, url_id, request) -> None:
    browser, device = extract_browser_and_device(request.headers.get("user-agent", ""))
    click = Click(
        url_id=url_id,
        ip_address=request.client.host if request.client else None,
        browser=browser,
        device=device,
        referrer=request.headers.get("referer"),
    )
    db.add(click)
