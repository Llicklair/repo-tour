"""Las escenas que no son VS Code: HTML de 1280x720, animado al ritmo de la voz.

Cada escena recibe su duracion (la de su narracion) y reparte sus apariciones a
lo largo de ella, para que lo que se ve llegue cuando se nombra.
"""
from __future__ import annotations

import html
import json

ANCHO, ALTO = 1280, 720

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
    css = """.s{padding:88px 96px;display:grid;grid-template-columns:1.25fr 1fr;gap:64px;height:666px;align-items:center}
h1{font-size:64px;margin:18px 0 22px}.sub{font-size:24px;color:var(--suave);line-height:1.4}
ol{list-style:none;display:flex;flex-direction:column;gap:10px}
li{background:var(--panel);border:1px solid var(--borde);border-radius:14px;padding:13px 18px;font-size:19px;display:flex;gap:14px}
.n{color:var(--azul)}"""
    return _pagina(f"<div class='s'><div><div class='eyebrow entra'>Un recorrido para aprender</div>"
                   f"<h1 class='entra' style='animation-delay:.25s'>{html.escape(titulo)}</h1>"
                   f"<p class='sub entra' style='animation-delay:.5s'>{html.escape(subtitulo)}</p></div>"
                   f"<ol>{items}</ol></div>{_pie('Portada', repo, 0)}", css)


def diapositiva(capitulo: str, titulo: str, puntos: list[str], repo: str, progreso: float, dur: float,
                cifras: list[list[str]] | None = None) -> str:
    """`puntos`: frases. `cifras`: [[valor, etiqueta], ...] — hechos medidos, en tarjetas grandes."""
    ds = _retrasos(len(puntos) + len(cifras or []), dur, 0.9)
    tarjetas = "".join(
        f"<div class='cifra entra' style='animation-delay:{ds[i]:.2f}s'><b class='mono'>{html.escape(v)}</b>"
        f"<span>{html.escape(e)}</span></div>" for i, (v, e) in enumerate(cifras or []))
    off = len(cifras or [])
    lis = "".join(f"<li class='entra' style='animation-delay:{ds[off + i]:.2f}s'>{p}</li>"
                  for i, p in enumerate(_marcado(puntos)))
    css = """.s{padding:70px 96px 0;height:666px;display:flex;flex-direction:column}
h1{margin:14px 0 34px;max-width:1000px}
.cifras{display:flex;gap:18px;margin-bottom:30px}
.cifra{background:var(--panel);border:1px solid var(--borde);border-radius:16px;padding:18px 24px;min-width:170px;display:flex;flex-direction:column;gap:4px}
.cifra b{font-size:40px;color:var(--verde);font-weight:600}.cifra span{color:var(--suave);font-size:16px}
ul{list-style:none;display:flex;flex-direction:column;gap:14px;max-width:1060px}
li{font-size:25px;line-height:1.35;padding-left:30px;position:relative}
li::before{content:'';position:absolute;left:0;top:13px;width:11px;height:11px;border-radius:3px;background:var(--azul)}
li code{background:#ffffff10;border:1px solid var(--borde);border-radius:6px;padding:1px 7px;font-size:21px;color:var(--ambar)}"""
    return _pagina(f"<div class='s'><div class='eyebrow entra'>{html.escape(capitulo)}</div>"
                   f"<h1 class='entra' style='animation-delay:.2s'>{html.escape(titulo)}</h1>"
                   f"{'<div class=cifras>' + tarjetas + '</div>' if tarjetas else ''}<ul>{lis}</ul></div>"
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
             revelar: float) -> str:
    """La pregunta, una cuenta atras para pensar, y la respuesta en `revelar` segundos."""
    espera = max(3.0, revelar - 1.0)
    css = f""".s{{padding:90px 110px 0;height:666px;display:flex;flex-direction:column;gap:34px}}
.q{{font-size:40px;line-height:1.25;font-weight:600;max-width:1020px}}
.reloj{{width:74px;height:74px}}.reloj circle{{fill:none;stroke-width:6}}
.fondo{{stroke:#ffffff14}}.anillo{{stroke:var(--ambar);stroke-dasharray:201;stroke-dashoffset:0;transform:rotate(-90deg);transform-origin:50% 50%;
animation:cuenta {espera:.2f}s linear .8s forwards}}@keyframes cuenta{{to{{stroke-dashoffset:201}}}}
.r{{background:var(--panel);border:1px solid var(--borde);border-left:4px solid var(--verde);border-radius:14px;padding:22px 26px;font-size:26px;line-height:1.4;max-width:1060px}}
.r small{{display:block;color:var(--verde);letter-spacing:.12em;text-transform:uppercase;font-size:13px;margin-bottom:8px;font-weight:600}}"""
    return _pagina(f"<div class='s'><div class='eyebrow entra'>Comprueba que lo has entendido</div>"
                   f"<div class='q entra' style='animation-delay:.2s'>{html.escape(texto)}</div>"
                   f"<svg class='reloj entra' style='animation-delay:.6s' viewBox='0 0 74 74'><circle class='fondo' cx='37' cy='37' r='32'/>"
                   f"<circle class='anillo' cx='37' cy='37' r='32'/></svg>"
                   f"<div class='r entra' style='animation-delay:{revelar:.2f}s'><small>Respuesta</small>{_marcado([respuesta])[0]}</div></div>"
                   f"{_pie(capitulo, repo, progreso)}", css)


