import sys


__all__ = [
    'PY2',
    'bytestring_type',
    'text_type',
    ]


PY2 = sys.version_info[0] == 2

if PY2:
    text_type = unicode
    bytestring_type = str
else:
    text_type = str
    bytestring_type = bytes
