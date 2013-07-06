import sys


__all__ = [
    'PY2',
    'bytestring',
    'text',
    ]


PY2 = sys.version_info[0] == 2

if PY2:
    text = unicode
    bytestring = str
else:
    text = str
    bytestring = bytes
