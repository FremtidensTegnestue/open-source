"""Explicit multiplicative conversions for the material-calculation pipeline.

normalize(value, unit, dimension) preserves the original number/unit and produces
one canonical unit for the requested dimension. Only enumerated spellings are
accepted; it does not infer dimensions or repair ambiguous units.

Conventions and constants:
* international inch = 0.0254 m and foot = 0.3048 m, exactly;
* avoirdupois pound = 0.45359237 kg, exactly;
* litre = 0.001 m3, metric tonne = 1000 kg, hour = 3600 s;
* Fahrenheit TEMPERATURE DIFFERENCE = 5/9 K (no absolute-temperature conversion);
* all 'Btu' aliases mean International Table Btu = 1055.05585262 J, exactly.
  Thermochemical Btu is different and is deliberately not an accepted alias.
* 'ton' means metric tonne in this Danish material-data interface. US short ton
  and imperial long ton are not accepted under that spelling.
* 1/%MC remains per one PERCENTAGE POINT of wood moisture content. Converting
  0.00256 1/%MC does not turn it into 0.0000256 or 0.256.

Primary conversion references:
https://www.nist.gov/pml/special-publication-811/nist-guide-si-appendix-b-conversion-factors/nist-guide-si-appendix-b8
https://www.nist.gov/pml/special-publication-811/nist-guide-si-footnotes

Source scientific meaning, observation conditions, and declared EPD reference
amounts remain the caller's responsibility. In particular, thermal resistivity
(m K/W) is NOT area thermal resistance (m2 K/W). No general EPD-denominator,
source_ambiguous, model-material equivalence or physical-value validation is done.
Negative finite values are preserved; the caller enforces physical constraints.
"""
from __future__ import annotations

import math
from numbers import Real

INCH_M = 0.0254
FOOT_M = 0.3048
POUND_KG = 0.45359237
BTU_IT_J = 1055.05585262
HOUR_S = 3600.0
FAHRENHEIT_DIFFERENCE_K = 5.0 / 9.0

# Values are (canonical unit, {exact accepted source spelling: SI factor}).
# These maps intentionally keep squared/cubed factors explicit and distinguish
# conductivity, capacity and resistance rather than rewriting unit strings.
_CONVERSIONS = {
    "mass": ("kg", {
        "kg": 1.0, "g": 0.001, "mg": 1e-6,
        "t": 1000.0, "ton": 1000.0, "tonne": 1000.0, "metric tonne": 1000.0,
        "lb": POUND_KG, "lbs": POUND_KG,
    }),
    "length": ("m", {
        "m": 1.0, "mm": 0.001, "cm": 0.01,
        "in": INCH_M, "inch": INCH_M, "ft": FOOT_M,
    }),
    "area": ("m2", {
        "m2": 1.0, "m²": 1.0, "m^2": 1.0,
        "mm2": 1e-6, "mm²": 1e-6, "mm^2": 1e-6,
        "cm2": 1e-4, "cm²": 1e-4, "cm^2": 1e-4,
        "ft2": FOOT_M ** 2, "ft²": FOOT_M ** 2, "ft^2": FOOT_M ** 2,
        "in2": INCH_M ** 2, "in²": INCH_M ** 2, "in^2": INCH_M ** 2,
    }),
    "volume": ("m3", {
        "m3": 1.0, "m³": 1.0, "m^3": 1.0,
        "mm3": 1e-9, "mm³": 1e-9, "mm^3": 1e-9,
        "cm3": 1e-6, "cm³": 1e-6, "cm^3": 1e-6,
        "dm3": 0.001, "dm³": 0.001, "dm^3": 0.001,
        "L": 0.001, "l": 0.001, "liter": 0.001, "litre": 0.001,
        "ft3": FOOT_M ** 3, "ft³": FOOT_M ** 3, "ft^3": FOOT_M ** 3,
        "in3": INCH_M ** 3, "in³": INCH_M ** 3, "in^3": INCH_M ** 3,
    }),
    "density": ("kg/m3", {
        "kg/m3": 1.0, "kg/m³": 1.0, "kg/m^3": 1.0,
        "g/cm3": 1000.0, "g/cm³": 1000.0, "g/cm^3": 1000.0,
        "kg/dm3": 1000.0, "kg/dm³": 1000.0, "kg/dm^3": 1000.0,
        "t/m3": 1000.0, "t/m³": 1000.0, "ton/m³": 1000.0,
        "lb/ft3": POUND_KG / FOOT_M ** 3,
        "lb/ft³": POUND_KG / FOOT_M ** 3,
        "lb/ft^3": POUND_KG / FOOT_M ** 3,
    }),
    "thermal_conductivity": ("W/(m K)", {
        "W/(m K)": 1.0, "W/m-K": 1.0, "W/(m*K)": 1.0, "W/(m·K)": 1.0,
        "Btu*in/(h*ft^2*degF)": BTU_IT_J * INCH_M / (HOUR_S * FOOT_M ** 2 * FAHRENHEIT_DIFFERENCE_K),
        "Btu_IT*in/(h*ft^2*degF)": BTU_IT_J * INCH_M / (HOUR_S * FOOT_M ** 2 * FAHRENHEIT_DIFFERENCE_K),
        "Btu/(h*ft*degF)": BTU_IT_J / (HOUR_S * FOOT_M * FAHRENHEIT_DIFFERENCE_K),
    }),
    "heat_capacity": ("J/(kg K)", {
        "J/(kg K)": 1.0, "J/kg-K": 1.0, "J/(kg*K)": 1.0,
        "kJ/(kg K)": 1000.0, "kJ/kg-K": 1000.0,
        "Btu/(lb*degF)": BTU_IT_J / (POUND_KG * FAHRENHEIT_DIFFERENCE_K),
        "Btu_IT/(lb*degF)": BTU_IT_J / (POUND_KG * FAHRENHEIT_DIFFERENCE_K),
    }),
    "thermal_resistance": ("m2 K/W", {
        "m2 K/W": 1.0, "m² K/W": 1.0, "m^2 K/W": 1.0,
        "m2-K/W": 1.0, "m²·K/W": 1.0, "(m2 K)/W": 1.0,
        "h*ft^2*degF/Btu": HOUR_S * FOOT_M ** 2 * FAHRENHEIT_DIFFERENCE_K / BTU_IT_J,
        "h*ft^2*degF/Btu_IT": HOUR_S * FOOT_M ** 2 * FAHRENHEIT_DIFFERENCE_K / BTU_IT_J,
    }),
    "dimensionless": ("1", {
        "1": 1.0, "dimensionless": 1.0, "%": 0.01,
    }),
    "moisture_coefficient": ("1/%MC", {
        "1/%MC": 1.0,
    }),
}


