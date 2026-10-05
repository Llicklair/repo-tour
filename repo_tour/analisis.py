"""Analisis propio, sin gb: grafo de modulos, simbolos con su linea y llamadas resueltas.

Devuelve lo mismo que `gb graph|symbols|floor --json` en las claves que lee
`hechos`, para que el resto no sepa de donde vienen. Solo biblioteca estandar:

- Python: `ast`. Imports (tambien relativos), funciones, clases y metodos con
  inicio/fin, y llamadas `f()`, `modulo.f()`, `self.metodo()` cuando el nombre se
  resuelve sin adivinar. `obj.metodo()` sobre variables no se resuelve: se cuenta.
- JavaScript/TypeScript: imports y `require` relativos, funciones y clases de
  primer nivel con su fin (por llaves), y llamadas a lo importado.
- Otros lenguajes: no hay grafo; los hechos salen del README, el manifiesto y
  las carpetas. Para esos, mejor `gb`.
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

IGNORAR = {"node_modules", "__pycache__", "dist", "build", "target", "venv", "env", "site-packages",
           "coverage", "vendor", "out"}
PY = {".py"}
JS = {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts"}
MAX_FICHEROS = 5000


def _ficheros(repo: Path) -> list[Path]:
    salida = []
    pila = [repo]
    while pila and len(salida) < MAX_FICHEROS:
        d = pila.pop()
        try:
            hijos = sorted(d.iterdir())
        except OSError:
            continue
        for p in hijos:
            if p.name.startswith(".") or p.name in IGNORAR:
                continue
            if p.is_dir():
                pila.append(p)
            elif p.suffix in PY | JS and not p.name.endswith(".d.ts"):
                salida.append(p)
    return salida


def _modulo(repo: Path, f: Path) -> str:
    partes = list(f.relative_to(repo).with_suffix("").parts)
    if partes and partes[0] == "src" and len(partes) > 1:
        partes = partes[1:]
    if partes[-1] in ("__init__", "index") and len(partes) > 1:
        partes = partes[:-1]
    return ".".join(partes)


class _Analisis:
    def __init__(self, repo: Path):
        self.repo = repo
        self.ficheros = _ficheros(repo)
        self.mods = {_modulo(repo, f): f for f in self.ficheros}
        self.por_fichero = {f: m for m, f in self.mods.items()}
        self.nodos: dict[str, dict] = {}
        self.aristas: set[tuple[str, str]] = set()
        self.llamadas: list[list[str]] = []
        self.total = 0

    def nodo(self, qual, kind, modulo, f, linea, fin=None, sig="", doc=""):
        self.nodos.setdefault(qual, {"qual": qual, "kind": kind, "module": modulo, "doc": doc or "",
                                     "file": str(f.relative_to(self.repo)), "line": linea, "end": fin, "sig": sig})

    def correr(self):
        arboles = {}
        for f in self.ficheros:
            try:
                texto = f.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                continue
            m = self.por_fichero[f]
            if f.suffix in PY:
                try:
                    arboles[m] = (f, ast.parse(texto))
                except (SyntaxError, ValueError):
                    self.nodo(m, "module", m, f, 1)
            else:
                arboles[m] = (f, texto)
        # dos pasadas: primero todos los simbolos, luego las llamadas que los nombran
        for m, (f, a) in arboles.items():
            (self._py_simbolos if f.suffix in PY else self._js_simbolos)(m, f, a)
        for m, (f, a) in arboles.items():
            (self._py_llamadas if f.suffix in PY else self._js_llamadas)(m, f, a)

    # --- Python -------------------------------------------------------------------
    def _py_simbolos(self, m, f, arbol):
        self.nodo(m, "module", m, f, 1, doc=(ast.get_docstring(arbol) or "").strip())

        def firma(n):
            try:
                return f"{n.name}({ast.unparse(n.args)})"
            except Exception:
                return n.name

        for n in arbol.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.nodo(f"{m}.{n.name}", "function", m, f, n.lineno, n.end_lineno, firma(n),
                          (ast.get_docstring(n) or "").strip())
            elif isinstance(n, ast.ClassDef):
                self.nodo(f"{m}.{n.name}", "class", m, f, n.lineno, n.end_lineno, f"class {n.name}",
                          (ast.get_docstring(n) or "").strip())
                for s in n.body:
                    if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self.nodo(f"{m}.{n.name}.{s.name}", "method", m, f, s.lineno, s.end_lineno, firma(s),
                                  (ast.get_docstring(s) or "").strip())

    def _py_absoluto(self, m, f, nivel, nombre):
        if not nivel:
            return nombre or ""
        paquete = m.split(".") if f.name == "__init__.py" else m.split(".")[:-1]
        base = paquete[:len(paquete) - (nivel - 1)] if nivel > 1 else paquete
        return ".".join(base + ([nombre] if nombre else []))

    def _py_interno(self, nombre):
        """El modulo del repo que nombra un import, por el prefijo mas largo."""
        partes = nombre.split(".")
        for i in range(len(partes), 0, -1):
            c = ".".join(partes[:i])
            if c in self.mods:
                return c
        return None

    def _py_llamadas(self, m, f, arbol):
        alias: dict[str, str] = {}  # nombre local -> qual del repo (modulo o simbolo)
        for n in ast.walk(arbol):
            if isinstance(n, ast.Import):
                for a in n.names:
                    destino = self._py_interno(a.name)
                    if destino:
                        self.aristas.add((m, destino))
                        alias[a.asname or a.name.split(".")[0]] = a.name if a.asname else a.name.split(".")[0]
            elif isinstance(n, ast.ImportFrom):
                base = self._py_absoluto(m, f, n.level, n.module)
                for a in n.names:
                    completo = f"{base}.{a.name}" if base else a.name
                    destino = self._py_interno(completo) if completo in self.mods else self._py_interno(base)
                    if destino:
                        self.aristas.add((m, destino))
                        alias[a.asname or a.name] = completo
        propios = {q.rsplit(".", 1)[-1]: q for q, n in self.nodos.items()
                   if n["module"] == m and n["kind"] in ("function", "class")}

        def resolver(func, clase):
            if isinstance(func, ast.Name):
                q = propios.get(func.id) or alias.get(func.id)
            elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                v = func.value.id
                if v in ("self", "cls") and clase:
                    q = f"{clase}.{func.attr}"
                elif v in alias:
                    q = f"{alias[v]}.{func.attr}"
                else:
                    return None
            else:
                return None
            return q if q in self.nodos else None

        def barrer(cuerpo, origen, clase=None):
            for n in cuerpo:
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    q = f"{clase}.{n.name}" if clase else f"{m}.{n.name}"
                    if q in self.nodos:
                        barrer(n.body, q, clase)
                        continue
                if isinstance(n, ast.ClassDef) and origen == m:
                    barrer(n.body, origen, f"{m}.{n.name}")
                    continue
                for c in ast.walk(n):
                    if isinstance(c, ast.Call):
                        self.total += 1
                        q = resolver(c.func, clase)
                        if q:
                            self.llamadas.append([origen, q, "CALLS"])

        barrer(arbol.body, m)

    # --- JavaScript / TypeScript --------------------------------------------------
    _DECL = re.compile(
        r"^[ \t]*(?:export\s+(?:default\s+)?)?(?:"
        r"(?:async\s+)?function\s*\*?\s*(?P<f>[\w$]+)\s*\("
        r"|(?:abstract\s+)?class\s+(?P<c>[\w$]+)"
        r"|(?:const|let|var)\s+(?P<v>[\w$]+)\s*(?::[^=]+)?=\s*(?:async\s+)?(?:function\b|\([^)]*\)\s*(?::[^=]+)?=>|[\w$]+\s*=>)"
        r"|(?:module\.)?exports\.(?P<e>[\w$]+)\s*=\s*(?:async\s+)?function\b)", re.M)
    _IMPORT = re.compile(
        r"import\s+(?P<cl>[^'\"]*?)\s*from\s*['\"](?P<d>\.[^'\"]+)['\"]"
        r"|(?:const|let|var)\s+(?P<cr>[\w${}\s,:]+?)\s*=\s*require\(\s*['\"](?P<dr>\.[^'\"]+)['\"]\s*\)"
        r"|(?:import|require)\(\s*['\"](?P<ds>\.[^'\"]+)['\"]\s*\)"
        r"|import\s*['\"](?P<db>\.[^'\"]+)['\"]")

    @staticmethod
    def _limpio(texto):
        """Comentarios y cadenas a espacios, conservando lineas y posiciones."""
        def blanco(mt):
            s = mt.group(0)
            if s[0] in "'\"`" and len(s) > 1:
                return s[0] + re.sub(r"[^\n]", " ", s[1:-1]) + s[-1]
            return re.sub(r"[^\n]", " ", s)
        return re.sub(r"//[^\n]*|/\*.*?\*/|'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\"|`(?:\\.|[^`\\])*`",
                      blanco, texto, flags=re.S)

    def _js_simbolos(self, m, f, texto):
        self.nodo(m, "module", m, f, 1)
        limpio = self._limpio(texto)
        for d in self._DECL.finditer(limpio):
            nombre = d.group("f") or d.group("c") or d.group("v") or d.group("e")
            linea = limpio.count("\n", 0, d.start()) + 1
            inicio = limpio.find("{", d.end() - 1)
            fin = None
            if inicio != -1 and limpio.count("\n", d.end(), inicio) <= 3:
                prof = 0
                for i in range(inicio, len(limpio)):
                    if limpio[i] == "{":
                        prof += 1
                    elif limpio[i] == "}":
                        prof -= 1
                        if prof == 0:
                            fin = limpio.count("\n", 0, i) + 1
                            break
            sig = texto.splitlines()[linea - 1].strip()[:160]
            self.nodo(f"{m}.{nombre}", "class" if d.group("c") else "function", m, f, linea, fin, sig)

    def _js_resolver(self, f, ruta):
        base = (f.parent / ruta).resolve()
        for c in [base] + [base.with_name(base.name + e) for e in JS] + [base / ("index" + e) for e in JS]:
            if c in self.por_fichero:
                return self.por_fichero[c]
        return None

    def _js_llamadas(self, m, f, texto):
        limpio_codigo = self._limpio(texto)
        alias: dict[str, str] = {}
        for i in self._IMPORT.finditer(texto):
            ruta = i.group("d") or i.group("dr") or i.group("ds") or i.group("db")
            destino = self._js_resolver(f, ruta)
            if not destino:
                continue
            self.aristas.add((m, destino))
            clausula = (i.group("cl") or i.group("cr") or "").strip()
            if not clausula:
                continue
            ns = re.match(r"(?:\*\s+as\s+)?([\w$]+)\s*(?:,|$)", clausula)
            if ns:
                alias[ns.group(1)] = destino  # por defecto, `* as x` o `x = require()`
            llaves = re.search(r"\{([^}]*)\}", clausula)
            for parte in (llaves.group(1).split(",") if llaves else []):
                orig, _, local = parte.strip().replace(" as ", ":").partition(":")
                if orig.strip():
                    alias[(local or orig).strip()] = f"{destino}.{orig.strip()}"
        lineas_de = [n for n in self.nodos.values() if n["module"] == m and n["kind"] != "module" and n["end"]]

        def origen(linea):
            dentro = [n for n in lineas_de if n["line"] <= linea <= n["end"]]
            return max(dentro, key=lambda n: n["line"])["qual"] if dentro else m

        propios = {q.rsplit(".", 1)[-1]: q for q, n in self.nodos.items() if n["module"] == m and n["kind"] != "module"}
        for c in re.finditer(r"(?<![\w$.])([\w$]+)(?:\.([\w$]+))?\s*\(", limpio_codigo):
            a, b = c.group(1), c.group(2)
            if a in ("if", "for", "while", "switch", "catch", "function", "return", "typeof", "require", "import"):
                continue
            self.total += 1
            q = f"{alias[a]}.{b}" if b and a in alias else (alias.get(a) or propios.get(a)) if not b else None
            if q in self.nodos and self.nodos[q]["kind"] != "module":
                linea = limpio_codigo.count("\n", 0, c.start()) + 1
                desde = origen(linea)
                if desde != q:
                    self.llamadas.append([desde, q, "CALLS"])


def _ciclos(mods, aristas):
    """Componentes fuertemente conexas de mas de un modulo (Tarjan, iterativo)."""
    vecinos: dict[str, list[str]] = {m: [] for m in mods}
    for a, b in aristas:
        vecinos[a].append(b)
    indice, bajo, pila, en_pila, salida, n = {}, {}, [], set(), [], 0
    for raiz in mods:
        if raiz in indice:
            continue
        trabajo = [(raiz, iter(vecinos[raiz]))]
        indice[raiz] = bajo[raiz] = n
        n += 1
        pila.append(raiz)
        en_pila.add(raiz)
        while trabajo:
            v, it = trabajo[-1]
            for w in it:
                if w not in indice:
                    indice[w] = bajo[w] = n
                    n += 1
                    pila.append(w)
                    en_pila.add(w)
                    trabajo.append((w, iter(vecinos[w])))
                    break
                if w in en_pila:
                    bajo[v] = min(bajo[v], indice[w])
            else:
                trabajo.pop()
                if trabajo:
                    bajo[trabajo[-1][0]] = min(bajo[trabajo[-1][0]], bajo[v])
                if bajo[v] == indice[v]:
                    comp = []
                    while True:
                        w = pila.pop()
                        en_pila.discard(w)
                        comp.append(w)
                        if w == v:
                            break
                    if len(comp) > 1:
                        salida.append(sorted(comp))
    return salida


def _tests(repo: Path) -> dict:
    """El comando de tests que el repo declara, y de donde sale."""
    encontrados = []
    pkg = repo / "package.json"
    if pkg.is_file():
        try:
            if "test" in json.loads(pkg.read_text(encoding="utf-8-sig")).get("scripts", {}):
                encontrados.append(("`npm test`", "package.json"))
        except ValueError:
            pass
    for nombre, cmd in (("Cargo.toml", "`cargo test`"), ("go.mod", "`go test ./...`")):
        if (repo / nombre).is_file():
            encontrados.append((cmd, nombre))
    for nombre in ("pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini"):
        p = repo / nombre
        if p.is_file() and "pytest" in p.read_text(encoding="utf-8", errors="replace"):
            encontrados.append(("`pytest -q`", nombre))
            break
    else:
        if any((repo / d).is_dir() for d in ("tests", "test")) and any(repo.glob("test*/test_*.py")):
            encontrados.append(("`pytest -q`", "tests/"))
    mk = repo / "Makefile"
    if mk.is_file() and re.search(r"^test\s*:", mk.read_text(encoding="utf-8", errors="replace"), re.M):
        encontrados.append(("`make test`", "Makefile"))
    if not encontrados:
        return {"key": "feedback", "status": "falta", "detail": "no encuentro comando de tests", "source": None}
    detalle = f"{encontrados[0][0]} detectado" + "".join(
        f" — tambien: {c} ({fuente})" for c, fuente in encontrados[1:])
    return {"key": "feedback", "status": "parcial", "detail": detalle, "source": encontrados[0][1]}


def analizar(repo: str | Path) -> tuple[dict, dict, dict]:
    """(graph, symbols, floor) con la forma de `gb ... --json`."""
    repo = Path(repo).resolve()
    a = _Analisis(repo)
    a.correr()
    mods = sorted(a.mods)
    aristas = sorted((x, y) for x, y in a.aristas if x != y)
    fan_in = {m: 0 for m in mods}
    fan_out = {m: 0 for m in mods}
    for x, y in aristas:
        fan_in[y] += 1
        fan_out[x] += 1
    grafo = {"modules": len(mods), "edges": len(aristas), "edge_list": [list(e) for e in aristas],
             "cycles": _ciclos(mods, aristas), "fan_in": fan_in, "fan_out": fan_out}
    unicas = list(dict.fromkeys(map(tuple, a.llamadas)))  # un llamante cuenta una vez
    simbolos = {"nodes": list(a.nodos.values()), "edges": [list(e) for e in unicas],
                "calls_total": a.total, "calls_resolved": len(a.llamadas)}
    return grafo, simbolos, {"levels": [_tests(repo)]}
