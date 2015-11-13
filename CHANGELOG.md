# Change Log

All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

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
	- resin.models.twofactor_auth.TwoFactorAuth.is_enabled()
	- resin.models.twofactor_auth.TwoFactorAuth.is_passed()
	- resin.models.twofactor_auth.TwoFactorAuth.challenge()
	- resin.models.twofactor_auth.TwoFactorAuth.generate_code()
	- resin.models.twofactor_auth.TwoFactorAuth.get_otpauth_secret()

## [1.1.1] - 2015-10-19

### Changed

- Update `setup.py` parse VERSION directly from `__init__.py` instead of importing resin.


## [1.1.0] - 2015-10-02

### Added

- Implement Resin API Key. User can authorize by credentials, auth token or set Resin API key as RESIN_API_KEY environment variable.
- Implement `resin.models.device.Device.restart()`
- Implement `resin.models.device.Device.has_device_url()`
- Implement `resin.models.device.Device.get_device_url()`
- Implement `resin.models.device.Device.enable_device_url()`
- Implement `resin.models.device.Device.disable_device_url()`

### Changed

- Fix `resin.auth.Auth.is_logged_in()` remove auth token.
- Fix bug with API endpoints in some functions.
- Implement `login` flag that marks functions only work if users authorize by credentials or auth token.

### Removed

- Remove `VALID_OPTIONS` in resin.models.device_os that blocks extra os parameters when downloading an image.
- Remove `resin.models.config.Config.get_pubnub_keys()`.
