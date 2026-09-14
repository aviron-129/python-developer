import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import unittest
from services import ServiceLogic

class TestService14(unittest.TestCase):
    def test_execution(self):
        res = ServiceLogic.process_task()
        self.assertEqual(res["result"], "success")

if __name__ == "__main__":
    unittest.main()
