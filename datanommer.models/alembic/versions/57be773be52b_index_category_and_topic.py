"""Add index to category and topic

Revision ID: 57be773be52b
Revises: 6c58cdb04760
Create Date: 2017-10-11 23:37:47.682954

"""

# revision identifiers, used by Alembic.
revision = '57be773be52b'
down_revision = '6c58cdb04760'

from alembic import op
import sqlalchemy as sa

# SQL commands:
# CREATE INDEX messages_topic_id ON messages (topic);
# CREATE INDEX messages_category_id ON messages (category);


def upgrade():
    """ Creates an index on messages.category, messages.topic and
    messages.username
    """
    op.create_index('messages_topic_id', 'messages', 'topic')
    op.create_index('messages_category_id', 'messages', 'category')


def downgrade():
    """ Removes the index on messages.category, messages.topic and
    messages.username
    """
    op.drop_index('messages_topic_id', 'messages')
    op.drop_index('messages_category_id', 'messages')
