from . import containers
from .. import util


__all__ = 'Form',

class Form(containers.Dict):
    """A collection of named fields or schema items.

    Forms are the most common top-level mapping.  They behave like
    :class:`flatland.Dict`, but do not need to be named.  Forms are
    defined with Python class syntax:

    .. doctest::

      >>> import flatland
      >>> class HelloForm(flatland.Form):
      ...     schema = [ flatland.String('hello'),
      ...                flatland.String('world') ]
      ...

    Subclasses must define a :attr:`schema` property, containing an
    ordered sequence of fields.  Forms may embed other container
    fields and other forms:

    .. doctest::

      >>> class BigForm(flatland.Form):
      ...     schema = [
      ...       HelloForm('main_hello'),
      ...       flatland.List('alt_hellos',
      ...                     flatland.Dict('alt',
      ...                                   flatland.String('alt_name'),
      ...                                   HelloForm('alt_hello')))
      ...              ]
      ...

    This would create a form with one ``HelloForm`` embedded as
    ``main_hello``, and a list of zero or more dicts, each containing
    an ``alt_name`` and another ``HelloForm``.

    """

    def __init__(self, name=None, **kw):
        try:
            members = self.schema
        except AttributeError:
            raise TypeError('a schema is required')

        if hasattr(self, 'validators'):
            if 'validators' in kw:
                v = self.validators[:]
                v.extend(kw['validators'])
                kw['validators'] = v
            else:
                kw['validators'] = self.validators[:]

        containers.Dict.__init__(self, name, *members, **kw)

    @classmethod
    def from_flat(cls, items, **kw):
        """Return a Form element initialized from a sequence of pairs.

        :param items: a sequence of ``(key, value)`` pairs, as for
           :meth:`Element.from_flat`.

        :param \*\*kw: keyword arguments will be passed to the
            :class:`Form` constructor.

        """
        element = cls(**kw).create_element()
        element.set_flat(items)
        return element

    @classmethod
    def from_value(cls, value, **kw):
        """Return a Form element initialized from a compatible value.

        :param value: any value, will be passed to :meth:`Element.set`.

        :param \*\*kw: keyword arguments will be passed to the
            :class:`Form` constructor.

        """
        element = cls(**kw).create_element()
        element.set(value)
        return element

    @classmethod
    def create_blank(cls, **kw):
        """Return a blank, empty Form element.

        :param \*\*kw: keyword arguments will be passed to the
            :class:`Form` constructor.

        The returned element will contain all of the keys defined in
        the :attr:`schema`.  Scalars will have a value of ``None`` and
        containers will have their empty representation.

        """
        return cls(**kw).create_element()

    @classmethod
    def from_defaults(cls, **kw):
        """Return a Form element initialized with FieldSchema defaults."""
        element = cls(**kw).create_element()
        element.set_default()
        return element

    @classmethod
    def from_object(cls, obj, include=None, omit=None, rename=None, **kw):
        """Return a Form element initialized with an object's attributes.

        :param obj: any object
        :param include: optional, an iterable of attribute names to
            pull from *obj*, if present on the object.  Only these
            attributes will be included.
        :param omit: optional, an iterable of attribute names to
            ignore on **obj**.  All other attributes matching a
            named field on the Form will be included.
        :param rename: optional, a mapping of attribute-to-field name
            transformations.  Attributes specified in the mapping will
            be included regardless of *include* or *omit*.
        :param \*\*kw: keyword arguments will be passed to the
            :class:`Form` constructor.

        *include* and *omit* are mutually exclusive.

        Creates and initializes a Form element, using as many
        attributes as possible from *obj*.  Object attributes that do
        not correspond to field names are ignored.

        Elements have two corresponding methods useful for
        round-tripping values in and out of your domain objects.

        .. testsetup::

          import flatland
          class UserForm(flatland.Form):
              schema = [ flatland.String('login'),
                         flatland.String('password'),
                         flatland.String('verify_password'), ]

          class User(object):
              def __init__(self, login=None, password=None):
                  self.login = login
                  self.password = password

          user = User('squiznart')

        :meth:`_DictElement.update_object` performs the inverse of
        :meth:`from_object`, and :meth:`_DictElement.slice` is useful
        for constructing new objects.

        .. doctest::

          >>> form = UserForm.from_object(user)
          >>> form.update_object(user, omit=['verify_password'])
          >>> new_user = User(**form.slice(omit=['verify_password'], key=str))

        """
        self = cls(**kw)

        attributes = set(self.fields.iterkeys())
        if rename:
            rename = list(util.to_pairs(rename))
            attributes.update(key for key, value in rename
                                  if value in attributes)
        if omit:
            omit = list(omit)
            attributes.difference_update(omit)

        possible = ((attr, getattr(obj, attr))
                    for attr in attributes
                    if hasattr(obj, attr))

        sliced = util.keyslice_pairs(possible, include=include,
                                     omit=omit, rename=rename)
        final = dict((key, value)
                     for key, value in sliced
                     if key in set(self.fields.iterkeys()))
        return self.create_element(value=final)
