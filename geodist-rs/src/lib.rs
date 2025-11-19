//! Public surface for geodist kernels and types.

#[cfg(feature = "python")]
mod python;

mod constants;
mod distance;
mod hausdorff;
mod types;

pub use constants::EARTH_RADIUS_METERS;
pub use distance::{geodesic_distance, geodesic_distances};
pub use hausdorff::{hausdorff, hausdorff_directed};
pub use types::{Distance, GeodistError, Point};
