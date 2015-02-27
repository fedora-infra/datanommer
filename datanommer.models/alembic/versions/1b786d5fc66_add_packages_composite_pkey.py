"""Add packages composite pkey

Revision ID: 1b786d5fc66
Revises: 19bb834d6f9
Create Date: 2015-02-27 15:04:57.632787

"""

# revision identifiers, used by Alembic.
revision = '1b786d5fc66'
down_revision = '19bb834d6f9'

import time
import logging

from alembic import op
import sqlalchemy as sa

log = logging.getLogger('alembic.migration')


def upgrade():
    start = time.time()
    engine = op.get_bind().engine
    try:
        cols = ['package', 'msg']
        for col in cols:
            query = "DELETE FROM package_messages WHERE %s is NULL" % col
            log.info("Running %r", query)
            engine.execute(sa.sql.text(query))

        log.info("Creating composite primary key")
        op.create_primary_key('package_messages_pkey', 'package_messages', cols)
    finally:
        log.info("Finished in %0.2fs", time.time() - start)

def downgrade():
    start = time.time()
    try:
        op.drop_constraint('package_messages_pkey', 'package_messages')
    finally:
        log.info("Finished in %0.2fs", time.time() - start)
