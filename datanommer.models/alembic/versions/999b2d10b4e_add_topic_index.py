"""Add topic index

Revision ID: 999b2d10b4e
Revises: 143ec484f5ba
Create Date: 2015-02-27 14:31:46.610136

"""

# revision identifiers, used by Alembic.
revision = '999b2d10b4e'
down_revision = '143ec484f5ba'

import time
import logging

from alembic import op
import sqlalchemy as sa

log = logging.getLogger('alembic.migration')


def upgrade():
    start = time.time()
    try:
        op.create_index('index_msg_topic', 'messages', ['topic'])
    finally:
        log.info("Finished in %0.2fs", time.time() - start)

def downgrade():
    start = time.time()
    try:
        op.drop_index('index_msg_topic')
    finally:
        log.info("Finished in %0.2fs", time.time() - start)
