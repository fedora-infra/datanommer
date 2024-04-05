import logging

import click
from fedora_messaging.message import load_message
from sqlalchemy import and_, func, select

import datanommer.models as m

from . import config_option, get_config


log = logging.getLogger(__name__)


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
    "--force-schema",
    default=None,
    help=(
        "Force usage of this schema name to extract usernames. This is the key in the "
        "exposed entry point / plugin, for example: wiki.article.edit.v1"
    ),
)
def main(config_path, topic, category, start, force_schema):
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
    if start:
        query = query.where(m.Message.timestamp >= start)

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

    query = query.order_by(m.Message.timestamp)
    click.echo(f"Considering {total} message{'s' if total > 1 else ''}")

    for message in m.session.scalars(query):
        headers = message.headers
        if force_schema:
            headers["fedora_messaging_schema"] = force_schema
        fm_msg = load_message(
            {
                "topic": message.topic,
                "headers": headers,
                "id": message.msg_id,
                "body": message.msg,
            }
        )
        usernames = fm_msg.usernames
        if not usernames:
            continue
        message._insert_list(m.User, m.users_assoc_table, usernames)
        click.echo(
            f"Usernames for message {message.msg_id} of topic {message.topic}"
            f": {', '.join(usernames)}"
        )
    m.session.commit()
