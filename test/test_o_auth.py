import unittest
import o_auth
import requests

class MyTestCase(unittest.TestCase):

    def test_something(self):
        auth = o_auth.Authorisation()
        auth.request_token()
        code = auth.authorize()
        print(code)
        resp = requests.post('https://master.apis.dev.openstreetmap.org/api/0.6/permissions', headers={"Authorization": code})
        print(resp.text)
        print(resp)

    def test_token(self):
        resp = requests.post('https://master.apis.dev.openstreetmap.org/api/0.6/permissions',
                             headers={"Authorization": 'uqYNXxiXtuNVIZhUsAh7GsG0jdWR9bYU6j0ruQxZ'})
        print(resp.text)
        print(resp)


if __name__ == '__main__':
    unittest.main()
