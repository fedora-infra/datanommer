"""Add category index

Revision ID: 5a167589eb8e
Revises: 999b2d10b4e
Create Date: 2015-02-27 14:45:41.777456

"""

# revision identifiers, used by Alembic.
revision = '5a167589eb8e'
down_revision = '999b2d10b4e'

import time
import logging

from alembic import op
import sqlalchemy as sa

log = logging.getLogger('alembic.migration')


def upgrade():
    start = time.time()
    try:
        op.create_index('index_msg_category', 'messages', ['category'])
    finally:
        log.info("Finished in %0.2fs", time.time() - start)

def downgrade():
    start = time.time()
    try:
        op.drop_index('index_msg_category')
    finally:
        log.info("Finished in %0.2fs", time.time() - start)
