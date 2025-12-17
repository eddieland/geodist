from __future__ import annotations

import pytest
from pytest import approx

from loxodrome import _loxodrome_rs


def test_densification_options_validation_and_defaults() -> None:
    opts = _loxodrome_rs.DensificationOptions()
    assert opts.to_tuple() == (100.0, 0.1, 50_000)

    with pytest.raises(_loxodrome_rs.InvalidDistanceError):
        _loxodrome_rs.DensificationOptions(
            max_segment_length_m=None,
            max_segment_angle_deg=None,
            sample_cap=10,
        )


def test_polyline_hausdorff_smoke() -> None:
    line_a = _loxodrome_rs.LineString([(0.0, 0.0), (0.0, 1.0)])
    line_b = _loxodrome_rs.LineString([(0.0, 0.0), (1.0, 0.0)])
    options = _loxodrome_rs.DensificationOptions(
        max_segment_length_m=1_000_000.0,
        max_segment_angle_deg=None,
        sample_cap=1000,
    )

    directed = _loxodrome_rs.hausdorff_directed_polyline([line_a], [line_b], options)
    assert isinstance(directed, _loxodrome_rs.PolylineDirectedWitness)
    assert directed.source_part == 0
    assert directed.target_part == 0
    assert directed.source_index == 1
    assert directed.target_index == 0
    assert directed.distance_m > 100_000
    assert directed.source_coord.to_tuple() == (0.0, 1.0)

    symmetric = _loxodrome_rs.hausdorff_polyline([line_a], [line_b], options)
    assert isinstance(symmetric, _loxodrome_rs.PolylineHausdorffWitness)
    assert symmetric.distance_m >= symmetric.a_to_b.distance_m
    assert symmetric.distance_m >= symmetric.b_to_a.distance_m
    assert (
        symmetric.a_to_b.source_part,
        symmetric.a_to_b.source_index,
        symmetric.a_to_b.target_part,
        symmetric.a_to_b.target_index,
    ) == (
        0,
        1,
        0,
        0,
    )
    assert (
        symmetric.b_to_a.source_part,
        symmetric.b_to_a.source_index,
        symmetric.b_to_a.target_part,
        symmetric.b_to_a.target_index,
    ) == (
        0,
        1,
        0,
        0,
    )


def test_polyline_hausdorff_multiline_witness_matches_argmax() -> None:
    # A has one shared part with B and one part shifted north; B mirrors with a southern part.
    line_a_overlap = _loxodrome_rs.LineString([(0.0, 0.0), (0.0, 1.0)])
    line_a_offset = _loxodrome_rs.LineString([(10.0, 0.0), (10.0, 1.0)])
    line_b_overlap = _loxodrome_rs.LineString([(0.0, 0.0), (0.0, 1.0)])
    line_b_offset = _loxodrome_rs.LineString([(-10.0, 0.0), (-10.0, 1.0)])
    options = _loxodrome_rs.DensificationOptions(
        max_segment_length_m=10_000_000.0,
        max_segment_angle_deg=None,
        sample_cap=10_000,
    )

    witness = _loxodrome_rs.hausdorff_polyline(
        [line_a_overlap, line_a_offset],
        [line_b_overlap, line_b_offset],
        options=options,
    )

    def directed_argmax(
        a_parts: list[_loxodrome_rs.LineString], b_parts: list[_loxodrome_rs.LineString]
    ) -> tuple[float, int, int, int, int]:
        max_len, max_angle, cap = options.to_tuple()
        sampled_a = [part.densify(max_len, max_angle, cap) for part in a_parts]
        sampled_b = [part.densify(max_len, max_angle, cap) for part in b_parts]
        best: tuple[float, int, int, int, int] | None = None
        for a_part_idx, samples in enumerate(sampled_a):
            for source_idx, source in enumerate(samples):
                min_dist = None
                min_target = None
                for b_part_idx, targets in enumerate(sampled_b):
                    for target_idx, target in enumerate(targets):
                        dist = _loxodrome_rs.geodesic_distance(source, target)
                        if min_dist is None or dist < min_dist:
                            min_dist = dist
                            min_target = (b_part_idx, target_idx)
                assert min_dist is not None
                assert min_target is not None
                if best is None or min_dist > best[0]:
                    best = (min_dist, a_part_idx, source_idx, min_target[0], min_target[1])
        assert best is not None
        return best

    a_to_b = directed_argmax([line_a_overlap, line_a_offset], [line_b_overlap, line_b_offset])
    b_to_a = directed_argmax([line_b_overlap, line_b_offset], [line_a_overlap, line_a_offset])

    assert witness.a_to_b.distance_m == approx(a_to_b[0])
    assert witness.a_to_b.source_part == a_to_b[1]
    assert witness.a_to_b.source_index == a_to_b[2]
    assert witness.a_to_b.target_part == a_to_b[3]
    assert witness.a_to_b.target_index == a_to_b[4]

    assert witness.b_to_a.distance_m == approx(b_to_a[0])
    assert witness.b_to_a.source_part == b_to_a[1]
    assert witness.b_to_a.source_index == b_to_a[2]
    assert witness.b_to_a.target_part == b_to_a[3]
    assert witness.b_to_a.target_index == b_to_a[4]

    assert witness.distance_m == approx(max(a_to_b[0], b_to_a[0]))


