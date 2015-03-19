"""This module contains the clparserutil's unit tests."""

import logging
import optparse
import os
import sys
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import clparserutil


class TestCase(unittest.TestCase):

    def test_check_logginglevel(self):
        option = clparserutil.Option(
            "--create",
            action="store",
            dest="logging_level",
            default=logging.FATAL,
            type="logginglevel",
            help="whatever")
        values = [
            ["debug", logging.DEBUG],
            ["info", logging.INFO],
            ["INFO", logging.INFO],
            ["warning", logging.WARNING],
            ["eRRor", logging.ERROR],
            ["CRITICAL", logging.CRITICAL],
            ["FATAL", logging.FATAL],

            ["dave", None],
            ["None", None],
            ["", None],
        ]
        type_checker = clparserutil.Option.TYPE_CHECKER["logginglevel"]
        self.assertIsNotNone(type_checker)
        opt_string = option.get_opt_string(),
        for value in values:
            if value[1] is not None:
                msg = "Failed to parse '%s' correctly." % value[0]
                result = type_checker(option, opt_string, value[0])
                self.assertEqual(result, value[1], msg)
            else:
                with self.assertRaises(optparse.OptionValueError):
                    type_checker(option, opt_string, value[0])

    def test_check_user_colon_password(self):
        option = clparserutil.Option(
            "--create",
            action="store",
            dest="server",
            default="",
            type="usercolonpassword",
            help="whatever")
        values = [
            ["dave:simons", ("dave", "simons")],

            ["dave", None],
            ["dave:", None],
            [":simons", None],
            [":", None],
            ["", None],
        ]
        type_checker = clparserutil.Option.TYPE_CHECKER["usercolonpassword"]
        self.assertIsNotNone(type_checker)
        opt_string = option.get_opt_string(),
        for value in values:
            if value[1] is not None:
                msg = "Failed to parse '%s' correctly." % value[0]
                result = type_checker(option, opt_string, value[0])
                self.assertEqual(result, value[1], msg)
            else:
                with self.assertRaises(optparse.OptionValueError):
                    type_checker(option, opt_string, value[0])

    def test_check_scheme_host_port(self):
        option = clparserutil.Option(
            "--create",
            action="store",
            dest="server",
            default="bindle:8909",
            type="schemehostport",
            help="whatever")
        values = [
            ["http://bindle:8909", "http://bindle:8909"],
            ["https://bindle:8909", "https://bindle:8909"],
            ["http://bindle", "http://bindle"],
            ["https://bindle", "https://bindle"],

            ["dave", None],
            ["http://bindle:", None],
            ["https://bindle:", None],
        ]
        type_checker = clparserutil.Option.TYPE_CHECKER["schemehostport"]
        self.assertIsNotNone(type_checker)
        opt_string = option.get_opt_string(),
        for value in values:
            if value[1] is not None:
                msg = "Failed to parse '%s' correctly." % value[0]
                result = type_checker(option, opt_string, value[0])
                self.assertEqual(result, value[1], msg)
            else:
                with self.assertRaises(optparse.OptionValueError):
                    type_checker(option, opt_string, value[0])

    def test_check_boolean(self):
        option = clparserutil.Option(
            "--create",
            action="store",
            dest="create",
            default=True,
            type="boolean",
            help="create key store - default = True")
        values = [
            ["true", True],
            ["True", True],
            ["trUe", True],
            ["t", True],
            ["T", True],
            ["1", True],
            ["y", True],
            ["yes", True],
            ["y", True],

            ["false", False],
            ["False", False],
            ["FaLse", False],
            ["f", False],
            ["F", False],
            ["0", False],
            ["f", False],
            ["no", False],
            ["n", False],

            ["dave", None],
            ["None", None],
            ["", None],
        ]
        type_checker = clparserutil.Option.TYPE_CHECKER["boolean"]
        opt_string = option.get_opt_string(),
        for value in values:
            if value[1] is not None:
                msg = "Failed to parse '%s' correctly." % value[0]
                result = type_checker(option, opt_string, value[0])
                self.assertEqual(result, value[1], msg)
            else:
                with self.assertRaises(optparse.OptionValueError):
                    type_checker(option, opt_string, value[0])
