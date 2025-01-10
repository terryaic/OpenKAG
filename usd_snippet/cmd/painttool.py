
# add some cubes into the scene, you can change the paint_candicator to your asset path
import omni.kit.commands

omni.kit.commands.execute('ScatterBrushPaintCommand',
	instancing_type='Point Instancing',
	paint_candicator={'https://omniverse-content-production.s3.us-west-2.amazonaws.com/Assets/Extensions/Samples/Paint/cube.usd': []},
	out_paint_asset_prims=[])
