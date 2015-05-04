import logging
import uuid

from tor_async_couchdb import async_model_actions

from models import Fruit

_logger = logging.getLogger("fruit_store.%s" % __name__)


class AsyncFruitPersister(async_model_actions.AsyncPersister):

    def __init__(self, fruit, async_state=None):
        async_model_actions.AsyncPersister.__init__(self, fruit, [], async_state)


class AsyncFruitRetriever(async_model_actions.AsyncModelRetriever):

    def __init__(self, fruit_id, async_state=None):
        async_model_actions.AsyncModelRetriever.__init__(
            self,
            "fruit_by_fruit_id",
            fruit_id,
            async_state)

    def create_model_from_doc(self, doc):
        return Fruit(doc=doc)


class AsyncFruitsRetriever(async_model_actions.AsyncModelsRetriever):

    def __init__(self, async_state=None):
        async_model_actions.AsyncModelsRetriever.__init__(
            self,
            "fruit_by_fruit_id",
            async_state)

    def create_model_from_doc(self, doc):
        return Fruit(doc=doc)


class AsyncAction(object):

    def __init__(self, async_state):
        object.__init__(self)

        self.async_state = async_state


class AsyncFruitCreator(AsyncAction):

    def __init__(self, async_state=None):
        AsyncAction.__init__(self, async_state)

        self._callback = None

    def create(self, callback):
        assert self._callback is None
        self._callback = callback

        fruit = Fruit(fruit_id=uuid.uuid4().hex, fruit=Fruit.get_random_fruit())

        ap = AsyncFruitPersister(fruit)
        ap.persist(self._on_persist_done)

    def _on_persist_done(self, is_ok, is_conflict, ap):
        if not is_ok:
            # won't generate conflict because just created the resource
            assert not is_conflict
            self._call_callback(False)
            return

        self._call_callback(True, ap.model)

    def _call_callback(self, is_ok, fruit=None):
        assert self._callback is not None
        self._callback(is_ok, fruit, self)
        self._callback = None


class AsyncFruitUpdater(AsyncAction):

    def __init__(self, fruit_id, async_state=None):
        AsyncAction.__init__(self, async_state)

        self.fruit_id = fruit_id

        self._callback = None

    def update(self, callback):
        assert callback is not None
        self._callback = callback

        afr = AsyncFruitRetriever(self.fruit_id, None)
        afr.fetch(self._on_fetch_done)

    def _on_fetch_done(self, is_ok, fruit, afr):
        if not is_ok:
            self._call_callback(False)
            return

        if fruit is None:
            self._call_callback(True)
            return

        new_fruit = afr.async_state
        if not new_fruit:
            new_fruit = Fruit.get_random_fruit()

        fruit.change_fruit(new_fruit)

        afp = AsyncFruitPersister(fruit)
        afp.persist(self._on_persist_done)

    def _on_persist_done(self, is_ok, is_conflict, afp):
        if not is_ok:
            if is_conflict:
                afr = AsyncFruitRetriever(
                    afp.model.fruit_id,
                    afp.model.fruit)
                afr.fetch(self._on_fetch_done)
                return

            self._call_callback(False)
            return

        self._call_callback(True, afp.model)

    def _call_callback(self, is_ok, fruit=None):
        assert self._callback is not None
        self._callback(is_ok, fruit, self)
        self._callback = None


class AsyncFruitDeleter(AsyncAction):

    def __init__(self, fruit_id, async_state=None):
        AsyncAction.__init__(self, async_state)

        self.fruit_id = fruit_id

        self._callback = None

    def delete(self, callback):
        assert callback is not None
        self._callback = callback

        afr = AsyncFruitRetriever(self.fruit_id)
        afr.fetch(self._on_fetch_done)

    def _on_fetch_done(self, is_ok, fruit, afr):
        if not is_ok:
            self._call_callback(False)
            return

        if fruit is None:
            self._call_callback(True)
            return

        ad = async_model_actions.AsyncDeleter(fruit)
        ad.delete(self._on_delete_done)

    def _on_delete_done(self, is_ok, is_conflict, ad):
        if not is_ok:
            if is_conflict:
                afr = AsyncFruitRetriever(self.fruit_id)
                afr.fetch(self._on_fetch_done)
                return

            self._call_callback(False)
            return

        self._call_callback(True, ad.model)

    def _call_callback(self, is_ok, fruit=None):
        assert self._callback is not None
        self._callback(is_ok, fruit, self)
        self._callback = None
