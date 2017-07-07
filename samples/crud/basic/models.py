import datetime

import dateutil.parser
from tor_async_couchdb.model import Model


class Fruit(Model):

    def __init__(self, **kwargs):
        Model.__init__(self, **kwargs)

        if 'doc' in kwargs:
            doc = kwargs['doc']

            doc_type = doc['type']
            if doc_type != 'fruit_v1.0':
                raise Exception('Unknown fruit doc type \'%s\'' % doc_type)

            self.fruit_id = doc['fruit_id']
            self.color = doc['color']
            self.created_on = dateutil.parser.parse(doc['created_on'])
            self.updated_on = dateutil.parser.parse(doc['updated_on'])
            return

        self.fruit_id = kwargs['fruit_id']
        self.color = kwargs['color']
        utc_now = type(self)._utc_now()
        self.created_on = utc_now
        self.updated_on = utc_now

    def as_doc_for_store(self):
        rv = Model.as_doc_for_store(self)
        rv['type'] = 'fruit_v1.0'
        rv['fruit_id'] = self.fruit_id
        rv['color'] = self.color
        rv['created_on'] = self.created_on.isoformat()
        rv['updated_on'] = self.updated_on.isoformat()
        return rv

    def change_color(self, color):
        self.color = color
        self.updated_on = type(self)._utc_now()

    @classmethod
    def _utc_now(cls):
        return datetime.datetime.utcnow().replace(tzinfo=dateutil.tz.tzutc())
