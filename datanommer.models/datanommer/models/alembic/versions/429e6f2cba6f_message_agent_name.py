"""Message.username → Message.agent_name

Revision ID: 429e6f2cba6f
Revises: 951c40020acc
Create Date: 2024-06-07 09:12:33.393757

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "429e6f2cba6f"
down_revision = "f6918385051f"


def upgrade():
    op.alter_column("messages", "username", new_column_name="agent_name")
    op.create_index(op.f("ix_messages_agent_name"), "messages", ["agent_name"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_messages_agent_name"), table_name="messages")
    op.alter_column("messages", "agent_name", new_column_name="username")
