from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.shortener import UrlShortenerService
from app.database.repository import PostgresShortUrlRepository
from app.database.session import get_db


def get_repository(db: Session = Depends(get_db)) -> PostgresShortUrlRepository:
    return PostgresShortUrlRepository(db)


def get_shortener_service(
    repository: PostgresShortUrlRepository = Depends(get_repository),
) -> UrlShortenerService:
    return UrlShortenerService(repository)
