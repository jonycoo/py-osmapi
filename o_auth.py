import os
import logging

from rauth import OAuth1Service

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    CLIENT_KEY = os.environ['OSM_KEY']
    CLIENT_SECRET = os.environ['OSM_SECRET']
except KeyError:
    logger.exception('please set up environment variables OSM_KEY and OSM_SECRET')
    raise AttributeError


class Authorisation:

    def __init__(self, req_token_url=None, base_auth_url=None, acc_token_url=None):
        self.verifier = ''
        self.request_token_url = req_token_url or 'https://master.apis.dev.openstreetmap.org/oauth/request_token'
        self.base_authorization_url = base_auth_url or 'https://master.apis.dev.openstreetmap.org/oauth/authorize'
        self.access_token_url = acc_token_url or 'https://master.apis.dev.openstreetmap.org/oauth/access_token'
        self.osm = OAuth1Service(
            name='osmate',
            consumer_key=CLIENT_KEY,
            consumer_secret=CLIENT_SECRET,
            request_token_url=self.request_token_url,
            access_token_url=self.access_token_url,
            authorize_url=self.base_authorization_url,
            base_url='https://master.apis.dev.openstreetmap.org/api/0.6')

    def request_token(self):
        return self.osm.get_request_token()

    def authorize(self):
        authorize_url = self.osm.get_authorize_url(self.osm.get_request_token()[0])

        print('Visit this URL in your browser: ' + authorize_url)
        self.verifier = input('Enter PIN from browser: ')  # `input` if using Python 3!

        self.osm.get_access_token(*self.osm.get_request_token())
        self.osm.get_access_token()
        return self.verifier


