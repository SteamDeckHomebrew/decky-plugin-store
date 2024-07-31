"""initial db setup

Revision ID: abe90daeb874
Revises: 4fc55239b4d6
Create Date: 2022-11-19 18:23:52.915293

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "abe90daeb874"
down_revision = "642324500b07"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("artifacts", sa.Column("visible", sa.Boolean(), server_default="1", nullable=True))
    with op.batch_alter_table("artifacts") as batch_op:
        batch_op.alter_column("visible", nullable=False)  # type: ignore[attr-defined]


def downgrade() -> None:
    op.drop_column("artifacts", "visible")
