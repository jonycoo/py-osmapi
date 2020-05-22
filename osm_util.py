import json
import math


class Element:
    def __init__(self, i_id, i_type, tags):
        self.id = i_id
        self.type = i_type
        self.tags = {}
        if tags:
            for tag in tags:
                self.tags[tag['k']] = tag['v']

    def __repr__(self):
        return json.dumps(self.__dict__)

    def __str__(self):
        return self.elem_id

    @property
    def elem_id(self):
        return self.type + '_' + str(self.id)


def create_bbox(lat, lon, rad):
    '''rad: radius in meters'''

    EARTH_RAD = float(6378000)
    lat_d = (math.asin(float(rad) / (EARTH_RAD * math.cos(math.pi * lat / 180)))) * 180 / math.pi
    lon_d = (math.asin(float(rad) / EARTH_RAD)) * 180 / math.pi

    max_lat = lat + lat_d
    min_lat = lat - lat_d
    max_lon = lon + lon_d
    min_lon = lon - lon_d

    return min_lon, min_lat, max_lon, max_lat


print(repr(Element(000000, 'way', None)))
print(create_bbox(49.16949, 9.38447, 1000))
