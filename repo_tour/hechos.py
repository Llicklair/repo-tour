"""Los hechos de un repo, sacados de gb: la materia prima del guion.

Nada de aqui opina. El nucleo es lo mas importado, los llamantes son aristas
del grafo con su fichero y su linea, el comando de tests es el que `floor`
detecta. El agente escribe el guion A PARTIR de esto, y el video enseña lo que
estos comandos dicen el dia que se graba.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

MAX_NUCLEO = 6
MAX_SIMBOLOS = 4
MAX_LLAMANTES = 5


def _gb(*args: str) -> dict:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run(["gb", *args, "--json"], capture_output=True, env=env, timeout=600)
    try:
        return json.loads(r.stdout.decode("utf-8", errors="replace"))
    except ValueError:
        return {}


#: Lo que no es el codigo que se aprende: tests, ejemplos, documentacion, bancos.
#: En express, sin esto, el "nucleo" eran los `examples/` (24-sep-2026).
_FUERA = ("tests", "test", "testing", "conftest", "examples", "example", "docs", "doc",
          "benchmarks", "benchmark", "bench", "scripts", "fixtures")


def _es_test(nombre: str) -> bool:
    partes = nombre.split(".")
    return any(p in _FUERA or p.startswith("test_") for p in partes)


def _leer(repo: Path, *nombres: str, lineas: int = 80) -> str:
    for n in nombres:
        p = repo / n
        if p.is_file():
            return "\n".join(p.read_text(encoding="utf-8-sig", errors="replace").splitlines()[:lineas])
    return ""


def recoger(repo: str | Path) -> dict:
    repo = Path(repo).resolve()
    grafo = _gb("graph", str(repo))
    simbolos = _gb("symbols", str(repo))
    suelo = _gb("floor", str(repo))

    nodos = {n["qual"]: n for n in simbolos.get("nodes", [])}
    llamantes: dict[str, list[str]] = {}
    for origen, destino, tipo in simbolos.get("edges", []):
        if tipo == "CALLS":
            llamantes.setdefault(destino, []).append(origen)

    def ficha(qual: str) -> dict:
        n = nodos.get(qual, {})
        return {k: n.get(k) for k in ("qual", "kind", "file", "line", "end", "sig", "doc") if n.get(k) not in (None, "")}

    fan_in = grafo.get("fan_in", {})
    fan_out = grafo.get("fan_out", {})
    nucleo_mods = [m for m, _ in sorted(fan_in.items(), key=lambda kv: -kv[1]) if not _es_test(m)][:MAX_NUCLEO]

    nucleo = []
    for mod in nucleo_mods:
        propios = [q for q, n in nodos.items()
                   if n.get("module") == mod and n.get("kind") in ("function", "class", "method")]
        propios.sort(key=lambda q: -len(llamantes.get(q, [])))
        nucleo.append({
            "modulo": mod,
            "importado_por": fan_in.get(mod, 0),
            "fichero": nodos.get(mod, {}).get("file"),
            "doc": (nodos.get(mod, {}).get("doc") or "")[:400],
            "simbolos": [
                {**ficha(q),
                 "n_llamantes": len(llamantes.get(q, [])),
                 "llamantes": [ficha(c) for c in llamantes.get(q, [])[:MAX_LLAMANTES]]}
                for q in propios[:MAX_SIMBOLOS]
            ],
        })

    entradas = [ficha(q) for q, n in nodos.items()
                if n.get("kind") == "module" and not _es_test(q)
                and q.rsplit(".", 1)[-1] in ("cli", "__main__", "main", "app", "api", "server")]

    niveles = {lv["key"]: {"estado": lv["status"], "detalle": lv["detail"], "fuente": lv.get("source")}
               for lv in suelo.get("levels", [])}

    carpetas = sorted(p.name + ("/" if p.is_dir() else "") for p in repo.iterdir()
                      if not p.name.startswith(".") and p.name not in ("node_modules", "__pycache__"))

    return {
        "repo": str(repo),
        "nombre": repo.name,
        "readme": _leer(repo, "README.md", "README.rst", "README.txt", "README"),
        "manifiesto": _leer(repo, "pyproject.toml", "package.json", "Cargo.toml", "go.mod", lineas=40),
        "carpetas": carpetas,
        "modulos": grafo.get("modules", 0),
        "aristas": len(grafo.get("edge_list", []) or []),
        "ciclos": grafo.get("cycles", []),
        "nucleo": nucleo,
        "cabeza": [{"modulo": m, "depende_de": v} for m, v in
                   sorted(fan_out.items(), key=lambda kv: -kv[1]) if not _es_test(m)][:5],
        "entradas": entradas[:5],
        "suelo": niveles,
        "comando_tests": (niveles.get("feedback", {}).get("detalle") or ""),
        "llamadas": {"total": simbolos.get("calls_total"), "resueltas": simbolos.get("calls_resolved")},
    }
