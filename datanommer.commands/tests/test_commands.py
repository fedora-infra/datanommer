import unittest
from mock import Mock
from mock import patch
from datetime import datetime
import json

import datanommer.commands
import datanommer.models
from nose.tools import eq_

class TestCommands(unittest.TestCase):
    def test_dump(self):
        LoggerMessage = datanommer.models.LoggerMessage
        now = datetime.utcnow()

        msg1 = LoggerMessage(
            topic = 'Python'
            , timestamp = now
        )

        msg2 = LoggerMessage(
            topic = 'Fedora'
            , timestamp = now
        )

        msg1.msg = 'Message 1'
        msg2.msg = 'Message 2'
        objects = [msg1, msg2]

        models = [LoggerMessage]

        with patch('datanommer.models.models', models):
            LoggerMessage.query = Mock()
            LoggerMessage.query.all = Mock(return_value = objects)

            config = {
                'datanommer.sqlalchemy.url': 'sqlite:///'
            }

            with patch('datanommer.commands.DumpCommand.get_config') as gc:
                gc.return_value = config

                command = datanommer.commands.DumpCommand()

                logged_info = []

                def info(data):
                    logged_info.append(data)

                command.logger.info = info
                command.run()

                json_object = json.loads(logged_info[0])

                eq_(json_object[0]['topic'], 'Python')
