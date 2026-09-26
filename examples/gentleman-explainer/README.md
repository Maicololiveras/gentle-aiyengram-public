# Gentleman: ecosistema, ODD, Engram y Gentle Shell

Presentación binaria ASCII narrada en español. El video dura **6:52** e incluye 20 escenas, música y subtítulos seleccionables.

## Abrir o editar

- `Gentleman-ecosistema-ODD-Engram-Gentle-Shell.mp4`: video final entregado junto al proyecto editable.
- `generated/index.html`: presentación Canvas interactiva producida al ejecutar el script. Ábrela desde un servidor local, por ejemplo `python -m http.server 8000`, y visita `/examples/gentleman-explainer/generated/`. Pulsa reproducir para activar el audio.
- `storyboard.json`: texto, secuencia, colores, imágenes y voz por escena.
- `timed-storyboard.json`: duraciones medidas y mezcla de voz y música para el conversor `binary-ascii present`.
- `audio/subtitulos.srt`: subtítulos y guion de voz.

Para regenerar, instala Pillow y `espeakng-loader`, conserva FFmpeg en el PATH y ejecuta `bash tools/build_explainer_video.sh` desde el repositorio. El script usa el conversor `binary_ascii` del proyecto para obtener las celdas 0/1 de las imágenes y construir el Canvas. El render del video dibuja esas mismas celdas, nunca las plantillas raster sobre el cuadro final. La voz se sintetiza sin conexión con eSpeak NG; puedes sustituir `audio/mix.m4a` por una grabación de estudio manteniendo las duraciones del manifiesto.

## Fuentes del contenido

- [Gentle AI: uso previsto y ODD](https://github.com/Gentleman-Programming/gentle-ai/blob/main/docs/intended-usage.md)
- [Gentle AI: registro de habilidades y caché](https://github.com/Gentleman-Programming/gentle-ai/blob/main/docs/usage.md)
- [Gentle Shell: TUI sobre Pi](https://github.com/Gentleman-Programming/gentle-shell)
- [Engram: herramientas MCP y protocolo de memoria](https://github.com/Gentleman-Programming/engram/blob/main/DOCS.md)

El video describe mecanismos que pueden reducir el contexto enviado al modelo. No atribuye un porcentaje de ahorro de tokens sin una medición comparable.
