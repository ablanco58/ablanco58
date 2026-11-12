"""Casco 3D basado en la referencia del usuario, con pintura azul asimetrica."""
import argparse
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

parser = argparse.ArgumentParser()
parser.add_argument('--animate', action='store_true')
parser.add_argument('--preview', action='store_true')
parser.add_argument('--size', type=int, default=400)
parser.add_argument('--frames', type=int, default=72)
parser.add_argument('--samples', type=int, default=16)
options = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'output' / 'helmet'
OUTPUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.use_gtao = True
scene.eevee.gtao_distance = 0.15
scene.eevee.gtao_factor = 1.15
scene.eevee.taa_render_samples = options.samples
scene.eevee.use_soft_shadows = True
scene.render.resolution_x = scene.render.resolution_y = options.size
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.fps = 24
scene.frame_start, scene.frame_end = 1, options.frames
scene.world.color = (0.22, 0.22, 0.22)
scene.view_settings.view_transform = 'AgX'
root = bpy.data.objects.new('Blue stripe helmet turntable', None)
scene.collection.objects.link(root)


def material(name, color, roughness=0.35, metallic=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    return mat


BLACK = material('Black rubber and cavities', (0.008, 0.009, 0.010), 0.46)
LENS = material('Black glass lenses', (0.0015, 0.003, 0.004), 0.22)
next(n for n in LENS.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Specular IOR Level'].default_value = 0.02
GREY = material('Dark graphite', (0.085, 0.090, 0.085), 0.48)
METAL = material('Aerator metallic mesh', (0.24, 0.27, 0.27), 0.38, 0.55)
BLUE = material('Blue cheek vent paint', (0.018, 0.063, 0.13), 0.40)
PAINT = material('Aged ivory shell with asymmetric blue stripe', (0.78, 0.79, 0.73), 0.32)

# Coordenadas comunes al casco: la franja sigue un volumen real durante el giro.
nodes, links = PAINT.node_tree.nodes, PAINT.node_tree.links
shader = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
coords = nodes.new('ShaderNodeTexCoord')
coords.object = root
xyz = nodes.new('ShaderNodeSeparateXYZ')
links.new(coords.outputs['Object'], xyz.inputs[0])


def math_node(operation, a, b=None):
    node = nodes.new('ShaderNodeMath')
    node.operation = operation
    for index, value in enumerate((a, b)):
        if value is None:
            continue
        if isinstance(value, (float, int)):
            node.inputs[index].default_value = value
        else:
            links.new(value, node.inputs[index])
    return node.outputs[0]


# Se estrecha y desplaza ligeramente hacia el centro al bajar por el rostro.
lower = math_node('MAXIMUM', math_node('SUBTRACT', 0.4, xyz.outputs['Z']), 0.0)
lower = math_node('MINIMUM', lower, 1.35)
center = math_node('ADD', -0.39, math_node('MULTIPLY', lower, 0.085))
width = math_node('SUBTRACT', 0.19, math_node('MULTIPLY', lower, 0.085))
distance = math_node('ABSOLUTE', math_node('SUBTRACT', xyz.outputs['X'], center))
band = math_node('LESS_THAN', distance, width)
paint = nodes.new('ShaderNodeMixRGB')
paint.inputs[1].default_value = (0.78, 0.79, 0.735, 1)
paint.inputs[2].default_value = (0.018, 0.065, 0.14, 1)
links.new(band, paint.inputs[0])

# Desgaste sutil de superficie, sin usar la fotografia como una tarjeta plana.
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 34
noise.inputs['Detail'].default_value = 3
noise.inputs['Roughness'].default_value = 0.7
links.new(coords.outputs['Object'], noise.inputs['Vector'])
wear = nodes.new('ShaderNodeValToRGB')
wear.color_ramp.elements[0].position = 0.62
wear.color_ramp.elements[0].color = (0, 0, 0, 1)
wear.color_ramp.elements[1].position = 0.80
wear.color_ramp.elements[1].color = (0.45, 0.45, 0.45, 1)
links.new(noise.outputs['Fac'], wear.inputs[0])
grime = nodes.new('ShaderNodeMixRGB')
links.new(wear.outputs['Color'], grime.inputs[0])
links.new(paint.outputs[0], grime.inputs[1])
grime.inputs[2].default_value = (0.31, 0.29, 0.23, 1)
links.new(grime.outputs[0], shader.inputs['Base Color'])


def finish(obj, name, mat=PAINT, smooth=True, bevel=0):
    obj.name = name
    obj.parent = root
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons:
        polygon.use_smooth = smooth
    if bevel:
        mod = obj.modifiers.new('Rounded shell edges', 'BEVEL')
        mod.width, mod.segments = bevel, 3
        obj.modifiers.new('Weighted surface normals', 'WEIGHTED_NORMAL')
        if hasattr(obj.data, 'use_auto_smooth'):
            obj.data.use_auto_smooth = True
    return obj


def oval(name, at, scale, mat=PAINT):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=32, location=at)
    obj = bpy.context.object
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, name, mat)


