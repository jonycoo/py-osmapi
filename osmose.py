'''
Documentation, License etc.

@package osmote
'''

import logging
import math
import requests
import json

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

URL = 'http://osmose.openstreetmap.fr/en/api/0.2/errors'
lang = 'en'
user = 'jonycoo'


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
    def from_api_issue(cls, lst):
        elems = str(lst[6]).split('_')
        return cls(lst[0], lst[1], lst[2], lst[9], lst[8], elems)

    @classmethod
    def gen_issue(cls, issue_lst):
        for issue in issue_lst:
            yield cls.from_api_issue(issue)

    def __str__(self):
        return '"{}" Issue at: {}, elems: {}'.format(self.title, self.loc, self.elems)


def get_issues_user(user):
    return requests.get(URL + '?full=true&username=' + user).json()


def get_issues_loc(lat, lon):
    path = '?full=true&lat={}&lon={}'
    path = path.format(lat, lon)
    return requests.get(URL + path).json()


issues = get_issues_user(user)
for issue in Issue.gen_issue(issues['errors']):
    print(issue)

issues = get_issues_loc(49.14161, 9.22224)
for issue in issues['errors']:
    print(issue[2])

