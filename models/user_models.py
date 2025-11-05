from sqlalchemy import (
    Table,UniqueConstraint,
    Column, Integer, String, Boolean, DateTime, Date, DECIMAL, Text, Enum, ForeignKey, MetaData
)
from models.admin_models import metadata

# -- User table --
user = Table(
    "user",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(255), unique=True, nullable=False, index=True),
    Column("name", String(255), nullable=False),
    Column("surname", String(255), nullable=False),
    Column("password", String(255), nullable=False),
    Column("is_active", Boolean, default=True),
    Column("is_admin", Boolean, default=False),
    Column("is_staff", Boolean, default=False),
    Column("is_superuser", Boolean, default=False)
)



# -- VerificationCode table --
verification_code = Table(
    "verification_code",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "user_id",
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False
    ),
    Column("code", String(10), nullable=False),
    Column("type", String(50), nullable=False),
    UniqueConstraint("user_id", "type", name="unique_user_code")
)