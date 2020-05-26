import unittest
import osm


class MyTestCase(unittest.TestCase):
    def test_get_from_id(self):
        this_way = osm.get_elem('way', 34946775)
        print(this_way.tags())


if __name__ == '__main__':
    unittest.main()
