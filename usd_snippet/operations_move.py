#move the prim/object
from pxr import Usd, UsdGeom, Gf, Sdf
import omni.usd
stage = omni.usd.get_context().get_stage()
selections = omni.usd.get_context().get_selection().get_selected_prim_paths()
prim = stage.GetPrimAtPath(selections[0])

translate = prim.GetAttribute('xformOp:translate').Get()
#move left for 2 meter
val = (translate[0]+2, translate[1], translate[2])
prim.GetAttribute('xformOp:translate').Set(val)
