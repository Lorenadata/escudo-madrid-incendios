"""M18: redondeo grueso del portal público (anti-diferencias)."""

from escudo_api.routers.portal import _coarse, _share


def test_shares_are_binned_to_10_points_and_counts_to_5():
    assert _share(1, 27) == 0.0 and _share(3, 27) == 0.1 and _share(2, 3) == 0.7 and _share(0, 0) is None
    assert _coarse(27) == 25 and _coarse(28) == 30 and _coarse(2) == 0
