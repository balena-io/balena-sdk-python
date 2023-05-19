## Balena Python SDK

Welcome to the balena python SDK documentation.
This document aims to describe all the functions supported by the SDK, as well as
showing examples of their expected usage.

Install the Balena SDK:

From Pip:
```
pip install balena-sdk
```

From Source (In case, you want to test a development branch):
```
https://github.com/balena-io/balena-sdk-python
```

Getting started:

```python
>>> from balena import Balena
>>> balena = Balena()
>>> credentials = {'username':<your email>, 'password':<your password>}
>>> balena.auth.login(**credentials)
...
```

If you feel something is missing, not clear or could be improved, [please don't
hesitate to open an issue in GitHub](https://github.com/balena-io/balena-sdk-python/issues), we'll be happy to help.

## Table of Contents
- [Balena](#balena)
    - [Models](#models)
        - [Application](#application)
            - [ApplicationInvite](#applicationinvite)
            - [ApplicationMembership](#applicationmembership)
        - [ApiKey](#apikey)
        - [Config](#config)
        - [ConfigVariable](#configvariable)
            - [ApplicationConfigVariable](#applicationconfigvariable)
            - [DeviceConfigVariable](#deviceconfigvariable)
        - [Device](#device)
        - [DeviceOs](#deviceos)
        - [DeviceType](#devicetype)
        - [EnvironmentVariable](#environmentvariable)
            - [ApplicationEnvVariable](#applicationenvvariable)
            - [ServiceEnvVariable](#serviceenvvariable)
            - [DeviceEnvVariable](#deviceenvvariable)
            - [DeviceServiceEnvVariable](#deviceserviceenvvariable)
        - [Image](#image)
        - [Organization](#organization)
            - [OrganizationInvite](#organizationinvite)
            - [OrganizationMembership](#organizationmembership)
                - [OrganizationMembershipTag](#organizationmembershiptag)
        - [Release](#release)
        - [Service](#service)
        - [Tag](#tag)
            - [ApplicationTag](#applicationtag)
            - [DeviceTag](#devicetag)
            - [ReleaseTag](#releasetag)
        - [Key](#key)
        - [Supervisor](#supervisor)
        - [History](#history)
            - [DeviceHistory](#devicehistory)
    - [Auth](#auth)
    - [Logs](#logs)
    - [Settings](#settings)
    - [TwoFactorAuth](#twofactorauth)

## Models

This module implements all models for balena python SDK.
## Application

This class implements application model for balena python SDK.
### Function: create(name, device_type, organization, application_class)

Create an application.

#### Args:
    name (str): application name.
    device_type (str): device type (slug).
    organization (Union[str, int]): handle or id of the organization that the application will belong to.
    application_class (Optional[Literal["app", "fleet", "block"]]): application class.

#### Returns:
    dict: application info.

#### Examples:
```python
>>> balena.models.application.create('foo', 'raspberry-pi', 12345)
>>> balena.models.application.create('foo', 'raspberry-pi', 12345, 'block')
```
### Function: disable_device_urls(slug_or_uuid_or_id)

Disable device urls for all devices that belong to an application.

#### Args:
    slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number).

#### Examples:
```python
>>> balena.models.application.disable_device_urls(5685)
```
### Function: enable_device_urls(slug_or_uuid_or_id)

Enable device urls for all devices that belong to an application

#### Args:
    slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number).

#### Examples:
```python
>>> balena.models.application.enable_device_urls(5685)
```
### Function: generate_provisioning_key(slug_or_uuid_or_id, key_name, description, expiry_date)

Generate a device provisioning key for a specific application.

#### Args:
    slug_or_uuid_or_id (str): application slug (string), uuid (string) or id (number)
    key_name (Optional[str]): provisioning key name.
    description (Optional[str]): description for provisioning key.
    expiry_date (Optional[str]): expiry date for provisioning key, for example: `2030-01-01T00:00:00Z`.

#### Returns:
    str: device provisioning key.

#### Examples:
```python
>>> balena.models.application.generate_provisioning_key(5685)
```
### Function: get(slug_or_uuid_or_id, options, context)

Get a single application.

#### Args:
    slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
    options (AnyObject): extra pine options to use
    context (Optional[str]): extra access filters, None or 'directly_accessible'

#### Returns:
    ApplicationType: application info.

#### Examples:
```python
>>> balena.models.application.get("myorganization/myapp")
>>> balena.models.application.get(123)
```
### Function: get_all(options, context)

Get all applications

#### Args:
    options (AnyObject): extra pine options to use
    context (Optional[str]): extra access filters, None or 'directly_accessible'

#### Returns:
    List[APIKeyType]: user API key

#### Examples:
```python
>>> balena.models.application.get_all()
```
### Function: get_all_directly_accessible(options)

Get all applications directly accessible by the user

#### Args:
    options (AnyObject): extra pine options to use

#### Returns:
    List[APIKeyType]: user API key

#### Examples:
```python
>>> balena.models.application.get_all_directly_accessible()
```
### Function: get_by_name(app_name, options, context)

 Get a single application using the appname.

#### Args:
    slug_or_uuid_or_id (str): application slug (string), uuid (string) or id (number)
    options (AnyObject): extra pine options to use
    context (Optional[str]): extra access filters, None or 'directly_accessible'

#### Returns:
    ApplicationType: application info.

#### Examples:
```python
>>> balena.models.application.get("myapp")
```
### Function: get_by_owner(app_name, owner, options)

Get a single application using the appname and the handle of the owning organization.

#### Args:
    app_name (str): application name.
    owner (str): The handle of the owning organization.
    options (AnyObject): extra pine options to use.

#### Returns:
    ApplicationType: application info.

#### Examples:
```python
>>> balena.models.application.get_by_owner('foo', 'my_org')
```
### Function: get_dashboard_url(app_id)

Get Dashboard URL for a specific application.

#### Args:
    app_id (int): application id.

#### Returns:
    str: Dashboard URL for the specific application.

#### Examples:
```python
>>> balena.models.application.get_dashboard_url(1476418)
```
### Function: get_directly_accessible(slug_or_uuid_or_id, options)

Get a single application directly accessible by the user

#### Args:
    slug_or_uuid_or_id (str): application slug (string), uuid (string) or id (number)
    options (AnyObject): extra pine options to use

#### Returns:
    ApplicationType: application info.

#### Examples:
```python
>>> balena.models.application.get_directly_accessible("myorganization/myapp")
>>> balena.models.application.get_directly_accessible(123)
```
