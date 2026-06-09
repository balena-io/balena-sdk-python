import importlib
import inspect

balena = importlib.import_module("balena", ".")
doc2md = importlib.import_module("docs.doc2md", ".")

TOC_ROOT = 0
TOC_L1 = 1
TOC_L2 = 2
TOC_L3 = 3
TOC_L4 = 4

FUNCTION_NAME_TEMPLATE = "{f_name}({f_args})"


def get_function_docs(baseclass, model_hints):
    """
    Generates and collects documentation for all functions within a class.
    Returns a list of tuples: (function_name, markdown_string)
    """
    func_docs = []
    for (func_name, _) in inspect.getmembers(baseclass, predicate=inspect.isfunction):
        if func_name != "__init__" and not func_name.startswith("_"):
            func = getattr(baseclass, func_name)

            clean_name, f_args, func_output_hint = doc2md.make_function_name(func, func_name)

            hint_ref = None
            for model_hint in model_hints:
                # if the func_output_hint includes the name of a type, create the reference for that type
                # for example, when child_hint is List[AType] we want it to be able to navigate to AType ref
                if model_hint in func_output_hint:
                    hint_ref = model_hint.lower()

            module_path = baseclass.__module__
            full_function_call = f"{module_path}.{clean_name}{f_args}"

            if hint_ref:
                signature_line = (
                    f"**Signature:** `{full_function_call}` ⇒ [<code>{func_output_hint}</code>](#{hint_ref})"
                )
            else:
                signature_line = f"**Signature:** `{full_function_call}` ⇒ <code>{func_output_hint}</code>"

            heading_markdown = doc2md.doc2md(func.__doc__, clean_name, type=1, signature=signature_line)

            func_docs.append((clean_name, heading_markdown + "\n"))

    return func_docs


def main():
    hints = []
    model_hints = inspect.getmembers(balena.types.models)
    for type_tuple in model_hints:
        if not type_tuple[0].startswith("__") and not str(type_tuple[1]).startswith("typing"):
            hints.append(type_tuple[0])

    print(doc2md.doc2md(balena.__doc__, "Balena Python SDK", type=0))
    print("")
    print(doc2md.doc2md(balena.models.__doc__, "Models", type=0))
    print("")

    # A list of tuples: (name, markdown_content)
    documentation_pool = []

    # Target classes
    targets = [
        (balena.models.application.Application, "Application"),
        (balena.models.application.ApplicationTag, "ApplicationTag"),
        (balena.models.application.ApplicationConfigVariable, "ApplicationConfigVariable"),
        (balena.models.application.ApplicationEnvVariable, "ApplicationEnvVariable"),
        (balena.models.application.BuildEnvVariable, "BuildEnvVariable"),
        (balena.models.application.ApplicationMembership, "ApplicationMembership"),
        (balena.models.application.ApplicationInvite, "ApplicationInvite"),
        (balena.models.device.Device, "Device"),
        (balena.models.device.DeviceTag, "DeviceTag"),
        (balena.models.device.DeviceConfigVariable, "DeviceConfigVariable"),
        (balena.models.device.DeviceEnvVariable, "DeviceEnvVariable"),
        (balena.models.device.DeviceServiceEnvVariable, "DeviceServiceEnvVariable"),
        (balena.models.device.DeviceHistory, "DeviceHistory"),
        (balena.models.device_type.DeviceType, "DeviceType"),
        (balena.models.api_key.ApiKey, "ApiKey"),
        (balena.models.key.Key, "Key"),
        (balena.models.organization.Organization, "Organization"),
        (balena.models.organization.OrganizationMembership, "OrganizationMembership"),
        (balena.models.organization.OrganizationMembershipTag, "OrganizationMembershipTag"),
        (balena.models.organization.OrganizationInvite, "OrganizationInvite"),
        (balena.models.os.DeviceOs, "DeviceOs"),
        (balena.models.config.Config, "Config"),
        (balena.models.release.Release, "Release"),
        (balena.models.release.ReleaseTag, "ReleaseTag"),
        (balena.models.Service, "Service"),
        (balena.models.service.ServiceEnvVariable, "ServiceEnvVariable"),
        (balena.models.Image, "Image"),
        (balena.auth.Auth, "Auth"),
        (balena.twofactor_auth.TwoFactorAuth, "TwoFactorAuth"),
        (balena.logs.Logs, "Logs"),
        (type(balena.settings), "Settings")
    ]

    for (element_cls, title) in targets:
        # Generate the main Markdown body for the class itself
        class_md = doc2md.doc2md(element_cls.__doc__, title, type=0)
        documentation_pool.append((title, class_md))

        method_docs = get_function_docs(element_cls, hints)
        method_docs.sort(key=lambda method: method[0].lower())
        for _, m_md in method_docs:
            # Anchor these methods to their parent class using a "Class Z_method" key.
            # This suffix ensures a global sort keeps the methods grouped directly underneath
            # their parent class header, instead of scattering them across the document.
            documentation_pool.append((title + " Z_method", m_md))

    documentation_pool.sort(key=lambda name: name[0].lower())

    for (_, markdown_content) in documentation_pool:
        print(markdown_content)

    doc2md.print_types(balena.types.models)


if __name__ == "__main__":
    main()
