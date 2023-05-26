# encoding: utf-8
"""
This script is from https://github.com/nghiant2710/doc2md
"""
import inspect
import re
import sys
import json
import pprint


import typing
from typing import Any, get_type_hints


def simplify_type_hint(type_hint: Any) -> str:

    # print(type_hint)

    if isinstance(type_hint, str):
        return f'"{type_hint}"'
    elif type_hint is None or type_hint.__name__ == "NoneType":
        # print("A")
        return 'None'
    elif inspect.isclass(type_hint) or type(type_hint) == type(Ellipsis):
        # print("B")
        return type_hint.__name__  # type: ignore
    elif type_hint is Any:
        # print("C")
        return 'Any'
    elif hasattr(type_hint, '_name') and type_hint._name:
        # print("D")

        if not hasattr(type_hint, "__args__"):
            return type_hint._name

        inner_types = [simplify_type_hint(t) for t in type_hint.__args__]

        # Handle Optional[...]
        if type_hint._name == 'Optional' and 'None' in inner_types:
            inner_types.remove('None')
            return f'Optional[{", ".join(inner_types)}]'

        return f'{type_hint._name}[{", ".join(inner_types)}]'
    elif isinstance(type_hint, typing._GenericAlias):  # type: ignore
        # print("E")
        inner_types = [simplify_type_hint(t) for t in type_hint.__args__]
        base = simplify_type_hint(type_hint.__origin__)
        return f'{base}[{", ".join(inner_types)}]'
    elif isinstance(type_hint, typing._SpecialForm):
        # print("F")
        return str(type_hint)
    else:
        # print("G")
        return str(type_hint)


__all__ = ["doctrim", "doc2md"]

SECTIONS = ["Args:", "Attributes:", "Returns:", "Raises:", "Notes:", "Examples:"]

INDENT = "    "
NEW_LINE = ""

# Level for each section in class
CLASS_NAME = 2
FUNCTION_NAME = 3
SECTION_NAME = 4

doctrim = inspect.cleandoc


def unindent(lines):
    """
    Remove common indentation from string.

    Unlike doctrim there is no special treatment of the first line.

    """
    try:
        # Determine minimum indentation:
        indent = min(len(line) - len(line.lstrip()) for line in lines if line)
    except ValueError:
        return lines
    else:
        return [line[indent:] for line in lines]


def code_block(lines, language=""):
    """
    Mark the code segment for syntax highlighting.
    """
    return ["```" + language] + lines + ["```"]


# Since we don't want to omit `>>>` in code block, the two following methods will be commented out.
# def doctest2md(lines):
#    """
#    Convert the given doctest to a syntax highlighted markdown segment.
#    """
#    is_only_code = True
#    lines = unindent(lines)
#    for line in lines:
#        if not line.startswith('>>> ') and not line.startswith(
#                '... ') and line not in ['>>>', '...']:
#            is_only_code = False
#            break
#    if is_only_code:
#        orig = lines
#        lines = []
#        for line in orig:
#            lines.append(line[4:])
#    return lines


def doc_code_block(lines, language):
    if language == "python":
        lines = unindent(lines)
    return code_block(lines, language)


_reg_section = re.compile("^#+ ")


def is_heading(line):
    return _reg_section.match(line)


def get_heading(line):
    assert is_heading(line)
    part = line.partition(" ")
    return len(part[0]), part[2]


def make_heading(level, title):
    return "#" * max(level, 1) + " " + title


def find_sections(lines):
    """
    Find all section names and return a list with their names.
    """
    sections = []
    for line in lines:
        if is_heading(line):
            sections.append(get_heading(line))
    return sections


def make_toc(sections, hints=[]):
    """
    Generate table of contents for array of section names.
    """

    if not sections:
        return []
    refs = []
    for sec, ind, ref in sections:
        sons = []
        if ref is None:
            ref = sec.lower()
        else:
            if isinstance(ref, str):
                ref = ref.lower()
            else:
                sons = get_funcs(ref)
                ref = ref.__name__.lower().split('.')[-1]

        ref = ref.replace(" ", "-")
        ref = ref.replace("?", "")
        refs.append(INDENT * (ind) + "- [%s](#%s)" % (sec, ref))

        for (son_name, hint, son_ref) in sons:
            hint_ref = None
            for h in hints:
                if h in hint:
                    hint_ref = h.lower()

            if hint_ref:
                refs.append(INDENT * (ind+1) + f"- [{son_name}](#{son_ref}) ⇒ [<code>{hint}</code>](#{hint_ref})")
            else:
                refs.append(INDENT * (ind+1) + f"- [{son_name}](#{son_ref}) ⇒ <code>{hint}</code>")

    return "\n".join(refs)


def get_funcs(baseclass):
    sons = []
    for func_name, _ in inspect.getmembers(baseclass, predicate=inspect.isfunction):
        if func_name != "__init__" and not func_name.startswith("_"):
            func = getattr(baseclass, func_name)
            if "self" in inspect.getfullargspec(func)[0]:
                print_name, hint = make_function_name(func, func_name)
                ref_name = f"{baseclass.__name__.lower()}.{func_name}"

                sons.append((print_name, hint, ref_name))
    return sons


