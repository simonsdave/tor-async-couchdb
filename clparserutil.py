"""This module contains a series of generally useful and reusable
components for use when building extensions to the optparse module
which parses command lines."""

import collections
import re
import logging
import optparse

_logger = logging.getLogger("util.%s" % __name__)

#
# used with the usercolonpassword type
#
UserPassword = collections.namedtuple(
    "UserPassword",
    "user password")


def _check_logging_level(option, opt, value):
    """Type checking function for command line parser's 'logginglevel' type."""
    reg_ex_pattern = "^(DEBUG|INFO|WARNING|ERROR|CRITICAL|FATAL)$"
    reg_ex = re.compile(reg_ex_pattern, re.IGNORECASE)
    if reg_ex.match(value):
        return getattr(logging, value.upper())
    fmt = (
        "option %s: should be one of "
        "DEBUG, INFO, WARNING, ERROR, CRITICAL or FATAL"
    )
    raise optparse.OptionValueError(fmt % opt)


def _check_user_colon_password(option, opt, value):
    """Type checking function for command line parser's
    'usercolonpassword' type."""
    reg_ex_pattern = "^(?P<user>[^\:]+)\:(?P<password>.+)$"
    reg_ex = re.compile(reg_ex_pattern, re.IGNORECASE)
    match = reg_ex.match(value)
    if not match:
        msg = "option %s: required format is 'user:password'" % opt
        raise optparse.OptionValueError(msg)
    return UserPassword(match.group("user"), match.group("password"))


def _check_scheme_host_port(option, opt, value):
    """Type checking function for command line parser's
    'schemehostport' type."""
    reg_ex_pattern = "^\s*https?\:\/\/[^\:]+(?:\:\d+)?\s*$"
    reg_ex = re.compile(reg_ex_pattern, re.IGNORECASE)
    if reg_ex.match(value):
        return value
    msg = "option %s: required format is http[s]://host:port" % opt
    raise optparse.OptionValueError(msg)


def _check_boolean(option, opt, value):
    """Type checking function for command line parser's 'boolean' type."""
    true_reg_ex_pattern = "^(true|t|y|yes|1)$"
    true_reg_ex = re.compile(true_reg_ex_pattern, re.IGNORECASE)
    if true_reg_ex.match(value):
        return True
    false_reg_ex_pattern = "^(false|f|n|no|0)$"
    false_reg_ex = re.compile(false_reg_ex_pattern, re.IGNORECASE)
    if false_reg_ex.match(value):
        return False
    msg = "option %s: should be one of true, false, yes, no, 1 or 0" % opt
    raise optparse.OptionValueError(msg)


class Option(optparse.Option):
    """Adds couchdb, hostcolonport, hostcolonports, boolean & logginglevel
    types to the command line parser's list of available types."""
    new_types = (
        "logginglevel",
        "schemehostport",
        "usercolonpassword",
        "boolean",
    )
    TYPES = optparse.Option.TYPES + new_types
    TYPE_CHECKER = optparse.Option.TYPE_CHECKER.copy()
    TYPE_CHECKER["logginglevel"] = _check_logging_level
    TYPE_CHECKER["schemehostport"] = _check_scheme_host_port
    TYPE_CHECKER["usercolonpassword"] = _check_user_colon_password
    TYPE_CHECKER["boolean"] = _check_boolean