def terminal(capitulo: str, cmd: str, salida: str, repo: str, progreso: float, dur: float) -> str:
    lineas = salida.splitlines()[-24:]
    escribir = min(2.5, 0.045 * len(cmd))
    paso = max(0.02, min(0.09, (dur * 0.55) / max(1, len(lineas))))
    css = """.v{position:absolute;left:56px;right:56px;top:40px;bottom:78px;background:#0a0e18;border:1px solid var(--borde);
border-radius:14px;overflow:hidden;box-shadow:0 30px 80px #0008}
.t{height:40px;background:#141a2b;display:flex;align-items:center;gap:8px;padding:0 16px;color:var(--suave);font-size:14px}
.d{width:12px;height:12px;border-radius:50%}#o{padding:18px 24px;font-size:17px;line-height:1.45;white-space:pre-wrap;word-break:break-word;color:#cfd5e6}
.p{color:var(--verde)}.c{color:#fff}"""
    js = f"""const CMD={json.dumps(cmd)},L={json.dumps(lineas)};const o=document.getElementById('o');
o.innerHTML="<span class='p'>$ </span><span class='c' id='c'></span>";let i=0;
function t(){{if(i<CMD.length){{document.getElementById('c').textContent+=CMD[i++];setTimeout(t,{escribir * 1000 / max(1, len(cmd)):.0f});}}else setTimeout(s,400)}}
let j=0;function s(){{if(j<L.length){{o.appendChild(document.createTextNode('\\n'+L[j++]));setTimeout(s,{paso * 1000:.0f})}}}}
setTimeout(t,500);"""
    return _pagina(f"<div class='v'><div class='t'><span class='d' style='background:#f7768e'></span>"
                   f"<span class='d' style='background:#e0af68'></span><span class='d' style='background:#9ece6a'></span>"
                   f"<span style='margin-left:10px' class='mono'>{html.escape(repo)}</span></div><div id='o' class='mono'></div></div>"
                   f"{_pie(capitulo, repo, progreso)}<script>{js}</script>", css)


def _marcado(textos: list[str]) -> list[str]:
    """Escapa y convierte `codigo` en <code>. Nada mas: el guion no trae HTML."""
    salida = []
    for t in textos:
        partes = html.escape(t).split("`")
        salida.append("".join(f"<code>{p}</code>" if i % 2 else p for i, p in enumerate(partes)))
    return salida
