"""Geometry wrappers exposed by the geodist Python package."""

from __future__ import annotations

from .errors import KernelUnavailableError
from .types import Coordinate, CoordinateSequence, CRSLike


class Geometry:
    """Base class for immutable geometry wrappers backed by Rust handles."""

    __slots__ = ("_handle", "_crs")

    def __init__(self, handle: object | None, crs: CRSLike = None) -> None:
        self._handle = handle
        self._crs = crs

    @property
    def crs(self) -> CRSLike:
        """Declared coordinate reference system, if provided."""
        return self._crs

    def __eq__(self, other: object) -> bool:
        # Defer to typed equals predicate once kernels are wired.
        return NotImplemented

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(crs={self._crs!r})"

    @staticmethod
    def _raise_missing_kernel() -> None:
        raise KernelUnavailableError(
            "Rust kernels are not available; build the extension to enable geometry construction."
        )


class Point(Geometry):
    """Immutable point geometry using an opaque Rust handle."""

    __slots__ = ()

    def __init__(self, coordinate: Coordinate, crs: CRSLike = None) -> None:
        super().__init__(handle=None, crs=crs)
        self._raise_missing_kernel()

    @classmethod
    def from_xy(cls, x: float, y: float, crs: CRSLike = None) -> Point:
        """Build a point from an x/y pair."""
        cls._raise_missing_kernel()
        raise AssertionError("Point construction did not raise as expected.")  # pragma: no cover


class LineString(Geometry):
    """Ordered sequence of coordinates forming a line."""

    __slots__ = ()

    def __init__(self, coordinates: CoordinateSequence, crs: CRSLike = None) -> None:
        super().__init__(handle=None, crs=crs)
        self._raise_missing_kernel()


class Polygon(Geometry):
    """Polygon with an outer ring and optional interior holes."""

    __slots__ = ()

    def __init__(
        self,
        exterior: CoordinateSequence,
        holes: list[CoordinateSequence] | None = None,
        crs: CRSLike = None,
    ) -> None:
        super().__init__(handle=None, crs=crs)
        self._raise_missing_kernel()


class GeometryCollection(Geometry):
    """Heterogeneous collection of geometry objects."""

    __slots__ = ()

    def __init__(self, geometries: list[Geometry], crs: CRSLike = None) -> None:
        super().__init__(handle=None, crs=crs)
        self._raise_missing_kernel()


__all__ = (
    "Geometry",
    "GeometryCollection",
    "LineString",
    "Point",
    "Polygon",
)
