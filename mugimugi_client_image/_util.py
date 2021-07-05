from typing import AsyncIterable, AsyncIterator, Iterable, TypeVar, Union

U = TypeVar("U")


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
