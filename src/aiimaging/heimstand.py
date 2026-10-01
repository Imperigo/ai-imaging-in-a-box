"""Der **Stand des Heim-PC** für die Startzeilen der Mac-App (Plan v0.1.7, Blatt 13).

Drei Fragen, je mit einem Satz: Ist Blender da? Wie viel Grafikspeicher ist frei? Steht
der Assistent? Der Server reicht das Ergebnis unter ``GET /api/heim`` durch; die Form ist
ein **fester Vertrag** mit der Mac-App::

    {"blender":     {"da": bool, "satz": str},
     "grafikkarte": {"frei_gb": number | null, "satz": str},
     "assistent":   {"stand": "bereit"|"laedt"|"fehlt"|"aus", "modell": str | null,
                     "satz": str},
     "satz": str}

**Ohne Pfade, ohne Rechner- und Gerätenamen** (Regel 3): Die Antwort geht über das Netz
bis auf einen Mac; wo Blender liegt und wie die Grafikkarte heisst, braucht dort niemand.

**Blender wird nur nachgesehen, nie geladen** (Regel 2): ob das Programm, das die Kette
aufrufen würde (``seams.finde_blender``), als ausführbare Datei daliegt. Kein ``import
bpy``, kein Start von Blender — der kostete Sekunden, und die Startzeile soll sofort
antworten.

Ohne Oberfläche aufrufbar (Regel 4): ``from aiimaging import heimstand;
heimstand.heimstand()``.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from aiimaging import assistent, seams

__all__ = ["blender", "grafikkarte", "heimstand", "FRIST_NVIDIA_SMI_S"]

#: Wie lange ``nvidia-smi`` antworten darf — **gesetzt**: Es antwortet gewöhnlich in
#: Bruchteilen einer Sekunde; hängt der Treiber, soll die Startzeile nicht mithängen.
FRIST_NVIDIA_SMI_S = 5.0


def blender() -> dict:
    """``{"da", "satz"}`` — liegt das Blender-Programm da, das die Kette aufriefe?"""
    try:
        pfad = Path(seams.finde_blender())
    except seams.SeamError:
        return {"da": False,
                "satz": "Blender nicht gefunden — am Heim-PC AIIMAGING_BLENDER setzen oder "
                        "blender in den Suchpfad legen."}
    if pfad.is_file() and os.access(pfad, os.X_OK):
        return {"da": True, "satz": "Blender ist da."}
    # DER PFAD BLEIBT DRAUSSEN, auch hier: Er nennt den Benutzer des Heim-PC.
    return {"da": False,
            "satz": "Blender ist eingestellt, aber die Datei fehlt oder ist nicht "
                    "ausführbar."}


def grafikkarte() -> dict:
    """``{"frei_gb", "satz"}`` — freier Grafikspeicher laut ``nvidia-smi``, oder ``None``.

    ``None`` heisst **nicht gemessen**, nicht null. Gerechnet in GB zu 1024 MiB, auf eine
    Stelle — so, wie die Messungen am Heim-PC ihn nennen. Bei mehreren Karten zählt die
    erste (die, auf der gerechnet wird), und der Satz sagt es.
    """
    programm = shutil.which("nvidia-smi")
    if programm is None:
        return {"frei_gb": None,
                "satz": "nvidia-smi nicht gefunden — freier Grafikspeicher nicht gemessen."}
    try:
        lauf = subprocess.run(
            [programm, "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=FRIST_NVIDIA_SMI_S, check=False)
    except (OSError, subprocess.SubprocessError):
        return {"frei_gb": None,
                "satz": "nvidia-smi antwortete nicht — freier Grafikspeicher nicht gemessen."}
    zeilen = [z.strip() for z in (lauf.stdout or "").splitlines() if z.strip()]
    try:
        mib = float(zeilen[0])
    except (IndexError, ValueError):
        return {"frei_gb": None,
                "satz": "nvidia-smi gab keine lesbare Zahl — freier Grafikspeicher nicht "
                        "gemessen."}
    if lauf.returncode != 0 or mib < 0:
        return {"frei_gb": None,
                "satz": "nvidia-smi meldete einen Fehler — freier Grafikspeicher nicht "
                        "gemessen."}
    frei = round(mib / 1024, 1)
    zusatz = f" (erste von {len(zeilen)} Karten)" if len(zeilen) > 1 else ""
    return {"frei_gb": frei, "satz": f"{frei:.1f} GB Grafikspeicher frei{zusatz}."}


_ASSISTENT_WORT = {
    assistent.STAND_BEREIT: "Assistent bereit",
    assistent.STAND_LAEDT: "Assistent wartet auf das Bild",
    assistent.STAND_FEHLT: "Assistent fehlt",
    assistent.STAND_AUS: "Assistent aus",
}


def heimstand(*, sprachmodell=None, bild_rechnet: bool = False) -> dict:
    """Die Antwort von ``GET /api/heim`` — siehe Modulkopf für die Form.

    Args:
        sprachmodell: wie bei :func:`aiimaging.assistent.stand` (Vorgabe: Ollama aus der
            Umgebung).
        bild_rechnet: Rechnet gerade ein Bild? Dann steht der Assistent auf ``laedt``.
    """
    b = blender()
    g = grafikkarte()
    a = assistent.stand(sprachmodell=sprachmodell, bild_rechnet=bild_rechnet)
    teile = ["Blender da" if b["da"] else "Blender fehlt",
             f"{g['frei_gb']:.1f} GB Grafikspeicher frei" if g["frei_gb"] is not None
             else "Grafikspeicher nicht gemessen",
             _ASSISTENT_WORT[a["stand"]]]
    return {"blender": b, "grafikkarte": g, "assistent": a,
            "satz": "Heim-PC antwortet: " + ", ".join(teile) + "."}
