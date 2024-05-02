"""Messages.headers index

Revision ID: f6918385051f
Revises: 951c40020acc
Create Date: 2024-05-07 16:05:05.344863

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "f6918385051f"
down_revision = "951c40020acc"


def upgrade():
    op.create_index(
        "ix_messages_headers",
        "messages",
        ["headers"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"headers": "jsonb_path_ops"},
    )


def downgrade():
    op.drop_index("ix_messages_headers", table_name="messages", postgresql_using="gin")
