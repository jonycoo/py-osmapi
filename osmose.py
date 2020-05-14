'''
Documentation, License etc.

@package osmate
'''

import logging
import requests
import json

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s', level=logging.DEBUG)
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
    def from_api_issue(cls, lst):
        elems = str(lst[6]).split('_')
        return cls(lst[0], lst[1], lst[2], lst[9], lst[8], elems)

    @classmethod
    def to_issue_list(cls, issue_lst):
        ret = []
        for issue in issue_lst['errors']:
            ret.append(cls.from_api_issue(issue))
        return ret

    def __str__(self):
        return '"{}" Issue at: {}, elems: {} ,more: /{}'.format(self.title, self.loc, self.elems, 'iss' + self.id)


def get_issues_user(user):
    logger.debug('Entering: get_issues_user')
    lst = requests.get(URL + '/errors?full=true&username={}&limit=50'.format(user)).json()
    logger.debug(lst)
    return Issue.to_issue_list(lst)


def get_issues_loc(lat, lon):
    logger.debug('Entering: get_issues_loc')
    path = '/errors?full=true&lat={}&lon={}&limit=50'
    path = path.format(lat, lon)
    return Issue.to_issue_list(requests.get(URL + path).json())


def get_issue(issue_id):
    logger.debug('Entering: get_issue')
    '''returns single issue with more info'''
    as_json = requests.get(URL + '/error/{}'.format(issue_id)).json()
    print(as_json)
    return Issue(as_json['lat'], as_json['lon'], issue_id,
                 as_json['title'], as_json['subtitle'], as_json['elems_id'].split('_'))


class Pager:
    def __init__(self, lst, step):
        self.lst = lst
        self.index = step * (-1)
        self.step = step

    def next(self):
        if self.index + self.step > len(self.lst):
            self.index = 0
        else:
            self.index += self.step
        ret = self.lst[self.index: self.index + self.step]
        logger.debug('pager index after next:' + str(self.index))
        return ret

    def prev(self):
        if self.index - 2*self.step < 0:
            self.index = len(self.lst) - self.step
        else:
            self.index -= self.step
        ret = self.lst[(self.index - 2*self.step): (self.index - self.step)]
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
        return self.lst[self.index - self.step: self.index]