def test_polyline_hausdorff_clipped_smoke() -> None:
    line_a = _loxodrome_rs.LineString([(0.0, 0.0), (0.0, 1.0)])
    line_b = _loxodrome_rs.LineString([(0.0, 0.0), (1.0, 0.0)])
    bbox = _loxodrome_rs.BoundingBox(-2.0, 2.0, -2.0, 2.0)
    options = _loxodrome_rs.DensificationOptions(
        max_segment_length_m=250_000.0,
        max_segment_angle_deg=None,
        sample_cap=1000,
    )

    clipped = _loxodrome_rs.hausdorff_polyline_clipped([line_a], [line_b], bbox, options)
    assert isinstance(clipped, _loxodrome_rs.PolylineHausdorffWitness)
    assert clipped.a_to_b.source_part == 0
    assert clipped.b_to_a.target_part == 0
    assert clipped.distance_m >= clipped.a_to_b.distance_m


def test_polyline_chamfer_mean_smoke() -> None:
    line_a = _loxodrome_rs.LineString([(0.0, 0.0), (0.0, 1.0)])
    line_b = _loxodrome_rs.LineString([(0.0, 0.0), (0.0, 2.0)])
    options = _loxodrome_rs.DensificationOptions(
        max_segment_length_m=1_000_000.0,
        max_segment_angle_deg=None,
        sample_cap=1000,
    )

    chamfer = _loxodrome_rs.chamfer_polyline([line_a], [line_b], reduction="mean", options=options)
    assert isinstance(chamfer, _loxodrome_rs.ChamferResult)
    assert chamfer.a_to_b.witness is None
    assert chamfer.b_to_a.witness is None
    assert chamfer.distance_m >= 0.0


def test_polyline_chamfer_max_emits_witness() -> None:
    line_a = _loxodrome_rs.LineString([(0.0, 0.0), (0.0, 1.0), (0.0, 2.0)])
    line_b = _loxodrome_rs.LineString([(0.0, 0.0), (0.0, 0.2)])
    options = _loxodrome_rs.DensificationOptions(
        max_segment_length_m=1_000_000.0,
        max_segment_angle_deg=None,
        sample_cap=1000,
    )

    directed = _loxodrome_rs.chamfer_directed_polyline([line_a], [line_b], reduction="max", options=options)
    assert isinstance(directed.witness, _loxodrome_rs.PolylineDirectedWitness)
    assert directed.distance_m == directed.witness.distance_m
    assert directed.witness.source_index >= directed.witness.target_index


def test_polyline_chamfer_clipped_errors() -> None:
    line_a = _loxodrome_rs.LineString([(10.0, 0.0), (10.0, 1.0)])
    line_b = _loxodrome_rs.LineString([(11.0, 0.0), (11.0, 1.0)])
    bbox = _loxodrome_rs.BoundingBox(-1.0, 1.0, -1.0, 1.0)

    with pytest.raises(_loxodrome_rs.EmptyPointSetError):
        _loxodrome_rs.chamfer_polyline_clipped([line_a], [line_b], bbox, reduction="mean")
