from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.url import Url
from app.utils.short_code import generate_short_code
from sqlalchemy import update
from app.core.shortener import RequestInfo, normalize_url, InvalidUrlError
from app.models.click import Click

MAX_RETRIES = 5

def create_short_url(db: Session, original_url: str, user_id=None, custom_alias: str | None = None, expires_at=None) -> Url:
    try:
        original_url = normalize_url(original_url)
    except InvalidUrlError as e:
        raise ValueError(str(e))
        
    code = custom_alias or generate_short_code()
    for attempt in range(MAX_RETRIES):
        url_row = Url(original_url=original_url, short_code=code, user_id=user_id, expires_at=expires_at)
        db.add(url_row)
        try:
            db.commit()
            db.refresh(url_row)
            return url_row
        except IntegrityError:
            db.rollback()
            if custom_alias:
                raise ValueError(f"Alias '{custom_alias}' is already taken")
            code = generate_short_code()
            # retry with a fresh random code
    raise RuntimeError("Could not generate a unique short code after several attempts")

def resolve_short_url(db: Session, short_code: str, request_info: RequestInfo | None = None) -> Url | None:
    url_row = db.query(Url).filter(Url.short_code == short_code).first()
    if url_row and request_info:
        db.execute(update(Url).where(Url.id == url_row.id).values(click_count=Url.click_count + 1))
        click = Click(
            url_id=url_row.id,
            ip_address=request_info.ip_address,
            country=request_info.country,
            browser=request_info.browser,
            device=request_info.device,
            referrer=request_info.referrer,
        )
        db.add(click)
        db.commit()
    return url_row
