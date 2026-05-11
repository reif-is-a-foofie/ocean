"""
Rainbow canal bridge optical system — Blender 4.0 procedural scene.
Run inside Blender: Text Editor > Open > Run Script, or:
  blender --background --python rainbow_bridge_canal.py
"""
import math

import bpy
from mathutils import Vector

# ---------------------------------------------------------------------------
# Scene constants (chamber 1.8 m tall; deck top / GLASS_PANEL aligned)
# ---------------------------------------------------------------------------
# Chamber void: Z in [CHAMBER_Z0, CHAMBER_Z1]. Deck top = CHAMBER_Z1 so the
# sealed box and skylight glass share the same Z; deck mass extended upward
# from the old 2.5 m top (glass was Z=2.5) — minimal change below deck floor.
CHAMBER_Z0 = 2.0
CHAMBER_Z1 = 3.8  # 2.0 + 1.8 m optical height
DECK_TOP = CHAMBER_Z1
DECK_BOTTOM = 1.85
PRISM_PIVOT_X = 1.5
PRISM_YAW_DEG = 73.0
FIRST_WATER_X = 22.9
SECOND_WATER_X = 45.8
BEAM_ELEV_DEG = 5.0  # path in XZ: (cos θ, 0, -sin θ) toward water
CANAL_WIDTH_Y = 8.0

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)
    for img in bpy.data.images:
        bpy.data.images.remove(img)


def new_material(name):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat


def set_principled_transmission(bsdf, value):
    """Blender 4.2+ renamed Transmission -> Transmission Weight on Principled BSDF."""
    key = "Transmission Weight" if "Transmission Weight" in bsdf.inputs else "Transmission"
    bsdf.inputs[key].default_value = value


def set_principled_specular_level(principled, value):
    """Zero spec for matte canal floor; API name varies slightly by version."""
    for key in ("Specular", "Specular IOR Level"):
        if key in principled.inputs:
            principled.inputs[key].default_value = value
            break


def add_output_nodes(mat, surface=None, volume=None):
    """Connect a surface and/or volume shader; each arg may be a node or a shader socket."""
    nt = mat.node_tree
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (400, 0)
    if surface is not None:
        src = surface.outputs[0] if hasattr(surface, "outputs") else surface
        nt.links.new(src, out.inputs["Surface"])
    if volume is not None:
        src = volume.outputs[0] if hasattr(volume, "outputs") else volume
        nt.links.new(src, out.inputs["Volume"])
    return out


def new_object(name, mesh):
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def look_at(obj, eye: Vector, target: Vector):
    """Set world matrix so obj's -Z points from eye to target (camera convention)."""
    direction = (target - eye).normalized()
    # Camera -Z forward
    quat = direction.to_track_quat("-Z", "Y")
    obj.location = eye
    obj.rotation_euler = quat.to_euler()


def prism_east_exit_point(prism_obj):
    """Approximate exit on +X side of rotated prism from world bound box."""
    bpy.context.view_layer.update()
    mw = prism_obj.matrix_world
    corners = [mw @ Vector(c) for c in prism_obj.bound_box]
    max_x = max(c.x for c in corners)
    east = [c for c in corners if (max_x - c.x) < 0.05]
    if not east:
        east = corners
    return sum(east, Vector((0.0, 0.0, 0.0))) / len(east)


def beam_path_from_landing(land_xyz, z_exit, elev_deg, land_x):
    """Ray at elev_deg below horizontal in +X that hits (land_x, 0, 0) from height z_exit."""
    el = math.radians(elev_deg)
    d = Vector((math.cos(el), 0.0, -math.sin(el)))
    land = Vector((land_x, 0.0, land_xyz))
    L = z_exit / math.sin(el)
    start = land - d * L
    length = (land - start).length
    mid = (start + land) * 0.5
    return start, land, d, length, mid


def band_angle_spread_deg():
    """Seven spectral paths: small fan around BEAM_ELEV_DEG (matches prior band spread idea)."""
    n = 7
    spread = 0.5
    lo = BEAM_ELEV_DEG - spread * 0.5
    return [lo + spread * i / (n - 1) for i in range(n)]


