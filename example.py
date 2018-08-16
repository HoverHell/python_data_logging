#!/usr/bin/env python
# coding: utf8
"""
A test / example.

NOTE: requires the '.log' directory to exist.
"""

from __future__ import division, absolute_import, print_function, unicode_literals

import logging
import logging.config
import data_logging.example


def main_base():
    logging.config.dictConfig(data_logging.example.SAMPLE_LOGGING_CONFIG)

    logger = logging.getLogger('some_logger')

    logger.info("A message ⋯", extra=dict(extra_field_a=1, extra_field_b='⋯'))
    logger.info("A bytes message ⋯".encode("utf-8"), extra=dict(extra_field_a=1, extra_field_b='⋯'))

    try:
        raise Exception("A test exception ⋯")
    except Exception:
        logger.exception("Just testing ⋯")

    try:
        raise Exception("A bytes test exception ⋯".encode("utf-8"))
    except Exception:
        logger.exception("Just testing bytes ⋯".encode("utf-8"))

    return locals()


def main():
    import os

    # Same as in the sample config.
    fln = '.log/debug_json.log'

    # Make sure the dir exists
    try:
        os.makedirs(os.path.dirname(fln))
    except OSError:
        pass  # probably exists / don't bother

    try:
        with open(fln, 'w') as fo:  # Empty the file
            pass
    except IOError:
        pass

    result = main_base()

    try:
        with open(fln) as fo:  # Read the results
            data = fo.read()
    except IOError:
        print("(!?) no data")
    else:
        print(data)

    return result


if __name__ == '__main__':
    main()
