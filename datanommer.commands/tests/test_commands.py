import unittest
from mock import Mock
from mock import patch
from datetime import datetime
import json
import os

import datanommer.commands
import datanommer.models
import fedmsg.config
from nose.tools import (
    eq_,
    ok_,
)
try:
    from nose.tools import (
        assert_in,
        assert_not_in,
    )
except ImportError:
    # Old versions of nose don't have assert_in and friends.
    def assert_in(item, lst, msg=None):
        ok_(item in lst, msg)

    def assert_not_in(item, lst, msg=None):
        ok_(item not in lst, msg)


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
        self.config.update(fedmsg.config.load_config())
        datanommer.models.init(uri=uri, create=True)

    def tearDown(self):
        datanommer.models.session.rollback()
        os.remove(filename)

    def test_stats(self):
        from datanommer.models import session

        Message = datanommer.models.Message

        with patch('datanommer.commands.StatsCommand.get_config') as gc:
            self.config['topic'] = False
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

            command = datanommer.commands.StatsCommand()

            command.log.info = info
            command.run()

            assert_in('git has 2 entries', logged_info)
            assert_in('fas has 1 entries', logged_info)

    def test_stats_topics(self):
        from datanommer.models import session

        Message = datanommer.models.Message

        with patch('datanommer.commands.StatsCommand.get_config') as gc:
            self.config['topic'] = True
            gc.return_value = self.config

            datanommer.models.init(
                uri=self.config['datanommer.sqlalchemy.url']
            )
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


            command = datanommer.commands.StatsCommand()

            command.log.info = info
            command.run()

            assert_in('org.fedoraproject.prod.git.receive.valgrind.master has 1 entries', logged_info)
            assert_in('org.fedoraproject.stg.fas.user.create has 1 entries', logged_info)
            assert_in('org.fedoraproject.prod.git.branch.valgrind.master has 1 entries', logged_info)

    def test_stats_cat_topics(self):
        from datanommer.models import session

        Message = datanommer.models.Message

        with patch('datanommer.commands.StatsCommand.get_config') as gc:
            self.config['topic'] = True
            self.config['category'] = 'git'
            gc.return_value = self.config

            datanommer.models.init(
                uri=self.config['datanommer.sqlalchemy.url']
            )
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


            command = datanommer.commands.StatsCommand()

            command.log.info = info
            command.run()

            assert_in('org.fedoraproject.prod.git.receive.valgrind.master has 1 entries', logged_info)
            assert_not_in('org.fedoraproject.stg.fas.user.create has 1 entries', logged_info)
            assert_in('org.fedoraproject.prod.git.branch.valgrind.master has 1 entries', logged_info)

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

    def test_dump_before(self):
        from datanommer.models import session

        Message = datanommer.models.Message

        with patch('datanommer.commands.DumpCommand.get_config') as gc:
            self.config['before'] = '2013-02-16'
            gc.return_value = self.config

            datanommer.models.init(
                uri=self.config['datanommer.sqlalchemy.url']
            )

            time1 = datetime(2013,02,14)
            time2 = datetime(2013,02,15)
            time3 = datetime(2013,02,16,8)

            msg1 = Message(
                topic='org.fedoraproject.prod.git.branch.valgrind.master',
                timestamp=time1,
                i=4
            )

            msg2 = Message(
                topic='org.fedoraproject.prod.git.receive.valgrind.master',
                timestamp=time2,
                i=3
            )

            msg3 = Message(
                topic='org.fedoraproject.prod.log.receive.valgrind.master',
                timestamp=time3,
                i=2
            )

            msg1.msg = 'Message 1'
            msg2.msg = 'Message 2'
            msg3.msg = 'Message 3'

            session.add_all([msg1, msg2, msg3])
            session.flush()

            logged_info = []

            def info(data):
                logged_info.append(data)

            command = datanommer.commands.DumpCommand()

            command.log.info = info
            command.run()

            json_object = json.loads(logged_info[0])

            eq_(json_object[0]['topic'],
                'org.fedoraproject.prod.git.branch.valgrind.master')
            eq_(json_object[1]['topic'],
                'org.fedoraproject.prod.git.receive.valgrind.master')
            eq_(len(json_object), 2)

    def test_dump_since(self):
        from datanommer.models import session

        Message = datanommer.models.Message

        with patch('datanommer.commands.DumpCommand.get_config') as gc:
            self.config['since'] = '2013-02-14T08:00:00'
            gc.return_value = self.config

            datanommer.models.init(
                uri=self.config['datanommer.sqlalchemy.url']
            )

            time1 = datetime(2013,02,14)
            time2 = datetime(2013,02,15)
            time3 = datetime(2013,02,16,8)

            msg1 = Message(
                topic='org.fedoraproject.prod.git.branch.valgrind.master',
                timestamp=time1,
                i=4
            )

            msg2 = Message(
                topic='org.fedoraproject.prod.git.receive.valgrind.master',
                timestamp=time2,
                i=3
            )

            msg3 = Message(
                topic='org.fedoraproject.prod.log.receive.valgrind.master',
                timestamp=time3,
                i=2
            )

            msg1.msg = 'Message 1'
            msg2.msg = 'Message 2'
            msg3.msg = 'Message 3'

            session.add_all([msg1, msg2, msg3])
            session.flush()

            logged_info = []

            def info(data):
                logged_info.append(data)

            command = datanommer.commands.DumpCommand()

            command.log.info = info
            command.run()

            json_object = json.loads(logged_info[0])

            eq_(json_object[0]['topic'],
                'org.fedoraproject.prod.git.receive.valgrind.master')
            eq_(json_object[1]['topic'],
                'org.fedoraproject.prod.log.receive.valgrind.master')
            eq_(len(json_object), 2)

    def test_dump_timespan(self):
        from datanommer.models import session

        Message = datanommer.models.Message

        with patch('datanommer.commands.DumpCommand.get_config') as gc:
            self.config['before'] = '2013-02-16'
            self.config['since'] = '2013-02-14T08:00:00'
            gc.return_value = self.config

            datanommer.models.init(
                uri=self.config['datanommer.sqlalchemy.url']
            )

            time1 = datetime(2013,02,14)
            time2 = datetime(2013,02,15)
            time3 = datetime(2013,02,16,8)

            msg1 = Message(
                topic='org.fedoraproject.prod.git.branch.valgrind.master',
                timestamp=time1,
                i=4
            )

            msg2 = Message(
                topic='org.fedoraproject.prod.git.receive.valgrind.master',
                timestamp=time2,
                i=3
            )

            msg3 = Message(
                topic='org.fedoraproject.prod.log.receive.valgrind.master',
                timestamp=time3,
                i=2
            )

            msg1.msg = 'Message 1'
            msg2.msg = 'Message 2'
            msg3.msg = 'Message 3'

            session.add_all([msg1, msg2, msg3])
            session.flush()

            logged_info = []

            def info(data):
                logged_info.append(data)

            command = datanommer.commands.DumpCommand()

            command.log.info = info
            command.run()

            json_object = json.loads(logged_info[0])

            eq_(json_object[0]['topic'],
                'org.fedoraproject.prod.git.receive.valgrind.master')
            eq_(len(json_object), 1)


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

    def test_latest_timestamp_human(self):
        from datanommer.models import session

        Message = datanommer.models.Message

        with patch('datanommer.commands.LatestCommand.get_config') as gc:
            self.config['overall'] = False
            self.config['timestamp'] = True
            self.config['human'] = True
            gc.return_value = self.config

            time1 = datetime(2013,02,14)
            time2 = datetime(2013,02,15,15,15,15,15)
            time3 = datetime(2013,02,16,16,16,16,16)

            datanommer.models.init(
                uri=self.config['datanommer.sqlalchemy.url']
            )

            msg1 = Message(
                topic='org.fedoraproject.prod.git.branch.valgrind.master',
                timestamp=time1,
                i=1
            )

            msg2 = Message(
                topic='org.fedoraproject.stg.fas.user.create',
                timestamp=time2,
                i=1
            )

            msg3 = Message(
                topic='org.fedoraproject.prod.git.receive.valgrind.master',
                timestamp=time3,
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

            eq_(json_object[0], "2013-02-16 16:16:16.000016")
            eq_(json_object[1], "2013-02-15 15:15:15.000015")
            eq_(len(json_object), 2)

    def test_latest_timestamp(self):
        from datanommer.models import session
        import time

        Message = datanommer.models.Message

        with patch('datanommer.commands.LatestCommand.get_config') as gc:
            self.config['overall'] = False
            self.config['timestamp'] = True
            gc.return_value = self.config

            time1 = datetime(2013,02,14)
            time2 = datetime(2013,02,15)
            time3 = datetime(2013,02,16)

            datanommer.models.init(
                uri=self.config['datanommer.sqlalchemy.url']
            )

            msg1 = Message(
                topic='org.fedoraproject.prod.git.branch.valgrind.master',
                timestamp=time1,
                i=1
            )

            msg2 = Message(
                topic='org.fedoraproject.stg.fas.user.create',
                timestamp=time2,
                i=1
            )

            msg3 = Message(
                topic='org.fedoraproject.prod.git.receive.valgrind.master',
                timestamp=time3,
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

            eq_(json_object[0], time.mktime(datetime(2013,2,16).timetuple()))
            eq_(json_object[1], time.mktime(datetime(2013,2,15).timetuple()))
            eq_(len(json_object), 2)

    def test_latest_timesince(self):
        from datanommer.models import session

        Message = datanommer.models.Message

        with patch('datanommer.commands.LatestCommand.get_config') as gc:
            self.config['overall'] = False
            self.config['timesince'] = True
            gc.return_value = self.config

            now = datetime.now()
            time1 = now.replace(day=now.day-1)
            time2 = now.replace(minute=now.minute-1)
            time3 = now.replace(second=now.second-1)

            datanommer.models.init(
                uri=self.config['datanommer.sqlalchemy.url']
            )

            msg1 = Message(
                topic='org.fedoraproject.prod.git.branch.valgrind.master',
                timestamp=time1,
                i=1
            )

            msg2 = Message(
                topic='org.fedoraproject.stg.fas.user.create',
                timestamp=time2,
                i=1
            )

            msg3 = Message(
                topic='org.fedoraproject.prod.git.receive.valgrind.master',
                timestamp=time3,
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

            # allow .1 second to run test
            assert int(json_object[0])<=1.1
            assert int(json_object[0])>=1
            assert int(json_object[1])<=60.1
            assert int(json_object[1])>=60
            eq_(len(json_object), 2)

    def test_latest_timesince_human(self):
        from datanommer.models import session

        Message = datanommer.models.Message

        with patch('datanommer.commands.LatestCommand.get_config') as gc:
            self.config['overall'] = False
            self.config['timesince'] = True
            self.config['human'] = True
            gc.return_value = self.config

            now = datetime.now()
            time1 = now.replace(day=now.day-2)
            time2 = now.replace(day=now.day-1)
            time3 = now.replace(second=now.second-1)

            datanommer.models.init(
                uri=self.config['datanommer.sqlalchemy.url']
            )

            msg1 = Message(
                topic='org.fedoraproject.prod.git.branch.valgrind.master',
                timestamp=time1,
                i=1
            )

            msg2 = Message(
                topic='org.fedoraproject.stg.fas.user.create',
                timestamp=time2,
                i=1
            )

            msg3 = Message(
                topic='org.fedoraproject.prod.git.receive.valgrind.master',
                timestamp=time3,
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

            # cannot assert exact value because of time to run test
            assert_not_in('day', json_object[0])
            assert_in('0:00:01.', json_object[0])
            assert_in('1 day, 0:00:00.', json_object[1])
            eq_(len(json_object), 2)

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

