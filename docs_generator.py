import inspect
import importlib

resin = importlib.import_module('resin', '.')
doc2md = importlib.import_module('docs.doc2md', '.')

TOC_ROOT = 0
TOC_L1 = 1
TOC_L2 = 2
TOC_L3 = 3

Table_Of_Content = [
    ('Resin', TOC_ROOT),
    ('Models', TOC_L1),
    ('Application', TOC_L2),
    ('Config', TOC_L2),
    ('Device', TOC_L2),
    ('DeviceOs', TOC_L2),
    ('EnvironmentVariable', TOC_L2),
    ('DeviceEnvVariable', TOC_L3),
    ('ApplicationEnvVariable', TOC_L3),
    ('Key', TOC_L2),
    ('Auth', TOC_L1),
    ('Logs', TOC_L1),
    ('Settings', TOC_L1),
]

FUNCTION_NAME_TEMPLATE = "{f_name}({f_args})"


def print_newline():
    """
    Add new line

    """
    print ""


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

    print(doc2md.doc2md(resin.__doc__, 'Resin Python SDK', type=0))
    print_newline()
    print('## Table of Contents')
    print(doc2md.make_toc(Table_Of_Content))
    print_newline()
    print(doc2md.doc2md(resin.models.__doc__, 'Models', type=0))
    print(doc2md.doc2md(
        resin.models.application.Application.__doc__, 'Application', type=0))
    print_functions(resin.models.application.Application)
    print(doc2md.doc2md(resin.models.device.Device.__doc__, 'Device', type=0))
    print_functions(resin.models.device.Device)
    print(doc2md.doc2md(resin.models.config.Config.__doc__, 'Config', type=0))
    print_functions(resin.models.config.Config)
    print(doc2md.doc2md(
        resin.models.device_os.DeviceOs.__doc__, 'DeviceOs', type=0))
    print_functions(resin.models.device_os.DeviceOs)
    print(doc2md.doc2md(
        resin.models.environment_variables.EnvironmentVariable.__doc__,
        'EnvironmentVariable', type=0))
    print(doc2md.doc2md(
        resin.models.environment_variables.ApplicationEnvVariable.__doc__,
        'ApplicationEnvVariable', type=0))
    print_functions(resin.models.environment_variables.ApplicationEnvVariable)
    print(doc2md.doc2md(
        resin.models.environment_variables.DeviceEnvVariable.__doc__,
        'DeviceEnvVariable', type=0))
    print_functions(resin.models.environment_variables.DeviceEnvVariable)
    print(doc2md.doc2md(resin.models.key.Key.__doc__, 'Key', type=0))
    print_functions(resin.models.key.Key)
    print(doc2md.doc2md(resin.auth.Auth.__doc__, 'Auth', type=0))
    print_functions(resin.auth.Auth)
    print(doc2md.doc2md(resin.logs.Logs.__doc__, 'Logs', type=0))
    print_functions(resin.logs.Logs)
    print(doc2md.doc2md(resin.settings.Settings.__doc__, 'Settings', type=0))
    print_functions(resin.settings.Settings)

if __name__ == '__main__':
    main()
