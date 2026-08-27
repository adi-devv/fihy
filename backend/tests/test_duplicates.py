import uuid

from tests.conftest import auth, create_issue, sign_in

REPORTER = "+919876543210"
NEIGHBOUR = "+919876500001"
LAT, LNG = 19.0612, 72.8371


def report_id() -> str:
    return str(uuid.uuid4())


def metres_north(latitude: float, metres: float) -> float:
    """One degree of latitude is about 111.19 km everywhere."""
    return latitude + metres / 111_195.08


async def nearby_duplicates(client, lat=LAT, lng=LNG, **params):
    response = await client.get(
        "/issues/duplicates", params={"lat": lat, "lng": lng, **params}
    )
    assert response.status_code == 200, response.text
    return response.json()


async def test_a_report_on_the_same_corner_is_offered(client, sender):
    reporter = await sign_in(client, sender, REPORTER)
    existing = (await create_issue(client, reporter, report_id=report_id())).json()

    body = await nearby_duplicates(client, lat=metres_north(LAT, 30), category="manhole")

    assert [d["issue"]["id"] for d in body["items"]] == [existing["id"]]
    assert 25 < body["items"][0]["distance_m"] < 35
    assert body["radius_m"] == 100.0


async def test_a_report_past_the_radius_is_not(client, sender):
    reporter = await sign_in(client, sender, REPORTER)
    await create_issue(client, reporter, report_id=report_id())

    body = await nearby_duplicates(client, lat=metres_north(LAT, 140), category="manhole")

    assert body["items"] == []


async def test_the_boundary_is_the_radius_not_the_box(client, sender):
    """The bounding box is a square; the radius is a circle. A report on the
    diagonal sits inside the box and outside the circle."""
    reporter = await sign_in(client, sender, REPORTER)
    await create_issue(client, reporter, report_id=report_id())

    diagonal = {
        "lat": metres_north(LAT, 80),
        "lng": LNG + 80 / (111_195.08 * 0.945),
    }
    body = await nearby_duplicates(client, **diagonal, category="manhole")

    assert body["items"] == [], "113 m away on the diagonal is not a duplicate"


async def test_a_different_category_is_a_different_problem(client, sender):
    reporter = await sign_in(client, sender, REPORTER)
    await create_issue(client, reporter, report_id=report_id(), category="manhole")

    body = await nearby_duplicates(client, category="garbage")

    assert body["items"] == [], "a bin and a manhole on one corner are two problems"


async def test_without_a_category_everything_close_is_offered(client, sender):
    reporter = await sign_in(client, sender, REPORTER)
    await create_issue(client, reporter, report_id=report_id(), category="manhole")
    await create_issue(client, reporter, report_id=report_id(), category="garbage")

    body = await nearby_duplicates(client)

    assert len(body["items"]) == 2


async def test_a_resolved_report_is_not_a_duplicate(client, sender):
    """A problem that came back is news, not a repeat."""
    from tests.test_profile import set_status

    reporter = await sign_in(client, sender, REPORTER)
    issue_id = (await create_issue(client, reporter, report_id=report_id())).json()["id"]
    await set_status(issue_id, "resolved")

    body = await nearby_duplicates(client, category="manhole")

    assert body["items"] == []


async def test_a_removed_report_is_never_offered(client, sender):
    from tests.test_profile import set_status

    reporter = await sign_in(client, sender, REPORTER)
    issue_id = (await create_issue(client, reporter, report_id=report_id())).json()["id"]
    await set_status(issue_id, "removed")

    body = await nearby_duplicates(client, category="manhole")

    assert body["items"] == []


async def test_the_closest_comes_first(client, sender):
    reporter = await sign_in(client, sender, REPORTER)
    far = (
        await create_issue(
            client, reporter, report_id=report_id(), latitude=metres_north(LAT, 70)
        )
    ).json()["id"]
    near = (
        await create_issue(
            client, reporter, report_id=report_id(), latitude=metres_north(LAT, 10)
        )
    ).json()["id"]

    body = await nearby_duplicates(client, category="manhole")

    assert [d["issue"]["id"] for d in body["items"]] == [near, far]
    assert body["items"][0]["distance_m"] < body["items"][1]["distance_m"]


async def test_the_radius_is_overridable_but_capped(client, sender):
    reporter = await sign_in(client, sender, REPORTER)
    await create_issue(
        client, reporter, report_id=report_id(), latitude=metres_north(LAT, 300)
    )

    tight = await nearby_duplicates(client, category="manhole")
    wide = await nearby_duplicates(client, category="manhole", radius_m=500)

    assert tight["items"] == []
    assert len(wide["items"]) == 1
    assert wide["radius_m"] == 500


async def test_the_candidate_carries_enough_to_render_a_card(client, sender):
    reporter = await sign_in(client, sender, REPORTER)
    await create_issue(client, reporter, report_id=report_id())

    body = await nearby_duplicates(client, category="manhole")

    issue = body["items"][0]["issue"]
    assert issue["title"] and issue["cover_url"] and issue["reporter"]["display_name"]
    assert issue["confirmation_count"] == 0
    assert issue["photos"] is None, "the chooser shows cards, not galleries"


async def test_duplicates_needs_no_sign_in(client, sender):
    """The check runs before publishing, which is before the sign-in prompt."""
    reporter = await sign_in(client, sender, REPORTER)
    await create_issue(client, reporter, report_id=report_id())

    response = await client.get(
        "/issues/duplicates", params={"lat": LAT, "lng": LNG, "category": "manhole"}
    )

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


async def test_confirmed_by_me_is_marked_for_a_signed_in_caller(client, sender):
    reporter = await sign_in(client, sender, REPORTER)
    issue_id = (await create_issue(client, reporter, report_id=report_id())).json()["id"]
    neighbour = await sign_in(client, sender, NEIGHBOUR)
    await client.post(f"/issues/{issue_id}/confirmations", headers=auth(neighbour))

    response = await client.get(
        "/issues/duplicates",
        headers=auth(neighbour),
        params={"lat": LAT, "lng": LNG, "category": "manhole"},
    )

    assert response.json()["items"][0]["issue"]["confirmed_by_me"] is True
