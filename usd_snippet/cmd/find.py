#traverse the stage to find all the prim/object
from pxr import Usd, UsdGeom, Gf, Sdf
import omni.usd
stage = omni.usd.get_context().get_stage()

#object to select
obj_name = 'Cube'
primPaths = []
for prim in stage.Traverse():
    primPath = str(prim.GetPath())
    if primPath.endswith(obj_name):
        primPaths.append(primPath)

omni.usd.get_context().get_selection().set_selected_prim_paths(primPaths, False)