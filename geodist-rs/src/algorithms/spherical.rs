//! Spherical great-circle implementation using the WGS84 mean radius.
//!
//! Inputs are degrees; output is meters.

use crate::constants::EARTH_RADIUS_METERS;
use crate::{Distance, GeodistError, Point};

use super::GeodesicAlgorithm;

/// Baseline spherical algorithm.
#[derive(Debug, Clone, Copy, Default)]
pub struct Spherical;

impl GeodesicAlgorithm for Spherical {
  fn geodesic_distance(&self, p1: Point, p2: Point) -> Result<Distance, GeodistError> {
    spherical_distance(p1, p2)
  }
}

fn spherical_distance(p1: Point, p2: Point) -> Result<Distance, GeodistError> {
  p1.validate()?;
  p2.validate()?;

  let lat1 = p1.latitude.to_radians();
  let lat2 = p2.latitude.to_radians();
  let delta_lat = (p2.latitude - p1.latitude).to_radians();
  let delta_lon = (p2.longitude - p1.longitude).to_radians();

  let sin_lat = (delta_lat / 2.0).sin();
  let sin_lon = (delta_lon / 2.0).sin();

  let a = sin_lat * sin_lat + lat1.cos() * lat2.cos() * sin_lon * sin_lon;
  // Clamp to guard against minor floating error that could push `a` outside
  // [0, 1] and cause NaNs.
  let normalized_a = a.clamp(0.0, 1.0);
  let c = 2.0 * normalized_a.sqrt().atan2((1.0 - normalized_a).sqrt());

  let meters = EARTH_RADIUS_METERS * c;
  Distance::from_meters(meters)
}

#[cfg(test)]
mod tests {
  use super::*;

  #[test]
  fn computes_expected_distance() {
    let origin = Point::new(0.0, 0.0).unwrap();
    let east = Point::new(0.0, 1.0).unwrap();

    let meters = Spherical.geodesic_distance(origin, east).unwrap().meters();
    let expected = 111_195.080_233_532_9;
    assert!((meters - expected).abs() < 1e-6);
  }

  #[test]
  fn propagates_validation_errors() {
    let invalid = Point {
      latitude: 200.0,
      longitude: 0.0,
    };
    let valid = Point::new(0.0, 0.0).unwrap();
    let result = Spherical.geodesic_distance(invalid, valid);
    assert!(matches!(result, Err(GeodistError::InvalidLatitude(200.0))));
  }
}
