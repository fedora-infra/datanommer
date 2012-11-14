import datanommer.models
import fedmsg.encoding

from fedmsg.commands import command


@command(name="datanommer-create-db")
def create(**kw):
    """ Create a database and tables for 'datanommer.sqlalchemy.url' """
    datanommer.models.init(kw['datanommer.sqlalchemy.url'], create=True)


@command(name="datanommer-dump")
def dump(**kw):
    """ Dump the contents of the datanommer database as JSON """
    datanommer.models.init(kw['datanommer.sqlalchemy.url'])
    for model in datanommer.models.models:
        for entry in model.query.all():
            print fedmsg.encoding.pretty_dumps(entry)


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

    if kw['overall']:
        winner = latest.items()[0]
        for k, v in latest.items():
            if v.timestamp > winner[1].timestamp:
                winner = (k, v)

        print winner[0], fedmsg.encoding.pretty_dumps(winner[1])
    else:
        for k, v in sorted(latest.items()):
            print k, fedmsg.encoding.pretty_dumps(v)