def box(name, at, dimensions, mat=PAINT, bevel=0.04):
    bpy.ops.mesh.primitive_cube_add(size=1, location=at)
    obj = bpy.context.object
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, name, mat, False, bevel)


def tube(name, points, radius, mat=PAINT, cyclic=False):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 2
    curve.bevel_depth = radius
    curve.bevel_resolution = 4
    path = curve.splines.new('POLY')
    path.points.add(len(points) - 1)
    for point, xyz in zip(path.points, points):
        point.co = (*xyz, 1)
    path.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, curve)
    scene.collection.objects.link(obj)
    obj.parent = root
    curve.materials.append(mat)
    return obj


def mesh(name, vertices, faces, mat=PAINT, smooth=True, bevel=0, front=False):
    if front:
        faces = [tuple(reversed(face)) if (
            Vector(vertices[face[1]]) - Vector(vertices[face[0]])).cross(
            Vector(vertices[face[2]]) - Vector(vertices[face[0]])).y > 0 else face for face in faces]
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    return finish(obj, name, mat, smooth, bevel)


def plate(name, points, mat=PAINT, depth=0.04, bevel=0.025):
    n = len(points)
    vertices = points + [(x, y + depth, z) for x, y, z in points]
    face = tuple(range(n))
    if (Vector(points[1]) - Vector(points[0])).cross(Vector(points[2]) - Vector(points[0])).y > 0:
        face = tuple(reversed(face))
    faces = [face, tuple(index + n for index in reversed(face))]
    faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    return mesh(name, vertices, faces, mat, False, bevel)


def cylinder(name, start, end, radius, mat, bevel=0.008):
    delta = Vector(end) - Vector(start)
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=radius, depth=delta.length,
        location=(Vector(start) + Vector(end)) / 2)
    obj = bpy.context.object
    obj.rotation_euler = delta.to_track_quat('Z', 'Y').to_euler()
    return finish(obj, name, mat, True, bevel)


oval('Helmet shell', (0, 0.065, 0.30), (1.015, 0.83, 1.12))
oval('Lower rear skirt', (0, 0.25, -0.37), (0.90, 0.68, 0.48))
# Banda negra que separa el domo de los ojos y rodea los laterales.
tube('Continuous black brow seal', [(1.0 * math.cos(i * math.tau / 128),
    0.065 + 0.815 * math.sin(i * math.tau / 128), 0.57) for i in range(128)], 0.043, BLACK, True)

