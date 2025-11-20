"""Optional Shapely interoperability helpers.

Imports are guarded so Shapely remains an opt-in dependency.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from ..errors import InvalidGeometryError
from ..geometry import BoundingBox, Point, Point3D

__all__ = ("from_shapely", "to_shapely")


@runtime_checkable
class _PointLike(Protocol):
    x: float
    y: float
    has_z: bool

    @property
    def z(self) -> float: ...


@runtime_checkable
class _PolygonLike(Protocol):
    bounds: tuple[float, float, float, float]

    def equals(self, other: Any) -> bool: ...


def _import_shapely_geometry() -> tuple[type[Any], type[Any], Any]:
    try:
        from shapely.geometry import Point as ShapelyPoint
        from shapely.geometry import Polygon as ShapelyPolygon
        from shapely.geometry import box as shapely_box
    except ModuleNotFoundError as exc:
        raise ImportError(
            "Shapely is required for interop helpers; install the optional extra with "
            "`pip install pygeodist[shapely]` or add `shapely` to your environment."
        ) from exc
    return ShapelyPoint, ShapelyPolygon, shapely_box


def to_shapely(geometry: Point | Point3D | BoundingBox) -> Any:
    """Convert a geodist geometry into the matching Shapely shape."""
    shapely_point, _, shapely_box = _import_shapely_geometry()
    if isinstance(geometry, Point):
        latitude, longitude = geometry.to_tuple()
        return shapely_point(longitude, latitude)
    if isinstance(geometry, Point3D):
        latitude, longitude, altitude_m = geometry.to_tuple()
        return shapely_point(longitude, latitude, altitude_m)
    if isinstance(geometry, BoundingBox):
        min_lat, max_lat, min_lon, max_lon = geometry.to_tuple()
        return shapely_box(min_lon, min_lat, max_lon, max_lat)

    raise TypeError(
        f"to_shapely expects a geodist geometry type (Point, Point3D, BoundingBox), got {type(geometry).__name__}",
    )


def from_shapely(geometry: _PointLike | _PolygonLike) -> Point | Point3D | BoundingBox:
    """Convert a Shapely geometry into a geodist geometry."""
    shapely_point, shapely_polygon, shapely_box = _import_shapely_geometry()
    if isinstance(geometry, shapely_point):
        latitude: float = float(geometry.y)
        longitude: float = float(geometry.x)
        if getattr(geometry, "has_z", False):
            altitude_m: float = float(geometry.z)
            return Point3D(latitude, longitude, altitude_m)
        return Point(latitude, longitude)

    if isinstance(geometry, shapely_polygon):
        min_lon, min_lat, max_lon, max_lat = geometry.bounds
        rectangle = shapely_box(min_lon, min_lat, max_lon, max_lat)
        if not geometry.equals(rectangle):
            raise InvalidGeometryError("Only axis-aligned rectangular polygons can be converted to BoundingBox.")
        return BoundingBox(float(min_lat), float(max_lat), float(min_lon), float(max_lon))

    raise TypeError(
        "from_shapely expects shapely.geometry.Point (2D/3D) or a rectangular shapely.geometry.Polygon, "
        f"got {type(geometry).__name__}",
    )
