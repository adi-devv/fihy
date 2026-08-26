# API contract

The mobile app codes against this. `backend/` implements it in FastAPI. Until it
exists, the app runs against an in-memory fake with the same shape
(`mobile/src/data/fakeIssues.ts`), selected with `EXPO_PUBLIC_DEMO=true`.

Base URL comes from `EXPO_PUBLIC_API_URL`. All bodies are JSON unless stated.
All timestamps are RFC 3339 UTC. All ids are strings.

## Conventions

- Auth: `Authorization: Bearer <access_token>` on everything except the two
  `/auth` endpoints and the two public reads.
- Errors: `{ "detail": "human readable message" }` with a normal HTTP status.
  The app surfaces `detail` verbatim, so write it for a person.
- Pagination: opaque `cursor`. The client never parses it. A `null`
  `next_cursor` means the end. Anything encoding offset, keyset, or a token is
  fine as long as it round-trips.

## Types

### Issue

```jsonc
{
  "id": "3f9c...",
  "title": "Cover missing on the footpath side",   // <= 140 chars
  "description": "Cover missing on the footpath side. Unlit after dark.",
  "category": "manhole",          // see enum below
  "severity": "high",             // low | medium | high
  "status": "community_verified", // see enum below
  "latitude": 19.0612,
  "longitude": 72.8371,
  "locality": "Bandra East",      // nullable, short place name for the card
  "confirmation_count": 7,
  "confirmed_by_me": false,       // false when unauthenticated
  "comment_count": 0,
  "cover_url": null,              // nullable; signed, short-lived when present
  "created_at": "2026-08-20T09:12:00Z"
}
```

`category`: `pothole_road`, `garbage`, `footpath`, `streetlight`,
`water_drainage`, `manhole`, `traffic_infrastructure`, `fallen_tree`,
`public_property`, `other`

`status`: `reported`, `community_verified`, `submitted_to_authority`,
`authority_acknowledged`, `in_progress`, `resolution_claimed`, `resolved`,
`reopened`, `duplicate`, `removed`

### Page

```jsonc
{ "items": [ /* Issue */ ], "next_cursor": "eyJvIjoyMH0" }
```

## Endpoints

### `GET /issues/nearby`

Public. Ordered by distance ascending, with a stable tiebreak so paging cannot
repeat or drop a row.

| Query | Type | Default | Notes |
|---|---|---|---|
| `lat` | float | required | |
| `lng` | float | required | |
| `radius_m` | float | `500` | |
| `category` | enum | none | filter |
| `cursor` | string | none | from a previous `next_cursor` |
| `limit` | int | `20` | clamp server-side to 1..100 |

→ `200` Page

### `GET /issues/{id}`

Public. → `200` Issue, `404` if unknown or removed.

### `POST /issues`

Authenticated. `multipart/form-data`, because the photo is required.

| Field | Type | Notes |
|---|---|---|
| `client_report_id` | string (uuid) | idempotency key; a repeat returns the original |
| `title` | string | 3..140 |
| `description` | string | <= 2000, may be empty |
| `category` | enum | |
| `severity` | enum | |
| `latitude` | float | |
| `longitude` | float | |
| `photos` | file[] | at least one, JPEG |

→ `201` Issue. `422` with `detail` for validation failures.

Notes for the implementer:
- The client strips EXIF before upload, but **re-strip server-side**. Never
  trust the client for that; it is a privacy guarantee, not a nicety.
- Store originals privately. `cover_url` should be a short-lived signed URL to
  a derived thumbnail, never the raw upload.
- Repeating a `client_report_id` must return the existing issue, not a
  duplicate. The app retries queued drafts on reconnect.

### `POST /issues/{id}/confirmations`

Authenticated. Idempotent — confirming twice is not an error.
Body: `{ "note": "optional, <= 1000 chars" }`
→ `200` Issue (with updated `confirmation_count` and `confirmed_by_me`)

### `DELETE /issues/{id}/confirmations`

Authenticated. → `200` Issue

Reporters must not be able to confirm their own issue; the value of the count
is that it is independent corroboration.

### `POST /auth/otp/request`

Body: `{ "phone": "+919876543210" }` → `204`

Rate limit per phone and per IP. Do not reveal whether the number is known.

### `POST /auth/otp/verify`

Body: `{ "phone": "+919876543210", "code": "123456" }`
→ `200 { "access_token": "...", "token_type": "bearer", "expires_in": 3600, "refresh_token": "..." }`
→ `401` with `detail` on a bad or expired code.

### `GET /me`

Authenticated. → `200 { "id": "...", "display_name": "...", "avatar_url": null }`

## Open questions for the backend author

1. **Geofence.** The prototype restricted reports to a Mumbai bounding box.
   Decide whether that stays, widens to India, or moves to a config value.
2. **Comments.** `comment_count` is in the Issue shape and the UI renders it,
   but no comment endpoints exist yet. Ship it as a constant `0` until they do.
3. **Refresh tokens.** The app currently assumes a long-lived access token. If
   you want short-lived tokens plus refresh, say so and the client will add the
   interceptor.
