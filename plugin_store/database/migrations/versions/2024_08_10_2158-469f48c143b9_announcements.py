"""empty message

Revision ID: 469f48c143b9
Revises: f5a91a25a410
Create Date: 2024-08-10 21:58:11.798321

"""

import sqlalchemy as sa
from alembic import op

from database import utils

# revision identifiers, used by Alembic.
revision = "469f48c143b9"
down_revision = "f5a91a25a410"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "announcements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("updated", utils.TZDateTime(), nullable=False),
        sa.Column("created", utils.TZDateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("announcements")
    # ### end Alembic commands ###