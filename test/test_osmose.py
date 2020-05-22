import unittest
import osmose


class OsmoseTest(unittest.TestCase):
    def test_iss_loc(self):
        issues = osmose.get_issues_loc(49.16949, 9.38447)
        print(str(issues))


if __name__ == '__main__':
    unittest.main()
