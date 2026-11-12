# Casco 3D del perfil

Casco de stormtrooper modelado a partir de la referencia frontal aportada por el
usuario. Incluye pintura marfil con desgaste sutil, franja azul asimétrica, lentes
negras, banda del domo, mejillas, respirador y filtros con rejilla. El volumen de
los laterales y la parte posterior es una interpretación modelada de la referencia.

La geometría gira 360 grados sobre su eje vertical con cámara e iluminación fijas.

- `helmet-spin.gif`: animación transparente de 400 × 400 píxeles, 72 fotogramas,
  un giro completo cada 3 segundos y repetición continua. Es el casco del README.
- `helmet-blue-stripe.blend`: modelo editable, materiales, luces, cámara y animación.
- `../scripts/render_helmet.py`: geometría y pintura procedural; la franja azul se
  mantiene unida al volumen durante el giro.
- `../scripts/build_stormtrooper_gif.py`: ensamblador de GIF compartido, con paleta
  común y limpieza entre fotogramas para evitar estelas.

El modelo completo anterior y su script se conservan como una variante; el perfil
utiliza el nuevo casco.

## Regenerar

Entorno utilizado: Blender 4.0.2, Python 3 y Pillow.

```bash
blender -b --factory-startup --python-exit-code 1 --python scripts/render_helmet.py -- --animate
python3 scripts/build_stormtrooper_gif.py --source helmet --name helmet-spin.gif
```

Para una imagen de prueba:

```bash
blender -b --factory-startup --python-exit-code 1 --python scripts/render_helmet.py -- --preview
```

Los PNG intermedios se guardan en `output/helmet/`, fuera del control de versiones.
