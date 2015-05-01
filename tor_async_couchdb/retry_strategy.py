"""This module contains various strategy patterns that implement
approaches to retrying CouchDB updates/deletes that result in 409
conflict responses.
"""

import datetime
import random

from tornado.ioloop import IOLoop


class RetryStrategy(object):
    """With CouchDB's optimistic concurrency it's possible for
    document updates and deletes to result in a 409 Conflict. When this
    happens the document must be reread from the database, changes
    reapplied (as required) and another database update or delete
    attempted.

    This update|delete/persist/retry loop shouldn't be allowed to
    go on forever. There are various strategies for both executing
    and terminating these loops:

        -- keep retrying forever as each conflict is detected
        -- retry immediately as a conflict is detected and only
           retry at most 5 times
        -- retry after pausing for 100 ms after a conflict is
           detected and only retry at most 7 times

    Retry strategies are represented using a strategy pattern
    and ```RetryStrategy``` is the abstract base class for all
    concrete strategy classes.
    """

    def __init__(self, max_num_retries=20):
        object.__init__(self)

        self.num_retries = 0
        self.max_num_retries = max_num_retries

    def next_attempt(self):
        self.num_retries += 1
        return self.num_retries < self.max_num_retries

    def wait(self, callback, *callback_args, **callback_kwargs):
        raise NotImplementedError("must implement 'wait()' in subclass")


class ExponentialBackoffRetryStrategy(RetryStrategy):
    """```ExponentialBackoffRetryStrategy``` implements a retry strategy
    that, as the name suggests, waits exponentially longer time as the
    number of retry attempts increases. The specific time waited is calculated
    with the formula:

        (2 ** retry_number) * 25 +/- random # between -10 & 10

    To get a general sense of wait times:

        for retry in range(1, 20): print (2**retry) * 100

    References

        * https://developers.google.com/google-apps/documents-list/?csw=1#implementing_exponential_backoff
        * http://googleappsdeveloper.blogspot.ca/2011/12/documents-list-api-best-practices.html
        * http://docs.aws.amazon.com/general/latest/gr/api-retries.html
    """

    def wait(self, callback, *callback_args, **callback_kwargs):

        if not self.next_attempt():
            callback(0, *callback_args, **callback_kwargs)
            return

        delay_in_ms = (2 ** self.num_retries) * 25 + random.randint(-10, 10)

        IOLoop.current().add_timeout(
            datetime.timedelta(0, delay_in_ms / 1000.0, 0),
            callback,
            delay_in_ms,
            *callback_args,
            **callback_kwargs)

        return delay_in_ms
