import unittest
import os
from pyosmapi import exceptions
import pyosmapi.osm_api as osmapi
import pyosmapi.osm_util


class MyTestCase(unittest.TestCase):
    osmo = osmapi.OsmApi()

    def auth(self):
        try:
            username = os.environ['OSM_USERNAME']
            password = os.environ['OSM_PASSWORD']
            return username, password
        except KeyError:
            exit()

    def test_get_api_versions(self):
        data = self.osmo.get_api_versions()
        print(data)

    def test_capability(self):
        data = self.osmo.get_api_capabilities()
        print(data)

    def test_permissions(self):
        data = self.osmo.get_permissions(self.auth())
        print(data)

    def test_cs_cre(self):
        data = self.osmo.open_changeset({'comment': 'test', 'created_by': 'osmate'}, self.auth())
        print(data)

    def test_cs_unsub(self):
        data = self.osmo.unsub_changeset(177967, self.auth())
        print(data)

    def test_cs_sub(self):
        data = self.osmo.sub_changeset(177967, self.auth())
        print(data)

    def test_cs_get(self):
        cs = self.osmo.get_changeset(177967)
        print(cs)

    def test_cs_get_by_params(self):
        cs = self.osmo.get_changesets(bbox=(13.428416654163087, 52.49863874116848, 13.446383345836914, 52.52816125883152))
        for s in cs:
            print(s)

    def test_cs_download(self):
        cs = self.osmo.download_changeset(177967)
        print(cs)

    def test_cs_upload(self):
        diff = '<osmChange version="0.6" generator="pyosm"> ' \
               '<create> ' \
               '<node id="-1" changeset="187558" lat="-33.9135123" lon="151.1173123" /> ' \
               '<node id="-2" changeset="187558" lat="-33.9233721" lon="151.1173321" /> ' \
               '<way id="-3" changeset="187558"> ' \
               '<nd ref="-1"/> <nd ref="-2"/> ' \
               '</way> ' \
               '</create> ' \
               '</osmChange>'
        cs = self.osmo.diff_upload(187558, diff, self.auth())
        print(cs)

    def test_cs_comment(self):
        cs = self.osmo.comm_changeset(177967, 'Hallo Welt', self.auth())
        print(cs)

    def test_get_node(self):
        node = self.osmo.get_element('node', 4314858041)
        print(node)

    def test_get_way(self):
        node = self.osmo.get_element('way', 201774)
        print(node.__repr__())

    def test_get_relation(self):
        rel = self.osmo.get_element('relation', 4304875773)
        print(rel.__repr__())

    def test_get_hist(self):
        node = self.osmo.history_version_element('node', 4314858041)
        print(node.__repr__())

    def test_get_full_elem(self):
        rel = self.osmo.get_full_element('way', 4305504687)
        for item in rel:
            print(item.__repr__)

    def test_get_elem_bbox_pos(self):
        # westlimit=9.3852744541; southlimit=49.1700528219; eastlimit=9.38678722; northlimit=49.1708595043
        print(pyosmapi.osm_util.create_bbox(52.5134, 13.4374, 1000))
        elems = self.osmo.get_element_bbox((13.428416654163087, 52.49863874116848, 13.446383345836914, 52.52816125883152))
        for item in elems:
            print(item.__repr__)

    def test_get_elem_bbox_neg(self):
        with self.assertRaises(exceptions.NoneFoundError):
            # westlimit=9.3852744541; southlimit=49.1700528219; eastlimit=9.38678722; northlimit=49.1708595043
            print(pyosmapi.osm_util.create_bbox(52.5134, 13.4374, 1000))
            elems = self.osmo.get_element_bbox((9.3849565809, 49.1700030402, 9.3867590254, 49.1707360702))
            for item in elems:
                print(item.__repr__)

    def test_get_gpx_bbox(self):
        # 46.7723/12.1855
        print(pyosmapi.osm_util.create_bbox(51.4564, -0.214097, 750))
        gpx = self.osmo.get_gpx_bbox(pyosmapi.osm_util.create_bbox(51.4564, -0.214097, 750), 0)
        print(gpx)

    def test_send_gpx(self):
        gpx = open('/home/marvin/Downloads/2020-05-31_15-23_Sun.gpx').read()
        tid = self.osmo.upload_gpx(gpx, 'test_trace.xml', 'test', {'test', 'osmate'}, self.auth())
        print(tid)

    def test_get_gpx(self):
        tid = self.osmo.get_gpx(1714, self.auth())
        print(tid)

    def test_meta_gpx(self):
        meta = self.osmo.get_meta_gpx(47, self.auth())
        print(meta)

#   only works with defined value
#    def test_delete_gpx(self):
#        self.osmo.delete_gpx()

    def test_get_own_gpx(self):
        list_gpx = self.osmo.get_own_gpx(self.auth())
        print(list_gpx)

    def test_get_notes_bbox(self):
        notes = self.osmo.get_notes_bbox((13.428416654163087, 52.49863874116848, 13.446383345836914, 52.52816125883152))
        print(notes[0])

    def test_get_notes_search(self):
        notes = self.osmo.search_note('abc')
        print(notes[0])

    def test_get_preferences(self):
        prefs = self.osmo.get_own_preferences(self.auth())
        print(prefs)

    def test_put_preferences(self):
        prefs = {'gps.trace.visibility': 'trackable', 'hallo': 'welt'}
        answ = self.osmo.update_own_preferences(prefs, self.auth())
        print(answ)

    def test_get_preference(self):
        prefs = self.osmo.get_own_preference('hello', self.auth())
        print(prefs)

    def test_set_preference(self):
        prefs = self.osmo.set_own_preference('hello', 'welt', self.auth())
        print(prefs)

    def test_delete_preference(self):
        prefs = self.osmo.delete_own_preference('hello', self.auth())
        print(prefs)

    def tests_get_note(self):
        note = self.osmo.get_note(22599)
        print(note)

    def test_close_note(self):
        data = self.osmo.close_note(22599, 'abc', self.auth())
        print(data)

    def test_edit_elem(self):
        node = self.osmo.get_element('node', 4314858041)
        data = self.osmo.edit_element(node, 178488, self.auth())
        print(data)

    def test_get_users(self):
        users = self.osmo.get_users([7634, 7122])
        print(users)


if __name__ == '__main__':
    unittest.main()
