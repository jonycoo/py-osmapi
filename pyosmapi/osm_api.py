import requests
from http import HTTPStatus
import logging
import xml.etree.ElementTree as ElemTree
from pyosmapi.osm_util import *
from pyosmapi.exceptions import *

logger = logging.getLogger(__name__)


class OsmApi:
    base_url = 'https://master.apis.dev.openstreetmap.org/api/0.6'

    def __init__(self, live: bool = False):
        if live:
            self.base_url = 'https://api.openstreetmap.org/api/0.6'

    def get_api_versions(self):
        """
        :returns: supported API versions
        """
        data = requests.get('https://api.openstreetmap.org/api' + '/versions')
        if data.ok:
            return ElemTree.fromstring(data.text).find('api/version').text
        raise Exception(data.text)

    def get_api_capabilities(self) -> dict:
        """
        Max / Min values
        image blacklisting
        :returns:
        """
        # allowed by convenience with version
        data = requests.get(self.base_url + '/capabilities')
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            capabiliy = {}
            for item in tree.find('api').iter():
                capabiliy[item.tag] = item.attrib
            blacklist = []
            for item in tree.findall('policy/imagery/blacklist'):
                blacklist.append(item.get('regex'))
            capabiliy['image_blacklist'] = blacklist
            return capabiliy
        raise Exception(data.text)

    def get_permissions(self, auth) -> set:
        """
        current permissions
        Authorisation required else None
        :param auth: either OAuth1 object or tuple (username, password)
        :returns: set of all current permissions
        """
        data = requests.get(self.base_url + '/permissions', auth=auth)
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            permissions = set()
            for item in tree.findall('permissions/permission'):
                permissions.add(item.get('name'))
            return permissions if len(permissions) else None
        raise Exception(data.text)

    ############################################### CHANGESET #######################################################

    def open_changeset(self, tags: dict, auth) -> int:
        """
        opens a new changeset and returns its id
        Authorisation required

        :param tags: Dictionary containing additional tags
        :param auth: either OAuth1 object or tuple (username, password)
        :returns: changeset ID
        """
        root = ElemTree.Element('pyosmapi')
        cs = ElemTree.SubElement(root, 'changeset')
        try:
            self.__kv_serial(tags, cs)
        except AttributeError:
            pass
        xml = ElemTree.tostring(root)

        logger.debug(xml)
        data = requests.put(self.base_url + '/changeset/create', data=xml, auth=auth)
        if data.ok:
            return int(data.text)
        elif data.status_code == HTTPStatus.BAD_REQUEST:
            raise ParseError(data.text)
        raise Exception(data.text)

    def get_changeset(self, cid: int, discussion: bool = False) -> ChangeSet:
        """
        A Call to get a changeset optionally with discussion.
        no elements included

        :param cid: changeset ID
        :param discussion: include changeset discussion?
        :returns: dictionary representation of the changeset
        :raises NoneFoundError: no changeset matching this ID
        """
        url = self.base_url + '/changeset/{}'.format(cid)
        if discussion:
            url += '?include_discussion=True'
        data = requests.get(url)
        if data.ok:
            logger.debug(data.text)
            tree = ElemTree.fromstring(data.text).find('changeset')
            return self.__changeset_parser(tree)
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        raise Exception(data.text)

    def edit_changeset(self, changeset: ChangeSet, auth):
        """
        edits only changeset tags, only tags in this update remain in changeset

        :param changeset: ChangeSet object
        :param auth: either OAuth1 object or tuple (username, password)
        :raises NoneFoundError: no changeset of that ID
        :raises ConflictError: other user than creator trying to use changeset / or changeset already closed.
        """
        root = ElemTree.Element('pyosmapi')
        cs = ElemTree.SubElement(root, 'changeset')
        self.__kv_serial(changeset.tags, cs)
        xml = ElemTree.tostring(root)

        data = requests.put(self.base_url + '/changeset/{}'.format(changeset.id), data=xml, auth=auth)
        if data.ok:
            return None
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        elif data.status_code == HTTPStatus.CONFLICT:
            raise ConflictError(data.text)
        raise Exception(data.text)

    def close_changeset(self, cid: int, auth):
        """
        closes a changeset
        Authorisation required

        :param cid: changeset ID
        :param auth: either OAuth1 object or tuple (username, password)
        :raises NoneFoundError: no changeset of that ID
        :raises ConflictError: other user than creator trying to use changeset / or changeset already closed.
        """
        data = requests.get(self.base_url + '/changeset/{}/close'.format(cid), auth=auth)
        if data.ok:
            return None
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        elif data.status_code == HTTPStatus.CONFLICT:
            raise ConflictError(data.text)
        raise Exception(data.text)

    def download_changeset(self, cid: int) -> str:
        """
        downloads a OsmChange document

        :param cid: changeset ID
        :raises NoneFoundError: no changeset of that ID
        """
        data = requests.get(self.base_url + '/changeset/{}/download'.format(cid))
        if data.ok:
            return data.text
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        raise Exception(data.text)

    def get_changesets(self, bbox: tuple = None, user: str = '', time: datetime = None,
                       is_open: bool = False, is_closed: bool = False, changesets: list = None) -> list:
        """
        max 100 changesets matching all provided parameters

        :param bbox:(min_lon, min_lat, max_lon, max_lat)
        :param user: username or user_id
        :param time: Time format: Anything that this_ Ruby function will parse.
        :param is_open: xor is_closed
        :param is_closed: xor is_open
        :param changesets: changeset_ids as list
        :returns: found changesets in a list

        .. _this: https://ruby-doc.org/stdlib-2.7.2/libdoc/date/rdoc/DateTime.html#method-c-parse
        """
        params = {}
        if bbox:
            params['bbox'] = ','.join(map(str, bbox))
        if user:
            if user.isdigit():
                params['user'] = int(user)
            else:
                params['display_name'] = user
        if time:
            params['time'] = ','.join(map(str, time.isoformat()))
        if is_open ^ is_closed:
            if is_open:
                params['open'] = True
            else:
                params['closed'] = True
        if changesets:
            params['changesets'] = ','.join(map(str, changesets))

        data = requests.get(self.base_url + '/changesets', params=params)
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            logger.debug(data.text)
            cs = []
            for sub in tree.findall('changeset'):
                cs.append(self.__changeset_parser(sub))
            return cs
        elif data.status_code == HTTPStatus.BAD_REQUEST:
            raise ValueError(data.text)
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise ValueError(data.text)
        raise Exception(data.text)

    def diff_upload(self, cid: int, xml: str, auth) -> list:
        """
        uploads all changes at once, an error rolls back all (All or Nothing)

        - each element must carry a changeset and a version attribute, except when you are creating an element where the
          version is not required as the server sets that for you. The changeset must be the same as the
          changeset ID being uploaded to.
        - a <delete> block in the OsmChange document may have an if-unused attribute (the value of which is ignored).
          If this attribute is present, then the delete operation(s) in this block are conditional and will only be
          executed if the object to be deleted is not used by another object. Without the if-unused, such a situation
          would lead to an error, and the whole diff upload would fail. Setting the attribute will also cause
          deletions of already deleted objects to not generate an error.
        - OsmChange documents generally have user and uid attributes on each element.
          These are not required in the document uploaded to the API.

        Authorisation required

        :param cid: changeset id
        :type cid: int/str
        :param xml: OsmChange document as a String
        :param auth: either OAuth1 object or tuple (username, password)
        :returns: list with dict {type, old_id, new_id, new_version}
        """
        data = requests.post(self.base_url + '/changeset/{}/upload'.format(cid), data=xml, auth=auth)
        if data.ok:
            changes = []
            tree = ElemTree.fromstring(data.text)
            for item in tree.iter():
                item: ElemTree.Element
                line = {'type': item.tag, 'old_id': item.get('old_id')}
                if item.get('new_id'):
                    line['new_id'] = item.get('new_id')
                    line['new_version'] = item.get('new_version')
                changes.append(line)
            return changes
        elif data.status_code == HTTPStatus.BAD_REQUEST:
            raise ParseError(data.text)
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        elif data.status_code == HTTPStatus.CONFLICT:
            raise ConflictError(data.text)
        raise Exception(data.text)

    def __changeset_parser(self, tree: ElemTree):
        tags = self.__kv_parser(tree.findall('tag'))
        cs_prop = {}
        for key in tree.keys():
            cs_prop[key] = tree.get(key)

        com_xml = tree.findall('discussion/comment')
        comments = []
        for com in com_xml:
            comments.append(Comment(com.find('text').text, com.get('uid'), com.get('user'), com.get('date')))
        try:
            bbox = cs_prop['min_lon'], cs_prop['min_lat'], cs_prop['max_lon'], cs_prop['max_lat']
        except KeyError:
            bbox = (None, None, None, None)
        created = datetime.strptime(cs_prop['created_at'], "%Y-%m-%dT%H:%M:%SZ")
        if cs_prop['created_at'] is True:
            closed = None
        else:
            closed = datetime.strptime(cs_prop['closed_at'], "%Y-%m-%dT%H:%M:%SZ")
        ch_set = ChangeSet(cs_prop['id'], cs_prop['user'], cs_prop['uid'], created,
                           cs_prop['open'], bbox, closed, tags, comments)
        return ch_set

    def comm_changeset(self, cid: int, text: str, auth) -> ChangeSet:
        """
        Add a comment to a changeset. The changeset must be closed.
        Authorisation required

        :param cid: changeset ID
        :param text: text in new comment
        :param auth: either OAuth1 object or tuple (username, password)
        :returns: ChangeSet just commented, no comments
        :raises ValueError: no textfield present
        :raises ConflictError: deleted
        """
        data = requests.post(self.base_url + '/changeset/{}/comment'.format(str(cid)),
                             data={'text': text}, auth=auth)
        logger.debug(data.text)
        if data.ok:
            tree = ElemTree.fromstring(data.text).find('changeset')
            return self.__changeset_parser(tree)
        elif data.status_code == HTTPStatus.BAD_REQUEST:
            raise ValueError(data.text)
        elif data.status_code == HTTPStatus.CONFLICT:
            raise ConflictError(data.text)

    def sub_changeset(self, cid: int, auth) -> ChangeSet:
        """
        Subscribes the current authenticated user to changeset discussion
        Authorisation required

        :param cid: changeset ID
        :param auth: either OAuth1 object or tuple (username, password)
        :returns: ChangeSet just subscribed
        :raises ConflictError: already subscribed
        """
        data = requests.post(self.base_url + '/changeset/{}/subscribe'.format(cid), auth=auth)
        if data.ok:
            tree = ElemTree.fromstring(data.text).find('changeset')
            return self.__changeset_parser(tree)
        elif data.status_code == HTTPStatus.CONFLICT:
            raise ConflictError(data.text)
        raise Exception(data.text)

    def unsub_changeset(self, cid: int, auth) -> ChangeSet:
        """
        Unsubscribe the current authenticated user from changeset discussion
        Authorisation required

        :param cid: changeset ID
        :param auth: either OAuth1 object or tuple (username, password)
        :raises NoneFoundError: is not subscribed
        """
        data = requests.post(self.base_url + '/changeset/{}/unsubscribe'.format(cid), auth=auth)
        if data.ok:
            tree = ElemTree.fromstring(data.text).find('changeset')
            return self.__changeset_parser(tree)
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        raise Exception(data.text)

    ############################################## ELEMENT #########################################################

    def create_element(self, elem: Element, cid: int, auth) -> int:
        """
        creates new element of specified type
        Authorisation required

        :param elem: element to get created
        :param cid: open changeset ID
        :param auth: either OAuth1 object or tuple (username, password)
        :returns: Element ID
        :raises NoneFoundError:
            - When a changeset ID is missing (non consistent error message)
            - When a node is outside the world
            - When there are too many nodes for a way -> limit, see capabilities
        :raises ConflictError:
            - When changeset already closed
            - When changeset creator and element creator different
        :raises ParseError: When a way/relation has nodes that do not exist or are not visible
        """
        elem.changeset = cid
        xml = self.__serial_elem(elem, True)
        data = requests.get(self.base_url + '/{}/create'.format(elem.e_type), data=xml, auth=auth)
        if data.ok:
            return int(data.text)
        elif data.status_code == HTTPStatus.BAD_REQUEST:
            raise NoneFoundError(data.text)
        elif data.status_code == HTTPStatus.CONFLICT:
            raise ConflictError(data.text)
        elif data.status_code == HTTPStatus.PRECONDITION_FAILED:
            raise ParseError(data.text)

    def get_element(self, e_type: str, eid: int) -> Element:
        """
        returns only this element

        :param e_type: type of element ('node'/'way'/'relation')
        :param eid: element id
        :returns: requested Element of that Type
        :raises NoneFoundError: No Element with such id
        :raises LockupError: Deleted Element
        """
        data = requests.get(self.base_url + '/{}/{}'.format(e_type, eid))
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            logger.debug(data.text)
            return self.__parse_elem(tree[0])
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        elif data.status_code == HTTPStatus.GONE:
            raise LookupError(data.text)
        raise Exception(data.text)

    def __parse_elem(self, elem: ElemTree.Element):
        eid = elem.get('id')
        version = int(elem.get('version'))
        changeset = elem.get('changeset')
        cr_date = datetime.strptime(elem.get('timestamp'), "%Y-%m-%dT%H:%M:%SZ")
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

    def __serial_elem(self, elem: Element, is_create: bool = False) -> str:
        root = ElemTree.Element("pyosmapi")
        doc = ElemTree.Element('None')
        if not is_create:
            params = {'id': elem.id, 'version': str(elem.version), 'changeset': str(elem.changeset),
                      'user': elem.user, 'uid': str(elem.uid),
                      'visible': str(elem.visible), 'timestamp': elem.created}
        else:
            params = {'changeset': str(elem.changeset)}
        if isinstance(elem, Node):
            params['lat'] = str(elem.lat)
            params['lon'] = str(elem.lon)
            doc = ElemTree.SubElement(root, "node", params)
        elif isinstance(elem, Way):
            doc = ElemTree.SubElement(root, "way", params)
            for ref in elem.nodes:
                ElemTree.SubElement(doc, 'nd', {'ref': ref})
        elif isinstance(elem, Relation):
            doc = ElemTree.SubElement(root, "relation", params)
            for member in elem.members:
                ElemTree.SubElement(doc, 'member', member)
        self.__kv_serial(elem.tags, doc)

        return ElemTree.tostring(root).decode()

    def edit_element(self, elem: Element, cid: int, auth) -> int:
        """
        chage tags/position of element
        Authorisation required

        :param elem: changed element to get uploaded (Node/Way/Relation)
        :param cid: open changeset id
        :param auth: either OAuth1 object or tuple (username, password)
        :returns: New version number
        :raises ValueError:
            When a changeset ID is missing
            When a node is outside the world
            When there are too many nodes for a way -> limit, see capabilities
            When the version of the provided element does not match the current database version of the element
        :raises NoneFoundError: Element ID not found
        :raises ConflictError:
            When changeset already closed
            When changeset creator and element creator different
        :raises ParseError: When a way/relation has nodes that do not exist or are not visible
        """
        elem.changeset = cid
        data = requests.put(self.base_url + '/{}/{}'.format(elem.e_type, elem.id),
                            data=self.__serial_elem(elem), auth=auth)
        if data.ok:
            return int(data.text)
        elif data.status_code == HTTPStatus.BAD_REQUEST:
            raise ValueError(data.text)
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        elif data.status_code == HTTPStatus.CONFLICT:
            raise ConflictError(data.text)
        elif data.status_code == HTTPStatus.PRECONDITION_FAILED:
            raise ParseError(data.text)
        raise Exception(data.text)

    def delete_element(self, elem: Element, cid: int, auth) -> int:
        """
        deletes element
        Authorisation required

        :param elem: changed element to get deleted (Node/Way/Relation)
        :param cid: open changeset id
        :param auth: either OAuth1 object or tuple (username, password)
        :returns: new version number
        :raises ValueError:
            When a changeset ID is missing
            When a node is outside the world
            When there are too many nodes for a way
            When the version of the provided element does not match the current database version of the element
        :raises NonFoundError: Element ID not found
        :raises ConflictError:
            When changeset already closed
            When changeset creator and element creator different
        :raises LookupError: deleted
        :raises ParseError:
            When node is still part of way/relation
            When way is still part of relation
            When relation is still part of another relation
        """
        elem.changeset = cid
        data = requests.delete(self.base_url + '/{}/{}'.format(elem.e_type, elem.id),
                               data=self.__serial_elem(elem), auth=auth)
        if data.ok:
            return int(data.text)
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

    def history_element(self, e_type: str, eid: int) -> list:
        """
        complete history of an element

        :param e_type: type of element ('node'/'way'/'relation')
        :param eid: element id
        :returns: all versions of that element
        """
        data = requests.get(self.base_url + '/{}/{}/history'.format(e_type, eid))
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            logger.debug(data.text)
            elems = []
            for sub in tree:
                elems.append(self.__parse_elem(sub))
            return elems
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        raise Exception(data.text)

    def history_version_element(self, e_type: str, eid: int, version: int = 1) -> Element:
        """
        complete history of an element

        :param e_type: type of element ('node'/'way'/'relation')
        :param eid: element id
        :param version: defaults to 1
        :returns: all versions of that element
        """
        data = requests.get(self.base_url + '/{}/{}/{}'.format(e_type, eid, version))
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            logger.debug(data.text)
            return self.__parse_elem(tree[0])
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        raise Exception(data.text)

    def get_elements(self, e_type: str, lst_eid: list) -> list:
        """
        returns multiple elements of same e_type

        :returns: multiple elements as specified in the list of eid
        :param e_type: element type one of [node, way, relation]
        :param lst_eid: list of eid
        :raises ParseError: missing or wrong parameter
        :raises NoneFoundError: requested object never existed
        :raises MethodError: you might never try ro request more than ~700 elements at once
        """
        data = requests.get(self.base_url + '/{}s?{}s={}'.format(e_type, e_type, ','.join(map(str, lst_eid))))
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

    def get_relation_of_element(self, e_type: str, eid: int) -> list:
        """
        returns all relations containing this element

        :param e_type: type of element ('node'/'way'/'relation')
        :param eid: element id
        :returns: relations containing this element
        :raises NoneFoundError: no such element or no relations containing this element
        """
        data = requests.get(self.base_url + '/{}/{}/relations'.format(e_type, eid))
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
        use only on node elements

        :param eid: element ID
        :returns: ways directly using this node
        :raises NoneFoundError: no connected ways found
        """
        data = requests.get(self.base_url + '/node/{}/ways'.format(eid))
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
        all elements within bbox

        :param bbox: tuple (lon_min, lat_min, lon_max, lat_max)
        :returns: all Elements with minimum one Node within this BoundingBox
        :raise NoneFoundError: either none or over 50.000 elements are found
        """
        data = requests.get(self.base_url + '/map?bbox={}'.format(','.join(map(str, bbox))))
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

    def get_full_element(self, e_type: str, eid: int) -> list:
        """
        returns all elements directly referenced or referenced by 2nd grade

        :param e_type: type of element ('node'/'way'/'relation') referenced
        :param eid: element id
        :returns: elements referenced up to 2nd grade with element
        :raises NoneFoundError: eid not found / element deleted
        """
        data = requests.get(self.base_url + '/{}/{}/full'.format(e_type, eid))
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            logger.debug(data.text)
            elems = []
            for sub in tree:
                elems.append(self.__parse_elem(sub))
            return elems
        elif data.status_code == HTTPStatus.NOT_FOUND:
            raise NoneFoundError(data.text)
        elif data.status_code == HTTPStatus.GONE:
            raise NoneFoundError(data.text)
        raise Exception(data.text)

    ################################################## GPX ########################################################

    def get_gpx_bbox(self, bbox: tuple, page: int = 0) -> str:
        """
        returns max 5000GPS trackpoints as gpx string, increase page for any additional 5000

        :param bbox: (min_lon, min_lat, max_lon, max_lat)
        :param page: 5000 trackpoints are returned each page
        :returns: format GPX Version 1.0 string
        """
        data = requests.get(self.base_url + '/trackpoints', params={'bbox': ','.join(map(str, bbox)), 'page': page})
        if data.ok:
            return data.text
        raise Exception(data.text)

    def upload_gpx(self, trace: str, name: str, description: str, tags: set, auth,
                   visibility: str = 'trackable') -> int:
        """
        uploads gpx trace
        Authorisation required

        :param trace: gpx trace file string
        :param description: gpx description
        :param name: file name on pyosmapi
        :param tags: additional tags: eg.: mappingtour, etc
        :param auth: either OAuth1 object or tuple (username, password)
        :param visibility: one of [private, public, trackable, identifiable]
            more https://wiki.openstreetmap.org/wiki/Visibility_of_GPS_traces
        :returns: gpx_id
        """
        content = {'description': description, 'tags': ','.join(tags), 'visibility': visibility}
        req_file = {'file': (name, trace)}
        data = requests.post(self.base_url + '/gpx/create', auth=auth, files=req_file, data=content)
        if data.ok:
            return int(data.text)
        raise Exception(data.text)

    def update_gpx(self, tid: int, trace: str, description: str, tags: list, auth,
                   public: bool = True, visibility: str = 'trackable'):
        """
        updates gpx trace
        Authorisation required

        :param tid: uploaded trace id
        :param trace: gpx trace as string
        :param description: gpx description
        :param tags: additional tags mapping_tour, etc
        :param auth: either OAuth1 object or tuple (username, password)
        :param public: True for public tracks else False
        :param visibility: one of [private, public, trackable, identifiable]
            more https://wiki.openstreetmap.org/wiki/Visibility_of_GPS_traces
        """
        content = {'description': description, 'tags': ','.join(tags), 'public': public, 'visibility': visibility}
        req_file = {'file': ('test-trace.gpx', trace)}
        data = requests.put(self.base_url + '/gpx/' + str(tid), auth=auth, files=req_file, data=content)
        if data.ok:
            logger.debug('updated')
        else:
            logger.debug('not updated')
            raise Exception(data.text)

    def delete_gpx(self, tid: int, auth):
        """
        deletes own gpx indicated by ID
        Authorisation required

        :param tid: trace ID
        :param auth: either OAuth1 object or tuple (username, password)
        """
        data = requests.delete(self.base_url + '/gpx/' + str(tid), auth=auth)
        if data.ok:
            logger.debug('deleted')
            return None
        else:
            logger.debug('not deleted')
            raise Exception(data.text)

    def get_meta_gpx(self, tid: int, auth) -> dict:
        """
        returns meta data of identified gpx
        Authentication required

        :param tid: trace ID
        :param auth: either OAuth1 object or tuple (username, password)
        :returns: dict with metadata
        """
        data = requests.get(self.base_url + '/gpx/{}/details'.format(tid), auth=auth)
        if data.ok:
            logger.debug(data.text)
            tree = ElemTree.fromstring(data.text)
            ret = tree.find('gpx_file').attrib
            ret['timestamp'] = datetime.strptime(ret['timestamp'], "%Y-%m-%dT%H:%M:%SZ")
            ret['description'] = tree.find('gpx_file/description').text
            tags = []
            for tag in tree.findall('gpx_file/tag'):
                tags.append(tag.text)
            ret['tags'] = tags
            return ret
        raise Exception(data.text)

    def get_gpx(self, tid: int, auth) -> str:
        """identifying the gpx file
        downloads public or own private gpx file
        Authentication required

        :param tid: trace ID
        :param auth: either OAuth1 object or tuple (username, password)
        :returns: the full gpx file as a string
        """
        data = requests.get(self.base_url + '/gpx/{}/data'.format(tid), auth=auth)
        if data.ok:
            return data.text
        raise Exception(data.text)

    def get_own_gpx(self, auth) -> list:
        """
        meta data of all own gpx files
        Authorisation required

        :param auth: either OAuth1 object or tuple (username, password)
        :returns: list of dictionary representing the metadata
        """
        data = requests.get(self.base_url + '/user/gpx_files', auth=auth)
        if data.ok:
            return self.__parse_gpx_info(data.text)
        raise Exception(data.text)

    def __parse_gpx_info(self, xml):
        tree = ElemTree.fromstring(xml)
        lst = []
        for item in tree.findall('gpx_file'):
            attrib = item.attrib
            attrib['timestamp'] = datetime.strptime(attrib['timestamp'], "%Y-%m-%dT%H:%M:%SZ")
            for info in item:
                attrib[info.tag] = info.text
            lst.append(attrib)
        return lst

    ################################################# USER ######################################################

    def get_user(self, uid: int) -> dict:
        """
        user data and  statistic

        :param uid: user ID
        :returns: dictionary with user detail
        """
        data = requests.get(self.base_url + '/user/' + str(uid))
        if data.ok:
            return self.__parse_user(data.text)[0]
        raise Exception(data.text)

    def get_users(self, uids: list) -> list:
        """
        user data an statistics for multiple users

        :param uids: uid in a list
        :returns: list of dictionary with user detail
        """
        data = requests.get(self.base_url + '/users?users=' + ','.join(map(str, uids)))
        if data.ok:
            logger.debug(data.text)
            return self.__parse_user(data.text)
        raise Exception(data.text)

    def get_current_user(self, auth) -> dict:
        """
        own user data and statistics
        Authorisation required

        :param auth: either OAuth1 object or tuple (username, password)
        :returns: dictionary with user detail
        """
        data = requests.get(self.base_url + '/user/details', auth=auth)
        if data.ok:
            return self.__parse_user(data.text)[0]
        raise Exception(data.text)

    def __parse_user(self, xml: str) -> list:
        tree = ElemTree.fromstring(xml)
        users = []
        for user in tree.findall('user'):
            users.append({'uid': user.get('id'),
                          'name': user.get('display_name'),
                          'cr_date': user.get('account_created'),
                          'description': user.find('description').text,
                          'terms': bool(user.find('contributor-terms').get('agreed')),
                          'changeset_count': int(user.find('changesets').get('count')),
                          'traces_count': int(user.find('traces').get('count'))})
        return users

    def get_own_preferences(self, auth) -> dict:
        """
        returns all own user preferences
        Authorisation required

        :param auth: either OAuth1 object or tuple (username, password)
        :returns: dictionary with preferences
        """
        data = requests.get(self.base_url + '/user/preferences', auth=auth)
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            return self.__kv_parser(tree.findall('preferences/preference'))
        raise Exception(data.text)

    def update_own_preferences(self, pref: dict, auth):
        """
        updates all user preferences at once
        Authorisation required

        :param auth: either OAuth1 object or tuple (username, password)
        :param pref: dictionary with preferences
        """
        root = ElemTree.Element("pyosmapi")
        prefs = ElemTree.SubElement(root, 'preferences')
        for key, value in pref.items():
            ElemTree.SubElement(prefs, 'preference', {'k': key, 'v': value})
        data = ElemTree.tostring(root).decode()
        print(data)
        ret = requests.put(self.base_url + '/user/preferences', data=data, auth=auth)
        if ret.ok:
            return None
        raise Exception(ret.text)

    def get_own_preference(self, key: str, auth) -> str:
        """
        returns the value of a single preference
        Authorisation required

        GET /api/0.6/user/preferences/<your_key>

        :param auth: either OAuth1 object or tuple (username, password)
        :param key: key of preference
        :returns: value
        """
        data = requests.get(self.base_url + '/user/preferences/{}'.format(key), auth=auth)
        if data.ok:
            return data.text
        raise Exception(data.text)

    def set_own_preference(self, key: str, value: str, auth):
        """
        updates the value of a single preference
        Authorisation required

        :param key: key of preference
        :param value: new value
        :param auth: either OAuth1 object or tuple (username, password)
        """
        data = requests.put(self.base_url + '/user/preferences/{}'.format(key), data=value, auth=auth)
        if data.ok:
            return None
        raise Exception(data.text)

    def delete_own_preference(self, key: str, auth):
        """
        deletes a single preference
        Authorisation required

        :param key: key of preference
        :param auth: either OAuth1 object or tuple (username, password)
        """
        data = requests.delete(self.base_url + '/user/preferences/{}'.format(key), auth=auth)
        if data.ok:
            return None
        raise Exception(data.text)

    ################################################# NOTE ######################################################

    def __parse_notes(self, tree: ElemTree.Element):
        lst = []
        for item in tree.findall('note'):
            lon = item.get('lon')
            lat = item.get('lat')
            nid = item.find('id').text
            main_created = datetime.strptime(item.find('date_created').text, "%Y-%m-%d %H:%M:%S UTC")
            is_open = item.find('status').text
            if not is_open == 'closed':
                is_open = True
            else:
                is_open = False
                datetime.strptime(item.find('date_closed').text, "%Y-%m-%d %H:%M:%S UTC")

            comments = []
            for comment in item.findall('comments/comment'):
                created = datetime.strptime(comment.find('date').text, "%Y-%m-%d %H:%M:%S UTC")
                uid = comment.find('uid').text
                user = comment.find('user').text
                text = comment.find('text').text
                action = comment.find('action').text
                comments.append(Comment(text, uid, user, created, action))
            lst.append(Note(nid, lat, lon, main_created, is_open, comments))
        return lst

    def get_notes_bbox(self, bbox: tuple, limit: int = 100, closed: int = 7) -> list:
        """
        searches for all notes within the boundaries of bbox

        :param bbox: (lon_min, lat_min, lon_max, lat_max)
        :param limit: 0-1000
        :param closed: max days closed -1=all, 0=only_open
        :returns: list of Notes
        :raises ValueError: When any of the limits are crossed
        """
        data = requests.get(self.base_url + '/notes', params={'bbox': ','.join(map(str, bbox)),
                                                              'limit': limit, 'closed': closed})
        logger.debug(data.text)
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            return self.__parse_notes(tree)
        elif data.status_code == HTTPStatus.BAD_REQUEST:
            raise ValueError(data.text)
        raise Exception(data.text)

    def get_note(self, nid: int) -> Note:
        """
        a note with all comments

        :param nid: note id
        :return: the identified Note
        :raises NoneFoundError: note ID not found
        """
        data = requests.get(self.base_url + '/notes/{}'.format(str(nid)))
        logger.debug(data.text)
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            return self.__parse_notes(tree)[0]
        elif data.status_code == HTTPStatus.BAD_REQUEST:
            raise ValueError(data.text)
        raise Exception(data.text)

    def create_note(self, text: str, lat: float, lon: float, auth) -> Note:
        """
        creates anonymous or user made notes depending if auth is provided
        Authorisation optional

        :param text: Note Text
        :param lat: latitude
        :param lon: longitude
        :param auth: either OAuth1 object or tuple (username, password)
        :returns: note ID
        :raises ValueError: No text field
        """
        data = requests.post(self.base_url + '/notes', params={'lat': lat, 'lon': lon, 'text': text}, auth=auth)
        logger.debug(data.text)
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            return self.__parse_notes(tree)[0]
        elif data.status_code == HTTPStatus.BAD_REQUEST:
            raise ValueError(data.text)
        raise Exception(data.text)

    def comment_note(self, nid: int, text: str, auth) -> Note:
        """
        adds a comment to the note
        Authorisation required

        :param nid: note ID
        :param text: Text
        :param auth: either OAuth1 object or tuple (username, password)
        :returns: the Note itself
        :raises ValueError: no Textfield
        :raises NoneFoundError: note ID not found
        :raises ConflictError: already closed Note
        """
        data = requests.post(self.base_url + '/notes/{}/comment'.format(str(nid)),
                             params={'text': text}, auth=auth)
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

    def close_note(self, nid: int, text: str, auth) -> Note:
        """
        closes a note, no comments can be added to a closed note
        Authorisation required

        :param nid: note ID
        :param text: Closing comment
        :param auth: either OAuth1 object or tuple (username, password)
        :returns: the Note itself
        :raises NoneFoundError: note ID not found
        :raises ConflictError: already closed Note
        """
        data = requests.post(self.base_url + '/notes/{}/close'.format(str(nid)),
                             params={'text': text}, auth=auth)
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

    def reopen_note(self, nid: int, text: str, auth):
        """
        reopens a note, open for more comments
        Authorisation required

        :param nid: Note ID
        :param text: Text
        :param auth: either OAuth1 object or tuple (username, password)
        :returns: the Note itself
        :raises NoneFoundError: note ID not found
        :raises ConflictError: already closed Note
        :raises LookupError: deleted Note
        """
        data = requests.post(self.base_url + '/notes/{}/close'.format(str(nid)),
                             params={'text': text}, auth=auth)
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

    def search_note(self, text: str, limit: int = 100, closed: int = 7, user: str = None,
                    start: datetime = None, end: datetime = None,
                    sort: str = 'updated_at', order: str = 'newest') -> list:
        """
        searches for notes complying all parameters
        Authorisation required

        :param text: <free text>
        :param limit: 0-1000 max amount notes returned
        :param closed: max days closed -1=all, 0=only_open
        :param user: User ID or Username
        :param start: from earliest date
        :param end: to newer date default: today
        :param sort: created_at or updated_at
        :param order: oldest or newest
        :returns: list of Notes
        :raises ValueError: When any of the limits are crossed
        """
        params = {'q': text, 'limit': limit, 'closed': closed, 'sort': sort, 'order': order}
        if user:
            if type(user) == int or (type(user) == str and user.isdigit()):
                params['user'] = int(user)
            else:
                params['username'] = user
        if start:
            params['from'] = start.isoformat()
        if end:
            params['to'] = end.isoformat()

        data = requests.get(self.base_url + '/notes/search', params=params)
        if data.ok:
            tree = ElemTree.fromstring(data.text)
            return self.__parse_notes(tree)
        elif data.status_code == HTTPStatus.BAD_REQUEST:
            raise ValueError(data.text)

    def rss_notes(self, bbox) -> str:
        """
        gets a notes RSS feed of the area

        :param bbox: (lon_min, lat_min, lon_max, lat_max)
        :return: xml RSS feed
        """
        params = {'bbox': ','.join(map(str, bbox))}
        data = requests.get(self.base_url + '/notes/feed', params=params)
        if data.ok:
            return data.text
        raise Exception(data.text)

    def __kv_parser(self, lst: list) -> dict:
        """
        :param lst: list of tags form <tag k="some" v="value"/>
        :return: dictionary of key value pairs
        """
        tags = {}
        for item in lst:
            tags[item.get('k')] = item.get('v')
        return tags

    def __kv_serial(self, tags: dict, parent: ElemTree.Element):
        for key, value in tags.items():
            ElemTree.SubElement(parent, 'tag', {'k': key, 'v': value})
