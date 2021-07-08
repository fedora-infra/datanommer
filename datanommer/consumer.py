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
import logging

import fedmsg
import fedmsg.consumers

import datanommer.models


DEFAULTS = {
    "datanommer.enabled": False,
    # Put a sqlite db in the current working directory if the user doesn't
    # specify a real location.
    "datanommer.sqlalchemy.url": "sqlite:///datanommer.db",
}


log = logging.getLogger("fedmsg")


class Nommer(fedmsg.consumers.FedmsgConsumer):
    topic = "*"
    config_key = "datanommer.enabled"

    def __init__(self, hub):
        # The superclass __init__() subscribes the hub to the topic specified
        # by the consumer. If we have a topic we want use instead of "*", it
        # needs to be set before calling the superclass.
        if "datanommer.topic" in hub.config:
            self.topic = hub.config["datanommer.topic"]

        super().__init__(hub)

        # If fedmsg doesn't think we should be enabled, then we should quit
        # before setting up all the extra special zmq machinery.
        # _initialized is set in moksha.api.hub.consumer
        if not getattr(self, "_initialized", False):
            return

        # Setup a sqlalchemy DB connection (postgres, or sqlite)
        datanommer.models.init(self.hub.config["datanommer.sqlalchemy.url"])

    def consume(self, message):
        log.debug("Nomming %r" % message)
        try:
            datanommer.models.add(message)
        except Exception:
            datanommer.models.session.rollback()
            raise
