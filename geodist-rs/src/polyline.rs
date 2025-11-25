//! Polyline and MultiLineString sampling helpers.
//!
//! Densification follows the geometry distance metrics spec: callers supply at
//! least one spacing knob and a sample cap, vertices are validated in order,
//! and consecutive duplicates collapse before sampling to keep indices
//! deterministic.

use std::f64::consts::PI;

use rstar::{AABB, PointDistance, RTree, RTreeObject};

use crate::constants::EARTH_RADIUS_METERS;
use crate::distance::geodesic_distance;
use crate::{BoundingBox, Distance, GeodistError, Point, VertexValidationError};

/// Options controlling polyline densification.
///
/// At least one of [`max_segment_length_m`] or [`max_segment_angle_deg`] must
/// be provided to bound spacing between emitted samples. [`sample_cap`] limits
/// the total number of generated points to guard against runaway densification.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct DensificationOptions {
  /// Maximum allowed chord length per subsegment in meters.
  pub max_segment_length_m: Option<f64>,
  /// Maximum allowed angular separation per subsegment in degrees.
  pub max_segment_angle_deg: Option<f64>,
  /// Hard cap on the number of emitted samples across the flattened geometry.
  pub sample_cap: usize,
}

trait SegmentGeometry {
  type SegmentData: Copy;

  fn describe_segment(
    &self,
    start: Point,
    end: Point,
    options: &DensificationOptions,
    start_index: usize,
  ) -> Result<Option<SegmentDescriptor<Self::SegmentData>>, GeodistError>;

  fn interpolate_segment(
    &self,
    start: Point,
    end: Point,
    descriptor: &SegmentDescriptor<Self::SegmentData>,
  ) -> Vec<Point>;
}

impl Default for DensificationOptions {
  fn default() -> Self {
    Self {
      max_segment_length_m: Some(100.0),
      max_segment_angle_deg: Some(0.1),
      sample_cap: 50_000,
    }
  }
}

impl DensificationOptions {
  const fn validate(&self) -> Result<(), GeodistError> {
    if self.max_segment_length_m.is_none() && self.max_segment_angle_deg.is_none() {
      return Err(GeodistError::MissingDensificationKnob);
    }
    Ok(())
  }
}

/// Flattened samples for a (multi)polyline with part offsets preserved.
///
/// Samples are stored contiguously in traversal order, while `part_offsets`
/// records the start index of each component polyline to avoid re-allocating
/// nested vectors.
#[derive(Debug, Clone, PartialEq)]
pub struct FlattenedPolyline {
  samples: Vec<Point>,
  part_offsets: Vec<usize>,
}

impl FlattenedPolyline {
  /// Return the sampled points across all parts.
  pub fn samples(&self) -> &[Point] {
    &self.samples
  }

  /// Offsets delimiting each part within the flattened samples.
  pub fn part_offsets(&self) -> &[usize] {
    &self.part_offsets
  }

  /// Clip samples to a bounding box while preserving part offsets.
  ///
  /// Empty outputs return [`GeodistError::EmptyPointSet`].
  pub fn clip(&self, bounding_box: &crate::BoundingBox) -> Result<Self, GeodistError> {
    let mut filtered = Vec::new();
    let mut offsets = Vec::with_capacity(self.part_offsets.len());
    offsets.push(0);
    let mut running_total = 0usize;

    for window in self.part_offsets.windows(2) {
      let start = window[0];
      let end = window[1];
      let part_slice = &self.samples[start..end];
      let mut kept: Vec<Point> = part_slice
        .iter()
        .copied()
        .filter(|point| bounding_box.contains(point))
        .collect();
      running_total += kept.len();
      offsets.push(running_total);
      filtered.append(&mut kept);
    }

    if filtered.is_empty() {
      return Err(GeodistError::EmptyPointSet);
    }

    Ok(Self {
      samples: filtered,
      part_offsets: offsets,
    })
  }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct PolylineHausdorffOptions {
  pub symmetric: bool,
  pub bounding_box: Option<BoundingBox>,
  pub return_witness: bool,
  pub max_segment_length_m: Option<f64>,
  pub max_segment_angle_deg: Option<f64>,
  pub sample_cap: usize,
}

impl Default for PolylineHausdorffOptions {
  fn default() -> Self {
    Self {
      symmetric: true,
      bounding_box: None,
      return_witness: false,
      max_segment_length_m: Some(100.0),
      max_segment_angle_deg: Some(0.1),
      sample_cap: 50_000,
    }
  }
}

impl PolylineHausdorffOptions {
  pub const fn densification_options(&self) -> DensificationOptions {
    DensificationOptions {
      max_segment_length_m: self.max_segment_length_m,
      max_segment_angle_deg: self.max_segment_angle_deg,
      sample_cap: self.sample_cap,
    }
  }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct PolylineWitness {
  distance: Distance,
  source_part: usize,
  source_index: usize,
  target_part: usize,
  target_index: usize,
  source_coord: Point,
  target_coord: Point,
}

impl PolylineWitness {
  pub const fn distance(&self) -> Distance {
    self.distance
  }

