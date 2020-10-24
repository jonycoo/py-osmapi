import unittest
import os
from rauth import OAuth1Service
from requests_oauthlib import OAuth1


class MyTestCase(unittest.TestCase):

    def test_oauth(self):
        try:
            CONSUMER_KEY = os.environ['OSM_CONSUMER_KEY']
            CONSUMER_SECRET = os.environ['OSM_CONSUMER_SECRET']
        except KeyError:
            self.skipTest("external resource not available")
            exit()

        osm_auth = OAuth1Service(
            name='osm',
            consumer_key= CONSUMER_KEY,
            consumer_secret= CONSUMER_SECRET,
            request_token_url='https://master.apis.dev.openstreetmap.org/oauth/request_token',
            access_token_url='https://master.apis.dev.openstreetmap.org/oauth/access_token',
            authorize_url='https://master.apis.dev.openstreetmap.org/oauth/authorize',
            base_url='https://master.apis.dev.openstreetmap.org')

        request_token, request_token_secret = osm_auth.get_request_token()
        authorize_url = osm_auth.get_authorize_url(request_token)
        print('Visit this URL in your browser: ' + authorize_url)
        pin = input('Enter PIN from browser: ')  # `does not need
        acc_token, acc_token_secret = osm_auth.get_access_token(request_token, request_token_secret)

        print('token: ' + acc_token + ' secret: ' + acc_token_secret)
        req_token = OAuth1(acc_token, client_secret=acc_token_secret)
        api = osm.osm_api.OsmApi()
        user = api.get_user(9992, req_token)
        print(user)


if __name__ == '__main__':
    unittest.main()
