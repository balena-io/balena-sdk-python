import ConfigParser
import os.path as Path
import os
import shutil

from . import exceptions
from .resources import Message


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

    _setting = {}
    _default_setting = {
        'pine_endpoint': 'https://api.resin.io/ewa/',
        'api_endpoint': 'https://api.resin.io/',
        'data_directory': Path.join(HOME_DIRECTORY, '.resin'),
        # cache time : 1 week in milliseconds
        'image_cache_time': (1 * 1000 * 60 * 60 * 24 * 7),
        # token refresh interval: 1 hour in milliseconds
        'token_refresh_interval': (1 * 1000 * 60 * 60)
    }

    _default_setting['cache_directory'] = Path.join(_default_setting['data_directory'],
                                                    'cache')

    @staticmethod
    def __init_settings():
        try:
            config_file_path = Path.join(Settings._default_setting['data_directory'],
                                         Settings.CONFIG_FILENAME)
            if Settings._setting:
                Settings.__read_settings(Path.join(Settings._setting['data_directory'],
                                         Settings.CONFIG_FILENAME))
            else:
                Settings.__read_settings(config_file_path)
        except:
                # Backup old settings file if it exists.
                try:
                    if Path.isfile(config_file_path):
                        shutil.move(config_file_path,
                                    Path.join(Settings._default_setting['data_directory'],
                                              "{0}.{1}".format(Settings.CONFIG_FILENAME, 'old')))
                except OSError:
                    pass
                Settings.__write_settings(
                    Settings._default_setting['data_directory'],
                    Settings._default_setting)
                Settings._setting = Settings._default_setting
                print(Message.INVALID_SETTINGS.format(path=config_file_path))

    @staticmethod
    def __write_settings(path, settings):
        config = ConfigParser.ConfigParser()
        config.add_section(Settings.CONFIG_SECTION)
        for key in settings:
            config.set(Settings.CONFIG_SECTION, key, settings[key])
        if not Path.isdir(path):
            os.makedirs(path)
        with open(Path.join(path, Settings.CONFIG_FILENAME), 'wb') as config_file:
            config.write(config_file)

    @staticmethod
    def __read_settings(path):
        config_reader = ConfigParser.ConfigParser()
        config_reader.read(path)
        config_data = {}
        options = config_reader.options(Settings.CONFIG_SECTION)
        for option in options:
            try:
                config_data[option] = config_reader.get(Settings.CONFIG_SECTION,
                                                        option)
            except:
                config_data[option] = None
        Settings._setting = config_data

    @staticmethod
    def has(key):
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

        Settings.__init_settings()
        if key in Settings._setting:
            return True
        return False

    @staticmethod
    def get(key):
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
            Settings.__init_settings()
            return Settings._setting[key]
        except KeyError:
            raise exceptions.InvalidOption(key)

    @staticmethod
    def get_all():
        """
        Get all settings.

        Returns:
            dict: all settings.

        Examples:
            >>> resin.settings.get_all()
            {'image_cache_time': '604800000', 'api_endpoint': 'https://api.resin.io/', 'data_directory': '/root/.resin', 'token_refresh_interval': '3600000', 'cache_directory': '/root/.resin/cache', 'pine_endpoint': 'https://api.resin.io/ewa/'}


        """

        Settings.__read_settings(Path.join(Settings._setting['data_directory'],
                                           Settings.CONFIG_FILENAME))
        return self._setting

    @staticmethod
    def set(key, value):
        """
        Set value for a setting.

        Args:
            key (str): setting.
            value (str): setting value.

        Examples:
            >>> resin.settings.set(key='tmp',value='123456')
            (Empty Return)

        """
        Settings.__init_settings()
        Settings._setting[key] = str(value)
        Settings.__write_settings(Settings._setting['data_directory'], Settings._setting)

    @staticmethod
    def remove(key):
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
        Settings.__init_settings()
        result = Settings._setting.pop(key, False)
        if result is not False:
            Settings.__write_settings(Settings._setting['data_directory'], Settings._setting)
            return True
        return False
