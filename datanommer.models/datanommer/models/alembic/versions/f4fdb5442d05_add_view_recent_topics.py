"""Add view recent_topics

Revision ID: f4fdb5442d05
Revises: 429e6f2cba6f
Create Date: 2025-05-30 13:52:11.648140

"""

# revision identifiers, used by Alembic.
revision = "f4fdb5442d05"
down_revision = "429e6f2cba6f"

from alembic import op  # noqa: E402

from datanommer.models.view import CreateMaterializedView, get_selectable  # noqa: E402


def upgrade():

    # Create the materialized view using the factored selectable
    selectable = get_selectable()
    op.execute(CreateMaterializedView("recent_topics", selectable))

    # Create unique index on topic
    op.create_index(
        "uq_recent_topics_topic", "recent_topics", ["topic"], unique=True, if_not_exists=True
    )

    # Create index on message_count for sorting
    op.create_index(
        "ix_recent_topics_message_count", "recent_topics", ["message_count"], if_not_exists=True
    )


def downgrade():
    op.execute("DROP MATERIALIZED VIEW IF EXISTS recent_topics")
