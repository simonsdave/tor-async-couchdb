"""This module contains the retry_strategy module's unit tests."""

import unittest

import mock

from .. import retry_strategy


class RetryStrategyTestCase(unittest.TestCase):
    """A collection of unit tests for the RetryStrategy class."""

    def test_ctr(self):
        rs = retry_strategy.RetryStrategy()
        self.assertEqual(0, rs.num_retries)
        self.assertTrue(0 < rs.max_num_retries)

        the_max_num_retries = 45
        rs = retry_strategy.RetryStrategy(the_max_num_retries)
        self.assertEqual(0, rs.num_retries)
        self.assertEqual(the_max_num_retries, rs.max_num_retries)

    def test_next_attempt(self):
        the_max_num_retries = 45
        rs = retry_strategy.RetryStrategy(the_max_num_retries)
        self.assertEqual(0, rs.num_retries)

        self.assertTrue(rs.next_attempt())
        self.assertEqual(1, rs.num_retries)
        self.assertTrue(0 < rs.max_num_retries)

    def test_wait_must_be_implemented(self):
        rs = retry_strategy.RetryStrategy()
        callback = mock.Mock()
        with self.assertRaises(NotImplementedError):
            rs.wait(callback)


class ExponentialBackoffRetryStrategyTestCase(unittest.TestCase):
    """A collection of unit tests for the
    ExponentialBackoffRetryStrategyTestCase class.
    """

    def test_wait(self):
        the_max_num_retries = 45
        rs = retry_strategy.ExponentialBackoffRetryStrategy(the_max_num_retries)
        while True:
            add_timeout_patch = mock.Mock()
            with mock.patch("tornado.ioloop.IOLoop.add_timeout", add_timeout_patch):
                wait_callback = mock.Mock()
                delay_in_ms = rs.wait(wait_callback)
                if delay_in_ms:
                    self.assertEqual(1, add_timeout_patch.call_count)
                    self.assertEqual(0, wait_callback.call_count)
                    self.assertTrue(0 < delay_in_ms)
                else:
                    self.assertEqual(0, add_timeout_patch.call_count)
                    self.assertEqual(1, wait_callback.call_count)
                    self.assertEqual(the_max_num_retries, rs.num_retries)
                    return

        self.assertTure(False)
