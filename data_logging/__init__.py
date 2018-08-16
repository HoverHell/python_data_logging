# coding: utf-8
"""
Overview:
 * Handler: Either of:
   * WatchedFileHandler:
     * Simplest configuration.
     * `Watched` for supporting logrotate.
   * TaggedSysLogHandler:
     * More / most performant.
     * Needs system-wide configuration: see the
       `python-data-logging-syslog` debian package.
 * `annotators`: can be used for adding data to the record (based off filters).
   * `time_diff_annotator`: `time_diff`, time since the last record.
   * `full_hostname_annotator`: `hostname`, current host fqdn.
 * Formatter:
   * `JSONFormatter`: turns a logging record into a JSON line.
     * Heavily parametrised and subclassable.
 * `utils`: some additional functions, both for internal use and for
   making a configuration.
"""

from __future__ import division, absolute_import, print_function, unicode_literals
