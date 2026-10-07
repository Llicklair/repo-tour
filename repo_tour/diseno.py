"""Las escenas que no son VS Code: HTML de 1280x720, animado al ritmo de la voz.

Cada escena recibe su duracion (la de su narracion) y reparte sus apariciones a
lo largo de ella, para que lo que se ve llegue cuando se nombra.
"""
from __future__ import annotations

import html
import json

ANCHO, ALTO = 1280, 720

IDIOMA = "es"  # "idioma" del guion; cambia los textos fijos de la interfaz
TEXTOS = {
    "es": {"eyebrow": "Un recorrido para aprender", "portada": "Portada", "comprueba": "Comprueba que lo has entendido",
           "respuesta": "Respuesta", "dinero": "dinero", "riesgo": "riesgo", "siniestros": "siniestros",
           "información": "información"},
    "en": {"eyebrow": "A guided tour", "portada": "Intro", "comprueba": "Check your understanding",
           "respuesta": "Answer", "dinero": "money", "riesgo": "risk", "siniestros": "claims",
           "información": "information"},
}


def texto_ui(clave: str) -> str:
    return TEXTOS.get(IDIOMA, TEXTOS["es"]).get(clave, TEXTOS["es"][clave])

BASE = """*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0b1020;--panel:#131a2e;--borde:#26304d;--texto:#e6e9f2;--suave:#8b93b0;
--azul:#7aa2f7;--verde:#9ece6a;--ambar:#e0af68;--rosa:#f7768e}
body{width:1280px;height:720px;overflow:hidden;color:var(--texto);
font-family:'Segoe UI Variable Display','Segoe UI',system-ui,sans-serif;
background:radial-gradient(1200px 700px at 85% -10%,#1b2750 0%,transparent 60%),
radial-gradient(900px 600px at -10% 110%,#162238 0%,transparent 55%),var(--bg)}
.pie{position:absolute;left:0;right:0;bottom:0;height:54px;display:flex;align-items:center;
gap:14px;padding:0 56px;color:var(--suave);font-size:15px}
.cap{border:1px solid var(--borde);background:#ffffff08;border-radius:999px;padding:5px 14px;color:var(--azul);
letter-spacing:.06em;text-transform:uppercase;font-size:12.5px;font-weight:600}
.barra{position:absolute;left:0;bottom:0;height:3px;background:linear-gradient(90deg,var(--azul),var(--verde))}
.entra{opacity:0;transform:translateY(14px);animation:entra .55s cubic-bezier(.2,.7,.2,1) forwards}
@keyframes entra{to{opacity:1;transform:none}}
.eyebrow{color:var(--azul);letter-spacing:.14em;text-transform:uppercase;font-size:15px;font-weight:600}
h1{font-size:50px;line-height:1.08;font-weight:650;letter-spacing:-.01em}
code,.mono{font-family:'Cascadia Code','Cascadia Mono',Consolas,monospace}
code{background:#ffffff10;border:1px solid var(--borde);border-radius:6px;padding:1px 7px;font-size:.84em;color:var(--ambar)}
"""


def _pie(capitulo: str, repo: str, progreso: float) -> str:
    return (f"<div class='pie'><span class='cap'>{html.escape(capitulo)}</span>"
            f"<span>{html.escape(repo)}</span><span style='margin-left:auto' class='mono'>repo-tour</span></div>"
            f"<div class='barra' style='width:{progreso * 100:.1f}%'></div>")


def _pagina(cuerpo: str, css: str = "") -> str:
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE}{css}</style></head><body>{cuerpo}</body></html>"


def _retrasos(n: int, dur: float, inicio: float = 0.4, margen: float = 0.25) -> list[float]:
    """n apariciones repartidas en la primera (1 - margen) de la escena."""
    if n <= 0:
        return []
    tramo = max(0.0, dur * (1 - margen) - inicio)
    return [inicio + tramo * i / max(1, n) for i in range(n)]


def portada(titulo: str, subtitulo: str, capitulos: list[str], repo: str, dur: float) -> str:
    items = "".join(
        f"<li class='entra' style='animation-delay:{d:.2f}s'><span class='n mono'>{i + 1:02d}</span>{html.escape(c)}</li>"
        for i, (c, d) in enumerate(zip(capitulos, _retrasos(len(capitulos), dur, 1.2))))
    dos = len(capitulos) > 8  # no caben en una columna: dos, mas compactas
    css = (".s{padding:88px 96px;display:grid;grid-template-columns:" + ("1fr 1.15fr" if dos else "1.25fr 1fr")
           + ";gap:64px;height:666px;align-items:center}"
           + ("ol{display:grid!important;grid-template-columns:1fr 1fr;gap:10px 12px!important}"
              "li{font-size:17px!important;padding:11px 14px!important}" if dos else "")) + """
h1{font-size:64px;margin:18px 0 22px}.sub{font-size:24px;color:var(--suave);line-height:1.4}
ol{list-style:none;display:flex;flex-direction:column;gap:10px}
li{background:var(--panel);border:1px solid var(--borde);border-radius:14px;padding:13px 18px;font-size:19px;display:flex;gap:14px}
.n{color:var(--azul)}"""
    return _pagina(f"<div class='s'><div><div class='eyebrow entra'>{texto_ui('eyebrow')}</div>"
                   f"<h1 class='entra' style='animation-delay:.25s'>{html.escape(titulo)}</h1>"
                   f"<p class='sub entra' style='animation-delay:.5s'>{html.escape(subtitulo)}</p></div>"
                   f"<ol>{items}</ol></div>{_pie(texto_ui('portada'), repo, 0)}", css)


