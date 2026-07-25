import sys
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.url import Url
from app.database.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

db.query(Url).filter(Url.short_code.in_(["valid1", "deact1", "expir1"])).delete(synchronize_session=False)

u1 = Url(original_url="https://valid.com", short_code="valid1", is_active=True)
u2 = Url(original_url="https://deact.com", short_code="deact1", is_active=False)
u3 = Url(original_url="https://expir.com", short_code="expir1", is_active=True, expires_at=datetime.now(timezone.utc) - timedelta(days=1))

db.add_all([u1, u2, u3])
db.commit()
print("Test URLs inserted")
