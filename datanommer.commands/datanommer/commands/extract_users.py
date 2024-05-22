import datetime
import logging

import click
from fedora_messaging.exceptions import ValidationError
from fedora_messaging.message import load_message as load_message
from sqlalchemy import and_, func, not_, select

import datanommer.models as m

from . import config_option, get_config


# Go trough messages these at a time
CHUNK_SIZE = 10000
log = logging.getLogger(__name__)

SKIP_TOPICS = [
    "%.anitya.%",
    "%.discourse.%",
    "%.hotness.update.bug.file",
    "%.koschei.%",
    "%.mdapi.%",
]


@click.command()
@config_option
@click.option("--topic", default=None, help="Only extract users for messages of a specific topic.")
@click.option(
    "--category",
    default=None,
    help="Only extract users for messages of a specific category.",
)
@click.option(
    "--start",
    default=None,
    type=click.DateTime(),
    help="Only extract users for messages after a specific timestamp.",
)
@click.option(
    "--end",
    default=None,
    type=click.DateTime(),
    help="Only extract users for messages before a specific timestamp.",
)
@click.option(
    "--force-schema",
    default=None,
    help=(
        "Force usage of this schema name to extract usernames. This is the key in the "
        "exposed entry point / plugin, for example: wiki.article.edit.v1"
    ),
)
@click.option(
    "--chunk-size",
    default=CHUNK_SIZE,
    type=int,
    show_default=True,
    help="Go through messages these many at a time (lower is slower but saves memory).",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Show more information.",
)
def main(config_path, topic, category, start, end, force_schema, chunk_size, debug):
    """Go over old messages, extract users and store them.

    This is useful when a message schema has been added and we want to populate the users table
    with the new information.
    """
    config = get_config(config_path)
    m.init(
        config["datanommer_sqlalchemy_url"],
        alembic_ini=config["alembic_ini"],
    )

    if topic and category:
        raise click.UsageError("can't use both --topic and --category, choose one.")

    query = select(m.Message)
    if topic:
        query = query.where(m.Message.topic == topic)
    elif category:
        query = query.where(m.Message.category == category)
    else:
        query = query.where(and_(*[not_(m.Message.topic.like(skipped)) for skipped in SKIP_TOPICS]))
    if start:
        query = query.where(m.Message.timestamp >= start)
    else:
        start = m.session.execute(
            select(m.Message.timestamp).order_by(m.Message.timestamp).limit(1)
        ).scalar_one()
    if end:
        query = query.where(m.Message.timestamp < end)
    else:
        end = datetime.datetime.now()
    if force_schema is None:
        query = query.where(
            m.Message.headers.has_key("fedora_messaging_schema"),
            m.Message.headers["fedora_messaging_schema"].astext != "base.message",
        )

    query = query.join(
        m.users_assoc_table,
        and_(
            m.Message.id == m.users_assoc_table.c.msg_id,
            m.Message.timestamp == m.users_assoc_table.c.msg_timestamp,
        ),
        isouter=True,
    ).where(m.users_assoc_table.c.msg_id.is_(None))

    total = m.session.scalar(query.with_only_columns(func.count(m.Message.id)))
    if not total:
        click.echo("No messages matched.")
        return

    click.echo(f"Considering {total} message{'s' if total > 1 else ''}")

    query = query.order_by(m.Message.timestamp)
    with click.progressbar(length=total) as bar:
        has_messages = True
        chunk_start = start
        first_run = True
        while has_messages:
            chunk_query = query.where(m.Message.timestamp >= chunk_start).limit(chunk_size)
            if not first_run:
                chunk_query = chunk_query.offset(1)
            has_messages = False
            for message in m.session.scalars(chunk_query):
                bar.update(1)
                has_messages = True
                usernames = get_usernames(message, force_schema=force_schema)
                if not usernames:
                    m.session.expunge(message)
                    continue
                message._insert_list(m.User, m.users_assoc_table, usernames)
                if debug:
                    click.echo(
                        f"Usernames for message {message.msg_id} of topic {message.topic}"
                        f": {', '.join(usernames)}"
                    )
            chunk_start = message.timestamp
            first_run = False
            m.session.commit()
            m.session.expunge_all()


def get_usernames(db_message, force_schema):
    headers = db_message.headers
    if force_schema and headers is not None:
        headers["fedora_messaging_schema"] = force_schema
    try:
        fm_message = load_message(
            {
                "topic": db_message.topic,
                "headers": headers,
                "id": db_message.msg_id,
                "body": db_message.msg,
            }
        )
    except ValidationError as e:
        try:
            # Remove this block after fedora-messaging 3.6.0 and use e.summary
            error_msg = e.args[0].summary
        except AttributeError:
            error_msg = str(e).split("\n")[0]
        click.echo(
            f"Could not load message {db_message.msg_id} on topic {db_message.topic}: {error_msg}",
            err=True,
        )
        return None

    return fm_message.usernames
