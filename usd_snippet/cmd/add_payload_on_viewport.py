# Add a usd file on the surface of another object/asset
from  omni.kit.viewport.window.raycast import perform_raycast_query
from omni.kit.viewport.utility import get_active_viewport
from typing import Sequence
viewport_api = get_active_viewport()
mouse_ndc = (0,0)
mouse, valid = viewport_api.map_ndc_to_texture_pixel(mouse_ndc)
perform_raycast_query(
    viewport_api=viewport_api,
    mouse_ndc=mouse_ndc,
    mouse_pixel=mouse,
    on_complete_fn=lambda *args: query_complete(*args),
    query_name='omni.kit.viewport.dragdrop.DragDropHandler'
)
def query_complete(prim_path: str, world_space_pos: Sequence[float], *args):
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
    # set the position of the new added file
    omni.kit.commands.create('TransformPrimSRTCommand', path=Sdf.Path('/World/Agave'), new_translation=world_space_pos).do()