def normalize(value: float, unit: str, dimension: str) -> dict:
    """Return an explicit conversion record, or ValueError for an unsafe input.

    Unit matching is case sensitive and exact except for surrounding whitespace.
    Canonical values are floats. IEEE-754 overflow is rejected after conversion.
    All original input values are retained in the result for an audit trail.
    """
    if not isinstance(value, Real) or isinstance(value, bool):
        raise ValueError("value must be a finite real number; numeric strings and booleans are not accepted")
    try:
        number = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError("value must be a finite real number") from exc
    if not math.isfinite(number):
        raise ValueError("value must be a finite real number")
    if not isinstance(dimension, str) or dimension not in _CONVERSIONS:
        raise ValueError(f"unsupported dimension: {dimension!r}")
    if not isinstance(unit, str) or not unit.strip():
        raise ValueError("unit must be an explicit nonempty string")
    source_unit = unit.strip()
    canonical, factors = _CONVERSIONS[dimension]
    if source_unit not in factors:
        raise ValueError(f"unsupported or ambiguous unit {unit!r} for {dimension}")
    factor = factors[source_unit]
    normalized = number * factor
    if not math.isfinite(normalized):
        raise ValueError("unit conversion overflows the finite numeric range")
    conventions = []
    if "Btu" in source_unit:
        conventions.append("Btu means International Table Btu, exactly 1055.05585262 J; degF is a temperature difference of 5/9 K")
    if source_unit in ("t", "ton", "tonne", "metric tonne", "t/m3", "t/m³", "ton/m³"):
        conventions.append("ton/tonne/t means metric tonne, exactly 1000 kg")
    if dimension == "moisture_coefficient":
        conventions.append("per one percentage-point change in wood moisture content; coefficient numerical value unchanged")
    return {
        "value": normalized,
        "unit": canonical,
        "dimension": dimension,
        "original_value": value,
        "original_unit": unit,
        "factor": factor,
        "offset": 0.0,
        "conventions": conventions,
    }


def supported_units(dimension: str) -> tuple[str, ...]:
    """List exact accepted source spellings for agent discovery and diagnostics."""
    if dimension not in _CONVERSIONS:
        raise ValueError(f"unsupported dimension: {dimension!r}")
    return tuple(sorted(_CONVERSIONS[dimension][1]))
