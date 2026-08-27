import uuid

from tests.conftest import create_issue, sign_in

REPORTER = "+919876543210"
LAT, LNG = 19.0612, 72.8371


def report_id() -> str:
    return str(uuid.uuid4())


async def seed(client, token):
    rows = [
        ("Manhole cover missing on the footpath", "manhole", "high"),
        ("Water collects across both lanes", "pothole_road", "medium"),
        ("Streetlight dark near the market", "streetlight", "low"),
        ("Garbage piled beside the school gate", "garbage", "high"),
    ]
    for index, (title, category, severity) in enumerate(rows):
        await create_issue(
            client,
            token,
            report_id=report_id(),
            title=title,
            description=f"{title}. Reported by a resident.",
            category=category,
            severity=severity,
            latitude=LAT + index * 0.00002,
        )


async def search(client, **params):
    response = await client.get(
        "/issues/nearby", params={"lat": LAT, "lng": LNG, **params}
    )
    assert response.status_code == 200, response.text
    return [item["title"] for item in response.json()["items"]]


async def test_a_text_query_matches_the_title(client, sender):
    token = await sign_in(client, sender, REPORTER)
    await seed(client, token)

    assert await search(client, q="manhole") == [
        "Manhole cover missing on the footpath"
    ]


async def test_a_text_query_is_case_insensitive(client, sender):
    token = await sign_in(client, sender, REPORTER)
    await seed(client, token)

    assert await search(client, q="STREETLIGHT") == [
        "Streetlight dark near the market"
    ]


async def test_a_text_query_matches_the_description(client, sender):
    token = await sign_in(client, sender, REPORTER)
    await seed(client, token)

    assert await search(client, q="by a resident") == [
        "Manhole cover missing on the footpath",
        "Water collects across both lanes",
        "Streetlight dark near the market",
        "Garbage piled beside the school gate",
    ]


async def test_a_query_with_no_matches_is_an_empty_page(client, sender):
    token = await sign_in(client, sender, REPORTER)
    await seed(client, token)

    response = await client.get(
        "/issues/nearby", params={"lat": LAT, "lng": LNG, "q": "helicopter"}
    )

    assert response.json() == {"items": [], "next_cursor": None}


async def test_wildcards_in_a_query_are_taken_literally(client, sender):
    token = await sign_in(client, sender, REPORTER)
    await seed(client, token)
    await create_issue(
        client,
        token,
        report_id=report_id(),
        title="Sale board blocks 50% of the footpath",
        latitude=LAT,
    )

    # Unescaped, a bare "%" would match all five rows. Escaped, it matches
    # only the one that literally contains a percent sign.
    assert await search(client, q="%") == [
        "Sale board blocks 50% of the footpath"
    ]
    assert await search(client, q="50%") == [
        "Sale board blocks 50% of the footpath"
    ]


async def test_underscores_in_a_query_are_taken_literally(client, sender):
    token = await sign_in(client, sender, REPORTER)
    await seed(client, token)

    assert await search(client, q="_") == []


async def test_the_severity_filter_applies(client, sender):
    token = await sign_in(client, sender, REPORTER)
    await seed(client, token)

    assert await search(client, severity="high") == [
        "Manhole cover missing on the footpath",
        "Garbage piled beside the school gate",
    ]


async def test_the_status_filter_applies(client, sender):
    token = await sign_in(client, sender, REPORTER)
    await seed(client, token)

    assert len(await search(client, status="reported")) == 4
    assert await search(client, status="resolved") == []


async def test_filters_combine(client, sender):
    token = await sign_in(client, sender, REPORTER)
    await seed(client, token)

    assert await search(client, q="footpath", severity="high") == [
        "Manhole cover missing on the footpath"
    ]
    assert await search(client, q="footpath", severity="low") == []


async def test_a_query_pages_without_repeating(client, sender):
    token = await sign_in(client, sender, REPORTER)
    for index in range(9):
        await create_issue(
            client,
            token,
            report_id=report_id(),
            title=f"Pothole number {index} on the main road",
            category="pothole_road",
            latitude=LAT + index * 0.00002,
        )
    await create_issue(
        client, token, report_id=report_id(), title="Something else entirely"
    )

    seen: list[str] = []
    cursor = None
    while True:
        params = {"lat": LAT, "lng": LNG, "q": "pothole", "limit": 4}
        if cursor:
            params["cursor"] = cursor
        page = (await client.get("/issues/nearby", params=params)).json()
        seen.extend(item["id"] for item in page["items"])
        cursor = page["next_cursor"]
        if cursor is None:
            break

    assert len(seen) == len(set(seen)) == 9


async def test_an_overlong_query_is_rejected(client):
    response = await client.get(
        "/issues/nearby", params={"lat": LAT, "lng": LNG, "q": "x" * 200}
    )

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], str)


async def test_search_is_public(client, sender):
    token = await sign_in(client, sender, REPORTER)
    await seed(client, token)

    response = await client.get(
        "/issues/nearby", params={"lat": LAT, "lng": LNG, "q": "manhole"}
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["confirmed_by_me"] is False
