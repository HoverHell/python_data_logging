# coding: utf-8

from __future__ import division, absolute_import, print_function, unicode_literals

from . import utils
from .utils import to_str


ANNOTATING_FILTERS = {
    'time_diff': {'()': 'data_logging.annotators.time_diff_annotator'},
    'hostname': {'()': 'data_logging.annotators.full_hostname_annotator'},
}
DEFAULT_LOGGER_CONFIG = dict(
    utils.DEFAULT_LOGGER_CONFIG,
    filters=tuple(ANNOTATING_FILTERS.keys()))
LOGGING_ENV_DEV = {
    'logdir_base': '.',
    'logdir_rel': '.log',
    'default_config': DEFAULT_LOGGER_CONFIG}
LOGGING_ENV_SYS = {
    'logdir_rel': 'my-project',
    'default_config': DEFAULT_LOGGER_CONFIG}
LOGGING_ENV = LOGGING_ENV_DEV

SAMPLE_LOGGING_CONFIG = dict(
    version=1,
    disable_existing_loggers=False,
    formatters=dict(
        json=dict(
            {'()': 'data_logging.formatters.JSONFormatter'},
            defaults=dict(marker='data_logging_example'),
            # # example:
            # rename_fields=dict(hostname='fqdn', process='pid'),
        ),
        # ...
    ),
    filters=dict(
        ANNOTATING_FILTERS,
        # some_other_filter={...},
    ),
    handlers=dict(
        syslog_full=utils.make_file_logger_syslog(LOGGING_ENV, dict(filename='debug_json')),
        file_full=utils.make_file_logger_file(LOGGING_ENV, dict(filename='debug_json')),
    ),
    loggers=dict(
        # ...
    ),
    root=dict(
        handlers=(
            'file_full',
        ),
        level=1,
    ),
)


_logrotate_example = """
# Project-specific path.
/var/log/my-project/*.log {
    # Project-specific things.
    rotate 40
    compress
    daily
    missingok
    # Make the newly created files syslog-writable.
    # 'myproject' is the user the service runs under.
    create 664 myproject syslog
    # Notify syslog about the files having been rotated.
    postrotate
        # Why all the silencing is unclear, might be unneeded.
        service rsyslog reload >/dev/null 2>&1 || true
    endscript
}
"""

_postinst_example = """
# Make sure the logdir exists and is syslog-writable (as normally
# syslog won't have a permission to create a folder in /var/log).
# Project-specific path.
LOGDIR="/var/log/my-project"
mkdir -p "$LOGDIR"
# 'myproject' is the user the service runs under.
chown -R myproject:syslog "$LOGDIR"
chmod ug=rwX,o=rX -R "$LOGDIR"
"""
