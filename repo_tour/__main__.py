"""repo-tour: un video para aprender un repo, con sus hechos y VS Code de verdad.

  python -m repo_tour hechos <repo> [-o hechos.json] [--fuente auto|gb|propio]
  python -m repo_tour video <guion.json> [-o video.mp4] [--escenas 0-3]
  python -m repo_tour previa <guion.json> [--escenas 0-3]   (PNG del final de cada escena)
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import diseno, hechos, montaje, voz

AQUI = Path(__file__).resolve().parent.parent


def _capturar(cmd: str, repo: Path) -> str:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "NO_COLOR": "1"}
    r = subprocess.run(cmd, shell=True, cwd=str(repo), capture_output=True, env=env, timeout=900)
    return (r.stdout + r.stderr).decode("utf-8", errors="replace").replace("\r", "").strip()


def _rango(texto: str | None, n: int) -> list[int]:
    if not texto:
        return list(range(n))
    a, _, b = texto.partition("-")
    return list(range(int(a), (int(b) if b else int(a)) + 1))


def cmd_hechos(args) -> int:
    datos = hechos.recoger(args.repo, args.fuente)
    salida = Path(args.o or AQUI / "out" / f"hechos-{Path(args.repo).resolve().name}.json")
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    print(salida)
    return 0


def _html_de(e: dict, guion: dict, nombre: str, prog: float, d: float, revelar: float, repo: Path) -> str:
    """El HTML de una escena que no es VS Code."""
    cap = e.get("capitulo", "")
    if e["tipo"] == "portada":
        return diseno.portada(e["titulo"], e.get("subtitulo", ""), guion.get("capitulos", []), nombre, d)
    if e["tipo"] == "diapositiva":
        return diseno.diapositiva(cap, e["titulo"], e.get("puntos", []), nombre, prog, d, e.get("cifras"),
                                  e.get("disposicion", "auto"), e.get("columnas"), e.get("destacado", ""))
    if e["tipo"] == "barras":
        return diseno.barras(cap, e["titulo"], e["datos"], nombre, prog, d, e.get("nota", ""))
    if e["tipo"] == "diagrama":
        return diseno.diagrama(cap, e["titulo"], e["nodos"], e["flechas"], nombre, prog, d, e.get("nota", ""),
                               e.get("direccion", "horizontal"))
    if e["tipo"] == "pregunta":
        return diseno.pregunta(cap, e["texto"], e["respuesta"], nombre, prog, d, revelar,
                               e.get("opciones"), e.get("correcta"))
    if e["tipo"] == "terminal":
        return diseno.terminal(cap, e["cmd"], _capturar(e["cmd"], repo), nombre, prog, d, e.get("filtro", ""))
    raise SystemExit(f"tipo de escena desconocido: {e['tipo']}")


def _dur_estimada(texto: str, velocidad: int = 0) -> float:
    """Lo que tarda la voz SAPI en decir `texto`: ~2.5 palabras/s a velocidad 0."""
    return 0.4 + len(texto.split()) / (2.5 * (1 + 0.1 * velocidad)) + 0.2


def cmd_previa(args) -> int:
    """El ultimo fotograma de cada escena (no VS Code), en PNG y en una hoja de contactos.
    Sin voz ni video: segundos en vez de minutos, para corregir el guion antes de grabar."""
    from playwright.sync_api import sync_playwright

    guion = json.loads(Path(args.guion).read_text(encoding="utf-8"))
    repo = Path(guion["repo"]).resolve()
    nombre = guion.get("nombre") or repo.name
    todas = guion["escenas"]
    vel = guion.get("velocidad_voz", 0)
    destino = Path(args.o or AQUI / "out" / f"previa-{nombre}")
    destino.mkdir(parents=True, exist_ok=True)
    fin = "*,*::before,*::after{animation-delay:0s!important;animation-duration:1ms!important}"
    hechas = []
    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pg = navegador.new_page(viewport={"width": 1280, "height": 720})
        for i in _rango(args.escenas, len(todas)):
            e = todas[i]
            if e["tipo"] == "vscode":
                continue
            revelar = 0.0
            if e["tipo"] == "pregunta":
                revelar = _dur_estimada(e["narracion"], vel) + float(e.get("pausa", 5))
                d = revelar + _dur_estimada(e.get("respuesta_narrada") or e["respuesta"], vel)
            else:
                d = _dur_estimada(e["narracion"], vel)
            pagina = _html_de(e, guion, nombre, (i + 1) / len(todas), d, revelar, repo)
            pg.set_content(pagina.replace("</style>", fin + "</style>", 1), wait_until="load")
            pg.wait_for_timeout(int(d * 1000) if e["tipo"] == "terminal" else 300)
            png = destino / f"{i:02d}-{e['tipo']}.png"
            pg.screenshot(path=str(png))
            avisos = diseno.revisar(pg)
            hechas.append((i, e, png, d, avisos))
            print(f"escena {i:02d} {e['tipo']:<11} ~{d:4.0f}s  {png.name}")
            for a in avisos:
                print(f"    ! {a}")
        navegador.close()
    hoja = destino / "index.html"
    hoja.write_text("<!doctype html><meta charset='utf-8'><title>previa " + nombre + "</title>"
                    "<style>body{background:#111;color:#ccc;font:14px system-ui;margin:24px}"
                    "div{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:18px}"
                    "img{width:100%;border:1px solid #333}b{color:#f7768e;display:block}</style><div>" + "".join(
                        f"<figure><img src='{png.name}'><figcaption>{i:02d} {e['tipo']} ~{d:.0f}s"
                        + "".join(f"<b>{a}</b>" for a in avisos) + "</figcaption></figure>"
                        for i, e, png, d, avisos in hechas) + "</div>", encoding="utf-8")
    print(f"previa: {hoja}")
    return 0


def cmd_video(args) -> int:
    from playwright.sync_api import sync_playwright

    from . import vscode

    guion = json.loads(Path(args.guion).read_text(encoding="utf-8"))
    repo = Path(guion["repo"]).resolve()
    nombre = guion.get("nombre") or repo.name
    todas = guion["escenas"]
    indices = _rango(args.escenas, len(todas))
    escenas = [todas[i] for i in indices]
    trabajo = AQUI / "out" / ("trabajo-" + nombre)
    shutil.rmtree(trabajo, ignore_errors=True)
    (trabajo / "webm").mkdir(parents=True)

    # 1. voz: una o varias partes por escena (las preguntas llevan silencio para pensar)
    textos, mapa = [], []
    for e in escenas:
        if e["tipo"] == "pregunta":
            mapa.append((len(textos), len(textos) + 1))
            textos += [e["narracion"], e.get("respuesta_narrada") or e["respuesta"]]
        else:
            mapa.append((len(textos),))
            textos.append(e["narracion"])
    wavs = voz.sintetizar(textos, trabajo / "voz", velocidad=guion.get("velocidad_voz", 0))
    audios, revelar = [], []
    for i, (e, idx) in enumerate(zip(escenas, mapa)):
        destino = trabajo / f"audio{i:02d}.wav"
        if e["tipo"] == "pregunta":
            pausa = float(e.get("pausa", 5))
            montaje.audio_de_escena([0.4, wavs[idx[0]], pausa, wavs[idx[1]]], destino)
            revelar.append(0.4 + voz.duracion(wavs[idx[0]]) + pausa)
        else:
            montaje.audio_de_escena([0.4, wavs[idx[0]]], destino)
            revelar.append(0)
        audios.append(destino)
    duraciones = [voz.duracion(a) for a in audios]
    print("voz:", " ".join(f"{d:.0f}s" for d in duraciones), f"= {sum(duraciones) / 60:.1f} min")

    # 2. imagen
    total = len(todas)
    videos: list[tuple[Path, float]] = [None] * len(escenas)  # type: ignore[list-item]
    with sync_playwright() as p:
        navegador = p.chromium.launch()
        for i, (e, d) in enumerate(zip(escenas, duraciones)):
            if e["tipo"] == "vscode":
                continue
            pagina = _html_de(e, guion, nombre, (indices[i] + 1) / total, d, revelar[i], repo)
            ctx = navegador.new_context(viewport={"width": 1280, "height": 720},
                                        record_video_dir=str(trabajo / "webm"),
                                        record_video_size={"width": 1280, "height": 720})
            pg = ctx.new_page()
            pg.set_content(pagina, wait_until="load")
            pg.wait_for_timeout(int((d + 1.0) * 1000))
            ruta = Path(pg.video.path())
            ctx.close()
            videos[i] = (ruta, 0.35)
            print(f"escena {indices[i]:02d} {e['tipo']:<11} {d:5.1f}s")
        navegador.close()

        codigo = [i for i, e in enumerate(escenas) if e["tipo"] == "vscode"]
        if codigo:
            with vscode.Servidor() as servidor:
                vscode.preparar(servidor, repo, p)
                editor = vscode.Editor(servidor, repo, p, trabajo / "webm")
                tramos = {}
                for i in codigo:
                    tramos[i] = editor.escena(escenas[i]["pasos"], duraciones[i] + 0.8)
                    print(f"escena {indices[i]:02d} vscode      {duraciones[i]:5.1f}s")
                grabacion = editor.cerrar()
            for i in codigo:
                videos[i] = (grabacion, tramos[i][0])

    # 3. montaje
    segmentos, capitulos, subs, t = [], [], [], 0.0
    ultimo = None
    for i, (e, (video, desde)) in enumerate(zip(escenas, videos)):
        seg = trabajo / f"seg{i:02d}.mp4"
        d = montaje.segmento(video, audios[i], seg, desde=desde)
        cap = e.get("capitulo") or ("Portada" if e["tipo"] == "portada" else "")
        if cap and cap != ultimo:
            capitulos.append((t, cap))
            ultimo = cap
        if e["tipo"] == "pregunta":
            q = voz.duracion(wavs[mapa[i][0]])
            subs.append((t + 0.4, t + 0.4 + q, e["narracion"]))
            subs.append((t + revelar[i], t + d - 0.8, e.get("respuesta_narrada") or e["respuesta"]))
        else:
            subs.append((t + 0.4, t + d - 0.8, e["narracion"]))
        segmentos.append(seg)
        t += d
    destino = Path(args.o or AQUI / "out" / f"{nombre}.mp4")
    srt = destino.with_suffix(".srt")
    montaje.subtitulos(subs, srt)
    montaje.unir(segmentos, capitulos or [(0, nombre)], srt, destino)
    print(f"video: {destino}  ({t / 60:.1f} min, {len(capitulos)} capitulos)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="repo_tour", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("hechos", help="los hechos del repo (gb si esta, o analisis propio)")
    h.add_argument("repo")
    h.add_argument("-o")
    h.add_argument("--fuente", choices=("auto", "gb", "propio"), default="auto",
                   help="de donde salen: gb, el analisis propio, o auto (gb si esta en el PATH)")
    h.set_defaults(func=cmd_hechos)
    v = sub.add_parser("video", help="el video, a partir de un guion.json")
    v.add_argument("guion")
    v.add_argument("-o")
    v.add_argument("--escenas", help="solo un rango, p.ej. 0-3 (para iterar rapido)")
    v.set_defaults(func=cmd_video)
    pv = sub.add_parser("previa", help="el ultimo fotograma de cada escena en PNG, sin grabar")
    pv.add_argument("guion")
    pv.add_argument("-o", help="carpeta (por defecto out/previa-<nombre>)")
    pv.add_argument("--escenas", help="solo un rango, p.ej. 0-3")
    pv.set_defaults(func=cmd_previa)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
