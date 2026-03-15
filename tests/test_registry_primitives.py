import unittest
from ui.services.primitive_registry import PrimitiveRegistry
from ui.model.primitive_definition import PrimitiveDefinition

class TestPrimitiveRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = PrimitiveRegistry()

    def test_initial_categories_exist(self):
        categories = self.registry.get_categories()
        expected = ["Combinational", "Input/Output", "Sequential", "Memory", "ALUs", "MUXes"]
        for cat in expected:
            self.assertIn(cat, categories)

    def test_minimal_primitives_exist(self):
        # Input, Output, NOT, AND, OR, XOR, Clock, Probe
        expected = ["input", "output", "not", "and", "or", "xor", "clock", "probe"]
        for type_id in expected:
            prim = self.registry.get_primitive(type_id)
            self.assertIsNotNone(prim, f"Primitive {type_id} should be registered")

    def test_primitive_geometry_properties(self):
        prim = self.registry.get_primitive("and")
        self.assertEqual(prim.num_inputs, 2)
        self.assertEqual(prim.num_outputs, 1)
        self.assertEqual(prim.width, 1)
        self.assertEqual(prim.height, 1)

    def test_custom_registration(self):
        custom = PrimitiveDefinition(
            type_id="custom_mux",
            category="MUXes",
            num_inputs=3,
            num_outputs=1,
            display_name="Custom MUX"
        )
        self.registry.register(custom)
        
        prim = self.registry.get_primitive("custom_mux")
        self.assertIsNotNone(prim)
        self.assertEqual(prim.category, "MUXes")
        
        # Test geometry logic dynamically
        self.assertEqual(prim.width, 1)
        self.assertEqual(prim.height, 2) # ceil(3 / 2) = 2

    def test_duplicate_registration_fails(self):
        prim = PrimitiveDefinition(
            type_id="and",
            category="Combinational",
            num_inputs=2,
            num_outputs=1,
            display_name="Duplicate AND"
        )
        with self.assertRaises(ValueError):
            self.registry.register(prim)

if __name__ == '__main__':
    unittest.main()
