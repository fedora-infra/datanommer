# datanommer

Datanommer is an application that is comprised of only a Fedora Messaging consumer that places every message into a Postgres / TimescaleDB database.

It is comprised of 3 modules:

* **datanommer.consumer**: the Fedora Messaging consumer that monitors the queue and places every message into the database
* **datanommer.models**: the database models used by the consumer. These models are also used by [Datagrepper](https://github.com/fedora-infra/datagrepper), [FMN](https://github.com/fedora-infra/fedbadges), and [fedbadges](https://github.com/fedora-infra/fmn). Typically, to access the information stored in the database by datanommer, use the [Datagrepper](https://github.com/fedora-infra/datagrepper) JSON API.
* **datanommer.commands**: a set of commandline tools for use by developers and sysadmins.


## Development Environment
Vagrant allows contributors to get quickly up and running with a datanommer development environment by automatically configuring a virtual machine. 

The datanommer Vagrant environment is configured to be empty when first provisioned, but to consume messages from the stage Fedora Messaging queue.

### Install vagrant
To get started, run the following commands to install the Vagrant and Virtualization packages needed, and start the libvirt service:

    $ sudo dnf install ansible libvirt vagrant-libvirt vagrant-sshfs vagrant-hostmanager
    $ sudo systemctl enable libvirtd
    $ sudo systemctl start libvirtd

### Checkout and Provision
Next, check out the datanommer code and run vagrant up:

    $ git clone https://github.com/fedora-infra/datanommer
    $ cd datanommer
    $ vagrant up

### Using the development environment
SSH into your newly provisioned development environment:

    $ vagrant ssh

The vagrant setup also defines 4 handy commands to interact with the datanommer consumer: 

    $ datanommer-consumer-start
    $ datanommer-consumer-stop
    $ datanommer-consumer-restart
    $ datanommer-consumer-logs

Note also, that the commands provided by datanommer.commands are also available to interact with the datanommer database:

    $ datanommer-dump
    $ datanommer-latest
    $ datanommer-stats
    $ datanommer-create-db

### Running the tests
Datanommer is comprised of 3 seperate modules in this single repository. There is a handy script in the top directory of this repo to run the tests on all 3 modules:

    $ ./runtests.sh

However, tests can also be run on a single module by invotking tox in that modules' directory. For example:

    $ cd datanommer.models/
    $ tox

Note, that the tests use virtual environments that are not created from scratch with every subsequent run of the tests. Therefore, **when changes happen to dependencies, the tests may fail to run correctly**. To recreate the virtual envrionments,  run the tests commands with the `-r` flag, for example:

    $ ./runtests.sh -r

or

    $ cd datanommer.models/
    $ tox -r


## Migration with Alembic

When the database models are changed, we use alembic to retain the data. Alembic is located in the models::

    (datanommer)$ cd datanommer.models

To check the current models version::

    (datanommer)$ alembic current

If your models are up to date, you should see::

    INFO  [alembic.migration] Context impl SQLiteImpl.
    INFO  [alembic.migration] Will assume transactional DDL.
    Current revision for postgresql://datanommer:datanommer@localhost/messages: 198447250956 -> ae2801c4cd9 (head), add category column

If your result is::

    INFO  [alembic.migration] Context impl SQLiteImpl.
    INFO  [alembic.migration] Will assume transactional DDL.
    Current revision for postgresql://datanommer:datanommer@localhost/messages: None

then migrate to the most recent version with::

    (datanommer)$ alembic upgrade head

You should see::

    INFO  [alembic.migration] Context impl SQLiteImpl.
    INFO  [alembic.migration] Will assume transactional DDL.
    INFO  [alembic.migration] Running upgrade None -> 198447250956
    INFO  [alembic.migration] Running upgrade 198447250956 -> ae2801c4cd9
