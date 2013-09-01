"""Fix git topics as follows:

git.branch.* => git.branch
git.lookaside.*.new => git.lookaside.new
git.receive.* => git.receive

There is no downgrade section as this is not a schema change. This revision
cannot be reversed.

Revision ID: 2affa1daa804
Revises: 310c88783271
Create Date: 2013-09-01 10:58:03.127503

"""

# revision identifiers, used by Alembic.
revision = '2affa1daa804'
down_revision = '310c88783271'

from alembic import op
import sqlalchemy as sa

import datanommer.models as m


def upgrade():
    engine = op.get_bind().engine
    m.init(engine=engine)

    # git.branch
    branch = m.Message.topic.like(u'%.git.branch.%')
    for msg in m.Message.query.filter(branch).yield_per(100):
        prefix, suffix = msg.topic.split(u'.git.branch.')
        msg.topic = prefix + '.git.branch'
        m.session.add(msg)

    # git.lookaside.*.new
    lookaside = m.Message.topic.like(u'%.git.lookaside.%.new')
    for msg in m.Message.query.filter(lookaside).yield_per(100):
        prefix, suffix = msg.topic.split(u'.git.lookaside.')
        msg.topic = prefix + '.git.lookaside.new'
        m.session.add(msg)

    # git.receive
    receive = m.Message.topic.like(u'%.git.receive.%')
    for msg in m.Message.query.filter(receive).yield_per(100):
        prefix, suffix = msg.topic.split(u'.git.receive.')
        msg.topic = prefix + '.git.receive'
        m.session.add(msg)

    m.session.commit()


def downgrade():
    pass