def _foco(ds: list[float], dur: float) -> list[str]:
    """Animacion de cada elemento de una lista: entra cuando se nombra, se atenua cuando
    entra el siguiente (la vista va a lo que suena) y al final vuelven todos (repaso)."""
    final = max(dur * 0.86, (ds[-1] + 1.5) if ds else 0)
    estilos = []
    for k, d in enumerate(ds):
        a = [f"entra .55s cubic-bezier(.2,.7,.2,1) {d:.2f}s forwards"]
        if k + 1 < len(ds) and len(ds) > 2:
            a += [f"apaga .4s {ds[k + 1]:.2f}s forwards", f"enciende .5s {final:.2f}s forwards"]
        estilos.append("animation:" + ",".join(a))
    return estilos


_CSS_FOCO = "@keyframes apaga{from{opacity:1}to{opacity:.42}}@keyframes enciende{from{opacity:.42}to{opacity:1}}"


def _partir(p: str) -> tuple[str, str] | None:
    """"Titulo: texto" -> (titulo, texto) si el titulo es corto; si no, None."""
    titulo, sep, resto = p.partition(": ")
    return (titulo, resto) if sep and resto and len(titulo.replace("`", "")) <= 32 else None


def diapositiva(capitulo: str, titulo: str, puntos: list[str], repo: str, progreso: float, dur: float,
                cifras: list[list[str]] | None = None, disposicion: str = "auto",
                columnas: list[dict] | None = None, destacado: str = "") -> str:
    """`puntos`: frases. `cifras`: [[valor, etiqueta], ...] — hechos medidos, en tarjetas grandes.
    `disposicion`: lista | tarjetas | auto (tarjetas si todos los puntos son "Titulo: texto").
    `columnas`: [{titulo, puntos, color?}] — comparacion lado a lado, en lugar de `puntos`.
    `destacado`: la idea clave, en un recuadro al pie que aparece al final."""
    cifras = cifras or []
    partidos = [_partir(p) for p in puntos]
    if disposicion == "auto":
        disposicion = "tarjetas" if 3 <= len(puntos) <= 6 and all(partidos) and not cifras else "lista"
    n_col = sum(1 + len(c.get("puntos", [])) for c in columnas or [])
    ds = _retrasos(len(cifras) + (n_col if columnas else len(puntos)) + bool(destacado), dur, 0.9)
    tarjetas = "".join(
        f"<div class='cifra entra' style='animation-delay:{ds[i]:.2f}s'><b class='mono'>{html.escape(v)}</b>"
        f"<span>{html.escape(e)}</span></div>" for i, (v, e) in enumerate(cifras))
    off = len(cifras)
    if columnas:
        cols, k = [], off
        for c in columnas:
            color = f"var(--{c.get('color', 'azul')})"
            cab = (f"<h2 class='entra' style='animation-delay:{ds[k]:.2f}s;color:{color}'>"
                   f"{_marcado([c.get('titulo', '')])[0]}</h2>")
            k += 1
            items = []
            for t in _marcado(c.get("puntos", [])):
                items.append(f"<li class='entra' style='animation-delay:{ds[k]:.2f}s'>{t}</li>")
                k += 1
            cols.append(f"<div class='col' style='--c:{color}'>{cab}<ul>{''.join(items)}</ul></div>")
        cuerpo = f"<div class='cols'>{''.join(cols)}</div>"
        off = k
    elif disposicion == "tarjetas":
        estilos = _foco(ds[off:off + len(puntos)], dur)
        cuerpo = "<div class='tarj n" + str(len(puntos)) + "'>" + "".join(
            f"<div class='t' style='{st}'><b>{_marcado([t])[0]}</b><p>{_marcado([r])[0]}</p></div>"
            for (t, r), st in zip(partidos, estilos)) + "</div>"
        off += len(puntos)
    else:
        estilos = _foco(ds[off:off + len(puntos)], dur)
        cuerpo = "<ul>" + "".join(f"<li style='{st}'>{p}</li>" for p, st in zip(_marcado(puntos), estilos)) + "</ul>"
        off += len(puntos)
    caja = (f"<div class='dest entra' style='animation-delay:{max(ds[off], dur * .62):.2f}s'>"
            f"{_marcado([destacado])[0]}</div>" if destacado else "")
    css = """.s{padding:70px 96px 0;height:666px;display:flex;flex-direction:column}
h1{margin:14px 0 30px;max-width:1040px}
.cuerpo{flex:1;display:flex;flex-direction:column;gap:26px;padding:6px 0 34px;min-height:0}
.cifras{display:flex;gap:18px}
.cifra{background:var(--panel);border:1px solid var(--borde);border-radius:16px;padding:18px 24px;min-width:170px;display:flex;flex-direction:column;gap:4px}
.cifra b{font-size:40px;color:var(--verde);font-weight:600}.cifra span{color:var(--suave);font-size:16px}
ul{list-style:none;display:flex;flex-direction:column;gap:16px;max-width:1060px}
li{opacity:0;transform:translateY(14px);font-size:26px;line-height:1.35;padding-left:32px;position:relative}
li::before{content:'';position:absolute;left:0;top:13px;width:11px;height:11px;border-radius:3px;background:var(--azul)}
li code{font-size:22px}
.tarj{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.tarj.n4{grid-template-columns:repeat(2,1fr)}
.t{opacity:0;transform:translateY(14px);background:var(--panel);border:1px solid var(--borde);border-top:3px solid var(--azul);border-radius:14px;padding:22px 24px}
.t b{display:block;font-size:24px;font-weight:650;margin-bottom:8px}.t p{color:#c3c9db;font-size:20px;line-height:1.4}
.t b code{background:none;border:0;padding:0;font-size:.92em;color:var(--ambar)}
.t:nth-child(3n+2){border-top-color:var(--verde)}.t:nth-child(3n+3){border-top-color:var(--ambar)}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(0,1fr));gap:20px}
.col{background:var(--panel);border:1px solid var(--borde);border-top:4px solid var(--c);border-radius:16px;padding:22px 26px}
.col h2{font-size:27px;margin-bottom:16px;opacity:0}.col ul{gap:12px}.col li{font-size:21px}
.col li::before{background:var(--c);top:10px;width:9px;height:9px}
.dest{border:1px solid var(--borde);border-left:4px solid var(--ambar);background:#e0af680d;border-radius:12px;
padding:16px 22px;font-size:22px;line-height:1.4;max-width:1060px}""" + _CSS_FOCO
    return _pagina(f"<div class='s'><div class='eyebrow entra'>{html.escape(capitulo)}</div>"
                   f"<h1 class='entra' style='animation-delay:.2s'>{html.escape(titulo)}</h1><div class='cuerpo'>"
                   f"{'<div class=cifras>' + tarjetas + '</div>' if tarjetas else ''}{cuerpo}{caja}</div></div>"
                   f"{_pie(capitulo, repo, progreso)}", css)


