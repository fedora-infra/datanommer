=============
Release Notes
=============

.. towncrier release notes start

v1.2.0
======

Released on 2024-04-15.
This is a feature release that adds the datanommer-extract-users script.

Features
^^^^^^^^

* Add the datanommer-extract-users script to fill the usernames table with data
  from recently-added message schemas (`320a466
  <https://github.com/fedora-infra/datanommer/commit/320a466>`_).

Development Improvements
^^^^^^^^^^^^^^^^^^^^^^^^

* Use Ruff instead of flake8 and isort and bandit (:issue:`4f7ffaa`
     `#4f7ffaa <https://github.com/fedora-infra/datanommer/issues/4f7ffaa>`_).


v1.1.0
======

Released on 2023-09-22.
This is a feature release that adds support for Python 3.10, drops support for
Python 3.7, and improves the database creation for Alembic integration.

Dependency Changes
^^^^^^^^^^^^^^^^^^

* Drop support for python 3.7, add support for python 3.10 (`PR#890
  <https://github.com/fedora-infra/datanommer/pull/890>`_).

Features
^^^^^^^^

* Use Alembic to stamp the database when creating it. This requires adding a
  config variable ``alembic_ini`` in the fedora-messaging configuration file
  that points to the ``alembic.ini`` file. (`PR#815
  <https://github.com/fedora-infra/datanommer/pull/815>`_).


v1.0.3
======

Released on 2022-03-18. This is a minor release:

- support fedora-messaging 3.0+
- update dependencies
