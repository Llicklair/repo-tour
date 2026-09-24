"""La voz: la sintesis del sistema (Windows SAPI), local, sin nube ni claves."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

VOZ = "Microsoft Helena Desktop"


def duracion(ruta: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(ruta)],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def sintetizar(textos: list[str], carpeta: Path, voz: str = VOZ, velocidad: int = 0) -> list[Path]:
    carpeta.mkdir(parents=True, exist_ok=True)
    wavs = [carpeta / f"voz{i:02d}.wav" for i in range(len(textos))]
    manifiesto = carpeta / "voz.json"
    manifiesto.write_text(json.dumps([{"wav": str(w), "texto": t} for w, t in zip(wavs, textos)],
                                     ensure_ascii=False), encoding="utf-8")
    ps = f"""$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$items = Get-Content -Raw -Encoding UTF8 '{manifiesto}' | ConvertFrom-Json
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {{ $s.SelectVoice('{voz}') }} catch {{
  $es = $s.GetInstalledVoices() | Where-Object {{ $_.VoiceInfo.Culture.Name -like 'es-*' }} | Select-Object -First 1
  if ($es) {{ $s.SelectVoice($es.VoiceInfo.Name) }} }}
$s.Rate = {int(velocidad)}
foreach ($it in $items) {{ $s.SetOutputToWaveFile($it.wav); $s.Speak($it.texto); $s.SetOutputToDefaultAudioDevice() }}
$s.Dispose()
"""
    script = carpeta / "voz.ps1"
    script.write_text("﻿" + ps, encoding="utf-8")
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)], check=True)
    return wavs