def barras(capitulo: str, titulo: str, datos: list[list], repo: str, progreso: float, dur: float,
           nota: str = "") -> str:
    """Barras horizontales animadas: [[nombre, valor], ...]."""
    maximo = max((v for _, v in datos), default=1) or 1
    ds = _retrasos(len(datos), dur, 0.9)
    filas = "".join(
        f"<div class='fila entra' style='animation-delay:{d:.2f}s'><span class='nom mono'>{html.escape(str(n))}</span>"
        f"<div class='pista'><div class='llena' style='--w:{v / maximo * 100:.1f}%;animation-delay:{d + .2:.2f}s'></div></div>"
        f"<b class='mono'>{v}</b></div>" for (n, v), d in zip(datos, ds))
    css = """.s{padding:70px 96px 0;height:666px}h1{margin:14px 0 34px}
.fila{display:grid;grid-template-columns:420px 1fr 60px;align-items:center;gap:18px;margin-bottom:16px}
.nom{font-size:19px;color:var(--texto);text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;direction:rtl}
.pista{height:26px;background:#ffffff08;border-radius:8px;overflow:hidden}
.llena{height:100%;width:0;border-radius:8px;background:linear-gradient(90deg,var(--azul),var(--verde));animation:crece .9s cubic-bezier(.2,.7,.2,1) forwards}
@keyframes crece{to{width:var(--w)}}b{font-size:22px;color:var(--verde)}
.nota{color:var(--suave);font-size:18px;margin-top:18px}"""
    return _pagina(f"<div class='s'><div class='eyebrow entra'>{html.escape(capitulo)}</div>"
                   f"<h1 class='entra' style='animation-delay:.2s'>{html.escape(titulo)}</h1>{filas}"
                   f"<p class='nota entra' style='animation-delay:{dur * .6:.2f}s'>{html.escape(nota)}</p></div>"
                   f"{_pie(capitulo, repo, progreso)}", css)


