from __future__ import annotations

from enum import Enum
from io import BytesIO
from pathlib import Path
from types import TracebackType
from typing import AsyncContextManager, ClassVar, Union

from httpx import AsyncClient
from PIL import Image

from .constant import Constant


class Size(Enum):
    BIG = "big"
    SMALL = "tn"


class MugiMugiImageClient(AsyncContextManager):
    API: ClassVar[AsyncClient] = AsyncClient(base_url=Constant.API_PATH)
    MODULO: ClassVar[int] = Constant.IMAGE_MODULO

    @classmethod
    async def get(cls, id_: int, size: Size = Size.BIG) -> Image:
        print(f"{Constant.API_PATH}/{size.value}/{int(id_/cls.MODULO)}/{id_}.jpg")
        return Image.open(
            BytesIO(
                (
                    await cls.API.get(f"{size.value}/{int(id_/cls.MODULO)}/{id_}.jpg")
                ).content
            )
        )

    @classmethod
    async def save(
        cls, path: Union[str, Path], id_: int, size: Size = Size.BIG
    ) -> Path:
        path = Path(path).resolve()
        (await cls.get(id_, size)).save(path)
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
