//! Polygon ring validation and boundary densification.
//!
//! Rings enforce closure, orientation (CCW exterior, CW holes), and bounds.
//! Boundary sampling uses the polyline densifier; interior coverage grids are
//! deferred.

use crate::polyline::{DensificationOptions, FlattenedPolyline, collapse_duplicates, densify_multiline};
use crate::{GeodistError, Point, RingOrientation, VertexValidationError};

const RING_CLOSURE_TOLERANCE_DEG: f64 = 1e-9;

/// A polygon consisting of an exterior ring and zero or more interior holes.
#[derive(Debug, Clone, PartialEq)]
pub struct Polygon {
  exterior: Vec<Point>,
  holes: Vec<Vec<Point>>,
}

impl Polygon {
  /// Construct a validated polygon (boundary-only) from rings.
  ///
  /// # Errors
  /// - [`GeodistError::DegeneratePolyline`] when a ring is too short or not
  ///   closed.
  /// - [`GeodistError::InvalidVertex`] when coordinates are out of bounds.
  /// - [`GeodistError::InvalidBoundingBox`] when orientation is wrong or a hole
  ///   lies outside the exterior ring.
  pub fn new(exterior: Vec<Point>, holes: Vec<Vec<Point>>) -> Result<Self, GeodistError> {
    let exterior = normalize_ring(exterior, RingOrientation::CounterClockwise, None)?;
    let mut normalized_holes = Vec::with_capacity(holes.len());

    for (idx, hole) in holes.into_iter().enumerate() {
      let normalized = normalize_ring(hole, RingOrientation::Clockwise, Some(idx + 1))?;
      ensure_hole_inside_exterior(&normalized, &exterior)?;
      normalized_holes.push(normalized);
    }

    Ok(Self {
      exterior,
      holes: normalized_holes,
    })
  }

  /// Densify boundary rings, returning flattened samples and part offsets.
  ///
  /// Parts are ordered as exterior then each hole in sequence. Sample cap
  /// applies to the flattened result.
  pub fn densify_boundaries(&self, options: DensificationOptions) -> Result<FlattenedPolyline, GeodistError> {
    let mut parts = Vec::with_capacity(1 + self.holes.len());
    parts.push(self.exterior.clone());
    parts.extend(self.holes.iter().cloned());
    densify_multiline(&parts, options)
  }
}

fn normalize_ring(
  ring: Vec<Point>,
  expected_orientation: RingOrientation,
  part_index: Option<usize>,
) -> Result<Vec<Point>, GeodistError> {
  validate_vertices(&ring, part_index)?;
  let deduped = collapse_duplicates(&ring);
  if deduped.len() < 4 {
    return Err(GeodistError::DegeneratePolyline { part_index });
  }

  ensure_closed(&deduped, part_index)?;
  ensure_orientation(&deduped, expected_orientation)?;
  Ok(deduped)
}

fn validate_vertices(vertices: &[Point], part_index: Option<usize>) -> Result<(), GeodistError> {
  for (index, vertex) in vertices.iter().enumerate() {
    if !vertex.lat.is_finite()
      || vertex.lat < crate::constants::MIN_LAT_DEGREES
      || vertex.lat > crate::constants::MAX_LAT_DEGREES
    {
      return Err(GeodistError::InvalidVertex {
        part_index,
        vertex_index: index,
        error: VertexValidationError::Latitude(vertex.lat),
      });
    }

    if !vertex.lon.is_finite()
      || vertex.lon < crate::constants::MIN_LON_DEGREES
      || vertex.lon > crate::constants::MAX_LON_DEGREES
    {
      return Err(GeodistError::InvalidVertex {
        part_index,
        vertex_index: index,
        error: VertexValidationError::Longitude(vertex.lon),
      });
    }
  }
  Ok(())
}

fn ensure_closed(vertices: &[Point], part_index: Option<usize>) -> Result<(), GeodistError> {
  let first = vertices
    .first()
    .ok_or(GeodistError::DegeneratePolyline { part_index })?;
  let last = vertices.last().expect("non-empty after check");
  let lat_delta = (first.lat - last.lat).abs();
  let lon_delta = (first.lon - last.lon).abs();
  if lat_delta > RING_CLOSURE_TOLERANCE_DEG || lon_delta > RING_CLOSURE_TOLERANCE_DEG {
    return Err(GeodistError::DegeneratePolyline { part_index });
  }
  Ok(())
}

