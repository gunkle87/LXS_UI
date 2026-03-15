import unittest
from ui.model.geometry import (
    calculate_component_depth, 
    calculate_component_width, 
    get_lane_y_offset,
    validate_component_geometry,
    validate_lane_offset
)
from ui.model.primitive_definition import PrimitiveDefinition

class TestModelGeometry(unittest.TestCase):
    def test_width_is_always_one(self):
        self.assertEqual(calculate_component_width(), 1)
        
        prim = PrimitiveDefinition("test", "Combinational", 2, 1, "Test")
        self.assertEqual(prim.width, 1)

    def test_depth_calculation(self):
        # inputs, outputs, expected depth
        cases = [
            (0, 1, 1), # Input
            (1, 0, 1), # Output
            (1, 1, 1), # NOT
            (2, 1, 1), # AND/OR/XOR
            (3, 1, 2), # 3-input gate
            (4, 1, 2), # 4-input gate
            (5, 2, 3), # 5-input, 2-output
            (0, 0, 1), # Minimum depth is 1
        ]
        
        for inputs, outputs, expected in cases:
            with self.subTest(inputs=inputs, outputs=outputs):
                self.assertEqual(calculate_component_depth(inputs, outputs), expected)

    def test_lane_y_offsets(self):
        # Index 0 is cell 0, upper lane (0.25)
        self.assertEqual(get_lane_y_offset(0, 1, 1), 0.25)
        # Index 1 is cell 0, lower lane (0.75)
        self.assertEqual(get_lane_y_offset(1, 2, 1), 0.75)
        # Index 2 is cell 1, upper lane (1.25)
        self.assertEqual(get_lane_y_offset(2, 3, 2), 1.25)
        # Index 3 is cell 1, lower lane (1.75)
        self.assertEqual(get_lane_y_offset(3, 4, 2), 1.75)

    def test_validation_helpers(self):
        # Geometry rule validations
        self.assertTrue(validate_component_geometry(1, 1, 2, 1))
        self.assertFalse(validate_component_geometry(2, 1, 2, 1)) # Invalid width
        self.assertFalse(validate_component_geometry(1, 2, 2, 1)) # Invalid height

        # Lane offset validations
        self.assertTrue(validate_lane_offset(0.25))
        self.assertTrue(validate_lane_offset(0.75))
        self.assertTrue(validate_lane_offset(1.25))
        self.assertTrue(validate_lane_offset(5.75))
        
        # Invalid offsets
        self.assertFalse(validate_lane_offset(0.50)) # No centered lanes
        self.assertFalse(validate_lane_offset(0.00))
        self.assertFalse(validate_lane_offset(1.00))

if __name__ == '__main__':
    unittest.main()
