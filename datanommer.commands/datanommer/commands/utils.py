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


def iterate_over_messages(query, chunk_size):
    total = m.session.scalar(query.with_only_columns(func.count(m.Message.id)))
    if not total:
        click.echo("No messages matched.")
        return

    click.echo(f"Considering {total} message{'s' if total > 1 else ''}")

    query = query.order_by(m.Message.timestamp)
    with click.progressbar(length=total) as bar:
        for chunk in range(int(total / chunk_size) + 1):
            offset = chunk * chunk_size
            chunk_query = query.limit(chunk_size).offset(offset)
            for message in m.session.scalars(chunk_query):
                bar.update(1)
                yield message
            m.session.commit()
            m.session.expunge_all()
