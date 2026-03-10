from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models import user, workspace, record, billing  # noqa: E402,F401