  pub const fn source_part(&self) -> usize {
    self.source_part
  }

  pub const fn source_index(&self) -> usize {
    self.source_index
  }

  pub const fn target_part(&self) -> usize {
    self.target_part
  }

  pub const fn target_index(&self) -> usize {
    self.target_index
  }

  pub const fn source_coord(&self) -> Point {
    self.source_coord
  }

  pub const fn target_coord(&self) -> Point {
    self.target_coord
  }
}

#[derive(Debug, Clone, PartialEq)]
pub struct PolylineHausdorffResult {
  distance: Distance,
  witness: Option<PolylineWitness>,
}

impl PolylineHausdorffResult {
  pub const fn distance(&self) -> Distance {
    self.distance
  }

  pub const fn witness(&self) -> Option<PolylineWitness> {
    self.witness
  }
}

/// Directed or symmetric Hausdorff distance over polylines and
/// MultiLineStrings.
///
/// Inputs are supplied as collections of parts, where each part contains
/// ordered vertices `(lat, lon)` in degrees. Densification follows
/// [`DensificationOptions`] and preserves part offsets for witness mapping.
/// When `options.symmetric` is `true` (default), returns the dominant
/// direction; otherwise evaluates A→B only.
pub fn hausdorff_polyline(
  polyline_a: &[Vec<Point>],
  polyline_b: &[Vec<Point>],
  options: PolylineHausdorffOptions,
) -> Result<PolylineHausdorffResult, GeodistError> {
  let densification = options.densification_options();
  let samples_a = densify_multiline(polyline_a, densification)?;
  let samples_b = densify_multiline(polyline_b, densification)?;

  let clipped_a = clip_if_needed(samples_a, options.bounding_box)?;
  let clipped_b = clip_if_needed(samples_b, options.bounding_box)?;

  let enumerated_a = enumerate_samples(&clipped_a);
  let enumerated_b = enumerate_samples(&clipped_b);

  if options.symmetric {
    let forward = hausdorff_directed_polyline(&enumerated_a, &enumerated_b)?;
    let reverse = hausdorff_directed_polyline(&enumerated_b, &enumerated_a)?;
    let dominant = pick_symmetric_witness(forward, reverse);
    let distance = Distance::from_meters(dominant.distance_m)?;
    let witness = options.return_witness.then(|| map_directed_witness(dominant));

    return Ok(PolylineHausdorffResult { distance, witness });
  }

  let directed = hausdorff_directed_polyline(&enumerated_a, &enumerated_b)?;
  let distance = Distance::from_meters(directed.distance_m)?;
  let witness = options.return_witness.then(|| map_directed_witness(directed));

  Ok(PolylineHausdorffResult { distance, witness })
}

/// Densify a single polyline into ordered samples.
///
/// Collapses consecutive duplicate vertices, validates latitude/longitude
/// ranges, and inserts intermediate samples along great-circle arcs according
/// to the provided [`DensificationOptions`]. Returns an error if the input is
/// degenerate after de-duplication, if no spacing knobs are configured, or if
/// densification would exceed the configured sample cap.
pub fn densify_polyline(vertices: &[Point], options: DensificationOptions) -> Result<Vec<Point>, GeodistError> {
  densify_polyline_with_geometry(vertices, options, &GreatCircleGeometry)
}

/// Densify a MultiLineString-structured collection of polylines, returning
/// flattened samples and part offsets.
///
/// Each part is validated independently with part indices threaded through
/// errors for caller context. Offsets in the returned [`FlattenedPolyline`]
/// reference the starting index of each part within the flattened samples.
/// Returns [`GeodistError::SampleCapExceeded`] when the accumulated emission
/// would cross the configured cap.
pub fn densify_multiline(
  parts: &[Vec<Point>],
  options: DensificationOptions,
) -> Result<FlattenedPolyline, GeodistError> {
  densify_multiline_with_geometry(parts, options, &GreatCircleGeometry)
}

fn densify_polyline_with_geometry<G: SegmentGeometry>(
  vertices: &[Point],
  options: DensificationOptions,
  geometry: &G,
) -> Result<Vec<Point>, GeodistError> {
  options.validate()?;
  let deduped = validate_polyline(vertices, None)?;

  let segments = build_segments(&deduped, &options, geometry)?;
  densify_segments(&segments, &deduped, &options.sample_cap, None, geometry)
}

fn densify_multiline_with_geometry<G: SegmentGeometry>(
  parts: &[Vec<Point>],
  options: DensificationOptions,
  geometry: &G,
) -> Result<FlattenedPolyline, GeodistError> {
  options.validate()?;

  let mut result = Vec::new();
  let mut offsets = Vec::with_capacity(parts.len() + 1);
  offsets.push(0);

  let mut validator = VertexValidator::new(Some(0));
  let mut total_samples = 0usize;

  for (part_index, part) in parts.iter().enumerate() {
    validator.set_part_index(part_index);
    let deduped = validate_polyline(part, Some(part_index))?;

    let segments = build_segments(&deduped, &options, geometry)?;
    // Pre-flight cap check before emitting.
    let expected = 1 + segments.iter().map(|info| info.split_count).sum::<usize>();
    let predicted_total = total_samples + expected;
    if predicted_total > options.sample_cap {
      return Err(GeodistError::SampleCapExceeded {
        expected: predicted_total,
        cap: options.sample_cap,
        part_index: Some(part_index),
      });
    }

    let mut samples = densify_segments(&segments, &deduped, &options.sample_cap, Some(part_index), geometry)?;
    total_samples = predicted_total;
    offsets.push(offsets.last().copied().unwrap_or(0) + samples.len());
    result.append(&mut samples);
  }

  Ok(FlattenedPolyline {
    samples: result,
    part_offsets: offsets,
  })
}

const WITNESS_DISTANCE_TOLERANCE_M: f64 = 1e-12;
const MIN_INDEXED_POLYLINE_SIZE: usize = 32;
const MAX_NAIVE_CROSS_PRODUCT: usize = 4_000;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum HausdorffStrategy {
  Naive,
  Indexed,
}

#[derive(Clone, Copy)]
struct PolylineSample {
  point: Point,
  part_index: usize,
  vertex_index: usize,
}

#[derive(Clone, Copy)]
struct DirectedPolylineWitness {
  distance_m: f64,
  source: PolylineSample,
  target: PolylineSample,
}

fn clip_if_needed(
  polyline: FlattenedPolyline,
  bounding_box: Option<BoundingBox>,
) -> Result<FlattenedPolyline, GeodistError> {
  if let Some(bbox) = bounding_box {
    return polyline.clip(&bbox);
  }
  Ok(polyline)
}

fn enumerate_samples(polyline: &FlattenedPolyline) -> Vec<PolylineSample> {
  let mut samples = Vec::with_capacity(polyline.samples.len());
  for (part_index, window) in polyline.part_offsets.windows(2).enumerate() {
    let start = window[0];
    let end = window[1];
    for (vertex_index, point) in polyline.samples[start..end].iter().copied().enumerate() {
      samples.push(PolylineSample {
        point,
        part_index,
        vertex_index,
      });
    }
  }
  samples
}

fn pick_symmetric_witness(a_to_b: DirectedPolylineWitness, b_to_a: DirectedPolylineWitness) -> DirectedPolylineWitness {
  let diff = (a_to_b.distance_m - b_to_a.distance_m).abs();
  if diff <= WITNESS_DISTANCE_TOLERANCE_M {
    return a_to_b;
  }

  if a_to_b.distance_m > b_to_a.distance_m {
    return a_to_b;
  }

  b_to_a
}

const fn map_directed_witness(witness: DirectedPolylineWitness) -> PolylineWitness {
  PolylineWitness {
    distance: Distance::from_meters_unchecked(witness.distance_m),
    source_part: witness.source.part_index,
    source_index: witness.source.vertex_index,
    target_part: witness.target.part_index,
    target_index: witness.target.vertex_index,
    source_coord: witness.source.point,
    target_coord: witness.target.point,
  }
}

fn hausdorff_directed_polyline(
  origins: &[PolylineSample],
  candidates: &[PolylineSample],
) -> Result<DirectedPolylineWitness, GeodistError> {
  if origins.is_empty() || candidates.is_empty() {
    return Err(GeodistError::EmptyPointSet);
  }

  let strategy = choose_strategy(origins.len(), candidates.len());
  match strategy {
    HausdorffStrategy::Naive => hausdorff_directed_polyline_naive(origins, candidates),
    HausdorffStrategy::Indexed => hausdorff_directed_polyline_indexed(origins, candidates),
  }
}

fn hausdorff_directed_polyline_naive(
  origins: &[PolylineSample],
  candidates: &[PolylineSample],
) -> Result<DirectedPolylineWitness, GeodistError> {
  let mut best: Option<DirectedPolylineWitness> = None;

  for origin in origins {
    let mut nearest: Option<DirectedPolylineWitness> = None;
    for candidate in candidates {
      let witness = directed_witness(origin, candidate)?;
      nearest = match nearest {
        Some(current) if prefers_target(current, witness) => Some(witness),
        None => Some(witness),
        Some(current) => Some(current),
      };
    }

    if let Some(nearest_witness) = nearest {
      best = match best {
        Some(current) if prefers_worse_witness(current, nearest_witness) => Some(nearest_witness),
        None => Some(nearest_witness),
        Some(current) => Some(current),
      };
    }
  }

  best.ok_or(GeodistError::EmptyPointSet)
}

fn hausdorff_directed_polyline_indexed(
  origins: &[PolylineSample],
  candidates: &[PolylineSample],
) -> Result<DirectedPolylineWitness, GeodistError> {
  let index = RTree::bulk_load(build_indexed_points(candidates));
  let mut best: Option<DirectedPolylineWitness> = None;

  for origin in origins {
    let query = [origin.point.lon, origin.point.lat];
    let mut iter = index.nearest_neighbor_iter(&query);
    let Some(first) = iter.next() else {
      return Err(GeodistError::EmptyPointSet);
    };

    let mut nearest = directed_witness(origin, &first.sample)?;
    for candidate in iter {
      let witness = directed_witness(origin, &candidate.sample)?;
      if witness.distance_m + WITNESS_DISTANCE_TOLERANCE_M < nearest.distance_m {
        nearest = witness;
        continue;
      }
      if (witness.distance_m - nearest.distance_m).abs() <= WITNESS_DISTANCE_TOLERANCE_M {
        if prefers_target(nearest, witness) {
          nearest = witness;
        }
        continue;
      }
      if witness.distance_m > nearest.distance_m + WITNESS_DISTANCE_TOLERANCE_M {
        break;
      }
    }

    best = match best {
      Some(current) if prefers_worse_witness(current, nearest) => Some(nearest),
      None => Some(nearest),
      Some(current) => Some(current),
    };
  }

  best.ok_or(GeodistError::EmptyPointSet)
}

fn directed_witness(
  origin: &PolylineSample,
  candidate: &PolylineSample,
) -> Result<DirectedPolylineWitness, GeodistError> {
  let distance_m = geodesic_distance(origin.point, candidate.point)?.meters();
  Ok(DirectedPolylineWitness {
    distance_m,
    source: *origin,
    target: *candidate,
  })
}

fn prefers_target(current: DirectedPolylineWitness, candidate: DirectedPolylineWitness) -> bool {
  if candidate.distance_m + WITNESS_DISTANCE_TOLERANCE_M < current.distance_m {
    return true;
  }

  (candidate.distance_m - current.distance_m).abs() <= WITNESS_DISTANCE_TOLERANCE_M
    && (candidate.target.part_index < current.target.part_index
      || (candidate.target.part_index == current.target.part_index
        && candidate.target.vertex_index < current.target.vertex_index))
}

fn prefers_worse_witness(current: DirectedPolylineWitness, candidate: DirectedPolylineWitness) -> bool {
  if candidate.distance_m > current.distance_m + WITNESS_DISTANCE_TOLERANCE_M {
    return true;
  }

  (candidate.distance_m - current.distance_m).abs() <= WITNESS_DISTANCE_TOLERANCE_M
    && (candidate.source.part_index < current.source.part_index
      || (candidate.source.part_index == current.source.part_index
        && (candidate.source.vertex_index < current.source.vertex_index
          || (candidate.source.vertex_index == current.source.vertex_index
            && (candidate.target.part_index < current.target.part_index
              || (candidate.target.part_index == current.target.part_index
                && candidate.target.vertex_index < current.target.vertex_index))))))
}

fn choose_strategy(a_len: usize, b_len: usize) -> HausdorffStrategy {
  if should_use_naive(a_len, b_len) {
    HausdorffStrategy::Naive
  } else {
    HausdorffStrategy::Indexed
  }
}

fn should_use_naive(a_len: usize, b_len: usize) -> bool {
  let min_size = a_len.min(b_len);
  let cross_product = a_len.saturating_mul(b_len);
  min_size < MIN_INDEXED_POLYLINE_SIZE || cross_product <= MAX_NAIVE_CROSS_PRODUCT
}

fn build_indexed_points(samples: &[PolylineSample]) -> Vec<IndexedPolylinePoint> {
  samples
    .iter()
    .copied()
    .map(|sample| IndexedPolylinePoint { sample })
    .collect()
}

#[derive(Clone, Copy)]
struct IndexedPolylinePoint {
  sample: PolylineSample,
}

impl RTreeObject for IndexedPolylinePoint {
  type Envelope = AABB<[f64; 2]>;

