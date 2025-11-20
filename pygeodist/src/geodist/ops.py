"""Stateless geodesic operations backed by the Rust kernels."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from . import _geodist_rs
from .errors import GeodistError
from .geometry import BoundingBox, Point
from .types import Meters

__all__ = (
    "GeodesicResult",
    "geodesic_distance",
    "geodesic_with_bearings",
    "hausdorff_directed",
    "hausdorff",
    "hausdorff_directed_clipped",
    "hausdorff_clipped",
)


@dataclass(frozen=True)
class GeodesicResult:
    distance_meters: Meters
    initial_bearing_degrees: float
    final_bearing_degrees: float


def _to_handle(point: Point) -> _geodist_rs.Point:
    if not isinstance(point, Point):
        raise TypeError(f"geodesic_distance expects Point arguments, got {type(point).__name__}")
    return point._handle


def _to_handles(points: Iterable[Point], *, argument_name: str) -> list[_geodist_rs.Point]:
    handles: list[_geodist_rs.Point] = []
    for point in points:
        if not isinstance(point, Point):
            raise TypeError(f"{argument_name} expects Point instances, got {type(point).__name__}")
        handles.append(point._handle)
    return handles


def geodesic_distance(origin: Point, destination: Point) -> Meters:
    """Compute the great-circle distance between two points in meters."""
    try:
        return float(_geodist_rs.geodesic_distance(_to_handle(origin), _to_handle(destination)))
    except ValueError as exc:
        raise GeodistError(str(exc)) from exc


def geodesic_with_bearings(origin: Point, destination: Point) -> GeodesicResult:
    """Compute great-circle distance and bearings between two points."""
    try:
        solution = _geodist_rs.geodesic_with_bearings(_to_handle(origin), _to_handle(destination))
    except ValueError as exc:
        raise GeodistError(str(exc)) from exc

    return GeodesicResult(
        distance_meters=float(solution.distance_meters),
        initial_bearing_degrees=float(solution.initial_bearing_degrees),
        final_bearing_degrees=float(solution.final_bearing_degrees),
    )


def hausdorff_directed(a: Iterable[Point], b: Iterable[Point]) -> Meters:
    """Directed Hausdorff distance from set `a` to set `b`."""
    handles_a = _to_handles(a, argument_name="hausdorff_directed first argument")
    handles_b = _to_handles(b, argument_name="hausdorff_directed second argument")
    try:
        return float(_geodist_rs.hausdorff_directed(handles_a, handles_b))
    except ValueError as exc:
        raise GeodistError(str(exc)) from exc


def hausdorff(a: Iterable[Point], b: Iterable[Point]) -> Meters:
    """Symmetric Hausdorff distance between two point sets."""
    handles_a = _to_handles(a, argument_name="hausdorff first argument")
    handles_b = _to_handles(b, argument_name="hausdorff second argument")
    try:
        return float(_geodist_rs.hausdorff(handles_a, handles_b))
    except ValueError as exc:
        raise GeodistError(str(exc)) from exc


def _validate_bounding_box(bounding_box: BoundingBox) -> _geodist_rs.BoundingBox:
    if not isinstance(bounding_box, BoundingBox):
        raise TypeError(
            "bounding_box must be a geodist BoundingBox, "
            f"got {type(bounding_box).__name__}"
        )
    return bounding_box._handle


def hausdorff_directed_clipped(
    a: Iterable[Point],
    b: Iterable[Point],
    bounding_box: BoundingBox,
) -> Meters:
    """Directed Hausdorff distance after clipping both sets to a bounding box."""
    handles_a = _to_handles(a, argument_name="hausdorff_directed_clipped first argument")
    handles_b = _to_handles(b, argument_name="hausdorff_directed_clipped second argument")
    bbox_handle = _validate_bounding_box(bounding_box)
    try:
        return float(_geodist_rs.hausdorff_directed_clipped(handles_a, handles_b, bbox_handle))
    except ValueError as exc:
        raise GeodistError(str(exc)) from exc


def hausdorff_clipped(a: Iterable[Point], b: Iterable[Point], bounding_box: BoundingBox) -> Meters:
    """Symmetric Hausdorff distance after clipping both sets to a bounding box."""
    handles_a = _to_handles(a, argument_name="hausdorff_clipped first argument")
    handles_b = _to_handles(b, argument_name="hausdorff_clipped second argument")
    bbox_handle = _validate_bounding_box(bounding_box)
    try:
        return float(_geodist_rs.hausdorff_clipped(handles_a, handles_b, bbox_handle))
    except ValueError as exc:
        raise GeodistError(str(exc)) from exc
