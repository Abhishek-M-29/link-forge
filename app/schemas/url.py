import uuid
from typing import Annotated
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator


class GenerateRequest(BaseModel):
    url: Annotated[HttpUrl, Field(max_length=2048)]


class GenerateResponse(BaseModel):
    id: uuid.UUID
    original_url: str
    short_code: str
    short_url: str


class ResolveResponse(BaseModel):
    id: uuid.UUID
    original_url: str
    short_code: str


class ShortUrlLookupResponse(BaseModel):
    short_code: str
    original_url: str
    short_url: str


class UrlCreateRequest(BaseModel):
    original_url: HttpUrl
    custom_alias: str | None = None
    expires_at: datetime | None = None

    @field_validator("custom_alias")
    @classmethod
    def alias_is_url_safe(cls, v):
        if v and not v.isalnum():
            raise ValueError("custom_alias must be alphanumeric")
        return v

class UrlResponse(BaseModel):
    id: str
    short_code: str
    short_url: str
    original_url: str
    is_active: bool
    click_count: int
    expires_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True

class UrlUpdateRequest(BaseModel):
    original_url: HttpUrl | None = None
    is_active: bool | None = None
    expires_at: datetime | None = None
