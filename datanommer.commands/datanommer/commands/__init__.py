import datanommer.models

from fedmsg.encoding import pretty_dumps
from fedmsg.commands import BaseCommand

import time


class CreateCommand(BaseCommand):
    """ Create a database and tables for 'datanommer.sqlalchemy.url' """
    name="datanommer-create-db"

    def run(self):
        datanommer.models.init(self.config['datanommer.sqlalchemy.url'], create=True)


class DumpCommand(BaseCommand):
    """ Dump the contents of the datanommer database as JSON """
    name="datanommer-dump"

    def run(self):
        datanommer.models.init(self.config['datanommer.sqlalchemy.url'])

        for model in datanommer.models.models:
            for entry in model.query.all():
                self.logger.info(pretty_dumps(entry))


class StatsCommand(BaseCommand):
    """ Produce stats on the contents of the datanommer database """
    name="datanommer-stats"

    def run(self):
        datanommer.models.init(self.config['datanommer.sqlalchemy.url'])

        for model in datanommer.models.models:
            self.logger.info(model, "has", model.query.count(), "entries")




# Extra arguments for datanommer-latest


class LatestCommand(BaseCommand):
    """ Print the latest message(s) ingested by datanommer.

    The default is to display the latest message in each message category.
    """
    name = "datanommer-latest"
    extra_args = extra_args = [
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

    def run(self):
        datanommer.models.init(self.config['datanommer.sqlalchemy.url'])
        models = datanommer.models.models

        if self.config['model']:
            eq = lambda m: self.config['model'].lower() in m.__name__.lower()
            models = filter(eq, models)

        latest = {}
        for model in sorted(models):
            query = model.query.order_by(model.timestamp.desc())
            if query.count():
                latest[model] = query.first()

        formatter = lambda model, value: "%s, %s" % (model, pretty_dumps(value))
        if self.config['timestamp'] and self.config['human']:
            formatter = lambda m, v: v.timestamp
        elif self.config['timestamp'] and not self.config['human']:
            formatter = lambda m, v: time.mktime(v.timestamp.timetuple())

        if self.config['overall']:
            winner = latest.items()[0]
            for k, v in latest.items():
                if v.timestamp > winner[1].timestamp:
                    winner = (k, v)

            self.logger.info(formatter(*winner))
        else:
            for k, v in sorted(latest.items()):
                self.logger.info(formatter(k, v))

def create():
    command = CreateCommand()
    command.execute()

def dump():
    command = DumpCommand()
    command.execute()

def stats():
    command = StatsCommand()
    command.execute()

def latest():
    command = LatestCommand()
    command.execute()
