# Add an external usd file as reference into scene
from pxr import Usd, Sdf, UsdGeom
import omni.usd
stage = omni.usd.get_context().get_stage()

# Create an xform which should hold all references in this sample
ref_prim: Usd.Prim = UsdGeom.Xform.Define(stage, Sdf.Path("/World/ref_prim")).GetPrim()
references: Usd.References = ref_prim.GetReferences()
references.AddReference(
    assetPath="http://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Vegetation/Trees/Douglas_Fir.usd"
)
