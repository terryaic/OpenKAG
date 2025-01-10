# Create material
from pxr import Sdf
import omni.kit.commands
#first create the looks scope in case it does not exists.
omni.kit.commands.execute('CreatePrim',
    prim_path='/World/Looks',
    prim_type='Scope',
    select_new_prim=False)

#then create a material prim
import omni.usd
import omni.kit.commands
mtl_path = '/World/Looks/OmniPBR'
omni.kit.commands.execute('CreateMdlMaterialPrim',
    mtl_url='OmniPBR.mdl',
    mtl_name='OmniPBR',
    mtl_path=mtl_path,
    select_new_prim=False)

#and add a texture as the source for the surface’s diffuse_texture
url = "http://www.example.com/a.png"
prop_path = mtl_path + "/Shader.inputs:diffuse_texture"
omni.kit.commands.execute('ChangeProperty',
    prop_path=Sdf.Path(prop_path),
    value=Sdf.AssetPath(url),
    prev=None)

#finally, bind material to the selected prim
stage = omni.usd.get_context().get_stage()
selections = omni.usd.get_context().get_selection().get_selected_prim_paths()
prim = stage.GetPrimAtPath(selections[0])
omni.kit.commands.execute('BindMaterial',
    prim_path=prim.GetPath(),
    material_path='/World/Looks/OmniPBR')