# This file is a part of datanommer, a message sink for fedmsg.
# Copyright (C) 2014, Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
import fedmsg
import fedmsg.consumers
import datanommer.models
import sqlalchemy.exc

DEFAULTS = {
    'datanommer.enabled': False,
    # Put a sqlite db in the current working directory if the user doesn't
    # specify a real location.
    'datanommer.sqlalchemy.url': 'sqlite:///datanommer.db',
}


import logging
log = logging.getLogger("fedmsg")


class Nommer(fedmsg.consumers.FedmsgConsumer):
    topic = "*"
    config_key = 'datanommer.enabled'

    def __init__(self, hub):
        super(Nommer, self).__init__(hub)

        # If fedmsg doesn't think we should be enabled, then we should quit
        # before setting up all the extra special zmq machinery.
        # _initialized is set in moksha.api.hub.consumer
        if not getattr(self, "_initialized", False):
            return

        # Setup a sqlalchemy DB connection (postgres, or sqlite)
        datanommer.models.init(self.hub.config['datanommer.sqlalchemy.url'])

    def consume(self, message):
        log.debug("Nomming %r" % message)
        try:
            datanommer.models.add(message['body'])
        except Exception as e:
            log.error("Got error (trying without uuid): %s" % str(e))
            datanommer.models.session.rollback()
            # Assume it's all the uuid/msg_id's fault and try again
            uuid = message['body'].get('msg_id', None)
            message['body']['msg_id'] = None
            # Also remove cert and sig
            if 'certificate' in message['body']:
                del message['body']['certificate']
            if 'signature' in message['body']:
                del message['body']['signature']
            try:
                datanommer.models.add(message['body'])
            except Exception as e:
                log.error("Got error (again): %s" % str(e))
                datanommer.models.session.rollback()
            else:
                # Adding the message succeeded, so it's time to tell somebody
                fedmsg.publish(topic='datanommer.wat', msg={'uuid': uuid})
