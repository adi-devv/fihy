from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from .. import service
from ..config import get_settings
from ..cursor import InvalidCursor, TimeCursor
from ..deps import CurrentUser, SessionDep
from ..schemas import MarkReadIn, NotificationPage, UnreadCountOut
from ..storage import get_store

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationPage)
async def read_notifications(
    session: SessionDep,
    user: CurrentUser,
    cursor: str | None = None,
    limit: Annotated[int | None, Query()] = None,
) -> NotificationPage:
    settings = get_settings()
    requested = settings.default_limit if limit is None else limit
    page_size = max(1, min(requested, settings.max_limit))

    parsed: TimeCursor | None = None
    if cursor:
        try:
            parsed = TimeCursor.decode(cursor)
        except InvalidCursor as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    return await service.notifications(
        session,
        user=user,
        store=get_store(),
        cursor=parsed,
        limit=page_size,
    )


@router.post("/read", response_model=UnreadCountOut)
async def mark_read(
    session: SessionDep, user: CurrentUser, body: MarkReadIn | None = None
) -> UnreadCountOut:
    """Omit ids to mark the whole feed read, which is what opening the screen
    does. Passing ids marks just those, so a single row can be dismissed."""
    remaining = await service.mark_read(session, user, body.ids if body else None)
    return UnreadCountOut(unread_count=remaining)
