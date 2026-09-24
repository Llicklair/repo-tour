"""ffmpeg: cada escena con su voz, en un solo mp4 con capitulos y subtitulos.

Los capitulos dejan saltar de un tema a otro en cualquier reproductor (VLC, el de
Windows, mpv); los subtitulos van incrustados como pista activable y tambien al
lado, en .srt.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .voz import duracion

FPS = 25


def _ff(*args: str) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def audio_de_escena(partes: list, destino: Path) -> float:
    """`partes`: rutas .wav o segundos de silencio, en orden. Devuelve la duracion."""
    entradas, filtros = [], []
    for i, p in enumerate(partes):
        if isinstance(p, (int, float)):
            entradas += ["-f", "lavfi", "-t", f"{p:.2f}", "-i", "anullsrc=r=44100:cl=mono"]
        else:
            entradas += ["-i", str(p)]
        filtros.append(f"[{i}:a]aresample=44100,aformat=channel_layouts=mono[a{i}]")
    une = "".join(f"[a{i}]" for i in range(len(partes)))
    _ff(*entradas, "-filter_complex", ";".join(filtros) + f";{une}concat=n={len(partes)}:v=0:a=1[s]",
        "-map", "[s]", str(destino))
    return duracion(destino)


def segmento(video: Path, audio: Path, destino: Path, desde: float = 0.0, cola: float = 0.8) -> float:
    """Video (recortado desde `desde`) + audio, con la duracion del audio + `cola`."""
    total = duracion(audio) + cola
    _ff("-ss", f"{desde:.2f}", "-i", str(video), "-i", str(audio),
        "-filter_complex",
        f"[0:v]scale=1280:720,fps={FPS},tpad=stop_mode=clone:stop_duration={total:.2f}[v];"
        f"[1:a]apad=pad_dur={cola + 0.5:.2f}[a]",
        "-map", "[v]", "-map", "[a]", "-t", f"{total:.2f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-ar", "44100", str(destino))
    return total


def _hms(t: float, sep: str = ",") -> str:
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}{sep}{int((s % 1) * 1000):03d}"


def subtitulos(tramos: list[tuple[float, float, str]], destino: Path) -> None:
    """tramos: (inicio, fin, texto) de cada narracion; se parte por frases."""
    bloques, n = [], 1
    for ini, fin, texto in tramos:
        frases = [f.strip() for f in re.split(r"(?<=[.!?¿?:;])\s+", texto) if f.strip()]
        total = sum(len(f) for f in frases) or 1
        t = ini
        for f in frases:
            d = (fin - ini) * len(f) / total
            bloques.append(f"{n}\n{_hms(t)} --> {_hms(t + d)}\n{f}\n")
            n, t = n + 1, t + d
    destino.write_text("\n".join(bloques), encoding="utf-8")


def unir(segmentos: list[Path], capitulos: list[tuple[float, str]], srt: Path, destino: Path) -> None:
    carpeta = destino.parent
    lista = carpeta / "lista.txt"
    lista.write_text("\n".join(f"file '{s.as_posix()}'" for s in segmentos), encoding="utf-8")
    total = sum(duracion(s) for s in segmentos)
    meta = [";FFMETADATA1"]
    for i, (ini, titulo) in enumerate(capitulos):
        fin = capitulos[i + 1][0] if i + 1 < len(capitulos) else total
        meta += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={int(ini * 1000)}", f"END={int(fin * 1000)}",
                 f"title={titulo}"]
    (carpeta / "capitulos.txt").write_text("\n".join(meta) + "\n", encoding="utf-8")
    _ff("-f", "concat", "-safe", "0", "-i", str(lista), "-i", str(carpeta / "capitulos.txt"), "-i", str(srt),
        "-map", "0", "-map", "2", "-map_metadata", "1", "-map_chapters", "1",
        "-c", "copy", "-c:s", "mov_text", "-metadata:s:s:0", "language=spa", str(destino))
