import io
import uuid

from PIL import Image

from tests.conftest import auth, create_issue, jpeg_bytes, png_bytes, sign_in

REPORTER = "+919876543210"
NEIGHBOUR = "+919876500001"


def report_id() -> str:
    return str(uuid.uuid4())


async def test_display_name_can_be_changed(client, sender):
    token = await sign_in(client, sender, REPORTER)

    response = await client.patch(
        "/me", headers=auth(token), json={"display_name": "Asha from Khar"}
    )

    assert response.status_code == 200
    assert response.json()["display_name"] == "Asha from Khar"
    assert (await client.get("/me", headers=auth(token))).json()["display_name"] == (
        "Asha from Khar"
    )


async def test_a_new_name_shows_on_the_public_profile_and_on_reports(client, sender):
    token = await sign_in(client, sender, REPORTER)
    issue_id = (await create_issue(client, token, report_id=report_id())).json()["id"]
    me = (await client.get("/me", headers=auth(token))).json()["id"]

    await client.patch("/me", headers=auth(token), json={"display_name": "Asha"})

    assert (await client.get(f"/users/{me}")).json()["display_name"] == "Asha"
    detail = await client.get(f"/issues/{issue_id}")
    assert detail.json()["reporter"]["display_name"] == "Asha"


async def test_a_blank_or_tiny_name_is_rejected(client, sender):
    token = await sign_in(client, sender, REPORTER)

    for bad in ("", " ", "a"):
        response = await client.patch(
            "/me", headers=auth(token), json={"display_name": bad}
        )
        assert response.status_code == 422, bad
        assert isinstance(response.json()["detail"], str)


async def test_renaming_requires_a_token(client):
    assert (await client.patch("/me", json={"display_name": "Nobody"})).status_code == 401


async def test_an_avatar_can_be_set_and_fetched(client, sender):
    token = await sign_in(client, sender, REPORTER)

    response = await client.put(
        "/me/avatar",
        headers=auth(token),
        files={"photo": ("face.jpg", jpeg_bytes(900, 900), "image/jpeg")},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["avatar_url"] is not None
    fetched = await client.get(body["avatar_url"])
    assert fetched.status_code == 200
    assert fetched.headers["content-type"] == "image/jpeg"


async def test_the_avatar_is_stripped_of_exif_like_any_photo(client, sender):
    token = await sign_in(client, sender, REPORTER)

    body = (
        await client.put(
            "/me/avatar",
            headers=auth(token),
            files={"photo": ("face.jpg", jpeg_bytes(1200, 1200), "image/jpeg")},
        )
    ).json()

    fetched = await client.get(body["avatar_url"])
    assert not dict(Image.open(io.BytesIO(fetched.content)).getexif())


async def test_replacing_an_avatar_drops_the_previous_one(client, sender):
    from app.storage import get_store

    token = await sign_in(client, sender, REPORTER)
    first = (
        await client.put(
            "/me/avatar",
            headers=auth(token),
            files={"photo": ("a.jpg", jpeg_bytes(600, 600), "image/jpeg")},
        )
    ).json()["avatar_url"]
    second = (
        await client.put(
            "/me/avatar",
            headers=auth(token),
            files={"photo": ("b.jpg", jpeg_bytes(600, 600), "image/jpeg")},
        )
    ).json()["avatar_url"]

    assert first != second
    # The old object is gone, not merely unreferenced.
    old_key = first.split("/media/")[1].split("?")[0]
    assert await get_store().get(old_key) is None


async def test_an_avatar_can_be_removed(client, sender):
    token = await sign_in(client, sender, REPORTER)
    await client.put(
        "/me/avatar",
        headers=auth(token),
        files={"photo": ("a.jpg", jpeg_bytes(600, 600), "image/jpeg")},
    )

    response = await client.delete("/me/avatar", headers=auth(token))

    assert response.status_code == 200
    assert response.json()["avatar_url"] is None


async def test_a_non_jpeg_avatar_is_rejected(client, sender):
    token = await sign_in(client, sender, REPORTER)

    response = await client.put(
        "/me/avatar",
        headers=auth(token),
        files={"photo": ("a.png", png_bytes(), "image/jpeg")},
    )

    assert response.status_code == 422
    assert "JPEG" in response.json()["detail"]


async def test_the_avatar_shows_on_the_public_profile(client, sender):
    token = await sign_in(client, sender, REPORTER)
    me = (await client.get("/me", headers=auth(token))).json()["id"]
    await client.put(
        "/me/avatar",
        headers=auth(token),
        files={"photo": ("a.jpg", jpeg_bytes(600, 600), "image/jpeg")},
    )

    assert (await client.get(f"/users/{me}")).json()["avatar_url"] is not None


async def test_setting_an_avatar_requires_a_token(client):
    response = await client.put(
        "/me/avatar", files={"photo": ("a.jpg", jpeg_bytes(400, 400), "image/jpeg")}
    )
    assert response.status_code == 401
