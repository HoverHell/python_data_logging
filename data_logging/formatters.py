# coding: utf-8

from __future__ import division, absolute_import, print_function, unicode_literals

try:
    import simplejson as json
except Exception:
    import json
import datetime
import logging
import traceback
from collections import OrderedDict
from . import datetime_helpers
from . import utils
from .utils import force_text
from .subsix import PY_3, PY_37, text


__all__ = (
    'JSONFormatter',
)


DEFAULT_ORDERED_FIRST = (
    'unixtime', 'full_timestamp',
    # ...
    'name', 'levelname',
    'pid', 'threadName', 'caller_info',
)
DEFAULT_ORDERED_LAST = (
    'exc_info', 'message',
)
DEFAULT_RENAME_FIELDS = {
    'process': 'pid',
}
DEFAULT_EXCLUDED_FIELDS = set((
    # By default, using unixtime and full_timestamp.
    'timestamp', 'timezone',
    # using `threadName` instead.
    'thread',
    # using `process` (pid) instead.
    'processName',
    # processed implicitly into timestamp.
    'created',
    # No known example of use.
    'args',
    # `caller_info` single-field is used instead
    'pathname', 'lineno', 'funcName',
    # `pathname` is more complete than these
    'module', 'filename',
    # using `levelname` instead, usually.
    'levelno',
    # Using fully formatted `exc_info` instead.
    'exc_text',
    # Using `message` through `getMessage`, normally.
    'msg',
    # ...
    'relativeCreated', 'msecs',
))


# # An example record:
# {'args': (),
#  'created': 1466417865.28255,
#  'django_request_id': 'unkn',
#  'exc_info': None,
#  'exc_text': None,
#  'filename': 'base.py',
#  'funcName': '__init__',
#  'levelname': 'INFO',
#  'levelno': 20,
#  'lineno': 198,
#  # Actually, no idea where this one came from.
#  'message': 'Raven is not configured ...',
#  'module': 'base',
#  'msecs': 282.5500965118408,
#  'msg': 'Raven is not configured ...',
#  'name': 'raven.contrib.django.client.DjangoClient',
#  'pathname': '/usr/lib/python2.7/dist-packages/raven/base.py',
#  'process': 11974,
#  'processName': 'MainProcess',
#  'relativeCreated': 4520.756006240845,
#  'thread': 140563671230208,
#  'threadName': 'Dummy-1',
#  'time_diff': 0.0007410049438476562}


