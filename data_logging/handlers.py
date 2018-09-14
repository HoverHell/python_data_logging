# coding: utf8

from __future__ import division, absolute_import, print_function, unicode_literals

import os
from logging import handlers
from .utils import to_bytes


__all__ = (
    'TaggedSysLogHandler',
)


class TaggedSysLogHandlerBase(handlers.SysLogHandler):
    """ A version of SysLogHandler that adds a tag to the logged line
    so that it can be sorted by the syslog daemon into files.

    Generally equivalent to using a formatter but semantically more
    similar to FileHandler's `filename` parameter.

    Automatically sets the `address` if it was not specified.
    """
    def __init__(self, *args, **kwargs):
        address = kwargs.get('address')
        if address is None:
            address = '/dev/log-ext' if os.path.exists('/dev/log-ext') else '/dev/log'
            kwargs['address'] = address
        self.syslog_tag = to_bytes(kwargs.pop('syslog_tag'))
        super(TaggedSysLogHandlerBase, self).__init__(*args, **kwargs)

    def format(self, *args, **kwargs):  # pylint: disable=arguments-differ
        res = super(TaggedSysLogHandlerBase, self).format(*args, **kwargs)
        res = to_bytes(res)
        return self.syslog_tag + b" " + res


class TaggedSysLogHandler(TaggedSysLogHandlerBase):
    """ An addition that sets the SO_SNDBUF to a large value to allow large log lines. """
    _sndbuf_size = 5 * 2**20

    def __init__(self, *args, **kwargs):
        self._sbdbuf_size = kwargs.pop('sbdbuf_size', self._sndbuf_size)
        super(TaggedSysLogHandler, self).__init__(*args, **kwargs)
        self.configure_socket(self.socket)

    def configure_socket(self, sock):
        import socket
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, self._sndbuf_size)
