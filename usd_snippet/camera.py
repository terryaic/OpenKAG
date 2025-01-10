#create a camera and postion it.
import omni.usd
from pxr import Usd, UsdLux, UsdGeom, Sdf, Gf, Tf, UsdPhysics
stage = omni.usd.get_context().get_stage()
defaultPrimPath = str(stage.GetDefaultPrim().GetPath())

# create and position camera
cam = UsdGeom.Camera.Define(stage, defaultPrimPath + "/Camera")
cam.CreateFocalLengthAttr().Set(16.0)
camPos = Gf.Vec3d(749.0, 398.0, 15.0)
camRot = Gf.Vec3d(107.0, 0.0, 119.0)
cam.AddTranslateOp().Set(camPos)
cam.AddRotateXYZOp().Set(camRot)
cam.AddScaleOp().Set(value=(1,1,1))
cam.AddTransformOp()

