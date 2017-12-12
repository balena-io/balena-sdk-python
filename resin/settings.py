from __future__ import print_function

import os.path as Path
import os
import shutil
import sys

from . import exceptions
from .resources import Message

try:  # Python 3 imports
    import configparser
except ImportError:  # Python 2 imports
    import ConfigParser as configparser


class Settings(object):
    """
    This class handles settings for Resin Python SDK.

    Attributes:
        HOME_DIRECTORY (str): home directory path.
        CONFIG_SECTION (str): section name in configuration file.
        CONFIG_FILENAME (str): configuration file name.
        _setting (dict): default value to settings.

    """

    HOME_DIRECTORY = Path.expanduser('~')
    CONFIG_SECTION = 'Settings'
    CONFIG_FILENAME = 'resin.cfg'
    DEFAULT_SETTING_KEYS = set(['pine_endpoint', 'api_endpoint', 'api_version',
                                'data_directory', 'image_cache_time',
                                'token_refresh_interval', 'cache_directory'])

    _setting = {
        # These are default config values to write default config file.
        # All values here must be in string format otherwise there will be error when write config file.
        'pine_endpoint': 'https://api.resin.io/v3/',
        'api_endpoint': 'https://api.resin.io/',
        'api_version': 'v3',
        'data_directory': Path.join(HOME_DIRECTORY, '.resin'),
        # cache time : 1 week in milliseconds
        'image_cache_time': str(1 * 1000 * 60 * 60 * 24 * 7),
        # token refresh interval: 1 hour in milliseconds
        'token_refresh_interval': str(1 * 1000 * 60 * 60)
    }

    _setting['cache_directory'] = Path.join(_setting['data_directory'],
                                            'cache')

    def __init__(self):
        config_file_path = Path.join(self._setting['data_directory'],
                                     self.CONFIG_FILENAME)
        try:
            self.__read_settings()
            if not self.DEFAULT_SETTING_KEYS.issubset(set(self._setting)):
                raise
        except:
            # Backup old settings file if it exists.
            try:
                if Path.isfile(config_file_path):
                    shutil.move(config_file_path,
                                Path.join(self._setting['data_directory'],
                                          "{0}.{1}".format(self.CONFIG_FILENAME,
                                                           'old')))
            except OSError:
                pass
            self.__write_settings(default=True)
            print(Message.INVALID_SETTINGS.format(path=config_file_path), file=sys.stderr)

    def __write_settings(self, default=None):
        """
        Write settings to file.

        Args:
            default (Optional[bool]): write default settings.

        """

        if default:
            self._setting = Settings._setting
        config = configparser.ConfigParser()
        config.add_section(self.CONFIG_SECTION)
        for key in self._setting:
            config.set(self.CONFIG_SECTION, key, self._setting[key])
        if not Path.isdir(self._setting['data_directory']):
            os.makedirs(self._setting['data_directory'])
        with open(Path.join(self._setting['data_directory'],
                            self.CONFIG_FILENAME), 'w') as config_file:
            config.write(config_file)

    def __read_settings(self):
        config_reader = configparser.ConfigParser()
        config_reader.read(Path.join(self._setting['data_directory'],
                                     self.CONFIG_FILENAME))
        config_data = {}
        options = config_reader.options(self.CONFIG_SECTION)
        for option in options:
            try:
                config_data[option] = config_reader.get(self.CONFIG_SECTION,
                                                        option)
            except:
                config_data[option] = None
        self._setting = config_data

    def has(self, key):
        """
        Check if a setting exists.

        Args:
            key (str): setting.

        Returns:
            bool: True if exists, False otherwise.

        Examples:
            >>> resin.settings.has('api_endpoint')
            True

        """

        self.__read_settings()
        if key in self._setting:
            return True
        return False

    def get(self, key):
        """
        Get a setting value.

        Args:
            key (str): setting.

        Returns:
            str: setting value.

        Raises:
            InvalidOption: If getting a non-existent setting.

        Examples:
            >>> resin.settings.get('api_endpoint')
            'https://api.resin.io/'

        """

        try:
            self.__read_settings()
            return self._setting[key]
        except KeyError:
            raise exceptions.InvalidOption(key)

    def get_all(self):
        """
        Get all settings.

        Returns:
            dict: all settings.

        Examples:
            >>> resin.settings.get_all()
            {'image_cache_time': '604800000', 'api_endpoint': 'https://api.resin.io/', 'data_directory': '/root/.resin', 'token_refresh_interval': '3600000', 'cache_directory': '/root/.resin/cache', 'pine_endpoint': 'https://api.resin.io/ewa/'}


        """

        self.__read_settings()
        return self._setting

    def set(self, key, value):
        """
        Set value for a setting.

        Args:
            key (str): setting.
            value (str): setting value.

        Examples:
            >>> resin.settings.set(key='tmp',value='123456')
            (Empty Return)

        """

        self._setting[key] = str(value)
        self.__write_settings()

    def remove(self, key):
        """
        Remove a setting.

        Args:
            key (str): setting.

        Returns:
            bool: True if successful, False otherwise.

        Examples:
            # Remove an existing key from settings
            >>> resin.settings.remove('tmp')
            True
            # Remove a non-existing key from settings
            >>> resin.settings.remove('tmp1')
            False

        """

        # if key is not in settings, return False
        result = self._setting.pop(key, False)
        if result is not False:
            self.__write_settings()
            return True
        return False
