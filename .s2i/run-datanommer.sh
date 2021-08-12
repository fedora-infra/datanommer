#!/bin/bash

set -e

# We install the app in a specific virtualenv:
export PATH=/opt/app-root/src/.local/venvs/datanommer/bin:$PATH

# Run the application
fedora-messaging consume --callback datanommer.consumer:Nommer
