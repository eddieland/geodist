"""Stateless geodesic operations backed by the Rust kernels."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Literal, TypeAlias, overload

from . import _geodist_rs
from .errors import InvalidGeometryError
from .geometry import BoundingBox, Ellipsoid, LineString, Point, Point3D, Polygon, _coerce_point_like
from .types import Meters
from .types import Point as PointTuple

__all__ = (
    "GeodesicResult",
    "HausdorffDirectedWitness",
    "HausdorffWitness",
    "PolylineWitness",
    "geodesic_distance",
    "geodesic_distance_on_ellipsoid",
    "geodesic_distance_3d",
    "geodesic_with_bearings",
    "geodesic_with_bearings_on_ellipsoid",
    "hausdorff_directed_3d",
    "hausdorff_directed",
    "hausdorff_3d",
    "hausdorff",
    "hausdorff_directed_clipped_3d",
    "hausdorff_directed_clipped",
    "hausdorff_clipped_3d",
    "hausdorff_clipped",
    "hausdorff_polyline",
    "hausdorff_polygon_boundary",
)


@dataclass(frozen=True, slots=True)
class GeodesicResult:
    """Result of a geodesic computation including distance and bearings."""

    distance_m: Meters
    initial_bearing_deg: float
    final_bearing_deg: float


@dataclass(frozen=True, slots=True)
class HausdorffDirectedWitness:
    """Directed Hausdorff witness containing the realizing pair indices."""

    distance_m: Meters
    origin_index: int
    candidate_index: int


@dataclass(frozen=True, slots=True)
class HausdorffWitness:
    """Symmetric Hausdorff witness with per-direction details."""

    distance_m: Meters
    a_to_b: HausdorffDirectedWitness
    b_to_a: HausdorffDirectedWitness


@dataclass(frozen=True, slots=True)
class PolylineWitness:
    """Hausdorff witness for polylines including realizing coordinates."""

    distance_m: Meters
    source_part: int
    source_index: int
    target_part: int
    target_index: int
    source_coord: PointTuple
    target_coord: PointTuple


def _looks_like_coord(value: object) -> bool:
    if isinstance(value, Point):
        return True
    if isinstance(value, tuple) and len(value) == 2:
        lat, lon = value
        return (
            isinstance(lat, (int, float))
            and not isinstance(lat, bool)
            and isinstance(lon, (int, float))
            and not isinstance(lon, bool)
        )
    return False


PointLike: TypeAlias = Point | tuple[float, float]
PartLike: TypeAlias = Sequence[PointLike]
PolylineLike: TypeAlias = LineString | Sequence[PointLike | PartLike]


def _coerce_polyline_parts(polyline: PolylineLike) -> list[list[PointTuple]]:
    if isinstance(polyline, LineString):
        return [polyline.to_tuple()]

    try:
        sequence = list(polyline)
    except TypeError as exc:  # pragma: no cover - defensive branch
        raise InvalidGeometryError(
            f"expected LineString or coordinate sequences, got {type(polyline).__name__}"
        ) from exc

    if not sequence:
        raise InvalidGeometryError("polyline must contain at least one part")

    first = sequence[0]
    if isinstance(first, LineString):
        return [part.to_tuple() for part in sequence]

    if _looks_like_coord(first):
        return [[_coerce_point_like(vertex) for vertex in sequence]]  # type: ignore[arg-type]

    parts: list[list[PointTuple]] = []
    for part in sequence:
        try:
            parts.append([_coerce_point_like(vertex) for vertex in part])  # type: ignore[arg-type]
        except TypeError as exc:  # pragma: no cover - defensive branch
            raise InvalidGeometryError("expected MultiLineString-style sequence of coordinate arrays") from exc

    return parts


def geodesic_distance(origin: Point, destination: Point) -> Meters:
    """Compute the great-circle distance between two points in meters.

    Uses the WGS84 mean-radius sphere; expect ~0.3–0.5% error versus a true
    ellipsoid. Prefer :func:`geodesic_distance_on_ellipsoid` for accuracy-
    sensitive work or compliance with geodesy references.
    """
    return float(_geodist_rs.geodesic_distance(origin._handle, destination._handle))


def geodesic_distance_on_ellipsoid(
    origin: Point,
    destination: Point,
    ellipsoid: Ellipsoid | None = None,
) -> Meters:
    """Compute the ellipsoidal geodesic distance between two points in meters."""
    model = ellipsoid or Ellipsoid.wgs84()
    return float(
        _geodist_rs.geodesic_distance_on_ellipsoid(
            origin._handle,
            destination._handle,
            ellipsoid=model._handle,
        )
    )


def geodesic_distance_3d(origin: Point3D, destination: Point3D) -> Meters:
    """Compute straight-line (ECEF chord) distance between two 3D points in meters."""
    return float(_geodist_rs.geodesic_distance_3d(origin._handle, destination._handle))


def geodesic_with_bearings(origin: Point, destination: Point) -> GeodesicResult:
    """Compute great-circle distance and bearings between two points.

    Uses a mean-radius sphere; prefer
    :func:`geodesic_with_bearings_on_ellipsoid` for tighter agreement with
    reference ellipsoids.
    """
    solution = _geodist_rs.geodesic_with_bearings(origin._handle, destination._handle)

    return GeodesicResult(
        distance_m=float(solution.distance_m),
        initial_bearing_deg=float(solution.initial_bearing_deg),
        final_bearing_deg=float(solution.final_bearing_deg),
    )


def geodesic_with_bearings_on_ellipsoid(
    origin: Point,
    destination: Point,
    ellipsoid: Ellipsoid | None = None,
) -> GeodesicResult:
    """Compute ellipsoidal distance and bearings between two points."""
    model = ellipsoid or Ellipsoid.wgs84()
    solution = _geodist_rs.geodesic_with_bearings_on_ellipsoid(
        origin._handle,
        destination._handle,
        ellipsoid=model._handle,
    )

    return GeodesicResult(
        distance_m=float(solution.distance_m),
        initial_bearing_deg=float(solution.initial_bearing_deg),
        final_bearing_deg=float(solution.final_bearing_deg),
    )


@overload
def hausdorff_polyline(
    polyline_a: LineString | PolylineLike,
    polyline_b: LineString | PolylineLike,
    *,
    symmetric: bool = True,
    bbox: BoundingBox | None = None,
    max_segment_length_m: float | None = 100.0,
    max_segment_angle_deg: float | None = 0.1,
    sample_cap: int = 50_000,
    return_witness: Literal[False] = False,
) -> float: ...


@overload
def hausdorff_polyline(
    polyline_a: LineString | PolylineLike,
    polyline_b: LineString | PolylineLike,
    *,
    symmetric: bool = True,
    bbox: BoundingBox | None = None,
    max_segment_length_m: float | None = 100.0,
    max_segment_angle_deg: float | None = 0.1,
    sample_cap: int = 50_000,
    return_witness: Literal[True],
) -> tuple[float, PolylineWitness | None]: ...


def hausdorff_polyline(
    polyline_a: LineString | PolylineLike,
    polyline_b: LineString | PolylineLike,
    *,
    symmetric: bool = True,
    bbox: BoundingBox | None = None,
    max_segment_length_m: float | None = 100.0,
    max_segment_angle_deg: float | None = 0.1,
    sample_cap: int = 50_000,
    return_witness: bool = False,
) -> float | tuple[float, PolylineWitness | None]:
    """Hausdorff distance between polylines with optional witness."""
    parts_a = _coerce_polyline_parts(polyline_a)
    parts_b = _coerce_polyline_parts(polyline_b)

    if return_witness:
        distance_m, payload = _geodist_rs.hausdorff_polyline(
            parts_a,
            parts_b,
            symmetric=bool(symmetric),
            bbox=bbox._handle if bbox is not None else None,
            max_segment_length_m=max_segment_length_m,
            max_segment_angle_deg=max_segment_angle_deg,
            sample_cap=int(sample_cap),
            return_witness=True,
        )

        witness = (
            PolylineWitness(
                distance_m=float(payload.distance_m),
                source_part=int(payload.source_part),
                source_index=int(payload.source_index),
                target_part=int(payload.target_part),
                target_index=int(payload.target_index),
                source_coord=(float(payload.source_coord[0]), float(payload.source_coord[1])),
                target_coord=(float(payload.target_coord[0]), float(payload.target_coord[1])),
            )
            if payload is not None
            else None
        )
        return float(distance_m), witness

    result = _geodist_rs.hausdorff_polyline(
        parts_a,
        parts_b,
        symmetric=bool(symmetric),
        bbox=bbox._handle if bbox is not None else None,
        max_segment_length_m=max_segment_length_m,
        max_segment_angle_deg=max_segment_angle_deg,
        sample_cap=int(sample_cap),
        return_witness=False,
    )
    return float(result)


def hausdorff_directed(a: Iterable[Point], b: Iterable[Point]) -> HausdorffDirectedWitness:
    """Directed Hausdorff distance and witness from set `a` to set `b`."""
    witness = _geodist_rs.hausdorff_directed(
        a=[it._handle for it in a],
        b=[it._handle for it in b],
    )

    return HausdorffDirectedWitness(
        distance_m=float(witness.distance_m),
        origin_index=int(witness.origin_index),
        candidate_index=int(witness.candidate_index),
    )


def hausdorff(a: Iterable[Point], b: Iterable[Point]) -> HausdorffWitness:
    """Symmetric Hausdorff distance and witnesses between two point sets."""
    witness = _geodist_rs.hausdorff(
        a=[it._handle for it in a],
        b=[it._handle for it in b],
    )

    return HausdorffWitness(
        distance_m=float(witness.distance_m),
        a_to_b=HausdorffDirectedWitness(
            distance_m=float(witness.a_to_b.distance_m),
            origin_index=int(witness.a_to_b.origin_index),
            candidate_index=int(witness.a_to_b.candidate_index),
        ),
        b_to_a=HausdorffDirectedWitness(
            distance_m=float(witness.b_to_a.distance_m),
            origin_index=int(witness.b_to_a.origin_index),
            candidate_index=int(witness.b_to_a.candidate_index),
        ),
    )


def hausdorff_directed_clipped(
    a: Iterable[Point],
    b: Iterable[Point],
    bounding_box: BoundingBox,
) -> HausdorffDirectedWitness:
    """Directed Hausdorff witness after clipping both sets to a bounding box."""
    witness = _geodist_rs.hausdorff_directed_clipped(
        [it._handle for it in a],
        [it._handle for it in b],
        bounding_box._handle,
    )

    return HausdorffDirectedWitness(
        distance_m=float(witness.distance_m),
        origin_index=int(witness.origin_index),
        candidate_index=int(witness.candidate_index),
    )


def hausdorff_clipped(a: Iterable[Point], b: Iterable[Point], bounding_box: BoundingBox) -> HausdorffWitness:
    """Symmetric Hausdorff witness after clipping both sets to a bounding box."""
    witness = _geodist_rs.hausdorff_clipped(
        [it._handle for it in a],
        [it._handle for it in b],
        bounding_box._handle,
    )

    return HausdorffWitness(
        distance_m=float(witness.distance_m),
        a_to_b=HausdorffDirectedWitness(
            distance_m=float(witness.a_to_b.distance_m),
            origin_index=int(witness.a_to_b.origin_index),
            candidate_index=int(witness.a_to_b.candidate_index),
        ),
        b_to_a=HausdorffDirectedWitness(
            distance_m=float(witness.b_to_a.distance_m),
            origin_index=int(witness.b_to_a.origin_index),
            candidate_index=int(witness.b_to_a.candidate_index),
        ),
    )


def hausdorff_directed_3d(a: Iterable[Point3D], b: Iterable[Point3D]) -> HausdorffDirectedWitness:
    """Directed 3D Hausdorff witness using the ECEF chord metric."""
    witness = _geodist_rs.hausdorff_directed_3d(
        a=[it._handle for it in a],
        b=[it._handle for it in b],
    )

    return HausdorffDirectedWitness(
        distance_m=float(witness.distance_m),
        origin_index=int(witness.origin_index),
        candidate_index=int(witness.candidate_index),
    )


def hausdorff_3d(a: Iterable[Point3D], b: Iterable[Point3D]) -> HausdorffWitness:
    """Symmetric 3D Hausdorff witness using the ECEF chord metric."""
    witness = _geodist_rs.hausdorff_3d(
        a=[it._handle for it in a],
        b=[it._handle for it in b],
    )

    return HausdorffWitness(
        distance_m=float(witness.distance_m),
        a_to_b=HausdorffDirectedWitness(
            distance_m=float(witness.a_to_b.distance_m),
            origin_index=int(witness.a_to_b.origin_index),
            candidate_index=int(witness.a_to_b.candidate_index),
        ),
        b_to_a=HausdorffDirectedWitness(
            distance_m=float(witness.b_to_a.distance_m),
            origin_index=int(witness.b_to_a.origin_index),
            candidate_index=int(witness.b_to_a.candidate_index),
        ),
    )


def hausdorff_directed_clipped_3d(
    a: Iterable[Point3D],
    b: Iterable[Point3D],
    bounding_box: BoundingBox,
) -> HausdorffDirectedWitness:
    """Directed 3D Hausdorff witness after clipping points by latitude/longitude."""
    witness = _geodist_rs.hausdorff_directed_clipped_3d(
        [it._handle for it in a],
        [it._handle for it in b],
        bounding_box._handle,
    )

    return HausdorffDirectedWitness(
        distance_m=float(witness.distance_m),
        origin_index=int(witness.origin_index),
        candidate_index=int(witness.candidate_index),
    )


def hausdorff_clipped_3d(a: Iterable[Point3D], b: Iterable[Point3D], bounding_box: BoundingBox) -> HausdorffWitness:
    """Symmetric 3D Hausdorff witness after clipping points by latitude/longitude."""
    witness = _geodist_rs.hausdorff_clipped_3d(
        [it._handle for it in a],
        [it._handle for it in b],
        bounding_box._handle,
    )

    return HausdorffWitness(
        distance_m=float(witness.distance_m),
        a_to_b=HausdorffDirectedWitness(
            distance_m=float(witness.a_to_b.distance_m),
            origin_index=int(witness.a_to_b.origin_index),
            candidate_index=int(witness.a_to_b.candidate_index),
        ),
        b_to_a=HausdorffDirectedWitness(
            distance_m=float(witness.b_to_a.distance_m),
            origin_index=int(witness.b_to_a.origin_index),
            candidate_index=int(witness.b_to_a.candidate_index),
        ),
    )


def hausdorff_polygon_boundary(
    exterior_a: Sequence[Point | tuple[float, float]],
    exterior_b: Sequence[Point | tuple[float, float]],
    *,
    holes_a: Sequence[Sequence[Point | tuple[float, float]]] | None = None,
    holes_b: Sequence[Sequence[Point | tuple[float, float]]] | None = None,
    max_segment_length_m: float | None = 100.0,
    max_segment_angle_deg: float | None = 0.1,
    sample_cap: int = 50_000,
) -> float:
    """Symmetric Hausdorff distance over polygon boundaries."""
    polygon_a = Polygon(exterior_a, holes_a)
    polygon_b = Polygon(exterior_b, holes_b)

    return float(
        _geodist_rs.hausdorff_polygon_boundary(
            polygon_a._handle,
            polygon_b._handle,
            max_segment_length_m,
            max_segment_angle_deg,
            int(sample_cap),
        )
    )
