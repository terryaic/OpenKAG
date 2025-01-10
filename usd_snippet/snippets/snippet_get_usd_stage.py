# USD/Get USD Stage
from pxr import Usd, UsdGeom
import omni.usd

stage = omni.usd.get_context().get_stage()
print(stage)
