# This file is a part of datanommer, a message sink for fedmsg.
# Copyright (C) 2014, Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
import datanommer.models as m
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
        m.init(
            self.config['datanommer.sqlalchemy.url'], create=True
        )


class DumpCommand(BaseCommand):
    """ Dump the contents of the datanommer database as JSON.

    You can also specify a timespan with the --since and --before arguments:

        $ datanommer-dump --before 2013-02-15 --since 2013-02-11T08:00:00 > datanommer-dump.json
    """
    name = "datanommer-dump"
    extra_args = extra_args = [
        (['--since'], {
            'dest': 'since',
            'default': None,
            'help': "Only after datetime, ex 2013-02-14T08:05:59.87",
        }),
        (['--before'], {
            'dest': 'before',
            'default': None,
            'help': "Only before datetime, ex 2013-02-14T08:05:59.87",
        }),
    ]

    def run(self):
        m.init(self.config['datanommer.sqlalchemy.url'])
        config = self.config

        query = m.Message.query
        if config.get('before', None):
            query = query.filter(m.Message.timestamp<=config.get('before'))

        if config.get('since', None):
            query = query.filter(m.Message.timestamp>=config.get('since'))

        results = query.all()

        self.log.info(pretty_dumps(results))


class StatsCommand(BaseCommand):
    """ Produce stats on the contents of the datanommer database.

    The default is to display the stats per category. You can also display
    the stats per topic with the --topic argument:

        $ datanommer-stats --topic
        org.fedoraproject.stg.fas.group.member.remove has 10 entries
        org.fedoraproject.stg.logger.log has 76 entries
        org.fedoraproject.stg.bodhi.update.comment has 5 entries
        org.fedoraproject.stg.busmon.colorized-messages has 10 entries
        org.fedoraproject.stg.fas.user.update has 10 entries
        org.fedoraproject.stg.wiki.article.edit has 106 entries
        org.fedoraproject.stg.fas.user.create has 3 entries
        org.fedoraproject.stg.bodhitest.testing has 4 entries
        org.fedoraproject.stg.fedoratagger.tag.create has 9 entries
        org.fedoraproject.stg.fedoratagger.user.rank.update has 5 entries
        org.fedoraproject.stg.wiki.upload.complete has 1 entries
        org.fedoraproject.stg.fas.group.member.sponsor has 6 entries
        org.fedoraproject.stg.fedoratagger.tag.update has 1 entries
        org.fedoraproject.stg.fas.group.member.apply has 17 entries
        org.fedoraproject.stg.__main__.testing has 1 entries

    The --category argument can be combined with --topic to shows stats of the
    topics with a specific category or can be used alone to show the stats for
    only the one category:

        $ datanommer-stats --topic --category fas
        org.fedoraproject.stg.fas.group.member.remove has 10 entries
        org.fedoraproject.stg.fas.user.update has 10 entries
        org.fedoraproject.stg.fas.user.create has 3 entries
        org.fedoraproject.stg.fas.group.member.sponsor has 6 entries
        org.fedoraproject.stg.fas.group.member.apply has 17 entries

        $ datanommmer-stats --category fas
        fas has 46 entries

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
        m.init(self.config['datanommer.sqlalchemy.url'])
        config = self.config

        if config.get('topic', None):
            if config.get('category',None):
                query = m.session.query(
                    m.Message.topic, func.count(m.Message.topic)
                ).filter(
                    m.Message.category==config.get('category')
                )
            else:
                query = m.session.query(
                    m.Message.topic, func.count(m.Message.topic)
                )
            query = query.group_by(m.Message.topic)
        else:
            if config.get('category',None):
                query = m.session.query(
                    m.Message.category, func.count(m.Message.category)
                ).filter(
                    m.Message.category==config.get('category')
                )
            else:
                query = m.session.query(
                    m.Message.category, func.count(m.Message.category)
                )
            query = query.group_by(m.Message.category)


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

    The default is to display the latest message in each message category. The
    latest in only a specified category or topic can also be returned:

        $ datanommer-latest --category bodhi
        [{"bodhi": {
          "topic": "org.fedoraproject.stg.bodhi.update.comment",
          "msg": {
            "comment": {
              "group": null,
              "author": "ralph",
              "text": "Testing for latest datanommer.",
              "karma": 0,
              "anonymous": false,
              "timestamp": 1360349639.0,
              "update_title": "xmonad-0.10-10.fc17"
            },
            "agent": "ralph"
          },
        }}]

        $ datanommer-latest --topic org.fedoraproject.stg.bodhi.update.comment
        [{"bodhi": {
          "topic": "org.fedoraproject.stg.bodhi.update.comment",
          "msg": {
            "comment": {
              "group": null,
              "author": "ralph",
              "text": "Testing for latest datanommer.",
              "karma": 0,
              "anonymous": false,
              "timestamp": 1360349639.0,
              "update_title": "xmonad-0.10-10.fc17"
            },
            "agent": "ralph"
          },
        }}]

    Or to display the latest, regardless of the topic or category:

        $ datanommer-latest --overall
        [{"bodhi": {
          "topic": "org.fedoraproject.stg.bodhi.update.comment",
          "msg": {
            "comment": {
              "group": null,
              "author": "ralph",
              "text": "Testing for latest datanommer.",
              "karma": 0,
              "anonymous": false,
              "timestamp": 1360349639.0,
              "update_title": "xmonad-0.10-10.fc17"
            },
            "agent": "ralph"
          },
        }}]

    You can combine either a --topic, --category or --overall argument while
    requesting information about the timestamp of the latest:

        $ datanommer-latest --category wiki --timestamp
        [1361166918.0]

        # February 18, 2013 at 5:55AM
        $ datanommer-latest --category wiki --timestamp --human
        ["2013-02-18 05:55:18"]

    Or how recent that timestamp is:

        # 49250 seconds ago
        $ datanommer-latest --category wiki --timesince
        [49250]

        # 13 hours, 40 minutes, 59.52 seconds ago
        $ datanommer-latest --category wiki --timesince --human
        [13:40:59.519447]
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
        m.init(self.config['datanommer.sqlalchemy.url'])
        config = self.config

        if config.get('topic', None):
            queries = [
                m.Message.query.filter(m.Message.topic == config.get('topic'))
            ]

        elif config.get('category', None):
            queries = [m.Message.query.filter(
                m.Message.category == config.get('category')
            )]
        elif not config.get('overall', False):
            # If no args..
            fedmsg.meta.make_processors(**config)
            categories = [
                p.__name__.lower() for p in fedmsg.meta.processors
            ]
            queries = [m.Message.query.filter(
                m.Message.category == category
            ) for category in categories]
        else:
            # Show only the single latest message, regardless of type.
            queries = [m.Message.query]

        # Order and limit to the latest.
        queries = [
            q.order_by(m.Message.timestamp.desc()).limit(1)
            for q in queries
        ]

        def formatter(key, val):
            if config.get('timestamp', None) and config.get('human', None):
                return pretty_dumps(str(val.timestamp))
            elif config.get('timestamp', None):
                return pretty_dumps(time.mktime(val.timestamp.timetuple()))
            elif config.get('timesince', None) and config.get('human', None):
                return pretty_dumps(str(datetime.datetime.now()-val.timestamp))
            elif config.get('timesince', None):
                timedelta = datetime.datetime.now() - val.timestamp
                return pretty_dumps(str((timedelta.days * 86400)+timedelta.seconds))
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
