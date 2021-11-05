import unittest


from ptzpicocam.camera import CameraAPI

from ptzpicocam.pico import calc_Pan_Com







class TestPico(unittest.TestCase):
    def test_Test(self):
        self.assertEqual(7, 7)  

    def test_Pan(self):
        dirTest,speedTest=calc_Pan_Com(32767)
        self.assertEqual(dirTest,CameraAPI.CameraAPI.PanDirection(1))
        self.assertEqual(speedTest,0)
  