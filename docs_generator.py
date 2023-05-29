import importlib
import inspect


balena = importlib.import_module("balena", ".")
doc2md = importlib.import_module("docs.doc2md", ".")

TOC_ROOT = 0
TOC_L1 = 1
TOC_L2 = 2
TOC_L3 = 3
TOC_L4 = 4

Table_Of_Content = [
    ("balena", TOC_ROOT, None),
    (".models", TOC_L1, "Models"),
    (".application", TOC_L2, balena.models.Application),
    (".tags", TOC_L3, balena.models.application.ApplicationTag),
    (".config_var", TOC_L3, balena.models.application.ApplicationConfigVariable),
    (".env_var", TOC_L3, balena.models.application.ApplicationEnvVariable),
    (".build_var", TOC_L3, balena.models.application.BuildEnvVariable),
    (".membership", TOC_L3, balena.models.application.ApplicationMembership),
    (".invite", TOC_L3, balena.models.application.ApplicationInvite),
    (".device", TOC_L2, balena.models.Device),
    (".tags", TOC_L3, balena.models.device.DeviceTag),
    (".config_var", TOC_L3, balena.models.device.DeviceConfigVariable),
    (".env_var", TOC_L3, balena.models.device.DeviceEnvVariable),
    (".service_var", TOC_L3, balena.models.device.DeviceServiceEnvVariable),
    (".history", TOC_L3, balena.models.device.DeviceHistory),
    (".device_type", TOC_L2, balena.models.DeviceType),
    (".api_key", TOC_L2, balena.models.ApiKey),
    (".key", TOC_L2, balena.models.Key),
    (".organization", TOC_L2, balena.models.Organization),
    (".membership", TOC_L3, balena.models.organization.OrganizationMembership),
    (".tags", TOC_L4, balena.models.organization.OrganizationMembershipTag),
    (".invite", TOC_L3, balena.models.organization.OrganizationInvite),
    (".os", TOC_L2, balena.models.DeviceOs),
    (".config", TOC_L2, balena.models.Config),
    (".release", TOC_L2, balena.models.Release),
    (".tags", TOC_L3, balena.models.release.ReleaseTag),
    (".service", TOC_L2, balena.models.Service),
    (".var", TOC_L3, balena.models.service.ServiceEnvVariable),
    (".image", TOC_L2, balena.models.Image),
    (".auth", TOC_L1, balena.auth.Auth),
    (".two_factor", TOC_L2, balena.twofactor_auth.TwoFactorAuth),
    (".logs", TOC_L1, balena.logs.Logs),
    (".settings", TOC_L1, type(balena.settings)),
    (".types", TOC_L1, balena.types),
]

FUNCTION_NAME_TEMPLATE = "{f_name}({f_args})"


def print_newline():
    """
    Add new line

    """
    print("")


def print_functions(baseclass, model_hints):
    for func_name, blah in inspect.getmembers(baseclass, predicate=inspect.isfunction):
        if func_name != "__init__" and not func_name.startswith("_"):
            func = getattr(baseclass, func_name)
            print(f'\n<a name="{baseclass.__name__.lower()}.{func_name}"></a>')

            print_name, func_output_hint = doc2md.make_function_name(func, func_name)

            hint_ref = None
            for model_hint in model_hints:
                # if the func_output_hint includes the name of a type, create the reference for that type
                # for example, when child_hint is List[AType] we want it to be able to navigate to AType ref
                if model_hint in func_output_hint:
                    hint_ref = model_hint.lower()

            if hint_ref:
                print_name = f"{print_name} ⇒ [<code>{func_output_hint}</code>](#{hint_ref})"
            else:
                print_name = f"{print_name} ⇒ <code>{func_output_hint}</code>"

            print(doc2md.doc2md(func.__doc__, print_name, type=1))


