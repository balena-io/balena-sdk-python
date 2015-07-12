from .baseapi import BaseAPI


class Environment_Variables(BaseAPI):

    def create(self, app_id, name, value):
        data = {
            'name': name,
            'value': value,
            'application': app_id
        }
        return self.request('environment_variable', 'POST', data=data)
