#set the postion/roation/scale of a prim
from pxr import Usd, UsdLux, UsdGeom, Sdf, Gf, Tf, UsdPhysics
import omni.usd
stage = omni.usd.get_context().get_stage()
defaultPrimPath = str(stage.GetDefaultPrim().GetPath())

# create a cube of specific size, position, orientation, and color
size = 25.0
position = Gf.Vec3f(0.0, 0.0, 500.0)
orientation = Gf.Quatf(1.0)
color = Gf.Vec3f(71.0 / 255.0, 105.0 / 255.0, 1.0)

# create a cube
cubeGeom = UsdGeom.Cube.Define(stage, defaultPrimPath + "/Cube")

cubeGeom.CreateSizeAttr(size)
half_extent = size / 2
cubeGeom.CreateExtentAttr([(-half_extent, -half_extent, -half_extent), (half_extent, half_extent, half_extent)])

#set the cube position
if not cubeGeom.GetPrim().GetAttribute("xformOp:translate"):
    cubeGeom.AddTranslateOp().Set(position)
else:
    cubeGeom.GetPrim().GetAttribute("xformOp:translate").Set(position)

#set the cube rotation
if not cubeGeom.GetPrim().GetAttribute("xformOp:rotateXYZ"):
    cubeGeom.AddOrientOp().Set(orientation)
else:
    cubeGeom.GetPrim().GetAttribute("xformOp:rotateXYZ").Set(orientation)

#set the cube scale
if not cubeGeom.GetPrim().GetAttribute("xformOp:scale"):
    cubeGeom.AddScaleOp().Set(Gf.Vec3f(size))
else:
    cubeGeom.GetPrim().GetAttribute("xformOp:scale").Set(Gf.Vec3f(size))

#setting the color
cubeGeom.CreateDisplayColorAttr().Set([color])

# create a sphere
geom = UsdGeom.Sphere.Define(stage, defaultPrimPath + "/Sphere")

# create a Cone
geom = UsdGeom.Cone.Define(stage, defaultPrimPath + "/Cone")

# create a Cone
geom = UsdGeom.Cylinder.Define(stage, defaultPrimPath + "/Cylinder")

