"""Python bindings for the geodist Rust library."""

try:
    from ._geodist_rs import EARTH_RADIUS_METERS
except ImportError as exc:  # pragma: no cover - exercised by importers
    raise ImportError(
        "geodist._geodist_rs is missing; build the extension with `uv run maturin develop`."
    ) from exc

__all__ = ("EARTH_RADIUS_METERS",)
