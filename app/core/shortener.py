"""Core URL shortener primitives using cryptographically secure random tokens.

This module is intentionally framework-agnostic so it can serve as the core
domain/service layer for a future backend.
"""

from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Protocol
from urllib.parse import urlparse


SHORT_CODE_LENGTH = 7


class ShortenerError(Exception):
    """Base exception for shortener-related failures."""


class InvalidUrlError(ShortenerError):
    """Raised when a URL is malformed or unsupported."""


class InvalidShortCodeError(ShortenerError):
    """Raised when a short code cannot be decoded."""


class ShortCodeNotFoundError(ShortenerError):
    """Raised when no record exists for a decoded short code."""


class ShortCodeCollisionError(ShortenerError):
    """Raised when a generated short code already exists in the database."""


@dataclass(slots=True)
class ShortUrl:
    """Represents a stored shortened URL record."""

    id: uuid.UUID
    original_url: str
    short_code: str
    created_at: datetime


@dataclass(slots=True)
class RequestInfo:
    """Information about the client request for tracking clicks."""

    ip_address: Optional[str] = None
    country: Optional[str] = None
    browser: Optional[str] = None
    device: Optional[str] = None
    referrer: Optional[str] = None


class ShortUrlRepository(Protocol):
    """Persistence contract for the URL shortener core."""

    def create(self, original_url: str, short_code: str) -> ShortUrl:
        """Create a record and return it."""

    def get_by_id(self, record_id: uuid.UUID) -> Optional[ShortUrl]:
        """Return a record for the given database ID, if present."""

    def get_by_short_code(self, short_code: str) -> Optional[ShortUrl]:
        """Return a record for the given short code, if present."""

    def get_by_original_url(self, original_url: str) -> Optional[ShortUrl]:
        """Return an existing record for the same original URL, if present."""

    def record_click(self, url_id: uuid.UUID, request_info: RequestInfo) -> None:
        """Record a click event for the given URL ID."""


def normalize_url(url: str) -> str:
    """Validate and normalize a URL before storing it."""
    candidate = url.strip()
    parsed = urlparse(candidate)

    if parsed.scheme not in {"http", "https"}:
        raise InvalidUrlError("URL must start with http:// or https://")
    if not parsed.netloc:
        raise InvalidUrlError("URL must include a valid host.")

    return candidate


class UrlShortenerService:
    """Domain service for creating and resolving short URLs."""

    def __init__(self, repository: ShortUrlRepository) -> None:
        self.repository = repository

    def shorten(self, original_url: str, *, deduplicate: bool = True) -> ShortUrl:
        """Create or reuse a short URL for the given original URL."""
        normalized_url = normalize_url(original_url)

        if deduplicate:
            existing = self.repository.get_by_original_url(normalized_url)
            if existing is not None:
                return existing

        # Retry logic for collisions
        for _ in range(5):
            short_code = secrets.token_urlsafe(SHORT_CODE_LENGTH)[:SHORT_CODE_LENGTH]
            try:
                return self.repository.create(normalized_url, short_code)
            except ShortCodeCollisionError:
                continue

        raise ShortenerError("Could not generate a unique short code after multiple attempts.")

    def resolve(self, short_code: str, request_info: Optional[RequestInfo] = None) -> ShortUrl:
        """Resolve a short code back to its stored URL record."""
        record = self.repository.get_by_short_code(short_code)
        if record is None:
            raise ShortCodeNotFoundError(f"No URL found for short code: {short_code}")
        
        if request_info:
            self.repository.record_click(record.id, request_info)
            
        return record

    def build_short_url(self, short_code: str, base_url: str) -> str:
        """Combine a short code with a configured public base URL."""
        clean_base = base_url.rstrip("/")
        if not clean_base:
            raise ValueError("base_url cannot be empty")
        return f"{clean_base}/{short_code}"


class InMemoryShortUrlRepository:
    """Tiny in-memory repository useful for tests and local experimentation."""

    def __init__(self) -> None:
        self._records: dict[uuid.UUID, ShortUrl] = {}
        self._original_to_id: dict[str, uuid.UUID] = {}
        self._short_code_to_id: dict[str, uuid.UUID] = {}

    def create(self, original_url: str, short_code: str) -> ShortUrl:
        if short_code in self._short_code_to_id:
            raise ShortCodeCollisionError(f"Short code {short_code} already exists.")
            
        record_id = uuid.uuid4()
        record = ShortUrl(
            id=record_id,
            original_url=original_url,
            short_code=short_code,
            created_at=datetime.now(timezone.utc),
        )
        self._records[record_id] = record
        self._original_to_id[original_url] = record_id
        self._short_code_to_id[short_code] = record_id
        return record

    def get_by_id(self, record_id: uuid.UUID) -> Optional[ShortUrl]:
        return self._records.get(record_id)

    def get_by_short_code(self, short_code: str) -> Optional[ShortUrl]:
        record_id = self._short_code_to_id.get(short_code)
        if record_id is None:
            return None
        return self._records.get(record_id)

    def get_by_original_url(self, original_url: str) -> Optional[ShortUrl]:
        record_id = self._original_to_id.get(original_url)
        if record_id is None:
            return None
        return self._records.get(record_id)

    def record_click(self, url_id: uuid.UUID, request_info: RequestInfo) -> None:
        pass
