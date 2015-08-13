import ConfigParser
import os.path as Path
import os


HOME_DIRECTORY = Path.expanduser('~')
CONFIG_SECTION = 'Settings'
CONFIG_FILENAME = 'resin.cfg'

class Settings(object):

	_setting = {
		'pine_endpoint': 'https://api.resinstaging.io/ewa/',
		'api_endpoint': 'https://api.resinstaging.io/',
		'data_directory': Path.join(HOME_DIRECTORY, '.resin'),
		# cache time : 1 week in milliseconds
		'image_cache_time': (1 * 1000 * 60 * 60 * 24 * 7),
		# token refresh interval: 1 hour in milliseconds
		'token_refresh_interval': (1 * 1000 * 60 * 60)	
		}

	_setting['cache_directory'] = Path.join(_setting['data_directory'], 'cache')

	def __init__(self):		
		if Path.isdir(self._setting['data_directory']):
			if Path.isfile(Path.join(self._setting['data_directory'], CONFIG_FILENAME)):
				self.__read_settings()
			else:
				self.__write_settings()
		else:
			# data directory doesn't exist
			self.__write_settings()

	def __write_settings(self):
		config = ConfigParser.ConfigParser()
		config.add_section(CONFIG_SECTION)
		for key in self._setting:
			config.set(CONFIG_SECTION, key, self._setting[key])
		if not Path.isdir(self._setting['data_directory']):
			os.makedirs(self._setting['data_directory'])
		with open(Path.join(self._setting['data_directory'], CONFIG_FILENAME), 'wb') as config_file:
			config.write(config_file)

	def __read_settings(self):
		config_reader = ConfigParser.ConfigParser()
		config_reader.read(Path.join(self._setting['data_directory'], CONFIG_FILENAME))
		config_data = {}
		options = config_reader.options(CONFIG_SECTION)
		for option in options:
			try:
				config_data[option] = config_reader.get(CONFIG_SECTION, option)
			except:
				config_data[option] = None
		self._setting = config_data

	def has(self, key):
		self.__read_settings()
		if key in self._setting:
			return True
		return False

	def get(self, key):
		try:
			self.__read_settings()
			return self._setting[key]
		except KeyError:
			# TODO: need exception type for setting key not found
			raise

	def get_all(self):
		self.__read_settings()
		return self._setting

	def set(self, key, value):
		self._setting[key] = str(value)
		self.__write_settings()

	def remove(self, key):
		# if key is not in settings, return False
		result = self._setting.pop(key, False)
		if result is not False:
			self.__write_settings()
			return True
		return False