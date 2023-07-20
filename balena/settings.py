import configparser
import os
import os.path as Path
import shutil
import sys
from typing import Dict, TypedDict, Optional, Union, Literal
from abc import ABC, abstractmethod
from copy import deepcopy

from . import exceptions
from .resources import Message


class SettingsConfig(TypedDict, total=False):
    balena_host: str
    api_version: str
    device_actions_endpoint_version: str
    data_directory: Union[str, Literal[False]]
    image_cache_time: str
    token_refresh_interval: str
    timeout: str


class SettingsProviderInterface(ABC):

    @abstractmethod
    def has(self, key: str) -> bool:
        pass

    @abstractmethod
    def get(self, key: str) -> str:
        pass

    @abstractmethod
    def get_all(self) -> Dict[str, str]:
        pass

    @abstractmethod
    def set(self, key: str, value: str) -> None:
        pass

    @abstractmethod
    def remove(self, key: str) -> bool:
        pass


DEFAULT_SETTINGS = {
    # These are default config values
    "balena_host": "balena-cloud.com",
    "api_version": "v6",
    "device_actions_endpoint_version": "v1",
    # cache time : 1 week in milliseconds
    "image_cache_time": str(1 * 1000 * 60 * 60 * 24 * 7),
    # token refresh interval: 1 hour in milliseconds
    "token_refresh_interval": str(1 * 1000 * 60 * 60),
    # requests timeout: 30 seconds in milliseconds
    "timeout": str(30 * 1000),
}


class FileStorageSettingsProvider(SettingsProviderInterface):
    """
    This class handles settings for balena python SDK.

    Attributes:
        HOME_DIRECTORY (str): home directory path.
        CONFIG_SECTION (str): section name in configuration file.
        CONFIG_FILENAME (str): configuration file name.
        _setting (dict): default value to settings.

    """

    HOME_DIRECTORY = os.getenv("BALENA_SETTINGS_HOME_DIRECTORY", default=Path.expanduser("~"))
    CONFIG_SECTION = os.getenv("BALENA_SETTINGS_CONFIG_SECTION", default="Settings")
    CONFIG_FILENAME = os.getenv("BALENA_SETTINGS_CONFIG_FILENAME", default="balena.cfg")
    DEFAULT_SETTING_KEYS = set(
        [
            "builder_url",
            "pine_endpoint",
            "api_endpoint",
            "api_version",
            "data_directory",
            "image_cache_time",
            "token_refresh_interval",
            "cache_directory",
            "timeout",
            "device_actions_endpoint_version",
        ]
    )

    def __init__(self, settings_config: Optional[SettingsConfig]):
        _base_settings = deepcopy(DEFAULT_SETTINGS)

        if settings_config is not None:
            _base_settings = {**_base_settings, **settings_config}

        host = _base_settings["balena_host"]
        _base_settings["builder_url"] = f"https://builder.{host}/"
        _base_settings["api_endpoint"] = f"https://api.{host}/"
        _base_settings["pine_endpoint"] = f"https://api.{host}/{_base_settings['api_version']}/"

        data_directory = _base_settings.get("data_directory")
        if data_directory is None or data_directory is True:
            _base_settings["data_directory"] = Path.join(FileStorageSettingsProvider.HOME_DIRECTORY, ".balena")

        _base_settings["cache_directory"] = Path.join(_base_settings["data_directory"], "cache")

        self.__base_settings = _base_settings
        self._setting = _base_settings

        config_file_path = Path.join(self._setting["data_directory"], self.CONFIG_FILENAME)
        try:
            self.__read_settings()
            if not self.DEFAULT_SETTING_KEYS.issubset(set(self._setting)):
                raise
        except Exception:
            # Backup old settings file if it exists.
            try:
                if Path.isfile(config_file_path):
                    shutil.move(
                        config_file_path,
                        Path.join(
                            self._setting["data_directory"],
                            "{0}.{1}".format(self.CONFIG_FILENAME, "old"),
                        ),
                    )
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
            self._setting = self.__base_settings
        config = configparser.ConfigParser()
        config.add_section(self.CONFIG_SECTION)
        for key in self._setting:
            config.set(self.CONFIG_SECTION, key, self._setting[key])
        if not Path.isdir(self._setting["data_directory"]):
            os.makedirs(self._setting["data_directory"])
        with open(Path.join(self._setting["data_directory"], self.CONFIG_FILENAME), "w") as config_file:
            config.write(config_file)

    def __read_settings(self):
        config_reader = configparser.ConfigParser()
        config_reader.read(Path.join(self._setting["data_directory"], self.CONFIG_FILENAME))
        config_data = {}
        options = config_reader.options(self.CONFIG_SECTION)
        for option in options:
            try:
                config_data[option] = config_reader.get(self.CONFIG_SECTION, option)
            except Exception:
                config_data[option] = None
        self._setting = config_data

    def has(self, key: str) -> bool:
        self.__read_settings()
        if key in self._setting:
            return True
        return False

    def get(self, key: str) -> str:
        try:
            self.__read_settings()
            return self._setting[key]
        except KeyError:
            raise exceptions.InvalidOption(key)

    def get_all(self) -> Dict[str, str]:
        self.__read_settings()
        return self._setting

    def set(self, key: str, value: str) -> None:
        self._setting[key] = str(value)
        self.__write_settings()

    def remove(self, key: str) -> bool:
        # if key is not in settings, return False
        result = self._setting.pop(key, False)
        if result is not False:
            self.__write_settings()
            return True
        return False


