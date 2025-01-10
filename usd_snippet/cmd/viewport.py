#raycast for object
from  omni.kit.viewport.window.raycast import perform_raycast_query
from omni.kit.viewport.utility import get_active_viewport
from typing import Sequence
viewport_api = get_active_viewport()
perform_raycast_query(
    viewport_api=viewport_api,
    mouse_ndc=(0,0),
    mouse_pixel=(0,0),
    on_complete_fn=lambda *args: query_complete(False, *args),
    query_name='omni.kit.viewport.dragdrop.DragDropHandler'
)
def query_complete(is_drop: bool, prim_path: str, world_space_pos: Sequence[float], *args):
    print(world_space_pos)