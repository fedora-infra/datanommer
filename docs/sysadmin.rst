==============
Sysadmin Guide
==============

Write the sysadmin guide here (installation, maintenance, known issues, etc).

Migration with Alembic
----------------------

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
