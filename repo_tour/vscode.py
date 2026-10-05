"""VS Code de verdad en el video: `code serve-web` en local, manejado por Playwright.

La navegacion no usa "ir a la definicion" (exigiria la extension del lenguaje):
salta a fichero:linea con los datos de `hechos`, que ya son el hecho de donde vive cada
simbolo y cada llamante. Lo que se ve es lo que dice el grafo.

Pasos de una escena `vscode` (el guion los escribe; se reparten en su narracion):
  {"abrir": "src/pkg/mod.py", "linea": 40}   abre el fichero y centra esa linea
  {"resaltar": [40, 62]}                      selecciona ese rango del fichero abierto
  {"buscar": "texto"}                         busqueda global: los usos, en la barra lateral
  {"explorador": true}                        vuelve al arbol de ficheros
  {"bajar": 15}                               desplaza el editor N lineas
"""
from __future__ import annotations

import json
import socket
import subprocess
import time
from pathlib import Path
from urllib.parse import quote

PUERTO = 8791  # 8765 es del Voice Bridge de AIOS
AQUI = Path(__file__).resolve().parent.parent
DATOS_SERVIDOR = AQUI / ".vscode-server-data"
NAVEGADOR = AQUI / ".navegador"

AJUSTES = {
    "workbench.colorTheme": "Default Dark Modern",
    "security.workspace.trust.enabled": False,
    "chat.disableAIFeatures": True,
    "workbench.startupEditor": "none",
    "workbench.tips.enabled": False,
    "workbench.welcomePage.walkthroughs.openOnInstall": False,
    "extensions.ignoreRecommendations": True,
    "editor.minimap.enabled": False,
    "editor.fontSize": 17,
    "editor.lineHeight": 1.6,
    "editor.cursorBlinking": "solid",
    "editor.renderWhitespace": "none",
    "editor.stickyScroll.enabled": False,
    "workbench.editor.enablePreview": False,
    "window.commandCenter": False,
    "workbench.layoutControl.enabled": False,
    "workbench.activityBar.location": "default",
    "telemetry.telemetryLevel": "off",
    "update.showReleaseNotes": False,
    "files.exclude": {"**/__pycache__": True, "**/.pytest_cache": True, "**/*.egg-info": True},
    "explorer.autoReveal": True,
    "search.showLineNumbers": True,
}