class InMemorySettingsProvider(SettingsProviderInterface):
    def __init__(self, settings_config: Optional[SettingsConfig]):
        self._settings = deepcopy(DEFAULT_SETTINGS)

        if settings_config is not None:
            self._settings = {**DEFAULT_SETTINGS, **settings_config}

        host = self._settings["balena_host"]
        self._settings["builder_url"] = f"https://builder.{host}/"
        self._settings["api_endpoint"] = f"https://api.{host}/"
        self._settings["pine_endpoint"] = f"https://api.{host}/{self._settings['api_version']}/"

    def has(self, key: str) -> bool:
        if key in self._settings:
            return True
        return False

    def get(self, key: str) -> str:
        try:
            return self._settings[key]
        except KeyError:
            raise exceptions.InvalidOption(key)

    def get_all(self) -> Dict[str, str]:
        return self._settings

    def set(self, key: str, value: str) -> None:
        self._settings[key] = str(value)

    def remove(self, key: str) -> bool:
        result = self._settings.pop(key, False)
        if result:
            return True
        return False


class Settings(SettingsProviderInterface):
    """
    This class handles settings for balena python SDK.

    """

    def __init__(self, settings_config: Optional[SettingsConfig]):
        self.__settings_provider: SettingsProviderInterface

        if settings_config and settings_config.get("data_directory") is False:
            self.__settings_provider = InMemorySettingsProvider(settings_config)
        else:
            self.__settings_provider = FileStorageSettingsProvider(settings_config)

    def has(self, key: str) -> bool:
        """
        Check if a setting exists.

        Args:
            key (str): setting.

        Returns:
            bool: True if exists, False otherwise.

        Examples:
            >>> balena.settings.has('api_endpoint')
        """
        return self.__settings_provider.has(key)

    def get(self, key: str) -> str:
        """
        Get a setting value.

        Args:
            key (str): setting.

        Returns:
            str: setting value.

        Raises:
            InvalidOption: If getting a non-existent setting.

        Examples:
            >>> balena.settings.get('api_endpoint')
        """
        return self.__settings_provider.get(key)

    def get_all(self) -> Dict[str, str]:
        """
        Get all settings.

        Returns:
            dict: all settings.

        Examples:
            >>> balena.settings.get_all()
        """
        return self.__settings_provider.get_all()

    def set(self, key: str, value: str) -> None:
        """
        Set value for a setting.

        Args:
            key (str): setting.
            value (str): setting value.

        Examples:
            >>> balena.settings.set(key='tmp',value='123456')
        """
        return self.__settings_provider.set(key, value)

    def remove(self, key: str) -> bool:
        """
        Remove a setting.

        Args:
            key (str): setting.

        Returns:
            bool: True if successful, False otherwise.

        Examples:
            # Remove an existing key from settings
            >>> balena.settings.remove('tmp')
            # Remove a non-existing key from settings
            >>> balena.settings.remove('tmp1')
        """
        return self.__settings_provider.remove(key)
