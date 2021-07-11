from asyncio import FIRST_COMPLETED, Task, create_task, wait
from typing import (
    Any,
    AsyncIterable,
    AsyncIterator,
    Awaitable,
    Callable,
    Iterable,
    TypeVar,
    Union,
)

U = TypeVar("U")
V = TypeVar("V")


async def asynchronize(
    iterable: Union[Iterable[U], AsyncIterable[U]]
) -> AsyncIterator[U]:
    if isinstance(iterable, Iterable):
        for u in iterable:
            yield u
    elif isinstance(iterable, AsyncIterable):
        async for u in iterable:
            yield u
    else:
        raise TypeError(f"Invalid type {type(iterable)}")


async def execute_and_retry(
    func: Callable[[U], Awaitable[V]],
    input: U,
    retry_on: Union[type, tuple[Union[type, tuple[Any, ...]], ...]] = None,
    try_limit: int = 2,
) -> V:
    while (try_limit := try_limit - 1) :
        try:
            return await func(input)
        except Exception as e:
            if not retry_on or isinstance(e, retry_on):
                raise e
    raise Exception(f"Failed to execute {func.__name__}, too many failures")


async def execute_in_pool(
    func: Callable[[U], Awaitable[V]],
    iterable: Union[Iterable[U], AsyncIterable[U]],
    pool_size: int = 10,
    retry_on: Union[type, tuple[Union[type, tuple[Any, ...]], ...]] = None,
    retry_limit: int = 2,
) -> AsyncIterator[V]:

    remaining_tasks: set[Task] = set()
    completed_tasks: set[Task] = set()

    async for u in asynchronize(iterable):
        remaining_tasks.add(
            create_task(execute_and_retry(func, u, retry_on, retry_limit))
        )
        if not (pool_size := pool_size - 1):
            for t in completed_tasks:
                yield t.result()

            (completed_tasks, remaining_tasks) = await wait(
                remaining_tasks, return_when=FIRST_COMPLETED
            )

            pool_size += len(completed_tasks)

    while remaining_tasks:
        for t in completed_tasks:
            yield t.result()

        (completed_tasks, remaining_tasks) = await wait(
            remaining_tasks, return_when=FIRST_COMPLETED
        )

    for t in completed_tasks:
        yield t.result()
