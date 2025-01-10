#Viewport Camera，Look at a Prim
from omni.kit.viewport.utility import get_active_viewport
from pxr import Usd, UsdLux, UsdGeom, Sdf, Gf, Tf, UsdPhysics
import omni.usd
stage = omni.usd.get_context().get_stage()
selections = omni.usd.get_context().get_selection().get_selected_prim_paths()
prim = stage.GetPrimAtPath(selections[0])

target_prim_xform_mat = UsdGeom.Xformable(prim).GetLocalTransformation()

# The target location (target_loc) is for this particular prim,
# but could also be any arbitrary location
target_loc = target_prim_xform_mat.ExtractTranslation()

viewport = get_active_viewport()
active_camera_path = viewport.camera_path.pathString
camera_prim = stage.GetPrimAtPath(active_camera_path)
camera_pos = UsdGeom.Xformable(camera_prim).GetLocalTransformation().ExtractTranslation()

new_cam_mat = Gf.Matrix4d(1.0)
new_cam_mat.SetLookAt(camera_pos, target_loc, Gf.Vec3d(0,1,0))
destXformAttr = camera_prim.GetAttribute('xformOp:transform')
destXformAttr.Set(new_cam_mat.GetInverse())