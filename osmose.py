'''
Documentation, License etc.

@package osmote
'''

import math
import requests
import json


url = 'http://osmose.openstreetmap.fr/en/api/0.2/'

lang = 'en'
user = 'jonycoo'


def get_issues_user(user):
    return requests.get(url +'user/{}'.format(user)).json()


# def create_bbox(lat, lon, r):
#     R = float(6371.000785)
#     x = lon
#     y = lat
#     dy = 360 * r / R
#     dx = dy * math.cos(math.radians(y))
#     se = x+dx, y+dy
#     nw = x-dx, y-dy
#     return se, nw


def get_issues_loc(lat, lon):
#    bbox = create_bbox(lat, lon, 1)
    path = '/errors?full=true&lat={}&lon={}'
    path = path.format(lat, lon)
    print(path)
    isDic = requests.get(url + path).json()

    return isDic


def convert_to_dict(arr):
    tit_ar = arr['description']
    err_ar = arr['errors']
    res = list()
    for i in range(len(err_ar)):
        item = dict()
        for j in range(len(tit_ar)):
            item[tit_ar[j]] = err_ar[i][j]
        res.append(item)
    return res


def noteIssue(issue):
    a = 5


issues = get_issues_user(user)['issues']
for issue in issues:
    print(issue['id'])

issuesl = get_issues_loc(49.14161, 9.22224)
issuesl = convert_to_dict(issuesl)
for issue in issuesl:
    print(issue['error_id'])