def pregunta(capitulo: str, texto: str, respuesta: str, repo: str, progreso: float, dur: float,
             revelar: float, opciones: list[str] | None = None, correcta: int | None = None) -> str:
    """La pregunta, una cuenta atras para pensar, y la respuesta en `revelar` segundos.
    Con `opciones` (tipo test) y `correcta` (indice desde 0): al revelar, la correcta se
    marca en verde y las demas se apagan; `respuesta` explica por que."""
    espera = max(3.0, revelar - 1.0)
    opciones = opciones or []
    ds = _retrasos(len(opciones), max(1.0, revelar - 1.5), 0.9, 0.1)
    ops = "".join(
        f"<li class='op entra{' ok' if k == correcta else ' no'}' style='animation:entra .5s cubic-bezier(.2,.7,.2,1) "
        f"{d:.2f}s forwards,{'acierta' if k == correcta else 'descarta'} .5s {revelar:.2f}s forwards'>"
        f"<span class='l mono'>{'ABCDEFGH'[k]}</span><span>{t}</span></li>"
        for k, (t, d) in enumerate(zip(_marcado(opciones), ds)))
    q = 34 if opciones else 40
    css = f""".s{{padding:{70 if opciones else 90}px 110px 0;height:666px;display:flex;flex-direction:column;gap:{22 if opciones else 34}px}}
.cab{{display:flex;align-items:center;gap:16px}}
.q{{font-size:{q}px;line-height:1.25;font-weight:600;max-width:1040px}}
.reloj{{width:{40 if opciones else 74}px;height:{40 if opciones else 74}px;animation:entra .5s .6s forwards,fuera .4s {revelar:.2f}s forwards}}
.reloj circle{{fill:none;stroke-width:6}}
.fondo{{stroke:#ffffff14}}.anillo{{stroke:var(--ambar);stroke-dasharray:201;stroke-dashoffset:0;transform:rotate(-90deg);transform-origin:50% 50%;
animation:cuenta {espera:.2f}s linear .8s forwards}}@keyframes cuenta{{to{{stroke-dashoffset:201}}}}
@keyframes fuera{{to{{opacity:0;transform:scale(.6)}}}}
ol{{list-style:none;display:grid;grid-template-columns:{'1fr 1fr' if sum(len(o) for o in opciones) > 160 else '1fr'};gap:10px;max-width:1060px}}
.op{{display:flex;gap:14px;align-items:baseline;background:var(--panel);border:1px solid var(--borde);border-radius:12px;padding:12px 18px;font-size:21px;line-height:1.35}}
.op .l{{color:var(--azul);font-weight:700}}
@keyframes acierta{{from{{opacity:1}}to{{opacity:1;border-color:var(--verde);background:#9ece6a1c;box-shadow:0 0 0 1px var(--verde)}}}}
@keyframes descarta{{from{{opacity:1}}to{{opacity:.38}}}}
.r{{background:var(--panel);border:1px solid var(--borde);border-left:4px solid var(--verde);border-radius:14px;padding:{'16px 22px' if opciones else '22px 26px'};font-size:{21 if opciones else 26}px;line-height:1.4;max-width:1060px}}
.r small{{display:block;color:var(--verde);letter-spacing:.12em;text-transform:uppercase;font-size:13px;margin-bottom:8px;font-weight:600}}"""
    reloj = (f"<svg class='reloj' style='opacity:0' viewBox='0 0 74 74'><circle class='fondo' cx='37' cy='37' r='32'/>"
             f"<circle class='anillo' cx='37' cy='37' r='32'/></svg>")
    return _pagina(f"<div class='s'><div class='cab'><div class='eyebrow entra'>{texto_ui('comprueba')}</div>"
                   f"{reloj if opciones else ''}</div>"
                   f"<div class='q entra' style='animation-delay:.2s'>{html.escape(texto)}</div>"
                   f"{'<ol>' + ops + '</ol>' if opciones else reloj}"
                   f"<div class='r entra' style='animation-delay:{revelar:.2f}s'><small>{texto_ui('respuesta')}</small>{_marcado([respuesta])[0]}</div></div>"
                   f"{_pie(capitulo, repo, progreso)}", css)


def terminal(capitulo: str, cmd: str, salida: str, repo: str, progreso: float, dur: float,
             filtro: str = "") -> str:
    """La salida real, escrita linea a linea con scroll. `filtro`: regex de lineas a
    quitar (p.ej. los tests entre los llamantes), para que quepa lo que se narra."""
    import re as _re
    lineas = [ln for ln in salida.splitlines() if not (filtro and _re.search(filtro, ln))][:120]
    escribir = min(2.5, 0.045 * len(cmd))
    paso = max(0.02, min(0.09, (dur * 0.55) / max(1, len(lineas))))
    css = """.v{position:absolute;left:56px;right:56px;top:40px;bottom:78px;background:#0a0e18;border:1px solid var(--borde);
border-radius:14px;overflow:hidden;box-shadow:0 30px 80px #0008}
.t{height:40px;background:#141a2b;display:flex;align-items:center;gap:8px;padding:0 16px;color:var(--suave);font-size:14px}
.d{width:12px;height:12px;border-radius:50%}#o{padding:18px 24px;font-size:17px;line-height:1.45;white-space:pre-wrap;word-break:break-word;color:#cfd5e6;height:calc(100% - 40px);overflow:hidden}
.p{color:var(--verde)}.c{color:#fff}"""
    js = f"""const CMD={json.dumps(cmd)},L={json.dumps(lineas)};const o=document.getElementById('o');
o.innerHTML="<span class='p'>$ </span><span class='c' id='c'></span>";let i=0;
function t(){{if(i<CMD.length){{document.getElementById('c').textContent+=CMD[i++];setTimeout(t,{escribir * 1000 / max(1, len(cmd)):.0f});}}else setTimeout(s,400)}}
let j=0;function s(){{if(j<L.length){{o.appendChild(document.createTextNode('\\n'+L[j++]));o.scrollTop=o.scrollHeight;setTimeout(s,{paso * 1000:.0f})}}}}
setTimeout(t,500);"""
    return _pagina(f"<div class='v'><div class='t'><span class='d' style='background:#f7768e'></span>"
                   f"<span class='d' style='background:#e0af68'></span><span class='d' style='background:#9ece6a'></span>"
                   f"<span style='margin-left:10px' class='mono'>{html.escape(repo)}</span></div><div id='o' class='mono'></div></div>"
                   f"{_pie(capitulo, repo, progreso)}<script>{js}</script>", css)