def _escucha(puerto: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", puerto)) == 0


class Servidor:
    """Arranca `code serve-web` si no esta ya escuchando; lo para al salir solo si lo arranco el."""

    def __init__(self, puerto: int = PUERTO):
        self.puerto, self.proceso = puerto, None

    def __enter__(self):
        if not _escucha(self.puerto):
            DATOS_SERVIDOR.mkdir(exist_ok=True)
            self.proceso = subprocess.Popen(
                ["code", "serve-web", "--host", "127.0.0.1", "--port", str(self.puerto),
                 "--without-connection-token", "--accept-server-license-terms",
                 "--server-data-dir", str(DATOS_SERVIDOR)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
            for _ in range(120):
                if _escucha(self.puerto):
                    break
                time.sleep(0.5)
        return self

    def __exit__(self, *exc):
        if self.proceso:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(self.proceso.pid)], capture_output=True)

    def url(self, repo: Path) -> str:
        return f"http://127.0.0.1:{self.puerto}/?folder=" + quote("/" + repo.as_posix())


def _abrir_workbench(pg, url: str):
    pg.goto(url, timeout=240_000)
    pg.wait_for_selector(".monaco-workbench", timeout=240_000)
    pg.wait_for_selector(".explorer-folders-view, .explorer-viewlet", timeout=120_000)
    time.sleep(3)


def _comando(pg, nombre: str):
    pg.keyboard.press("F1")
    time.sleep(0.5)
    pg.keyboard.type(nombre, delay=8)
    time.sleep(0.7)
    pg.keyboard.press("Enter")
    time.sleep(0.8)


def preparar(servidor: Servidor, repo: Path, playwright) -> None:
    """Deja los ajustes del video en el perfil del navegador (una vez; se recuerdan)."""
    marca = NAVEGADOR / "ajustes.json"
    if marca.is_file() and json.loads(marca.read_text(encoding="utf-8")) == AJUSTES:
        return
    ctx = playwright.chromium.launch_persistent_context(
        str(NAVEGADOR), viewport={"width": 1280, "height": 720},
        permissions=["clipboard-read", "clipboard-write"])
    pg = ctx.pages[0] if ctx.pages else ctx.new_page()
    _abrir_workbench(pg, servidor.url(repo))
    _comando(pg, "Preferences: Open User Settings (JSON)")
    time.sleep(1.5)
    pg.evaluate("t => navigator.clipboard.writeText(t)", json.dumps(AJUSTES, indent=2))
    pg.keyboard.press("Control+A")
    pg.keyboard.press("Control+V")
    time.sleep(0.5)
    pg.keyboard.press("Control+S")
    time.sleep(1)
    _comando(pg, "View: Close All Editors")
    ctx.close()
    marca.write_text(json.dumps(AJUSTES), encoding="utf-8")


class Editor:
    """Una sesion grabada de VS Code: las escenas se ejecutan seguidas y se anota
    cuando empieza cada una, para cortar el video despues."""

    def __init__(self, servidor: Servidor, repo: Path, playwright, carpeta_video: Path):
        self.repo = repo
        self.ctx = playwright.chromium.launch_persistent_context(
            str(NAVEGADOR), viewport={"width": 1280, "height": 720},
            record_video_dir=str(carpeta_video), record_video_size={"width": 1280, "height": 720})
        self.pg = self.ctx.pages[0] if self.ctx.pages else self.ctx.new_page()
        self.t0 = time.monotonic()
        _abrir_workbench(self.pg, servidor.url(repo))
        _comando(self.pg, "Notifications: Clear All Notifications")
        _comando(self.pg, "View: Close All Editors")
        self.pg.keyboard.press("Control+Shift+E")
        time.sleep(1)

    def ahora(self) -> float:
        return time.monotonic() - self.t0

    def escena(self, pasos: list[dict], duracion: float) -> tuple[float, float]:
        """Ejecuta los pasos repartidos en `duracion`; devuelve (inicio, fin) en el video."""
        inicio = self.ahora()
        if not any("buscar" in p for p in pasos):
            # la busqueda de una escena anterior no se queda tapando el arbol
            self.pg.keyboard.press("Control+Shift+E")
        hueco = duracion / max(1, len(pasos))
        for i, paso in enumerate(pasos):
            objetivo = inicio + hueco * i
            self._esperar_hasta(objetivo)
            self._paso(paso)
        self._esperar_hasta(inicio + duracion)
        return inicio, self.ahora()

    def cerrar(self) -> Path:
        ruta = Path(self.pg.video.path())
        self.ctx.close()
        return ruta

    def _esperar_hasta(self, t: float):
        falta = t - self.ahora()
        if falta > 0:
            time.sleep(falta)

    def _paso(self, paso: dict):
        pg = self.pg
        if "abrir" in paso:
            ruta = str(paso["abrir"]).replace("\\", "/")
            pg.keyboard.press("Control+P")
            time.sleep(0.4)
            pg.keyboard.type(ruta + (":%d" % paso["linea"] if paso.get("linea") else ""), delay=14)
            time.sleep(0.9)
            pg.keyboard.press("Enter")
            time.sleep(0.6)
        elif "resaltar" in paso:
            desde, hasta = paso["resaltar"]
            pg.keyboard.press("Control+G")
            time.sleep(0.3)
            pg.keyboard.type(str(desde), delay=30)
            pg.keyboard.press("Enter")
            time.sleep(0.3)
            pg.keyboard.press("Home")
            for _ in range(max(0, int(hasta) - int(desde) + 1)):
                pg.keyboard.press("Shift+ArrowDown")
                time.sleep(0.025)
        elif "buscar" in paso:
            pg.keyboard.press("Control+Shift+F")
            time.sleep(0.5)
            pg.keyboard.press("Control+A")
            pg.keyboard.type(str(paso["buscar"]), delay=35)
            time.sleep(0.4)
            pg.keyboard.press("Enter")
            time.sleep(0.8)
        elif paso.get("explorador"):
            pg.keyboard.press("Control+Shift+E")
            time.sleep(0.4)
        elif "bajar" in paso:
            for _ in range(int(paso["bajar"])):
                pg.keyboard.press("Control+ArrowDown")
                time.sleep(0.06)
