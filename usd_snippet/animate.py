# Moving Objects with Animated Transformations: Spinning the object
from pxr import Usd, UsdGeom, Gf, Sdf
import omni.usd
stage = omni.usd.get_context().get_stage()
selections = omni.usd.get_context().get_selection().get_selected_prim_paths()
prim = stage.GetPrimAtPath(selections[0])

if UsdGeom.GetStageUpAxis(stage) == 'Y':
    #UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    stage.SetStartTimeCode(1)
    stage.SetEndTimeCode(192)
    xform = UsdGeom.Xform.Get(stage, prim.GetPath())
    spin = xform.AddRotateYOp(opSuffix='spin')
    spin.Set(time=1, value=0)
    spin.Set(time=192, value=1440)

# start play the animation
import omni.timeline
timeline_interface = omni.timeline.get_timeline_interface()
timeline_interface.play()