def main():
    hints = []
    model_hints = inspect.getmembers(balena.types.models)
    for type_tuple in model_hints:
        if not type_tuple[0].startswith("__") and not str(type_tuple[1]).startswith("typing"):
            hints.append(type_tuple[0])

    print(doc2md.doc2md(balena.__doc__, "Balena Python SDK", type=0))
    print_newline()
    print("## Table of Contents")
    print(doc2md.make_toc(Table_Of_Content, hints))
    print_newline()
    print(doc2md.doc2md(balena.models.__doc__, "Models", type=0))
    print(doc2md.doc2md(balena.models.application.Application.__doc__, "Application", type=0))
    print_functions(balena.models.application.Application, hints)
    print(
        doc2md.doc2md(
            balena.models.application.ApplicationTag.__doc__,
            "ApplicationTag",
            type=0,
        ),
    )
    print_functions(balena.models.application.ApplicationTag, hints)
    print(
        doc2md.doc2md(
            balena.models.application.ApplicationConfigVariable.__doc__,
            "ApplicationConfigVariable",
            type=0,
        )
    )
    print_functions(balena.models.application.ApplicationConfigVariable, hints)
    print(
        doc2md.doc2md(
            balena.models.application.ApplicationEnvVariable.__doc__,
            "ApplicationEnvVariable",
            type=0,
        )
    )
    print_functions(balena.models.application.ApplicationEnvVariable, hints)
    print(
        doc2md.doc2md(
            balena.models.application.BuildEnvVariable.__doc__,
            "BuildEnvVariable",
            type=0,
        )
    )
    print_functions(balena.models.application.BuildEnvVariable, hints)
    print(
        doc2md.doc2md(
            balena.models.application.ApplicationMembership.__doc__,
            "ApplicationMembership",
            type=0,
        )
    )
    print_functions(balena.models.application.ApplicationMembership, hints)
    print(
        doc2md.doc2md(
            balena.models.application.ApplicationInvite.__doc__,
            "ApplicationInvite",
            type=0,
        )
    )
    print_functions(balena.models.application.ApplicationInvite, hints)
    print(doc2md.doc2md(balena.models.device.Device.__doc__, "Device", type=0))
    print_functions(balena.models.device.Device, hints)

    print(
        doc2md.doc2md(
            balena.models.device.DeviceTag.__doc__,
            "DeviceTag",
            type=0,
        )
    )
    print_functions(balena.models.device.DeviceTag, hints)

    print(
        doc2md.doc2md(
            balena.models.device.DeviceConfigVariable.__doc__,
            "DeviceConfigVariable",
            type=0,
        )
    )
    print_functions(balena.models.device.DeviceConfigVariable, hints)

    print(
        doc2md.doc2md(
            balena.models.device.DeviceEnvVariable.__doc__,
            "DeviceEnvVariable",
            type=0,
        )
    )
    print_functions(balena.models.device.DeviceEnvVariable, hints)

    print(
        doc2md.doc2md(
            balena.models.device.DeviceServiceEnvVariable.__doc__,
            "DeviceServiceEnvVariable",
            type=0,
        )
    )
    print_functions(balena.models.device.DeviceServiceEnvVariable, hints)

    print(
        doc2md.doc2md(
            balena.models.device.DeviceHistory.__doc__,
            "DeviceHistory",
        )
    )

    print_functions(balena.models.device.DeviceHistory, hints)

    print(doc2md.doc2md(balena.models.device_type.DeviceType.__doc__, "DeviceType", type=0))
    print_functions(balena.models.device_type.DeviceType, hints)

    print(doc2md.doc2md(balena.models.api_key.ApiKey.__doc__, "ApiKey", type=0))
    print_functions(balena.models.api_key.ApiKey, hints)

    print(doc2md.doc2md(balena.models.key.Key.__doc__, "Key", type=0))
    print_functions(balena.models.key.Key, hints)

    print(doc2md.doc2md(balena.models.organization.Organization.__doc__, "Organization", type=0))
    print_functions(balena.models.organization.Organization, hints)

    print(
        doc2md.doc2md(
            balena.models.organization.OrganizationMembership.__doc__,
            "OrganizationMembership",
            type=0,
        )
    )
    print_functions(balena.models.organization.OrganizationMembership, hints)

    print(
        doc2md.doc2md(
            balena.models.organization.OrganizationMembershipTag.__doc__,
            "OrganizationMembershipTag",
            type=0,
        )
    )
    print_functions(balena.models.organization.OrganizationMembershipTag, hints)

    print(
        doc2md.doc2md(
            balena.models.organization.OrganizationInvite.__doc__,
            "OrganizationInvite",
            type=0,
        )
    )
    print_functions(balena.models.organization.OrganizationInvite, hints)

    print(doc2md.doc2md(balena.models.os.DeviceOs.__doc__, "DeviceOs", type=0))
    print_functions(balena.models.os.DeviceOs, hints)

    print(doc2md.doc2md(balena.models.config.Config.__doc__, "Config", type=0))
    print_functions(balena.models.config.Config, hints)

    print(doc2md.doc2md(balena.models.release.Release.__doc__, "Release", type=0))
    print_functions(balena.models.release.Release, hints)

    print(doc2md.doc2md(balena.models.release.ReleaseTag.__doc__, "ReleaseTag", type=0))
    print_functions(balena.models.release.ReleaseTag, hints)

    print(doc2md.doc2md(balena.models.Service.__doc__, "Service", type=0))
    print_functions(balena.models.Service, hints)

    print(
        doc2md.doc2md(
            balena.models.service.ServiceEnvVariable.__doc__,
            "ServiceEnvVariable",
            type=0,
        )
    )
    print_functions(balena.models.service.ServiceEnvVariable, hints)

    print(doc2md.doc2md(balena.models.Image.__doc__, "Image", type=0))
    print_functions(balena.models.Image, hints)

    print(doc2md.doc2md(balena.auth.Auth.__doc__, "Auth", type=0))
    print_functions(balena.auth.Auth, hints)

    print(doc2md.doc2md(balena.twofactor_auth.TwoFactorAuth.__doc__, "TwoFactorAuth", type=0))
    print_functions(balena.twofactor_auth.TwoFactorAuth, hints)

    print(doc2md.doc2md(balena.logs.Logs.__doc__, "Logs", type=0))
    print_functions(balena.logs.Logs, hints)

    print(doc2md.doc2md(type(balena.settings).__doc__, "Settings", type=0))
    print_functions(type(balena.settings), hints)

    doc2md.print_types(balena.types.models)


if __name__ == "__main__":
    main()
