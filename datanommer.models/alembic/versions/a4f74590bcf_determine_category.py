"""determine category

Revision ID: a4f74590bcf
Revises: ae2801c4cd9
Create Date: 2013-02-05 14:01:13.581491

"""

# revision identifiers, used by Alembic.
revision = 'a4f74590bcf'
down_revision = 'ae2801c4cd9'

from alembic import op


def map_values(row):
    return dict(
        topic=row[0],
        category=row[1],
    )

def upgrade():
    from sqlalchemy.sql import text

    import fedmsg.meta
    import fedmsg.config

    from fedmsg.config import _gather_configs_in
    from alembic import context
    config_path = context.config.get_main_option('fedmsg_config_dir')
    filenames = _gather_configs_in(config_path)

    config = fedmsg.config.load_config(filenames=filenames)
    fedmsg.meta.make_processors(**config)

    filters = []
    for f in fedmsg.meta.processors:
        filters.append(f.__name__.lower())


    query = "SELECT topic, category FROM messages WHERE category IS NULL"
    bquery = "UPDATE messages SET category = '%s' WHERE topic = '%s'"

    engine = op.get_bind().engine
    results = engine.execute(text(query))
    data = map(map_values, results.fetchall())

    for log in data:
        for filter in filters:
            if filter in log['topic']:
                log['category'] = filter
                engine.execute(text(bquery % (log['category'], log['topic'])))

def downgrade():
    pass