  fn envelope(&self) -> Self::Envelope {
    AABB::from_point([self.sample.point.lon, self.sample.point.lat])
  }
}

impl PointDistance for IndexedPolylinePoint {
  fn distance_2(&self, point: &[f64; 2]) -> f64 {
    let query = Point {
      lat: point[1],
      lon: point[0],
    };

    match geodesic_distance(self.sample.point, query) {
      Ok(distance) => {
        let meters = distance.meters();
        meters * meters
      }
      Err(_) => f64::INFINITY,
    }
  }
}

#[derive(Debug, Clone, Copy)]
struct SegmentDescriptor<G> {
  start_index: usize,
  end_index: usize,
  split_count: usize,
  geometry: G,
}

fn build_segments<G: SegmentGeometry>(
  vertices: &[Point],
  options: &DensificationOptions,
  geometry: &G,
) -> Result<Vec<SegmentDescriptor<G::SegmentData>>, GeodistError> {
  let mut segments = Vec::with_capacity(vertices.len().saturating_sub(1));

  for (index, window) in vertices.windows(2).enumerate() {
    let start = window[0];
    let end = window[1];

    if let Some(descriptor) = geometry.describe_segment(start, end, options, index)? {
      segments.push(descriptor);
    }
  }

  Ok(segments)
}

fn densify_segments<G: SegmentGeometry>(
  segments: &[SegmentDescriptor<G::SegmentData>],
  vertices: &[Point],
  sample_cap: &usize,
  part_index: Option<usize>,
  geometry: &G,
) -> Result<Vec<Point>, GeodistError> {
  if segments.is_empty() {
    // All segments collapsed to duplicates; emit one sample for the retained
    // vertex.
    return Ok(vertices.first().map_or_else(Vec::new, |vertex| vec![*vertex]));
  }

  let total_samples = 1 + segments.iter().map(|info| info.split_count).sum::<usize>();
  if total_samples > *sample_cap {
    return Err(GeodistError::SampleCapExceeded {
      expected: total_samples,
      cap: *sample_cap,
      part_index,
    });
  }

  let mut samples = Vec::with_capacity(total_samples);
  samples.push(vertices[segments[0].start_index]);

  for segment in segments {
    let start = vertices[segment.start_index];
    let end = vertices[segment.end_index];
    samples.extend(geometry.interpolate_segment(start, end, segment));
  }

  Ok(samples)
}

#[derive(Debug, Clone, Copy)]
struct GreatCircleGeometry;

impl GreatCircleGeometry {
  fn segment_split_count(distance_m: f64, central_angle_rad: f64, options: &DensificationOptions) -> usize {
    let mut splits = 1usize;

    if let Some(max_length) = options.max_segment_length_m
      && max_length > 0.0
    {
      let parts = (distance_m / max_length).ceil() as usize;
      splits = splits.max(parts);
    }

    if let Some(max_angle) = options.max_segment_angle_deg
      && max_angle > 0.0
    {
      let central_angle_deg = central_angle_rad * (180.0 / PI);
      let parts = (central_angle_deg / max_angle).ceil() as usize;
      splits = splits.max(parts);
    }

    splits.max(1)
  }

