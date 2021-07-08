"""Add users composite pkey

Revision ID: 19bb834d6f9
Revises: 5a167589eb8e
Create Date: 2015-02-27 14:47:46.001824

"""

import logging
import time

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "19bb834d6f9"
down_revision = "5a167589eb8e"


log = logging.getLogger("alembic.migration")


def upgrade():
    start = time.time()
    engine = op.get_bind().engine
    try:
        cols = ["username", "msg"]
        for col in cols:
            query = "DELETE FROM user_messages WHERE %s is NULL" % col  # nosec
            log.info("Running %r", query)
            engine.execute(sa.sql.text(query))

        log.info("Creating composite primary key")
        op.create_primary_key("user_messages_pkey", "user_messages", cols)
    finally:
        log.info("Finished in %0.2fs", time.time() - start)


def downgrade():
    start = time.time()
    try:
        op.drop_constraint("user_messages_pkey", "user_messages")
    finally:
        log.info("Finished in %0.2fs", time.time() - start)
