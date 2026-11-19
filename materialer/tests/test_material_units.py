"""Independent physical conversion cases and rejection of unsafe interpretation."""
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from material_units import normalize, supported_units


class MaterialUnitsTests(unittest.TestCase):
    def test_model_geometric_units_use_correct_power(self):
        self.assertEqual(normalize(50_000_000, 'mm3', 'volume')['value'], 0.05)
        self.assertEqual(normalize(500_000, 'mm2', 'area')['value'], 0.5)
        self.assertEqual(normalize(100, 'mm', 'length')['value'], 0.1)
        self.assertEqual(normalize(1000, 'cm3', 'volume')['value'], 0.001)
        self.assertEqual(normalize(2, 'litre', 'volume')['value'], 0.002)

    def test_density_imperial_reference_and_mass_chain(self):
        # Reference rounded independently from NIST SI conversion factors.
        result = normalize(1, 'lb/ft^3', 'density')
        self.assertAlmostEqual(result['value'], 16.01846337396014, places=12)
        self.assertEqual(result['unit'], 'kg/m3')
        self.assertAlmostEqual(normalize(30, 'lb/ft^3', 'density')['value'] * 0.05,
                               24.02769506094021, places=10)
        self.assertEqual(normalize(1.8, 'g/cm³', 'density')['value'], 1800.0)
        self.assertEqual(normalize(470, 'kg/m³', 'density')['value'], 470.0)

    def test_explicit_mass_conventions(self):
        self.assertEqual(normalize(2, 'ton', 'mass')['value'], 2000.0)
        self.assertTrue(normalize(2, 'ton', 'mass')['conventions'])
        self.assertEqual(normalize(1000, 'g', 'mass')['value'], 1.0)
        self.assertEqual(normalize(1, 'lb', 'mass')['value'], 0.45359237)

    def test_thermal_it_reference_factors(self):
        conductivity = normalize(1, 'Btu*in/(h*ft^2*degF)', 'thermal_conductivity')
        self.assertAlmostEqual(conductivity['value'], 0.1442279, places=7)
        self.assertTrue(conductivity['conventions'])
        capacity = normalize(1, 'Btu/(lb*degF)', 'heat_capacity')
        self.assertAlmostEqual(capacity['value'], 4186.8, places=8)
        self.assertEqual(normalize(1.6, 'kJ/(kg K)', 'heat_capacity')['value'], 1600.0)
        resistance = normalize(1, 'h*ft^2*degF/Btu', 'thermal_resistance')
        self.assertAlmostEqual(resistance['value'], 0.1761101838, places=9)
        self.assertEqual(normalize(2, 'm2-K/W', 'thermal_resistance')['value'], 2.0)

    def test_moisture_per_percentage_point_is_not_fraction(self):
        result = normalize(0.00256, '1/%MC', 'moisture_coefficient')
        self.assertEqual(result['value'], 0.00256)
        self.assertEqual(result['factor'], 1.0)
        # 1 m board, 4 percentage-point change: 10.24 mm, within source range.
        self.assertAlmostEqual(1.0 * result['value'] * 4.0, 0.01024)
        self.assertTrue(result['conventions'])
        self.assertEqual(normalize(50, '%', 'dimensionless')['value'], 0.5)

    def test_preserves_original_and_only_trims_outer_unit_whitespace(self):
        result = normalize(100, ' mm ', 'length')
        self.assertEqual(result['original_value'], 100)
        self.assertEqual(result['original_unit'], ' mm ')
        self.assertEqual(result['factor'], 0.001)
        self.assertEqual(result['offset'], 0.0)
        with self.assertRaises(ValueError):
            normalize(100, 'MM', 'length')

    def test_ambiguous_and_dimension_mismatch_fail(self):
        for unit, dimension in [(None, 'density'), ('', 'density'),
                                ('source_ambiguous', 'thermal_resistance'),
                                ('m K/W', 'thermal_resistance'),
                                ('kg/m²', 'density'), ('mm', 'volume'),
                                ('kg CO2-eq', 'mass'),
                                ('1/%MC', 'dimensionless'),
                                ('Btu_th/(lb*degF)', 'heat_capacity')]:
            with self.subTest(unit=unit, dimension=dimension), self.assertRaises(ValueError):
                normalize(1, unit, dimension)
        with self.assertRaises(ValueError):
            normalize(1, 'kg', 'unknown')

    def test_only_finite_real_values_and_finite_results(self):
        for value in [None, True, False, '12', math.nan, math.inf, -math.inf, complex(1, 0)]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize(value, 'kg', 'mass')
        with self.assertRaises(ValueError):
            normalize(1e308, 'ton', 'mass')
        with self.assertRaises(ValueError):
            normalize(10**1000, 'kg', 'mass')
        self.assertEqual(normalize(-2, 'kg', 'mass')['value'], -2)
        self.assertEqual(normalize(0, 'kg', 'mass')['value'], 0)

    def test_discovery_does_not_mutate_conversion_map(self):
        units = supported_units('volume')
        self.assertIsInstance(units, tuple)
        self.assertIn('mm³', units)
        with self.assertRaises(ValueError):
            supported_units('unknown')


if __name__ == '__main__':
    unittest.main()
