//! Pluggable algorithm abstractions for geodesic kernels.
//!
//! The default strategy uses a spherical great-circle model, but consumers can
//! supply their own implementations while reusing the higher-level APIs.

use crate::{Distance, GeodistError, Point};

mod spherical;

pub use spherical::Spherical;

/// Strategy for computing geodesic distance between two points.
///
/// Implementations take latitude/longitude in degrees and return meter
/// distances. This trait stays minimal to remain FFI-friendly and to keep
/// algorithm swaps lightweight.
pub trait GeodesicAlgorithm {
  /// Compute geodesic distance between two points in degrees.
  fn geodesic_distance(&self, p1: Point, p2: Point) -> Result<Distance, GeodistError>;

  /// Compute distances for multiple point pairs using the same strategy.
  fn geodesic_distances(&self, pairs: &[(Point, Point)]) -> Result<Vec<f64>, GeodistError> {
    pairs
      .iter()
      .map(|(a, b)| self.geodesic_distance(*a, *b).map(|d| d.meters()))
      .collect()
  }
}
