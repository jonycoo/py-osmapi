'''
Documentation, License etc.

@package osmate
'''

import logging
import requests
import json

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

URL = 'http://osmose.openstreetmap.fr/en/api/0.2'
lang = 'en'


class Issue:
    def __init__(self, lat, lon, e_id, title, subtitle, elems):
        self.lat = lat
        self.lon = lon
        self.id = e_id
        self.title = title
        self.subtitle = subtitle
        self.elems = elems

    @property
    def loc(self):
        return self.lat, self.lon

    @classmethod
    def from_list_issue(cls, lst):
        elems = str(lst[6]).split('_')
        return cls(lst[0], lst[1], lst[2], lst[9], lst[8], elems)

    @classmethod
    def gen_issue(cls, issue_lst):
        for issue in issue_lst['errors']:
            yield cls.from_list_issue(issue)

    def __str__(self):
        return '"{}" Issue at: {}, elems: {}'.format(self.title, self.loc, self.elems)


def get_issues_user(user):
    return requests.get(URL + '/errors?full=true&username={}&limit=20'.format(user)).json()


def get_issues_loc(lat, lon):
    path = '/errors?full=true&lat={}&lon={}&limit=20'
    path = path.format(lat, lon)
    return requests.get(URL + path).json()


def get_issue(issue_id):
    as_json = requests.get(URL + '/error/{}'.format(issue_id)).json()
    print(as_json)
    return Issue(as_json['lat'], as_json['lon'], issue_id,
                 as_json['title'], as_json['subtitle'], as_json['elems_id'].split('_'))