  fn interpolate_segment(start: Point, end: Point, central_angle_rad: f64, split_count: usize) -> Vec<Point> {
    let mut points = Vec::with_capacity(split_count);

    // Prevent divide-by-zero in degenerate cases; zero-length segments are
    // filtered earlier so this represents extremely short arcs.
    let sin_delta = central_angle_rad.sin();
    if sin_delta == 0.0 {
      points.push(end);
      return points;
    }

    let (lat1, lon1) = (start.lat.to_radians(), start.lon.to_radians());
    let (lat2, lon2) = (end.lat.to_radians(), end.lon.to_radians());

    for step in 1..=split_count {
      let fraction = step as f64 / split_count as f64;
      let a = ((1.0 - fraction) * central_angle_rad).sin() / sin_delta;
      let b = (fraction * central_angle_rad).sin() / sin_delta;

      let x = a * lat1.cos() * lon1.cos() + b * lat2.cos() * lon2.cos();
      let y = a * lat1.cos() * lon1.sin() + b * lat2.cos() * lon2.sin();
      let z = a * lat1.sin() + b * lat2.sin();

      let lat = z.atan2((x * x + y * y).sqrt());
      let lon = y.atan2(x);

      points.push(Point::new_unchecked(lat.to_degrees(), lon.to_degrees()));
    }

    points
  }
}

impl SegmentGeometry for GreatCircleGeometry {
  type SegmentData = f64;

