//! Great-circle distance on a spherical Earth (WGS84 mean radius).
//!
//! Inputs are degrees; output is meters.

use crate::algorithms::{GeodesicAlgorithm, Spherical};
use crate::{Distance, GeodistError, Point};

/// Compute great-circle (geodesic) distance between two geographic points in
/// degrees using the default spherical algorithm.
///
/// Returns a validated [`Distance`] in meters. Inputs are validated before
/// calculations.
pub fn geodesic_distance(p1: Point, p2: Point) -> Result<Distance, GeodistError> {
  geodesic_distance_with(&Spherical, p1, p2)
}

/// Compute geodesic distance using a custom algorithm strategy.
pub fn geodesic_distance_with<A: GeodesicAlgorithm>(
  algorithm: &A,
  p1: Point,
  p2: Point,
) -> Result<Distance, GeodistError> {
  algorithm.geodesic_distance(p1, p2)
}

/// Compute geodesic distances for many point pairs in a single call.
///
/// Accepts a slice of `(origin, destination)` tuples and returns a `Vec` of
/// meter distances in the same order. Validation is performed for every point;
/// the first invalid coordinate returns an error and short-circuits.
pub fn geodesic_distances(pairs: &[(Point, Point)]) -> Result<Vec<f64>, GeodistError> {
  geodesic_distances_with(&Spherical, pairs)
}

/// Compute batch geodesic distances with a custom algorithm strategy.
pub fn geodesic_distances_with<A: GeodesicAlgorithm>(
  algorithm: &A,
  pairs: &[(Point, Point)],
) -> Result<Vec<f64>, GeodistError> {
  algorithm.geodesic_distances(pairs)
}

#[cfg(test)]
mod tests {
  use super::*;

  #[test]
  fn computes_equatorial_degree() {
    let origin = Point::new(0.0, 0.0).unwrap();
    let east = Point::new(0.0, 1.0).unwrap();

    let meters = geodesic_distance(origin, east).unwrap().meters();
    let expected = 111_195.080_233_532_9;
    assert!((meters - expected).abs() < 1e-6);
  }

  #[test]
  fn handles_polar_antipodal_case() {
    let north_pole = Point::new(90.0, 0.0).unwrap();
    let south_pole = Point::new(-90.0, 0.0).unwrap();

    let meters = geodesic_distance(north_pole, south_pole).unwrap().meters();
    let expected = 20_015_114.442_035_925;
    assert!((meters - expected).abs() < 1e-6);
  }

  #[test]
  fn computes_long_range_path() {
    let new_york = Point::new(40.7128, -74.0060).unwrap();
    let london = Point::new(51.5074, -0.1278).unwrap();

    let meters = geodesic_distance(new_york, london).unwrap().meters();
    let expected = 5_570_229.873_656_523;
    assert!((meters - expected).abs() < 1e-6);
  }

  #[test]
  fn identical_points_are_zero() {
    let point = Point::new(10.0, 20.0).unwrap();
    let meters = geodesic_distance(point, point).unwrap().meters();
    assert_eq!(meters, 0.0);
  }

  #[test]
  fn computes_batch_distances_in_order() {
    let pairs = [
      (Point::new(0.0, 0.0).unwrap(), Point::new(0.0, 1.0).unwrap()),
      (Point::new(0.0, 0.0).unwrap(), Point::new(1.0, 0.0).unwrap()),
    ];

    let results = geodesic_distances(&pairs).unwrap();
    assert_eq!(results.len(), 2);

    let expected_first = geodesic_distance(pairs[0].0, pairs[0].1).unwrap().meters();
    let expected_second = geodesic_distance(pairs[1].0, pairs[1].1).unwrap().meters();

    assert!((results[0] - expected_first).abs() < 1e-9);
    assert!((results[1] - expected_second).abs() < 1e-9);
  }

  #[test]
  fn propagates_validation_error() {
    let valid = Point::new(0.0, 0.0).unwrap();
    let invalid = Point {
      latitude: 95.0,
      longitude: 0.0,
    };
    let pairs = [(valid, valid), (invalid, valid)];

    let result = geodesic_distances(&pairs);
    assert!(matches!(result, Err(GeodistError::InvalidLatitude(95.0))));
  }

  #[test]
  fn supports_custom_algorithm_for_single_distance() {
    struct FakeAlgorithm;

    impl GeodesicAlgorithm for FakeAlgorithm {
      fn geodesic_distance(&self, _p1: Point, _p2: Point) -> Result<Distance, GeodistError> {
        Distance::from_meters(42.0)
      }
    }

    let origin = Point::new(0.0, 0.0).unwrap();
    let destination = Point::new(1.0, 1.0).unwrap();

    let meters = geodesic_distance_with(&FakeAlgorithm, origin, destination)
      .unwrap()
      .meters();
    assert_eq!(meters, 42.0);
  }

  #[test]
  fn supports_custom_algorithm_for_batch() {
    struct ConstantAlgorithm;

    impl GeodesicAlgorithm for ConstantAlgorithm {
      fn geodesic_distance(&self, _p1: Point, _p2: Point) -> Result<Distance, GeodistError> {
        Distance::from_meters(1.5)
      }
    }

    let points = [
      (Point::new(0.0, 0.0).unwrap(), Point::new(0.0, 1.0).unwrap()),
      (Point::new(10.0, 10.0).unwrap(), Point::new(10.0, 11.0).unwrap()),
    ];

    let results = geodesic_distances_with(&ConstantAlgorithm, &points).unwrap();
    assert_eq!(results, vec![1.5, 1.5]);
  }
}
