"""determine category

Revision ID: a4f74590bcf
Revises: ae2801c4cd9
Create Date: 2013-02-05 14:01:13.581491

"""

# revision identifiers, used by Alembic.
revision = 'a4f74590bcf'
down_revision = 'ae2801c4cd9'

from alembic import op


from sqlalchemy.schema import MetaData
from sqlalchemy.sql import text

filters = [
    "bodhi", "busmon", "compose", "fas", "git", "httpd", "koji",
    "logger", "meetbot", "tagger", "unclassified", "wiki"
]

metadata = MetaData()

def map_values(row):
    return dict(
        topic=row[0],
        category=row[1],
    )

def upgrade():
    query = "SELECT topic, category FROM messages"
    base_query = "UPDATE messages SET category = '%s' WHERE topic = '%s'"


    engine = op.get_bind().engine
    results = engine.execute(text(query))
    data = map(map_values, results.fetchall())

    i = 0
    if data[i]['category'] == '' or data[i]['category']==None:
        for filter in filters:
            if filter in data[i]['topic']:
                data[i]['category'] = filter
                engine.execute(text(base_query % (data[i]['category'], data[i]['topic'])))
                i += 1

def downgrade():
    pass

