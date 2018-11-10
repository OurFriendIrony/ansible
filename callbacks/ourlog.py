from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import sys
from datetime import datetime

try:
    from ansible.utils.color import colorize, hostcolor
    from ansible.plugins.callback import CallbackBase
except ImportError:
    class CallbackBase:
        pass

# Fields we would like to see before the others, in this order, please...
PREFERRED_FIELDS = ['stdout', 'rc', 'stderr', 'start', 'end', 'msg']

# Fields we will delete from the result
DELETABLE_FIELDS = [
    'stdout', 'stdout_lines', 'rc', 'stderr', 'start', 'end', 'msg',
    '_ansible_verbose_always', '_ansible_no_log']

COLOUR_CHANGED = 'yellow'
COLOUR_UNCHANGED = 'green'
COLOUR_SKIPPED = 'cyan'
COLOUR_FAILED = 'red'


def deep_serialize(data, indent=0):
    # THIS BLOCK IS RESPONSIBLE FOR OUTPUTTING THE OBJECT WHEN A CHANGE IS MADE

    padding = " " * indent * 2
    if isinstance(data, list):
        if data == []:
            return "[]"
        output = "[ "
        if len(data) == 1:
            output = output + \
                     ("\n" +
                      padding).join(deep_serialize(data[0], 0).splitlines()) + " ]"
        else:
            list_padding = " " * (indent + 1) * 2

            for item in data:
                output = output + "\n" + list_padding + "- " + \
                         deep_serialize(item, indent)
            output = output + "\n" + padding + " ]"
    elif isinstance(data, dict):
        if "_ansible_no_log" in data and data["_ansible_no_log"]:
            data = {"censored":
                        "the output has been hidden due to the fact that"
                        " 'no_log: true' was specified for this result"}
        list_padding = " " * (indent + 1) * 2
        output = "{\n"

        for key in PREFERRED_FIELDS:
            if key in data.keys():
                value = data[key]
                prefix = list_padding + "- %s: " % key
                output = output + prefix + "%s\n" % \
                         "\n".join([" " * len(prefix) + line
                                    for line in deep_serialize(value, indent)
                                   .splitlines()]).strip()

        for key in DELETABLE_FIELDS:
            if key in data.keys():
                del data[key]

        for key, value in data.items():
            output = output + list_padding + \
                     "- %s: %s\n" % (key, deep_serialize(value, indent + 1))

        output = output + padding + "}"
    else:
        string_form = str(data)
        if len(string_form) == 0:
            return "\"\""
        else:
            return string_form
    return output


