from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import sys
import json
from datetime import datetime

try:
    from ansible.utils.color import colorize, hostcolor
    from ansible.plugins.callback import CallbackBase
except ImportError:
    class CallbackBase:
        pass

# Fields we will delete from the result
DELETABLE_FIELDS = [
    'stdout', 'stdout_lines', 'rc', 'stderr', 'start', 'end',
    '_ansible_verbose_always', '_ansible_no_log', 'diff', 'changed'
]

ANSIBLE_STATUSES = [
    "OK", "CHANGED", "SKIPPED", "FAILED", "UNREACHABLE"
]

# Colours
COLOUR_CHANGED = 'yellow'
COLOUR_OK = 'green'
COLOUR_SKIPPED = 'cyan'
COLOUR_INCLUDED = 'cyan'
COLOUR_FAILED = 'red'
COLOUR_UNREACHABLE = 'red'
COLOUR_EXTRA = 'magenta'


def override(o):
    return o


def deep_serialize_list(data, indent):
    padding = " " * indent * 2
    output = "\n"
    for item in data:
        output = "{}->{}{}".format(
            output,
            padding,
            deep_serialize(item, indent + 1)
        )

    return output


def deep_serialize_dict(data, indent):
    padding = " " * indent * 2
    if "_ansible_no_log" in data and data["_ansible_no_log"]:
        data = {
            "censored": "the output has been hidden due to the fact that 'no_log: true' was specified for this result"
        }

    for key in DELETABLE_FIELDS:
        if key in data.keys():
            del data[key]

    output = "\n"
    for key, value in data.items():
        output = "{}{}{}: {}\n".format(
            output,
            padding,
            key,
            deep_serialize(value, indent + 1)
        )

    return output


def deep_serialize_string(data):
    string_form = str(data)
    if len(string_form) == 0:
        return '""'
    else:
        return string_form


def deep_serialize(data, indent=1):
    if isinstance(data, list):
        return deep_serialize_list(data, indent)
    elif isinstance(data, dict):
        return deep_serialize_dict(data, indent)
    else:
        return deep_serialize_string(data)


