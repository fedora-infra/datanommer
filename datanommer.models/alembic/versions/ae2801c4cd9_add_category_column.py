# This file is a part of datanommer, a message sink for fedmsg.
# Copyright (C) 2014, Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
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
