from nose.tools import eq_


def setup_package():
    from flatland.schema import base
    eq_(base.Element.__bases__, (base._BaseElement,))

    import flatland.out.genshi
    flatland.out.genshi.install_element_mixin()
    assert len(base.Element.__bases__) == 2

def teardown_package():
    from flatland.schema import base

    assert len(base.Element.__bases__) == 2

    import flatland.out.genshi
    flatland.out.genshi.uninstall_element_mixin()
    eq_(base.Element.__bases__, (base._BaseElement,))
