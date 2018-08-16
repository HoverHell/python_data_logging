#!/bin/sh
# ###
# Increment the version, commit.
# ###

set -e

NO_SETUP_FIX=1
PACKAGE_NAME="python-data-logging-syslog"
. ./../_upversion.sh
