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
import json
import logging
import time
from datetime import datetime, timedelta

import click
from fedora_messaging import config as fedora_messaging_config
from sqlalchemy import func

import datanommer.models as m


log = logging.getLogger("datanommer")


def get_datanommer_sqlalchemy_url(config_path=None):
    if config_path:
        fedora_messaging_config.conf.load_config(config_path)
    try:
        return fedora_messaging_config.conf["consumer_config"][
            "datanommer_sqlalchemy_url"
        ]
    except KeyError:
        raise click.ClickException(
            "datanommer_sqlalchemy_url not defined in the fedora-messaging config"
        )


config_option = click.option(
    "-c",
    "--config",
    "config_path",
    help="Load this Fedora Messaging config file",
    type=click.Path(exists=True, readable=True),
)


@click.command()
@config_option
def create(config_path):
    """Create a database and tables for 'datanommer.sqlalchemy.url'"""
    datanommer_sqlalchemy_url = get_datanommer_sqlalchemy_url(config_path)
    click.echo("Creating Datanommer database and tables")
    m.init(datanommer_sqlalchemy_url, create=True)


@click.command()
@config_option
@click.option(
    "--since", default=None, help="Only after datetime, ex 2013-02-14T08:05:59.87"
)
@click.option(
    "--before", default=None, help="Only before datetime, ex 2013-02-14T08:05:59.87"
)
def dump(config_path, since, before):
    """Dump the contents of the datanommer database as JSON.

    You can also specify a timespan with the --since and --before arguments:

        $ datanommer-dump --before 2013-02-15 --since 2013-02-11T08:00:00 > datanommer-dump.json
    """
    datanommer_sqlalchemy_url = get_datanommer_sqlalchemy_url(config_path)
    m.init(datanommer_sqlalchemy_url)

    query = m.Message.query
    if before:
        try:
            before = datetime.fromisoformat(before)
        except ValueError:
            raise click.ClickException("Invalid date format")

        query = query.filter(m.Message.timestamp <= before)

    if since:
        try:
            since = datetime.fromisoformat(since)
        except ValueError:
            raise click.ClickException("Invalid date format")

        query = query.filter(m.Message.timestamp >= since)

    results = [json.dumps(msg.as_fedora_message_dict()) for msg in query.all()]
    click.echo(f"[{','.join(results)}]")


@click.command()
@config_option
@click.option("--topic", is_flag=True, help="Shows the stats per topic")
@click.option(
    "--category",
    default=None,
    help="Shows the stats within only the specified category",
)
def stats(config_path, topic, category):
    """Produce stats on the contents of the datanommer database.

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
    datanommer_sqlalchemy_url = get_datanommer_sqlalchemy_url(config_path)

    m.init(datanommer_sqlalchemy_url)

    if topic:
        if category:
            query = m.session.query(
                m.Message.topic, func.count(m.Message.topic)
            ).filter(m.Message.category == category)
        else:
            query = m.session.query(m.Message.topic, func.count(m.Message.topic))
        query = query.group_by(m.Message.topic)
    else:
        if category:
            query = m.session.query(
                m.Message.category, func.count(m.Message.category)
            ).filter(m.Message.category == category)
        else:
            query = m.session.query(m.Message.category, func.count(m.Message.category))
        query = query.group_by(m.Message.category)

    results = query.all()

    if topic:
        for topic, count in results:
            click.echo(f"{topic} has {count} entries")
    else:
        for category, count in results:
            click.echo(f"{category} has {count} entries")


@click.command()
@config_option
@click.option(
    "--topic", default=None, help="Show the latest for only a specific topic."
)
@click.option(
    "--category", default=None, help="Show the latest for only a specific category."
)
@click.option(
    "--overall",
    is_flag=True,
    help="Show only the latest message out of all message types.",
)
@click.option(
    "--timestamp", is_flag=True, help="Show only the timestamp of the message(s)."
)
@click.option(
    "--timesince",
    is_flag=True,
    help="Show the number of seconds since the last message",
)
@click.option(
    "--human",
    is_flag=True,
    help="When combined with --timestamp or --timesince,show a human readable date.",
)
def latest(config_path, topic, category, overall, timestamp, timesince, human):
    """Print the latest message(s) ingested by datanommer.

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
    datanommer_sqlalchemy_url = get_datanommer_sqlalchemy_url(config_path)

    m.init(datanommer_sqlalchemy_url)

    if topic:
        queries = [m.Message.query.filter(m.Message.topic == topic)]

    elif category:
        queries = [m.Message.query.filter(m.Message.category == category)]
    elif not overall:
        # If no args..
        categories = [
            c[0]
            for c in m.session.query(m.Message.category)
            .distinct()
            .order_by(m.Message.category)
        ]
        queries = [
            m.Message.query.filter(m.Message.category == category)
            for category in categories
        ]
    else:
        # Show only the single latest message, regardless of type.
        queries = [m.Message.query]

    # Only check messages from the last year to speed up queries
    a_year = timedelta(days=365)
    earliest = datetime.utcnow() - a_year
    queries = [q.filter(m.Message.timestamp > earliest) for q in queries]

    # Order and limit to the latest.
    queries = [q.order_by(m.Message.timestamp.desc()).limit(1) for q in queries]

    def formatter(key, val):
        if timestamp and human:
            return json.dumps(str(val.timestamp))
        elif timestamp:
            return json.dumps(time.mktime(val.timestamp.timetuple()))
        elif timesince and human:
            return json.dumps(str(datetime.now() - val.timestamp))
        elif timesince:
            timedelta = datetime.now() - val.timestamp
            return json.dumps(str((timedelta.days * 86400) + timedelta.seconds))
        else:
            return f'{{"{key}": {json.dumps(val.as_fedora_message_dict())}}}'

    results = []
    for result in sum((query.all() for query in queries), []):
        results.append(formatter(result.category, result))

    click.echo(f"[{','.join(results)}]")


# Set the version
try:  # pragma: no cover
    import importlib.metadata

    __version__ = importlib.metadata.version("datanommer.commands")
except ImportError:  # pragma: no cover
    try:
        import pkg_resources

        try:
            __version__ = pkg_resources.get_distribution("datanommer.commands").version
        except pkg_resources.DistributionNotFound:
            # The app is not installed, but the flask dev server can run it nonetheless.
            __version__ = None
    except ImportError:
        __version__ = None
