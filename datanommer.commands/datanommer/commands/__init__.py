import datanommer.models
from datanommer.models import Message

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

        self.log.info(pretty_dumps(results))


class StatsCommand(BaseCommand):
    """ Produce stats on the contents of the datanommer database """
    name = "datanommer-stats"

    def run(self):
        datanommer.models.init(self.config['datanommer.sqlalchemy.url'])

        for model in datanommer.models.models:
            logger_args = (model, "has", model.query.count(), "entries")
            self.log.info("%s, %s, %s, %s" % logger_args)


# Extra arguments for datanommer-latest


class LatestCommand(BaseCommand):
    """ Print the latest message(s) ingested by datanommer.

    The default is to display the latest message in each message category.
    """
    name = "datanommer-latest"
    extra_args = extra_args = [
        (['--topic'], {
            'dest': 'topic',
            'default': None,
            'help': "Show the latest for only a specific topic.",
        }),
        (['--category'], {
            'dest': 'category',
            'default': None,
            'help': "Show the latest for only a specific category.",
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
        config = self.config

        if config.get('topic', None):
            query = Message.query.filter(Message.topic == config.get('topic'))
        elif config.get('category', None):
            query = Message.query.filter(
                Message.category == config.get('category')
            )
        else:
            query = Message.query.group_by(Message.category)

        query = query.order_by(Message.timestamp.desc())

        if config.get('overall', None) or config.get('topic', None):
            query = query.limit(1)
        if config.get('category', None):
            query = query.limit(1)

        def formatter(key, val):
            if config.get('timestamp', None) and config.get('human', None):
                return pretty_dumps(str(val.timestamp))
            elif config.get('timestamp', None):
                return pretty_dumps(time.mktime(val.timestamp.timetuple()))
            else:
                return "{%s: %s}" % (pretty_dumps(key), pretty_dumps(val))

        results = []
        for result in query.all():
            results.append(formatter(result.category, result))

        self.log.info('[%s]' % ','.join(results))


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
