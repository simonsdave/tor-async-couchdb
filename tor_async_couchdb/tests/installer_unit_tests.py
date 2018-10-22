"""This module contains the installer module's unit/integration tests."""

import sys
import uuid
import unittest

import mock

from ..installer import CommandLineParser
from ..installer import main


class SysDotArgcPatcher(object):

    def __init__(self, sys_dot_argv):
        object.__init__(self)

        self.sys_dot_argv = sys_dot_argv
        self._old_sys_dot_argv = None

    def __enter__(self):
        assert self._old_sys_dot_argv is None

        self._old_sys_dot_argv = sys.argv
        sys.argv = self.sys_dot_argv[:]
        sys.argv.insert(0, self._old_sys_dot_argv[0])

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        assert self._old_sys_dot_argv is not None
        sys.argv = self._old_sys_dot_argv
        self._old_sys_dot_argv = None


class NoUsageCommandLineParser(CommandLineParser):
    """This class exists **only** so that usage messages
    are **not** written to stderr when unit tests are
    being run.
    """

    def print_usage(self, file=None):
        pass


class CommandLineParserTestCase(unittest.TestCase):
    """Unit tests for installer.CommandLine() function."""

    def test_invalid_command_line(self):
        sys_dot_arv = [
            '--dave=bindle',
            '--host=http://172.17.0.1:5984',
        ]
        with SysDotArgcPatcher(sys_dot_arv):
            description = uuid.uuid4().hex
            default_database = 'aaa%s' % uuid.uuid4().hex
            clp = NoUsageCommandLineParser(description, default_database)
            mock_op_exit = mock.Mock()
            with mock.patch('optparse.OptionParser.exit', mock_op_exit):
                (clo, cla) = clp.parse_args()
                self.assertEqual(mock_op_exit.call_count, 1)
                self.assertEqual(mock_op_exit.call_args[0][0], 2)
                self.assertIsNotNone(mock_op_exit.call_args[0][1])


class MainTestCase(unittest.TestCase):
    """Unit/integration tests for installer.main() function."""

    def test_whatever(self):
        description = uuid.uuid4().hex
        default_database = 'aaa%s' % uuid.uuid4().hex

        sys_dot_arv = [
            '--create=true',
            '--delete=false',
            '--host=http://172.17.0.1:5984',
        ]
        with SysDotArgcPatcher(sys_dot_arv):
            clp = NoUsageCommandLineParser(description, default_database)
            rv = main(clp)
            self.assertEqual(rv, 0)

        sys_dot_arv = [
            '--create=false',
            '--delete=true',
            '--host=http://172.17.0.1:5984',
        ]
        with SysDotArgcPatcher(sys_dot_arv):
            clp = NoUsageCommandLineParser(description, default_database)
            rv = main(clp)
            self.assertEqual(rv, 0)