  fn describe_segment(
    &self,
    start: Point,
    end: Point,
    options: &DensificationOptions,
    start_index: usize,
  ) -> Result<Option<SegmentDescriptor<Self::SegmentData>>, GeodistError> {
    let distance = geodesic_distance(start, end)?.meters();

    // Skip zero-length segments while preserving ordering.
    if distance == 0.0 {
      return Ok(None);
    }

    let central_angle_rad = distance / EARTH_RADIUS_METERS;
    let split_count = Self::segment_split_count(distance, central_angle_rad, options);

    Ok(Some(SegmentDescriptor {
      start_index,
      end_index: start_index + 1,
      split_count,
      geometry: central_angle_rad,
    }))
  }

  fn interpolate_segment(
    &self,
    start: Point,
    end: Point,
    descriptor: &SegmentDescriptor<Self::SegmentData>,
  ) -> Vec<Point> {
    Self::interpolate_segment(start, end, descriptor.geometry, descriptor.split_count)
  }
}

/// Collapse consecutive duplicate vertices while preserving order.
///
/// Intended as a preprocessing step before sampling so zero-length segments do
/// not inflate counts or produce ambiguous offsets.
pub fn collapse_duplicates(vertices: &[Point]) -> Vec<Point> {
  let mut deduped = Vec::with_capacity(vertices.len());
  let mut last: Option<Point> = None;

  for &vertex in vertices {
    if last != Some(vertex) {
      deduped.push(vertex);
      last = Some(vertex);
    }
  }

  deduped
}

/// Validate polyline vertices and collapse consecutive duplicates.
///
/// Ensures all vertices fall within valid latitude/longitude ranges and that
/// the resulting polyline retains at least two distinct vertices. Returns the
/// deduplicated vertices for downstream sampling.
pub fn validate_polyline(vertices: &[Point], part_index: Option<usize>) -> Result<Vec<Point>, GeodistError> {
  let validator = VertexValidator::new(part_index);
  validator.check_vertices(vertices)?;
  let deduped = collapse_duplicates(vertices);

  if deduped.len() < 2 {
    return Err(GeodistError::DegeneratePolyline { part_index });
  }

  Ok(deduped)
}

struct VertexValidator {
  part_index: Option<usize>,
}

impl VertexValidator {
  const fn new(part_index: Option<usize>) -> Self {
    Self { part_index }
  }

