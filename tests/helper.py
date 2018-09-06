from datetime import datetime
import os.path as Path
import os
import jwt
import json
try:  # Python 3 imports
    import configparser
except ImportError:  # Python 2 imports
    import ConfigParser as configparser

from resin import Resin
from resin import exceptions as resin_exceptions
from resin.base_request import BaseRequest
from resin.settings import Settings


class TestHelper(object):

    credentials = {}

    resin = Resin()

    def __init__(self):
        TestHelper.load_env()
        self.resin_exceptions = resin_exceptions
        self.base_request = BaseRequest()
        self.settings = Settings()
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

    def create_multicontainer_app(self, app_name='FooBar', device_type='Raspberry Pi 2'):
        """
        Create a multicontainer application with a device and two releases.
        """

        app = self.resin.models.application.create(app_name, device_type, 'microservices-starter')
        dev = self.resin.models.device.register(app['id'], self.resin.models.device.generate_uuid())

        # Register web & DB services

        data = {
            'application': app['id'],
            'service_name': 'web'
        }

        web_service = json.loads(self.base_request.request('service', 'POST', data=data, endpoint=self.settings.get('pine_endpoint')).decode('utf-8'))

        data = {
            'application': app['id'],
            'service_name': 'db'
        }

        db_service = json.loads(self.base_request.request('service', 'POST', data=data, endpoint=self.settings.get('pine_endpoint')).decode('utf-8'))

        # Register an old & new release of this application

        data = {
            'belongs_to__application': app['id'],
            'is_created_by__user': app['user']['__id'],
            'commit': 'old-release-commit',
            'status': 'success',
            'source': 'cloud',
            'composition': {},
            'start_timestamp': 1234
        }

        old_release = json.loads(self.base_request.request('release', 'POST', data=data, endpoint=self.settings.get('pine_endpoint')).decode('utf-8'))

        data = {
            'belongs_to__application': app['id'],
            'is_created_by__user': app['user']['__id'],
            'commit': 'new-release-commit',
            'status': 'success',
            'source': 'cloud',
            'composition': {},
            'start_timestamp': 54321
        }

        new_release = json.loads(self.base_request.request('release', 'POST', data=data, endpoint=self.settings.get('pine_endpoint')).decode('utf-8'))

        # Set device to the new release

        data = {
            'is_on__commit': new_release['commit']
        }

        params = {
            'filter': 'uuid',
            'eq': dev['uuid']
        }

        self.base_request.request('device', 'PATCH', params=params, data=data, endpoint=self.settings.get('pine_endpoint'))
        dev = self.resin.models.device.get(dev['uuid'])

        # Register an old & new web image build from the old and new
        # releases, a db build in the new release only

        data = {
            'is_a_build_of__service': web_service['id'],
            'project_type': 'dockerfile',
            'content_hash': 'abc',
            'build_log': 'old web log',
            'start_timestamp': 1234,
            'push_timestamp': 1234,
            'status': 'success'
        }

        old_web_image = json.loads(self.base_request.request('image', 'POST', data=data, endpoint=self.settings.get('pine_endpoint')).decode('utf-8'))

        data = {
            'is_a_build_of__service': web_service['id'],
            'project_type': 'dockerfile',
            'content_hash': 'def',
            'build_log': 'new web log',
            'start_timestamp': 54321,
            'push_timestamp': 54321,
            'status': 'success'
        }

        new_web_image = json.loads(self.base_request.request('image', 'POST', data=data, endpoint=self.settings.get('pine_endpoint')).decode('utf-8'))

        data = {
            'is_a_build_of__service': db_service['id'],
            'project_type': 'dockerfile',
            'content_hash': 'jkl',
            'build_log': 'old db log',
            'start_timestamp': 123,
            'push_timestamp': 123,
            'status': 'success'
        }

        old_db_image = json.loads(self.base_request.request('image', 'POST', data=data, endpoint=self.settings.get('pine_endpoint')).decode('utf-8'))

        data = {
            'is_a_build_of__service': db_service['id'],
            'project_type': 'dockerfile',
            'content_hash': 'ghi',
            'build_log': 'new db log',
            'start_timestamp': 54321,
            'push_timestamp': 54321,
            'status': 'success'
        }

        new_db_image = json.loads(self.base_request.request('image', 'POST', data=data, endpoint=self.settings.get('pine_endpoint')).decode('utf-8'))

        # Tie the images to their corresponding releases

        data = {
            'image': old_web_image['id'],
            'is_part_of__release': old_release['id']
        }

        self.base_request.request('image__is_part_of__release', 'POST', data=data, endpoint=self.settings.get('pine_endpoint'))

        data = {
            'image': old_db_image['id'],
            'is_part_of__release': old_release['id']
        }

        self.base_request.request('image__is_part_of__release', 'POST', data=data, endpoint=self.settings.get('pine_endpoint'))

        data = {
            'image': new_web_image['id'],
            'is_part_of__release': new_release['id']
        }

        self.base_request.request('image__is_part_of__release', 'POST', data=data, endpoint=self.settings.get('pine_endpoint'))

        data = {
            'image': new_db_image['id'],
            'is_part_of__release': new_release['id']
        }

        self.base_request.request('image__is_part_of__release', 'POST', data=data, endpoint=self.settings.get('pine_endpoint'))

        # Create image installs for the images on the device

        data = {
            'installs__image': old_web_image['id'],
            'is_provided_by__release': old_release['id'],
            'device': dev['id'],
            'download_progress': 100,
            'status': 'running',
            'install_date': '2017-10-01'
        }

        self.base_request.request('image_install', 'POST', data=data, endpoint=self.settings.get('pine_endpoint'))

        data = {
            'installs__image': new_web_image['id'],
            'is_provided_by__release': new_release['id'],
            'device': dev['id'],
            'download_progress': 50,
            'status': 'downloading',
            'install_date': '2017-10-30'
        }

        self.base_request.request('image_install', 'POST', data=data, endpoint=self.settings.get('pine_endpoint'))

        data = {
            'installs__image': old_db_image['id'],
            'is_provided_by__release': old_release['id'],
            'device': dev['id'],
            'download_progress': 100,
            'status': 'Deleted',
            'install_date': '2017-09-30'
        }

        self.base_request.request('image_install', 'POST', data=data, endpoint=self.settings.get('pine_endpoint'))

        data = {
            'installs__image': new_db_image['id'],
            'is_provided_by__release': new_release['id'],
            'device': dev['id'],
            'download_progress': 100,
            'status': 'running',
            'install_date': '2017-10-30'
        }

        self.base_request.request('image_install', 'POST', data=data, endpoint=self.settings.get('pine_endpoint'))

        # Create service installs for the services running on the device

        data = {
            'installs__service': web_service['id'],
            'device': dev['id']
        }

        self.base_request.request('service_install', 'POST', data=data, endpoint=self.settings.get('pine_endpoint'))

        data = {
            'installs__service': db_service['id'],
            'device': dev['id']
        }

        self.base_request.request('service_install', 'POST', data=data, endpoint=self.settings.get('pine_endpoint'))

        return {
            'app': app,
            'device': dev,
            'web_service': web_service,
            'db_service': db_service,
            'old_release': old_release,
            'current_release': new_release,
            'old_web_image': old_web_image,
            'current_web_image': new_web_image,
            'old_db_image': old_db_image,
            'current_db_image': new_db_image
        }
