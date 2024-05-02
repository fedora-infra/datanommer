import datetime
import logging

import click
from fedora_messaging.message import load_message as load_message
from sqlalchemy import cast, select, update
from sqlalchemy.dialects import postgresql

import datanommer.models as m

from .utils import config_option, get_config


log = logging.getLogger(__name__)


@click.command()
@config_option
@click.option(
    "--chunk-size",
    default=30,
    type=int,
    show_default=True,
    help="Go through messages these many days at a time (lower is slower but saves memory).",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Show more information.",
)
def main(config_path, chunk_size, debug):
    """Go over old messages and populate the msg_json field."""
    config = get_config(config_path)
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO, format="%(message)s")
    m.init(
        config["datanommer_sqlalchemy_url"],
        alembic_ini=config["alembic_ini"],
    )

    query = select(m.Message).where(m.Message.msg_json.is_(None))
    first_message = m.session.scalars(query.order_by(m.Message.timestamp).limit(1)).first()
    if first_message is None:
        click.echo("No message to populate.")
        return

    for start_date, end_date in iterate_over_time(
        first_message.timestamp, datetime.timedelta(days=chunk_size)
    ):
        log.debug(
            "Converting messages between %s and %s",
            start_date.date().isoformat(),
            end_date.date().isoformat(),
        )
        # Fill the msg_json column from the contents of the msg_raw column
        query = (
            update(m.Message)
            .where(
                m.Message.msg_json.is_(None),
                m.Message.timestamp >= start_date,
                m.Message.timestamp < end_date,
            )
            .values(msg_json=cast(m.Message.msg_raw, postgresql.JSONB(none_as_null=True)))
        )
        result = m.session.execute(query)
        m.session.commit()
        log.debug("Populated %s rows", result.rowcount)
        # Empty the msg_raw column if msg_json is not filled
        query = (
            update(m.Message)
            .where(
                m.Message.msg_json.is_not(None),
                m.Message.timestamp >= start_date,
                m.Message.timestamp < end_date,
            )
            .values(msg_raw=None)
        )
        result = m.session.execute(query)
        log.debug("Purged %s rows", result.rowcount)


def iterate_over_time(start_at, interval):
    intervals = []
    start_date = start_at
    now = datetime.datetime.now()
    while start_date < now:
        end_date = start_date + interval
        intervals.append((start_date, end_date))
        start_date = end_date

    total = len(intervals)
    with click.progressbar(length=total) as bar:
        for start_date, end_date in intervals:
            yield start_date, end_date
            m.session.commit()
            m.session.expunge_all()
            bar.update(1)
