from typing import Any, Callable, Generator, Generic, Optional, TypeVar, Union
import dataclasses
import inspect

import ray
from ray.util import ActorPool

@dataclasses.dataclass
class ErrorResult:
    """Report an error that occured when computing a result using a :py:meth:`LexActorPool.map_unordered_with_error` ."""

    #: The value that was submitted to the pool.
    value: Any
    #: The exception raised when applying fn to value.
    error: Exception
    #: The callable used to compute over value.
    fn: Optional[Callable] = None
    #: The pool doing the computation.
    pool: Optional[ActorPool] = None

    @property
    def fn_wrapper(self):
        """Backwards compatibility read-only alias for :py:attr:`fn` ."""
        return self.fn
    
    def retry(self):
        """Call to re-submit the :py:attr:`fn` and :py:attr:`value` that caused this :py:attr:`error`"""
        return self.pool.submit(self.fn, self.value)


ActorType = TypeVar('ActorType', bound=ray.actor.ActorClass)

class FacebookActorPool(ActorPool, Generic[ActorType]):
    """Provide an actor pool with some extra convenience methods."""

    def __init__(self, actors: list[ActorType]):
        super().__init__(actors)
        self.future_to_value = {}

    @classmethod
    def with_actors(cls, actor_constructor: Callable[[], ActorType], n: int):
        """Construct an actor pool with ``n`` actors instantiated by calling ``actor_constructor()``."""

        return cls([actor_constructor() for _ in range(n)])

    def _return_actor(self, actor):
        self._idle_actors.append(actor)
        if self._pending_submits:
            # Changed to submit while there are idle actors available.
            # Useful if actors have been pushed into pool after map has started.
            while self._idle_actors and self._pending_submits:
                self.submit(*self._pending_submits.pop(0))

    def next_result_ref_unordered(self, timeout=None):
        """Returns a ref to any of the next pending results."""
        if not self.has_next():
            raise StopIteration("No more results to get")
        # TODO(ekl) bulk wait for performance
        res, _ = ray.wait(list(self._future_to_actor), num_returns=1, timeout=timeout)
        if res:
            [future] = res
        else:
            raise TimeoutError("Timed out waiting for result")
        i, a = self._future_to_actor.pop(future)
        self._return_actor(a)
        del self._index_to_future[i]
        self._next_return_index = max(self._next_return_index, i + 1)
        return future

    def map_refs_unordered(self, fn, values):
        """Similar to map(), but returning an unordered iterator over result refs."""
        # Ignore/Cancel all the previous submissions
        # by calling `has_next` and `gen_next_unordered` repeteadly.
        self._pending_submits = []
        while self.has_next():
            try:
                self.next_result_ref_unordered(timeout=0)
            except TimeoutError:
                pass

        for v in values:
            self.submit(fn, v)
        while self.has_next():
            yield self.next_result_ref_unordered()

    def map_unordered(self, fn, values):
        self._pending_submits = []
        yield from super().map_unordered(fn, values)

    def map(self, fn, values):
        self._pending_submits = []
        yield from super().map_(fn, values)

    def map_unordered_with_error(
        self, fn, values
    ) -> Generator[Union[ErrorResult, Any]]:
        """Similar to map(), but returning an unordered iterator over either result refs or ErrorResults."""

        for ready_future in self.map_refs_unordered(fn, values):
            try:
                yield ray.get(ready_future)
            except Exception as exc:
                value = self.future_to_value[ready_future]
                yield ErrorResult(value=value, error=exc, fn=fn, pool=self)

            del self.future_to_value[ready_future]

    def submit(self, fn, value):
        def fn_wrapper(actor, value):
            future = fn(actor, value)
            self.future_to_value[future] = value
            return future

        return super().submit(fn_wrapper, value)

def remotecaller(method_name: Union[str, Callable]):
    """Returns a callable object that takes actor and value and calls ``actor.method_name.remote(value)```"""
    if inspect.ismethod(method_name):
        method_name = method_name.__name__

    def fn(actor, value):
        return getattr(actor, method_name).remote(value)
    
    return fn