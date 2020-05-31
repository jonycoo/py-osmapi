import unittest
import ee_osmose
import osm.osm_api as osmapi
import osm.osm_util


class MyTestCase(unittest.TestCase):
    osmo = osmapi.OsmApi()

    def test_permissions(self):
        data = self.osmo.get_permissions()
        print(data)

    def test_cs_sub(self):
        data = self.osmo.sub_changeset(3335)
        print(data)

    def test_cs_unsub(self):
        data = self.osmo.unsub_changeset(3335)
        print(data)

    def test_cs_get(self):
        cs = self.osmo.get_changeset(3335)
        print(cs)

    def test_get_node(self):
        node = self.osmo.get_element('node', 4314858041)
        print(node.__repr__())

    def test_get_way(self):
        node = self.osmo.get_element('way', 201774)
        print(node.__repr__())

    def test_get_relation(self):
        rel = self.osmo.get_element('relation', 4304875773)
        print(rel.__repr__())

    def test_get_mutiple_elem(self):
        rel = self.osmo.get_elements('way', [201774, 4305504687])
        for item in rel:
            print(item.__repr__)

    def test_get_elem_bbox_pos(self):
        # westlimit=9.3852744541; southlimit=49.1700528219; eastlimit=9.38678722; northlimit=49.1708595043
        print(osm.osm_util.create_bbox(52.5134, 13.4374, 1000))
        elems = self.osmo.get_element_bbox((13.428416654163087, 52.49863874116848, 13.446383345836914, 52.52816125883152))
        for item in elems:
            print(item.__repr__)

    def test_get_elem_bbox_neg(self):
        with self.assertRaises(ee_osmose.NoneFoundError):
            # westlimit=9.3852744541; southlimit=49.1700528219; eastlimit=9.38678722; northlimit=49.1708595043
            print(osm.osm_util.create_bbox(52.5134, 13.4374, 1000))
            elems = self.osmo.get_element_bbox((9.3849565809, 49.1700030402, 9.3867590254, 49.1707360702))
            for item in elems:
                print(item.__repr__)

    def test_get_gpx_bbox(self):
        # 46.7723/12.1855
        print(osm.osm_util.create_bbox(46.7723, 12.1855, 1000))
        gpx = self.osmo.get_bbox_gpx((12.176516654163086, 46.75918370114128, 12.194483345836913, 46.78541629885872), 0)


if __name__ == '__main__':
    unittest.main()