# ---------------------------------------------------------------------------
# CANAL GEOMETRY
# ---------------------------------------------------------------------------
# Canal: 60 m along X (east-west), 8 m wide along Y (north-south).
# Water Z=0; walls extended upward for raised deck / chamber.


def build_canal_walls():
    mat = new_material("MasonryWall")
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (0, 0)
    principled.inputs["Base Color"].default_value = (0.04, 0.04, 0.04, 1.0)
    principled.inputs["Roughness"].default_value = 0.7
    brick = nodes.new("ShaderNodeTexBrick")
    brick.location = (-500, 200)
    brick.inputs["Color1"].default_value = (0.08, 0.08, 0.08, 1.0)
    brick.inputs["Color2"].default_value = (0.12, 0.12, 0.12, 1.0)
    brick.inputs["Mortar Size"].default_value = 0.08
    brick.inputs["Mortar Smooth"].default_value = 0.15
    brick.inputs["Bias"].default_value = 0.0
    brick.inputs["Brick Width"].default_value = 0.45
    brick.inputs["Row Height"].default_value = 0.18
    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-800, 200)
    texcoord = nodes.new("ShaderNodeTexCoord")
    texcoord.location = (-1050, 200)
    normal_map = nodes.new("ShaderNodeNormalMap")
    normal_map.location = (-200, -150)
    normal_map.inputs["Strength"].default_value = 0.35
    bump = nodes.new("ShaderNodeBump")
    bump.location = (-400, -150)
    bump.inputs["Strength"].default_value = 0.25
    links.new(texcoord.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], brick.inputs["Vector"])
    links.new(brick.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], normal_map.inputs["Color"])
    links.new(normal_map.outputs["Normal"], principled.inputs["Normal"])
    add_output_nodes(mat, surface=principled.outputs["BSDF"])

    # Four segments: north/south × two halves along X for manageable meshes.
    half = 30.0
    thick = 1.0
    wall_h = max(4.5, DECK_TOP + 0.5)
    y_south_outer = -4.0 - thick / 2.0
    y_north_outer = 4.0 + thick / 2.0

    def wall_box(name, cx, cy, cz, lx, ly, lz):
        bpy.ops.mesh.primitive_cube_add(size=2.0, location=(cx, cy, cz))
        o = bpy.context.active_object
        o.name = name
        o.scale = (lx / 2.0, ly / 2.0, lz / 2.0)
        bpy.ops.object.transform_apply(scale=True)
        o.data.materials.append(mat)
        return o

    zc = wall_h / 2.0
    for i, x0 in enumerate((-15.0, 15.0)):
        wall_box(f"WallSouth_{i}", x0, y_south_outer, zc, half, thick, wall_h)
        wall_box(f"WallNorth_{i}", x0, y_north_outer, zc, half, thick, wall_h)


# ---------------------------------------------------------------------------
# BRIDGE DECK
# ---------------------------------------------------------------------------
# Deck at X=0: 4 m E-W, 8 m N-S; top Z=DECK_TOP (matches chamber roof / glass).


def build_bridge_deck():
    mat = new_material("BridgeDeckStone")
    nt = mat.node_tree
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = (0.78, 0.78, 0.76, 1.0)
    p.inputs["Roughness"].default_value = 0.85
    add_output_nodes(mat, surface=p.outputs["BSDF"])

    cz = (DECK_BOTTOM + DECK_TOP) / 2.0
    dz = DECK_TOP - DECK_BOTTOM
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 0.0, cz))
    deck = bpy.context.active_object
    deck.name = "BRIDGE_DECK"
    deck.scale = (4.0 / 2.0, CANAL_WIDTH_Y / 2.0, dz / 2.0)
    bpy.ops.object.transform_apply(scale=True)
    deck.data.materials.append(mat)
    return deck


# ---------------------------------------------------------------------------
# OPTICAL CHAMBER
# ---------------------------------------------------------------------------
# Sealed rectangular void: 4.0 m (X) × 1.8 m (Z) × 8.0 m (Y),
# bottom Z=CHAMBER_Z0. Fresnel, cylindrical lens, prism, lamps, beams.


# ---------------------------------------------------------------------------
# FRESNEL LENS
# ---------------------------------------------------------------------------
# Plane on west face X=-2, 8 m (Y) × chamber height (Z), glass blue tint.