def make_function_name(func, func_name):
    args_list = inspect.getfullargspec(func)[0]
    if "self" in args_list:
        args_list.remove("self")

    f_args = ", ".join(args_list)

    fqh = get_type_hints(func).get("return")
    if fqh:
        hint = simplify_type_hint(fqh)
    else:
        hint = "None"
    return f"{func_name}({f_args})", hint


def _get_class_intro(lines):
    intro = []
    contents = lines[:]
    for line in lines:
        if line.strip() in SECTIONS:
            return intro, contents
        else:
            contents.pop(0)
            intro += [line + NEW_LINE]
    return intro, contents


def _is_class_section(line):
    line = line.strip()
    if line in SECTIONS:
        return SECTION_NAME
    return 0


def _doc2md(lines):
    md = []
    is_code = False
    code = []
    language = ""
    for line in lines:
        trimmed = line.lstrip()
        level = _is_class_section(line)
        if is_code:
            if line:
                code.append(line)
            else:
                is_code = False
                md += doc_code_block(code, language)
                md += [line]
        elif trimmed.startswith(">>> "):
            is_code = True
            language = "python"
            code = [line]
        elif trimmed.startswith("$ "):
            is_code = True
            language = "bash"
            code = [line]
        elif trimmed.startswith("# "):
            is_code = True
            language = "python"
            code = [line]
        elif level > 0:
            md += [make_heading(level, line)]
        else:
            md += [line]
    if is_code:
        md += doc_code_block(code, language)
    return md


def doc2md(docstr, title, type=0):
    # Type = 0 -> class, Type = 1 -> functions
    """
    Convert a docstring to a markdown text.
    """
    text = doctrim(docstr)
    lines = text.split("\n")
    intro, contents = _get_class_intro(lines)
    if type == 0:
        level = CLASS_NAME
    if type == 1:
        level = FUNCTION_NAME
        title = "Function: {func_name}".format(func_name=title)
    md = [make_heading(level, title), NEW_LINE]
    md += intro
    md += _doc2md(contents)
    return "\n".join(md)


def mod2md(module, title, title_api_section, toc=True):
    """
    Generate markdown document from module, including API section.
    """
    docstr = module.__doc__

    text = doctrim(docstr)
    lines = text.split("\n")

    sections = find_sections(lines)
    if sections:
        level = min(n for n, t in sections) - 1
    else:
        level = 1

    api_md = []
    api_sec = []
    if title_api_section and module.__all__:
        sections.append((level + 1, title_api_section))
        for name in module.__all__:
            api_sec.append((level + 2, name))
            api_md += ["", ""]
            entry = module.__dict__[name]
            if entry.__doc__:
                md, sec = doc2md(entry.__doc__, name, min_level=level + 2, more_info=True, toc=False)
                api_sec += sec
                api_md += md

    sections += api_sec

    # headline
    md = [make_heading(level, title), "", lines.pop(0), ""]

    # main sections
    if toc:
        md += make_toc(sections)
    md += _doc2md(lines)

    # API section
    md += [
        "",
        "",
        make_heading(level + 1, title_api_section),
    ]
    if toc:
        md += [""]
        md += make_toc(api_sec)
    md += api_md

    return "\n".join(md)


def main(args=None):
    # parse the program arguments
    import argparse

    parser = argparse.ArgumentParser(description="Convert docstrings to markdown.")

    parser.add_argument("module", help="The module containing the docstring.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("entry", nargs="?", help="Convert only docstring of this entry in module.")
    group.add_argument(
        "-a",
        "--all",
        dest="all",
        action="store_true",
        help="Create an API section with the contents of module.__all__.",
    )
    parser.add_argument("-t", "--title", dest="title", help="Document title (default is module name)")
    parser.add_argument(
        "--no-toc",
        dest="toc",
        action="store_false",
        default=True,
        help="Do not automatically generate the TOC",
    )
    args = parser.parse_args(args)

    import importlib
    import inspect
    import os

    def add_path(*pathes):
        for path in reversed(pathes):
            if path not in sys.path:
                sys.path.insert(0, path)

    file = inspect.getfile(inspect.currentframe())
    add_path(os.path.realpath(os.path.abspath(os.path.dirname(file))))
    add_path(os.getcwd())

    mod_name = args.module
    if mod_name.endswith(".py"):
        mod_name = mod_name.rsplit(".py", 1)[0]
    title = args.title or mod_name.replace("_", "-")

    module = importlib.import_module(mod_name)

    if args.all:
        print(mod2md(module, title, "API", toc=args.toc))

    else:
        if args.entry:
            docstr = module.__dict__[args.entry].__doc__
        else:
            docstr = module.__doc__

        print(doc2md(docstr, title, toc=args.toc))


def typed_dict_to_dict(typed_dict_cls):
    return {k: simplify_type_hint(v) for k, v in get_type_hints(typed_dict_cls).items()}


def pretty_print_python_dict(d):
    items = [f'    "{k}": {v}' for k, v in d.items()]
    p_dict = "{\n" + ",\n".join(items) + "\n}"
    print(p_dict)


def print_types(types):
    print("## Types")
    members = inspect.getmembers(types)

    for type_tuple in members:
        if not type_tuple[0].startswith("__") and not str(type_tuple[1]).startswith("typing"):
            # print(type_tuple)
            print("### " + type_tuple[0])
            print("\n")
            print("```python")
            pretty_print_python_dict(typed_dict_to_dict(type_tuple[1]))
            print("```")
            print("\n")

if __name__ == "__main__":
    main()
