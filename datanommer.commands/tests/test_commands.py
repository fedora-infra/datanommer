import unittest
from mock import Mock
from mock import patch
from datetime import datetime
import json
import os

import datanommer.commands
import datanommer.models
from nose.tools import eq_

filename = "datanommer-test.db"


class TestCommands(unittest.TestCase):
    def setUp(self):
        uri = "sqlite:///%s" % filename
        self.config = {
            'datanommer.sqlalchemy.url': uri,
            'logging': {
                'version': 1
            }
        }
        datanommer.models.init(uri=uri, create=True)

    def tearDown(self):
        os.remove(filename)

    def test_dump(self):
        Message = datanommer.models.Message
        now = datetime.utcnow()

        msg1 = Message(
            topic='Python',
            timestamp=now
        )

        msg2 = Message(
            topic='Fedora',
            timestamp=now
        )

        msg1.msg = 'Message 1'
        msg2.msg = 'Message 2'
        objects = [msg1, msg2]

        models = [Message]

        with patch('datanommer.models.models', models):
            with patch('datanommer.models.Message.query') as query:
                Message.query.all = Mock(return_value=objects)

                with patch('datanommer.commands.DumpCommand.get_config') as gc:
                    gc.return_value = self.config

                    command = datanommer.commands.DumpCommand()

                    logged_info = []

                    def info(data):
                        logged_info.append(data)

                    command.log.info = info
                    command.run()

                    json_object = json.loads(logged_info[0])

                    eq_(json_object[0]['topic'], 'Python')

    def test_latest_overall(self):
        from datanommer.models import session

        Message = datanommer.models.Message

        with patch('datanommer.commands.LatestCommand.get_config') as gc:
            self.config['overall'] = True
            gc.return_value = self.config

            datanommer.models.init(
                uri=self.config['datanommer.sqlalchemy.url']
            )

            msg1 = Message(
                topic='Python',
                timestamp=datetime.utcnow(),
                i=1
            )

            msg2 = Message(
                topic='Fedora',
                timestamp=datetime.utcnow(),
                i=1
            )

            msg3 = Message(
                topic='Linux',
                timestamp=datetime.utcnow(),
                i=1
            )

            msg1.msg = 'Message 1'
            msg2.msg = 'Message 2'
            msg3.msg = 'Message 3'

            session.add_all([msg1, msg2, msg3])
            session.flush()

            logged_info = []

            def info(data):
                logged_info.append(data)

            command = datanommer.commands.LatestCommand()

            command.log.info = info
            command.run()

            json_object = json.loads(logged_info[0])

            eq_(json_object['Message']['msg'], 'Message 3')
            eq_(len(json_object), 1)

    def test_latest(self):
        from datanommer.models import session

        Message = datanommer.models.Message

        with patch('datanommer.commands.LatestCommand.get_config') as gc:
            self.config['overall'] = False
            gc.return_value = self.config

            datanommer.models.init(
                uri=self.config['datanommer.sqlalchemy.url']
            )

            msg1 = Message(
                topic='Python',
                timestamp=datetime.utcnow(),
                i=1
            )

            msg2 = Message(
                topic='Fedora',
                timestamp=datetime.utcnow(),
                i=1
            )

            msg3 = Message(
                topic='Linux',
                timestamp=datetime.utcnow(),
                i=1
            )

            msg1.msg = 'Message 1'
            msg2.msg = 'Message 2'
            msg3.msg = 'Message 3'

            session.add_all([msg1, msg2, msg3])
            session.flush()

            logged_info = []

            def info(data):
                logged_info.append(data)

            command = datanommer.commands.LatestCommand()

            command.log.info = info
            command.run()

            json_object = json.loads(logged_info[0])

            eq_(json_object[0]['Message']['msg'], 'Message 3')
            eq_(len(json_object), 1)
