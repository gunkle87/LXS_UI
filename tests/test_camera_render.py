import unittest
from PySide6.QtCore import QPointF, QRectF
from ui.camera import Camera
from ui.model.geometry import GridBounds
from ui.model.platform_state import compute_platform_bounds
from ui.model.component_instance import ComponentInstance

class TestCamera(unittest.TestCase):
    def test_zoom_steps(self):
        cam = Camera()
        self.assertEqual(cam.zoom, 1.0)
        
        # Zoom in
        cam.zoom_in()
        self.assertEqual(cam.zoom, 1.25)
        
        # Zoom out
        cam.zoom_out()
        self.assertEqual(cam.zoom, 1.0)
        
    def test_pan(self):
        cam = Camera()
        self.assertEqual(cam.pan_x, 0.0)
        self.assertEqual(cam.pan_y, 0.0)
        
        cam.pan(100.0, -50.0)
        self.assertEqual(cam.pan_x, 100.0)
        self.assertEqual(cam.pan_y, -50.0)

    def test_coordinate_conversion(self):
        cam = Camera()
        # Zoom is 1.0, Pan is 0.0
        scene_pt = QPointF(10.0, 20.0)
        view_pt = cam.scene_to_view(scene_pt)
        self.assertEqual(view_pt, scene_pt)
        
        back_pt = cam.view_to_scene(view_pt)
        self.assertEqual(back_pt, scene_pt)
        
        # Test with zoom and pan
        cam.zoom_in() # 1.25
        cam.pan(50.0, 50.0)
        
        scene_pt2 = QPointF(100.0, 100.0)
        view_pt2 = cam.scene_to_view(scene_pt2)
        self.assertEqual(view_pt2.x(), 100.0 * 1.25 + 50.0)
        self.assertEqual(view_pt2.y(), 100.0 * 1.25 + 50.0)
        
        back_pt2 = cam.view_to_scene(view_pt2)
        self.assertEqual(back_pt2.x(), 100.0)
        self.assertEqual(back_pt2.y(), 100.0)

class TestPlatformBounds(unittest.TestCase):
    def test_empty_components(self):
        bounds = compute_platform_bounds({}, padding_cells=4)
        self.assertTrue(bounds.width > 0)
        self.assertTrue(bounds.height > 0)
        
    def test_with_components(self):
        c1 = ComponentInstance("c1", "test_prim", 0, 0)
        c1.bounds = GridBounds(x=0, y=0, width=5, height=5)
        
        c2 = ComponentInstance("c2", "test_prim", 10, 10)
        c2.bounds = GridBounds(x=10, y=10, width=5, height=5)
        
        components = {c1.id: c1, c2.id: c2}
        
        bounds = compute_platform_bounds(components, padding_cells=2)
        
        self.assertEqual(bounds.x, -2)
        self.assertEqual(bounds.y, -2)
        self.assertEqual(bounds.width, 15 + 4) # 15 + 2*2
        self.assertEqual(bounds.height, 15 + 4) # 15 + 2*2

if __name__ == '__main__':
    unittest.main()
