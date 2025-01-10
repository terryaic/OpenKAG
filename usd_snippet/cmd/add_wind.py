#add wind into scene
from pxr import Gf
from omni.physx.scripts import particleUtils 
import omni.usd
stage = omni.usd.get_context().get_stage()
windStart= Gf.Vec3f(10,10,10)
windEnd= Gf.Vec3f(50,50,50)
windAttr = particleUtils.get_default_particle_system(stage).GetWindAttr()
print(windAttr.Get())
windAttr.Set(time=1, value=windStart)
windAttr.Set(time=1440, value=windEnd)