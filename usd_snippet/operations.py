#move/rotate/scale the prim
from pxr import Usd, UsdGeom, Gf, Sdf
import omni.usd
stage = omni.usd.get_context().get_stage()
selections = omni.usd.get_context().get_selection().get_selected_prim_paths()
prim = stage.GetPrimAtPath(selections[0])

rotation = prim.GetAttribute('xformOp:rotateXYZ').Get()
#rotate by Y for 50 degree
val = (rotation[0], rotation[1]+50, rotation[2])
prim.GetAttribute('xformOp:rotateXYZ').Set(val)

translate = prim.GetAttribute('xformOp:translate').Get()
#move left for 2 meter
val = (translate[0]+2, translate[1], translate[2])
prim.GetAttribute('xformOp:translate').Set(val)

scale = prim.GetAttribute('xformOp:scale').Get()
#scale for 3 times
val = (scale[0]*3, scale[1]*3, scale[2]*3)
prim.GetAttribute('xformOp:scale').Set(val)
