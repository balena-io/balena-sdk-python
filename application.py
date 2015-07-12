from .baseapi import BaseAPI

class Application(BaseAPI):

    def get_all(self):
        '''
        "List all applications"
        '''
        return self.request('application', 'GET')