fn ensure_orientation(vertices: &[Point], expected: RingOrientation) -> Result<(), GeodistError> {
  let area2 = signed_area(vertices);
  let is_ccw = area2 > 0.0;
  match expected {
    RingOrientation::CounterClockwise if !is_ccw => Err(GeodistError::InvalidBoundingBox {
      min_lat: 0.0,
      max_lat: 0.0,
      min_lon: 0.0,
      max_lon: 0.0,
    }),
    RingOrientation::Clockwise if is_ccw => Err(GeodistError::InvalidBoundingBox {
      min_lat: 0.0,
      max_lat: 0.0,
      min_lon: 0.0,
      max_lon: 0.0,
    }),
    _ => Ok(()),
  }
}

fn ensure_hole_inside_exterior(hole: &[Point], exterior: &[Point]) -> Result<(), GeodistError> {
  // Use first vertex as a witness; rings are simple in this increment.
  let witness = hole
    .first()
    .ok_or(GeodistError::DegeneratePolyline { part_index: None })?;
  if point_in_ring(witness, exterior) {
    Ok(())
  } else {
    Err(GeodistError::InvalidBoundingBox {
      min_lat: 0.0,
      max_lat: 0.0,
      min_lon: 0.0,
      max_lon: 0.0,
    })
  }
}

fn point_in_ring(point: &Point, ring: &[Point]) -> bool {
  let mut intersects = false;
  for edge in ring.windows(2) {
    let (p1, p2) = (edge[0], edge[1]);
    let intersects_edge = ((p1.lat > point.lat) != (p2.lat > point.lat))
      && (point.lon < (p2.lon - p1.lon) * (point.lat - p1.lat) / (p2.lat - p1.lat + f64::EPSILON) + p1.lon);
    if intersects_edge {
      intersects = !intersects;
    }
  }
  intersects
}

fn signed_area(vertices: &[Point]) -> f64 {
  let mut sum = 0.0;
  for window in vertices.windows(2) {
    let (x1, y1) = (window[0].lon, window[0].lat);
    let (x2, y2) = (window[1].lon, window[1].lat);
    sum += x1 * y2 - x2 * y1;
  }
  sum
}

#[cfg(test)]
mod tests {
  use super::*;

  fn ccw_square() -> Vec<Point> {
    vec![
      Point::new(0.0, 0.0).unwrap(),
      Point::new(0.0, 1.0).unwrap(),
      Point::new(1.0, 1.0).unwrap(),
      Point::new(1.0, 0.0).unwrap(),
      Point::new(0.0, 0.0).unwrap(),
    ]
  }

  fn cw_square() -> Vec<Point> {
    vec![
      Point::new(0.0, 0.0).unwrap(),
      Point::new(1.0, 0.0).unwrap(),
      Point::new(1.0, 1.0).unwrap(),
      Point::new(0.0, 1.0).unwrap(),
      Point::new(0.0, 0.0).unwrap(),
    ]
  }

  #[test]
  fn rejects_unclosed_ring() {
    let mut ring = ccw_square();
    ring.pop();
    let result = Polygon::new(ring, vec![]);
    assert!(matches!(result, Err(GeodistError::DegeneratePolyline { .. })));
  }

  #[test]
  fn rejects_wrong_orientation() {
    let exterior = cw_square();
    let result = Polygon::new(exterior, vec![]);
    assert!(matches!(result, Err(GeodistError::InvalidBoundingBox { .. })));
  }

  #[test]
  fn rejects_hole_outside_exterior() {
    let exterior = ccw_square();
    let mut hole = cw_square();
    hole.iter_mut().for_each(|p| p.lat += 5.0);
    let result = Polygon::new(exterior, vec![hole]);
    assert!(matches!(result, Err(GeodistError::InvalidBoundingBox { .. })));
  }

  #[test]
  fn accepts_ccw_exterior_and_cw_hole() {
    let exterior = ccw_square();
    let hole = cw_square();
    let polygon = Polygon::new(exterior.clone(), vec![hole.clone()]).unwrap();
    let samples = polygon
      .densify_boundaries(DensificationOptions {
        max_segment_length_m: Some(1_000.0),
        max_segment_angle_deg: None,
        sample_cap: 10_000,
      })
      .unwrap();
    assert_eq!(samples.part_offsets().len(), 3);
  }
}
