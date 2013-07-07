import sys


__all__ = [
    'PY2',
    'bytestring_type',
    'getattr_py2',
    'hasattr_py2',
    'identifier_transform',
    'setattr_py2',
    'string_types',
    'text_type',
    ]


PY2 = sys.version_info[0] == 2

if PY2:
    text_type = unicode
    bytestring_type = str

    def identifier_transform(identifier):
        if isinstance(identifier, unicode):
            return identifier.encode('ascii')
        else:
            return identifier

    def hasattr_py2(obj, attr):
        attr = identifier_transform(attr)
        return hasattr(obj, attr)

    def getattr_py2(obj, attr, *default):
        # quietly downgrade u'attribute' to b'attribute'
        attr = identifier_transform(attr)
        if default:
            return getattr(obj, attr, default[0])
        else:
            return getattr(obj, attr)

    def setattr_py2(obj, attr, value):
        attr = identifier_transform(attr)
        setattr(obj, attr, value)

else:
    text_type = str
    bytestring_type = bytes
    identifier_transform = lambda i: i
    getattr_py2 = getattr
    hasattr_py2 = hasattr
    setattr_py2 = setattr

string_types = (bytestring_type, text_type)
