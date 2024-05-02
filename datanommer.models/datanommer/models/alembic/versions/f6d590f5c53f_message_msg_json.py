"""Create the Message.msg_json column and index it.

Revision ID: f6d590f5c53f
Revises: f6918385051f
Create Date: 2024-05-02 14:38:38.399397

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "f6d590f5c53f"
down_revision = "f6918385051f"


def upgrade():
    op.add_column(
        "messages",
        sa.Column(
            "msg_json", postgresql.JSONB(none_as_null=True, astext_type=sa.Text()), nullable=True
        ),
    )
    op.create_index(
        "ix_messages_msg_json_root",
        "messages",
        ["msg_json"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"msg_json": "jsonb_path_ops"},
    )
    # Make the msg column nullable so that the populate-json script can run
    op.alter_column("messages", "msg", nullable=True)


def downgrade():
    op.alter_column("messages", "msg", nullable=False)
    op.drop_index("ix_messages_msg_json_root", table_name="messages", postgresql_using="gin")
    op.drop_column("messages", "msg_json")
