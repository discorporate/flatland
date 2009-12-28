

def setup_package():
    # undo any augmentation that nose may have triggered during
    # test discovery
    import flatland.out.genshi
    flatland.out.genshi.uninstall_element_mixin()

    # TODO: switch this on with an environ variable or something.
    # and document.
    #import tests._util
    #tests._util.enable_coercion_blocker()
