"""IO helpers for serializing and parsing geometry representations."""

from __future__ import annotations

from .errors import KernelUnavailableError
from .geometry import Geometry
from .types import CRSLike, GeoJSONLike


def loads_wkt(wkt: str, *, crs: CRSLike = None) -> Geometry:
    """Parse a WKT string into a geometry, preserving optional CRS metadata."""
    raise KernelUnavailableError("WKT parsing is unavailable until Rust parsers are exposed to the Python layer.")


def dumps_wkt(geometry: Geometry) -> str:
    """Serialize a geometry to its WKT representation."""
    raise KernelUnavailableError(
        "WKT serialization is unavailable until Rust serializers are exposed to the Python layer."
    )


def loads_wkb(wkb: bytes, *, crs: CRSLike = None) -> Geometry:
    """Parse WKB bytes into a geometry."""
    raise KernelUnavailableError("WKB parsing is unavailable until Rust parsers are exposed to the Python layer.")


def dumps_wkb(geometry: Geometry) -> bytes:
    """Serialize a geometry to WKB bytes."""
    raise KernelUnavailableError(
        "WKB serialization is unavailable until Rust serializers are exposed to the Python layer."
    )


def loads_geojson(mapping: GeoJSONLike, *, crs: CRSLike = None) -> Geometry:
    """Parse a GeoJSON mapping into the corresponding geometry."""
    raise KernelUnavailableError("GeoJSON parsing is unavailable until Rust parsers are exposed to the Python layer.")


def dumps_geojson(geometry: Geometry) -> GeoJSONLike:
    """Serialize a geometry to a GeoJSON mapping."""
    raise KernelUnavailableError(
        "GeoJSON serialization is unavailable until Rust serializers are exposed to the Python layer."
    )


__all__ = (
    "dumps_geojson",
    "dumps_wkb",
    "dumps_wkt",
    "loads_geojson",
    "loads_wkb",
    "loads_wkt",
)
