#!/usr/bin/env python

"""
Migrate the datanommer database from the pre-2021 format to the TimescaleDB-based format.
"""

from json import dumps, JSONDecodeError, loads

import click
import toml
from sqlalchemy import (
    Column,
    create_engine,
    DateTime,
    ForeignKey,
    func,
    Integer,
    select,
    Table,
    UnicodeText,
)
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import declarative_base, relationship, Session

import datanommer.models as dm


CHUNK_SIZE = 5000

OldBase = declarative_base()

user_assoc_table = Table(
    "user_messages",
    OldBase.metadata,
    Column("username", UnicodeText, ForeignKey("user.name")),
    Column("msg", Integer, ForeignKey("messages.id")),
)

pack_assoc_table = Table(
    "package_messages",
    OldBase.metadata,
    Column("package", UnicodeText, ForeignKey("package.name")),
    Column("msg", Integer, ForeignKey("messages.id")),
)


class OldMessage(OldBase):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    msg_id = Column(UnicodeText)
    i = Column(Integer)
    topic = Column(UnicodeText)
    timestamp = Column(DateTime)
    certificate = Column(UnicodeText)
    signature = Column(UnicodeText)
    category = Column(UnicodeText)
    username = Column(UnicodeText)
    crypto = Column(UnicodeText)
    source_name = Column(UnicodeText)
    source_version = Column(UnicodeText)
    _msg = Column(UnicodeText)
    _headers = Column(UnicodeText)

    users = relationship("User", secondary=user_assoc_table, lazy="selectin")
    packages = relationship("Package", secondary=pack_assoc_table, lazy="selectin")


class User(OldBase):
    __tablename__ = "user"

    name = Column(UnicodeText, primary_key=True)


class Package(OldBase):
    __tablename__ = "package"

    name = Column(UnicodeText, primary_key=True)


def import_message(message):
    msg = message._msg.replace("\\u0000", "")
    try:
        msg = loads(msg)
    except JSONDecodeError:
        click.echo(
            f"Can't decode json in message {message.msg_id} ({message.timestamp})"
        )
        with open("failed.log", "a") as failedlog:
            failedlog.write(
                dumps(
                    {
                        "id": message.id,
                        "msg_id": message.msg_id,
                        "timestamp": message.timestamp.isoformat(),
                        "topic": message.topic,
                        "msg": message._msg,
                    }
                )
            )
            failedlog.write("\n")
        return
    if not msg:
        with open("failed.log", "a") as failedlog:
            failedlog.write(
                dumps(
                    {
                        "id": message.id,
                        "msg_id": message.msg_id,
                        "timestamp": message.timestamp.isoformat(),
                        "topic": message.topic,
                        "msg": repr(message._msg),
                    }
                )
            )
            failedlog.write("\n")
        return
    headers = message._headers
    if headers is not None:
        headers = headers.replace("\\u0000", "")
        headers = loads(headers)
    dm.Message.create(
        i=message.i,
        msg_id=message.msg_id,
        topic=message.topic,
        timestamp=message.timestamp,
        username=message.username,
        crypto=message.crypto,
        certificate=message.certificate,
        signature=message.signature,
        msg=msg,
        headers=headers,
        users=[u.name for u in message.users],
        packages=[p.name for p in message.packages],
    )


# https://github.com/sqlalchemy/sqlalchemy/wiki/RangeQuery-and-WindowedRangeQuery
def windowed_query(q, column, windowsize):
    """ "Break a Query into chunks on a given column."""

    single_entity = q.is_single_entity
    q = q.add_columns(column).order_by(column)
    last_id = None

    while True:
        subq = q
        if last_id is not None:
            subq = subq.where(column > last_id)
        chunk = subq.limit(windowsize).all()
        if not chunk:
            break
        last_id = chunk[-1][-1]
        for row in chunk:
            if single_entity:
                yield row[0]
            else:
                yield row[0:-1]


@click.command()
@click.option(
    "config_path",
    "-c",
    "--config",
    type=click.Path(),
    default="migrate.toml",
    show_default=True,
)
@click.option(
    "since",
    "-s",
    "--since",
    type=click.DateTime(),
)
def main(config_path, since):
    config = toml.load(config_path)
    dm.init(config["dest_url"], create=True)
    src_engine = create_engine(config["source_url"], future=True)

    with Session(src_engine) as src_db:
        click.echo("Querying messages...")
        old_messages = src_db.scalars(select(OldMessage).order_by(OldMessage.id))
        latest = dm.session.scalars(
            select(dm.Message).order_by(dm.Message.id.desc()).limit(1)
        ).first()
        if latest:
            try:
                latest_in_src = src_db.execute(
                    select(OldMessage).where(OldMessage.msg_id == latest.msg_id)
                ).scalar_one()
            except NoResultFound:
                latest_in_src = src_db.execute(
                    select(OldMessage)
                    .where(OldMessage.timestamp == latest.timestamp)
                    .where(OldMessage.topic == latest.topic)
                ).scalar_one()
            old_messages = old_messages.where(OldMessage.id > latest_in_src.id)
            click.echo(f"Resuming from message {latest.msg_id}")
        if since:
            old_messages = old_messages.where(OldMessage.timestamp > since)
            click.echo(f"Only importing messages after {since}")
        total = old_messages.count()
        with click.progressbar(
            length=total,
            label=f"Importing {total} messages",
            item_show_func=lambda m: m.timestamp.strftime("%Y-%m") if m else "",
            # item_show_func=lambda m: m.msg_id if m else "",
        ) as bar:
            for old_message in windowed_query(old_messages, OldMessage.id, CHUNK_SIZE):
                import_message(old_message)
                # Commit periodically
                if bar._completed_intervals % 1000 == 0:
                    dm.session.commit()
                else:
                    dm.session.flush()
                bar.update(1, old_message)
        dm.session.commit()
        # Verify counts
        click.echo(
            f"Messages in the old DB: {src_db.scalar(select(func.count(OldMessage.id)))}"
        )
        click.echo(
            f"Messages in the new DB: {dm.session.scalar(select(func.count(dm.Message.id)))}"
        )


if __name__ == "__main__":
    main()
