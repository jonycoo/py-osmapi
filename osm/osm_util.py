import json
import math
from datetime import datetime
import dateutil.parser


class Element:
    def __init__(self, eid: int, version: int, changeset: int,
                 user: str, uid: int, created: str, visible: bool, tags: dict):
        """

        :param eid:
        :param tags:
        """
        self._id = eid
        self.tags = tags
        self.version = version
        self.changeset = changeset
        self.user = user
        self.uid = uid
        self.created = created
        self.visible = visible
        self.e_type = 'element'

    def __repr__(self):
        return json.dumps(self.__dict__, default=lambda o: o.__dict__)

    def __str__(self):
        return str(self.id)

    @property
    def id(self):
        return self._id

    @property
    def type(self):
        return self._type


class MicroElem:
    def __init__(self, eid, e_type, tags: dict = None):
        self.eid = eid
        self.e_type = e_type
        self.tags = tags

    def __str__(self):
        return self.e_type + str(self.eid)


class Node(Element):
    def __init__(self, eid: int, lat: float, lon: float, version: int, changeset: int,
                 user: str, uid: int, created: str, visible: bool, tags: dict):
        super().__init__(eid, version, changeset, user, uid, created, visible, tags)
        self.lat = lat
        self.lon = lon
        self.e_type = 'node'


class Way(Element):
    def __init__(self, eid: int, nodes: list, version: int, changeset: int,
                 user: str, uid: int, created: str, visible: bool, tags: dict):
        super().__init__(eid, version, changeset, user, uid, created, visible, tags)
        self.nodes = nodes
        self.e_type = 'way'


class Relation(Element):
    def __init__(self, eid: int, members: list, version: int, changeset: int,
                 user: str, uid: int, created: str, visible: bool, tags: dict):
        super().__init__(eid, version, changeset, user, uid, created, visible, tags)
        self.members = members
        self.e_type = 'relation'


class Comment:
    def __init__(self, text: str, uid: int, username: str, created: datetime, action: str = None):
        self.text = text
        self._id = uid
        self.user = username
        self.created = created
        self.action = action

    def __repr__(self):
        return json.dumps(self.__dict__)

    @property
    def id(self):
        return self._id


class Note:
    def __init__(self, nid: int, lat: float, lon: float, created: str, is_open: bool, comments: list):
        self._id = nid
        self.lat = lat
        self.lon = lon
        try:
            dateutil.parser.parse(created)
            self._created = created
        except ValueError:
            self._created = None
        # todo date_closed
        self.open = is_open
        self.comments = comments

    def __repr__(self):
        return json.dumps(self.__dict__, default=lambda o: o.__dict__)

    @property
    def created(self) -> datetime:
        if self._created:
            return dateutil.parser.parse(self._created)
        else:
            return None

    @property
    def id(self):
        return self._id

    @property
    def location(self):
        return self._lat, self._lon


class ChangeSet:
    def __init__(self, cid: int, username: str, uid: int, created: datetime, is_open: bool, bbox: tuple,
                 closed: datetime = None, tags: dict = None, comments: list = None):
        self._id = cid
        self.user = username
        self.uid = uid
        self.created = created
        self.open = is_open
        self.maxlon = bbox[0] or None
        self.maxlat = bbox[1] or None
        self.minlon = bbox[2] or None
        self.minlan = bbox[3] or None
        self.closed = closed
        self.tags = tags or {}
        self.comments = comments or []

    def __repr__(self):
        return json.dumps(self.__dict__, default=lambda o: o.__dict__)

    @property
    def id(self):
        return self._id

    @property
    def open_comment(self):
        try:
            return self.tags['comment']
        except KeyError:
            return None

    @property
    def bbox(self):
        return self.maxlon, self.maxlat, self.minlon, self.minlan


def create_bbox(lat: float, lon: float, rad: int):
    """
    creates a Geo Bounding box with lat, lon as center

    :param lat: latitude
    :param lon: longitude
    :param rad: radius in meters
    """

    EARTH_RAD = float(6378000)
    lat_d = (math.asin(float(rad) / (EARTH_RAD * math.cos(math.pi * lat / 180)))) * 180 / math.pi
    lon_d = (math.asin(float(rad) / EARTH_RAD)) * 180 / math.pi

    max_lat = lat + lat_d
    min_lat = lat - lat_d
    max_lon = lon + lon_d
    min_lon = lon - lon_d

    return min_lon, min_lat, max_lon, max_lat
