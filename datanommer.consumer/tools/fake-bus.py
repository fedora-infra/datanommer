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
#!/usr/bin/env python
""" This script just emits a bunch of random messages on an endpoint to which
busmon is listening.  Run it while busmon is running to provide it with fake
test data.

    :author: Ralph Bean <rbean@redhat.com>

"""

import random
import time
import simplejson

import fedmsg


def main():
    # Prepare our context and publisher
    fedmsg.init(name="bodhi.marat")

    # Probabilities of us emitting an event on each topic.
    probs = {
        'bodhi': 0.35,
        'fedoratagger': 0.2,
        'pkgdb': 0.1,
        'fas': 0.2,
        'mediawiki': 0.3,
    }

    # Main loop
    i = 0
    while True:
        for service, thresh in probs.iteritems():
            if random.random() < thresh:
                print service, thresh
                fedmsg.send_message(
                    topic='fake_data',
                    msg={'test': "Test data." + str(i)},
                    modname=service,
                )
                i = i + 1
        time.sleep(random.random())

if __name__ == "__main__":
    main()
