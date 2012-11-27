datanommer
==========

.. split here

This is datanommer.  It is comprised of only a `fedmsg
<http://github.com/ralphbean/fedmsg>`_ consumer that stuffs every message in a
sqlalchemy database.

There are also a handful of CLI tools to dump information from the database.

Build Status
------------

.. |master| image:: https://secure.travis-ci.org/ralphbean/datanommer.png?branch=master
   :alt: Build Status - master branch
   :target: http://travis-ci.org/#!/ralphbean/datanommer

.. |develop| image:: https://secure.travis-ci.org/ralphbean/datanommer.png?branch=develop
   :alt: Build Status - develop branch
   :target: http://travis-ci.org/#!/ralphbean/datanommer

+----------+-----------+
| Branch   | Status    |
+==========+===========+
| master   | |master|  |
+----------+-----------+
| develop  | |develop| |
+----------+-----------+

Try it out
==========

Install it on your local machine::

    $ sudo yum -y install datanommer

Create the file ``/etc/fedmsg.d/datanommer.py`` and add the following content::

    config = {
        'datanommer.enabled': True,
        # This is not a safe location for a sqlite db...
        'datanommer.sqlalchemy.url': 'sqlite:////tmp/datanommer.db',
    }

Create datanommer's DB::

    $ /usr/bin/datanommer-create-db

Start fedmsg-relay and datanommer::

    $ sudo service fedmsg-relay start
    $ sudo service fedmsg-hub start  # this will find datanommer's consumer.

Emit a message, which gets picked up by the relay, rebroadcasted, consumed by datanommer, and stuffed into ``/tmp/datanommer.db``::

    $ echo "this is a test" | fedmsg-logger

Use datanommer's clumsy CLI tools to inspect the DB.  Was the message stored?

::

    $ /usr/bin/datanommer-stats
    $ /usr/bin/datanommer-dump
