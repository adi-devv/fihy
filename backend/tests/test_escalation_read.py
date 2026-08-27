import uuid

from tests.conftest import auth, create_issue, sign_in

REPORTER = "+919876543210"
LAT, LNG = 19.0612, 72.8371


def report_id() -> str:
    return str(uuid.uuid4())


async def make_escalation(issue_id: str, **over):
    from app.db import sessionmaker
    from app.enums import EscalationState
    from app.models import Escalation

    async with sessionmaker()() as session:
        record = Escalation(
            issue_id=issue_id,
            authority="H/East Ward, MCGM",
            recipient="ward.he@example.gov.in",
            reply_token="secret-token-value",
            subject="Manhole cover missing, Bandra East",
            body="Residents report a missing cover on the footpath side.",
            state=EscalationState.SENT,
            reference="MCGM/2026/0042",
            **over,
        )
        session.add(record)
        await session.commit()


async def test_the_letter_is_readable_by_anyone(client, sender):
    token = await sign_in(client, sender, REPORTER)
    issue_id = (await create_issue(client, token, report_id=report_id())).json()["id"]
    await make_escalation(issue_id)

    response = await client.get(f"/issues/{issue_id}/escalation")

    body = response.json()
    assert response.status_code == 200
    assert body["authority"] == "H/East Ward, MCGM"
    assert body["state"] == "sent"
    assert body["reference"] == "MCGM/2026/0042"
    assert "missing cover" in body["body"]


async def test_the_recipient_and_reply_token_never_leave_the_server(client, sender):
    token = await sign_in(client, sender, REPORTER)
    issue_id = (await create_issue(client, token, report_id=report_id())).json()["id"]
    await make_escalation(issue_id)

    raw = (await client.get(f"/issues/{issue_id}/escalation")).text

    assert "ward.he@example.gov.in" not in raw
    assert "secret-token-value" not in raw
    assert "recipient" not in raw
    assert "reply_token" not in raw


async def test_an_unraised_report_says_so(client, sender):
    token = await sign_in(client, sender, REPORTER)
    issue_id = (await create_issue(client, token, report_id=report_id())).json()["id"]

    response = await client.get(f"/issues/{issue_id}/escalation")

    assert response.status_code == 404
    assert response.json()["detail"] == "This report has not been raised yet."


async def test_an_unknown_issue_is_404(client):
    response = await client.get(f"/issues/{uuid.uuid4().hex}/escalation")

    assert response.status_code == 404
