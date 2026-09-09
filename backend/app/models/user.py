# Modelo de datos User - SQLModel
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone


class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda str: str(__import__("uuid").uuid4()), primary_key=True)
    email: str
    hashed_password: str
    full_name: str | None = None
    is_active: bool = True
    last_login: datetime | None = Field(default=None)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def verify_password(self, plain_password: str) -> bool:
        from app.core.security import verify_password
        return verify_password(plain_password, self.hashed_password)