ESTILOS = {  # estilo de flecha: (color, trazo discontinuo, nombre en la leyenda)
    "flujo": ("var(--azul)", "", ""),
    "dinero": ("var(--verde)", "", "dinero"),
    "riesgo": ("var(--ambar)", "", "riesgo"),
    "siniestro": ("var(--rosa)", "", "siniestros"),
    "info": ("var(--suave)", "7 6", "información"),
}


def _ancho(n: dict, base: int = 210, compacto: bool = False) -> float:
    """Lo bastante ancha para su texto (21px seminegrita ~11.5 px/letra; sub ~7.6)."""
    k = .86 if compacto else 1
    return n.get("w") or min(330, max(base * k, len(n["texto"]) * 11.5 * k + 36, len(n.get("sub", "")) * 7.6 * k + 30))


def _colocar(nodos: list[dict], flechas: list[dict], direccion: str = "horizontal") -> tuple[list[dict], bool]:
    """x, y (0..1) para los nodos que no los traen, y si hace falta el modo compacto.

    Por capas siguiendo las flechas (cada nodo, una capa despues del ultimo que le
    apunta). Las capas se reparten con el ancho real de sus cajas; dentro de una capa,
    cada caja va cerca de la media de las que le apuntan, con paso fijo, para que las
    flechas sean cortas y se crucen poco."""
    if all("x" in n and "y" in n for n in nodos):
        return nodos, False
    ids = [n["id"] for n in nodos]
    por_id = {n["id"]: n for n in nodos}
    entran = {i: [f["de"] for f in flechas if f["a"] == i and f["de"] in ids and f["de"] != i] for i in ids}
    capa: dict[str, int] = {}

    def nivel(i, visto=()):
        if i not in capa:
            capa[i] = max((nivel(o, visto + (i,)) + 1 for o in entran[i] if o not in visto), default=0)
        return capa[i]

    for i in ids:
        nivel(i)
    capas = [[i for i in ids if capa[i] == c] for c in range(max(capa.values()) + 1)]
    horizontal = direccion != "vertical"
    X0, Y0, AN, AL, H = 110, 205, 1060, 395, 72  # el lienzo de `diagrama`

    def medidas(compacto):
        anchos = {i: _ancho(por_id[i], compacto=compacto) for i in ids}
        if horizontal:
            tam = [max(anchos[i] for i in c) for c in capas]
            hueco = (1200 - sum(tam)) / max(1, len(capas) - 1)
        else:
            tam = [H * (.84 if compacto else 1)] * len(capas)
            hueco = (AL + H - sum(tam)) / max(1, len(capas) - 1)
        return anchos, tam, hueco

    compacto = False
    anchos, tam, hueco = medidas(False)
    if len(capas) > 1 and hueco < (70 if horizontal else 48):
        compacto = True
        anchos, tam, hueco = medidas(True)
    # eje de las capas: centros en pixeles
    if len(capas) == 1:
        largo = [X0 + AN / 2] if horizontal else [Y0 + AL / 2]
    else:
        inicio = 40 if horizontal else Y0 - H / 2
        largo, pos = [], inicio
        for t in tam:
            largo.append(pos + t / 2)
            pos += t + hueco
    # eje transversal: cerca de la media de los padres, con paso fijo
    centro_t = X0 + AN / 2 if not horizontal else Y0 + AL / 2
    lim = (X0 - 70, X0 + AN + 70) if not horizontal else (Y0, Y0 + AL)
    trans: dict[str, float] = {}
    for c in capas:
        def deseo(i):
            padres = [trans[o] for o in entran[i] if o in trans]
            return sum(padres) / len(padres) if padres else centro_t
        c.sort(key=lambda i: (deseo(i), ids.index(i)))
        if horizontal:
            paso = min(150, AL / max(1, len(c) - 1)) if len(c) > 1 else 0
        else:
            paso = max(anchos[i] for i in c) + 60
        media = sum(deseo(i) for i in c) / len(c)
        bloque = paso * (len(c) - 1)
        primero = min(max(media - bloque / 2, lim[0]), lim[1] - bloque)
        for k, i in enumerate(c):
            trans[i] = primero + k * paso
    salida = []
    for n in nodos:
        if "x" in n and "y" in n:
            salida.append(n)
            continue
        c = capa[n["id"]]
        cx, cy = (largo[c], trans[n["id"]]) if horizontal else (trans[n["id"]], largo[c])
        salida.append({**n, "x": (cx - X0) / AN, "y": (cy - Y0) / AL})
    return salida, compacto


