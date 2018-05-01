from datetime import datetime
import os.path as Path
import os
import jwt
try:  # Python 3 imports
    import configparser
except ImportError:  # Python 2 imports
    import ConfigParser as configparser

from resin import Resin
from resin import exceptions as resin_exceptions


class TestHelper(object):

    credentials = {}

    resin = Resin()

    def __init__(self):
        TestHelper.load_env()
        self.resin_exceptions = resin_exceptions
        if not self.resin.auth.is_logged_in():
            self.resin.auth.login(
                **{
                    'username': self.credentials['user_id'],
                    'password': self.credentials['password']
                }
            )

        # Stop the test if it's run by an admin user account.
        token_data = jwt.decode(self.resin.settings.get('token'), verify=False)
        if any('admin' in s for s in token_data['permissions']):
            raise Exception('The test is run with an admin user account. Cancelled, please try again with a normal account!')

    @classmethod
    def load_env(cls):
        env_file_name = '.env'
        default_env_keys = set(['email', 'user_id', 'password'])
        cls.credentials = {}

        if Path.isfile(env_file_name):
            # If .env file exists
            config_reader = configparser.ConfigParser()
            config_reader.read(env_file_name)
            config_data = {}
            options = config_reader.options('Credentials')
            for option in options:
                try:
                    config_data[option] = config_reader.get('Credentials', option)
                except:
                    config_data[option] = None
            if not default_env_keys.issubset(set(config_data)):
                raise Exception('Mandatory env keys missing!')
            cls.credentials = config_data
        else:
            # If .env file not exists, read credentials from environment vars.
            try:
                cls.credentials['email'] = os.environ['TEST_ENV_EMAIL']
                cls.credentials['user_id'] = os.environ['TEST_ENV_USER_ID']
                cls.credentials['password'] = os.environ['TEST_ENV_PASSWORD']
            except:
                raise Exception('Mandatory env keys missing!')

    def wipe_application(self):
        """
        Wipe all user's apps
        """

        self.resin.models.application.base_request.request(
            'application', 'DELETE',
            endpoint=self.resin.settings.get('pine_endpoint'), login=True
        )

    def reset_user(self):
        """
        Wipe all user's apps and ssh keys added.
        """

        if self.resin.auth.is_logged_in():
            self.wipe_application()
            self.resin.models.key.base_request.request(
                'user__has__public_key', 'DELETE',
                endpoint=self.resin.settings.get('pine_endpoint'), login=True
            )

    def datetime_to_epoch_ms(self, dt):
        return int((dt - datetime.utcfromtimestamp(0)).total_seconds() * 1000)

    def create_device(self, app_name='FooBar', device_type='Raspberry Pi 2'):
        """
        Create a device belongs to an application.
        """

        app = self.resin.models.application.create(app_name, device_type)
        return app, self.resin.models.device.register(app['id'], self.resin.models.device.generate_uuid())
