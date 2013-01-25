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
`Contributing <http://fedmsg.readthedocs.org/en/latest/contributing/>`_ \
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


Cloning upstream the git repo¶
------------------------------
The source code is on github. 

Get fedmsg::

    (datanommer)$ git clone https://github.com/ralphbean/fedmsg.git

Get datanommer::

    (datanommer)$ git clone https://github.com/ralphbean/datanommer.git

Set up fedmsg::

    (datanommer)$ cd fedmsg

For development, avoid editing master branch. Checkout develop branch::

    (datanommer)$ git checkout develop
    (datanommer)$ python setup.py develop

Switch to datanommer:: 

    (datanommer)$ cd ../datanommer

Please note that you should set up the three packages in the following \
sequence: "datanommer.models", "datanommer.commands" and \
"datanommer.consumer". Go to the three subfolders in sequence and type::

    (datanommer)$ git checkout develop
    (datanommer)$ python setup.py develop

Create datanommer db::

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

If you result is::

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
