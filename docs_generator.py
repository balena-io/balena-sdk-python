from __future__ import print_function
import inspect
import importlib

balena = importlib.import_module('balena', '.')
doc2md = importlib.import_module('docs.doc2md', '.')

TOC_ROOT = 0
TOC_L1 = 1
TOC_L2 = 2
TOC_L3 = 3

Table_Of_Content = [
    ('Balena', TOC_ROOT),
    ('Models', TOC_L1),
    ('Application', TOC_L2),
    ('ApiKey', TOC_L2),
    ('Config', TOC_L2),
    ('ConfigVariable', TOC_L2),
    ('ApplicationConfigVariable', TOC_L3),
    ('DeviceConfigVariable', TOC_L3),
    ('Device', TOC_L2),
    ('DeviceOs', TOC_L2),
    ('EnvironmentVariable', TOC_L2),
    ('ApplicationEnvVariable', TOC_L3),
    ('ServiceEnvVariable', TOC_L3),
    ('DeviceEnvVariable', TOC_L3),
    ('DeviceServiceEnvVariable', TOC_L3),
    ('Image', TOC_L2),
    ('Organization', TOC_L2),
    ('Release', TOC_L2),
    ('Service', TOC_L2),
    ('Tag', TOC_L2),
    ('ApplicationTag', TOC_L3),
    ('DeviceTag', TOC_L3),
    ('ReleaseTag', TOC_L3),
    ('Key', TOC_L2),
    ('Supervisor', TOC_L2),
    ('Auth', TOC_L1),
    ('Logs', TOC_L1),
    ('Settings', TOC_L1),
    ('TwoFactorAuth', TOC_L1)
]

FUNCTION_NAME_TEMPLATE = "{f_name}({f_args})"


def print_newline():
    """
    Add new line

    """
    print("")


def print_functions(baseclass):
    for func_name, blah in inspect.getmembers(
            baseclass, predicate=inspect.ismethod):
        if func_name is not '__init__' and not func_name.startswith('_'):
            func = getattr(baseclass, func_name)
            print(doc2md.doc2md(func.__doc__, make_function_name(func, func_name), type=1))


def make_function_name(func, func_name):
    args_list = inspect.getargspec(func)[0]
    if 'self' in args_list:
        args_list.remove('self')
    return FUNCTION_NAME_TEMPLATE.format(
        f_name=func_name, f_args=', '.join(args_list))


def main():

    print(doc2md.doc2md(balena.__doc__, 'Balena Python SDK', type=0))
    print_newline()
    print('## Table of Contents')
    print(doc2md.make_toc(Table_Of_Content))
    print_newline()
    print(doc2md.doc2md(balena.models.__doc__, 'Models', type=0))
    print(doc2md.doc2md(
        balena.models.application.Application.__doc__, 'Application', type=0))
    print_functions(balena.models.application.Application)
    print(doc2md.doc2md(
        balena.models.api_key.ApiKey.__doc__, 'ApiKey', type=0))
    print_functions(balena.models.api_key.ApiKey)
    print(doc2md.doc2md(balena.models.config.Config.__doc__, 'Config', type=0))
    print_functions(balena.models.config.Config)
    print(doc2md.doc2md(
        balena.models.config_variable.ConfigVariable.__doc__,
        'ConfigVariable', type=0))
    print(doc2md.doc2md(
        balena.models.config_variable.ApplicationConfigVariable.__doc__,
        'ApplicationConfigVariable', type=0))
    print_functions(balena.models.config_variable.ApplicationConfigVariable)
    print(doc2md.doc2md(
        balena.models.config_variable.DeviceConfigVariable.__doc__,
        'DeviceConfigVariable', type=0))
    print_functions(balena.models.config_variable.DeviceConfigVariable)
    print(doc2md.doc2md(balena.models.device.Device.__doc__, 'Device', type=0))
    print_functions(balena.models.device.Device)
    print(doc2md.doc2md(
        balena.models.device_os.DeviceOs.__doc__, 'DeviceOs', type=0))
    print_functions(balena.models.device_os.DeviceOs)
    print(doc2md.doc2md(
        balena.models.environment_variables.EnvironmentVariable.__doc__,
        'EnvironmentVariable', type=0))
    print(doc2md.doc2md(
        balena.models.environment_variables.ApplicationEnvVariable.__doc__,
        'ApplicationEnvVariable', type=0))
    print_functions(balena.models.environment_variables.ApplicationEnvVariable)
    print(doc2md.doc2md(
        balena.models.environment_variables.ServiceEnvVariable.__doc__,
        'ServiceEnvVariable', type=0))
    print_functions(balena.models.environment_variables.ServiceEnvVariable)
    print(doc2md.doc2md(
        balena.models.environment_variables.DeviceEnvVariable.__doc__,
        'DeviceEnvVariable', type=0))
    print_functions(balena.models.environment_variables.DeviceEnvVariable)
    print(doc2md.doc2md(
        balena.models.environment_variables.DeviceServiceEnvVariable.__doc__,
        'DeviceServiceEnvVariable', type=0))
    print_functions(balena.models.environment_variables.DeviceServiceEnvVariable)
    print(doc2md.doc2md(balena.models.image.Image.__doc__, 'Image', type=0))
    print_functions(balena.models.image.Image)
    print(doc2md.doc2md(balena.models.organization.Organization.__doc__, 'Organization', type=0))
    print_functions(balena.models.organization.Organization)
    print(doc2md.doc2md(balena.models.release.Release.__doc__, 'Release', type=0))
    print_functions(balena.models.release.Release)
    print(doc2md.doc2md(balena.models.service.Service.__doc__, 'Service', type=0))
    print_functions(balena.models.service.Service)
    print(doc2md.doc2md(balena.models.tag.Tag.__doc__, 'Tag', type=0))
    print(doc2md.doc2md(balena.models.tag.DeviceTag.__doc__, 'DeviceTag', type=0))
    print_functions(balena.models.tag.DeviceTag)
    print(doc2md.doc2md(balena.models.tag.ApplicationTag.__doc__, 'ApplicationTag', type=0))
    print_functions(balena.models.tag.ApplicationTag)
    print(doc2md.doc2md(balena.models.tag.ReleaseTag.__doc__, 'ReleaseTag', type=0))
    print_functions(balena.models.tag.ReleaseTag)
    print(doc2md.doc2md(balena.models.key.Key.__doc__, 'Key', type=0))
    print_functions(balena.models.key.Key)
    print(doc2md.doc2md(balena.models.supervisor.Supervisor.__doc__, 'Supervisor', type=0))
    print_functions(balena.models.supervisor.Supervisor)
    print(doc2md.doc2md(balena.auth.Auth.__doc__, 'Auth', type=0))
    print_functions(balena.auth.Auth)
    print(doc2md.doc2md(balena.logs.Logs.__doc__, 'Logs', type=0))
    print_functions(balena.logs.Logs)
    print(doc2md.doc2md(balena.settings.Settings.__doc__, 'Settings', type=0))
    print_functions(balena.settings.Settings)
    print(doc2md.doc2md(balena.twofactor_auth.TwoFactorAuth.__doc__, 'TwoFactorAuth', type=0))
    print_functions(balena.twofactor_auth.TwoFactorAuth)

if __name__ == '__main__':
    main()
