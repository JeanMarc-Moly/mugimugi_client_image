from __future__ import annotations

from asyncio import FIRST_COMPLETED, Task, create_task, wait
from enum import Enum
from pathlib import Path
from types import TracebackType
from typing import (
    AsyncContextManager,
    AsyncIterable,
    AsyncIterator,
    ClassVar,
    Iterable,
    Union,
)

from httpx import AsyncClient

from ._util import asynchronize
from .constant import Constant

StrPath = Union[str, Path]
GreaterIntIterable = Union[Iterable[int], AsyncIterable[int]]
Saver = tuple[int, StrPath]


class Size(Enum):
    BIG = "big"
    SMALL = "tn"


class MugiMugiImageClient(AsyncContextManager):
    API: ClassVar[AsyncClient] = AsyncClient(base_url=Constant.API_PATH)
    MODULO: ClassVar[int] = Constant.IMAGE_MODULO
    PARALLEL: ClassVar[int] = Constant.PARALLEL_DOWNLOAD_COUNT

    @classmethod
    def get_url(cls, id_: int, size: Size):
        return f"{size.value}/{int(id_/cls.MODULO)}/{id_}.jpg"

    @classmethod
    async def get(cls, id_: int, size: Size = Size.BIG) -> bytes:
        return (await cls.API.get(cls.get_url(id_, size))).content

    @classmethod
    async def save(cls, path: StrPath, id_: int, size: Size = Size.BIG) -> Path:
        with (path := Path(path).resolve()).open("wb") as f:
            f.write(await cls.get(id_, size))
            return path

    @classmethod
    async def get_many(
        cls, ids: GreaterIntIterable, size: Size = Size.BIG, parallel: int = PARALLEL,
    ) -> AsyncIterator[tuple[int, bytes]]:

        get = cls.get

        async def _get(id_: int):
            return id_, await get(id_, size)

        remaining_tasks: set[Task] = set()
        completed_tasks: set[Task] = set()

        async def yield_and_wait():
            nonlocal completed_tasks
            nonlocal remaining_tasks

            for t in completed_tasks:
                yield t.result()

            (completed_tasks, remaining_tasks) = await wait(
                remaining_tasks, return_when=FIRST_COMPLETED
            )

        async for id_ in asynchronize(ids):
            remaining_tasks.add(create_task(_get(id_)))

            if not (parallel := parallel - 1):
                async for r in yield_and_wait():
                    yield r
                parallel += len(completed_tasks)

        while remaining_tasks:
            async for r in yield_and_wait():
                yield r

        for t in completed_tasks:
            yield t.result()

    @classmethod
    async def save_many(
        cls,
        images: Union[Iterable[Saver], AsyncIterable[Saver]],
        size: Size = Size.BIG,
        parallel: int = PARALLEL,
    ) -> dict[int, Path]:
        saved = {}

        async def dictionize():
            nonlocal saved
            async for id_, p in asynchronize(images):
                saved[id_] = Path(p).with_suffix(".jpg").resolve()
                yield id_

        # TODO: handle async images generator slower than image retrieval
        async for id_, raw in cls.get_many(dictionize(), size, parallel):
            with saved[id_].open("wb") as f:
                f.write(raw)

        return saved

    async def __aenter__(self) -> MugiMugiImageClient:
        await self.API.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] = None,
        exc_value: BaseException = None,
        traceback: TracebackType = None,
    ) -> None:
        await self.API.__aexit__(exc_type, exc_value, traceback)