for side in (-1, 1):
    eye = [(side * 0.14, -0.988, 0.365), (side * 0.78, -0.795, 0.405),
        (side * 0.72, -0.893, 0.075), (side * 0.56, -0.968, 0.015),
        (side * 0.28, -1.032, 0.095)]
    plate('Angular black eye lens', eye, LENS, bevel=0.055)
    tube('Raised eye socket rim', [(x, y + 0.015, z) for x, y, z in eye], 0.026, PAINT, True)
    panel_rows = [(0.09, 0.16, 0.86, -0.99, -0.77),
        (-0.12, 0.22, 0.88, -1.13, -0.85), (-0.25, 0.34, 0.90, -1.17, -0.87),
        (-0.42, 0.51, 0.94, -1.08, -0.90)]
    panel_vertices = []
    for row_index, (z, inner, outer, y_inner, y_outer) in enumerate(panel_rows):
        for j in range(17):
            t = j / 16
            panel_vertices.append((side * (inner * (1-t) + outer*t),
                y_inner*(1-t) + y_outer*t - 0.025*math.sin(t*math.pi),
                z - (0.10*math.sin(t*math.pi) if row_index == 0 else 0)))
    panel_faces = [(r*17+j, r*17+j+1, (r+1)*17+j+1, (r+1)*17+j)
        for r in range(3) for j in range(16)]
    panel = mesh('Continuous cheekbone mask', panel_vertices, panel_faces, front=True)
    panel.modifiers.new('Sculpted cheek surface', 'SUBSURF').levels = 2
    panel.modifiers.new('Cheek shell thickness', 'SOLIDIFY').thickness = 0.11
    oval('Cheek transition volume', (side * 0.59, -0.79, -0.25), (0.25, 0.21, 0.30))
    cheek = oval('Sweeping cheek shell', (side * 0.84, -0.51, -0.35), (0.28, 0.31, 0.64))
    cheek.rotation_euler.y = side * 0.30
    oval('Flared lower cheek', (side * 0.76, -0.65, -0.72), (0.33, 0.37, 0.30))
    # Rejillas azules de cada mejilla.
    for i in range(9):
        z = -0.30 - i * 0.035
        y = -0.833 + i * 0.011
        tube('Blue cheek vent', [(side * 0.91, y, z + 0.045),
            (side * 1.025, y + 0.045, z - 0.025)], 0.009, BLUE)
    # Filtros inferiores con una malla metalica visible dentro del alojamiento.
    cx, cz = side * 0.64, -0.755
    cylinder('Aerator white outer housing', (cx, -0.83, cz), (cx, -1.12, cz), 0.164, PAINT)
    cylinder('Aerator black recess', (cx, -1.121, cz), (cx, -1.133, cz), 0.126, BLACK)
    cylinder('Aerator metal backing', (cx, -1.134, cz), (cx, -1.142, cz), 0.086, METAL)
    for j in range(-4, 5):
        offset = j * 0.019
        span = math.sqrt(max(0, 0.084 ** 2 - offset ** 2))
        tube('Aerator mesh horizontal', [(cx - span, -1.149, cz + offset),
            (cx + span, -1.149, cz + offset)], 0.0035, BLACK)
        tube('Aerator mesh vertical', [(cx + offset, -1.151, cz - span),
            (cx + offset, -1.151, cz + span)], 0.0035, BLACK)
    cylinder('Ear black rim', (side * 0.97, 0.03, 0.18),
        (side * 1.10, 0.03, 0.18), 0.18, BLACK)
    cylinder('Ear armor cap', (side * 1.095, 0.03, 0.18),
        (side * 1.125, 0.03, 0.18), 0.135, PAINT)
    box('Ear control block', (side * 1.136, -0.005, 0.16), (0.035, 0.12, 0.17), GREY, 0.012)

# Nariz continua que avanza hacia el respirador.
rows = [(0.40, 0.115, -0.985), (0.24, 0.14, -1.06), (0.05, 0.19, -1.14),
    (-0.13, 0.24, -1.20), (-0.25, 0.35, -1.20)]
vertices = []
for z, width, y in rows:
    vertices += [(width * (j / 16 * 2 - 1), y + 0.075 * (j / 16 * 2 - 1) ** 2, z)
        for j in range(17)]
faces = [(r * 17 + j, r * 17 + j + 1, (r + 1) * 17 + j + 1, (r + 1) * 17 + j)
    for r in range(len(rows) - 1) for j in range(16)]
