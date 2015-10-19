# Change Log

All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

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
