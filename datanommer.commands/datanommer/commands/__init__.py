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
