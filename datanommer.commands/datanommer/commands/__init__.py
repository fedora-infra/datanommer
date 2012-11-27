import datanommer.models

from fedmsg.encoding import pretty_dumps
from fedmsg.commands import command

import time


@command(name="datanommer-create-db")
def create(**kw):
    """ Create a database and tables for 'datanommer.sqlalchemy.url' """
    datanommer.models.init(kw['datanommer.sqlalchemy.url'], create=True)


@command(name="datanommer-dump")
def dump(**kw):
    """ Dump the contents of the datanommer database as JSON """
    datanommer.models.init(kw['datanommer.sqlalchemy.url'])
    results = []
    for model in datanommer.models.models:
        results += model.query.all()
    print pretty_dumps(results)

@command(name="datanommer-stats")
def stats(**kw):
    """ Produce stats on the contents of the datanommer database """
    datanommer.models.init(kw['datanommer.sqlalchemy.url'])
    for model in datanommer.models.models:
        print model, "has", model.query.count(), "entries"


# Extra arguments for datanommer-latest
extra_args = [
    (['--model'], {
        'dest': 'model',
        'default': None,
        'help': "Show the latest for only a specific model.",
    }),
    (['--overall'], {
        'dest': 'overall',
        'default': False,
        'action': 'store_true',
        'help': "Show only the latest message out of all message types.",
    }),
    (['--timestamp'], {
        'dest': 'timestamp',
        'default': False,
        'action': 'store_true',
        'help': "Show only the timestamp of the message(s).",
    }),
    (['--human'], {
        'dest': 'human',
        'default': False,
        'action': 'store_true',
        'help': "When combined with --timestamp, show a human readable date.",
    }),
]


@command(name="datanommer-latest", extra_args=extra_args)
def latest(**kw):
    """ Print the latest message(s) ingested by datanommer.

    The default is to display the latest message in each message category.
    """

    datanommer.models.init(kw['datanommer.sqlalchemy.url'])
    models = datanommer.models.models

    if kw['model']:
        eq = lambda m: kw['model'].lower() in m.__name__.lower()
        models = filter(eq, models)

    latest = {}
    for model in sorted(models):
        query = model.query.order_by(model.timestamp.desc())
        if query.count():
            latest[model] = query.first()

    formatter = lambda model, value: "%s, %s" % (model, pretty_dumps(value))
    if kw['timestamp'] and kw['human']:
        formatter = lambda m, v: v.timestamp
    elif kw['timestamp'] and not kw['human']:
        formatter = lambda m, v: time.mktime(v.timestamp.timetuple())

    if kw['overall']:
        winner = latest.items()[0]
        for k, v in latest.items():
            if v.timestamp > winner[1].timestamp:
                winner = (k, v)

        print formatter(*winner)
    else:
        for k, v in sorted(latest.items()):
            print formatter(k, v)
