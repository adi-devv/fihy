from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from .. import service
from ..config import get_settings
from ..cursor import InvalidCursor, TimeCursor
from ..enums import Status
from ..deps import OptionalUser, SessionDep
from ..models import User
from ..schemas import Page, ProfileOut
from ..storage import get_store

router = APIRouter(prefix="/users", tags=["users"])

NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="That profile is not available."
)


def _page_size(limit: int | None) -> int:
    settings = get_settings()
    requested = settings.default_limit if limit is None else limit
    return max(1, min(requested, settings.max_limit))


def _cursor(raw: str | None) -> TimeCursor | None:
    if not raw:
        return None
    try:
        return TimeCursor.decode(raw)
    except InvalidCursor as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


async def _load(session: SessionDep, user_id: str) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise NOT_FOUND
    return user


@router.get("/{user_id}", response_model=ProfileOut)
async def read_profile(user_id: str, session: SessionDep) -> ProfileOut:
    """Public. A profile is a record of contribution, so anyone can read one."""
    user = await _load(session, user_id)
    return await service.profile(session, user=user, store=get_store())


@router.get("/{user_id}/issues", response_model=Page)
async def read_user_issues(
    user_id: str,
    session: SessionDep,
    viewer: OptionalUser,
    status: Status | None = None,
    cursor: str | None = None,
    limit: Annotated[int | None, Query()] = None,
) -> Page:
    user = await _load(session, user_id)
    return await service.user_issues(
        session,
        reporter_id=user.id,
        viewer=viewer,
        store=get_store(),
        cursor=_cursor(cursor),
        limit=_page_size(limit),
        include_hidden=viewer is not None and viewer.id == user.id,
        status=status,
    )


@router.get("/{user_id}/supports", response_model=Page)
async def read_user_supports(
    user_id: str,
    session: SessionDep,
    viewer: OptionalUser,
    cursor: str | None = None,
    limit: Annotated[int | None, Query()] = None,
) -> Page:
    user = await _load(session, user_id)
    return await service.user_supports(
        session,
        user_id=user.id,
        viewer=viewer,
        store=get_store(),
        cursor=_cursor(cursor),
        limit=_page_size(limit),
    )
