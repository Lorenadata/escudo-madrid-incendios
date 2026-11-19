"""Índice meteorológico de incendios de Fosberg (FFWI), calculado con la predicción horaria de AEMET.

Fórmula publicada (Fosberg, 1978): humedad de equilibrio del combustible a partir de temperatura y humedad relativa,
coeficiente de amortiguación y viento medio. Va de 0 a 100. Solo describe el tiempo: no conoce la vegetación ni la
lluvia acumulada, no es un producto de AEMET y no es una probabilidad de incendio.
"""

from __future__ import annotations

from math import sqrt

KMH_TO_MPH = 0.621371


def equilibrium_moisture(temp_f: float, rh_pct: float) -> float:
    """Humedad de equilibrio (%) con los tres tramos de humedad relativa de la fórmula original."""
    h = rh_pct
    if h < 10:
        return 0.03229 + 0.281073 * h - 0.000578 * h * temp_f
    if h <= 50:
        return 2.22749 + 0.160107 * h - 0.01478 * temp_f
    return 21.0606 + 0.005565 * h**2 - 0.00035 * h * temp_f - 0.483199 * h


def ffwi(temp_c: float | None, rh_pct: float | None, wind_kmh: float | None) -> float | None:
    """FFWI de una hora, de 0 a 100. Si falta cualquiera de las tres variables → `None`, sin estimarla."""
    if temp_c is None or rh_pct is None or wind_kmh is None:
        return None
    rh = max(0.0, min(100.0, rh_pct))
    m = max(0.0, min(30.0, equilibrium_moisture(temp_c * 9 / 5 + 32, rh))) / 30
    damping = 1 - 2 * m + 1.5 * m**2 - 0.5 * m**3
    wind_mph = max(0.0, wind_kmh) * KMH_TO_MPH
    return round(min(100.0, damping * sqrt(1 + wind_mph**2) / 0.3002), 1)
