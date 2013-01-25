from sqlalchemy import create_engine
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    ForeignKey,
    UnicodeText,
)

from sqlalchemy.orm import (
    sessionmaker,
    scoped_session,
    relationship,
)

from sqlalchemy.orm import validates


from sqlalchemy.schema import Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

import datetime
import fedmsg.encoding

maker = sessionmaker()
session = scoped_session(maker)

DeclarativeBase = declarative_base()
DeclarativeBase.query = session.query_property()

import logging
log = logging.getLogger("datanommer")


def init(uri=None, alembic_ini=None, create=False):
    """ Initialize a connection.  Create tables if requested."""

    if uri is None:
        uri = 'sqlite:////tmp/datanommer.db'
        log.warning("No db uri given.  Using %r" % uri)

    engine = create_engine(uri)
    session.configure(bind=engine)
    DeclarativeBase.query = session.query_property()

    # Loads the alembic configuration and generates the version table, with
    # the most recent revision stamped as head
    if alembic_ini is not None:
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config(alembic_ini)
        command.stamp(alembic_cfg, "head")

    if create:
        DeclarativeBase.metadata.create_all(engine)


def add(message):
    """ Take a dict-like fedmsg message and store it in the table.
    """
    timestamp = message['timestamp']
    try:
        timestamp = datetime.datetime.fromtimestamp(timestamp)
    except Exception:
        pass

    obj = Message(
        i=message['i'],
        topic=message['topic'],
        timestamp=timestamp,
        certificate=message.get('certificate', None),
        signature=message.get('signature', None),
    )

    obj.msg = message['msg']

    session.add(obj)

    usernames = fedmsg.meta.msg2usernames(message)
    packages = fedmsg.meta.msg2packages(message)
    for username in usernames:
        user = session.query(User).get(username)

        if not user:
            user = User(name=username)

        obj.users.append(user)

    for package in packages:
        package = session.query(Package).get(package)

        if not package:
            package = Package(name=package)

        obj.packages.append(package)

    # TODO -- can we avoid committing every time?
    session.flush()
    session.commit()


class BaseMessage(object):
    id = Column(Integer, primary_key=True)
    i = Column(Integer, nullable=False)
    topic = Column(UnicodeText, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    certificate = Column(UnicodeText)
    signature = Column(UnicodeText)
    category = Column(UnicodeText)
    _msg = Column(UnicodeText, nullable=False)

    @validates('topic')
    def get_category(self, key, topic):
        filters = ['bodhi', 'compose', 'git', 'wiki', 'tagger', 'busmon',
                    'fas', 'meetbot', 'koji', 'logger', 'httpd']

        for f in filters:
            if f in topic:
                self.category = f

        return topic

    @hybrid_property
    def msg(self):
        return fedmsg.encoding.loads(self._msg)

    @msg.setter
    def msg(self, dict_like_msg):
        self._msg = fedmsg.encoding.dumps(dict_like_msg)

    def __json__(self):
        return dict(
            i=self.i,
            topic=self.topic,
            timestamp=self.timestamp,
            certificate=self.certificate,
            signature=self.signature,
            msg=self.msg,
        )

user_assoc_table = Table('user_messages', DeclarativeBase.metadata,
    Column('username', UnicodeText, ForeignKey('user.name')),
    Column('msg', Integer, ForeignKey('messages.id'))
)

pack_assoc_table = Table('package_messages', DeclarativeBase.metadata,
    Column('package', UnicodeText, ForeignKey('package.name')),
    Column('msg', Integer, ForeignKey('messages.id'))
)


class User(DeclarativeBase):
    __tablename__ = 'user'
    name = Column(UnicodeText, primary_key=True)


class Package(DeclarativeBase):
    __tablename__ = 'package'
    name = Column(UnicodeText, primary_key=True)


class Message(DeclarativeBase, BaseMessage):
    __tablename__ = "messages"
    users = relationship("User", secondary=user_assoc_table)
    packages = relationship("Package", secondary=pack_assoc_table)

models = frozenset((
    v for k, v in locals().items()
    if (
        isinstance(v, type) and
        issubclass(v, BaseMessage) and
        k is not "BaseMessage"
    )
))
