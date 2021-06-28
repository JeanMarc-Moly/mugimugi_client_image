Mugimugi (doujinshi.org) image client

# How to use

## Get
```python
OBJECT_ID = 100100

from io import BytesIO
from PIL import Image
from mugimugi_client_image import MugiMugiImageClient

async with MugiMugiImageClient() as c:
    img = Image(BytesIO(await c.get(OBJECT_ID)))
```
And you'll have a nice image to edit in app.

## Save
If you want instead to keep it as is.
```python
OBJECT_ID = 100100

from mugimugi_client_image import MugiMugiImageClient, Size
async with MugiMugiImageClient() as c:
    print(await c.save("cover.jpg", OBJECT_ID, Size.SMALL))
```
