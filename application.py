from .baseapi import BaseAPI

class Application(BaseAPI):

    def get_all(self):
        return self.request('application', 'GET')

    def restart(self, app_id):
        return self.request('/application/' + str(app_id) + '/restart', 'POST')

    def get_by_id(self, app_id):
        params = {
            'filter': 'id',
            'eq': app_id
        }
        try:
            return self.request('application', 'GET', params=params)
        except IndexError:
            # found no application
            print(Message.NO_APPLICATION_FOUND.format(value=app_id,dev_att="id"))
        except:
            # unexpected exception
            raise