  const fn set_part_index(&mut self, part_index: usize) {
    self.part_index = Some(part_index);
  }

  fn check_vertices(&self, vertices: &[Point]) -> Result<(), GeodistError> {
    for (index, vertex) in vertices.iter().enumerate() {
      if !vertex.lat.is_finite()
        || vertex.lat < crate::constants::MIN_LAT_DEGREES
        || vertex.lat > crate::constants::MAX_LAT_DEGREES
      {
        return Err(GeodistError::InvalidVertex {
          part_index: self.part_index,
          vertex_index: index,
          error: VertexValidationError::Latitude(vertex.lat),
        });
      }

      if !vertex.lon.is_finite()
        || vertex.lon < crate::constants::MIN_LON_DEGREES
        || vertex.lon > crate::constants::MAX_LON_DEGREES
      {
        return Err(GeodistError::InvalidVertex {
          part_index: self.part_index,
          vertex_index: index,
          error: VertexValidationError::Longitude(vertex.lon),
        });
      }
    }
    Ok(())
  }
}

#[cfg(test)]
mod tests {
  use super::*;
  use crate::Point;

  #[test]
  fn rejects_missing_knobs() {
    let options = DensificationOptions {
      max_segment_length_m: None,
      max_segment_angle_deg: None,
      sample_cap: 10_000,
    };

    let vertices = vec![Point::new(0.0, 0.0).unwrap(), Point::new(0.0, 1.0).unwrap()];

    let result = densify_polyline(&vertices, options);
    assert!(matches!(result, Err(GeodistError::MissingDensificationKnob)));
  }

