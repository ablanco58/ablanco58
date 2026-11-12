"""Render del casco original de Freddan755 (CC BY 4.0), sin remodelarlo."""
import argparse
import hashlib
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.render-deps'))
import bpy
from mathutils import Vector

parser = argparse.ArgumentParser()
parser.add_argument('--animate', action='store_true')
parser.add_argument('--preview', action='store_true')
parser.add_argument('--samples', type=int, default=12)
options = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
source = ROOT / 'assets' / 'vendor' / 'freddan755' / 'stormtrooper-helmet.glb'
assert hashlib.sha256(source.read_bytes()).hexdigest() == '245834c73f9b3b94a34463c8b47e3789bdf0a5870e6e0b55512dd9a5923ba5d2'
OUTPUT = ROOT / 'output' / 'artist-helmet'
OUTPUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(source))
objects = list(bpy.context.scene.objects)
points = [obj.matrix_world @ Vector(corner) for obj in objects if obj.type == 'MESH' for corner in obj.bound_box]
minimum = Vector(tuple(min(p[i] for p in points) for i in range(3)))
maximum = Vector(tuple(max(p[i] for p in points) for i in range(3)))
center = (minimum + maximum) / 2
scale = 2.7 / (maximum - minimum).z
turntable = bpy.data.objects.new('Freddan755 helmet turntable', None)
normalized = bpy.data.objects.new('Centered original model', None)
scene = bpy.context.scene
scene.collection.objects.link(turntable)
scene.collection.objects.link(normalized)
normalized.parent = turntable
for obj in objects:
    if obj.parent is None:
        obj.parent = normalized
normalized.scale = (scale,) * 3
normalized.location = -center * scale

scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.use_gtao = True
scene.eevee.gtao_distance = 0.10
scene.eevee.gtao_factor = 1.0
scene.eevee.taa_render_samples = options.samples
scene.eevee.use_soft_shadows = True
scene.render.resolution_x = scene.render.resolution_y = 400
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.fps = 24
scene.frame_start, scene.frame_end = 1, 72
scene.world.color = (0.18, 0.18, 0.18)
scene.view_settings.view_transform = 'AgX'


def aim(obj, target=(0, 0, 0)):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def light(name, at, energy, size, color):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.size, data.color = energy, size, color
    data.use_shadow = False
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = at
    aim(obj)


light('Upper studio softbox', (3.5, -4, 5), 450, 4, (1.0, 0.98, 0.94))
light('Front fill', (-4, -2.5, 1.5), 240, 4, (0.89, 0.94, 1.0))
light('Rear rim', (2, 4, 4), 550, 3, (0.95, 0.97, 1.0))
light('Rear fill', (-3, 3, 1), 220, 3, (1.0, 1.0, 1.0))
camera = bpy.data.objects.new('Profile camera', bpy.data.cameras.new('Profile camera'))
scene.collection.objects.link(camera)
camera.location = (0.35, -7, 0.8)
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 3.65
aim(camera)
scene.camera = camera
turntable.rotation_euler.z = 0
turntable.keyframe_insert(data_path='rotation_euler', frame=1, index=2)
turntable.rotation_euler.z = math.tau
turntable.keyframe_insert(data_path='rotation_euler', frame=73, index=2)
for curve in turntable.animation_data.action.fcurves:
    for key in curve.keyframe_points:
        key.interpolation = 'LINEAR'
scene.frame_set(1)
if options.animate:
    scene.render.filepath = str(OUTPUT / 'frame-')
    bpy.ops.render.render(animation=True)
else:
    scene.render.filepath = str(OUTPUT / 'preview.png')
    bpy.ops.render.render(write_still=True)
