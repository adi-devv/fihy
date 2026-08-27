import uuid

from tests.conftest import auth, create_issue, sign_in

REPORTER = "+919876543210"
NEIGHBOUR = "+919876500001"


def report_id() -> str:
    return str(uuid.uuid4())


async def set_status(issue_id: str, status: str) -> None:
    from sqlalchemy import select

    from app.db import sessionmaker
    from app.models import Issue

    async with sessionmaker()() as session:
        issue = await session.scalar(select(Issue).where(Issue.id == issue_id))
        issue.status = status
        await session.commit()


async def test_the_status_filter_narrows_to_resolutions(client, sender):
    token = await sign_in(client, sender, REPORTER)
    me = (await client.get("/me", headers=auth(token))).json()["id"]
    fixed = (await create_issue(client, token, report_id=report_id(), title="The one that got fixed")).json()["id"]
    await create_issue(client, token, report_id=report_id(), title="The one still open")
    await set_status(fixed, "resolved")

    response = await client.get(f"/users/{me}/issues", params={"status": "resolved"})

    titles = [i["title"] for i in response.json()["items"]]
    assert titles == ["The one that got fixed"]


async def test_the_filter_agrees_with_the_profile_count(client, sender):
    token = await sign_in(client, sender, REPORTER)
    me = (await client.get("/me", headers=auth(token))).json()["id"]
    for index in range(3):
        issue_id = (
            await create_issue(
                client, token, report_id=report_id(), title=f"Report number {index} here"
            )
        ).json()["id"]
        if index < 2:
            await set_status(issue_id, "resolved")

    listed = await client.get(f"/users/{me}/issues", params={"status": "resolved"})
    profile = await client.get(f"/users/{me}")

    assert len(listed.json()["items"]) == 2
    assert profile.json()["contributions"]["resolutions"] == 2


async def test_no_resolutions_is_an_empty_page_not_an_error(client, sender):
    token = await sign_in(client, sender, REPORTER)
    me = (await client.get("/me", headers=auth(token))).json()["id"]
    await create_issue(client, token, report_id=report_id())

    response = await client.get(f"/users/{me}/issues", params={"status": "resolved"})

    assert response.status_code == 200
    assert response.json() == {"items": [], "next_cursor": None}


async def test_the_filter_still_only_shows_that_person(client, sender):
    mine = await sign_in(client, sender, REPORTER)
    me = (await client.get("/me", headers=auth(mine))).json()["id"]
    theirs = await sign_in(client, sender, NEIGHBOUR)
    other = (await create_issue(client, theirs, report_id=report_id(), title="Not mine at all")).json()["id"]
    await set_status(other, "resolved")

    response = await client.get(f"/users/{me}/issues", params={"status": "resolved"})

    assert response.json()["items"] == []


async def test_an_unknown_status_is_rejected(client, sender):
    token = await sign_in(client, sender, REPORTER)
    me = (await client.get("/me", headers=auth(token))).json()["id"]

    response = await client.get(f"/users/{me}/issues", params={"status": "banana"})

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], str)
