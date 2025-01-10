#change the texture of a prim/object
def change_texture(url, prop_path):
    import omni.kit.commands
    from pxr import Sdf, Usd, Gf
    omni.kit.commands.execute('ChangeProperty',
        prop_path=Sdf.Path(prop_path),
        value=Sdf.AssetPath(url),
        prev=None)