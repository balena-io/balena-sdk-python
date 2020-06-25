from datetime import datetime
import os.path as Path
import os
import jwt
import json
try:  # Python 3 imports
    import configparser
except ImportError:  # Python 2 imports
    import ConfigParser as configparser

from balena import Balena
from balena import exceptions as balena_exceptions
from balena.base_request import BaseRequest
from balena.settings import Settings


class TestHelper(object):

    credentials = {}

    balena = Balena()

    def __init__(self):
        TestHelper.load_env()
        self.balena_exceptions = balena_exceptions
        self.base_request = BaseRequest()
        self.settings = Settings()

        if 'api_endpoint' in self.credentials and self.credentials['api_endpoint'] is not None:
            self.settings.set('api_endpoint', self.credentials['api_endpoint'])
            self.settings.set('pine_endpoint', '{0}/{1}/'.format(self.credentials['api_endpoint'], self.settings.get('api_version')))

        if not self.balena.auth.is_logged_in():
            self.balena.auth.login(
                **{
                    'username': self.credentials['user_id'],
                    'password': self.credentials['password']
                }
            )

        # Stop the test if it's run by an admin user account.
        token_data = jwt.decode(self.balena.settings.get('token'), verify=False)
        if any('admin' in s for s in token_data['permissions']):
            raise Exception('The test is run with an admin user account. Cancelled, please try again with a normal account!')

        self.default_organization = self.balena.models.organization.get_by_handle(self.balena.auth.who_am_i())

    @classmethod
    def load_env(cls):
        env_file_name = '.env'
        required_env_keys = set(['email', 'user_id', 'password'])
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
            if not required_env_keys.issubset(set(config_data)):
                raise Exception('Mandatory env keys missing!')
            cls.credentials = config_data
        else:
            # If .env file not exists, read credentials from environment vars.
            try:
                cls.credentials['email'] = os.environ['TEST_ENV_EMAIL']
                cls.credentials['user_id'] = os.environ['TEST_ENV_USER_ID']
                cls.credentials['password'] = os.environ['TEST_ENV_PASSWORD']

                # Optional endpoint override:
                cls.credentials['api_endpoint'] = os.environ.get('TEST_API_ENDPOINT')
            except:
                raise Exception('Mandatory env keys missing!')

    def wipe_application(self):
        """
        Wipe all user's apps
        """

        params = {
            'filter': '1',
            'eq': 1
        }

        self.balena.models.application.base_request.request(
            'application', 'DELETE', params=params,
            endpoint=self.balena.settings.get('pine_endpoint'), login=True
        )

    def wipe_organization(self):
        """
        Wipe all user's orgs
        """

        for org in self.balena.models.organization.get_all():
            self.balena.models.organization.remove(org['id'])

    def reset_user(self):
        """
        Wipe all user's apps and ssh keys added.
        """

        params = {
            'filter': '1',
            'eq': 1
        }

        if self.balena.auth.is_logged_in():
            self.wipe_application()
            self.balena.models.key.base_request.request(
                'user__has__public_key', 'DELETE', params=params,
                endpoint=self.balena.settings.get('pine_endpoint'), login=True
            )

    def datetime_to_epoch_ms(self, dt):
        return int((dt - datetime.utcfromtimestamp(0)).total_seconds() * 1000)

    def create_device(self, app_name='FooBar', device_type='Raspberry Pi 2'):
        """
        Create a device belongs to an application.
        """

        app = self.balena.models.application.create(app_name, device_type, self.default_organization['id'])
        return app, self.balena.models.device.register(app['id'], self.balena.models.device.generate_uuid())

    def create_multicontainer_app(self, app_name='FooBar', device_type='Raspberry Pi 2'):
        """
        Create a multicontainer application with a device and two releases.
        """

        app = self.balena.models.application.create(app_name, device_type, self.default_organization['id'], 'microservices-starter')
        dev = self.balena.models.device.register(app['id'], self.balena.models.device.generate_uuid())
        user_id = self.balena.auth.get_user_id()

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
            'is_created_by__user': user_id,
            'commit': 'old-release-commit',
            'status': 'success',
            'source': 'cloud',
            'composition': {},
            'start_timestamp': 1234
        }

        old_release = json.loads(self.base_request.request('release', 'POST', data=data, endpoint=self.settings.get('pine_endpoint')).decode('utf-8'))

        data = {
            'belongs_to__application': app['id'],
            'is_created_by__user': user_id,
            'commit': 'new-release-commit',
            'status': 'success',
            'source': 'cloud',
            'composition': {},
            'start_timestamp': 54321
        }

        new_release = json.loads(self.base_request.request('release', 'POST', data=data, endpoint=self.settings.get('pine_endpoint')).decode('utf-8'))

        # Set device to the new release

        data = {
            'is_running__release': new_release['id']
        }

        params = {
            'filter': 'uuid',
            'eq': dev['uuid']
        }

        self.base_request.request('device', 'PATCH', params=params, data=data, endpoint=self.settings.get('pine_endpoint'))
        dev = self.balena.models.device.get(dev['uuid'])

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
            'status': 'deleted',
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

    def create_app_with_releases(self, app_name='FooBar', device_type='Raspberry Pi 2'):
        """
        Create a multicontainer application with  two releases.
        """

        app = self.balena.models.application.create(app_name, device_type, self.default_organization['id'], 'microservices-starter')
        user_id = self.balena.auth.get_user_id()

        # Register an old & new release of this application

        data = {
            'belongs_to__application': app['id'],
            'is_created_by__user': user_id,
            'commit': 'old-release-commit',
            'status': 'success',
            'source': 'cloud',
            'composition': {},
            'start_timestamp': 1234
        }

        old_release = json.loads(self.base_request.request('release', 'POST', data=data, endpoint=self.settings.get('pine_endpoint')).decode('utf-8'))

        data = {
            'belongs_to__application': app['id'],
            'is_created_by__user': user_id,
            'commit': 'new-release-commit',
            'status': 'success',
            'source': 'cloud',
            'composition': {},
            'start_timestamp': 54321
        }

        new_release = json.loads(self.base_request.request('release', 'POST', data=data, endpoint=self.settings.get('pine_endpoint')).decode('utf-8'))

        return {
            'app': app,
            'old_release': old_release,
            'current_release': new_release
        }
