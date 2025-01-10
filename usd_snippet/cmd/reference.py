# Add an external usd file into scene
import omni.kit.commands
from pxr import Sdf
import omni.usd
context = omni.usd.get_context()
omni.kit.commands.execute('CreatePayload',
	path_to=Sdf.Path('/World/Agave'),
	asset_path='http://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Vegetation/Plant_Tropical/Agave.usd',
    usd_context = context
)