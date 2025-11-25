from __future__ import annotations

import pytest
from pytest import approx

from geodist import (
    BoundingBox,
    Ellipsoid,
    EmptyPointSetError,
    GeodesicResult,
    HausdorffDirectedWitness,
    HausdorffWitness,
    Point,
    Point3D,
    PolylineWitness,
    geodesic_distance,
    geodesic_distance_3d,
    geodesic_distance_on_ellipsoid,
    geodesic_with_bearings,
    geodesic_with_bearings_on_ellipsoid,
    hausdorff,
    hausdorff_3d,
    hausdorff_clipped,
    hausdorff_clipped_3d,
    hausdorff_directed,
    hausdorff_directed_3d,
    hausdorff_directed_clipped,
    hausdorff_directed_clipped_3d,
    hausdorff_polygon_boundary,
    hausdorff_polyline,
)


def test_geodesic_distance_matches_rust_kernel() -> None:
    origin = Point(0.0, 0.0)
    east = Point(0.0, 1.0)

    assert geodesic_distance(origin, east) == approx(111_195.080_233_532_9)


def test_geodesic_distance_on_ellipsoid_matches_wgs84() -> None:
    origin = Point(0.0, 0.0)
    east = Point(0.0, 1.0)

    expected = 111_319.490_793_273_57
    assert geodesic_distance_on_ellipsoid(origin, east) == approx(expected)
    assert geodesic_distance_on_ellipsoid(origin, east, Ellipsoid.wgs84()) == approx(expected)


def test_geodesic_distance_3d_matches_vertical_offset() -> None:
    ground = Point3D(0.0, 0.0, 0.0)
    elevated = Point3D(0.0, 0.0, 150.0)

    assert geodesic_distance_3d(ground, elevated) == approx(150.0)


def test_geodesic_with_bearings_returns_distance_and_angles() -> None:
    origin = Point(0.0, 0.0)
    east = Point(0.0, 1.0)

    result = geodesic_with_bearings(origin, east)
    assert isinstance(result, GeodesicResult)
    assert result.distance_m == approx(111_195.080_233_532_9)
    assert result.initial_bearing_deg == approx(90.0)
    assert result.final_bearing_deg == approx(90.0)


def test_geodesic_with_bearings_on_ellipsoid_returns_distance_and_angles() -> None:
    origin = Point(0.0, 0.0)
    east = Point(0.0, 1.0)

    result = geodesic_with_bearings_on_ellipsoid(origin, east)
    assert isinstance(result, GeodesicResult)
    assert result.distance_m == approx(111_319.490_793_273_57)
    assert result.initial_bearing_deg == approx(90.0)
    assert result.final_bearing_deg == approx(90.0)


def test_hausdorff_and_directed_match_expected_distances() -> None:
    origin = Point(0.0, 0.0)
    east = Point(0.0, 1.0)

    symmetric = hausdorff([origin], [east])
    directed = hausdorff_directed([origin], [east])

    assert isinstance(symmetric, HausdorffWitness)
    assert isinstance(directed, HausdorffDirectedWitness)
    assert symmetric.distance_m == approx(geodesic_distance(origin, east))
    assert directed.distance_m == approx(geodesic_distance(origin, east))
    assert directed.origin_index == 0
    assert directed.candidate_index == 0


def test_hausdorff_clipped_filters_points() -> None:
    origin = Point(0.0, 0.0)
    east = Point(0.0, 1.0)
    east_only_box = BoundingBox(-1.0, 1.0, 0.5, 1.5)

    # Without clipping, A includes the origin so the maximum mismatch is origin->east.
    directed = hausdorff_directed([origin, east], [east])
    assert directed.distance_m == approx(geodesic_distance(origin, east))
    assert directed.origin_index == 0
    assert directed.candidate_index == 0

    # Clipping removes the origin, so both sets reduce to [east] and the distance collapses to 0.
    clipped_directed = hausdorff_directed_clipped([origin, east], [east], east_only_box)
    clipped_symmetric = hausdorff_clipped([origin, east], [east], east_only_box)
    assert clipped_directed.distance_m == approx(0.0)
    assert clipped_directed.origin_index == 1
    assert clipped_directed.candidate_index == 0
    assert clipped_symmetric.distance_m == approx(0.0)


def test_hausdorff_3d_matches_vertical_delta() -> None:
    ground = Point3D(0.0, 0.0, 0.0)
    elevated = Point3D(0.0, 0.0, 200.0)

    directed = hausdorff_directed_3d([ground], [elevated])
    symmetric = hausdorff_3d([ground], [elevated])
    assert directed.distance_m == approx(200.0)
    assert symmetric.distance_m == approx(200.0)


def test_hausdorff_3d_clipped_filters_points() -> None:
    inside = Point3D(0.0, 0.0, 50.0)
    outside = Point3D(10.0, 0.0, 0.0)
    box = BoundingBox(-1.0, 1.0, -1.0, 1.0)

    symmetric = hausdorff_clipped_3d([inside, outside], [inside], box)
    directed = hausdorff_directed_clipped_3d([inside, outside], [inside], box)
    assert symmetric.distance_m == approx(0.0)
    assert directed.distance_m == approx(0.0)


def test_polygon_boundary_hausdorff_matches_zero_for_identical() -> None:
    exterior = [
        (0.0, 0.0),
        (0.0, 1.0),
        (1.0, 1.0),
        (1.0, 0.0),
        (0.0, 0.0),
    ]
    distance = hausdorff_polygon_boundary(exterior, exterior)
    assert distance == approx(0.0)


def test_polyline_hausdorff_returns_witness() -> None:
    line_a = [(0.0, 0.0), (0.0, 1.0)]
    line_b = [(1.0, 0.0), (1.0, 1.0)]

    distance_m, witness = hausdorff_polyline(
        line_a,
        line_b,
        max_segment_length_m=200_000.0,
        max_segment_angle_deg=None,
        return_witness=True,
    )

    assert witness is not None
    assert isinstance(witness, PolylineWitness)
    assert witness.source_part == 0
    assert witness.source_index == 0
    assert witness.target_part == 0
    assert distance_m == approx(witness.distance_m)


def test_polyline_hausdorff_respects_multiline_parts() -> None:
    parts = [
        [(0.0, 0.0), (0.0, 0.1)],
        [(3.0, 0.0), (3.0, 0.1)],
    ]
    anchor = [(0.0, 0.0), (0.0, 0.1)]

    distance_m, witness = hausdorff_polyline(
        parts,
        anchor,
        max_segment_length_m=200_000.0,
        max_segment_angle_deg=None,
        return_witness=True,
    )

    assert witness is not None
    assert witness.source_part == 1
    assert distance_m == approx(witness.distance_m)


def test_polyline_hausdorff_clipping_empty_raises() -> None:
    line = [(0.0, 0.0), (0.0, 0.1)]
    bbox = BoundingBox(10.0, 20.0, 10.0, 20.0)

    with pytest.raises(EmptyPointSetError):
        hausdorff_polyline(line, line, bbox=bbox)
