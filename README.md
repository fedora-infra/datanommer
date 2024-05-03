# Datanommer

Datanommer is an application that is comprised of only a Fedora Messaging consumer that places every message into a Postgres / TimescaleDB database.

It is comprised of 3 modules:

* **datanommer.consumer**: the Fedora Messaging consumer that monitors the queue and places every message into the database
* **datanommer.models**: the database models used by the consumer. These models are also used by [Datagrepper](https://github.com/fedora-infra/datagrepper), [FMN](https://github.com/fedora-infra/fedbadges), and [fedbadges](https://github.com/fedora-infra/fmn). Typically, to access the information stored in the database by datanommer, use the [Datagrepper](https://github.com/fedora-infra/datagrepper) JSON API.
* **datanommer.commands**: a set of commandline tools for use by developers and sysadmins.

Refer to the [online documentation](https://datanommer.readthedocs.io/) for details.
