import logging

import click
from fedora_messaging import config as fedora_messaging_config
from fedora_messaging.message import load_message as load_message
from sqlalchemy import func

import datanommer.models as m


# Go trough messages these many at a time
CHUNK_SIZE = 10000
log = logging.getLogger(__name__)


def get_config(config_path=None):
    if config_path:
        fedora_messaging_config.conf.load_config(config_path)
    conf = fedora_messaging_config.conf["consumer_config"]
    for key in ("datanommer_sqlalchemy_url", "alembic_ini"):
        if key not in conf:
            raise click.ClickException(f"{key} not defined in the fedora-messaging config")
    return conf


config_option = click.option(
    "-c",
    "--config",
    "config_path",
    help="Load this Fedora Messaging config file",
    type=click.Path(exists=True, readable=True),
)


def iterate_over_messages(query, start, chunk_size):
    click.echo("Counting messages...")

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
            # click < 8.2 (Python < 3.10): use bar.is_hidden
            # click >= 8.2 (Python >= 3.10): use bar.hidden and the TTY check
            if (hasattr(bar, "is_hidden") and bar.is_hidden) or (
                hasattr(bar, "hidden") and (bar.hidden or not bar.file.isatty())
            ):
                click.echo(f"Working on {chunk_size} messages sent after {chunk_start}")
            chunk_query = query.where(m.Message.timestamp >= chunk_start).limit(chunk_size)
            if not first_run:
                chunk_query = chunk_query.offset(1)
            has_messages = False
            for message in m.session.scalars(chunk_query):
                bar.update(1)
                has_messages = True
                yield message
            if has_messages:
                chunk_start = message.timestamp
            first_run = False
            m.session.commit()
            m.session.expunge_all()
