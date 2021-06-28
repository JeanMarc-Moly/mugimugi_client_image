from __future__ import annotations

from enum import Enum
from pathlib import Path
from types import TracebackType
from typing import AsyncContextManager, ClassVar, Union

from httpx import AsyncClient

from .constant import Constant


class Size(Enum):
    BIG = "big"
    SMALL = "tn"


class MugiMugiImageClient(AsyncContextManager):
    API: ClassVar[AsyncClient] = AsyncClient(base_url=Constant.API_PATH)
    MODULO: ClassVar[int] = Constant.IMAGE_MODULO

    @classmethod
    def get_url(cls, id_: str, size: Size):
        return f"{size.value}/{int(id_/cls.MODULO)}/{id_}.jpg"

    @classmethod
    async def get(cls, id_: int, size: Size = Size.BIG) -> bytes:
        return (await cls.API.get(cls.get_url(id_, size))).content

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
