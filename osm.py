from OSMPythonTools.api import Api


def get_elem(type, id):
    api = Api()
    way = api.query('{}/{}'.format(type, id))
    return way