def build_fresnel_lens():
    mat = new_material("GlassFresnel")
    nt = mat.node_tree
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = (0.92, 0.95, 1.0, 1.0)
    p.inputs["Roughness"].default_value = 0.0
    p.inputs["IOR"].default_value = 1.5
    set_principled_transmission(p, 1.0)
    p.inputs["Metallic"].default_value = 0.0
    add_output_nodes(mat, surface=p.outputs["BSDF"])

    z0, z1 = CHAMBER_Z0, CHAMBER_Z1
    verts = [
        (-2.0, -4.0, z0),
        (-2.0, 4.0, z0),
        (-2.0, 4.0, z1),
        (-2.0, -4.0, z1),
    ]
    faces = [(0, 1, 2, 3)]
    mesh = bpy.data.meshes.new("FresnelLensMesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    o = new_object("FRESNEL_LENS", mesh)
    o.data.materials.append(mat)
    return o


# ---------------------------------------------------------------------------
# CYLINDRICAL LENS
# ---------------------------------------------------------------------------
# Plane at X=-0.5, 8 × chamber height, yellow-tint glass, transmission 0.95.


def build_cylindrical_lens():
    mat = new_material("GlassCylindrical")
    nt = mat.node_tree
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = (1.0, 0.98, 0.88, 1.0)
    p.inputs["Roughness"].default_value = 0.0
    p.inputs["IOR"].default_value = 1.5
    set_principled_transmission(p, 0.95)
    add_output_nodes(mat, surface=p.outputs["BSDF"])

    z0, z1 = CHAMBER_Z0, CHAMBER_Z1
    verts = [
        (-0.5, -4.0, z0),
        (-0.5, 4.0, z0),
        (-0.5, 4.0, z1),
        (-0.5, -4.0, z1),
    ]
    faces = [(0, 1, 2, 3)]
    mesh = bpy.data.meshes.new("CylindricalLensMesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    o = new_object("CYLINDRICAL_LENS", mesh)
    o.data.materials.append(mat)
    return o


# ---------------------------------------------------------------------------
# PRISM
# ---------------------------------------------------------------------------
# Triangle in XZ at X=PRISM_PIVOT_X, base CHAMBER_Z0, apex CHAMBER_Z1;
# extrude 8 m along Y. Origin at base center; yaw toward west around +Y.


def build_prism():
    mat = new_material("GlassBK7Prism")
    nt = mat.node_tree
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = (0.92, 1.0, 0.94, 1.0)
    p.inputs["Roughness"].default_value = 0.0
    p.inputs["IOR"].default_value = 1.517
    set_principled_transmission(p, 1.0)
    p.inputs["Metallic"].default_value = 0.0
    add_output_nodes(mat, surface=p.outputs["BSDF"])

    x0 = PRISM_PIVOT_X
    half_w = 0.32 / 2.0
    z_base = CHAMBER_Z0
    z_apex = CHAMBER_Z1
    verts = [
        (x0 - half_w, -4.0, z_base),
        (x0 + half_w, -4.0, z_base),
        (x0, -4.0, z_apex),
        (x0 - half_w, 4.0, z_base),
        (x0 + half_w, 4.0, z_base),
        (x0, 4.0, z_apex),
    ]
    faces = [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (0, 2, 5, 3), (1, 4, 5, 2)]
    mesh = bpy.data.meshes.new("PrismMesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    o = new_object("PRISM_BK7", mesh)
    o.data.materials.append(mat)

    # Pivot at base center (X,Z) = (x0, z_base); geometry in local space.
    for v in o.data.vertices:
        v.co.x -= x0
        v.co.z -= z_base
    o.data.update()
    o.location = (x0, 0.0, z_base)
    o.rotation_euler = (0.0, math.radians(PRISM_YAW_DEG), 0.0)
    return o


# ---------------------------------------------------------------------------
# BEAM WHITE
# ---------------------------------------------------------------------------
# Volume slab along 5° XZ path from prism exit region to first water contact.


def build_beam_white(prism_obj):
    mat = new_material("BeamWhiteVol")
    nt = mat.node_tree
    vp = nt.nodes.new("ShaderNodeVolumePrincipled")
    vp.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    vp.inputs["Density"].default_value = 0.12
    vp.inputs["Anisotropy"].default_value = 0.0
    vp.inputs["Emission Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    vp.inputs["Emission Strength"].default_value = 5.0
    add_output_nodes(mat, volume=vp.outputs["Volume"])

    exit_pt = prism_east_exit_point(prism_obj)
    z_exit = max(exit_pt.z, 0.05)
    _, _, d, length, mid = beam_path_from_landing(0.0, z_exit, BEAM_ELEV_DEG, FIRST_WATER_X)

    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(mid.x, 0.0, mid.z))
    o = bpy.context.active_object
    o.name = "BEAM_WHITE"
    o.scale = (length / 2.0, CANAL_WIDTH_Y / 2.0, 0.01 / 2.0)
    bpy.ops.object.transform_apply(scale=True)
    q = Vector((1.0, 0.0, 0.0)).rotation_difference(d)
    o.rotation_euler = q.to_euler()
    o.data.materials.append(mat)
    return o


# ---------------------------------------------------------------------------
# SPECTRUM BANDS (first segment)
# ---------------------------------------------------------------------------


def build_spectrum_bands(prism_obj, emission_scale=1.0):
    specs = [
        ("BAND_VIOLET", (0.686, 0.322, 0.871), 4.0),
        ("BAND_INDIGO", (0.345, 0.337, 0.820), 4.0),
        ("BAND_BLUE", (0.0, 0.478, 1.0), 4.0),
        ("BAND_GREEN", (0.204, 0.780, 0.349), 4.0),
        ("BAND_YELLOW", (1.0, 0.800, 0.0), 4.0),
        ("BAND_ORANGE", (1.0, 0.584, 0.0), 4.0),
        ("BAND_RED", (1.0, 0.231, 0.188), 4.0),
    ]
    angles = band_angle_spread_deg()
    exit_pt = prism_east_exit_point(prism_obj)
    z_exit = max(exit_pt.z, 0.05)
    objects = []

    for i, ((name, rgb, strength), ang_deg) in enumerate(zip(specs, angles)):
        start, land, d, length, mid = beam_path_from_landing(0.0, z_exit, ang_deg, FIRST_WATER_X)

        mat = new_material(f"Mat_{name}")
        nt = mat.node_tree
        vp = nt.nodes.new("ShaderNodeVolumePrincipled")
        vp.inputs["Color"].default_value = (*rgb, 1.0)
        vp.inputs["Density"].default_value = 0.08
        vp.inputs["Emission Color"].default_value = (*rgb, 1.0)
        vp.inputs["Emission Strength"].default_value = strength * emission_scale
        add_output_nodes(mat, volume=vp.outputs["Volume"])

        bpy.ops.mesh.primitive_cube_add(size=2.0, location=(mid.x, 0.0, mid.z))
        o = bpy.context.active_object
        o.name = name
        o.scale = (length / 2.0, CANAL_WIDTH_Y / 2.0, 0.01 / 2.0)
        bpy.ops.object.transform_apply(scale=True)
        q = Vector((1.0, 0.0, 0.0)).rotation_difference(d)
        o.rotation_euler = q.to_euler()
        o.data.materials.append(mat)
        objects.append(o)
    return objects


# ---------------------------------------------------------------------------
# SPECTRUM BANDS (second segment after bounce)
# ---------------------------------------------------------------------------
# From first water contact toward SECOND_WATER_X; emission 50% of first pass.


def build_spectrum_bands_bounce(emission_scale=0.5):
    specs = [
        ("BAND2_VIOLET", (0.686, 0.322, 0.871), 4.0),
        ("BAND2_INDIGO", (0.345, 0.337, 0.820), 4.0),
        ("BAND2_BLUE", (0.0, 0.478, 1.0), 4.0),
        ("BAND2_GREEN", (0.204, 0.780, 0.349), 4.0),
        ("BAND2_YELLOW", (1.0, 0.800, 0.0), 4.0),
        ("BAND2_ORANGE", (1.0, 0.584, 0.0), 4.0),
        ("BAND2_RED", (1.0, 0.231, 0.188), 4.0),
    ]
    angles = band_angle_spread_deg()
    z0 = 0.02
    objects = []

    for i, ((name, rgb, strength), ang_deg) in enumerate(zip(specs, angles)):
        el = math.radians(ang_deg)
        d = Vector((math.cos(el), 0.0, -math.sin(el)))
        horiz = SECOND_WATER_X - FIRST_WATER_X
        length = abs(horiz / math.cos(el))
        start = Vector((FIRST_WATER_X, 0.0, z0))
        mid = start + d * (length * 0.5)

        mat = new_material(f"Mat_{name}")
        nt = mat.node_tree
        vp = nt.nodes.new("ShaderNodeVolumePrincipled")
        vp.inputs["Color"].default_value = (*rgb, 1.0)
        vp.inputs["Density"].default_value = 0.08
        vp.inputs["Emission Color"].default_value = (*rgb, 1.0)
        vp.inputs["Emission Strength"].default_value = strength * emission_scale
        add_output_nodes(mat, volume=vp.outputs["Volume"])

        bpy.ops.mesh.primitive_cube_add(size=2.0, location=(mid.x, 0.0, mid.z))
        o = bpy.context.active_object
        o.name = name
        o.scale = (length / 2.0, CANAL_WIDTH_Y / 2.0, 0.01 / 2.0)
        bpy.ops.object.transform_apply(scale=True)
        q = Vector((1.0, 0.0, 0.0)).rotation_difference(d)
        o.rotation_euler = q.to_euler()
        o.data.materials.append(mat)
        objects.append(o)
    return objects


# ---------------------------------------------------------------------------
# GLASS_PANEL (deck skylight)
# ---------------------------------------------------------------------------


def build_glass_panel():
    mat = new_material("GlassPanelDeck")
    nt = mat.node_tree
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = (0.85, 0.95, 0.88, 1.0)
    p.inputs["Roughness"].default_value = 0.02
    p.inputs["IOR"].default_value = 1.5
    set_principled_transmission(p, 0.95)
    p.inputs["Metallic"].default_value = 0.0
    add_output_nodes(mat, surface=p.outputs["BSDF"])

    # Horizontal plane: 2.3 m X × 8 m Y on deck top (centered on chamber in X).
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, 0.0, DECK_TOP))
    o = bpy.context.active_object
    o.name = "GLASS_PANEL"
    o.scale = (2.3, CANAL_WIDTH_Y, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    return o


# ---------------------------------------------------------------------------
# WEIR
# ---------------------------------------------------------------------------


def build_weir():
    mat = new_material("WeirStone")
    nt = mat.node_tree
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = (0.65, 0.6, 0.5, 1.0)
    p.inputs["Roughness"].default_value = 0.9
    add_output_nodes(mat, surface=p.outputs["BSDF"])

    cx = 2.2
    thick = 0.15
    z0, z1 = -0.25, 0.0
    cz = (z0 + z1) / 2.0
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(cx, 0.0, cz))
    o = bpy.context.active_object
    o.name = "WEIR"
    o.scale = (thick / 2.0, CANAL_WIDTH_Y / 2.0, (z1 - z0) / 2.0)
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    return o


# ---------------------------------------------------------------------------
# MIST VOLUME
# ---------------------------------------------------------------------------


def build_mist_volume():
    mat = new_material("MistVolume")
    nt = mat.node_tree
    vp = nt.nodes.new("ShaderNodeVolumePrincipled")
    vp.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    vp.inputs["Density"].default_value = 0.08
    vp.inputs["Anisotropy"].default_value = 0.3
    add_output_nodes(mat, volume=vp.outputs["Volume"])

    x0, x1 = 2.2, 7.2
    z0, z1 = -0.1, 1.5
    cx = (x0 + x1) / 2.0
    cz = (z0 + z1) / 2.0
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(cx, 0.0, cz))
    o = bpy.context.active_object
    o.name = "MIST_VOLUME"
    o.scale = ((x1 - x0) / 2.0, CANAL_WIDTH_Y / 2.0, (z1 - z0) / 2.0)
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    return o


