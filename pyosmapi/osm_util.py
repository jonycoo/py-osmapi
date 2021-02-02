import json
import math
from datetime import datetime

OSM_URL = 'https://master.apis.dev.openstreetmap.org'


class Element:
    def __init__(self, eid: int, version: int, changeset: int,
                 user: str, uid: int, created: datetime, visible: bool, tags: dict):
        self._id = eid
        self.tags = tags or {}
        self.version = version
        self.changeset = changeset
        self.user = user
        self.uid = uid
        self.created = created
        self.visible = visible
        self.e_type = 'element'

    def __repr__(self):
        return json.dumps(self.__dict__, default=lambda o: _default(o))

    def __str__(self):

        str_tags = ''
        for attr, val in self.tags.items():
            str_tags += f"\n\t{attr} -- {val}"

        return f"type:{self.type}\nid:{self.id}\ntags:{str_tags}\nversion: {self.version}\n" \
               f"created: {self.created}\nvisible: {self.visible}" \
               f"\nchangeset:\n\tchangeset_id: {self.changeset}\n\tuser: {self.user}\n\tuser_id: {self.uid}\n"

    @property
    def id(self):
        return self._id

    @property
    def type(self):
        return self.e_type


class Node(Element):
    def __init__(self, eid: int, lat: float, lon: float, version: int, changeset: int,
                 user: str, uid: int, created: datetime, visible: bool, tags: dict):
        super().__init__(eid, version, changeset, user, uid, created, visible, tags)
        self.lat = lat
        self.lon = lon
        self.e_type = 'node'

    def __str__(self):
        return super(Node, self).__str__() + f"location:\n\tlatitude: {self.lat}\n\tlongitude: {self.lon}"


class Way(Element):
    def __init__(self, eid: int, nodes: list, version: int, changeset: int,
                 user: str, uid: int, created: datetime, visible: bool, tags: dict):
        super().__init__(eid, version, changeset, user, uid, created, visible, tags)
        self.nodes = nodes
        self.e_type = 'way'

    def __str__(self):
        return super(Way, self).__str__() + f"nodes: \n\t{self.nodes}"


class Relation(Element):
    def __init__(self, eid: int, members: list, version: int, changeset: int,
                 user: str, uid: int, created: datetime, visible: bool, tags: dict):
        super().__init__(eid, version, changeset, user, uid, created, visible, tags)
        self.members = members
        self.e_type = 'relation'

    def __str__(self):
        return super(Relation, self).__str__() + f"nodes: \n\t{self.members}"


class Comment:
    def __init__(self, text: str, uid: int, username: str, created: datetime, action: str = None):
        self.text = text
        self._id = uid
        self.user = username
        self.created = created
        self.action = action

    def __repr__(self):
        return json.dumps(self.__dict__)

    def __str__(self):
        return f"\n\tid: {self.id}\n\tusername: {self.user}\n\t" \
               f"text: \"{self.text}\"\n\taction: {self.action}\n\tcreated: {self.created}"

    @property
    def id(self):
        return self._id


class Note:
    def __init__(self, nid: int, lat: float, lon: float, created: datetime, is_open: bool,
                 comments: list, closed: datetime = None):
        self._id = nid
        self.lat = lat
        self.lon = lon
        self.open = is_open
        self.comments = comments
        self.created = created
        self.closed = closed

    def __repr__(self):
        return json.dumps(self.__dict__, default=lambda o: _default(o))

    def __str__(self):
        com_str = ''
        for com in self.comments:
            com_str += f'{com}'
        return f"id: {self.id}\nlocation:\n\tlatitude: {self.lat}\n\tlongitude: {self.lon}\nopen: {self.open}\n" \
               f"created: {self.created}{f'closed: {self.closed}' if not self.open else ''}\ncomments:{com_str}"

    @property
    def id(self):
        return self._id

    @property
    def location(self):
        return self.lat, self.lon


class Trace:
    def __init__(self, tid: int, gpx: str, filename: str, username: str, created: datetime,
                 desc: str = None, tags: set = None, visibility: str = 'trackable'):
        self._id = tid
        self.gpx = gpx
        self.name = filename
        self.username = username
        self.created = created
        self.desc = desc or 'no Description'
        self.tags = tags or []
        self.visibility = visibility

    def __repr__(self):
        return json.dumps(self.__dict__)

    def __str__(self):
        return f"id: {self.id}\nfilename: {self.name}\nDescription: {self.desc}\ntags: {self.tags}\n" \
               f"date: {self.created}\nvisible: {self.visibility}\nuploader: {self.username}"

    @property
    def id(self):
        return self._id

    @staticmethod
    def url(osm_user, tid):
        return OSM_URL + '/user/' + osm_user + '/traces/' + tid


class ChangeSet:
    def __init__(self, cid: int, username: str, uid: int, created: datetime, is_open: bool, bbox: tuple,
                 closed: datetime = None, tags: dict = None, comments: list = None):
        """
        :param bbox (min_lon, min_lat, max_lon, max_lat)
        """
        self._id = cid
        self.user = username
        self.uid = uid
        self.created = created
        self.open = is_open
        self.min_lon = bbox[0] or None
        self.min_lat = bbox[1] or None
        self.max_lon = bbox[2] or None
        self.max_lat = bbox[3] or None
        self.closed = closed
        self.tags = tags or {}
        self.comments = comments or []

    def __repr__(self):
        return json.dumps(self.__dict__, default=lambda o: _default(o))

    def __str__(self):
        com_str = ''
        for com in self.comments:
            com_str += f'{com}'
        tag_str = ''
        for tag, val in self.tags.items():
            tag_str += f'\n\t{tag}: {val}'
        return f"id: {self.id}\ncreator: {self.user}\ncreator_id: {self.uid}\ncreator_date: {self.created}\n" \
               f"open: {self.open}\nbbox: {(self.min_lat, self.min_lon, self.max_lat, self.max_lon)}\n" \
               f"closed: {self.closed}\ntags: {tag_str}\ncomments: {com_str}"

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
        return self.min_lon, self.min_lat, self.max_lon, self.max_lat


EARTH_RAD = float(6378000)


def create_bbox(lat: float, lon: float, rad: int):
    """
    creates a Geo Bounding box with lat, lon as center

    :param lat: latitude
    :param lon: longitude
    :param rad: radius in meters
    """

    lat_d = (math.asin(float(rad) / (EARTH_RAD * math.cos(math.pi * lat / 180)))) * 180 / math.pi
    lon_d = (math.asin(float(rad) / EARTH_RAD)) * 180 / math.pi

    dec = 8

    max_lat = round(lat + lat_d, dec)
    min_lat = round(lat - lat_d, dec)
    max_lon = round(lon + lon_d, dec)
    min_lon = round(lon - lon_d, dec)

    return min_lon, min_lat, max_lon, max_lat


def _default(obj):
    """Default JSON serializer."""
    import calendar

    if isinstance(obj, datetime):
        if obj.utcoffset() is not None:
            obj = obj - obj.utcoffset()
        millis = int(
            calendar.timegm(obj.timetuple()) * 1000 +
            obj.microsecond / 1000
        )
        return millis
    else:
        return obj.__dict__
    # raise TypeError('Not sure how to serialize %s' % (obj,))
