"""add download and update field

Revision ID: 91da3fef8793
Revises: 00b050c80d6d
Create Date: 2023-10-15 16:18:53.721007

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "91da3fef8793"
down_revision = "00b050c80d6d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("artifacts", sa.Column("downloads", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("artifacts", sa.Column("updates", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("artifacts", "updates")
    op.drop_column("artifacts", "downloads")
