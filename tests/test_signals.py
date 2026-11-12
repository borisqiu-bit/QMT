import unittest
from signals import analyze

class SignalTests(unittest.TestCase):
    def test_short_data(self):
        self.assertEqual(analyze([{"close": 1, "volume": 1}])["signal"], "NO_DATA")

    def test_breakout(self):
        rows = [{"close": 100.0, "volume": 100} for _ in range(60)]
        rows.append({"close": 110.0, "volume": 200})
        self.assertEqual(analyze(rows)["signal"], "BREAKOUT_WATCH")

    def test_weakness(self):
        rows = [{"close": 100.0, "volume": 100} for _ in range(60)]
        rows.append({"close": 80.0, "volume": 100})
        self.assertEqual(analyze(rows)["signal"], "WEAKNESS")

    def test_bad_values(self):
        rows = [{"close": -1.0, "volume": 100} for _ in range(61)]
        self.assertEqual(analyze(rows)["signal"], "NO_DATA")

if __name__ == "__main__":
    unittest.main()
