import math

from sqlalchemy import ColumnElement

from .config import get_settings
from .models import Issue

EARTH_RADIUS_M = 6_371_008.8
METRES_PER_DEGREE = math.pi * EARTH_RADIUS_M / 180.0


def within_geofence(latitude: float, longitude: float) -> bool:
    settings = get_settings()
    if not settings.geofence_enabled:
        return True
    return (
        settings.geofence_min_latitude <= latitude <= settings.geofence_max_latitude
        and settings.geofence_min_longitude
        <= longitude
        <= settings.geofence_max_longitude
    )


def bounding_box(
    latitude: float, longitude: float, radius_m: float
) -> tuple[float, float, float, float]:
    """Cheap prefilter so the index on (latitude, longitude) is usable."""
    d_lat = radius_m / METRES_PER_DEGREE
    cos_lat = max(math.cos(math.radians(latitude)), 1e-6)
    d_lng = radius_m / (METRES_PER_DEGREE * cos_lat)
    return (
        latitude - d_lat,
        latitude + d_lat,
        longitude - d_lng,
        longitude + d_lng,
    )


def squared_distance_m(latitude: float, longitude: float) -> ColumnElement[float]:
    """Squared metres from (latitude, longitude), equirectangular approximation.

    Ordering by this is equivalent to ordering by true distance, and the
    expression is pure arithmetic, so it evaluates identically on SQLite and
    PostgreSQL without extension functions. cos(lat) is folded into a Python
    constant because the query centre is fixed for the whole scan.
    """
    lat_scale = METRES_PER_DEGREE
    lng_scale = METRES_PER_DEGREE * math.cos(math.radians(latitude))
    d_lat = (Issue.latitude - latitude) * lat_scale
    d_lng = (Issue.longitude - longitude) * lng_scale
    return d_lat * d_lat + d_lng * d_lng


def distance_m(
    lat_a: float, lng_a: float, lat_b: float, lng_b: float
) -> float:
    d_lat = (lat_b - lat_a) * METRES_PER_DEGREE
    d_lng = (lng_b - lng_a) * METRES_PER_DEGREE * math.cos(math.radians(lat_a))
    return math.hypot(d_lat, d_lng)
