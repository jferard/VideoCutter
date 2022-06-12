import unittest
from pathlib import Path

FIXTURE_PATH = Path(__file__).parent / "fixture"
EXAMPLE_PATH = FIXTURE_PATH / "Distance_d_un_point_a_une_droite_dans_le_plan.theora.ogv.480p.webm"

from main import format_time, VideoCutter


class VideoCutterTestCase(unittest.TestCase):
    def test_extract(self):
        VideoCutter(EXAMPLE_PATH).extract_text()

    def test_assemble(self):
        VideoCutter(EXAMPLE_PATH).assemble()

    def test_fmt(self):
        self.assertEqual("00:20:34.445", format_time(1234.44564))
        self.assertEqual("12:40:48.463", format_time(45648.464))


if __name__ == '__main__':
    unittest.main()
