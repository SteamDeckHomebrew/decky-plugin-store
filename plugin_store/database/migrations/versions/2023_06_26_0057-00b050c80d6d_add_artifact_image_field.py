"""add artifact image field

Revision ID: 00b050c80d6d
Revises: 492a599cd718
Create Date: 2023-06-26 00:57:41.153757

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "00b050c80d6d"
down_revision = "492a599cd718"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("artifacts", sa.Column("image_path", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("artifacts", "image_path")
