"""Add msg_id column

Revision ID: 143ec484f5ba
Revises: 2affa1daa804
Create Date: 2013-09-05 21:34:12.915709

"""

# revision identifiers, used by Alembic.
revision = '143ec484f5ba'
down_revision = '2affa1daa804'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('messages', sa.Column('msg_id', sa.UnicodeText, nullable=True,
                                        unique=True, default=None))
    pass


def downgrade():
    op.drop_column('messages', 'msg_id')
    pass