def verbose_result(data):
    return str(json.dumps(data))


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'ourlog'

    def _capture_task_start(self):
        self.task_started = datetime.now()
        self.task_started_fmt = self.task_started.strftime("%H:%M:%S")

    def _capture_task_end(self):
        self.task_ended = datetime.now()

    def _get_task_duration(self):
        self._capture_task_end()
        total_duration = (self.task_ended - self.task_started)
        return total_duration.total_seconds()

    def _capture_play_start(self):
        self.play_started = datetime.now()
        self.play_started_fmt = self.play_started.strftime("%H:%M:%S")

    def _capture_play_end(self):
        self.play_ended = datetime.now()

    def _get_play_duration(self):
        self._capture_play_end()
        total_duration = (self.play_ended - self.play_started)
        return total_duration.total_seconds()

    def _host_string(self, result):
        delegated_vars = result._result.get('_ansible_delegated_vars', None)

        if delegated_vars:
            host_string = "{} -> {}".format(
                result._host.get_name(),
                delegated_vars['ansible_host']
            )
        else:
            host_string = result._host.get_name()

        return host_string

    def _output_result(self, colour, status, host, msg=None, extra_msgs=None):
        line = "\r[{} -> {}] {} | {} | {}\033[K".format(
            self.task_started_fmt,
            ("%ds" % self._get_task_duration()).ljust(self.ms_len),
            host.ljust(self.host_len),
            status.ljust(self.stat_len),
            self.task_title.ljust(self.task_len)
        )
        if msg:
            line = "{} | {}".format(
                line,
                msg.rstrip()
            )
        self._display.display(line, color=colour)
        if extra_msgs:
            self._display.display(extra_msgs, color=COLOUR_EXTRA)

    def _output_general(self, lines, color='normal'):
        for line in lines.splitlines():
            self._display.display("\r" + line + "\033[K", color=color)

    def _collect_host_info(self, hosts):
        self.host_count = len(hosts)
        self.host_len = 0
        for host in hosts:
            self.host_len = max(self.host_len, len(str(host)))
        self.stat_len = len(max(ANSIBLE_STATUSES, key=len))
        self.ms_len = 4
        self.task_len = 40

    def _is_changed(self, result):
        return result._result.get('changed', False)

    def _is_verbose(self, item):
        return (self._display.verbosity > 0 or ('_ansible_verbose_always' in item)) \
               and not ('_ansible_verbose_override' in item)

    def _get_extra_msgs(self, result):
        extra_msg = ""
        if 'results' in result._result:
            for item in result._result.get('results', None):
                if 'msg' in item:
                    if self._is_verbose(item):
                        extra_msg += "\n  " + item.get('msg')

        elif 'msg' in result._result:
            if self._is_verbose(result._result):
                extra_msg += "\n  " + result._result.get('msg')

        if extra_msg != "":
            return extra_msg.lstrip('\n')
        return None

    def _get_error_from_list(self, result):
        if 'results' in result._result:
            for item in result._result.get('results', None):
                if item.get('failed', False):
                    return item.get('stderr', item.get('msg', None))
        return result._result.get('stderr', item.get('msg', None))


    #
    # Override Hooks
    #
    @override
    def v2_playbook_on_play_start(self, *args, **kwargs):
        self._collect_host_info(
            args[0].get_variable_manager()._inventory.get_hosts()
        )
        self._capture_play_start()

    @override
    def v2_playbook_on_task_start(self, task, is_conditional):
        self._capture_task_start()
        self.task_title = task.get_name()

        sys.stdout.write(
            "[{}] {}".format(
                self.task_started_fmt,
                self.task_title
            )
        )

    @override
    def v2_playbook_on_handler_task_start(self, task):
        self._output_general(
            "> triggering handler | {} ".format(
                task.get_name().strip(),
                COLOUR_EXTRA
            )
        )

    @override
    def v2_runner_on_failed(self, result, ignore_errors=False):
        self._output_result(
            COLOUR_FAILED,
            "FAILED",
            self._host_string(result),
            result._result.get('module_stderr', self._get_error_from_list(result)),
            self._get_extra_msgs(result)
        )

    @override
    def v2_on_file_diff(self, result):
        if result._task.loop and 'results' in result._result:
            for res in result._result['results']:
                if 'diff' in res and res['diff'] and res.get('changed', False):
                    diff = self._get_diff(res['diff'])
                    if diff:
                        self._output_general(diff)

        elif 'diff' in result._result and \
                result._result['diff'] and \
                result._result.get('changed', False):
            diff = self._get_diff(result._result['diff'])
            if diff:
                self._output_general(diff)

    @override
    def v2_runner_on_ok(self, result):
        self._handle_warnings(result._result)

        if self._is_changed(result):
            self._output_result(
                COLOUR_CHANGED,
                "CHANGED",
                self._host_string(result),
                None,
                self._get_extra_msgs(result)
            )
        else:
            self._output_result(
                COLOUR_OK,
                "OK",
                self._host_string(result),
                None,
                self._get_extra_msgs(result)
            )

    @override
    def v2_runner_on_unreachable(self, result):
        self._output_result(
            COLOUR_UNREACHABLE,
            "UNREACHABLE",
            self._host_string(result),
            result._result.get('msg', ''),
            self._get_extra_msgs(result)
        )

    @override
    def v2_runner_on_skipped(self, result):
        self._output_result(
            COLOUR_SKIPPED,
            "SKIPPED",
            self._host_string(result),
            None,
            self._get_extra_msgs(result)
        )

    @override
    def v2_playbook_on_stats(self, stats):
        self._output_general(
            "-- Summary -- [ {} -> {} ]".format(
                self.play_started_fmt,
                ("%ds" % self._get_play_duration()).ljust(self.ms_len)
            ),
            color=COLOUR_EXTRA
        )

        hosts = sorted(stats.processed.keys())
        for host in hosts:
            totals = stats.summarize(host)
            self._output_general(
                u" {} : {} {} {} {}".format(
                    hostcolor(host, totals),
                    colorize(u'ok', totals['ok'], COLOUR_OK),
                    colorize(u'changed', totals['changed'], COLOUR_CHANGED),
                    colorize(u'unreachable', totals['unreachable'], COLOUR_UNREACHABLE),
                    colorize(u'failed', totals['failures'], COLOUR_FAILED)
                )
            )

    def __init__(self, *args, **kwargs):
        super(CallbackModule, self).__init__(*args, **kwargs)

        # Python2
        try:
            reload(sys).setdefaultencoding('utf8')
        except:
            pass
