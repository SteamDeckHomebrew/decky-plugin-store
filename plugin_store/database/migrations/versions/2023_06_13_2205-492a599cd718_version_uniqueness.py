"""empty message

Revision ID: 492a599cd718
Revises: abe90daeb874
Create Date: 2023-06-13 22:05:19.849032

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "492a599cd718"
down_revision = "abe90daeb874"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("artifacts") as batch_op_artifacts:
        batch_op_artifacts.alter_column(
            "visible",
            existing_type=sa.BOOLEAN(),
            nullable=True,
            existing_server_default=sa.text("'1'"),  # type: ignore[arg-type]
        )
    with op.batch_alter_table("versions") as batch_op_versions:
        batch_op_versions.add_column(sa.Column("file", sa.Text(), nullable=True))
        batch_op_versions.create_unique_constraint(
            "unique_version_artifact_id_name",
            ["artifact_id", "name"],
        )


def downgrade() -> None:
    with op.batch_alter_table("versions") as batch_op_versions:
        batch_op_versions.drop_constraint(
            "unique_version_artifact_id_name",
            type_="unique",
        )
        batch_op_versions.drop_column("file")
    with op.batch_alter_table("artifacts") as batch_op_artifacts:
        batch_op_artifacts.alter_column(
            "visible",
            existing_type=sa.BOOLEAN(),
            nullable=False,
            existing_server_default=sa.text("'1'"),  # type: ignore[arg-type]
        )
