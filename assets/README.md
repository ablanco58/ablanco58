# Casco 3D del perfil

El perfil utiliza **Star Wars Stormtrooper Helmet**, de
[Freddan755](https://sketchfab.com/Freddan755), con licencia
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

La geometría y los materiales son los del modelo original. Para esta presentación
se han añadido encuadre, luces de estudio y una rotación de 360 grados, renderizada
como GIF con fondo transparente.

## Archivos

- `stormtrooper-freddan755.gif`: animación del perfil, 400 × 400 píxeles,
  72 fotogramas, tres segundos por vuelta y repetición continua.
- `vendor/freddan755/stormtrooper-helmet.glb`: modelo del autor, sin modificar.
- [Créditos, licencia, procedencia y checksum](vendor/freddan755/ATTRIBUTION.md).
- `../scripts/render_artist_helmet.py`: importación y render en Blender.
- `../scripts/build_stormtrooper_gif.py`: ensamblado con paleta común y limpieza
  de los fotogramas para evitar estelas.

Los modelos procedurales anteriores se conservan como archivos históricos y no
son los que se muestran en el perfil.

## Regenerar la animación

Entorno utilizado: Blender 4.0.2 con Python 3.12, NumPy 1.26.4 y Pillow.
El importador glTF de Blender necesita NumPy. El script busca esa dependencia
en `.render-deps/`, carpeta excluida del repositorio:

```bash
python3 -m pip install --target .render-deps numpy==1.26.4
blender -b --factory-startup --python-exit-code 1 --python scripts/render_artist_helmet.py -- --animate
python3 scripts/build_stormtrooper_gif.py --source artist-helmet --name stormtrooper-freddan755.gif
```

El último comando necesita Pillow disponible en el Python que lo ejecuta.
Para renderizar una sola vista, sustituye `--animate` por `--preview`.
Los PNG intermedios quedan en `output/artist-helmet/`, fuera del control de versiones.
