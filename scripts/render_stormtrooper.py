"""Modelo procedural y turntable de un stormtrooper para el perfil.

blender -b --python scripts/render_stormtrooper.py -- --preview
blender -b --python scripts/render_stormtrooper.py -- --animate
"""
import argparse
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

args = argparse.ArgumentParser()
args.add_argument('--preview', action='store_true')
args.add_argument('--animate', action='store_true')
args.add_argument('--size', type=int, default=400)
args.add_argument('--frames', type=int, default=72)
args.add_argument('--samples', type=int, default=24)
args.add_argument('--engine', choices=['CYCLES', 'BLENDER_EEVEE'], default='BLENDER_EEVEE')
options = args.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'output' / 'stormtrooper'
OUTPUT.mkdir(parents=True, exist_ok=True)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = options.engine
scene.cycles.samples = 32
scene.cycles.use_denoising = False
scene.eevee.use_gtao = True
scene.eevee.gtao_distance = 0.18
scene.eevee.gtao_factor = 1.15
scene.eevee.taa_render_samples = options.samples
scene.eevee.use_soft_shadows = True
scene.render.threads_mode = 'FIXED'
scene.render.threads = 6
scene.render.resolution_x = options.size
scene.render.resolution_y = options.size
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.fps = 24
scene.frame_start, scene.frame_end = 1, options.frames
scene.world.color = (0.24, 0.24, 0.24)
scene.view_settings.view_transform = 'AgX'

root = bpy.data.objects.new('Stormtrooper turntable', None)
scene.collection.objects.link(root)


def material(name, color, roughness=0.32, metallic=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = next(node for node in mat.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    return mat


WHITE = material('Porcelain white armor', (0.82, 0.85, 0.89), 0.27)
BLACK = material('Black undersuit', (0.009, 0.012, 0.017), 0.60)
LENS = material('Glossy black eye lenses', (0.003, 0.008, 0.009), 0.16)
GREY = material('Graphite details', (0.12, 0.15, 0.18), 0.44)
METAL = material('Aerator centers', (0.43, 0.48, 0.53), 0.26, 0.65)


def finish(obj, name, mat, smooth=True, bevel=0):
    obj.name = name
    obj.parent = root
    obj.data.materials.append(mat)
    if smooth:
        for face in obj.data.polygons:
            face.use_smooth = True
    if bevel:
        modifier = obj.modifiers.new('Soft armor edges', 'BEVEL')
        modifier.width = bevel
        modifier.segments = 3
        modifier = obj.modifiers.new('Weighted normals', 'WEIGHTED_NORMAL')
        if hasattr(obj.data, 'use_auto_smooth'):
            obj.data.use_auto_smooth = True
    return obj


def box(name, at, dimensions, mat=WHITE, bevel=0.06):
    bpy.ops.mesh.primitive_cube_add(size=1, location=at)
    obj = bpy.context.object
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, name, mat, smooth=False, bevel=bevel)


def oval(name, at, scale, mat=WHITE):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, location=at)
    obj = bpy.context.object
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, name, mat)


def cylinder(name, start, end, radius, mat=WHITE, radius2=None, squash=1):
    direction = Vector(end) - Vector(start)
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=radius,
        radius2=radius if radius2 is None else radius2, depth=direction.length,
        location=(Vector(start) + Vector(end)) / 2)
    obj = bpy.context.object
    obj.scale.y = squash
    obj.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    return finish(obj, name, mat, bevel=0.025)


