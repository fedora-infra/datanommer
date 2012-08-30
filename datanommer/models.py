from sqlalchemy import create_engine
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    ForeignKey,
    Unicode,
)

from sqlalchemy.orm import sessionmaker, scoped_session
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


def init(uri, create=False):
    engine = create_engine(uri)
    session.configure(bind=engine)
    DeclarativeBase.query = session.query_property()

    if create:
        DeclarativeBase.metadata.create_all(engine)


def add(message):
    """ Take a dict-like fedmsg message and store it in the appropriate table.
    """

    possible = filter(lambda m: m.topic_filter in message['topic'], models)

    if len(possible) == 0:
        model_cls = UnclassifiedMessage
    elif len(possible) > 1:
        model_cls = possible[0]
        log.warn("Multiple models match message.  Using %r." % model)
    else:
        model_cls = possible[0]

    log.debug("Using %r" % model_cls)

    timestamp = message['timestamp']
    try:
        timestamp = datetime.datetime.fromtimestamp(timestamp)
    except Exception:
        pass

    obj = model_cls(
        i=message['i'],
        topic=message['topic'],
        timestamp=timestamp,
        certificate=message.get('certificate', None),
        signature=message.get('signature', None),
    )
    obj.msg = message['msg']

    session.add(obj)

    # TODO -- can we avoid committing every time?
    session.flush()
    session.commit()


class BaseMessage(object):
    id = Column(Integer, primary_key=True)
    i = Column(Integer, nullable=False)
    topic = Column(Unicode(255), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    certificate = Column(Unicode(1023))
    signature = Column(Unicode(255))
    _msg = Column(Unicode(1023), nullable=False)

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


class BodhiMessage(DeclarativeBase, BaseMessage):
    topic_filter = "bodhi"
    __tablename__ = "%s_messages" % topic_filter


class GitMessage(DeclarativeBase, BaseMessage):
    topic_filter = "git"
    __tablename__ = "%s_messages" % topic_filter


class WikiMessage(DeclarativeBase, BaseMessage):
    topic_filter = "wiki"
    __tablename__ = "%s_messages" % topic_filter


class TaggerMessage(DeclarativeBase, BaseMessage):
    topic_filter = "tagger"
    __tablename__ = "%s_messages" % topic_filter


class BusmonMessage(DeclarativeBase, BaseMessage):
    topic_filter = "busmon"
    __tablename__ = "%s_messages" % topic_filter


class FASMessage(DeclarativeBase, BaseMessage):
    topic_filter = "fas"
    __tablename__ = "%s_messages" % topic_filter


class MeetbotMessage(DeclarativeBase, BaseMessage):
    topic_filter = "meetbot"
    __tablename__ = "%s_messages" % topic_filter


class KojiMessage(DeclarativeBase, BaseMessage):
    topic_filter = "koji"
    __tablename__ = "%s_messages" % topic_filter


class LoggerMessage(DeclarativeBase, BaseMessage):
    topic_filter = "logger"
    __tablename__ = "%s_messages" % topic_filter


class HttpdMessage(DeclarativeBase, BaseMessage):
    topic_filter = "httpd"
    __tablename__ = "%s_messages" % topic_filter


class UnclassifiedMessage(DeclarativeBase, BaseMessage):
    topic_filter = "this will never be in a topic..."
    __tablename__ = "unclassified_messages"


models = frozenset((
    v for k, v in locals().items()
    if (
        isinstance(v, type) and
        issubclass(v, BaseMessage) and
        k is not "BaseMessage"
    )
))