# ---------------------------------------------------------------------------
# WATER RIBBON
# ---------------------------------------------------------------------------
# Planes near first landing X for spectral read on water.


def build_water_ribbon():
    specs = [
        ("RIBBON_VIOLET", (0.686, 0.322, 0.871)),
        ("RIBBON_INDIGO", (0.345, 0.337, 0.820)),
        ("RIBBON_BLUE", (0.0, 0.478, 1.0)),
        ("RIBBON_GREEN", (0.204, 0.780, 0.349)),
        ("RIBBON_YELLOW", (1.0, 0.800, 0.0)),
        ("RIBBON_ORANGE", (1.0, 0.584, 0.0)),
        ("RIBBON_RED", (1.0, 0.231, 0.188)),
    ]
    z = 0.01
    w = 0.098
    span = w * len(specs)
    x_start = FIRST_WATER_X - span / 2.0
    objs = []
    for i, (name, rgb) in enumerate(specs):
        cx = x_start + w * (i + 0.5)
        mat = new_material(f"Mat_{name}")
        nt = mat.node_tree
        emit = nt.nodes.new("ShaderNodeEmission")
        emit.inputs["Color"].default_value = (*rgb, 1.0)
        emit.inputs["Strength"].default_value = 3.0
        add_output_nodes(mat, surface=emit.outputs["Emission"])

        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(cx, 0.0, z))
        o = bpy.context.active_object
        o.name = name
        o.scale = (w, CANAL_WIDTH_Y, 1.0)
        bpy.ops.object.transform_apply(scale=True)
        o.data.materials.append(mat)
        objs.append(o)
    return objs