class RecordDataFormatterMixin(object):
    """ A mixin for formatters that use the record contents
    (e.g. serialize them into something) rather than a simple
    formatted message.

    Provides `__init__` with configuration (which can be set as
    attributes later as well), and `record_to_data` which returns
    `[(field_name, field_value), ...]`.

    Most things are in separate methods for easier overridability.
    """

    def __init__(self, include_fields=None, exclude_fields=None,
                 ordered_first=None, ordered_last=None, rename_fields=None,
                 skip_none=True, sort_other_fields=False,
                 extra_data=None, message_unicode_catch=True):
        """
        :param include_fields: inclusive list of fields to use. Preserves ordering.

        :param exlude_fields: list of fields to skip.

        :param ordered_first: list of fields to put at the beginning.

        :param ordered_last: list of fields to put at the end.

        :param rename_fields: mapping from record attribute name to
        the log data field name.

        :param skip_none: omit the `(key, None)` cases in the resulting data.

        :param sort_other_fields: for cases where include_fields is
        not specified, sort by name the fields that are not ordered
        explicitly.

        :param extra_data: data (dict or items) to add to all logging records.

        :param message_unicode_catch: catch unicode errors in record.getMessage (bug-crutch).

        NOTE: renaming is done before the ordering, i.e. ordering
        should use the renamed field names.
        """
        super(RecordDataFormatterMixin, self).__init__()
        self.include_fields = include_fields
        self.exclude_fields = set(exclude_fields or ())
        self.ordered_first = ordered_first
        self.ordered_last = ordered_last
        self.rename_fields = rename_fields
        self.skip_none = skip_none
        self.sort_other_fields = sort_other_fields
        self.message_unicode_catch = message_unicode_catch

        if isinstance(extra_data, dict):
            extra_data = list(extra_data.items())
        self.extra_data = extra_data

        # # Since there are some defaults for exlude_fields, using
        # # this is a bit too problematic.
        # if self.include_fields is not None and self.exclude_fields is not None:
        #     # There might be use cases for that, but if both are
        #     # specified it is more likely to be a mistake.
        #     raise Exception("include_fields and exlude_fields shouldn't be used together")

        if self.ordered_first and self.ordered_last:
            if set(self.ordered_first) & set(self.ordered_last):
                raise Exception("ordered_first and ordered_last overlap")

    _record_field_overrides_mapping = None

    def get_record_field_overrides(self):
        """ Cached `make_record_field_overrides` """
        if self._record_field_overrides_mapping is not None:
            return self._record_field_overrides_mapping
        self._record_field_overrides_mapping = self.make_record_field_overrides()
        return self._record_field_overrides_mapping

    def make_record_field_overrides(self):
        """ Gather the record field override functions """
        result = dict(
            message=self.get_record_message,
            timestamp=self.get_record_timestamp,
            timezone=self.get_timezone,
            unixtime=self.get_record_unixtime,
            full_timestamp=self.get_record_full_timestamp,
            exc_info=self.get_record_exc_info,
            # TODO?: exc_info_json? Or do that as a filter?
            caller_info=self.get_record_caller_info,
        )
        return result

    def get_record_message(self, record):
        try:
            return record.getMessage()
        except (UnicodeDecodeError, UnicodeEncodeError):
            if not self.message_unicode_catch:
                raise
        # Crutch-handling:
        # Try to salvage at least something:
        try:
            return record.msg % record.args
        except Exception:
            pass
        try:
            return record.msg
        except Exception as exc:
            try:
                return 'ERR:%r:%r' % (record, exc)
            except Exception as exc:
                pass
        return '???'

    @staticmethod
    def get_record_timestamp(record):
        dt = datetime.datetime.fromtimestamp(record.created)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def get_timezone(record):
        return datetime_helpers.get_utc_shift_stamp_cached()

    @staticmethod
    def get_record_unixtime(record):
        """ NOTE: mainly for uploading to the cluster """
        return int(record.created)

    @staticmethod
    def get_record_full_timestamp_utc(record):
        dt = datetime.datetime.utcfromtimestamp(record.created)
        # Kind-of-isoformat.
        result = dt.strftime('%Y-%m-%d %H:%M:%S.%fZ')
        return result

    @staticmethod
    def get_record_full_timestamp(record):
        dt_utc = datetime.datetime.utcfromtimestamp(record.created)
        dt = datetime.datetime.fromtimestamp(record.created)
        # Kind-of-isoformat.
        result = dt.strftime('%Y-%m-%d %H:%M:%S.%f')
        # Append the supposed timezone.
        tzoffset = (dt - dt_utc).total_seconds()
        tz = datetime_helpers.create_utc_shift_stamp(tzoffset)
        result = '%s%s' % (result, tz)
        return result

    @staticmethod
    def get_record_exc_info(record):
        exc_info = record.exc_info
        if exc_info is None:
            return None
        # return record.formatException()
        _, exc, _ = exc_info
        exc_info_formatted = "".join(
            utils.force_text(val)
            for val in traceback.format_exception(*exc_info))

        # Maybe `repr(exc)` instead? Probably not. Especially in the
        # unicode cases. And format_exception adds the repr() at the
        # end anyway.
        try:
            exc_str = force_text(exc)  # `__repr__` based
        except Exception:
            exc_str = text(exc)  # `__str__` / `__unicode__` based
        result = "%s\n%s" % (
            exc_str,  # str(exc) at the beginning for some readability.
            exc_info_formatted)
        return result

    @staticmethod
    def get_record_caller_info(record):
        """ Make a single-field human-readable combined caller info """
        result = '%s:%s:%s' % (
            record.pathname, record.lineno, record.funcName)
        return result

    def get_record_field(self, record, field):
        """ Some things on the record could've been properties but,
        since that is not the case, have to override """
        mapping = self.get_record_field_overrides()
        try:
            func = mapping[field]
        except KeyError:
            return getattr(record, field, None)
        else:
            return func(record)

    @staticmethod
    def reorder_data(items, ordered_first, ordered_last):
        data_dict_tmp = OrderedDict(items)

        def make_part(lst):
            # NOTE: mutates the `data_dict_tmp`
            result = []
            if not lst:
                return result
            for field in lst:
                try:
                    value = data_dict_tmp.pop(field)
                except KeyError:
                    continue
                result.append((field, value))
            return result

        data_start = make_part(ordered_first)
        data_end = make_part(ordered_last)
        data = data_start + list(data_dict_tmp.items()) + data_end
        return data

    def list_autogenerated_fields(self):
        return (
            'message', 'caller_info',
            'unixtime', 'full_timestamp',
            'timestamp', 'timezone')

    def record_to_fields(self, record):
        if self.include_fields is not None:
            fields = self.include_fields
        else:
            record_vars = vars(record)
            fields = list(record_vars)

            fields_set = set(fields)
            # Specially-processed (i.e. autogenerated) things:
            for key in self.list_autogenerated_fields():
                if key not in fields_set:
                    fields.append(key)

            if self.sort_other_fields:
                fields.sort()

        fields = self.fields_check(fields)
        return fields

    def fields_check(self, fields):
        """ Hook for checks of the resulting fields dict """
        return fields

    def record_to_data(self, record):
        """ Make items (list of `(name, value)`) from the record """

        fields = self.record_to_fields(record)

        rename_fields = self.rename_fields or {}

        # Renames, overrides and excludes in one pass.
        data = [
            (rename_fields.get(name, name),
             self.get_record_field(record, name))
            for name in fields
            if name not in self.exclude_fields]

        if self.extra_data is not None:
            data.extend(self.extra_data)

        if self.skip_none:
            data = [(name, value) for name, value in data
                    if value is not None]

        if self.ordered_first is not None or self.ordered_last is not None:
            data = self.reorder_data(
                data, ordered_first=self.ordered_first, ordered_last=self.ordered_last)

        return data


