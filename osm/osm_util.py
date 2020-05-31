import json
import math
from datetime import datetime


class Element:
    def __init__(self, i_id: int, i_type: str, tags: dict, nodes: list = None, members: list = None):
        """

        :param i_id:
        :param i_type:
        :param tags:
        :param nodes: list Node ID
        :param members: list of dictionary
        """
        self._id = i_id
        self._type = i_type
        self.tags = tags
        if nodes:
            self.nodes = nodes
        if members:
            self.members = members
        super().__init__()

    def __repr__(self):
        return json.dumps(self.__dict__)

    def __str__(self):
        return str(self.id)

    @property
    def id(self):
        return self._id

    @property
    def type(self):
        return self._type


class Comment:
    def __init__(self, text: str, uid: int, username: str, created: datetime):
        self.text = text
        self.uid = uid
        self.user = username
        self.created = created


class Note:
    def __init__(self):
        pass


class ChangeSet:
    def __init__(self, cid: int, username: str, uid: int, created: datetime, is_open: bool, bbox: tuple, closed: datetime = None,
                 tags: dict = None):
        self.id = cid
        self.user = username
        self.uid = uid
        self.created = created
        self.open = is_open
        self.maxlon, self.maxlat, self.minlon, self.minlan = bbox or None, None, None, None
        self.closed = closed
        self.tags = tags or {}
        self.comments = []

    def __repr__(self):
        return json.dumps(self.__dict__)

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
