#!/bin/bash

set -e

# run the application
fedora-messaging consume --callback datanommer.consumer:Nommer