class JSONFormatterBase(RecordDataFormatterMixin, logging.Formatter):

    encode_default = None

    def __init__(self, *args, **kwargs):
        """
        A logging formatter that turns a record into JSON, for convenient automatic processing.
        """

        self.defaults_data = kwargs.pop('defaults', None) or {}
        super(JSONFormatterBase, self).__init__(*args, **kwargs)

    __init__.__doc__ += RecordDataFormatterMixin.__init__.__doc__  # pylint: disable=no-member

    def _serialize(self, obj):
        _default = text if PY_3 else repr
        try:
            result = json.dumps(obj, ensure_ascii=False, default=_default)
            result += "\n"
        except Exception as exc:
            try:
                result = json.dumps(dict(LOGGING_ERROR="error dumping the value", LOGGING_EXC=exc), default=_default)
            except Exception:
                result = json.dumps(dict(LOGGING_ERROR="error dumping the value and its exc"))
        if PY_3:
            if isinstance(result, bytes):
                result = result.decode("utf-8", errors="replace")
        else:
            if isinstance(result, text):
                result = result.encode("utf-8", errors="replace")
        return result

    def format(self, record):
        data = self.record_to_data(record)
        data += list(self.defaults_data.items())
        dcls = dict if PY_37 else OrderedDict
        return self._serialize(dcls(data))


class JSONFormatter(JSONFormatterBase):
    """ JSONFormatterBase + useful defaults """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('exclude_fields', DEFAULT_EXCLUDED_FIELDS)
        kwargs.setdefault('ordered_first', DEFAULT_ORDERED_FIRST)
        kwargs.setdefault('ordered_last', DEFAULT_ORDERED_LAST)
        kwargs.setdefault('rename_fields', DEFAULT_RENAME_FIELDS)
        kwargs.setdefault('sort_other_fields', True)
        super(JSONFormatter, self).__init__(*args, **kwargs)
