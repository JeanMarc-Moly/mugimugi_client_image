# Changelog

## [0.4.0] - 2021-07-11

- `save_many` now returns `AsyncIterator[tuple[int, Path]]` instead of `dict[int, Path]`. Returns values as saved without waiting for all images to be saved
- `Size` become `Repository` since new value `SAMPLE = "imagedb"` is not cover size. `BIG` and `SMALL` prefixed with `COVER_`
- `*_many` actions now accept `AsyncIterable` as input (in addition to `Iterable`, not as replacement)
- `*_many` actions now retry on `TimeoutError` (attempts count value to configure in `Constant`)

## [0.3.0] - 2021-06-28

- add `get_many` & `save_many`

## [0.2.0] - 2021-06-28

- `get` returns raw bytes instead of Image
- removed PIL dependency

## [0.1.0] - 2021-06-26

- add `get` & `save` cover images
