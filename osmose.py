'''
Documentation, License etc.

@package osmate
'''

import logging
import requests
import json
from operator import itemgetter
import osm_util

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

URL = 'http://osmose.openstreetmap.fr/en/api/0.2'
lang = 'en'


class Issue:
    def __init__(self, lat, lon, e_id, title, subtitle, elems):
        self.lat = float(lat)
        self.lon = float(lon)
        self.id = e_id
        self.title = title
        self.subtitle = subtitle
        self.elems = elems

    @property
    def loc(self):
        return self.lat, self.lon

    @classmethod
    def from_api_issue(cls, lst):
        elems = str(lst[6]).split("_")
        return cls(lst[0], lst[1], lst[2], lst[9], lst[8], elems)

    @classmethod
    def to_issue_list(cls, issue_lst):
        ret = []
        for issue in issue_lst['errors']:
            ret.append(cls.from_api_issue(issue))
        logger.debug('Issue Items: ' + str(len(ret)))
        return ret

    @classmethod
    def detail_issue(cls, lat, lon, e_id, title, subtitle, elems, bbox):
        '''bbox format: (min_lon, min_lat, max_lon, max_lat)'''
        iss = cls(lat, lon, e_id, title, subtitle, elems)
        iss.bbox = bbox
        return iss

    def __repr__(self):
        return json.dumps(self.__dict__)

    def __str__(self):
        return '"{}" Issue at: <a href="{}">{}</a>, elems: {} '\
            .format(self.title, self.osm_url(), self.loc, [str(elem) for elem in self.elems])

    def osm_url(self):
        return "https://osm.org/#map=18/{}/{}&layers=ND".format(self.lat, self.lon)


def get_issues_user(user):
    logger.debug('Entering: get_issues_user')
    lst = requests.get(URL + '/errors?full=true&username={}&limit=53'.format(user)).json()
    logger.debug(lst)
    return Issue.to_issue_list(lst)


def get_issues_loc(lat, lon):
    logger.debug('Entering: get_issues_loc')
    path = '/errors?full=true&lat={}&lon={}&limit=50'
    path = path.format(lat, lon)
    lst = requests.get(URL + path).json()
    return Issue.to_issue_list(lst)


def get_issue(issue_id):
    logger.debug('Entering: get_issue')
    '''returns single issue with more info'''
    as_json = requests.get(URL + '/error/{}'.format(issue_id)).json()
    logger.debug(as_json)
    bbox = itemgetter('minlon', 'minlat', 'maxlon', 'maxlat')(as_json)
    elems = []
    for elem in as_json['elems']:
        elems.append(osm_util.Element(elem['id'], elem['type'], elem['tags']))

    issue = Issue.detail_issue(as_json['lat'], as_json['lon'], issue_id,
                               as_json['title'], as_json['subtitle'], elems, bbox)
    return issue


class Pager:
    def __init__(self, lst, step):
        self.lst = lst
        self.index = step * (-1)
        self.step = step

    def next(self):
        ret = []
        if (len(self.lst) - self.index) < self.step:
            ret = self.lst[self.index:]
        else:
            self.index += self.step
            ret = self.lst[self.index: (self.index + self.step)]
        logger.debug('pager index after next:' + str(self.index))
        return ret

    def prev(self):
        ret = []
        if self.index > 0:
            ret = self.lst[(self.index - self.step): self.index]
            self.index -= self.step
        else:
            ret = self.lst[(self.index - self.step): self.index]
            self.index = 0
        logger.debug('pager index after prev:' + str(self.index))
        return ret

    @staticmethod
    def to_msg(lst):
        message = ''
        for item in lst:
            message += str(item) + '\n\n'
        logger.debug(message)
        return message

    def curr(self):
        ret = self.lst[self.index: (self.index + self.step)]
        return ret
