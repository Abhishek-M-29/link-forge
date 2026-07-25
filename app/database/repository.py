import uuid
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import update

from app.core.shortener import (
    RequestInfo,
    ShortCodeCollisionError,
    ShortUrl,
    ShortUrlRepository,
)
from app.models.click import Click
from app.models.url import Url


class PostgresShortUrlRepository(ShortUrlRepository):
    """SQLAlchemy ORM repository backed by PostgreSQL."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, original_url: str, short_code: str) -> ShortUrl:
        db_url = Url(
            original_url=original_url,
            short_code=short_code,
        )
        self.db.add(db_url)
        try:
            self.db.commit()
            self.db.refresh(db_url)
        except IntegrityError as e:
            self.db.rollback()
            # If the integrity error is due to a short code collision, we raise the specific error.
            if "ix_urls_short_code" in str(e) or "unique constraint" in str(e).lower():
                # We could have a collision on original_url if we added a unique constraint to it, 
                # but currently Url model has unique=True on short_code.
                raise ShortCodeCollisionError("Short code already exists.")
            raise

        return self._map_to_domain(db_url)

    def get_by_id(self, record_id: uuid.UUID) -> Optional[ShortUrl]:
        db_url = self.db.query(Url).filter(Url.id == record_id).first()
        if not db_url:
            return None
        return self._map_to_domain(db_url)

    def get_by_short_code(self, short_code: str) -> Optional[ShortUrl]:
        db_url = self.db.query(Url).filter(Url.short_code == short_code).first()
        if not db_url:
            return None
        return self._map_to_domain(db_url)

    def get_by_original_url(self, original_url: str) -> Optional[ShortUrl]:
        db_url = self.db.query(Url).filter(Url.original_url == original_url).first()
        if not db_url:
            return None
        return self._map_to_domain(db_url)

    def record_click(self, url_id: uuid.UUID, request_info: RequestInfo) -> None:
        db_url = self.db.query(Url).filter(Url.id == url_id).first()
        if not db_url:
            raise ValueError(f"URL with id {url_id} not found")
            
        self.db.execute(update(Url).where(Url.id == url_id).values(click_count=Url.click_count + 1))
        click = Click(
            url_id=url_id,
            ip_address=request_info.ip_address,
            country=request_info.country,
            browser=request_info.browser,
            device=request_info.device,
            referrer=request_info.referrer,
        )
        self.db.add(click)
        self.db.commit()

    @staticmethod
    def _map_to_domain(db_url: Url) -> ShortUrl:
        return ShortUrl(
            id=db_url.id,
            original_url=db_url.original_url,
            short_code=db_url.short_code,
            created_at=db_url.created_at,
        )
