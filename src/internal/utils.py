import re


def merge_two_dicts(x, y):
    z = x.copy()  # start with keys and values of x
    if y is not None:
        z.update(y)  # modifies z with keys and values of y
    return z


UNSAFE_CHARS_REGEXP = """[<>\u2028\u2029/\\\r\n\t"]"""
CHARS_REGEXP = """[\\\r\n\t"]"""

UNICODE_CHARS = {
    '"': '\\"',
    '\n': '\\n',
    '\r': '\\r',
    '\t': '\\t',
    # eval('"\\u005C"') == eval('"\\\\"')
    '\u005C': '\\u005C',  # Backslash: \
    # '\\': '\\\\',  # Was needed before in serialise-javascript tests.
    '<': '\\u003C',
    '>': '\\u003E',
    '/': '\\u002F',
    #  '/': '/',
    '\0': '\\x00',  # null byte in source code did not cause problems. But it feels dangerous
    '\u2028': '\\u2028',  # LINE SEPARATOR
    '\u2029': '\\u2029',  # PARAGRAPH SEPARATOR
}


def safeString(s):
    for key in UNICODE_CHARS:
        s = s.replace(key, UNICODE_CHARS[key])
    return s


def unsafeString(s):
    for key in "\\\r\n\t\x00\"":
        s = s.replace(key, UNICODE_CHARS[key])
    return s


def quote(s, opts):
    # no real need to have the extra safe encoding in Python. It does not get embedded like JS does
    # also repr() works very nice out-of-the-box and does not do this kind of encoding
    fn = unsafeString if (opts["unsafe"]) else safeString
    return '"' + unsafeString(str(s)) + '"'


def toType(source):
    """
    Might need to return string.
    :param source:
    :return:
    """
    return type(source).__name__
