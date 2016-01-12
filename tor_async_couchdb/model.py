class Model(object):
    """Abstract base class for all models."""

    def __init__(self, *args, **kwargs):
        object.__init__(self)

        doc = kwargs.get('doc', None)
        if doc is not None:
            self._id = doc.get('_id', None)
            self._rev = doc.get('_rev', None)
        else:
            self._id = kwargs.get('_id', None)
            self._rev = kwargs.get('_rev', None)

    def as_doc_for_store(self):
        rv = {}
        if self._id:
            rv['_id'] = self._id
        if self._rev:
            rv['_rev'] = self._rev
        return rv
