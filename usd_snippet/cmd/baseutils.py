#base utils
from pxr import UsdGeom, Gf, Sdf, UsdPhysics, UsdShade
import omni
import omni.usd
import omni.kit.commands

def setup_physics_scene_and_upaxis(stage, primPathAsString = True, metersPerUnit = 0.01, gravityMod = 1.0, upAxis = UsdGeom.Tokens.z):

    defaultPrimPath = stage.GetDefaultPrim().GetPath()

    UsdGeom.SetStageUpAxis(stage, upAxis)
    UsdGeom.SetStageMetersPerUnit(stage, metersPerUnit)

    gravityDir = Gf.Vec3f(0.0, 0.0, -1.0)
    if upAxis == UsdGeom.Tokens.y:
        gravityDir = Gf.Vec3f(0.0, -1.0, 0.0)
    if upAxis == UsdGeom.Tokens.x:
        gravityDir = Gf.Vec3f(-1.0, 0.0, 0.0)

    scene = UsdPhysics.Scene.Define(stage, defaultPrimPath.AppendPath("physicsScene"))
    scene.CreateGravityDirectionAttr().Set(gravityDir)
    scene.CreateGravityMagnitudeAttr().Set(9.81 * gravityMod / metersPerUnit)

    if primPathAsString:
        defaultPrimPath = str(defaultPrimPath)

    return (defaultPrimPath, scene)

def setup_physics_scene(stage, metersPerUnit = 0.01, gravityMod = 1.0):
    defaultPrimPath = stage.GetDefaultPrim().GetPath()
    UsdGeom.SetStageMetersPerUnit(stage, metersPerUnit)

    upAxis = UsdGeom.GetStageUpAxis(stage)

    if upAxis == UsdGeom.Tokens.z:
        gravityDir = Gf.Vec3f(0.0, 0.0, -1.0)
    if upAxis == UsdGeom.Tokens.y:
        gravityDir = Gf.Vec3f(0.0, -1.0, 0.0)
    if upAxis == UsdGeom.Tokens.x:
        gravityDir = Gf.Vec3f(-1.0, 0.0, 0.0)

    scene = UsdPhysics.Scene.Define(stage, defaultPrimPath.AppendPath("physicsScene"))
    scene.CreateGravityDirectionAttr().Set(gravityDir)
    scene.CreateGravityMagnitudeAttr().Set(9.81 * gravityMod / metersPerUnit)

    return scene

def create_pbd_material(stage, mat_name: str, color_rgb: Gf.Vec3f = Gf.Vec3f(0.2, 0.2, 0.8)) -> Sdf.Path:
    # create material for extras
    create_list = []
    omni.kit.commands.execute(
        "CreateAndBindMdlMaterialFromLibrary",
        mdl_name="OmniPBR.mdl",
        mtl_name="OmniPBR",
        mtl_created_list=create_list,
        bind_selected_prims=False,
    )
    target_path = "/World/Looks/" + mat_name
    if create_list[0] != target_path:
        omni.kit.commands.execute("MovePrims", paths_to_move={create_list[0]: target_path})
    shader = UsdShade.Shader.Get(stage, target_path + "/Shader")
    shader.CreateInput("diffuse_color_constant", Sdf.ValueTypeNames.Color3f).Set(color_rgb)
    return Sdf.Path(target_path)