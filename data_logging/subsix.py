# coding: utf8

from __future__ import division, absolute_import, print_function, unicode_literals

import sys

PY_3 = sys.version_info >= (3,)
PY_37 = sys.version_info >= (3, 7)


if PY_3:
    long = int
    text = str
else:
    text = unicode  # pylint: disable=undefined-variable
