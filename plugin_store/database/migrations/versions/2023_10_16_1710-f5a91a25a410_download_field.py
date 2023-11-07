"""add download and update fields

Revision ID: f5a91a25a410
Revises: 00b050c80d6d
Create Date: 2023-10-16 17:10:46.948405

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f5a91a25a410"
down_revision = "00b050c80d6d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("versions", sa.Column("downloads", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("versions", sa.Column("updates", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("versions", "updates")
    op.drop_column("versions", "downloads")
