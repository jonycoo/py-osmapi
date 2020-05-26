import os
import logging

# Using OAuth1Session
from requests_oauthlib import OAuth1Session

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
        self.oauth = OAuth1Session(CLIENT_KEY, client_secret=CLIENT_SECRET)
        self.owner_key = ''
        self.owner_secret = ''
        self.verifier = ''
        self.request_token_url = req_token_url or 'https://master.apis.dev.openstreetmap.org/oauth/request_token'
        self.base_authorization_url = base_auth_url or 'https://master.apis.dev.openstreetmap.org/oauth/authorize'
        self.access_token_url = acc_token_url or 'https://master.apis.dev.openstreetmap.org/oauth/access_token'


    # Using OAuth1Session
    def request_token(self):

        fetch_response = self.oauth.fetch_request_token(self.request_token_url)
        logger.debug(fetch_response)

        self.owner_key = fetch_response.get('oauth_token')
        self.owner_secret = fetch_response.get('oauth_token_secret')
        return self.owner_key, self.owner_secret

    # Using OAuth1Session
    def authorize(self):
        authorization_url = self.oauth.authorization_url(self.base_authorization_url)
        print('Please go here and authorize,', authorization_url)  # TODO send this message to user
        redirect_response = 'raw_input("Paste the full redirect URL here: ")'  # TODO create socket for redirect
        oauth_response = self.oauth.parse_authorization_response(redirect_response)
        logger.debug(oauth_response)
        self.verifier = oauth_response.get('oauth_verifier')
        return self.verifier

    # Using OAuth1Session
    def access_token(self):
        self.oauth = OAuth1Session(CLIENT_KEY,
                                   client_secret=CLIENT_SECRET,
                                   resource_owner_key=self.owner_key,
                                   resource_owner_secret=self.owner_secret,
                                   verifier=self.verifier)
        oauth_tokens = self.oauth.fetch_access_token(self.acc_token_url)

