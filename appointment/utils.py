def str_to_bool(value):
    """
    Transforms string to boolean. Useful for query args. Any non-explicit True
    will be by default a False.

    :type value: str, None
    :rtype: bool
    """
    if value is None:
        return False
    return value.lower() in ('true', 'yes', 't', '1') or value == '1'
