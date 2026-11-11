# Modelo de datos User - SQLModel
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime, func
from datetime import datetime, timezone
from uuid import UUID, uuid4



def tz_column(**kwargs) -> Column:
    """Columna de fecha con zona horaria (se compara con datetime.now(timezone.utc))."""
    return Column(DateTime(timezone=True), nullable=True, **kwargs)


class User(SQLModel, table=True):
    # Los FKs de lots / lot_versions apuntan a "users.id"
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(index=True, unique=True, max_length=255)
    hashed_password: str
    full_name: str | None = None
    is_active: bool = True
    last_login: datetime | None = Field(default=None, sa_column=tz_column())
    deleted_at: datetime | None = Field(default=None, sa_column=tz_column())

    # Email verification
    email_verified: bool = Field(default=False)
    verification_token: str | None = Field(default=None, index=True)
    verification_token_expires: datetime | None = Field(default=None, sa_column=tz_column())

    # Password reset
    reset_token: str | None = Field(default=None, index=True)
    reset_token_expires: datetime | None = Field(default=None, sa_column=tz_column())

    # Refresh token vigente (rotación: al emitir uno nuevo el anterior queda inválido)
    refresh_token_jti: str | None = Field(default=None, max_length=64)

    # Login attempt control
    failed_login_attempts: int = Field(default=0)
    locked_until: datetime | None = Field(default=None, sa_column=tz_column())

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

    def verify_password(self, plain_password: str) -> bool:
        from app.core.security import verify_password
        return verify_password(plain_password, self.hashed_password)
    
    def is_locked(self) -> bool:
        """Verifica si la cuenta está bloqueada temporalmente."""
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until
    
    def record_failed_login(self) -> None:
        """Registra un intento fallido de login."""
        self.failed_login_attempts += 1
        # Bloquear después de 5 intentos fallidos por 15 minutos
        if self.failed_login_attempts >= 5:
            from datetime import timedelta
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    def reset_failed_logins(self) -> None:
        """Resetea contadores de login fallido tras éxito."""
        self.failed_login_attempts = 0
        self.locked_until = None