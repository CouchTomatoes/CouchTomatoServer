import unittest

class GateCanFail(unittest.TestCase):
    def test_fails(self):
        self.assertEqual(1, 2)