def diagrama(capitulo: str, titulo: str, nodos: list[dict], flechas: list[dict], repo: str, progreso: float,
             dur: float, nota: str = "", direccion: str = "horizontal") -> str:
    """Cajas y flechas animadas. `nodos`: {id, texto, sub?, x?, y?, color?, w?} con x, y en
    0..1 dentro del lienzo; sin ellos se colocan solos por capas (`direccion`:
    horizontal, de izquierda a derecha, o vertical, de arriba abajo). El ancho se ajusta
    al texto salvo que se de `w`. `flechas`: {de, a, texto?, estilo?, curva?} — `curva` (px)
    separa dos flechas entre los mismos nodos. Todo admite `paso`: lo del mismo paso
    aparece junto, y los pasos se reparten en la narracion. Por defecto los nodos salen
    en el paso 0 y cada flecha en el suyo, en orden."""
    import math
    x0, y0, an, al, w, h = 110, 205, 1060, 395, 210, 72
    nodos, compacto = _colocar(nodos, flechas, direccion)
    if compacto:
        h = 60
    caja = {n["id"]: (x0 + n["x"] * an, y0 + n["y"] * al, _ancho(n, w, compacto) / 2, h / 2) for n in nodos}
    flechas = [{"paso": i + 1, **f} for i, f in enumerate(flechas)]
    pasos = sorted({n.get("paso", 0) for n in nodos} | {f["paso"] for f in flechas})
    ds = dict(zip(pasos, _retrasos(len(pasos), dur, 0.9)))

    def borde(cx, cy, hw, hh, hacia):
        dx, dy = hacia[0] - cx, hacia[1] - cy
        t = min(hw / abs(dx) if dx else 1e9, hh / abs(dy) if dy else 1e9)
        k = 1 + 8 / max(1e-6, math.hypot(dx * t, dy * t))
        return cx + dx * t * k, cy + dy * t * k

    partes = []
    for f in flechas:
        (ax, ay, ahw, ahh), (bx, by, bhw, bhh) = caja[f["de"]], caja[f["a"]]
        mx, my, largo = (ax + bx) / 2, (ay + by) / 2, math.hypot(bx - ax, by - ay) or 1
        curva = f.get("curva", 0)
        c = (mx - (by - ay) / largo * curva * 2, my + (bx - ax) / largo * curva * 2)
        s, e = borde(ax, ay, ahw, ahh, c), borde(bx, by, bhw, bhh, c)
        ux, uy = e[0] - c[0], e[1] - c[1]
        u = math.hypot(ux, uy) or 1
        ux, uy = ux / u, uy / u
        punta = (f"{e[0]:.1f},{e[1]:.1f} {e[0] - 13 * ux - 6 * uy:.1f},{e[1] - 13 * uy + 6 * ux:.1f} "
                 f"{e[0] - 13 * ux + 6 * uy:.1f},{e[1] - 13 * uy - 6 * ux:.1f}")
        e2 = (e[0] - 10 * ux, e[1] - 10 * uy)
        color, discont, _ = ESTILOS.get(f.get("estilo", "flujo"), ESTILOS["flujo"])
        d = ds[f["paso"]]
        trazo = (f"stroke-dasharray:{discont};opacity:0;animation:entra .5s {d:.2f}s forwards" if discont
                 else f"stroke-dasharray:1;stroke-dashoffset:1;animation:traza .7s ease-out {d:.2f}s forwards")
        largo_attr = "" if discont else " pathLength='1'"
        lx, ly = .25 * s[0] + .5 * c[0] + .25 * e2[0], .25 * s[1] + .5 * c[1] + .25 * e2[1]
        ancla = "middle"
        texto = f.get("texto", "")
        vertical = abs(by - ay) > abs(bx - ax)
        if texto and (vertical or math.hypot(e2[0] - s[0], e2[1] - s[1]) < len(texto) * 8.6 + 16):
            # flecha corta o vertical: la etiqueta no cabe sobre la linea; la primera
            # posicion junto a la flecha que no pise ninguna caja
            ancho_t = len(texto) * 8.6
            lado = "end" if (c[0] < mx or (not vertical and by < ay)) else "start"
            candidatas = ([(lx - 12, ly, "end"), (lx + 12, ly, "start")] if vertical and lado == "end" else
                          [(lx + 12, ly, "start"), (lx - 12, ly, "end")] if vertical else
                          [(lx, ly - 16, "middle"), (lx + 10, ly - 10, "start"), (lx - 10, ly - 10, "end"),
                           (lx, ly + 22, "middle")])
            candidatas.append((lx, min(ay - ahh, by - bhh) - 14, "middle"))

            def pisa(x, y, a):
                x1 = x - ancho_t / 2 if a == "middle" else x - ancho_t if a == "end" else x
                return any(x1 < cx + hw and cx - hw < x1 + ancho_t and y - 9 < cy + hh and cy - hh < y + 9
                           for cx, cy, hw, hh in caja.values())

            lx, ly, ancla = next((cand for cand in candidatas if not pisa(*cand)), candidatas[-1])
        etiqueta = (f"<text class='et entra' x='{lx:.1f}' y='{ly + 5:.1f}' style='fill:{color};text-anchor:{ancla};"
                    f"animation-delay:{d + .4:.2f}s'>"
                    f"{html.escape(f['texto'])}</text>" if f.get("texto") else "")
        partes.append(f"<path d='M{s[0]:.1f},{s[1]:.1f} Q{c[0]:.1f},{c[1]:.1f} {e2[0]:.1f},{e2[1]:.1f}'{largo_attr} "
                      f"style='stroke:{color};{trazo}'/><polygon class='entra' points='{punta}' "
                      f"style='fill:{color};animation-delay:{d + .55:.2f}s'/>{etiqueta}")
    for n in nodos:
        cx, cy, hw, hh = caja[n["id"]]
        color = f"var(--{n.get('color', 'azul')})"
        texto_y = cy + ((-3 if n.get("sub") else 7) if not compacto else (-2 if n.get("sub") else 6))
        sub = (f"<text class='sub' x='{cx:.1f}' y='{cy + (21 if not compacto else 17):.1f}'>{html.escape(n['sub'])}</text>" if n.get("sub") else "")
        partes.append(f"<g class='nodo entra' style='animation-delay:{ds[n.get('paso', 0)]:.2f}s'>"
                      f"<rect x='{cx - hw:.1f}' y='{cy - hh:.1f}' width='{2 * hw:.1f}' height='{2 * hh:.1f}' rx='14' "
                      f"style='stroke:{color};color:{color};animation:brilla 1.6s ease-out {ds[n.get('paso', 0)] + .2:.2f}s'/><text class='nt' x='{cx:.1f}' y='{texto_y:.1f}'>{html.escape(n['texto'])}</text>"
                      f"{sub}</g>")
    usados = [ESTILOS[e] for e in dict.fromkeys(f.get("estilo", "flujo") for f in flechas)
              if e in ESTILOS and ESTILOS[e][2]]
    leyenda = "".join(f"<span><i style='background:{c}'></i>{html.escape(texto_ui(n))}</span>" for c, _, n in usados)
    pie_nota = (f"<p class='nota entra' style='animation-delay:{dur * .7:.2f}s'>{html.escape(nota)}</p>" if nota else "")
    css = """.s{padding:70px 96px 0;height:666px;position:relative}h1{margin:14px 0 0;font-size:44px}
svg{position:absolute;left:0;top:0;width:1280px;height:720px}
rect{fill:var(--panel);stroke-width:2}path{fill:none;stroke-width:3;stroke-linecap:round}
@keyframes traza{to{stroke-dashoffset:0}}
@keyframes brilla{0%{filter:none}25%{filter:drop-shadow(0 0 10px currentColor)}100%{filter:none}}
.nt{fill:var(--texto);font-size:21px;font-weight:600;text-anchor:middle}
.sub{fill:var(--suave);font-size:14.5px;text-anchor:middle}
.compacto .nt{font-size:18px}.compacto .sub{font-size:12.5px}
.et{font-size:16px;font-weight:600;text-anchor:middle;paint-order:stroke;stroke:var(--bg);stroke-width:7px;stroke-linejoin:round}
.ley{position:absolute;right:96px;top:84px;display:flex;gap:18px;color:var(--suave);font-size:15px}
.ley i{display:inline-block;width:18px;height:4px;border-radius:2px;margin-right:7px;vertical-align:middle}
.nota{position:absolute;left:96px;right:96px;bottom:76px;color:var(--suave);font-size:18px}"""
    return _pagina(f"<svg viewBox='0 0 {ANCHO} {ALTO}'{' class=compacto' if compacto else ''}>{''.join(partes)}</svg>"
                   f"<div class='s'><div class='eyebrow entra'>{html.escape(capitulo)}</div>"
                   f"<h1 class='entra' style='animation-delay:.2s'>{html.escape(titulo)}</h1>"
                   f"{'<div class=ley>' + leyenda + '</div>' if leyenda else ''}</div>"
                   f"{pie_nota}{_pie(capitulo, repo, progreso)}", css)


