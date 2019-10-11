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
