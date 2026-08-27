import io

import pytest
from PIL import Image

from app.config import get_settings
from app.images import ImageRejected, process_jpeg
from tests.conftest import jpeg_bytes, png_bytes


async def test_strips_every_trace_of_exif():
    source = Image.open(io.BytesIO(jpeg_bytes()))
    assert dict(source.getexif()), "fixture should carry EXIF to begin with"

    processed = await process_jpeg(jpeg_bytes())

    for payload in (processed.original, processed.thumbnail):
        output = Image.open(io.BytesIO(payload))
        assert not dict(output.getexif())
        assert not output.getexif().get_ifd(0x8825)
        assert output.info.get("icc_profile") is None


async def test_derives_a_thumbnail_and_caps_the_stored_width():
    settings = get_settings()
    processed = await process_jpeg(jpeg_bytes(4000, 3000))

    assert processed.width == settings.stored_image_width
    assert Image.open(io.BytesIO(processed.thumbnail)).width == settings.thumbnail_width
    assert len(processed.thumbnail) < len(processed.original)


async def test_bakes_in_orientation_before_dropping_it():
    image = Image.new("RGB", (100, 40), (200, 30, 30))
    exif = Image.Exif()
    exif[0x0112] = 6
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", exif=exif)

    processed = await process_jpeg(buffer.getvalue())

    assert (processed.width, processed.height) == (40, 100)


async def test_rejects_a_png():
    with pytest.raises(ImageRejected, match="JPEG"):
        await process_jpeg(png_bytes())


async def test_rejects_unreadable_bytes():
    with pytest.raises(ImageRejected):
        await process_jpeg(b"not an image at all")


async def test_rejects_an_empty_photo():
    with pytest.raises(ImageRejected):
        await process_jpeg(b"")


async def test_rejects_a_photo_over_the_size_limit():
    settings = get_settings()
    original = settings.max_photo_bytes
    settings.max_photo_bytes = 64
    try:
        with pytest.raises(ImageRejected, match="MB"):
            await process_jpeg(jpeg_bytes(400, 300))
    finally:
        settings.max_photo_bytes = original
