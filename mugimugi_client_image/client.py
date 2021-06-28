from __future__ import annotations
from asyncio.tasks import FIRST_COMPLETED

from enum import Enum
from pathlib import Path
from types import TracebackType
from typing import AsyncContextManager, AsyncGenerator, ClassVar, Iterable, Union
from asyncio import create_task, wait
from httpx import AsyncClient

from .constant import Constant


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
    async def get_many(
        cls, ids: Iterable[int], size: Size = Size.BIG, parallel: int = PARALLEL
    ) -> AsyncGenerator[tuple[int, bytes], None]:

        get = cls.get

        async def _get(id_: int):
            return id_, await get(id_, size)

        remaining_tasks: set = set()
        completed_tasks: set = set()

        async def yield_and_wait():
            nonlocal completed_tasks
            nonlocal remaining_tasks

            for t in completed_tasks:
                yield t.result()

            (completed_tasks, remaining_tasks) = await wait(
                remaining_tasks, return_when=FIRST_COMPLETED
            )

        for id_ in ids:
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
        cls, images: dict[int, Union[str, Path]]
    ) -> Iterable[int, Path]:
        async for i, p in cls.get_many(images.keys()):
            with Path(images[i]).with_suffix(".jpg").open("wb") as f:
                f.write(p)

    @classmethod
    async def save(
        cls, path: Union[str, Path], id_: int, size: Size = Size.BIG
    ) -> Path:
        with (path := Path(path).resolve()).open("wb") as f:
            f.write(await cls.get(id_, size))
            return path

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
