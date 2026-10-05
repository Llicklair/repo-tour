---
name: repo-tour
description: Genera un video narrado para APRENDER un repo cualquiera — diapositivas, VS Code real navegando el codigo y preguntas de comprension — con hechos sacados del codigo (galaxy-brain si esta instalado, o el analisis propio). Usar cuando Marcos pida "un video del repo", "explicame este proyecto en video" o "repo-tour <ruta>".
---

# repo-tour

Un video didactico para Marcos, sobre un repo que quiere entender. **Los hechos los
pone el analisis; tu escribes el guion; el pipeline graba.** Nada inventado en pantalla: cada
cifra, fichero y linea sale de `hechos.json` o de un comando que se ejecuta al grabar.

Codigo: `C:\Users\marcos\dev\repo-tour` (paquete `repo_tour`). Requisitos ya presentes
en la maquina: ffmpeg, Playwright (chromium), VS Code (`code serve-web`), voz
SAPI "Microsoft Helena Desktop". Opcional: `gb` (galaxy-brain).

## Fuente de los hechos

`hechos --fuente auto` (por defecto) usa `gb` si esta en el PATH y, si no, el
analisis propio (`repo_tour/analisis.py`, sin dependencias). `--fuente gb|propio`
lo fuerza. `hechos.json` dice cual se uso en `"fuente"`.

- `gb`: 17 lenguajes, grafo de modulos y de llamadas.
- `propio`: Python (con `ast`) y JavaScript/TypeScript. Grafo de imports, simbolos
  con inicio/fin y llamadas que se resuelven sin adivinar. En otros lenguajes solo
  hay README, manifiesto, carpetas y comando de tests: usa `gb` o lee el codigo.

## Pasos

1. **Hechos**: `cd C:\Users\marcos\dev\repo-tour; python -m repo_tour hechos <repo>`
   -> `out/hechos-<nombre>.json` (nucleo por fan-in, sus simbolos mas llamados con
   fichero/linea y llamantes, puntos de entrada, suelo, README, carpetas).
2. **Entiende el repo** antes de escribir: lee el README y los ficheros del nucleo y
   de las entradas (con Read, las lineas que vas a enseñar). Sigue un flujo real de
   punta a punta: con `gb calls <simbolo> --depth 2` si hay gb, o con los
   `llamantes` de `hechos.json` y `git grep -n "simbolo("`.
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
7. `terminal` — el mismo camino preguntado al repo: `gb calls ... --depth 2` si hay
   gb; si no, `git grep -n "simbolo("` (quien lo llama, con fichero y linea).
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
  {"tipo": "diagrama", "capitulo": "...", "titulo": "...", "nota": "opcional, abajo",
   "nodos": [{"id": "a", "texto": "Broker", "sub": "opcional", "x": 0.04, "y": 0.5, "paso": 0}],
   "flechas": [{"de": "a", "a": "b", "texto": "...", "estilo": "dinero", "curva": 16, "paso": 1}],
   "narracion": "..."},
  {"tipo": "terminal", "capitulo": "...", "cmd": "git grep -n \"simbolo(\"",
   "filtro": "tests\\W", "narracion": "..."},
  {"tipo": "pregunta", "capitulo": "Compruebalo", "texto": "...", "respuesta": "... `codigo` ...",
   "narracion": "la pregunta, en voz", "respuesta_narrada": "la respuesta, en voz", "pausa": 5}
 ]}
```

- `diagrama`: cajas y flechas animadas para flujos y mapas. `x`, `y` van de 0 a 1 en
  el lienzo bajo el titulo (x 0.04-0.95 y cajas de 210 px de ancho, `w` para otro).
  `estilo`: flujo (por defecto), dinero, riesgo, siniestro, info (discontinua); los
  usados salen en la leyenda. `curva` (px, con signo) separa flechas entre los mismos
  nodos. Lo del mismo `paso` aparece junto y los pasos se reparten en la narracion:
  ordenalos como los nombras. Previsualiza el ultimo fotograma: se cruzan flechas.
- `resaltar` actua sobre el fichero abierto; rangos de 8-20 lineas se ven enteros.
- `abrir` usa rutas relativas al repo, con `/`. La `linea` sale de `hechos.json`.
- `terminal` ejecuta el comando en el repo al grabar: que sea rapido y determinista.
  `filtro` (regex) quita lineas de la salida real — p.ej. los tests entre los
  llamantes de `gb calls` o de `git grep` — para que se vea lo que narras. Previsualiza la salida
  filtrada antes de grabar: caben ~24 lineas y se desplaza hacia abajo.
- Una escena `vscode` sin `buscar` vuelve sola al explorador (la busqueda de la
  anterior no tapa el arbol).
- Capitulo nuevo = capitulo del mp4. Repite el mismo nombre para escenas del mismo tema.

## Limites declarados

- La voz es la de Windows (SAPI): solo Windows.
- VS Code navega por fichero:linea, no por "ir a la definicion" (no hay extension de
  lenguaje): por eso las lineas salen de `hechos.json`.
- El analisis propio no resuelve `obj.metodo()` sobre variables (exige tipos): esas
  llamadas se cuentan pero no son aristas. Mejor una arista ausente que una inventada.
- El puerto de `serve-web` es 8791 (8765 es del Voice Bridge de AIOS).
