# Change Log

All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## [1.5.1] - 2016-07-05

## Changed

- Fix issue with PubNub logs channel. If available, use device.logs_channel for PubNub channel names.

## [1.5.0] - 2016-04-28

## Added

- Implement resin.models.supervisor.enable_tcp_ping().
- Implement resin.models.supervisor.disable_tcp_ping().
- Implement resin.models.supervisor.regenerate_supervisor_api_key().
- Implement resin.models.supervisor.get_device_state().
- Implement resin.models.supervisor.stop_application().
- Implement resin.models.supervisor.get_application_info().
- Implement resin.models.supervisor.start_application().

## Changed

- Update all functions in resin.models.supervisor, Use device_uuid instead of device_id for ease of use.


## [1.4.0] - 2016-02-26

## Added

- Implement resin.models.device.get_status()

## Changed

- Patch device types to be marked as ALPHA and BETA not PREVIEW and EXPERIMENTAL.
- Fix error when reading settings by backing up old settings file and rewriting default settings.
- Fix bug of device.get_local_ip_address().


## [1.3.1] - 2015-12-01

### Changed

- Fix bug with return value of `resin.auth.is_logged_in()`.


## [1.3.0] - 2015-11-26

### Added

- Implement resin.models.device.move().


## [1.2.0] - 2015-11-13

### Added

* Implement Resin Supervisor which provides an easy way to interact with the Supervisor agent on your device: 
	- resin.models.supervisor.ping()
	- resin.models.supervisor.blink()
	- resin.models.supervisor.update()
	- resin.models.supervisor.reboot()
	- resin.models.supervisor.shutdown()
	- resin.models.supervisor.purge()
	- resin.models.supervisor.restart()
	- resin.models.supervisor.force_api_endpoint()
* Implement basic two-factor authentication functionalities:
	- resin.models.twofactor_auth.is_enabled()
	- resin.models.twofactor_auth.is_passed()
	- resin.models.twofactor_auth.challenge()
	- resin.models.twofactor_auth.generate_code()
	- resin.models.twofactor_auth.get_otpauth_secret()


## [1.1.1] - 2015-10-19

### Changed

- Update `setup.py` parse VERSION directly from `__init__.py` instead of importing resin.


## [1.1.0] - 2015-10-02

### Added

- Implement Resin API Key. User can authorize by credentials, auth token or set Resin API key as RESIN_API_KEY environment variable.
- Implement `resin.models.device.restart()`
- Implement `resin.models.device.has_device_url()`
- Implement `resin.models.device.get_device_url()`
- Implement `resin.models.device.enable_device_url()`
- Implement `resin.models.device.disable_device_url()`

### Changed

- Fix `resin.auth.is_logged_in()` remove auth token.
- Fix bug with API endpoints in some functions.
- Implement `login` flag that marks functions only work if users authorize by credentials or auth token.

### Removed

- Remove `VALID_OPTIONS` in resin.models.device_os that blocks extra os parameters when downloading an image.
- Remove `resin.models.config.get_pubnub_keys()`.
