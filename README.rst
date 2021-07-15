**Datanommer is currently in the process of a major migration away from fedmsg to Fedora Messaging. As such, the below readme is outdated, and may not be useful until it is updated** 

datanommer
==========

.. split here

This is datanommer.  It is comprised of only a `fedmsg
<http://github.com/fedora-infra/fedmsg>`_ consumer that stuffs every message in a
sqlalchemy database.

There are also a handful of CLI tools to dump information from the database.


Build Status
------------

.. |master| image:: https://img.shields.io/travis/fedora-infra/datanommer/master.svg
   :alt: Build Status - master branch
   :target: https://travis-ci.org/fedora-infra/datanommer/branches

.. |develop| image:: https://img.shields.io/travis/fedora-infra/datanommer/develop.svg
   :alt: Build Status - develop branch
   :target: https://travis-ci.org/fedora-infra/datanommer/branches

+----------+-----------+
| Branch   | Status    |
+==========+===========+
| master   | |master|  |
+----------+-----------+
| develop  | |develop| |
+----------+-----------+

Try it out
==========


Using a virtualenv
------------------

Using a virtual environment is highly recommended, although this is not a \
must. Using virtualenvwrapper can isolate your development environment. You \
will be able to work on the latest datanommer from git checkout without \
messing the installed datanommer copy in your system.

Install virtualenvwrapper by::

    $ sudo yum install python-virtualenvwrapper


**Note:** If you decide not to use python-virtualenvwrapper, you can always \
use latest update of fedmsg and datanommer in fedora. If you are doing this, \
simply ignore all mkvirtualenv and workon commands in these instructions. \
You can install fedmsg with ``sudo yum install fedmsg``, and datanommer with \
``sudo yum install datanommer``.


Development dependencies
------------------------
Get::

    $ sudo yum install python-virtualenv openssl-devel zeromq-devel gcc

**Note:** If submitting patches, you should check \
`Contributing <https://fedmsg.readthedocs.io/en/stable/contributing/>`_ \
for style guidelines.


Set up virtualenv
-----------------
Create a new, empty virtualenv and install all the dependencies from pypi::

    $ mkvirtualenv datanommer
    (datanommer)$ cdvirtualenv


**Note:** If the mkvirtualenv command is unavailable try \
``source /usr/bin/virtualenvwrapper.sh`` on Fedora (if you do not run Fedora \
you might have to adjust the command a little).  You can also add this \
command to your ``~/.bashrc`` file to have it run automatically for you.


Cloning upstream the git repo
-----------------------------
The source code is on github. 

Get fedmsg::

    (datanommer)$ git clone https://github.com/fedora-infra/fedmsg.git

Get datanommer::

    (datanommer)$ git clone https://github.com/fedora-infra/datanommer.git

Set up fedmsg::

    (datanommer)$ cd fedmsg

For development, avoid editing master branch. Checkout develop branch::

    (datanommer)$ git checkout develop
    (datanommer)$ python setup.py develop

Switch to datanommer:: 

    (datanommer)$ cd ../datanommer

Please note that you should set up the three packages in the following \
sequence: "datanommer.models", "datanommer.commands" and \
"datanommer.consumer".

There is a script that will do this for you::

    (datanommer)$ ./.travis-dev-setup.sh

Or, if for some reason you wanted to do it on your own, go to the three
subfolders in sequence and type::

    (datanommer)$ git checkout develop
    (datanommer)$ python setup.py develop

Finally, initialize the datanommer db::

    (datanommer)$ datanommer-create-db


Try out datanommer
-------------------
Open three terminals to try out the commands. In each of them, activate your \
virtualenv with::

    $ workon datanommer

In one terminal, type::

    (datanommer)$ fedmsg-relay

In another, type::

    (datanommer)$ fedmsg-hub

In a third, emit a message, which gets picked up by the relay, rebroadcasted, \
consumed by datanommer, and inserted into datanommer.db::

    (datanommer)$ echo "this is a test" | fedmsg-logger

Try the commands. Was the message stored?::

    (datanommer)$ datanommer-stats

LoggerMessage should have entries.:: 

    (datanommer)$ datanommer-dump

