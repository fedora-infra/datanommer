#!/usr/bin/env python

"""
Migrate the datanommer database from the pre-2021 format to the TimescaleDB-based format.
"""

from json import loads

import click
import toml
from sqlalchemy import (
    Column,
    create_engine,
    DateTime,
    ForeignKey,
    Integer,
    Table,
    UnicodeText,
)
from sqlalchemy.orm import declarative_base, relationship, Session

import datanommer.models as dm


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

    users = relationship("User", secondary=user_assoc_table, lazy="joined")
    packages = relationship("Package", secondary=pack_assoc_table, lazy="joined")


class User(OldBase):
    __tablename__ = "user"

    name = Column(UnicodeText, primary_key=True)


class Package(OldBase):
    __tablename__ = "package"

    name = Column(UnicodeText, primary_key=True)


def import_message(message):
    msg = loads(message._msg)
    headers = message._headers
    if headers is not None:
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
        category=message.category,
        msg=msg,
        headers=headers,
        users=[u.name for u in message.users],
        packages=[p.name for p in message.packages],
    )


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
    dm.init(config["dest_url"])
    src_engine = create_engine(config["source_url"], future=True)

    with Session(src_engine) as src_db:
        click.echo("Querying messages...")
        old_messages = src_db.query(OldMessage).order_by(OldMessage.id)
        latest = dm.Message.query.order_by(dm.Message.id.desc()).first()
        if latest:
            latest_in_src = (
                src_db.query(OldMessage)
                .filter(OldMessage.msg_id == latest.msg_id)
                .one()
            )
            old_messages = old_messages.filter(OldMessage.id > latest_in_src.id)
            click.echo(f"Resuming from message {latest.msg_id}")
        if since:
            old_messages = old_messages.filter(OldMessage.timestamp > since)
            click.echo(f"Only importing messages after {since}")
        total = old_messages.count()
        with click.progressbar(
            old_messages,
            length=total,
            label=f"Importing {total} messages",
            # item_show_func=lambda m: m.msg_id if m else "",
        ) as bar:
            for old_message in bar:
                import_message(old_message)
                # Commit periodically
                if bar._completed_intervals % 1000 == 0:
                    dm.session.commit()
                else:
                    dm.session.flush()
        dm.session.commit()
        # Verify counts
        click.echo(f"Messages in the old DB: {src_db.query(OldMessage).count()}")
        click.echo(f"Messages in the new DB: {dm.Message.query.count()}")


if __name__ == "__main__":
    main()
