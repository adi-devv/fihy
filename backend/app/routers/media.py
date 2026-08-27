from fastapi import APIRouter, HTTPException, Response, status

from ..config import get_settings
from ..storage import LocalObjectStore, get_store

router = APIRouter(tags=["media"])

GONE = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN, detail="That image link has expired."
)


@router.get("/media/{key:path}")
async def read_media(key: str, expires: int, signature: str) -> Response:
    """Serves the local storage stand-in. With R2 configured, images are read
    straight from R2 by presigned URL and this route is never reached."""
    store = get_store()
    if not isinstance(store, LocalObjectStore):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    if not store.verify(key, expires, signature):
        raise GONE
    try:
        payload = await store.get(key)
    except ValueError as exc:
        raise GONE from exc
    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    return Response(
        content=payload,
        media_type="image/jpeg",
        headers={
            "Cache-Control": f"private, max-age={get_settings().signed_url_ttl_seconds}"
        },
    )
