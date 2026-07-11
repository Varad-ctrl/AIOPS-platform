"""
Role model - backs Role-Based Access Control (RBAC).

Three roles ship by default: admin, devops_engineer, viewer. Seeded by
app/db/init_db.py on startup.
"""
import enum

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class RoleName(str, enum.Enum):
    ADMIN = "admin"
    DEVOPS_ENGINEER = "devops_engineer"
    VIEWER = "viewer"


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), default="")

    users: Mapped[list["User"]] = relationship(back_populates="role")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Role id={self.id} name={self.name!r}>"
