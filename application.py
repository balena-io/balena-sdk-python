from .baseapi import BaseAPI

class Application(BaseAPI):

    def get_all(self):
        return self.request('application', 'GET')

    def restart(self, app_id):
        return self.request('/application/' + str(app_id) + '/restart', 'POST')

    def get_by_id(self, app_id):
        return self.request('application?id=' + str(app_id), 'GET')[0]
