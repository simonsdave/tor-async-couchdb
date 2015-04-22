class Model(object):
    """Abstract base class for all models."""

    def __init__(self, **kwargs):
        object.__init__(self)

        doc = kwargs["doc"] if "doc" in kwargs else {}

        self._id = doc.get("_id", None)
        self._rev = doc.get("_rev", None)

        self._callback = None

    def as_doc_for_store(self):
        rv = {}
        if self._id:
            rv["_id"] = self._id
        if self._rev:
            rv["_rev"] = self._rev
        return rv
