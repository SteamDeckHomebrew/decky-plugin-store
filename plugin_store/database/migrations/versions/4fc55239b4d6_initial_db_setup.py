"""initial db setup

Revision ID: 4fc55239b4d6
Revises: 
Create Date: 2022-11-07 01:36:59.727609

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4fc55239b4d6"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "artifacts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("author", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tag", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "plugin_tag",
        sa.Column("artifact_id", sa.Integer(), nullable=True),
        sa.Column("tag_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(("artifact_id",), ["artifacts.id"]),
        sa.ForeignKeyConstraint(("tag_id",), ["tags.id"]),
    )
    op.create_table(
        "versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("artifact_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("hash", sa.Text(), nullable=True),
        sa.Column("added_on", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(("artifact_id",), ["artifacts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("versions")
    op.drop_table("plugin_tag")
    op.drop_table("tags")
    op.drop_table("artifacts")
