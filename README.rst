datanommer
==========

This is an experimental stab at datanommer.  It is comprised only of a `fedmsg
<http://github.com/ralphbean/fedmsg>`_ consumer that stuffs every message in a
mongodb collection.

Try it out
==========

Install mongodb::

  $ sudo yum -y install mongodb mongodb-server

You need to start mongod, normally this is done with
``systemctl start mongod.service``, however this is an `outstanding bug
<https://bugzilla.redhat.com/show_bug.cgi?id=837904>`_ which will get in your
way.  There is a workaround described in the bugzilla ticket.

Once you're over that, install and use threebean's favorite
python dev tool::

  $ sudo yum -y install python-virtualenvwrapper
  $ mkvirtualenv nomnomnom

Get this code::

  $ git clone git://github.com/ralphbean/datanommer.git
  $ cd datanommer

Setup all the deps::

  $ workon nomnomnom
  $ pip install -e . --use-mirrors

Open two terms and, in the first, run a fake bus::

  $ workon nomnomnom
  $ python tools/fake-bus.py

In the second, run the fedmsg-hub (which picks up the datanommer consumer and
starts nomming)::

  $ workon nomnomnom
  $ fedmsg-hub
