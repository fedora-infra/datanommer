#!/bin/bash

trap 'rm -f "$TMPFILE"' EXIT

set -e
set -x

TMPFILE=$(mktemp -t requirements-XXXXXX.txt)

poetry export --dev --without-hashes -f requirements.txt -o $TMPFILE

# Use pip freeze instead of poetry when it fails
#pip freeze --exclude-editable --isolated > $TMPFILE

liccheck -r $TMPFILE