def _marcado(textos: list[str]) -> list[str]:
    """Escapa y convierte `codigo` en <code>. Nada mas: el guion no trae HTML."""
    salida = []
    for t in textos:
        partes = html.escape(t).split("`")
        salida.append("".join(f"<code>{p}</code>" if i % 2 else p for i, p in enumerate(partes)))
    return salida


_REVISAR = r"""() => {
const av = [], caja = el => el.getBoundingClientRect();
const corta = (a, b, m = 0) => a.left < b.right - m && b.left < a.right - m && a.top < b.bottom - m && b.top < a.bottom - m;
const nombre = el => (el.textContent || el.tagName).trim().replace(/\s+/g, ' ').slice(0, 40);
const pie = document.querySelector('.pie');
const tope = pie ? caja(pie).top : 720;
for (const el of document.querySelectorAll('.s *, .nota, svg text, svg rect')) {
  if (el.closest('.pie') || el.closest('#o')) continue;
  const r = caja(el);
  if (!r.width || !r.height) continue;
  if (r.right > 1281 || r.left < -1 || r.top < -1) av.push(`se sale del lienzo: "${nombre(el)}"`);
  else if (r.bottom > tope + 1 && !el.closest('ol')) av.push(`pisa el pie: "${nombre(el)}"`);
  else if (r.bottom > 721) av.push(`se sale por abajo: "${nombre(el)}"`);
}
for (const el of document.querySelectorAll('.nom, li, .cifra span, h1, .q, .r'))
  if (el.scrollWidth > el.clientWidth + 2 && getComputedStyle(el).overflow === 'hidden') av.push(`texto cortado: "${nombre(el)}"`);
const cajas = [...document.querySelectorAll('svg rect')], textos = [...document.querySelectorAll('svg text.et')];
for (let i = 0; i < cajas.length; i++) for (let j = i + 1; j < cajas.length; j++)
  if (corta(caja(cajas[i]), caja(cajas[j]))) av.push(`cajas solapadas: "${nombre(cajas[i].parentNode)}" y "${nombre(cajas[j].parentNode)}"`);
for (const t of textos) {
  for (const c of cajas) if (corta(caja(t), caja(c), 2)) av.push(`etiqueta sobre caja: "${nombre(t)}" / "${nombre(c.parentNode)}"`);
  for (const u of textos) if (u !== t && t.compareDocumentPosition(u) & 4 && corta(caja(t), caja(u), 1)) av.push(`etiquetas solapadas: "${nombre(t)}" / "${nombre(u)}"`);
}
for (const n of document.querySelectorAll('svg g')) {
  const [r, ...ts] = n.querySelectorAll('rect, text');
  for (const t of ts) if (r && caja(t).width > caja(r).width - 8) av.push(`texto mas ancho que su caja: "${nombre(t)}"`);
}
return [...new Set(av)];
}"""


