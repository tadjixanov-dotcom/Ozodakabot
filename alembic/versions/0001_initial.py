"""Boshlang'ich sxema — barcha jadvallar.

Revision ID: 0001
Revises:
Create Date: 2026-07-20

Eslatma: boshlang'ich migratsiya modellardagi metadata orqali yaratiladi.
Keyingi o'zgarishlar uchun `alembic revision --autogenerate` ishlating.
"""
from alembic import op

from app.database.models import Base

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
