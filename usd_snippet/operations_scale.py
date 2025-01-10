#scale the prim/object
from pxr import Usd, UsdGeom, Gf, Sdf
import omni.usd
stage = omni.usd.get_context().get_stage()
selections = omni.usd.get_context().get_selection().get_selected_prim_paths()
prim = stage.GetPrimAtPath(selections[0])

scale = prim.GetAttribute('xformOp:scale').Get()
#scale for 3 times
val = (scale[0]*3, scale[1]*3, scale[2]*3)
prim.GetAttribute('xformOp:scale').Set(val)