# ---------------------------------------------------------------------------
# WATER SURFACE
# ---------------------------------------------------------------------------


def build_water():
    mat = new_material("WaterSurface")
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    p = nodes.new("ShaderNodeBsdfPrincipled")
    p.location = (200, 0)
    p.inputs["Base Color"].default_value = (0.05, 0.15, 0.3, 1.0)
    p.inputs["Roughness"].default_value = 0.05
    p.inputs["IOR"].default_value = 1.33
    set_principled_transmission(p, 0.6)

    texcoord = nodes.new("ShaderNodeTexCoord")
    texcoord.location = (-800, 0)
    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-600, 0)
    wave = nodes.new("ShaderNodeTexWave")
    wave.location = (-400, 0)
    wave.wave_type = "BANDS"
    wave.inputs["Scale"].default_value = 8.0
    wave.inputs["Distortion"].default_value = 1.5
    wave.inputs["Detail"].default_value = 6.0
    wave.inputs["Detail Roughness"].default_value = 0.6

    bump = nodes.new("ShaderNodeBump")
    bump.location = (-100, -200)
    bump.inputs["Strength"].default_value = 0.4

    links.new(texcoord.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], wave.inputs["Vector"])
    height_out = wave.outputs["Fac"] if "Fac" in wave.outputs else wave.outputs["Color"]
    links.new(height_out, bump.inputs["Height"])
    links.new(bump.outputs["Normal"], p.inputs["Normal"])
    add_output_nodes(mat, surface=p.outputs["BSDF"])

    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, 0.0, 0.0))
    o = bpy.context.active_object
    o.name = "WATER_SURFACE"
    o.scale = (60.0 / 2.0, CANAL_WIDTH_Y / 2.0, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    return o


# ---------------------------------------------------------------------------
# CANAL FLOOR
# ---------------------------------------------------------------------------


def build_floor():
    mat = new_material("CanalFloorLimestone")
    nt = mat.node_tree
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = (0.95, 0.95, 0.92, 1.0)
    p.inputs["Roughness"].default_value = 0.85
    set_principled_specular_level(p, 0.0)
    add_output_nodes(mat, surface=p.outputs["BSDF"])

    floor_z = -0.4
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, 0.0, floor_z))
    o = bpy.context.active_object
    o.name = "CANAL_FLOOR"
    o.scale = (60.0 / 2.0, CANAL_WIDTH_Y / 2.0, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    return o


# ---------------------------------------------------------------------------
# LIGHTING
# ---------------------------------------------------------------------------
# Sun: azimuth 270° (west), elevation 5°. Area lamp in chamber. Sky world.


def setup_lighting():
    el = math.radians(5.0)
    prop = Vector((math.cos(el), 0.0, -math.sin(el))).normalized()

    bpy.ops.object.light_add(type="SUN", location=(-80.0, 0.0, 6.0))
    sun = bpy.context.active_object
    sun.name = "SUN_Sunset"
    sun.data.energy = 4.0
    sun.data.color = (1.0, 0.82, 0.55)
    q = Vector((0.0, 0.0, -1.0)).rotation_difference(prop)
    sun.rotation_euler = q.to_euler()

    cz = (CHAMBER_Z0 + CHAMBER_Z1) / 2.0
    bpy.ops.object.light_add(type="AREA", location=(0.0, 0.0, cz))
    area = bpy.context.active_object
    area.name = "AREA_ChamberFill"
    area.data.energy = 10.0
    area.data.color = (1.0, 1.0, 1.0)
    area.data.size = 3.0
    area.data.shape = "SQUARE"

    world = bpy.context.scene.world
    world.use_nodes = True
    wnt = world.node_tree
    wnt.nodes.clear()
    bg = wnt.nodes.new("ShaderNodeBackground")
    sky = wnt.nodes.new("ShaderNodeTexSky")
    out = wnt.nodes.new("ShaderNodeOutputWorld")
    sky.sky_type = "PREETHAM"
    sky.turbidity = 3.0
    sky.sun_elevation = el
    sky.sun_rotation = math.radians(270.0)
    wnt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    wnt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    bg.inputs["Strength"].default_value = 1.0


# ---------------------------------------------------------------------------
# CAMERA
# ---------------------------------------------------------------------------


def build_cameras():
    bpy.ops.object.camera_add(location=(18.0, -14.0, 5.0))
    cam_p = bpy.context.active_object
    cam_p.name = "CAM_PERSPECTIVE"
    look_at(cam_p, Vector((18.0, -14.0, 5.0)), Vector((5.0, 0.0, 0.5)))
    cam_p.data.lens = 50.0

    bpy.ops.object.camera_add(location=(2.0, 0.0, 8.0))
    cam_bridge = bpy.context.active_object
    cam_bridge.name = "CAM_BRIDGE_TOP"
    look_at(cam_bridge, Vector((2.0, 0.0, 8.0)), Vector((2.0, 0.0, 0.0)))
    cam_bridge.data.type = "PERSP"
    cam_bridge.data.lens = 24.0

    bpy.ops.object.camera_add(location=(0.0, 0.0, 20.0))
    cam_plan = bpy.context.active_object
    cam_plan.name = "CAM_PLAN"
    look_at(cam_plan, Vector((0.0, 0.0, 20.0)), Vector((0.0, 0.0, 0.0)))
    cam_plan.data.type = "ORTHO"
    cam_plan.data.ortho_scale = 70.0

    return cam_p, cam_bridge, cam_plan


# ---------------------------------------------------------------------------
# RENDER
# ---------------------------------------------------------------------------


def setup_render(cam_perspective):
    scene = bpy.context.scene
    scene.camera = cam_perspective
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 512
    if hasattr(scene.cycles, "use_adaptive_sampling"):
        scene.cycles.use_adaptive_sampling = True
    if hasattr(scene.cycles, "adaptive_threshold"):
        scene.cycles.adaptive_threshold = 0.01
    for vl in scene.view_layers:
        vl.cycles.use_denoising = True
    scene.render.resolution_x = 2560
    scene.render.resolution_y = 1440
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = "//rainbow_bridge_render.png"

    scene.view_settings.view_transform = "Filmic"
    scene.view_settings.look = "High Contrast"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0


def main():
    clear_scene()
    build_canal_walls()
    build_bridge_deck()
    build_fresnel_lens()
    build_cylindrical_lens()
    prism = build_prism()
    build_glass_panel()
    build_beam_white(prism)
    build_spectrum_bands(prism, emission_scale=1.0)
    build_spectrum_bands_bounce(emission_scale=0.5)
    build_water_ribbon()
    build_water()
    build_floor()
    build_weir()
    build_mist_volume()
    setup_lighting()
    cam_p, _cam_bridge, _cam_plan = build_cameras()
    setup_render(cam_p)

    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