Inspect the database::

    (datanommer)$ sqlite3 datanommer.db
    > select* from messages;

You should see a line similar to::

    1|1|org.fedoraproject.dev.logger.log|2012-11-30 23:33:12.077429|||{"log": "this is a test"}


Programming against the datanommer API
--------------------------------------

The ``datanommer.models`` module provides an API that will let other trusted
applications make queries against datanommer.  It was designed specifically
for use by the `datagrepper <https://github.com/fedora-infra/datagrepper>`_
and `fedbadges <https://github.com/fedora-infra/fedbadges>`_ applications.
Untrusted applications will have to go another route (like make http GET
queries on datagrepper); we simply can't allow them a direct connection
to the datanommer database.

*Querying Messages*

Before making any queries, you'll need to initialize the module-level session
for ``datanommer.models``:

.. code-block:: python

   import datanommer.models as m
   url = 'sqlite:///some_database.db'
   m.init(url)

In our production environment, datanommer's db URL is kept in
``/etc/fedmsg.d/``, so you can conveniently access it like this:

.. code-block:: python

   import fedmsg.config
   config = fedmsg.config.load_config()
   url = config['datanommer.sqlalchemy.url']

   import datanommer.models as m
   m.init(url)

You can query datanommer from python like this:

.. code-block:: python

   import datetime

   # Get all messages in the last hour
   then = datetime.datetime.now() - datetime.timedelta(hours=1)
   messages = m.Message.query.filter(m.Message.timestamp>=then).all()

It's SQLAlchemy, after all.  You can query for only bodhi messages like this:

.. code-block:: python

   messages = m.Message.query.filter(m.Message.category=='bodhi').all()

Another useful query might be to find all the messages for the user
`@lmacken <https://github.com/lmacken>`_ which you could accomplish with this:

.. code-block:: python

   user = m.User.query.filter(m.User.name=='lmacken').one()
   messages = user.messages

Conversely, you can get the ``User`` and ``Package`` objects associated
with a message by accessing attributes:

.. code-block:: python

   message = m.Message.query.first()
   packages = message.packages
   users = message.users

*Formatting Messages*

The raw JSON message is accessible from a ``.msg`` attribute:

.. code-block:: python

   for message in messages:
       print message.msg

Of course, the datanommer Message model plays nice with fedmsg's utilities.
You can use ``fedmsg.encoding`` to print a nicely formatted version of
your query:

.. code-block:: python

   import fedmsg.encoding
   for message in messages:
       print fedmsg.encoding.pretty_dumps(message)

And, if you ``yum install python-fedmsg-meta-fedora-infrastructure``, you'll
have access to all the metadata processors provided there.  Install it and try:

.. code-block:: python

   import fedmsg.config
   import fedmsg.meta

   config = fedmsg.config.load_config()

   for message in messages
       print fedmsg.meta.msg2title(message, **config)
       print " ", fedmsg.meta.msg2subtitle(message, **config)

Take a look at the `list of topics and message types
<https://fedora-fedmsg.readthedocs.io/en/latest/>`_ that ``fedmsg.meta`` understands.

Migration with Alembic
-----------------------

When the database models are changed, we use alembic to retain the data. \
Alembic is located in the models::

    (datanommer)$ cd datanommer.models

To check the current models version::

    (datanommer)$ alembic current

If your models are up to date, you should see::

    INFO  [alembic.migration] Context impl SQLiteImpl.
    INFO  [alembic.migration] Will assume transactional DDL.
    Current revision for sqlite:///../datanommer.db: 198447250956 -> ae2801c4cd9 (head), add category column

If your result is::

    INFO  [alembic.migration] Context impl SQLiteImpl.
    INFO  [alembic.migration] Will assume transactional DDL.
    Current revision for sqlite:///../datanommer.db: None

then migrate to the most recent version with::

    (datanommer)$ alembic upgrade head

You should see::

    INFO  [alembic.migration] Context impl SQLiteImpl.
    INFO  [alembic.migration] Will assume transactional DDL.
    INFO  [alembic.migration] Running upgrade None -> 198447250956
    INFO  [alembic.migration] Running upgrade 198447250956 -> ae2801c4cd9
