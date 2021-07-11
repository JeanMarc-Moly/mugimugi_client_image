from __future__ import annotations

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

from ._util import asynchronize, execute_in_pool
from .constant import Constant

StrPath = Union[str, Path]
GreaterIntIterable = Union[Iterable[int], AsyncIterable[int]]
Saver = tuple[int, StrPath]


class Repository(Enum):
    COVER_BIG = "big"
    COVER_SMALL = "tn"
    SAMPLE = "imagdb"


class MugiMugiImageClient(AsyncContextManager):
    API: ClassVar[AsyncClient] = AsyncClient(base_url=Constant.API_PATH)
    MODULO: ClassVar[int] = Constant.IMAGE_MODULO
    PARALLEL: ClassVar[int] = Constant.PARALLEL_DOWNLOAD_COUNT
    RETRY: ClassVar[int] = Constant.FAILURE_RETRY

    @classmethod
    def get_url(cls, id_: int, size: Repository):
        return f"{size.value}/{int(id_/cls.MODULO)}/{id_}.jpg"

    @classmethod
    async def get(cls, id_: int, size: Repository = Repository.COVER_BIG) -> bytes:
        return (await cls.API.get(cls.get_url(id_, size))).content

    @classmethod
    async def save(
        cls, path: StrPath, id_: int, size: Repository = Repository.COVER_BIG
    ) -> Path:
        with (path := Path(path).resolve()).open("wb") as f:
            f.write(await cls.get(id_, size))
            return path

    @classmethod
    async def get_many(
        cls, ids: GreaterIntIterable, size: Repository = Repository.COVER_BIG,
    ) -> AsyncIterator[tuple[int, bytes]]:
        async def _get(id_: int) -> tuple[int, bytes]:
            return id_, await cls.get(id_, size)

        async for int_bytes in execute_in_pool(
            _get, ids, cls.PARALLEL, TimeoutError, cls.RETRY
        ):
            yield int_bytes

    @classmethod
    async def save_many(
        cls,
        images: Union[Iterable[Saver], AsyncIterable[Saver]],
        size: Repository = Repository.COVER_BIG,
    ) -> AsyncIterator[tuple[int, Path]]:
        saved = {}

        async def dictionize():
            nonlocal saved
            async for id_, p in asynchronize(images):
                saved[id_] = Path(p).with_suffix(".jpg").resolve()
                yield id_

        # TODO: handle async images generator slower than image retrieval
        async for id_, raw in cls.get_many(dictionize(), size):
            with (path := saved[id_]).open("wb") as f:
                f.write(raw)
                yield id_, path

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
