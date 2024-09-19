from collections.abc import Generator
from contextlib import contextmanager
import dataclasses
import datetime
import inspect
from typing import Any, Callable, Generic, NamedTuple, Optional, TypeVar, Union

import ray
import ray.exceptions
from ray.util import ActorPool

from .utils import generator_close_return


@dataclasses.dataclass
class ErrorResult:
    """Report an error that occurred when computing a result using a :py:meth:`SermonActorPool.map_unordered_with_error` ."""

    #: The value that was submitted to the pool.
    value: Any
    #: The exception raised when applying fn to value.
    error: Exception
    #: The callable used to compute over value.
    fn: Optional[Callable] = None
    #: The pool doing the computation.
    pool: Optional[ActorPool] = None
    #: The object ref generator from a failed generator method
    object_ref_generator: Optional[ray.DynamicObjectRefGenerator] = None

    @property
    def fn_wrapper(self):
        """Backwards-compatibility read-only alias for :py:attr:`fn` ."""

        return self.fn

    def retry(self):
        """Call to re-submit the :py:attr:`fn` and :py:attr:`value` that caused this :py:attr:`error` to the original pool."""
        return self.pool.submit(self.fn, self.value)

    @property
    def original_cause(self) -> Exception:
        """Original exception from task that caused this ``ErrorResult``."""
        if isinstance(self.error, ray.exceptions.RayTaskError):
            return self.error.cause

        return self.error

    def successful_results(self) -> Generator[Any]:
        """Yield from :py:attr:`object_ref_generator` suppressing any exceptions."""
        if not self.object_ref_generator:
            raise ValueError('Not an ErrorResult from a generator task')

        for result_ref in self.object_ref_generator:
            try:
                yield ray.get(result_ref)
            except Exception:
                # Likely what caused us, so take no action.
                pass


ActorType = TypeVar('ActorType', bound=ray.actor.ActorClass)


class SermonActorPool(ActorPool, Generic[ActorType]):
    """Provide an actor pool with some extra convenience methods."""

    def __init__(self, actors: list[ActorType]):
        super().__init__(actors)
        self.future_to_value = None

    @classmethod
    def with_actors(cls, actor_constructor: Callable[[], ActorType], n: int):
        """Construct an actor pool with ``n`` actors instantiated by calling ``actor_constructor()`` ."""

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
        self.reset_pool()
        while self.has_next():
            try:
                self.next_result_ref_unordered(timeout=0)
            except TimeoutError:
                pass

        # Not used by us but used by map_unordered_with_error
        self.future_to_value = {}

        for v in values:
            self.submit(fn, v)
        while self.has_next():
            ready_future = self.next_result_ref_unordered()
            yield ready_future
            # Clean up for map_unordered_with_error
            if ready_future in self.future_to_value:
                del self.future_to_value[ready_future]

    def map_unordered(self, fn, values):
        """Similar to map(), but returning an unordered iterator."""
        self.reset_pool()
        yield from super().map_unordered(fn, values)

    def map(self, fn, values):
        self.reset_pool()
        yield from super().map(fn, values)

    def map_unordered_with_error(
        self, fn, values
    ) -> Generator[Union[ErrorResult, Any]]:
        """Similar to map(), but returning an unordered iterator over results, DynamicObjectRefGenerator, or ErrorResults."""

        for ready_future in self.map_refs_unordered(fn, values):
            try:
                result = ray.get(ready_future)
                if isinstance(result, ray.DynamicObjectRefGenerator):
                    if res_list := list(result):
                        final_ref = res_list[-1]
                        # Will raise exception if generator raised exception.
                        ray.get(final_ref)
                    # Reset DynamicObjectRefGenerator.
                    result = ray.get(ready_future)
                yield result
            except Exception as exc:
                value = self.future_to_value[ready_future]
                error_result = ErrorResult(value=value, error=exc, fn=fn, pool=self)
                try:
                    # Reset DynamicObjectRefGenerator.
                    error_result.object_ref_generator = ray.get(ready_future)
                except Exception:
                    pass  # Wasn't an object ref generator.
                yield error_result

    def repeat(self, fn, n):
        """Repeat tasks to actors in pool with fn n times

        Args:
            fn: a function that takes an actor and invokes the task
            n: int

        Returns:
            ray object refs
        """
        self.reset_pool()
        while self.has_next():
            try:
                self.next_result_ref_unordered(timeout=0)
            except TimeoutError:
                pass
        for _ in range(0, n):
            self.submit(lambda actor, value: fn(actor), tuple())
        while self.has_next():
            yield self.next_result_ref_unordered()

    def submit(self, fn, value):
        def fn_wrapper(actor, value):
            future = fn(actor, value)
            if self.future_to_value is not None:
                self.future_to_value[future] = value
            return future

        return super().submit(fn_wrapper, value)

    def drop_pending(self):
        """Drop all pending work."""
        self._pending_submits = []

    def reset_pool(self):
        """Drop all pending work & error reporting map."""
        self.drop_pending()
        self.future_to_value = None

    @contextmanager
    def borrowed_actor(self):
        """Borrow an _idle_ actor, do a task, then put it back into the pool when done."""
        actor = self.pop_idle()
        try:
            yield actor
        finally:
            self.push(actor)

    def run_on_all(self, fn: Callable):
        """Ensure each actor in the pool has had ``fn(actor)`` called.

        Args:
            fn: usually a ``lambda actor: actor.some_method.remote(a_value)``
        """

        assert not self._pending_submits
        assert not self.has_next()
        return ray.get([fn(actor) for actor in self._idle_actors])


