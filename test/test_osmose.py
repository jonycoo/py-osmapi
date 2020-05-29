import unittest

import ee_osmose
import osmose


# noinspection SpellCheckingInspection
class OsmoseTest(unittest.TestCase):
    def test_iss_loc(self):
        issues = osmose.get_issues_loc(49.16949, 9.38447, 500)
        self.assertGreater(len(issues), 0)
        print(issues)

    def test_iss_loc_neg(self):
        with self.assertRaises(ee_osmose.NoneFoundError):
            osmose.get_issues_loc(0.0, 0.0, 0)

    def test_iss_user_pos(self):
        issues = osmose.get_issues_user('jonycoo')
        self.assertGreater(len(issues), 0)
        print(issues)

    def test_iss_user_neg(self):
        with self.assertRaises(ee_osmose.NoneFoundError):
            osmose.get_issues_user(None)


if __name__ == '__main__':
    unittest.main()
