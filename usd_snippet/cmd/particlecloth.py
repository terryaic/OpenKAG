#create a physcis cloth
from omni.physx.scripts import physicsUtils, particleUtils
from pxr import UsdGeom, Gf, Sdf, UsdPhysics, UsdShade
import omni
import omni.usd
import omni.kit.commands
from baseutils import create_pbd_material, setup_physics_scene

stage = omni.usd.get_context().get_stage()
defaultPrimPath = str(stage.GetDefaultPrim().GetPath())
particle_system_path = defaultPrimPath + "/particleSystem"

# create a mesh that is turned into a cloth
plane_resolution = 100
plane_width = 200.0 #replace this var with the user prompt

# size rest offset according to plane resolution and width so that particles are just touching at rest
radius = 0.5 * (plane_width / plane_resolution)
restOffset = radius
contactOffset = restOffset * 1.5

# add Physics scene
scene = setup_physics_scene(stage)

# add physics particle system
particleUtils.add_physx_particle_system(
    stage=stage,
    particle_system_path=particle_system_path,
    contact_offset=contactOffset,
    rest_offset=restOffset,
    particle_contact_offset=contactOffset,
    solid_rest_offset=restOffset,
    fluid_rest_offset=0.0,
    solver_position_iterations=16,
    simulation_owner=scene.GetPath(),
)

# create cloth mesh
success, cloth_mesh_path = omni.kit.commands.execute(
    "CreateMeshPrimWithDefaultXform",
    prim_type="Plane",
    u_patches=plane_resolution,
    v_patches=plane_resolution,
    u_verts_scale=1,
    v_verts_scale=1,
    half_scale=0.5 * plane_width,
)
cloth_mesh = UsdGeom.Mesh.Get(stage, cloth_mesh_path)
physicsUtils.setup_transform_as_scale_orient_translate(cloth_mesh)
physicsUtils.set_or_add_translate_op(cloth_mesh, Gf.Vec3f(0.0, 200.0, 000.0))
physicsUtils.set_or_add_orient_op(cloth_mesh, Gf.Quatf(1, Gf.Vec3f(0.0, 0.0, 0.0)))
physicsUtils.set_or_add_scale_op(cloth_mesh, Gf.Vec3f(1.0))

# create particle material and assign it to the system:
particle_material_path = defaultPrimPath + "/particleMaterial"
particleUtils.add_pbd_particle_material(stage, particle_material_path)
# add some drag and lift to get aerodynamic effects
particleUtils.add_pbd_particle_material(stage, particle_material_path, drag=0.1, lift=0.3, friction=0.6)
physicsUtils.add_physics_material_to_prim(
    stage, stage.GetPrimAtPath(particle_system_path), particle_material_path
)

# configure as cloth
stretchStiffness = 10000.0
bendStiffness = 200.0
shearStiffness = 100.0
damping = 0.2
particleUtils.add_physx_particle_cloth(
    stage=stage,
    path=cloth_mesh_path,
    dynamic_mesh_path=None,
    particle_system_path=particle_system_path,
    spring_stretch_stiffness=stretchStiffness,
    spring_bend_stiffness=bendStiffness,
    spring_shear_stiffness=shearStiffness,
    spring_damping=damping,
    self_collision=True,
    self_collision_filter=True,
)

# configure mass:
particle_mass = 0.02
num_verts = len(cloth_mesh.GetPointsAttr().Get())
mass = particle_mass * num_verts
massApi = UsdPhysics.MassAPI.Apply(cloth_mesh.GetPrim())
massApi.GetMassAttr().Set(mass)

# add render material:
material_path = create_pbd_material(stage, "OmniPBR")
omni.kit.commands.execute(
    "BindMaterialCommand", prim_path=cloth_mesh_path, material_path=material_path, strength=None
)
