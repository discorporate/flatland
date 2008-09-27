

def setup_package():
    # undo any augmentation that nose may have triggered during
    # test discovery
    import flatland.out.genshi
    flatland.out.genshi.uninstall_element_mixin()


