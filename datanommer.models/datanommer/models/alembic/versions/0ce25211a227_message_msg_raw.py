"""Rename Message.msg to Message.msg_raw.

This is backwards-incompatible.

Revision ID: 0ce25211a227
Revises: f6d590f5c53f
Create Date: 2024-05-16 14:47:47.180323

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "0ce25211a227"
down_revision = "f6d590f5c53f"


def upgrade():
    # Rename the msg column to msg_raw
    op.alter_column("messages", "msg", new_column_name="msg_raw")


def downgrade():
    op.alter_column("messages", "msg_raw", new_column_name="msg")
