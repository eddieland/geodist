from pytest import approx

import geodist


def test_constant_reexported() -> None:
    assert geodist.EARTH_RADIUS_METERS == approx(6_371_008.8)
