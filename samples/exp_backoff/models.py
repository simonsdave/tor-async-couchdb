import datetime
import random

import dateutil.parser
from tor_async_couchdb.model import Model


class Fruit(Model):

    def __init__(self, **kwargs):
        Model.__init__(self, **kwargs)

        if "doc" in kwargs:
            doc = kwargs["doc"]
            self.fruit_id = doc["fruit_id"]
            self.fruit = doc["fruit"]
            self.created_on = dateutil.parser.parse(doc["created_on"])
            self.updated_on = dateutil.parser.parse(doc["updated_on"])
            return

        self.fruit_id = kwargs["fruit_id"]
        self.fruit = kwargs["fruit"]
        utc_now = type(self)._utc_now()
        self.created_on = utc_now
        self.updated_on = utc_now

    def as_doc_for_store(self):
        rv = Model.as_doc_for_store(self)
        rv["type"] = "fruit_v1.0"
        rv["fruit_id"] = self.fruit_id
        rv["fruit"] = self.fruit
        rv["created_on"] = self.created_on.isoformat()
        rv["updated_on"] = self.updated_on.isoformat()
        return rv

    def change_fruit(self, fruit):
        self.fruit = fruit
        self.updated_on = type(self)._utc_now()

    @classmethod
    def get_random_fruit(cls, but_not_this_fruit=None):
        fruits = ["apple", "pear", "fig", "orange", "kiwi"]
        while True:
            fruit = random.choice(fruits)
            if but_not_this_fruit is None:
                return fruit
            if but_not_this_fruit != fruit:
                return fruit

    @classmethod
    def _utc_now(cls):
        return datetime.datetime.utcnow().replace(tzinfo=dateutil.tz.tzutc())
