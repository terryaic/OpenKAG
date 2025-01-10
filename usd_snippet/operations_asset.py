# Add usd file as payload to stage, this is used for adding the customized models, like vegetation,equipment, or other things
from pxr import UsdGeom, Sdf, Usd
import omni.usd
stage = omni.usd.get_context().get_stage()

# Create an xform which should hold all payloads in this sample
payload_prim: Usd.Prim = UsdGeom.Xform.Define(stage, Sdf.Path("/World/payload_prim")).GetPrim()
payloads: Usd.Payloads = payload_prim.GetPayloads()

# Add an fir tree
payloads.AddPayload("http://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Vegetation/Trees/Douglas_Fir.usd")

# Add an lily flower
payloads.AddPayload("http://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Vegetation/Plant_Tropical/Crane_Lily.usd")

# Add an Arm chair
payloads.AddPayload("http://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/ArchVis/Residential/Furniture/Chairs/Armchair.usd")

# Add an sofa
payloads.AddPayload("http://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/ArchVis/Residential/Furniture/FurnitureSets/Crestwood/Crestwood_Sofa.usd")
