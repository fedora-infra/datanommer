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
"""category not null

Revision ID: 5091535d0fb4
Revises: a4f74590bcf
Create Date: 2013-02-23 23:31:48.450673

"""

# revision identifiers, used by Alembic.
revision = '5091535d0fb4'
down_revision = 'a4f74590bcf'

from alembic import op


def upgrade():
    op.alter_column("messages", "category", nullable=False)


def downgrade():
    op.alter_column("messages", "category", nullable=True)
