# repo-tour

Un video narrado para aprender un repo: diapositivas, VS Code real navegando el
codigo, diagramas animados y preguntas de comprension. Los hechos (nucleo, simbolos
con fichero y linea, quien llama a quien, comando de tests) salen del codigo; el
guion lo escribe un agente a partir de ellos; esto lo graba.

    python -m repo_tour hechos <repo>          # out/hechos-<nombre>.json
    python -m repo_tour video <guion.json>     # out/<nombre>.mp4 + .srt, con capitulos

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
