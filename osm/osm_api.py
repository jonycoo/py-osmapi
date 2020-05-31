import requests

from osm import a_osm_api
import logging
import os
from osm.osm_util import Element, Note, ChangeSet, Comment
from datetime import *

import gpxpy.gpx
from xml.etree import ElementTree as ElemTree
from http import HTTPStatus

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
        if data.status_code == HTTPStatus.OK:
            tree = ElemTree.fromstring(data.text)
            permissions = set()
            for item in tree.findall('permissions/permission'):
                permissions.add(item.get('name'))
            return permissions
        else:
            raise Exception(data.text)

    ''' changeset '''

    def create_changeset(self, changeset: ChangeSet) -> int:
        """
        PUT /api/0.6/changeset/create

        :param changeset: Dictionary containing additional tags

        :returns: changeset ID

        :raises ParseError:
            for HTTP 400 BAD REQUEST
        :raises MethodError:
            for HTTP 405 METHOD NOT ALLOWED
            only PUT allowed
        """
        data = requests.put(self.base_url + '/changeset/create', auth=(NAME, PASS))
        if data.status_code == HTTPStatus.OK:
            return int(data.text)
        elif data.status_code == HTTPStatus.BAD_REQUEST:
            raise ParseError(data.text)
        elif data.status_code == HTTPStatus.METHOD_NOT_ALLOWED:
            raise MethodError(data.text)
        else:
            raise Exception(data.text)

    def get_changeset(self, cid: int, discussion: bool = False) -> ChangeSet:
        """
        A Call to get a changeset optionally with discussion.
        no elements included

        GET /api/0.6/changeset/#id?include_discussion=
        exclude discussion by <empty> or omitting

        :param cid: changeset ID
        :param discussion: include changeset discussion?
        :returns: dictionary representation of the changeset
        :raises NoneFoundError:
            HTTP 404 NOT FOUND
            no changeset matching this ID
        """
        url = self.base_url + '/changeset/{}'.format(cid)
        if discussion:
            url += '?include_discussion=True'
        data = requests.get(url, auth=(NAME, PASS))
        if data.status_code == HTTPStatus.OK:
            return self.__changeset_parser(data.text)
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        else:
            raise Exception(data.text)

    def close_changeset(self, cid: int):
        """
        closes a changeset
        PUT /api/0.6/changeset/#id/close

        :raises NoneFoundError:
            HTTP 404 NOT FOUND
        :raises MethodError:
            HTTP 405 METHOD NOT ALLOWED
        :raises ConflictError:
            HTTP 409 CONFLICT
        """
        data = requests.get(self.base_url + '/changeset/close', auth=(NAME, PASS))
        if data.status_code == HTTPStatus.OK:
            return int(data.text)
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        elif data.status_code == HTTPStatus.BAD_REQUEST:
            raise ParseError(data.text)
        elif data.status_code == HTTPStatus.METHOD_NOT_ALLOWED:
            raise MethodError(data.text)
        else:
            raise Exception(data.text)

    def download_changeset(self, cid: int) -> ChangeSet:
        """
        GET /api/0.6/changeset/#id/download
        """
        raise NotImplementedError

    def __changeset_parser(self, data: str):
        tree = ElemTree.fromstring(data)
        tags = self.__kv_parser(tree.findall('changeset/tag'))
        cs_xml = tree.find('changeset')
        cs_prop = {}
        for key in cs_xml.keys():
            cs_prop[key] = cs_xml.get(key)

        com_xml = tree.findall('comment')
        comments = []
        for com in com_xml:
            cr_date = datetime.fromisoformat(com.get('date'))
            comments.append(Comment(com.find('text').text, com.get('uid'), com.get('user'), cr_date))
        try:
            bbox = cs_prop['max_lon'], cs_prop['max_lat'], cs_prop['min_lon'], cs_prop['min_lat']
        except KeyError:
            bbox = ()
        ch_set = ChangeSet(cs_prop['id'], cs_prop['user'], cs_prop['uid'], cs_prop['created_at'],
                           True, bbox, cs_prop['open'] or datetime.fromisoformat(cs_prop['closed_at']), tags)
        ch_set.comments = comments
        return ch_set

    def comm_changeset(self, cid: int, text: str) -> str:
        """
        Add a comment to a changeset. The changeset must be closed.
        POST /api/0.6/changeset/#id/comment
        text as "application/x-www-form-urlencoded" in body

        :raises NoneFoundError:
            HTTP 400 BAD REQUEST
            no textfield present
        :raises ConflictError:
            HTTP 409 CONFLICT
        """
        raise NotImplementedError

    def sub_changeset(self, cid: int) -> ChangeSet:
        """
        Subscribes the current authenticated user to changeset discussion
        POST /api/0.6/changeset/#id/subscribe

        :raises ConflictError:
            HTTP 409 CONFLICT
            already subscribed
        """
        data = requests.post(self.base_url + '/changeset/{}/subscribe'.format(cid), auth=(NAME, PASS))
        if data.status_code == HTTPStatus.OK:
            return self.__changeset_parser(data.text)
        elif data.status_code == HTTPStatus.CONFLICT:
            raise ConflictError(data.text)
        else:
            raise Exception(data.text)

    def unsub_changeset(self, cid: int) -> ChangeSet:
        """
        Unsubscribe the current authenticated user from changeset discussion
        POST /api/0.6/changeset/#id/subscribe

        :raises NoneFoundError:
            HTTP 400 NOT FOUND
            is not subscribed
        """
        data = requests.post(self.base_url + '/changeset/{}/unsubscribe'.format(cid), auth=(NAME, PASS))
        if data.status_code == HTTPStatus.OK:
            return self.__changeset_parser(data.text)
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        else:
            raise Exception(data.text)

    ''' Element '''

    def create_element(self, elem: Element, cid: int) -> int:
        """
        creates new element of specified type
        PUT /api/0.6/[node|way|relation]/create

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

        :returns: Element containing all available data.
        :raises NoneFoundError:
            HTTP 404 NOT FOUND
        :raises LockupError:
            HTTP 410 GONE
        """
        data = requests.get(self.base_url + '/{}/{}'.format(etype, eid), auth=(NAME, PASS))
        if data.status_code == HTTPStatus.OK:
            tree = ElemTree.fromstring(data.text)
            logger.debug(data.text)
            return self.__parse_elem(tree[0])
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        elif data.status_code == HTTPStatus.GONE:
            raise LookupError(data.text)

    def __parse_elem(self, elem: ElemTree.Element):
        eid = elem.get('id')
        etype = elem.tag
        version = elem.get('version')
        changeset = elem.get('changeset')
        cr_date = elem.get('timestamp')
        user = elem.get('user')
        uid = elem.get('uid')
        lat = elem.get('lat')
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

        elem = Element(eid, etype, self.__kv_parser(elem.findall('tag')), nodes, members)
        return elem

    def edit_element(self, elem: Element, cid: int) -> int:
        """
        PUT /api/0.6/[node|way|relation]/#id

        :returns: New version Number

        :raises NoneFoundError:
            HTTP 400 BAD REQUEST
                When there are errors parsing the XML -> ParseError
                When a changeset ID is missing
                When a node is outside the world
                When there are too many nodes for a way
                When the version of the provided element does not match the current database version of the element
        :raises MethodError:
            HTTP 404 NOT FOUND
                Element ID not found -> NoneFoundError
        :raises ConflictError:
            HTTP 409 CONFLICT
                When changeset already closed
                When changeset creator and element creator different
        :raises ParseError:
            HTTP 412 PRECONDITION FAILED
                When a way/relation has nodes that do not exist or are not visible
        """
        raise NotImplementedError

    def delete_element(self, elem: Element) -> int:
        """
        DELETE /api/0.6/[node|way|relation]/#id

        :returns: new version number

        :raises NoneFoundError:
            HTTP 400 BAD REQUEST
                    When there are errors parsing the XML -> ParseError
                    When a changeset ID is missing
                    When a node is outside the world
                    When there are too many nodes for a way
                    When the version of the provided element does not match the current database version of the element
        :raises MethodError:
            HTTP 404 NOT FOUND
                Element ID not found -> NoneFoundError
        :raises ConflictError:
            HTTP 409 CONFLICT
                When changeset already closed
                When changeset creator and element creator different
        :raises LookupError:
            HTTP 410 GONE
        :raises ParseError:
            HTTP 412 PRECONDITION FAILED
                When node is still part of way/relation
                When way is still part of relation
                When relation is still part of another relation
        """
        raise NotImplementedError

    def get_elements(self, etype: str, lst_eid: list) -> list:
        """
        multiple elements as specified in the list of eid
        GET /api/0.6/[nodes|ways|relations]?#parameters
        todo write doku
        """

        data = requests.get(self.base_url + '/{}s?{}s={}'.format(etype, etype, ','.join(map(str, lst_eid))),
                            auth=(NAME, PASS))
        if data.status_code == HTTPStatus.OK:
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
        if data.status_code == HTTPStatus.OK:
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
        :raise NoneFoundError:
        """
        data = requests.get(self.base_url + '/node/{}/ways'.format(eid),
                            auth=(NAME, PASS))
        if data.status_code == HTTPStatus.OK:
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

        :raise NoneFoundError:
        """
        data = requests.get(self.base_url + '/map?bbox={}'.format(','.join(map(str, bbox))), auth=(NAME, PASS))
        if data.status_code == HTTPStatus.OK:
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

    def get_bbox_gpx(self, bbox: tuple, page: int = 0) -> list:
        """
        returns 5000GPS trackpoints max increase page for any additional 5000
        GET /api/0.6/trackpoints?bbox=left,bottom,right,top&page=pageNumber

        :param bbox: (minlon, minlat, maxlon, maxlat)
        :param page: 5000 trackpoints are returned each page

        :returns: max 5000 trackpoints within bbox format GPX Version 1.0
        :rtype: tuple with lat, lon, time todo figger out what to return
        """
        data = requests.get(self.base_url + '/trackpoints?bbox={}'.format(','.join(map(str, bbox))), auth=(NAME, PASS))
        if data.status_code == HTTPStatus.OK:
            gpx = gpxpy.parse(data.text) 
            return gpx
        raise Exception(data.text)

    def upload_gpx(self, trace: str, description: str, tags: list,
                   public: bool = True, visibility: str = 'trackable') -> int:
        """
        uploads gpx trace
        POST /api/0.6/gpx/create

        :param trace: gpx trace file location
        :param description: gpx description
        :param tags: additional tags mappingtour, etc
        :param public: True for public tracks else False
        :param visibility: one of [private, public, trackable, identifiable]
            more https://wiki.openstreetmap.org/wiki/Visibility_of_GPS_traces
        :returns: gpx_id
        """
        raise NotImplementedError

    def update_gpx(self, trace: str, description: str, tags: list,
                   public: bool = True, visibility: str = 'trackable'):
        """
        updates gpx trace
        PUT /api/0.6/gpx/#id

        :param trace: gpx trace file location
        :param description: gpx description
        :param tags: additional tags mappingtour, etc
        :param public: True for public tracks else False
        :param visibility: one of [private, public, trackable, identifiable]
            more https://wiki.openstreetmap.org/wiki/Visibility_of_GPS_traces
        """
        raise NotImplementedError

    def delete_gpx(self, gpx_id: int):
        """
        DELETE /api/0.6/gpx/#id
        :param gpx_id: id identifying the gpx file on the server
        """
        raise NotImplementedError

    def get_gpx(self, gpx_id: int) -> str:
        """
        GET /api/0.6/gpx/#id/data
        :param gpx_id: id identifying the gpx file on the server
        :returns: string file location
        """
        raise NotImplementedError

    def get_own_gpx(self) -> list:
        """
        GET /api/0.6/user/gpx_files

        :returns: list of dictionary representing the metadata
        """
        raise NotImplementedError

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

    def get_notes_bbox(self, bbox: tuple, limit: int = 100, closed: int = 7) -> list:
        """
        GET /api/0.6/notes?bbox=left,bottom,right,top

        :param bbox: (lonmin, latmin, lonmax, latmax)
        :param limit: 0-1000
        :param closed: max days closed -1=all, 0=only_open
        :returns: list of Notes
        :raises ValueError: HTTP 400 BAD REQUEST
            When any of the limits are crossed
        """
        raise NotImplementedError

    def get_note(self, nid: int) -> Note:
        """
        GET /api/0.6/notes/#id

        :param nid: note id
        :return: the identified Note
        :raises NoneFoundError: HTTP 404 NOT FOUND no note with this id
        """
        raise NotImplementedError

    def create_note(self, text: str, lat: float, lon: float) -> int:
        """
        POST /api/0.6/notes?lat=<lat>&lon=<lon>&text=<ANote>

        :param text: Note Text
        :param lat: latitude
        :param lon: longitude
        :returns: Note ID
        :raises ValueError: No text field
        :raises MethodError: Only POST method
        """
        raise NotImplementedError

    def comment_note(self, nid: int, text: str) -> Note:
        """
        POST /api/0.6/notes/#id/comment?text=<ANoteComment>

        :param nid: Note ID
        :param text: Text
        :returns: the Note itself
        :raises ValueError: HTTP 400 BAD REQUEST No Textfield
        :raises NoneFoundError: HTTP 404 NOT FOUND
        :raises MethodError: HTTP 405 METHOD NOT ALLOWED
        :raises ConflictError: HTTP 409 CONFLICT closed Note
        """
        raise NotImplementedError

    def close_note(self, nid: int, text: str) -> str:
        """
        Close: POST /api/0.6/notes/#id/close?text=<Comment>

        :param nid: Note ID
        :param text: Closing comment
        :returns:
        :raises NoneFoundError: HTTP 404 NOT FOUND
        :raises MethodError: HTTP 405 METHOD NOT ALLOWED
        :raises ConflictError: HTTP 409 CONFLICT closed Note
        """
        raise NotImplementedError

    def reopen_note(self, nid: int, text: str):
        """
        POST /api/0.6/notes/#id/reopen?text=<ANoteComment>

        :param nid: Note ID
        :param text: Text
        :returns: the Note itself
        :raises NoneFoundError: HTTP 404 NOT FOUND
        :raises MethodError: HTTP 405 METHOD NOT ALLOWED
        :raises ConflictError: HTTP 409 CONFLICT closed Note
        :raises LookupError: HTTP 410 GONE deleted Note
        """
        raise NotImplementedError

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

    def __kv_parser(self, lst: list) -> dict:
        """

        :param lst: list of tags form <tag k="some" v="value"/>
        :return: dictionary of key value pairs
        """
        tags = {}
        for item in lst:
            tags[item.get('k')] = item.get('v')
        return tags
