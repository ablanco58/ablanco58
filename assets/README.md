# Stormtrooper del perfil

Modelo 3D procedural creado para este perfil: casco, armadura, traje interior,
respirador, cinturón y detalles en la espalda. La figura gira sobre su eje vertical;
la cámara permanece fija.

- `stormtrooper-spin.gif`: animación transparente de 400 × 400 píxeles, 72 fotogramas,
  un giro completo cada 3 segundos y repetición continua. Es la imagen que muestra
  el README de GitHub.
- `stormtrooper.blend`: modelo editable con geometría, materiales, luces, cámara
  y animación en el formato nativo de Blender.
- `../scripts/render_stormtrooper.py`: fuente del modelo y del render, sin modelos
  externos ni texturas descargadas.
- `../scripts/build_stormtrooper_gif.py`: ensamblado del GIF con paleta común y
  transparencia. Cada fotograma se limpia antes del siguiente para evitar estelas.

## Regenerar

Entorno utilizado: Blender 4.0.2, Python 3 y Pillow.

```bash
blender -b --factory-startup --python-exit-code 1 --python scripts/render_stormtrooper.py -- --animate
python3 scripts/build_stormtrooper_gif.py
```

Para una imagen de prueba:

```bash
blender -b --factory-startup --python-exit-code 1 --python scripts/render_stormtrooper.py -- --preview
```

Los PNG intermedios se guardan en `output/stormtrooper/`, fuera del control de versiones.
