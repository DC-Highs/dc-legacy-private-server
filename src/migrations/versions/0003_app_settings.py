"""app settings

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-22 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('app_settings',
    sa.Column('key', sa.String(length=64), nullable=False),
    sa.Column('value', sa.String(length=255), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('key')
    )


def downgrade() -> None:
    op.drop_table('app_settings')
