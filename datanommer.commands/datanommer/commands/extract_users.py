import logging

import click
from fedora_messaging.message import load_message
from sqlalchemy import and_, select

import datanommer.models as m

from . import config_option, get_config


log = logging.getLogger(__name__)


@click.command()
@config_option
@click.option(
    "--topic", default=None, help="Only extract users for messages of a specific topic."
)
@click.option(
    "--category",
    default=None,
    help="Only extract users for messages of a specific category.",
)
def main(config_path, topic, category):
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

    query = (
        query.join(
            m.users_assoc_table,
            and_(
                m.Message.id == m.users_assoc_table.c.msg_id,
                m.Message.timestamp == m.users_assoc_table.c.msg_timestamp,
            ),
            isouter=True,
        )
        .where(m.users_assoc_table.c.msg_id.is_(None))
        .order_by(m.Message.timestamp)
    )

    for message in m.session.scalars(query):
        fm_msg = load_message(
            {
                "topic": message.topic,
                "headers": message.headers,
                "id": message.msg_id,
                "body": message.msg,
            }
        )
        usernames = fm_msg.usernames
        if not usernames:
            continue
        message._insert_list(m.User, m.users_assoc_table, usernames)
        log.info(
            "Usernames for message %s of topic %s: %s",
            message.msg_id,
            message.topic,
            ", ".join(usernames),
        )
