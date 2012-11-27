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

Using a virtual environment is highly recommended, although this is not a must. Using virtualenvwrapper can isolate your development environment. You will be able to work on the latest datanommer from git checkout without messing the installed datanommer copy in your system. 

Install virtualenvwrapper by::

    $ sudo yum install python-virtualenvwrapper


**Note:** If you decide not to use python-virtualenvwrapper, you can always use latest update of fedmsg and datanommer in fedora. If you are doing this, simply ignore all mkvirtualenv and workon commands in these instructions. You can install fedmsg with ``sudo yum install fedmsg``, and datanommer with ``sudo yum install datanommer``.



Development dependencies
------------------------
Get::

    $ sudo yum install python-virtualenv openssl-devel zeromq-devel gcc


Cloning upstream the git repo¶
------------------------------
The source code is on github. 

Create a working folder to hold the source files::

    $ mkdir source
    $ cd source

Get fedmsg::

    $ git clone https://github.com/ralphbean/fedmsg.git

Get datanommer::

    $ git clone https://github.com/ralphbean/datanommer.git


**Note:** If submitting patches, you should check `Contributing <http://fedmsg.readthedocs.org/en/latest/contributing/>`_ for style guidelines.


Set up virtualenv
-----------------
Create a new, empty virtualenv and install all the dependencies from pypi::

    $ mkvirtualenv source


**Note:** If the mkvirtualenv command is unavailable try ``source /usr/bin/virtualenvwrapper.sh`` on Fedora (if you do not run Fedora you might have to adjust the command a little).  You can also add this command to your ``~/.bashrc`` file to have it run automatically for you.


Set up fedmsg::

    (source)$ cd fedmsg
    (source)$ python setup.py develop

Switch to datanommer:: 

    (source)$ cd ../datanommer

Please note that you should set up the three packages in the following sequence: "datanommer.models", "datanommer.commands" and "datanommer.consumer". Go to the three subfolders in sequence and type::

    (source)$ python setup.py develop

Create datanommer db::

    (source)$ datanommer-create-db


Try out datanommer
-------------------
Open three terminals to try out the commands. In each of them, activate your virtualenv with::

    $ workon source

In one terminal, type::

    (source)$ fedmsg-relay

In another, type::

    (source)$ fedmsg-hub

In a third, emit a message, which gets picked up by the relay, rebroadcasted, consumed by datanommer, and stuffed into /tmp/datanommer.db::

    $ echo "this is a test" | fedmsg-logger

Use datanommer's clumsy CLI tools to inspect the DB. Was the message stored?::

    $ /usr/bin/datanommer-stats
    $ /usr/bin/datanommer-dump