class CallbackModule(CallbackBase):
    '''
    This is the default callback interface, which simply prints messages
    to stdout when new callback events are received.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'ourlog'

    def _get_duration(self):
        self.task_ended = datetime.now()
        total_duration = (self.task_ended - self.task_started)
        return total_duration.total_seconds() * 1000

    def _command_generic_msg(self, hostname, result, caption):
        duration = self._get_duration()

        stdout = result.get('stdout', '')
        if self._display.verbosity > 0:
            if 'stderr' in result and result['stderr']:
                stderr = result.get('stderr', '')
                return "%s | %s | %sms | rc=%s | stdout: \n%s\n\n\t\t\t\tstderr: %s" % \
                       (hostname, caption, duration, result.get('rc', 0), stdout, stderr)
            else:
                if len(stdout) > 0:
                    return "%s | %s | %sms | rc=%s | stdout: \n%s\n" % \
                           (caption, hostname, duration, result.get('rc', 0), stdout)
                else:
                    return "%s | %s | %sms | rc=%s | no stdout" % \
                           (caption, hostname, duration, result.get('rc', 0))
        else:
            return "%s | %s | %sms | rc=%s" % (hostname, caption, duration, result.get('rc', 0))

    def v2_playbook_on_task_start(self, task, is_conditional):
        self._open_section(task.get_name(), task.get_path())

    def _open_section(self, section_name, task_path=None):
        '''
        This is the first part of the line that gets output, before the SUCCESS/result tag
        '''
        self.task_started = datetime.now()
        timestamp = self.task_started.strftime("%H:%M:%S")

        if self._display.verbosity > 1 and path:
            self._emit_line("[{}]: {}".format(timestamp, path))

        self.task_start_preamble = "[{}] {} ...".format(
            timestamp,
            section_name
        )
        sys.stdout.write(self.task_start_preamble)

    def v2_playbook_on_handler_task_start(self, task):
        self._emit_line("triggering handler | %s " % task.get_name().strip())

    def v2_runner_on_failed(self, result, ignore_errors=False):
        duration = self._get_duration()
        host_string = self._host_string(result)

        if 'exception' in result._result:
            exception_message = "An exception occurred during task execution."
            if self._display.verbosity < 3:
                # extract just the actual error message from the exception text
                error = result._result['exception'].strip().split('\n')[-1]
                msg = exception_message + \
                      "To see the full traceback, use -vvv. The error was: %s" % error
            else:
                msg = exception_message + \
                      "The full traceback is:\n" + \
                      result._result['exception'].replace('\n', '')

                self._emit_line(msg, color='red')

        self._emit_line("%s | FAILED | %dms" %
                        (host_string,
                         duration), color='red')
        self._emit_line(deep_serialize(result._result), color='red')

    def v2_on_file_diff(self, result):

        if result._task.loop and 'results' in result._result:
            for res in result._result['results']:
                if 'diff' in res and res['diff'] and res.get('changed', False):
                    diff = self._get_diff(res['diff'])
                    if diff:
                        self._emit_line(diff)

        elif 'diff' in result._result and \
                result._result['diff'] and \
                result._result.get('changed', False):
            diff = self._get_diff(result._result['diff'])
            if diff:
                self._emit_line(diff)

    def _host_string(self, result):
        delegated_vars = result._result.get('_ansible_delegated_vars', None)

        if delegated_vars:
            host_string = "%s -> %s" % (
                result._host.get_name(), delegated_vars['ansible_host'])
        else:
            host_string = result._host.get_name()

        return host_string

    def v2_runner_on_ok(self, result):
        # pylint: disable=I0011,W0201,
        duration = self._get_duration()

        self._clean_results(result._result, result._task.action)

        host_string = self._host_string(result)

        self._clean_results(result._result, result._task.action)

        if result._task.action in ('include', 'include_role'):
            sys.stdout.write("\b\b\b\b    \n")
            return

        msg, color = self._changed_or_not(result._result, host_string)

        if result._task.loop and self._display.verbosity > 0 and 'results' in result._result:
            for item in result._result['results']:
                msg, color = self._changed_or_not(item, host_string)
                item_msg = "%s - item=%s" % (msg, self._get_item(item))
                self._emit_line("%s | %dms" %
                                (item_msg, duration), color=color)
        else:
            self._emit_line("%s | %dms" %
                            (msg, duration), color=color)
        self._handle_warnings(result._result)

        if (
                self._display.verbosity > 0 or
                '_ansible_verbose_always' in result._result
        ) and not '_ansible_verbose_override' in result._result:
            self._emit_line(deep_serialize(result._result), color=color)

        result._preamble = self.task_start_preamble

    def _changed_or_not(self, result, host_string):
        if result.get('changed', False):
            msg = "CHANGED | %s" % host_string
            color = COLOUR_CHANGED
        else:
            msg = "SUCCESS | %s" % host_string
            color = COLOUR_UNCHANGED

        return [msg, color]

    def _emit_line(self, lines, color='normal'):

        if self.task_start_preamble is None:
            self._open_section("system")

        if self.task_start_preamble.endswith(" ..."):
            sys.stdout.write("\b\b\b\b | ")
            self.task_start_preamble = " "

        for line in lines.splitlines():
            self._display.display(line, color=color)

    def v2_runner_on_unreachable(self, result):
        self._task_level = 0
        self._emit_line("%s | UNREACHABLE!: %s" %
                        (self._host_string(result), result._result.get('msg', '')), color=COLOUR_CHANGED)

    def v2_runner_on_skipped(self, result):
        duration = self._get_duration()
        self._task_level = 0

        self._emit_line("%dms | SKIPPED | %s" % (duration, self._host_string(result)), color=COLOUR_SKIPPED)

    def v2_playbook_on_include(self, included_file):
        self._open_section("system")

        msg = 'included: %s for %s' % \
              (included_file._filename, ", ".join(
                  [h.name for h in included_file._hosts]))
        self._emit_line(msg, color=COLOUR_SKIPPED)

    def v2_playbook_on_stats(self, stats):
        self._open_section("system")
        self._emit_line("-- Play recap --")

        hosts = sorted(stats.processed.keys())
        for h in hosts:
            t = stats.summarize(h)

            self._emit_line(u" %s : %s %s %s %s" % (
                hostcolor(h, t),
                colorize(u'ok', t['ok'], COLOUR_UNCHANGED),
                colorize(u'changed', t['changed'], COLOUR_CHANGED),
                colorize(u'unreachable', t['unreachable'], COLOUR_CHANGED),
                colorize(u'failed', t['failures'], COLOUR_FAILED)))

    def __init__(self, *args, **kwargs):
        super(CallbackModule, self).__init__(*args, **kwargs)
        self.task_start_preamble = None

        # Python2
        try:
            reload(sys).setdefaultencoding('utf8')
        except:
            pass
