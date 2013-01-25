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
            topic='org.fedoraproject.prod.git.branch.valgrind.master',
            timestamp=now
        )

        msg2 = Message(
            topic='org.fedoraproject.prod.git.receive.valgrind.master',
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

                    eq_(json_object[0]['topic'],
                        'org.fedoraproject.prod.git.branch.valgrind.master')

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
                topic='org.fedoraproject.prod.git.branch.valgrind.master',
                timestamp=datetime.utcnow(),
                i=1
            )

            msg2 = Message(
                topic='org.fedoraproject.stg.fas.user.create',
                timestamp=datetime.utcnow(),
                i=1
            )

            msg3 = Message(
                topic='org.fedoraproject.prod.git.receive.valgrind.master',
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

            eq_(json_object[0]['git']['msg'], 'Message 3')
            eq_(len(json_object), 1)

    def test_latest_topic(self):
        from datanommer.models import session

        Message = datanommer.models.Message

        with patch('datanommer.commands.LatestCommand.get_config') as gc:
            self.config['topic'] = 'org.fedoraproject.stg.fas.user.create'
            gc.return_value = self.config

            datanommer.models.init(
                uri=self.config['datanommer.sqlalchemy.url']
            )

            msg1 = Message(
                topic='org.fedoraproject.prod.git.branch.valgrind.master',
                timestamp=datetime.utcnow(),
                i=1
            )

            msg2 = Message(
                topic='org.fedoraproject.stg.fas.user.create',
                timestamp=datetime.utcnow(),
                i=1
            )

            msg3 = Message(
                topic='org.fedoraproject.prod.git.receive.valgrind.master',
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

            eq_(json_object[0]['fas']['msg'], 'Message 2')
            eq_(len(json_object), 1)

    def test_latest_category(self):
        from datanommer.models import session

        Message = datanommer.models.Message

        with patch('datanommer.commands.LatestCommand.get_config') as gc:
            self.config['category'] = 'fas'
            gc.return_value = self.config

            datanommer.models.init(
                uri=self.config['datanommer.sqlalchemy.url']
            )

            msg1 = Message(
                topic='org.fedoraproject.prod.git.branch.valgrind.master',
                category='git',
                timestamp=datetime.utcnow(),
                i=1
            )

            msg2 = Message(
                topic='org.fedoraproject.stg.fas.user.create',
                category='fas',
                timestamp=datetime.utcnow(),
                i=1
            )

            msg3 = Message(
                topic='org.fedoraproject.prod.git.receive.valgrind.master',
                category='git',
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

            eq_(json_object[0]['fas']['msg'], 'Message 2')
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
                topic='org.fedoraproject.prod.git.branch.valgrind.master',
                timestamp=datetime.utcnow(),
                i=1
            )

            msg2 = Message(
                topic='org.fedoraproject.stg.fas.user.create',
                timestamp=datetime.utcnow(),
                i=1
            )

            msg3 = Message(
                topic='org.fedoraproject.prod.git.receive.valgrind.master',
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

            eq_(json_object[0]['git']['msg'], 'Message 3')
            eq_(json_object[1]['fas']['msg'], 'Message 2')
            eq_(len(json_object), 2)
