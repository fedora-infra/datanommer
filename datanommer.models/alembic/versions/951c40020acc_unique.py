"""Add a unique index on packages and users

Revision ID: 951c40020acc
Revises: 5db25abc63be
Create Date: 2021-09-22 15:38:57.339646
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "951c40020acc"
down_revision = "5db25abc63be"


def upgrade():
    op.drop_index("ix_packages_name", table_name="packages")
    op.create_index(op.f("ix_packages_name"), "packages", ["name"], unique=True)
    op.drop_index("ix_users_name", table_name="users")
    op.create_index(op.f("ix_users_name"), "users", ["name"], unique=True)


def downgrade():
    op.drop_index(op.f("ix_users_name"), table_name="users")
    op.create_index("ix_users_name", "users", ["name"], unique=False)
    op.drop_index(op.f("ix_packages_name"), table_name="packages")
    op.create_index("ix_packages_name", "packages", ["name"], unique=False)
