import requests
import json

class Device(object):

    """Device Object"""

    def __init__(self, Connection):
        self.connection = Connection

    def _get_resource(self, filtr=None, eq=None):
        '''
        @params odata filter and value
        returns body as json
        '''
        if filtr:
            query = "/device?$filter=" + \
                str(filtr) + "%20eq%20'" + str(eq) + "'"
        else:
            query = "/device"

        url = self.connection.base_url + query
        r = requests.get(url, headers=self.connection.headers)
        return r.json()['d']

    def get_by_uuid(self, uuid):
        '''
        @params device uuid
        returns device object
        '''
        return self._get_resource(filtr='uuid', eq=uuid)[0]

    def get_name(self, uuid):
        '''
        @params device uuid
        returns device name
        '''
        return self.get_by_uuid(uuid)['name']

    def is_online(self, uuid):
        '''
        @params device uuid
        returns device connection status
        '''
        return self.get_by_uuid(uuid)['is_online']

    def get_by_name(self, name):
        '''
        @params device name
        returns device object
        '''
        return self._get_resource(filtr='name', eq=name)[0]

    def get_all(self):
        """
        returns device objects
        """
        return self._get_resource()

    def get_all_by_application(self, app_id):
        """
        @parameter app_id: app_id(int)
        returns device objects
        """
        return self._get_resource(filtr='application', eq=app_id)
