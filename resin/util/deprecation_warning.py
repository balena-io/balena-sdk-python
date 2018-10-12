from __future__ import print_function
import sys
import textwrap


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def run_once(f):
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)
    wrapper.has_run = False
    return wrapper


@run_once
def print_rename_warning():
    eprint(textwrap.dedent("""\
        Warning: 'resin-sdk-python' is now 'balena-sdk-python'.
        Please update your dependencies to continue receiving new updates.
    """))