nose = mesh('Sculpted nose bridge', vertices, faces, front=True)
mod = nose.modifiers.new('Smooth nose contours', 'SUBSURF')
mod.levels = 2

# Boca en arco: cavidad oscura y separadores blancos siguiendo la curvatura.
mouth = []
for i in range(41):
    x = -0.63 + i * 1.26 / 40
    mouth.append((x, -1.205 + 0.15 * abs(x / 0.63), -0.23 - 0.29 * abs(x / 0.63) ** 1.25))
tube('Recessed frown grille', mouth, 0.055, GREY)
for i in range(-5, 6):
    x = i * 0.105
    z = -0.23 - 0.29 * abs(x / 0.63) ** 1.25
    y = -1.205 + 0.15 * abs(x / 0.63)
    tooth = box('Frown grille separator', (x, y - 0.012, z), (0.035, 0.09, 0.115), PAINT, 0.009)
    tooth.rotation_euler.y = -math.copysign(0.35, x) if x else 0

# Menton frontal ancho, con la abertura negra central del respirador inferior.
vertices = []
for row in range(9):
    t = row / 8
    for j in range(49):
        x = -0.84 + j * 1.68 / 48
        top = -0.325 - 0.29 * abs(x / 0.84) ** 1.35
        bottom = -0.91 + 0.32 * math.exp(-(x / 0.27) ** 4)
        z = top * (1 - t) + bottom * t
        y = -1.22 + 0.26 * (x / 0.84) ** 2 + 0.045 * math.sin(t * math.pi)
        vertices.append((x, y, z))
faces = [(r * 49 + j, r * 49 + j + 1, (r + 1) * 49 + j + 1, (r + 1) * 49 + j)
    for r in range(8) for j in range(48)]
chin = mesh('Broad curved chin armor', vertices, faces, front=True)
mod = chin.modifiers.new('Shell thickness', 'SOLIDIFY')
mod.thickness = 0.055
box('Central black lower respirator', (0, -1.04, -0.82), (0.38, 0.22, 0.43), BLACK, 0.12)
for i in range(-3, 4):
    oval('Lower respirator vertical rib', (i * 0.043, -1.17, -0.82), (0.019, 0.035, 0.18), GREY)
tube('Rear black lower seal', [(0.87 * math.cos(i * math.tau / 96),
    0.18 + 0.66 * math.sin(i * math.tau / 96), -0.66) for i in range(96)], 0.035, BLACK, True)
for side in (-1, 1):
    box('Rear vent inset', (side * 0.39, 0.816, 0.08), (0.31, 0.035, 0.13), GREY, 0.025)
    for i in range(5):
        box('Rear vent rib', (side * 0.39 + (i - 2) * 0.047, 0.843, 0.08),
            (0.016, 0.018, 0.10), BLACK, 0.005)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def light(name, at, energy, size, color):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.size, data.color = energy, size, color
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = at
    point_at(obj, (0, 0, 0.1))


light('Large upper softbox', (3, -5, 6), 500, 4, (1.0, 0.98, 0.94))
light('Soft frontal fill', (-4, -3, 2), 280, 4, (0.88, 0.94, 1.0))
light('Rear contour light', (2, 4, 4), 650, 3, (0.94, 0.97, 1.0))
light('Lower rear fill', (-3, 4, 1), 230, 3, (1.0, 1.0, 1.0))
camera = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
scene.collection.objects.link(camera)
camera.location = (0.65, -7, 1.15)
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 3.3
point_at(camera, (0, -0.10, 0.18))
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
    (ROOT / 'assets').mkdir(exist_ok=True)
    scene.render.filepath = '//helmet-frame-'
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'assets' / 'helmet-blue-stripe.blend'), compress=True)
    scene.render.filepath = str(OUTPUT / 'frame-')
    bpy.ops.render.render(animation=True)
else:
    scene.render.filepath = str(OUTPUT / 'preview.png')
    bpy.ops.render.render(write_still=True)
