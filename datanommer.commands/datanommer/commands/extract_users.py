import datetime
import logging

import click
from fedora_messaging.exceptions import ValidationError
from fedora_messaging.message import load_message as load_message
from sqlalchemy import and_, not_, select

import datanommer.models as m

from .utils import CHUNK_SIZE, config_option, get_config, iterate_over_messages


log = logging.getLogger(__name__)

USERNAMES_SKIP_TOPICS = [
    "%.anitya.%",
    "%.discourse.%",
    "%.hotness.update.bug.file",
    "%.hotness.update.drop",
    "%.koschei.%",
    "%.mdapi.%",
]
AGENT_SKIP_TOPICS = [
    "%.hotness.update.bug.file",
    "%.hotness.update.drop",
]


@click.group()
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
@click.pass_context
def main(ctx, config_path, topic, category, start, end, force_schema, chunk_size, debug):
    ctx.ensure_object(dict)
    ctx.obj["options"] = ctx.params
    ctx.obj["config"] = config = get_config(config_path)
    m.init(
        config["datanommer_sqlalchemy_url"],
        alembic_ini=config["alembic_ini"],
    )
    if topic and category:
        raise click.UsageError("can't use both --topic and --category, choose one.")

    if not start:
        ctx.obj["options"]["start"] = m.session.execute(
            select(m.Message.timestamp).order_by(m.Message.timestamp).limit(1)
        ).scalar_one()

    query = select(m.Message)
    if topic:
        query = query.where(m.Message.topic == topic)
    elif category:
        query = query.where(m.Message.category == category)

    query = query.where(m.Message.timestamp >= ctx.obj["options"]["start"])
    if end:
        query = query.where(m.Message.timestamp < end)
    else:
        end = datetime.datetime.now()

    if force_schema is None:
        query = query.where(
            m.Message.headers.has_key("fedora_messaging_schema"),
            m.Message.headers["fedora_messaging_schema"].astext != "base.message",
        )
    ctx.obj["query"] = query


@main.command("usernames")
@click.pass_context
def extract_usernames(ctx):
    """Go over old messages, extract users and store them.

    This is useful when a message schema has been added and we want to populate the users table
    with the new information.
    """
    debug = ctx.obj["options"]["debug"]
    query = ctx.obj["query"]
    query = query.where(
        and_(*[not_(m.Message.topic.like(skipped)) for skipped in USERNAMES_SKIP_TOPICS])
    )
    query = query.join(
        m.users_assoc_table,
        and_(
            m.Message.id == m.users_assoc_table.c.msg_id,
            m.Message.timestamp == m.users_assoc_table.c.msg_timestamp,
        ),
        isouter=True,
    ).where(m.users_assoc_table.c.msg_id.is_(None))

    for message in iterate_over_messages(
        query, ctx.obj["options"]["start"], ctx.obj["options"]["chunk_size"]
    ):
        fm_message = get_fedora_message(message, force_schema=ctx.obj["options"]["force_schema"])
        if fm_message is None or not fm_message.usernames:
            m.session.expunge(message)
            continue
        message._insert_list(m.User, m.users_assoc_table, fm_message.usernames)
        if debug:
            click.echo(
                f"Usernames for message {message.msg_id} of topic {message.topic}"
                f": {', '.join(fm_message.usernames)}"
            )


def get_fedora_message(db_message, force_schema):
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

    return fm_message


@main.command("agent")
@click.pass_context
def extract_agent(ctx):
    """Go over old messages, extract the agent_name and store it.

    This is useful when a message schema has been added and we want to populate the agent_name
    column with the new information.
    """
    debug = ctx.obj["options"]["debug"]
    query = ctx.obj["query"]
    query = query.where(
        and_(*[not_(m.Message.topic.like(skipped)) for skipped in AGENT_SKIP_TOPICS])
    )
    query = query.where(m.Message.agent_name.is_(None))

    for message in iterate_over_messages(
        query, ctx.obj["options"]["start"], ctx.obj["options"]["chunk_size"]
    ):
        fm_message = get_fedora_message(message, force_schema=ctx.obj["options"]["force_schema"])
        if fm_message is None or not fm_message.agent_name:
            m.session.expunge(message)
            continue
        message.agent_name = fm_message.agent_name
        if debug:
            click.echo(
                f"Agent for message {message.msg_id} of topic {message.topic}"
                f": {fm_message.agent_name}"
            )
