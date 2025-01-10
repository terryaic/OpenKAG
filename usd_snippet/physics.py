#define a rigidbody to a prim/object
from pxr import Usd, UsdLux, UsdGeom, Sdf, Gf, Tf, UsdPhysics, PhysxSchema, UsdShade
import omni.usd
stage = omni.usd.get_context().get_stage()
defaultPrimPath = str(stage.GetDefaultPrim().GetPath())
selections = omni.usd.get_context().get_selection().get_selected_prim_paths()
prim = stage.GetPrimAtPath(selections[0])

# apply rigidbody to prim
rigidBodyAPI = UsdPhysics.RigidBodyAPI.Apply(prim)

# apply Collision to prim
UsdPhysics.CollisionAPI.Apply(prim)

# apply mass to prim
UsdPhysics.MassAPI.Apply(prim)

# apply Physics material to prim
UsdShade.Material.Define(stage, prim.GetPath())
material = UsdPhysics.MaterialAPI.Apply(prim)
density = 3e-3  # kg / cm3
staticFriction = 0.6
dynamicFriction = 0.6
material.CreateStaticFrictionAttr().Set(staticFriction)
material.CreateDynamicFrictionAttr().Set(dynamicFriction)
material.CreateDensityAttr().Set(density)