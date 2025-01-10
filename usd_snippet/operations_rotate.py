#rotate the prim/object
from pxr import Usd, UsdGeom, Gf, Sdf
import omni.usd
stage = omni.usd.get_context().get_stage()
selections = omni.usd.get_context().get_selection().get_selected_prim_paths()
prim = stage.GetPrimAtPath(selections[0])

rotation = prim.GetAttribute('xformOp:rotateXYZ').Get()
#rotate along Y axis for 50 degree
val = (rotation[0], rotation[1]+50, rotation[2])
prim.GetAttribute('xformOp:rotateXYZ').Set(val)
