'''
Documentation, License etc.

@package osmote
'''

import math
import requests
import json


url = 'http://osmose.openstreetmap.fr/en/api/0.2/errors'

lang = 'en'
user = 'jonycoo'


def get_issues_user(user):
    return requests.get(url +'?full=true&username=' + user).json()


# def create_bbox(lat, lon, radius):
#     R = float(6371.000785) # R is radius of earth in km
#     x = lon
#     y = lat
#     dy = 360 * radius / R
#     dx = dy * math.cos(math.radians(y))
#     se = x+dx, y+dy
#     nw = x-dx, y-dy
#     return se, nw


def get_issues_loc(lat, lon):
    path = '?full=true&lat={}&lon={}'
    path = path.format(lat, lon)
    print(path)
    isDic = requests.get(url + path).json()
    return isDic


def noteIssue(issue):
    a = 5


issues = get_issues_user(user)
print(issues)
for issue in issues['errors']:
    print(issue[2])

issuesl = get_issues_loc(49.14161, 9.22224)
for issue in issuesl['errors']:
    print(issue[2])

'''
    0  : "lat",
    1  : "lon",
    2  : "error_id",
    3  : "item",
    4  : "source",
    5  : "class",
    6  : "elems",
    7  : "subclass",
    8  : "subtitle",
    9  : "title",
    10 : "level",
    11 : "update",
    12 : "username"

'''