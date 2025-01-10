#create lights, including sphere, distant, dome, disk, cylinder and rect light
from pxr import Usd, UsdLux, UsdGeom, Sdf, Gf, Tf, UsdPhysics
import omni.usd
stage = omni.usd.get_context().get_stage()
defaultPrimPath = str(stage.GetDefaultPrim().GetPath())

# create a sphere light at location (25.0,25.0,25.0), radius value:10, intensity: 20000
sphereLight = UsdLux.SphereLight.Define(stage, defaultPrimPath + "/SphereLight")
sphereLight.CreateRadiusAttr(10)
sphereLight.CreateIntensityAttr(20000)
sphereLight.AddTranslateOp().Set(Gf.Vec3f(25.0, 25.0, 50.0))
sphereLight.AddRotateXYZOp()

# create a distant light with intensity: 1500, Angle: 0.53
distantLight = UsdLux.DistantLight.Define(stage, defaultPrimPath + "/DistantLight")
distantLight.CreateIntensityAttr(1500)
distantLight.CreateAngleAttr(0.53)

# create a dome light with intensity: 100.0
dome_light = UsdLux.DomeLight.Define(stage, defaultPrimPath + "/DomeLight")
dome_light.CreateIntensityAttr().Set(100.0)

# create a disk light
diskLight = UsdLux.DiskLight.Define(stage, defaultPrimPath + "/DiskLight")
diskLight.CreateIntensityAttr(1500)
diskLight.CreateAngleAttr(0.53)

# create a Cylinder light
cylinderLight = UsdLux.CylinderLight.Define(stage, defaultPrimPath + "/CylinderLight")
cylinderLight.CreateIntensityAttr(1500)
cylinderLight.CreateAngleAttr(0.53)

# create a rect light
rectLight = UsdLux.RectLight.Define(stage, defaultPrimPath + "/RectLight")
rectLight.CreateIntensityAttr(1500)
rectLight.CreateAngleAttr(0.53)