  #[test]
  fn rejects_degenerate_parts_even_after_dedup() {
    let options = DensificationOptions::default();
    let vertices = vec![Point::new(0.0, 0.0).unwrap(), Point::new(0.0, 0.0).unwrap()];

    let result = densify_polyline(&vertices, options);
    assert!(matches!(
      result,
      Err(GeodistError::DegeneratePolyline { part_index: None })
    ));
  }

  #[test]
  fn densifies_to_expected_count() {
    // Approximately 10 km along the equator; defaults produce 100 m spacing.
    let start = Point::new(0.0, 0.0).unwrap();
    let end = Point::new(0.0, 0.089_9).unwrap();
    let vertices = vec![start, end];

    let samples = densify_polyline(&vertices, DensificationOptions::default()).unwrap();
    assert_eq!(samples.len(), 101);
    assert_eq!(samples.first().copied().unwrap(), start);
    let last = samples.last().copied().unwrap();
    assert!((last.lat - end.lat).abs() < 1e-12);
    assert!((last.lon - end.lon).abs() < 1e-8);
  }

  #[test]
  fn errors_when_sample_cap_exceeded_with_part_context() {
    let start = Point::new(0.0, 0.0).unwrap();
    let far_end = Point::new(0.0, 60.0).unwrap(); // ~6_672 km along equator.
    let vertices = vec![start, far_end];

    let options = DensificationOptions {
      max_segment_length_m: Some(100.0),
      max_segment_angle_deg: None,
      sample_cap: 50_000,
    };

    let result = densify_multiline(&[vertices], options);

    assert!(matches!(
      result,
      Err(GeodistError::SampleCapExceeded {
        part_index: Some(0),
        ..
      })
    ));
  }