def plate(name, points, depth, mat=WHITE, bevel=0.015):
    # Puntos (x,y,z), extruidos hacia el interior del casco/cuerpo.
    vertices = points + [(x, y + depth, z) for x, y, z in points]
    n = len(points)
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    faces.extend((i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    return finish(obj, name, mat, smooth=False, bevel=bevel)


# Botas, piernas y articulaciones del traje negro.
for side in (-1, 1):
    x = side * 0.265
    box('Black sole', (x, -0.105, 0.085), (0.405, 0.66, 0.105), BLACK, 0.045)
    box('White boot', (x, -0.115, 0.235), (0.39, 0.65, 0.29), WHITE, 0.085)
    cylinder('Shin armor', (x, 0, 0.36), (x, 0.015, 1.01), 0.185, WHITE, 0.215, 1.12)
    box('Shin front seam', (x, -0.214, 0.66), (0.015, 0.012, 0.40), GREY, 0.004)
    oval('Black knee joint', (x, 0.015, 1.085), (0.183, 0.195, 0.15), BLACK)
    box('Knee plate', (x, -0.182, 1.09), (0.32, 0.16, 0.245), WHITE, 0.055)
    cylinder('Thigh armor', (x, 0.015, 1.18), (x, 0.035, 1.82), 0.20, WHITE, 0.235, 1.10)
    oval('Hip joint', (x, 0.02, 1.87), (0.20, 0.21, 0.17), BLACK)

# Pelvis, cinturon y abdomen.
box('Black pelvis', (0, 0.015, 1.91), (0.85, 0.47, 0.32), BLACK, 0.11)
plate('Codpiece', [(-0.28, -0.265, 2.025), (0.28, -0.265, 2.025),
    (0.19, -0.31, 1.74), (-0.19, -0.31, 1.74)], 0.15, WHITE, 0.06)
box('Belt backing', (0, 0, 2.105), (1.00, 0.565, 0.17), WHITE, 0.04)
for i in range(-3, 4):
    box('Belt ammunition pouch', (i * 0.13, -0.32, 2.105), (0.11, 0.095, 0.165), WHITE, 0.018)
box('Abdomen undersuit', (0, 0.015, 2.36), (0.77, 0.43, 0.48), BLACK, 0.13)
box('Abdominal plate', (0, -0.205, 2.37), (0.66, 0.19, 0.43), WHITE, 0.075)
for z in (2.29, 2.37, 2.45):
    box('Abdominal groove', (0, -0.308, z), (0.29, 0.018, 0.024), GREY, 0.006)
for x in (-0.21, 0.21):
    box('Abdominal button panel', (x, -0.311, 2.37), (0.08, 0.025, 0.24), WHITE, 0.012)
    for z in (2.30, 2.37, 2.44):
        oval('Abdominal control', (x, -0.33, z), (0.022, 0.012, 0.022), GREY)

# Pecho y espalda; los detalles posteriores se ven durante el giro.
box('Torso undersuit', (0, 0.02, 2.82), (0.98, 0.52, 0.72), BLACK, 0.18)
plate('One-piece chest plate', [(-0.49, -0.245, 3.125), (0.49, -0.245, 3.125),
    (0.515, -0.32, 2.88), (0.425, -0.345, 2.69), (0, -0.375, 2.635),
    (-0.425, -0.345, 2.69), (-0.515, -0.32, 2.88)], 0.18, WHITE, 0.065)
box('Back armor', (0, 0.255, 2.83), (0.91, 0.24, 0.62), WHITE, 0.11)
box('Back inset', (0, 0.385, 2.86), (0.45, 0.035, 0.31), GREY, 0.03)
oval('Back circular detail', (-0.11, 0.411, 2.87), (0.09, 0.018, 0.09), WHITE)
for x in (0.04, 0.12):
    box('Back raised detail', (x, 0.414, 2.87), (0.045, 0.025, 0.19), WHITE, 0.009)
cylinder('Thermal detonator', (-0.27, 0.39, 2.105), (0.27, 0.39, 2.105), 0.102, GREY)
for side in (-1, 1):
    cylinder('Detonator end cap', (side * 0.22, 0.39, 2.105), (side * 0.30, 0.39, 2.105), 0.112)

# Brazos en una postura relajada; no se añade arma.
for side in (-1, 1):
    oval('Shoulder connection', (side * 0.58, 0.01, 2.98), (0.19, 0.20, 0.20), BLACK)
    oval('Shoulder pauldron', (side * 0.64, 0, 3.005), (0.255, 0.28, 0.255))
    cylinder('Upper arm armor', (side * 0.69, 0.005, 2.87), (side * 0.77, -0.015, 2.49), 0.165, WHITE, 0.19)
    oval('Elbow undersuit', (side * 0.78, -0.015, 2.43), (0.145, 0.155, 0.13), BLACK)
    cylinder('Forearm armor', (side * 0.785, -0.025, 2.34), (side * 0.79, -0.075, 2.015), 0.16, WHITE, 0.18)
    box('Forearm panel', (side * 0.79, -0.197, 2.19), (0.19, 0.045, 0.19), WHITE, 0.025)
    oval('Black glove', (side * 0.79, -0.07, 1.92), (0.15, 0.16, 0.18), BLACK)
    box('Hand armor', (side * 0.79, -0.207, 1.965), (0.195, 0.07, 0.15), WHITE, 0.035)

# Casco: dome, visores angulares, cejas, filtros y respirador.
cylinder('Neck seal', (0, 0.01, 3.08), (0, 0.01, 3.31), 0.22, BLACK)
oval('Helmet main shell', (0, 0.025, 3.79), (0.635, 0.49, 0.665))
box('Helmet lower rear shell', (0, 0.105, 3.48), (1.05, 0.66, 0.38), WHITE, 0.16)
for side in (-1, 1):
    oval('Temple armor', (side * 0.475, -0.14, 3.74), (0.18, 0.32, 0.36))
    plate('Black angular eye lens', [(side * 0.055, -0.497, 3.865),
        (side * 0.49, -0.397, 3.90), (side * 0.405, -0.475, 3.71),
        (side * 0.105, -0.533, 3.73)], 0.045, LENS, 0.02)
    plate('Helmet brow', [(side * 0.025, -0.51, 3.955),
        (side * 0.50, -0.394, 3.975), (side * 0.51, -0.408, 3.915),
        (side * 0.025, -0.527, 3.895)], 0.035, WHITE, 0.018)
    cheek = oval('White cheek armor', (side * 0.395, -0.365, 3.50), (0.19, 0.19, 0.31))
    cheek.rotation_euler.y = side * 0.22
    for i in range(4):
        vent = box('Cheek ventilation slot', (side * (0.43 + i * 0.025), -0.508 + i * 0.022, 3.48),
            (0.016, 0.022, 0.10), GREY, 0.006)
        vent.rotation_euler.y = side * 0.30
    cylinder('Aerator black housing', (side * 0.255, -0.49, 3.34), (side * 0.255, -0.665, 3.34), 0.093, BLACK)
    cylinder('Aerator metal center', (side * 0.255, -0.661, 3.34), (side * 0.255, -0.677, 3.34), 0.061, METAL)
    for dz in (-0.027, 0, 0.027):
        box('Aerator grille', (side * 0.255, -0.684, 3.34 + dz), (0.095, 0.008, 0.008), BLACK, 0.002)
plate('Nose bridge', [(-0.045, -0.55, 3.86), (0.045, -0.55, 3.86),
    (0.15, -0.625, 3.57), (-0.15, -0.625, 3.57)], 0.10, WHITE, 0.03)
plate('Black frown respirator', [(-0.27, -0.579, 3.51), (0, -0.653, 3.64),
    (0.27, -0.579, 3.51), (0.17, -0.633, 3.43), (-0.17, -0.633, 3.43)], 0.04, GREY, 0.013)
for x in (-0.13, -0.065, 0, 0.065, 0.13):
    box('Respirator teeth', (x, -0.66 + abs(x) * 0.15, 3.52), (0.022, 0.045, 0.10), WHITE, 0.005)
oval('White chin armor', (0, -0.40, 3.29), (0.29, 0.17, 0.09))
box('Rear helmet panel', (0, 0.49, 3.73), (0.40, 0.025, 0.10), GREY, 0.02)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def area(name, at, power, size, color):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = power
    data.shape = 'DISK'
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = at
    point_at(obj, (0, 0, 2.4))


area('Large front softbox', (4, -6, 8), 650, 5, (1.0, 0.96, 0.91))
area('Cool fill', (-4, -3, 4), 420, 4, (0.83, 0.91, 1.0))
area('Upper rear rim', (2, 4, 7), 800, 4, (0.94, 0.97, 1.0))
area('Rear fill', (-3, 4, 3), 260, 4, (1.0, 1.0, 1.0))

camera = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
scene.collection.objects.link(camera)
camera.location = (5.2, -10, 5.0)
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 5.25
point_at(camera, (0, 0, 2.25))
scene.camera = camera

root.rotation_euler.z = 0
root.keyframe_insert(data_path='rotation_euler', frame=1, index=2)
root.rotation_euler.z = math.tau
root.keyframe_insert(data_path='rotation_euler', frame=options.frames + 1, index=2)
for curve in root.animation_data.action.fcurves:
    for key in curve.keyframe_points:
        key.interpolation = 'LINEAR'
scene.frame_set(1)

if options.animate:
    # El archivo nativo conserva geometria, materiales, luces y el giro animado.
    (ROOT / 'assets').mkdir(exist_ok=True)
    scene.render.filepath = '//stormtrooper-frame-'
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'assets' / 'stormtrooper.blend'), compress=True)
    scene.render.filepath = str(OUTPUT / 'frame-')
    bpy.ops.render.render(animation=True)
else:
    scene.render.filepath = str(OUTPUT / 'preview.png')
    bpy.ops.render.render(write_still=True)
