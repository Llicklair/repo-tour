# repo-tour

Un video narrado para aprender un repo: diapositivas, VS Code real navegando el
codigo, diagramas animados y preguntas de comprension. Los hechos (nucleo, simbolos
con fichero y linea, quien llama a quien, comando de tests) salen del codigo; el
guion lo escribe un agente a partir de ellos; esto lo graba.

    python -m repo_tour hechos <repo>          # out/hechos-<nombre>.json
    python -m repo_tour previa <guion.json>    # PNG del final de cada escena + avisos, en segundos
    python -m repo_tour video <guion.json>     # out/<nombre>.mp4 + .srt, con capitulos

## Escenas

| Tipo | Que enseña |
|---|---|
| `portada` | titulo y capitulos (hasta 14, en dos columnas si son mas de 8) |
| `diapositiva` | puntos que se iluminan al narrarlos, tarjetas, comparacion en columnas, cifras e idea clave |
| `barras` | un ranking animado (p. ej. lo mas importado) |
| `diagrama` | cajas y flechas que aparecen por pasos; se colocan solas por capas si no das coordenadas |
| `vscode` | VS Code real: abrir, resaltar, buscar |
| `terminal` | la salida real de un comando, al grabar |
| `pregunta` | abierta o tipo test, con cuenta atras y la respuesta marcada |

`previa` revisa cada fotograma y avisa de texto que se sale o se corta, cajas o
etiquetas que se pisan y contenido sobre el pie, antes de gastar un render.

## De donde salen los hechos

`hechos` no depende de ninguna herramienta concreta:

| `--fuente` | Que usa | Lenguajes |
|---|---|---|
| `auto` (por defecto) | `gb` si esta en el PATH; si no, `propio` | |
| `gb` | [galaxy-brain](https://github.com/Llicklair/galaxy-brain) | 17 |
| `propio` | `repo_tour/analisis.py`, solo biblioteca estandar | Python, JS/TS |

El analisis propio saca el grafo de imports (con ciclos), funciones, clases y
metodos con su inicio y fin, y las llamadas que se resuelven sin adivinar
(`f()`, `modulo.f()`, `self.metodo()`, lo importado en JS). En otros lenguajes
deja README, manifiesto, carpetas y comando de tests.

## Requisitos

Python 3.11+, ffmpeg, Playwright (chromium), VS Code (`code serve-web`) y la voz
SAPI de Windows. `gb` es opcional.

Como se usa, el arco didactico y el esquema del guion: [SKILL.md](SKILL.md).
