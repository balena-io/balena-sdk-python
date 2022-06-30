import numbers


def is_id(value):
    """
    Return True, if the input value is a valid ID. False otherwise.

    """

    if isinstance(value, numbers.Number):
        try:
            int(value)
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
