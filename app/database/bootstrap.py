from app.database.session import Base, engine
import app.models  # noqa: F401


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
