import datanommer.models

from fedmsg.encoding import pretty_dumps
from fedmsg.commands import BaseCommand

import time


class CreateCommand(BaseCommand):
    """ Create a database and tables for 'datanommer.sqlalchemy.url' """
    name = "datanommer-create-db"

    def run(self):
        datanommer.models.init(
            self.config['datanommer.sqlalchemy.url'], create=True
        )


class DumpCommand(BaseCommand):
    """ Dump the contents of the datanommer database as JSON """
    name = "datanommer-dump"

    def run(self):
        datanommer.models.init(self.config['datanommer.sqlalchemy.url'])

        results = []
        for model in datanommer.models.models:
            results += model.query.all()

        self.logger.info(pretty_dumps(results))


class StatsCommand(BaseCommand):
    """ Produce stats on the contents of the datanommer database """
    name = "datanommer-stats"

    def run(self):
        datanommer.models.init(self.config['datanommer.sqlalchemy.url'])

        for model in datanommer.models.models:
            logger_args = (model, "has", model.query.count(), "entries")
            self.logger.info("%s, %s, %s, %s" % logger_args)


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
            'help': "When combined with --timestamp,"
                    + "show a human readable date.",
        }),
    ]

    def run(self):
        datanommer.models.init(self.config['datanommer.sqlalchemy.url'])
        models = datanommer.models.models
        config = self.config

        if config.get('model', None):
            eq = lambda m: config['model'].lower() in m.__name__.lower()
            models = filter(eq, models)

        latest = {}
        for model in sorted(models):
            query = model.query.order_by(model.timestamp.desc())
            if query.count():
                latest[model] = query.first()

        def formatter(model, val):
            model = pretty_dumps(str(model.__name__))
            if config.get('timestamp', None) and config.get('human', None):
                return pretty_dumps(str(val.timestamp))
            elif config.get('timestamp', None) and not config.get('human', None):
                return pretty_dumps(time.mktime(val.timestamp.timetuple()))
            else:
                return "{%s: %s}" % (model, pretty_dumps(val))

        if config.get('overall', None):
            winner = latest.items()[0]
            for k, v in latest.items():
                if v.timestamp > winner[1].timestamp:
                    winner = (k, v)
            self.logger.info(formatter(*winner))
        else:
            results = []

            for k, v in sorted(latest.items()):
                results.append(formatter(k, v))

            self.logger.info('[%s]' % ','.join(results))


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
