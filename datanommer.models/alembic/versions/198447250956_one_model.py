"""one model

Revision ID: 198447250956
Revises: None
Create Date: 2013-01-14 11:14:04.738115

"""

# revision identifiers, used by Alembic.
revision = '198447250956'
down_revision = None

from alembic import op
import sqlalchemy as sa

from sqlalchemy.schema import MetaData
from sqlalchemy.sql import text

tables = [
    "bodhi", "busmon", "compose", "fas", "git", "httpd", "koji",
    "logger", "meetbot", "tagger", "unclassified", "wiki"
]

metadata = MetaData()

def get_table_args(tname):
    return [
        tname,
        metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('i', sa.Integer, nullable=False),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('certificate', sa.UnicodeText),
        sa.Column('signature', sa.UnicodeText),
        sa.Column('topic', sa.UnicodeText),
        sa.Column('_msg', sa.UnicodeText, nullable=False)
    ]

def map_values(row):
    return dict(
        i=row[0]
        , timestamp=row[1]#datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S.%f')
        , certificate=row[2]
        , signature=row[3]
        , topic=row[4]
        , _msg=row[5]
    )


def upgrade():
    base_query = "SELECT i, timestamp, certificate, signature, topic, _msg FROM %s"

    # create table messages, messages_table is the python var for the sql table
    args = get_table_args('messages')
    engine = op.get_bind().engine
    messages_table = sa.Table(*args)
    metadata.create_all(engine)

    # query each topic table and insert into messages table
    for table in tables:
        tname = '%s_messages' % table
        query = base_query % tname

        results = engine.execute(text(query))
        data = map(map_values, results.fetchall())

        if data:
            op.bulk_insert(messages_table, data)


    # create the tables for the new models
    op.create_table(
        'user', sa.Column('name', sa.UnicodeText, primary_key=True)
    )

    op.create_table(
        'package', sa.Column('name', sa.UnicodeText, primary_key=True)
    )

    op.create_table('user_messages',
        sa.Column('username', sa.UnicodeText, sa.ForeignKey('user.name')),
        sa.Column('msg', sa.Integer, sa.ForeignKey('messages.id'))
    )

    op.create_table('package_messages',
        sa.Column('package', sa.UnicodeText, sa.ForeignKey('package.name')),
        sa.Column('msg', sa.Integer, sa.ForeignKey('messages.id'))
    )

    # drop each topic table
    for table in tables:
        op.drop_table('%s_messages' % table)


def downgrade():
    base_query = """
        SELECT i, timestamp, certificate, signature, topic, _msg
        FROM messages WHERE topic LIKE '%{0}%'
    """

    engine = op.get_bind().engine

    # create table for each topic
    db_tables = {}
    for table in tables:
        tname = '%s_messages' % table
        args = get_table_args(tname)
        db_table = sa.Table(*args)
        db_tables[tname] = db_table

    metadata.create_all(engine)

    # query message table with topic filter and insert in apropriate table
    for table in tables:
        tname = '%s_messages' % table
        results = engine.execute(text(base_query.format(table)))

        data = map(map_values, results.fetchall())

        if data:
            op.bulk_insert(db_tables[tname], data)

    # remove the new tables
    op.drop_table('user_messages')
    op.drop_table('package_messages')
    op.drop_table('messages')
    op.drop_table('user')
    op.drop_table('package')
