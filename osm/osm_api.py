import requests
from http import HTTPStatus
import logging
import os
import dateutil.parser
import xml.etree.ElementTree as ElemTree
from osm.osm_util import *
from osm import a_osm_api
from ee_osmose import *


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    NAME = os.environ['OSM_USERNAME']
    PASS = os.environ['OSM_PASSWORD']
except KeyError:
    logger.exception('no "OSM_USERNAME" or "OSM_PASSWORD" in environment variables.', 'Exit program')
    exit()


class OsmApi(a_osm_api.OsmApi):
    base_url = 'https://master.apis.dev.openstreetmap.org/api/0.6'

    def get_permissions(self) -> set:
        """
        current permissions
        GET /api/0.6/permissions
        """
        data = requests.get(self.base_url + '/permissions', auth=(NAME, PASS))
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            permissions = set()
            for item in tree.findall('permissions/permission'):
                permissions.add(item.get('name'))
            return permissions
        raise Exception(data.text)

    ''' changeset '''

    def create_changeset(self, tags: dict) -> int:
        """
        PUT /api/0.6/changeset/create
        :returns: changeset ID todo
        """
        data = requests.put(self.base_url + '/changeset/create', auth=(NAME, PASS))
        if data.ok:
            return int(data.text)
        elif data.status_code == HTTPStatus.BAD_REQUEST:
            raise ParseError(data.text)
        raise Exception(data.text)

    def get_changeset(self, cid: int, discussion: bool = False) -> ChangeSet:
        """
        A Call to get a changeset optionally with discussion.
        no elements included

        GET /api/0.6/changeset/#id?include_discussion=
        exclude discussion by <empty> or omitting
        """
        url = self.base_url + '/changeset/{}'.format(cid)
        if discussion:
            url += '?include_discussion=True'
        data = requests.get(url, auth=(NAME, PASS))
        if data.ok:
            logger.debug(data.text)
            return self.__changeset_parser(data.text)
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        raise Exception(data.text)

    def close_changeset(self, cid: int):
        """
        closes a changeset
        PUT /api/0.6/changeset/#id/close
        """
        data = requests.get(self.base_url + '/changeset/{}/close'.format(cid), auth=(NAME, PASS))
        if data.ok:
            return None
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        elif data.status_code == HTTPStatus.CONFLICT:
            raise ConflictError(data.text)
        raise Exception(data.text)

    def download_changeset(self, cid: int) -> str:
        """
        GET /api/0.6/changeset/#id/download
        """
        data = requests.get(self.base_url + '/changeset/close', auth=(NAME, PASS))
        if data.ok:
            return data.text
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        raise Exception(data.text)

    def __changeset_parser(self, data: str):
        tree = ElemTree.fromstring(data)
        tags = self.__kv_parser(tree.findall('changeset/tag'))
        cs_xml = tree.find('changeset')
        cs_prop = {}
        for key in cs_xml.keys():
            cs_prop[key] = cs_xml.get(key)

        com_xml = cs_xml.findall('discussion/comment')
        comments = []
        for com in com_xml:
            comments.append(Comment(com.find('text').text, com.get('uid'), com.get('user'), com.get('date')))
        try:
            bbox = cs_prop['max_lon'], cs_prop['max_lat'], cs_prop['min_lon'], cs_prop['min_lat']
        except KeyError:
            bbox = ()
        ch_set = ChangeSet(cs_prop['id'], cs_prop['user'], cs_prop['uid'], cs_prop['created_at'],
                           True, bbox, cs_prop['open'] or datetime.fromisoformat(cs_prop['closed_at']), tags, comments)
        return ch_set

    def comm_changeset(self, cid: int, text: str) -> ChangeSet:
        """
        Add a comment to a changeset. The changeset must be closed.
        POST /api/0.6/changeset/#id/comment
        """
        data = requests.post(self.base_url + '/changeset/{}/comment'.format(str(cid)),
                             data={'text': text}, auth=(NAME, PASS))
        logger.debug(data.text)
        if data.ok:
            return self.__changeset_parser(data.text)
        elif data.status_code == HTTPStatus.BAD_REQUEST:
            raise ValueError(data.text)
        elif data.status_code == HTTPStatus.CONFLICT:
            raise ConflictError(data.text)

    def sub_changeset(self, cid: int) -> ChangeSet:
        """
        Subscribes the current authenticated user to changeset discussion
        POST /api/0.6/changeset/#id/subscribe
        """
        data = requests.post(self.base_url + '/changeset/{}/subscribe'.format(cid), auth=(NAME, PASS))
        if data.ok:
            return self.__changeset_parser(data.text)
        elif data.status_code == HTTPStatus.CONFLICT:
            raise ConflictError(data.text)
        raise Exception(data.text)

    def unsub_changeset(self, cid: int) -> ChangeSet:
        """
        Unsubscribe the current authenticated user from changeset discussion
        POST /api/0.6/changeset/#id/subscribe
        """
        data = requests.post(self.base_url + '/changeset/{}/unsubscribe'.format(cid), auth=(NAME, PASS))
        if data.ok:
            return self.__changeset_parser(data.text)
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        raise Exception(data.text)

    ''' Element '''

    def create_element(self, elem: Element, cid: int) -> int:
        """
        creates new element of specified type
        PUT /api/0.6/[node|way|relation]/create
        todo
        :returns: Element ID

        :raises NoneFoundError:
            HTTP 400 BAD REQUEST
                When there are errors parsing the XML -> ParseError
                When a changeset ID is missing (unfortunately the error messages are not consistent)
                When a node is outside the world
                When there are too many nodes for a way
        :raises MethodError:
            HTTP 405 METHOD NOT ALLOWED
        :raises ConflictError:
            HTTP 409 CONFLICT
                When changeset already closed
                When changeset creator and element creator different
        :raises ParseError:
            HTTP 412 PRECONDITION FAILED
                When a way/relation has nodes that do not exist or are not visible
        """
        raise NotImplementedError

    def get_element(self, etype: str, eid: int) -> Element:
        """
        GET /api/0.6/[node|way|relation]/#id
        """
        data = requests.get(self.base_url + '/{}/{}'.format(etype, eid), auth=(NAME, PASS))
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            logger.debug(data.text)
            return self.__parse_elem(tree[0])
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        elif data.status_code == HTTPStatus.GONE:
            raise LookupError(data.text)

    def __parse_elem(self, elem: ElemTree.Element):
        eid = elem.get('id')
        version = int(elem.get('version'))
        changeset = elem.get('changeset')
        cr_date = elem.get('timestamp')
        user = elem.get('user')
        uid = elem.get('uid')
        visible = bool(elem.get('visible'))
        lat = elem.get('lat')  # lan & lon only type node
        lon = elem.get('lon')

        nodes = []
        for node in elem.findall('nd'):
            nodes.append(node.get('ref'))

        members = []
        for member in elem.findall('member'):
            mem = {}
            for item in member.keys():
                mem[item] = member.get(item)
            members.append(mem)

        if elem.tag == 'node':
            return Node(eid, lat, lon, version, changeset, user, uid, cr_date, visible,
                        self.__kv_parser(elem.findall('tag')))
        elif elem.tag == 'way':
            return Way(eid, nodes, version, changeset, user, uid, cr_date, visible,
                       self.__kv_parser(elem.findall('tag')))
        elif elem.tag == 'relation':
            return Relation(eid, members, version, changeset, user, uid, cr_date, visible,
                            self.__kv_parser(elem.findall('tag')))
        return elem

    def __serial_elem(self, elem: Element) -> str:
        root = ElemTree.Element("osm")
        doc = ElemTree.Element('None')
        if isinstance(elem, Node):
            doc = ElemTree.SubElement(root, "node", {'id': elem.id,
                                      'lat': str(elem.lat), 'lon': str(elem.lon), 'version': str(elem.version),
                                      'changeset': str(elem.changeset), 'user': elem.user, 'uid': str(elem.uid),
                                      'visible': str(elem.visible), 'timestamp': elem.created})
        elif isinstance(elem, Way):
            doc = ElemTree.SubElement(root, "way", {'id': elem.id, 'version': str(elem.version),
                                      'changeset': str(elem.changeset), 'user': elem.user, 'uid': str(elem.uid),
                                                    'visible': str(elem.visible), 'timestamp': elem.created})
            for ref in elem.nodes:
                ElemTree.SubElement(doc, 'nd', {'ref': ref})
        elif isinstance(elem, Relation):
            doc = ElemTree.SubElement(root, "relation", {'id': elem.id, 'version': str(elem.version),
                                      'changeset': str(elem.changeset), 'user': elem.user, 'uid': str(elem.uid),
                                                    'visible': str(elem.visible), 'timestamp': elem.created})
            for member in elem.members:
                ElemTree.SubElement(doc, 'member', member)

        for key, value in elem.tags.items():
            ElemTree.SubElement(doc, 'tag', {'k': key, 'v': value})

        return ElemTree.tostring(root)

    def edit_element(self, elem: Element, cid: int) -> int:
        """
        PUT /api/0.6/[node|way|relation]/#id
        :returns: New version Number
        """
        elem.changeset = cid
        data = requests.put(self.base_url + '/{}/{}'.format(elem.e_type, elem.id),
                            data=self.__serial_elem(elem), auth=(NAME, PASS))
        if data.ok:
            int(data.text)
        elif data.status_code == HTTPStatus.BAD_REQUEST:
            raise ValueError(data.text)
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        elif data.status_code == HTTPStatus.CONFLICT:
            raise ConflictError(data.text)
        elif data.status_code == HTTPStatus.PRECONDITION_FAILED:
            raise ParseError(data.text)
        raise Exception(data.text)

    def delete_element(self, elem: Element, cid: int) -> int:
        """
        DELETE /api/0.6/[node|way|relation]/#id

        :returns: new version number
        """
        elem.changeset = cid
        data = requests.delete(self.base_url + '/{}/{}'.format(elem.e_type, elem.id),
                               data=self.__serial_elem(elem), auth=(NAME, PASS))
        if data.ok:
            int(data.text)
        elif data.status_code == HTTPStatus.BAD_REQUEST:
            raise ValueError(data.text)
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        elif data.status_code == HTTPStatus.CONFLICT:
            raise ConflictError(data.text)
        elif data.status_code == HTTPStatus.GONE:
            raise LookupError(data.text)
        elif data.status_code == HTTPStatus.PRECONDITION_FAILED:
            raise ParseError(data.text)
        raise Exception(data.text)

    def get_elements(self, etype: str, lst_eid: list) -> list:
        """
        GET /api/0.6/[nodes|ways|relations]?#parameters
        """
        data = requests.get(self.base_url + '/{}s?{}s={}'.format(etype, etype, ','.join(map(str, lst_eid))),
                            auth=(NAME, PASS))
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            logger.debug(data.text)
            elems = []
            for sub in tree:
                elems.append(self.__parse_elem(sub))
            return elems

        elif data.status_code == HTTPStatus.BAD_REQUEST:
            raise ParseError(data.text)
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        elif data.status_code == HTTPStatus.REQUEST_URI_TOO_LONG:
            raise MethodError(data.text)
        raise Exception(data.text)

    def get_relation_of_element(self, etype: str, eid: int) -> list:
        """
        GET /api/0.6/[node|way|relation]/#id/relations
        """
        data = requests.get(self.base_url + '/{}/{}/relations'.format(etype, eid),
                            auth=(NAME, PASS))
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            logger.debug(data.text)
            elems = []
            for sub in tree:
                elems.append(self.__parse_elem(sub))
            if not elems:
                raise NoneFoundError('no such element or no relations on this element')
            return elems
        raise Exception(data.text)

    def get_ways_of_node(self, eid: int) -> list:
        """
        GET /api/0.6/node/#id/ways
        """
        data = requests.get(self.base_url + '/node/{}/ways'.format(eid),
                            auth=(NAME, PASS))
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            logger.debug(data.text)
            elems = []
            for sub in tree:
                elems.append(self.__parse_elem(sub))
            if not elems:
                raise NoneFoundError('no such node or no ways on this element')
            return elems
        raise Exception(data.text)

    def get_element_bbox(self, bbox: tuple) -> list:
        """
        :returns: all Elements with minimum one Node within this BoundingBox max: 50.000 Elements
        GET /api/0.6/map?bbox=left,bottom,right,top

        """
        data = requests.get(self.base_url + '/map?bbox={}'.format(','.join(map(str, bbox))), auth=(NAME, PASS))
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            logger.debug(data.text)
            elems = []
            for sub in tree[1:]:
                elems.append(self.__parse_elem(sub))
            if not len(tree) > 1:
                raise NoneFoundError('no elements or over 50.000 elements')
            return elems
        raise Exception(data.text)

    ''' GPX '''

    def get_bbox_gpx(self, bbox: tuple, page: int = 0) -> str:
        """
        returns 5000GPS trackpoints max, increase page for any additional 5000
        GET /api/0.6/trackpoints?bbox=left,bottom,right,top&page=pageNumber
        """
        data = requests.get(self.base_url + '/trackpoints?bbox={}'.format(','.join(map(str, bbox))), auth=(NAME, PASS))
        if data.ok:
            return data.text
        raise Exception(data.text)

    def upload_gpx(self, trace: str, name: str, description: str, tags: set,
                   public: bool = True, visibility: str = 'trackable') -> int:
        """
        uploads gpx trace
        POST /api/0.6/gpx/create
        """
        content = {'description': description, 'tags': ','.join(tags), 'public': public, 'visibility': visibility}
        req_file = {'file': (name, trace)}
        data = requests.post(self.base_url + '/gpx/create', auth=(NAME, PASS), files=req_file, data=content)
        if data.ok:
            return int(data.text)
        raise Exception(data.text)

    def update_gpx(self, tid: int, trace: str, description: str, tags: list,
                   public: bool = True, visibility: str = 'trackable'):
        """
        updates gpx trace
        PUT /api/0.6/gpx/#id
        """
        content = {'description': description, 'tags': ','.join(tags), 'public': public, 'visibility': visibility}
        req_file = {'file': ('test-trace.gpx', trace)}
        data = requests.put(self.base_url + '/gpx/' + str(tid), auth=(NAME, PASS), files=req_file, data=content)
        if data.ok:
            logger.debug('updated')
        else:
            logger.debug('not updated')
            raise Exception(data.text)

    def delete_gpx(self, tid: int):
        """
        DELETE /api/0.6/gpx/#id
        """
        data = requests.delete(self.base_url + '/gpx/' + str(tid), auth=(NAME, PASS))
        if data.ok:
            logger.debug('deleted')
        else:
            logger.debug('not deleted')
            raise Exception(data.text)

    def get_gpx(self, tid: int) -> str:
        """
        GET /api/0.6/gpx/#id/data
        """
        data = requests.get(self.base_url + '/gpx/{}/data'.format(tid), auth=(NAME, PASS))
        if data.ok:
            return data.text
        raise Exception(data.text)

    def get_own_gpx(self) -> list:
        """
        GET /api/0.6/user/gpx_files
        """
        data = requests.get(self.base_url + '/user/gpx_files', auth=(NAME, PASS))
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            lst = []
            for item in tree.findall('gpx_file'):
                attrib = item.attrib
                attrib['timestamp'] = dateutil.parser.isoparse(attrib['timestamp'])
                for info in item:
                    attrib[info.tag] = info.text
                lst.append(attrib)
            return lst
        raise Exception(data.text)

    ''' user '''

    def get_user(self, uid: int) -> dict:
        """
        GET /api/0.6/user/#id
        :param uid: user id
        :returns: dictionary with user detail
        """
        raise NotImplementedError

    def get_users(self, uids: list) -> list:
        """
        GET /api/0.6/users?users=#id1,#id2,...,#idn

        :param uids: uid in a list
        :returns: list of dictionary with user detail
        """
        raise NotImplementedError

    def get_own_preferences(self) -> dict:
        """
        GET /api/0.6/user/preferences

        :returns: dictionary with preferences
        """
        raise NotImplementedError

    ''' notes '''

    def __parse_notes(self, tree: ElemTree.Element):
        lst = []
        for item in tree.findall('note'):
            lon = item.get('lon')
            lat = item.get('lat')
            nid = item.find('id').text
            created = dateutil.parser.parse(item.find('date_created').text)
            is_open = item.find('status').text
            if not is_open == 'closed':
                is_open = True
            else:
                is_open = False
            comments = []
            for comment in item.findall('comments/comment'):
                created = comment.find('date').text
                uid = comment.find('uid').text
                user = comment.find('user').text
                text = comment.find('text').text
                action = comment.find('action').text
                comments.append(Comment(text, uid, user, created, action))
            lst.append(Note(nid, lat, lon, created, is_open, comments))
        return lst

    def get_notes_bbox(self, bbox: tuple, limit: int = 100, closed: int = 7) -> list:
        """
        GET /api/0.6/notes?bbox=left,bottom,right,top
        """
        data = requests.get(self.base_url + '/notes?bbox=' + ','.join(map(str, bbox)), auth=(NAME, PASS))
        logger.debug(data.text)
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            return self.__parse_notes(tree)
        elif data.status_code == HTTPStatus.BAD_REQUEST:
            raise ValueError(data.text)
        raise Exception(data.text)

    def get_note(self, nid: int) -> Note:
        """
        GET /api/0.6/notes/#id
        """
        data = requests.get(self.base_url + '/notes/{}'.format(str(nid)), auth=(NAME, PASS))
        logger.debug(data.text)
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            return self.__parse_notes(tree)[0]
        elif data.status_code == HTTPStatus.BAD_REQUEST:
            raise ValueError(data.text)
        raise Exception(data.text)

    def create_note(self, text: str, lat: float, lon: float) -> Note:
        """
        POST /api/0.6/notes?lat=<lat>&lon=<lon>&text=<ANote>
        """
        data = requests.post(self.base_url + '/notes', params={'lat': lat, 'lon': lon, 'text': text}, auth=(NAME, PASS))
        logger.debug(data.text)
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            return self.__parse_notes(tree)[0]
        elif data.status_code == HTTPStatus.BAD_REQUEST:
            raise ValueError(data.text)
        raise Exception(data.text)

    def comment_note(self, nid: int, text: str) -> Note:
        """
        POST /api/0.6/notes/#id/comment?text=<ANoteComment>
        """
        data = requests.post(self.base_url + '/notes/{}/comment'.format(str(nid)),
                             params={'text': text}, auth=(NAME, PASS))
        logger.debug(data.text)
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            return self.__parse_notes(tree)[0]
        elif data.status_code == HTTPStatus.BAD_REQUEST:
            raise ValueError(data.text)
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        elif data.status_code == HTTPStatus.CONFLICT:
            raise ConflictError(data.text)
        raise Exception(data.text)

    def close_note(self, nid: int, text: str) -> Note:
        """
        POST /api/0.6/notes/#id/close?text=<Comment>
        """
        data = requests.post(self.base_url + '/notes/{}/close'.format(str(nid)),
                             params={'text': text}, auth=(NAME, PASS))
        logger.debug(data.text)
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            return self.__parse_notes(tree)[0]
        elif data.status_code == HTTPStatus.BAD_REQUEST:
            raise ValueError(data.text)
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        elif data.status_code == HTTPStatus.CONFLICT:
            raise ConflictError(data.text)
        raise Exception(data.text)

    def reopen_note(self, nid: int, text: str):
        """
        POST /api/0.6/notes/#id/reopen?text=<ANoteComment>
        """
        data = requests.post(self.base_url + '/notes/{}/close'.format(str(nid)),
                             params={'text': text}, auth=(NAME, PASS))
        logger.debug(data.text)
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            return self.__parse_notes(tree)[0]
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        elif data.status_code == HTTPStatus.CONFLICT:
            raise ConflictError(data.text)
        elif data.status_code == HTTPStatus.GONE:
            raise LookupError(data.text)
        raise Exception(data.text)

    def search_note(self, text: str, limit: int = 100, closed: int = 7, username: str = None, user: int = None,
                    start: datetime = None, end: datetime = None,
                    sort: str = 'updated_at', order: str = 'newest') -> list:
        """
        GET /api/0.6/notes/search?q=<SearchTerm>&limit=&closed=&username=&user=&from=&to=&sort=&order=

        :param text: <free text>
        :param limit: 0-1000
        :param closed: max days closed -1=all, 0=only_open
        :param username: username
        :param user: User ID
        :param start: from earliest date
        :param end: to newer date default: today
        :param sort: created_at or updated_at
        :param order: oldest or newest
        :returns: list of Notes
        :raises ValueError: HTTP 400 BAD REQUEST
            When any of the limits are crossed
        """
        raise NotImplementedError

    def rss_notes(self, bbox) -> str:
        """
        GET /api/0.6/notes/feed?bbox=left,bottom,right,top

        :param bbox: (lonmin, latmin, lonmax, latmax)
        :return:
        """
        raise NotImplementedError

    def __kv_parser(self, lst: list) -> dict:
        """
        :param lst: list of tags form <tag k="some" v="value"/>
        :return: dictionary of key value pairs
        """
        tags = {}
        for item in lst:
            tags[item.get('k')] = item.get('v')
        return tags

    def __kv_serial(self, tags: dict, parent: ElemTree.Element) -> list:
        lst = []
        for key, value in enumerate(tags):
            lst.append(ElemTree.SubElement(parent, 'tag', {'k': key, 'v': value}))
        return lst
