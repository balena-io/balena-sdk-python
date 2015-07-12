import json
import requests

class BaseAPI(object):
	"""docstring for BaseApi"""
	def __init__(self, arg):
		super(BaseApi, self).__init__()
		self.arg = arg
		
def _get_resource(data):
    '''
    returns body as json
    '''
    
    if data['eq']:
    	query = "?$filter=" + data["filter"] + "%20eq%20'" + str(data["eq"]) + "'"
    else:
    	query = ""

    url = data['connection'].base_url + "/" + data['path'] + query
    r = requests.get(url, headers=data['connection'].headers)
    return r.json()['d']

def _post_resource(data):
    connection = data['connection']
    url = data['connection'].base_url + "/" + data['path']
    r = requests.post(url, data=json.dumps(data['body']), headers=data['connection'].headers)
    return r.json()['d']