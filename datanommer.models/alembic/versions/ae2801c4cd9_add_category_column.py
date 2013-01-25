"""add category column

Revision ID: ae2801c4cd9
Revises: 198447250956
Create Date: 2013-01-22 10:43:35.457862

"""

# revision identifiers, used by Alembic.
revision = 'ae2801c4cd9'
down_revision = '198447250956'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('messages', sa.Column('category', sa.UnicodeText))


def downgrade():
    op.drop_column('messages', 'category')
