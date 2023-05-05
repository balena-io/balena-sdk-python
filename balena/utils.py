import numbers
from copy import deepcopy
from typing import Any, Dict


def is_id(value: Any) -> bool:
    """
    Return True, if the input value is a valid ID. False otherwise.

    """

    if isinstance(value, numbers.Number):
        try:
            int(value)  # type: ignore
            return True
        except ValueError:
            return False
    return False


def is_full_uuid(value: Any) -> bool:
    """
    Return True, if the input value is a valid UUID. False otherwise.

    """

    if isinstance(value, str):
        if len(value) == 32 or len(value) == 62:
            try:
                str(value)
                return True
            except ValueError:
                return False
    return False


def compare(a, b):
    """

    Return 1 if a is greater than b, 0 if a is equal to b and -1 otherwise.

    """

    if a > b:
        return 1

    if b > a:
        return -1

    return 0


def merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two dictionaries, with conflicts resolved in favor of dict2.
    """
    result = deepcopy(dict1)
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    return result
