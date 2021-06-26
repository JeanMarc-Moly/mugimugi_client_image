Mugimugi (doujinshi.org) image client

# How to use
```python
OBJECT_ID = 100100
from mugimugi_client_image import MugiMugiImageClient, Size
async with MugiMugiImageClient() as c:
    print(await c.save("cover.jpg", OBJECT_ID, Size.SMALL))
```
`./cover.jpg`

![cover.jpg](https://img.doujinshi.org//tn/50/100100.jpg)
