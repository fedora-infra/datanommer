"""store headers

Revision ID: a356c9a10463
Revises: 1b786d5fc66
Create Date: 2017-05-09 16:03:29.944652

"""

# revision identifiers, used by Alembic.
revision = 'a356c9a10463'
down_revision = '1b786d5fc66'

import time
import logging

from alembic import op
import sqlalchemy as sa

log = logging.getLogger('alembic.migration')

def upgrade():
    start = time.time()
    try:
        op.add_column('messages', sa.Column('_headers', sa.UnicodeText(), nullable=True))
    finally:
        log.info("Finished in %0.2fs", time.time() - start)

def downgrade():
    start = time.time()
    try:
        op.drop_column('messages', '_headers')
    finally:
        log.info("Finished in %0.2fs", time.time() - start)
