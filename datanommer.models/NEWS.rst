=============
Release Notes
=============

For ``datanommer.models``

.. towncrier release notes start

v1.2.0
======

Released on 2024-04-15.
This is a feature release that adds schema packages and upgrades the SQLAlchemy
API to the 2.0 style.

Features
^^^^^^^^

* Upgrade to the SQLAlchemy 2.0 API (`981e2a4
  <https://github.com/fedora-infra/datanommer/commit/981e2a4>`_).
* Add a few schema packages to the dependencies.

Development Improvements
^^^^^^^^^^^^^^^^^^^^^^^^

* Use Ruff instead of flake8 and isort and bandit (`4f7ffaa
  <https://github.com/fedora-infra/datanommer/commit/4f7ffaa>`_).


v1.1.0
======

Released on 2023-09-22.
This is a feature release that adds ``koji-fedoramessaging-messages`` as a
dependency to interpret koji messages, and updates a lot of our other
dependencies.

Dependency Changes
^^^^^^^^^^^^^^^^^^

* Drop support for python 3.7, add support for python 3.10 (`PR#890
  <https://github.com/fedora-infra/datanommer/pull/890>`_).
* Add the ``koji-fedoramessaging-messages`` package (`#1257
  <https://github.com/fedora-infra/datanommer/issues/1257>`_).


v1.0.4
======

Released on 2022-05-31.
This is a minor release:

- adds fedora-messaging schema packages
- doesn't require a version of bodhi-messages in the dev deps
- adjusts pyproject for spec needs
- fixes integration of Alembic


v1.0.3
======

Released on 2022-03-18. This is a minor release:

- support fedora-messaging 3.0+
- update dependencies


v1.0.0
======

Released on 2022-01-17.

This is a major release that uses TimescaleDB to store the data.
The list of changes is too big to list here.
