import sys


__all__ = [
    'PY2',
    'bytestring_type',
    'identifier_transform',
    'string_types',
    'text_type',
    ]


PY2 = sys.version_info[0] == 2

if PY2:
    text_type = unicode
    bytestring_type = str
    identifier_transform = lambda i: i.encode('ascii')
else:
    text_type = str
    bytestring_type = bytes
    identifier_transform = lambda i: i

string_types = (bytestring_type, text_type)
