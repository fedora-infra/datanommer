import datanommer.models
from datanommer.models import Message
from datanommer.models import session
from sqlalchemy import func

from fedmsg.encoding import pretty_dumps
from fedmsg.commands import BaseCommand
import fedmsg.meta

import datetime
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
    """ Produce stats on the contents of the datanommer database.

    The default is to display the stats per category.
    """
    name = "datanommer-stats"
    extra_args = extra_args = [
        (['--topic'], {
            'dest': 'topic',
            'default': False,
            'action': 'store_true',
            'help': "Shows the stats per topic",
        }),
        (['--category'], {
            'dest': 'category',
            'default': None,
            'help': "Shows the stats within only the specified category",
        }),
    ]

    def run(self):
        datanommer.models.init(self.config['datanommer.sqlalchemy.url'])
        config = self.config

 #       if config.get('category', None):
 #           query = Message.query.filter(
 #                       Message.category == config.get('category')
 #           )

        if config.get('topic', None):
            if config.get('category',None):
                query = session.query(Message.topic, func.count(Message.topic)).filter(
                        Message.category==config.get('category'))
            else:
                query = session.query(Message.topic, func.count(Message.topic))
            query = query.group_by(Message.topic)
        else:
            if config.get('category',None):
                query = session.query(Message.category, func.count(Message.category)).filter(
                        Message.category==config.get('category'))
            else:
                query = session.query(Message.category, func.count(Message.category))
            query = query.group_by(Message.category)


        results = query.all()

        if config.get('topic', None):
            for topic, count in results:
                self.log.info("%s has %s entries" % (topic, count))
        else:
            for category, count in results:
                self.log.info("%s has %s entries" % (category, count))


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
        (['--timesince'], {
            'dest': 'timesince',
            'default': False,
            'action': 'store_true',
            'help': 'Show the number of seconds since the last message',
        }),
        (['--human'], {
            'dest': 'human',
            'default': False,
            'action': 'store_true',
            'help': "When combined with --timestamp or --timesince,"
                    + "show a human readable date.",
        }),
    ]

    def run(self):
        datanommer.models.init(self.config['datanommer.sqlalchemy.url'])
        config = self.config

        if config.get('topic', None):
            queries = [
                Message.query.filter(Message.topic == config.get('topic'))
            ]

        elif config.get('category', None):
            queries = [Message.query.filter(
                Message.category == config.get('category')
            )]
        elif not config.get('overall', False):
            # If no args..
            fedmsg.meta.make_processors(**config)
            categories = [
                p.__name__.lower() for p in fedmsg.meta.processors
            ]
            queries = [Message.query.filter(
                Message.category == category
            ) for category in categories]
        else:
            # Show only the single latest message, regardless of type.
            queries = [Message.query]

        # Order and limit to the latest.
        queries = [
            q.order_by(Message.timestamp.desc()).limit(1)
            for q in queries
        ]

        def formatter(key, val):
            if config.get('timestamp', None) and config.get('human', None):
                return pretty_dumps(str(val.timestamp))
            elif config.get('timestamp', None):
                return pretty_dumps(time.mktime(val.timestamp.timetuple()))
            elif config.get('timesince', None) and config.get('human', None):
                return str(datetime.datetime.now() - val.timestamp)
            elif config.get('timesince', None):
                timedelta = datetime.datetime.now() - val.timestamp
                return str((timedelta.days * 86400) + timedelta.seconds)
            else:
                return "{%s: %s}" % (pretty_dumps(key), pretty_dumps(val))

        results = []
        for result in sum([query.all() for query in queries], []):
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
