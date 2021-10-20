#!/bin/sh

exec /opt/app-root/src/.local/venvs/datanommer/bin/alembic \
    -c /etc/fedora-messaging/alembic.ini \
    upgrade head
