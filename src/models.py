import uuid
from datetime import datetime

from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyBaseOAuthAccountTableUUID
from sqlalchemy import TIMESTAMP, Identity, JSON, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Role(Base):
    __tablename__ = "role"

    id: Mapped[int] = mapped_column(Identity(increment=1, always=True), primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    permissions = mapped_column(JSON, nullable=True)

    users: Mapped[list["User"]] = relationship(back_populates="role", lazy='joined')


class OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, Base):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    logs: Mapped[list["Logs"]] = relationship(back_populates="user", lazy='joined')
    role_id: Mapped[int] = mapped_column(ForeignKey("role.id"))
    role: Mapped["Role"] = relationship(back_populates="users", lazy='joined')
    oauth_accounts: Mapped[list[OAuthAccount]] = relationship(
        "OAuthAccount", lazy="joined"
    )
    pass


class Logs(Base):
    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(Identity(increment=1, always=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"))
    user: Mapped[User] = relationship(back_populates="logs", lazy='joined')
    winner_id: Mapped[int] = mapped_column(nullable=False)
    loser_id: Mapped[int] = mapped_column(nullable=False)
    total_rounds: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=func.now())