  #[test]
  fn flattens_multiline_offsets() {
    let part_a = vec![Point::new(0.0, 0.0).unwrap(), Point::new(0.0, 0.001).unwrap()];
    let part_b = vec![Point::new(1.0, 0.0).unwrap(), Point::new(1.0, 0.001).unwrap()];

    let options = DensificationOptions {
      max_segment_length_m: Some(500.0),
      max_segment_angle_deg: None,
      sample_cap: 50_000,
    };

    let flattened = densify_multiline(&[part_a, part_b], options).unwrap();
    assert_eq!(flattened.part_offsets(), &[0, 2, 4]);
    assert_eq!(flattened.samples().len(), 4);
  }

  #[test]
  fn clipped_multiline_preserves_offsets_and_empties_error() {
    let part_a = vec![
      Point::new(0.0, 0.0).unwrap(),
      Point::new(0.0, 0.001).unwrap(),
      Point::new(0.0, 0.002).unwrap(),
    ];
    let part_b = vec![Point::new(10.0, 0.0).unwrap(), Point::new(10.0, 0.001).unwrap()];

    let options = DensificationOptions {
      max_segment_length_m: Some(1_000.0),
      max_segment_angle_deg: None,
      sample_cap: 50_000,
    };
    let flattened = densify_multiline(&[part_a, part_b], options).unwrap();
    let bbox = crate::BoundingBox::new(-1.0, 1.0, -1.0, 1.0).unwrap();
    let clipped = flattened.clip(&bbox).unwrap();

    assert_eq!(clipped.part_offsets(), &[0, 3, 3]);
    assert_eq!(clipped.samples().len(), 3);

    let empty_box = crate::BoundingBox::new(-1.0, 1.0, 50.0, 60.0).unwrap();
    let result = clipped.clip(&empty_box);
    assert!(matches!(result, Err(GeodistError::EmptyPointSet)));
  }

  #[test]
  fn polyline_hausdorff_returns_witness_for_parallel_shift() {
    let line_a = vec![Point::new(0.0, 0.0).unwrap(), Point::new(0.0, 1.0).unwrap()];
    let line_b = vec![Point::new(1.0, 0.0).unwrap(), Point::new(1.0, 1.0).unwrap()];

    let options = PolylineHausdorffOptions {
      max_segment_length_m: Some(200_000.0),
      max_segment_angle_deg: None,
      return_witness: true,
      ..Default::default()
    };

    let result = hausdorff_polyline(&[line_a], &[line_b], options).unwrap();
    let witness = result.witness().expect("witness requested");
    assert_eq!(witness.source_part(), 0);
    assert_eq!(witness.target_part(), 0);
    assert_eq!(witness.source_index(), 0);
    assert_eq!(witness.target_index(), 0);
    assert!(witness.distance().meters() > 100_000.0);
  }

  #[test]
  fn polyline_hausdorff_tracks_multiline_parts() {
    let near = vec![Point::new(0.0, 0.0).unwrap(), Point::new(0.0, 0.1).unwrap()];
    let far = vec![Point::new(5.0, 0.0).unwrap(), Point::new(5.0, 0.1).unwrap()];
    let anchor = vec![Point::new(0.0, 0.0).unwrap(), Point::new(0.0, 0.1).unwrap()];

    let options = PolylineHausdorffOptions {
      max_segment_length_m: Some(200_000.0),
      max_segment_angle_deg: None,
      return_witness: true,
      ..Default::default()
    };

    let result = hausdorff_polyline(&[near, far], &[anchor], options).unwrap();
    let witness = result.witness().expect("witness requested");
    assert_eq!(witness.source_part(), 1);
    assert_eq!(witness.target_part(), 0);
    assert!(witness.distance().meters() > 400_000.0);
  }

  #[test]
  fn polyline_hausdorff_errors_when_clipped_empty() {
    let line = vec![Point::new(0.0, 0.0).unwrap(), Point::new(0.0, 0.1).unwrap()];
    let bbox = crate::BoundingBox::new(10.0, 20.0, 10.0, 20.0).unwrap();

    let options = PolylineHausdorffOptions {
      bounding_box: Some(bbox),
      ..Default::default()
    };

    let parts = std::slice::from_ref(&line);
    let result = hausdorff_polyline(parts, parts, options);
    assert!(matches!(result, Err(GeodistError::EmptyPointSet)));
  }
}
