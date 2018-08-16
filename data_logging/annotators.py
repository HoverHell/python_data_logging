# coding: utf-8
"""
Annotating filters

https://docs.python.org/2/howto/logging-cookbook.html#adding-contextual-information-to-your-logging-output
"""

from __future__ import division, absolute_import, print_function, unicode_literals

import time
import logging
import socket  # for hostnames
from .utils import simple_cached_wrap, to_str


__all__ = (
    'time_diff_annotator',
    'short_hostname_annotator',
    'full_hostname_annotator',
)


_NOT_AVAILABLE = object()


class Annotator(logging.Filter):
    """ A convenience abstract class for most annotators """

    attribute_name = None
    # Shortcut for using the previously generated value.
    use_cached_value = True

    def __init__(self, *args, **kwargs):
        self.attribute_name = kwargs.pop('attribute_name', None) or self.attribute_name
        if self.attribute_name is None:
            raise Exception(
                "attribute_name should either be on class or always specified")
        super(Annotator, self).__init__(*args, **kwargs)

    def get_value(self, record, *args, **kwargs):
        raise NotImplementedError

    def _get_value_cached(self, record, *args, **kwargs):
        value = getattr(record, self.attribute_name, _NOT_AVAILABLE)
        if value is not _NOT_AVAILABLE:
            return value
        return self.get_value(record, *args, **kwargs)

    def filter(self, record):
        """ “annotate”, actually """
        if self.use_cached_value:
            value = self._get_value_cached(record)
        else:
            value = self.get_value(record)
        setattr(record, self.attribute_name, value)
        return True


class time_diff_annotator(Annotator):
    """ A simple filter that adds `time_diff` to the record, which
    shows the time from the last log line of the same process. Mostly
    useful in development. """

    attribute_name = 'time_diff'

    def __init__(self, *args, **kwargs):
        self.last_ts = time.time()
        super(time_diff_annotator, self).__init__(*args, **kwargs)

    def get_value(self, record, *args, **kwargs):
        now = time.time()
        result = now - self.last_ts
        self.last_ts = now
        return result


def make_simple_annotating_filter(name, func):

    def get_value(self, *args, **kwargs):
        return func()

    filter_class = type(
        to_str('_%s_annotator'), (Annotator,),
        dict(attribute_name=name, get_value=get_value))
    return filter_class


# getfqdn occasionally might use network, which is why it is better to
# cache it.
cached_getfqdn = simple_cached_wrap(socket.getfqdn)


short_hostname_annotator = make_simple_annotating_filter('hostname', socket.gethostname)
full_hostname_annotator = make_simple_annotating_filter('hostname', cached_getfqdn)


def get_celery_task_attributes():
    result = dict(task_name=None, task_id=None, meta=None, meta_meta=None)
    try:
        # See celery.app.log.TaskFormatter
        from celery._state import get_current_task
        task = get_current_task()
        if not task:
            return dict(result, meta='no_task')
        if not task.request:
            return dict(result, meta='no_task_request')
        return dict(result, task_name=task.name, task_id=task.request.id)
    except Exception as exc:
        return dict(result, meta='error', meta_meta=exc)


# NOTE: using these together could be more performant, but at the moment too bothersome.
celery_task_name_annotator = make_simple_annotating_filter(
    'celery_task_name', lambda: get_celery_task_attributes()['task_name'])
celery_task_id_annotator = make_simple_annotating_filter(
    'celery_task_id', lambda: get_celery_task_attributes()['task_id'])


class celery_process_name_annotator(Annotator):

    attribute_name = 'celery_process'
    skip_main_process = True

    def get_value(self, *args, **kwargs):  # pylint: disable=arguments-differ
        # see celery.utils.log
        try:
            try:
                from billiard import current_process
            except Exception:
                from billiard.process import current_process
            result = current_process()._name
            if self.skip_main_process and result == 'MainProcess':
                return None
            return result
        except Exception:
            return None


class extra_defaults_annotator(Annotator):
    """
    Adds multiple specified constant values to the record if they were not
    previously set (`setdefault`-like).
    """

    attribute_name = '__dummy_aan__'

    def __init__(self, *args, **kwargs):
        self.defaults = kwargs.pop('defaults')
        super(extra_defaults_annotator, self).__init__(*args, **kwargs)

    def get_value(self, *args, **kwargs):  # pylint: disable=arguments-differ
        raise Exception("Irrelevant here")

    def filter(self, record):
        for key, value in self.defaults.items():
            current = getattr(record, key, _NOT_AVAILABLE)
            if current is _NOT_AVAILABLE:
                setattr(record, key, value)
        return True
