# coding: utf8

from __future__ import division, absolute_import, print_function, unicode_literals

import datetime
import math

from .utils import simple_cached_wrap
from .subsix import PY_3
if PY_3:
    from .subsix import long


def get_utc_offset():
    """ Return rough estimate of utc offset """
    timedelta = datetime.datetime.now() - datetime.datetime.utcnow()
    # XXX: `return -time.timezone`?
    return timedelta.total_seconds()


def create_utc_shift_stamp(utc_offset):
    """ Hack for replacing the buggy '%z' datetime formatter """
    sign = "+" if utc_offset >= 0 else "-"
    abs_utc_offset = long(abs(math.ceil(utc_offset)))
    hours, minutes_in_sec = divmod(abs_utc_offset, 3600)
    minutes = minutes_in_sec / 60
    return "{sign}{hours:0>2}:{minutes:0>2}".format(
        sign=sign, hours=int(hours), minutes=int(minutes))


def get_utc_shift_stamp():
    return create_utc_shift_stamp(get_utc_offset())


@simple_cached_wrap
def get_utc_shift_stamp_cached():
    """ ...

    WARNING: this might occasionally be a bad idea if this is used
    with a timezone that has DST or changes at all. Although
    the non-cached one would be a bit problematic too.
    """
    # TODO: consider using utctimestamp and '+00:00'
    return get_utc_shift_stamp()
