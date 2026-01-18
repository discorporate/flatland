from flatland import (
    Dict,
    String,
)
from flatland.validation import (
    Converted,
    NoLongerThan,
)


class GetTextish:
    """Mimics a gettext translation."""

    catalog = {
        "%(label)s is not correct.": "reg %(label)s",
        "%(label)s may not exceed %(maxlength)s characters.": "default %(label)s %(maxlength)s",
        "%(label)s max is %(maxlength)s characters.": "plural %(label)s %(maxlength)s",
        "%(label)s max is %(maxlength)s character.": "single %(label)s %(maxlength)s",
        "age": "AGE",
        "name": "NAME",
    }

    def ugettext(self, text):
        try:
            return self.catalog[text]
        except KeyError:
            return text

    def ungettext(self, single, plural, n):
        lookup = single if n == 1 else plural
        return self.ugettext(lookup)


class LocalizedShort(NoLongerThan):
    exceeded = (
        "%(label)s max is %(maxlength)s character.",
        "%(label)s max is %(maxlength)s characters.",
        "maxlength",
    )


def test_regular_gettext():
    catalog = GetTextish()

    # translators placed at the top of the form
    schema = Dict.of(String.named("age").using(validators=[Converted()])).using(
        ugettext=catalog.ugettext, ungettext=catalog.ungettext
    )

    data = schema()
    data.validate()
    assert data["age"].errors == ["reg AGE"]


def test_local_gettext():
    catalog = GetTextish()

    # translators placed on a specific form element
    schema = Dict.of(
        String.named("age").using(
            validators=[Converted()],
            ugettext=catalog.ugettext,
            ungettext=catalog.ungettext,
        )
    )

    data = schema()
    data.validate()
    assert data["age"].errors == ["reg AGE"]


def test_local_gettext_search_is_not_overeager():
    catalog = GetTextish()

    def poison(*a):
        assert False

    # if a translator is found on an element, its parents won't be searched
    schema = Dict.of(
        String.named("age").using(
            validators=[Converted()],
            ugettext=catalog.ugettext,
            ungettext=catalog.ungettext,
        )
    ).using(ugettext=poison, ungettext=poison)

    data = schema()
    data.validate()
    assert data["age"].errors == ["reg AGE"]


def test_builtin_gettext():
    catalog = GetTextish()

    schema = Dict.of(String.named("age").using(validators=[Converted()]))

    data = schema()

    try:
        # translators can go into the builtins
        from flatland._compat import builtins

        builtins.ugettext = catalog.ugettext
        builtins.ungettext = catalog.ungettext
        data.validate()
        assert data["age"].errors == ["reg AGE"]
    finally:
        del builtins.ugettext
        del builtins.ungettext


def test_state_gettext():
    catalog = GetTextish()

    schema = Dict.of(String.named("age").using(validators=[Converted()]))

    # if state has ugettext or ungettext attributes, those will be used
    data = schema()
    data.validate(catalog)
    assert data["age"].errors == ["reg AGE"]

    # also works if state is dict-like
    data = schema()
    state = dict(ugettext=catalog.ugettext, ungettext=catalog.ungettext)
    data.validate(state)
    assert data["age"].errors == ["reg AGE"]


def test_tuple_single():
    catalog = GetTextish()
    schema = Dict.of(String.named("name").using(validators=[LocalizedShort(1)]))

    data = schema(dict(name="xxx"))
    data.validate(catalog)
    assert data["name"].errors == ["single NAME 1"]


def test_tuple_plural():
    catalog = GetTextish()
    schema = Dict.of(String.named("name").using(validators=[LocalizedShort(2)]))

    data = schema(dict(name="xxx"))
    data.validate(catalog)
    assert data["name"].errors == ["plural NAME 2"]
