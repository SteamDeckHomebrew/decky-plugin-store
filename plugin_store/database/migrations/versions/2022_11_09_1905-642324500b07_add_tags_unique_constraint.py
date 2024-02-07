"""add-tags-unique-constraint

Revision ID: 642324500b07
Revises: 4fc55239b4d6
Create Date: 2022-11-09 19:05:26.487490

"""
import sqlalchemy as sa
from alembic import op

from database.models import Artifact, PluginTag, Tag

# revision identifiers, used by Alembic.
revision = "642324500b07"
down_revision = "4fc55239b4d6"
branch_labels = None
depends_on = None


def upgrade() -> None:

    conn = op.get_bind()
    statement = sa.select(Tag.tag, sa.func.string_agg(str(Tag.id), ",").label("ids")).group_by(Tag.tag)
    tags = conn.execute(statement)
    replacements = {(ids[0], tag.tag): ids[1:] for tag in tags if len(ids := sorted(map(int, tag.ids.split(",")))) > 1}
    for (dest_id, tag), src_ids in replacements.items():
        # Fetch all plugins relating to any of src_ids
        get_matching_plugins = (
            sa.select(Artifact)
            .join(PluginTag)
            .where(
                PluginTag.c.tag_id.in_(src_ids),
                Artifact.id.not_in(sa.select(Artifact.id).join(PluginTag).where(PluginTag.c.tag_id == dest_id)),
            )
            .distinct()
        )
        plugins = list(conn.execute(get_matching_plugins).scalars().all())

        op.bulk_insert(PluginTag, [{"artifact_id": plugin_id, "tag_id": dest_id} for plugin_id in plugins])

        conn.execute(sa.delete(PluginTag).where(PluginTag.c.tag_id.in_(src_ids)))
        conn.execute(sa.delete(Tag).where(Tag.id.in_(src_ids)))

        # Remove all relations matching src_ids (ignore things fetched above)

    with op.batch_alter_table(Tag.__table__) as batch_op:  # type: ignore[arg-type]
        batch_op.create_unique_constraint("unique_tag_tag", ["tag"])  # type: ignore[attr-defined]


def downgrade() -> None:
    with op.batch_alter_table(Tag.__table__) as batch_op:  # type: ignore[arg-type]
        batch_op.drop_constraint("unique_tag_tag", type_="unique")  # type: ignore[attr-defined]