def revisar(pagina) -> list[str]:
    """Avisos de maquetacion sobre una pagina de Playwright ya en su estado final:
    lo que se sale, lo que se corta y lo que se pisa en los diagramas."""
    return pagina.evaluate(_REVISAR)


_REVISAR = """() => {
  const av = [], R = e => e.getBoundingClientRect(), nombre = e => (e.textContent || '').trim().slice(0, 40);
  const cruza = (a, b, m = 0) => a.left < b.right - m && b.left < a.right - m && a.top < b.bottom - m && b.top < a.bottom - m;
  const pie = 666;
  if (document.body.scrollHeight > 722 || document.body.scrollWidth > 1282) av.push('la pagina desborda 1280x720');
  for (const e of document.querySelectorAll('.s > *, li, .cifra, .fila, .r, .q, .nota, .ley')) {
    const r = R(e);
    if (r.height && r.bottom > pie + 1 && !e.closest('svg')) av.push(`"${nombre(e)}" pisa el pie (${Math.round(r.bottom)}px > ${pie})`);
    if (r.right > 1281) av.push(`"${nombre(e)}" se sale por la derecha`);
  }
  for (const e of document.querySelectorAll('.nom, .cifra b, .cifra span'))
    if (e.scrollWidth > e.clientWidth + 1) av.push(`"${nombre(e)}" no cabe y se corta`);
  const cajas = [...document.querySelectorAll('svg g.nodo')].map(g => ({g, r: R(g.querySelector('rect')), t: [...g.querySelectorAll('text')]}));
  for (const c of cajas) {
    for (const t of c.t) if (R(t).width > c.r.width - 12) av.push(`el texto "${nombre(t)}" no cabe en su caja`);
    if (c.r.left < 12 || c.r.right > 1268 || c.r.top < 150 || c.r.bottom > pie - 4) av.push(`la caja "${nombre(c.t[0])}" se sale del lienzo`);
  }
  for (let i = 0; i < cajas.length; i++) for (let j = i + 1; j < cajas.length; j++)
    if (cruza(cajas[i].r, cajas[j].r, -6)) av.push(`las cajas "${nombre(cajas[i].t[0])}" y "${nombre(cajas[j].t[0])}" se tocan`);
  const ets = [...document.querySelectorAll('svg text.et')];
  for (const t of ets) {
    const r = R(t);
    for (const c of cajas) if (cruza(r, c.r, 2)) av.push(`la etiqueta "${nombre(t)}" pisa la caja "${nombre(c.t[0])}"`);
    if (r.left < 20 || r.right > 1260) av.push(`la etiqueta "${nombre(t)}" se sale del lienzo`);
  }
  for (let i = 0; i < ets.length; i++) for (let j = i + 1; j < ets.length; j++)
    if (cruza(R(ets[i]), R(ets[j]), 2)) av.push(`las etiquetas "${nombre(ets[i])}" y "${nombre(ets[j])}" se pisan`);
  const ley = document.querySelector('.ley'), h1 = document.querySelector('h1');
  if (ley && h1 && cruza(R(ley), R(h1))) av.push('la leyenda pisa el titulo');
  return [...new Set(av)];
}"""


def revisar(pagina) -> list[str]:
    """Problemas de maquetacion en el fotograma final (pagina de Playwright ya cargada):
    texto que se sale o se corta, cajas o etiquetas que se pisan, cosas sobre el pie."""
    return pagina.evaluate(_REVISAR)
