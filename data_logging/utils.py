# coding; utf8
"""
Additional assorted helpers.
"""

from __future__ import division, absolute_import, print_function, unicode_literals


import os
import posixpath
import functools
from .subsix import text, PY_3


__all__ = (
    'simple_cached_wrap',
)


DEFAULT_ENCODING = 'utf-8'


def simple_cached_wrap(func):
    """ A very simple memoizer that saves the first call result permanently """

    _cache = {}

    @functools.wraps(func)
    def simple_cached_wrapped(*args, **kwargs):
        try:
            return _cache[None]
        except KeyError:
            pass

        result = func(*args, **kwargs)
        _cache[None] = result
        return result

    # Make the cache more easily accessible
    simple_cached_wrapped._cache = _cache  # pylint: disable=protected-access
    return simple_cached_wrapped


def to_bytes(st, **kwargs):
    if isinstance(st, bytes):
        return st
    if not isinstance(st, text):
        return st
    return st.encode(encoding=DEFAULT_ENCODING, **kwargs)


def to_text(st, **kwargs):
    if isinstance(st, text):
        return st
    if not isinstance(st, bytes):
        return st
    return st.decode(encoding=DEFAULT_ENCODING, **kwargs)


if PY_3:
    to_str = to_text
else:
    to_str = to_bytes


def force_bytes(val, **kwargs):
    if isinstance(val, bytes):
        return val
    if isinstance(val, text):
        return to_bytes(val, **kwargs)
    return to_bytes(repr(val), **kwargs)


def force_text(val, **kwargs):
    if isinstance(val, text):
        return val
    if isinstance(val, bytes):
        return to_text(val, **kwargs)
    return to_text(repr(val), **kwargs)


def split_list(lst, cond):
    """ Split list items into two into (matching, non_matching) by
      `cond(item)` callable """
    matched, unmatched = [], []
    for item in lst:
        if cond(item):
            matched.append(item)
        else:
            unmatched.append(item)
    return matched, unmatched


def slstrip(st, subst, require=False):
    """ Strip a substring `subst` from the left of `st` """
    if st.startswith(subst):
        return st[len(subst):]
    if require:
        raise ValueError("st does not start with subst", st, subst)
    return st


def srstrip(st, subst, require=False):
    """ Strip a substring `subst` from the left of `st` """
    if st.endswith(subst):
        return st[:len(subst)]
    if require:
        raise ValueError("st does not end with subst", st, subst)
    return st


_MAKE_FILE_LOGGER_DOC_COMMON = """
Uses a common base logger config and a common environment config.

:param env: an environment dict:

  :param logdir_rel: relative log directory, e.g. project-specific
  path, e.g. 'my-project'.

  :param logdir_base: base log directory, should match the one in the
  syslog config, default '/var/log'.

  :param default_config: defaults for the logger config, default is
  taken from `data_logging.utils.DEFAULT_LOGGER_CONFIG`.

:param config: the logger config.

  :param filename: the only required parameter, filename relative to
  `logdir_base`.
"""


DEFAULT_LOGGER_CONFIG = dict(
    level=1,
    filters=('time_diff', 'hostname'),
    formatter='json',
)


def make_file_logger_file(env, config):
    """Make a file logger that logs directly to a file."""

    result = dict(env.get('default_config', DEFAULT_LOGGER_CONFIG))
    result['class'] = env.get('filelogger', 'logging.handlers.WatchedFileHandler')
    result.update(config)
    filename = result['filename']
    if not filename.startswith('/'):
        logdir_base = env.get('logdir_base', '/var/log')
        logdir_rel = env['logdir_rel']
        filename = os.path.join(logdir_base, logdir_rel, filename)
    if not filename.endswith('.log'):
        filename = '%s.log' % (filename,)
    result['filename'] = filename
    return result

make_file_logger_file.__doc__ = make_file_logger_file.__doc__ + _MAKE_FILE_LOGGER_DOC_COMMON


def make_file_logger_syslog(env, config):
    """Make a file logger that logs to a file over specifically configured syslog daemon."""
    result = dict(env.get('default_config', DEFAULT_LOGGER_CONFIG))
    result['class'] = env.get('syslogger', 'data_logging.handlers.TaggedSysLogHandler')
    result['address'] = '/dev/log'
    result.update(config)
    filename = result.pop('filename')
    if filename.startswith('/'):
        logdir_base = env.get('logdir_base', '/var/log')
        filename = slstrip(filename, logdir_base, require=True)
    else:
        logdir_rel = env['logdir_rel']
        filename = posixpath.join(logdir_rel, filename)
    # NOTE: the '.log' is appended automatically in the default syslog config.
    filename = srstrip(filename, '.log')
    result['syslog_tag'] = 'file__%s' % (filename,)
    return result


make_file_logger_syslog.__doc__ = make_file_logger_syslog.__doc__ + _MAKE_FILE_LOGGER_DOC_COMMON


def make_file_logger_null(env=None, config=None):  # pylint: disable=unused-argument
    """ A 'fake' make_file_logger that returns a null logger """
    res = {'class': 'logging.NullHandler'}
    return res
