from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request, status

from app.core.shortener import RequestInfo
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services import url_service
from app.schemas.url import (
    GenerateRequest,
    GenerateResponse,
    ResolveResponse,
    ShortUrlLookupResponse,
)


router = APIRouter()
ShortCodePath = Annotated[
    str,
    Path(
        ...,
        min_length=1,
        max_length=32,
        pattern=r"^[0-9a-zA-Z]+$",
        description="Base62 short code",
    ),
]


def _extract_request_info(request: Request) -> RequestInfo:
    return RequestInfo(
        ip_address=request.client.host if request.client else None,
        browser=request.headers.get("user-agent"),
        referrer=request.headers.get("referer"),
        # To accurately get country and device, we would typically use an IP geolocation DB 
        # and User-Agent parser, but for now we just extract the basic available data.
        country=None,
        device=None,
    )


@router.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_201_CREATED)
def generate_short_url(
    payload: GenerateRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> GenerateResponse:
    record = url_service.create_short_url(db, str(payload.url))
    return GenerateResponse(
        id=record.id,
        original_url=record.original_url,
        short_code=record.short_code,
        short_url=str(request.base_url).rstrip("/") + f"/{record.short_code}",
    )


@router.get("/resolve/{short_code}", response_model=ResolveResponse)
def resolve_short_url(
    short_code: ShortCodePath,
    request: Request,
    db: Session = Depends(get_db),
) -> ResolveResponse:
    request_info = _extract_request_info(request)
    record = url_service.resolve_short_url(db, short_code, request_info=request_info)
    if not record:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Short code not found")
    return ResolveResponse(
        id=record.id,
        original_url=record.original_url,
        short_code=record.short_code,
    )


@router.get("/{short_code}", response_model=ShortUrlLookupResponse)
def lookup_short_url(
    short_code: ShortCodePath,
    request: Request,
    db: Session = Depends(get_db),
) -> ShortUrlLookupResponse:
    request_info = _extract_request_info(request)
    record = url_service.resolve_short_url(db, short_code, request_info=request_info)
    if not record:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Short code not found")
    return ShortUrlLookupResponse(
        short_code=record.short_code,
        original_url=record.original_url,
        short_url=str(request.base_url).rstrip("/") + f"/{record.short_code}",
    )
