=============
Release Notes
=============

For ``datanommer.models``

.. towncrier release notes start

v1.4.1
======

Released on 2025-05-30.

Dependency Changes
^^^^^^^^^^^^^^^^^^

* Add schema package mailman3-fedmsg-plugin-schemas (`#8ad6c47 <https://github.com/fedora-infra/datanommer/issues/8ad6c47>`_)
* Add schema package webhook-to-fedora-messaging-messages (`#865855c <https://github.com/fedora-infra/datanommer/issues/865855c>`_)
* Update koji-fedoramessaging-messages (`#c64cb31 <https://github.com/fedora-infra/datanommer/issues/c64cb31>`_)
* Add support for Python 3.9 (for RHEL9) (`#8d63e86 <https://github.com/fedora-infra/datanommer/issues/8d63e86>`_)
* Add the schema package journal-to-fedora-messaging-messages (`#3d9bc35 <https://github.com/fedora-infra/datanommer/issues/3d9bc35>`_)
* Add the `fedora-image-uploader-messages` schema package (`#7da3074 <https://github.com/fedora-infra/datanommer/issues/7da3074>`_)

Bug Fixes
^^^^^^^^^

* Fix unit tests (`#085f5c4 <https://github.com/fedora-infra/datanommer/issues/085f5c4>`_)

Other Changes
^^^^^^^^^^^^^

* Remove unneccessary int call (`#487341f <https://github.com/fedora-infra/datanommer/issues/487341f>`_)


v1.4.0
======

Released on 2024-06-12.

Features
^^^^^^^^

* Rename the unused `username` column to `agent_name` and use it to store the agent name (`#1309 <https://github.com/fedora-infra/datanommer/issues/1309>`_)
* Add a JSON index on the message headers

Bug Fixes
^^^^^^^^^

* Fix the `get_first()` query to actually return only one message


v1.3.0
======

Released on 2024-05-22.

Features
^^^^^^^^

* Add a ``get_first()`` method on ``Message`` to get the first message matching
  a grep-like query (`99fb739 <https://github.com/fedora-infra/datanommer/commit/99fb739>`_).

Bug Fixes
^^^^^^^^^

* Don't compute the total when not necessary (`99fb739 <https://github.com/fedora-infra/datanommer/commit/99fb739>`_).

Documentation Improvements
^^^^^^^^^^^^^^^^^^^^^^^^^^

* Add online documentation with Sphinx, see https://datanommer.readthedocs.io
  (`2631885 <https://github.com/fedora-infra/datanommer/commit/2631885>`_).

Other Changes
^^^^^^^^^^^^^

* Improve the unit tests (`610067f <https://github.com/fedora-infra/datanommer/commit/610067f>`_, `075052c <https://github.com/fedora-infra/datanommer/commit/075052c>`_).
* Update dependencies


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
