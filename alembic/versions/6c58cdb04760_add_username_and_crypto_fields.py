"""Add username and crypto fields.

Revision ID: 6c58cdb04760
Revises: a356c9a10463
Create Date: 2017-08-09 20:19:10.441599

"""

import logging
import time

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "6c58cdb04760"
down_revision = "a356c9a10463"


log = logging.getLogger("alembic.migration")


def upgrade():
    start = time.time()
    try:
        op.add_column(
            "messages", sa.Column("username", sa.UnicodeText(), nullable=True)
        )
        op.add_column("messages", sa.Column("crypto", sa.UnicodeText(), nullable=True))
    finally:
        log.info("Finished in %0.2fs", time.time() - start)


def downgrade():
    start = time.time()
    try:
        op.drop_column("messages", "username")
        op.drop_column("messages", "crypto")
    finally:
        log.info("Finished in %0.2fs", time.time() - start)