def remotecaller(method_name: Union[str, Callable]):
    """Returns a callable object that takes actor and value and calls ``actor.method_name.remote(value)``"""

    if inspect.ismethod(method_name):
        method_name = method_name.__name__

    def fn(actor, value):
        return getattr(actor, method_name).remote(value)

    return fn


def remote_kws_caller(method_name: Union[str, Callable]):
    """Returns a callable object that takes actor and value and calls ``actor.method_name.remote(**value)``"""

    if inspect.ismethod(method_name):
        method_name = method_name.__name__

    def fn(actor, value):
        return getattr(actor, method_name).remote(**value)

    return fn


class TooManyErrors(Exception):
    """Raised when a :py:class:`ErrorAccumulator` accumulates too many errors."""

    pass


class ErrorAccumulator:
    """Accumulate sequential errors until a maximum is reached."""

    def __init__(self, limit: int):
        self.limit = limit
        self.errors = []

    def push(self, error: ErrorResult):
        self.errors.append(error)

        if len(self.errors) > self.limit:
            raise TooManyErrors()

    def push_reset(self, result):
        """Push an error onto the accumulator, or reset if not an error."""

        if isinstance(result, ErrorResult):
            self.push(error=result)
            return

        self.errors.clear()


def unpack_gen(task_results):
    """Unpack any :py:class:`ray.DynamicObjectRefGenerator` we stumble across while iterating ``task_results``.

    Useful for, eg, pattern matching on the items from the generator.

    Yields:
        The items from task_results,
        except for any :py:class:`ray.DynamicObjectRefGenerator`,
        which are unpacked into tuples.
    """
    pass
    # for result in task_results:
    #     match result:
    #         case ray.DynamicObjectRefGenerator():
    #             yield tuple(result)
    #         case _:
    #             yield result


def time_limit(
    gen,
    *,
    start_time: datetime.datetime,
    time_limit: datetime.timedelta,
    exc: Exception,
):
    """Run a generator - usually an :py:class:`SermonActorPool` map method - until it completes or exceeds a time limit."""

    stopping = False

    for result in gen:
        yield result

        if not stopping and datetime.datetime.utcnow() - start_time > time_limit:
            try:
                yield gen.throw(exc)
            except StopIteration:
                return


class ReportedErrors(NamedTuple):
    retried: set
    abandoned: set
    root_close: Any | None = None


class AbandonedTask(NamedTuple):
    value: Any
    exception: Exception


@generator_close_return
def iter_consecutive_errors(iterable, consecutive_error_limit):
    consecutive_errors = ErrorAccumulator(
        limit=consecutive_error_limit,
    )
    for result in iterable:
        consecutive_errors.push_reset(result=result)
        yield result

    if hasattr(iterable, 'close'):
        return iterable.close()


@generator_close_return
def retry_tasks_once(iterable):
    retried = set()
    abandoned = set()

    for result in iterable:
        match result:
            case ErrorResult(value=dict(value)) as error if tuple(
                value.items()
            ) not in retried:
                retried.add(tuple(value.items()))
                error.retry()
            case ErrorResult(value=dict(value)) as error if tuple(
                value.items()
            ) in retried:
                abandoned.add(tuple(value.items()))
                yield AbandonedTask(value=value, exception=error.original_cause)
            case ErrorResult(value=value) as error if value not in retried:
                retried.add(value)
                error.retry()
            case ErrorResult(value=value) as error if value in retried:
                abandoned.add(value)
                yield AbandonedTask(value=value, exception=error.original_cause)
            case _:
                yield result

    if hasattr(iterable, 'close'):
        return ReportedErrors(
            retried=retried, abandoned=abandoned, root_close=iterable.close()
        )
    else:
        return ReportedErrors(retried=retried, abandoned=abandoned)
