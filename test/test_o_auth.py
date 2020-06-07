import unittest
import o_auth
import requests

class MyTestCase(unittest.TestCase):
    auth = o_auth.Authorisation()

    def test_something(self):
        owner_cr = self.auth.request_token()
        self.auth.prepare_auth_url()

    def test_something(self):
        self.auth.authorize()





if __name__ == '__main__':
    unittest.main()
