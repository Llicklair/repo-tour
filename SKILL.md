---
name: repo-tour
description: Genera un video narrado para APRENDER un repo cualquiera — diapositivas, VS Code real navegando el codigo y preguntas de comprension — con los hechos de galaxy-brain (gb). Usar cuando Marcos pida "un video del repo", "explicame este proyecto en video" o "repo-tour <ruta>".
---

# repo-tour

Un video didactico para Marcos, sobre un repo que quiere entender. **Los hechos los
pone gb; tu escribes el guion; el pipeline graba.** Nada inventado en pantalla: cada
cifra, fichero y linea sale de `hechos.json` o de un comando que se ejecuta al grabar.

Codigo: `C:\Users\marcos\dev\repo-tour` (paquete `repo_tour`). Requisitos ya presentes
en la maquina: `gb`, ffmpeg, Playwright (chromium), VS Code (`code serve-web`), voz
SAPI "Microsoft Helena Desktop".

## Pasos

1. **Hechos**: `cd C:\Users\marcos\dev\repo-tour; python -m repo_tour hechos <repo>`
   -> `out/hechos-<nombre>.json` (nucleo por fan-in, sus simbolos mas llamados con
   fichero/linea y llamantes, puntos de entrada, suelo, README, carpetas).
2. **Entiende el repo** antes de escribir: lee el README y los ficheros del nucleo y
   de las entradas (con Read, las lineas que vas a enseñar). Sigue un flujo real de
   punta a punta con `gb calls <simbolo> --depth 2`.
3. **Guion**: escribe `out/guion-<nombre>.json` (esquema abajo). 10-14 escenas, 5-8 min.
4. **Prueba barata**: `python -m repo_tour video out/guion-<nombre>.json --escenas 0-2 -o out/prueba.mp4`
   y mira fotogramas (`ffmpeg -ss <t> -i ... -frames:v 1 f.png` + Read).
5. **Video**: `python -m repo_tour video out/guion-<nombre>.json` -> `out/<nombre>.mp4`
   (+ `.srt`). Lleva capitulos: se salta de tema en cualquier reproductor.

## Arco didactico (el orden importa)

1. `portada` — que es, en una frase, y la lista de capitulos.
2. `diapositiva` con `cifras` — el problema que resuelve y el tamaño (modulos, aristas, ciclos).
3. `barras` — el mapa: lo mas importado. Di cual es el nucleo DE VERDAD (a veces el
   primero es logging/output: dilo y señala el siguiente).
4. `vscode` — el arbol de carpetas y el concepto central abierto en el editor.
5. `vscode` + `buscar` — quien usa ese concepto (la busqueda enseña los usos).
6. `vscode` — un flujo de punta a punta: entrada -> capa de aplicacion -> nucleo.
7. `terminal` — el mismo camino preguntado al grafo (`gb calls ... --depth 2`).
8. `vscode` — una pieza por dentro, la mas interesante.
9. `diapositiva` — "Lo que te llevas": 3-5 ideas.
10. `pregunta` x2-3 — comprension, no memoria de nombres ("¿que harias para...?", "¿por que...?").

## Narracion

- Español, segunda persona, didactica: explica el PORQUE, no leas numeros ni rutas.
  Las rutas se leen en pantalla; en voz, "contract punto py" como mucho.
- 60-110 palabras por escena (~25-45 s). Frases cortas: la voz es sintetica.
- Lo que dices tiene que estar en pantalla en ese momento: los pasos de `vscode` se
  reparten a partes iguales en la duracion de la narracion, en orden.
- Nada que no hayas comprobado leyendo el codigo. Si dudas, no lo digas.

## Esquema del guion

```json
{"repo": "C:/ruta/al/repo", "nombre": "repo", "velocidad_voz": 0,
 "capitulos": ["Que es", "El mapa", "..."],
 "escenas": [
  {"tipo": "portada", "titulo": "...", "subtitulo": "...", "narracion": "..."},
  {"tipo": "diapositiva", "capitulo": "Que es", "titulo": "...",
   "cifras": [["114", "modulos"]], "puntos": ["texto con `codigo`"], "narracion": "..."},
  {"tipo": "barras", "capitulo": "El mapa", "titulo": "...", "datos": [["mod", 19]], "nota": "...", "narracion": "..."},
  {"tipo": "vscode", "capitulo": "...", "narracion": "...", "pasos": [
     {"explorador": true},
     {"abrir": "src/pkg/mod.py", "linea": 40},
     {"resaltar": [40, 62]},
     {"buscar": "NombreClase("},
     {"bajar": 12}]},
  {"tipo": "terminal", "capitulo": "...", "cmd": "gb calls simbolo --depth 2", "narracion": "..."},
  {"tipo": "pregunta", "capitulo": "Compruebalo", "texto": "...", "respuesta": "... `codigo` ...",
   "narracion": "la pregunta, en voz", "respuesta_narrada": "la respuesta, en voz", "pausa": 5}
 ]}
```

- `resaltar` actua sobre el fichero abierto; rangos de 8-20 lineas se ven enteros.
- `abrir` usa rutas relativas al repo, con `/`. La `linea` sale de `hechos.json`.
- `terminal` ejecuta el comando en el repo al grabar: que sea rapido y determinista.
- Capitulo nuevo = capitulo del mp4. Repite el mismo nombre para escenas del mismo tema.

## Limites declarados

- La voz es la de Windows (SAPI): solo Windows.
- VS Code navega por fichero:linea, no por "ir a la definicion" (no hay extension de
  lenguaje): por eso las lineas salen de gb.
- El puerto de `serve-web` es 8791 (8765 es del Voice Bridge de AIOS).
