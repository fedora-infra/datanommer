"""add source columns

Revision ID: 4391ce7dc184
Revises: 1d4feffd78fe
Create Date: 2013-08-10 16:32:39.466582

"""

# revision identifiers, used by Alembic.
revision = '4391ce7dc184'
down_revision = '1d4feffd78fe'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('messages', sa.Column('source_name', sa.UnicodeText))
    op.add_column('messages', sa.Column('source_version', sa.UnicodeText))


def downgrade():
    op.drop_column('messages', 'source_name')
    op.drop_column('messages', 'source_version')
