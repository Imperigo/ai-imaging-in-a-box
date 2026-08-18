#!/usr/bin/env python3
"""RUNNER — EXR → rohe float32-Tiefen. Läuft INNERHALB von Blender, nie im Produkt.

Wozu dieses Skript da ist
-------------------------
``aiimaging.bildlesen`` liest EXR-Dateien im Normalfall **ohne jede Abhängigkeit**: Die
Dateien, die dieses Projekt selbst schreibt, sind scanline-organisiert, 32-Bit-FLOAT und
ZIP-komprimiert — und ZIP ist in OpenEXR nichts als ``zlib`` mit zwei Nachbearbeitungen.
Der stdlib-Weg ist damit der Hauptweg, und er ist es aus einem Grund: Die Geometrie-QA
soll überall laufen, auch ohne Blender (Regel 4).

Dieses Skript ist der **Rückfall** für alles, was der stdlib-Leser ehrlich abweist statt
zu raten: PIZ, DWAA/DWAB, B44, PXR24, gekachelte und mehrteilige Dateien. Der Grund, es
über Blender statt über eine Bibliothek zu lösen, ist eine Lizenzentscheidung:

* ``imageio`` erreicht EXR klassisch über **FreeImage** — FIPL **oder GPL**. Ein
  GPL-Fund, und damit unter Regel 1 ausgeschlossen.
* ``OpenImageIO`` ist selbst Apache-2.0, seine Wheels bündeln aber ungeprüfte
  Fremdbibliotheken (dieselbe Falle wie das ifcopenshell-Wheel mit GPL-CGAL).
* **Blender** steht bereits als GPL-Komponente im ``NOTICE``, wird bereits als
  Subprozess aufgerufen und hat diese Dateien ohnehin geschrieben. Der Rückfall kostet
  damit keine *neue* Lizenzentscheidung — nur Zeit.

Warum das ein eigener Prozess ist
---------------------------------
Blender steht unter GPL-2.0-or-later. Ein ``import bpy`` im Produkt-Environment machte
das Produkt GPL. Regel 2 zieht die Grenze am **Prozessaufruf**:

    blender --background --factory-startup --python blender_exr_lesen.py -- <argumente>

Das ist GPL-rechtlich eine Aggregation. **Dieses Modul darf aus ``aiimaging`` heraus
niemals importiert werden**; ``tests/test_prozessgrenze.py`` bewacht das.

Warum die Werte roh und nicht als JSON zurückkommen
---------------------------------------------------
Ein 512er-Bild sind 262 144 Zahlen. Als JSON-Text wären das mehrere Megabyte, die beide
Seiten schreiben und parsen müssten — plus die Frage, mit wie vielen Nachkommastellen.
Eine rohe ``float32``-Datei (little-endian) ist exakt, klein und mit drei Zeilen
``array`` wieder einzulesen. Der JSON-Report daneben trägt nur die Kopfdaten.

Reihenfolge der Werte
---------------------
Zeilenweise **von oben nach unten** — dieselbe Ordnung wie in der EXR-Datei selbst und
wie in ``lies_png_graustufen``. Blenders ``image.pixels`` läuft dagegen von **unten**
nach oben; dieses Skript spiegelt darum ausdrücklich. Ohne diese Spiegelung wären
stdlib-Weg und Blender-Weg nicht indexgleich, und ``geometrie_qa`` setzt Indexgleichheit
voraus: Ein Versatz wird dort nicht erkannt, sondern nur als schlechterer Score bestraft
— der teuerste denkbare Fehler, weil niemand nach ihm sucht.

Aufruf (immer über ``aiimaging.bildlesen``, nicht von Hand):
    blender --background --factory-startup --python blender_exr_lesen.py -- \
        --exr <in.exr> --out <verzeichnis>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy  # noqa: E402  — nur innerhalb von Blender vorhanden; siehe Modul-Docstring

#: Ab diesem Wert gilt ein Tiefenpixel als Hintergrund — dieselbe Schranke wie im
#: Multipass-Runner. Sie geht **nicht** in die zurückgegebenen Werte ein; sie dient nur
#: der Statistik im Report. Was Hintergrund ist, entscheidet ``geometrie_qa``, nicht ein
#: Dateileser.
HINTERGRUND_AB_M = 1.0e7

#: Kanalreihenfolge in Blenders Pixelpuffer. Blender liefert immer vier Kanäle, auch für
#: eine einkanalige EXR — der Tiefenwert steht dann in allen vieren, gelesen wird der erste.
KANAELE = 4


def _argumente():
    """Argumente hinter dem ``--``-Trenner lesen (davor gehört alles Blender)."""
    import argparse

    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--exr", required=True)
    ap.add_argument("--out", required=True)
    return ap.parse_args(argv)


def main() -> int:
    a = _argumente()
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    roh_datei = out_dir / "tiefe.f32"
    bericht = out_dir / "exr-report.json"

    # Reste eines früheren Laufs vor dem Start entfernen. Dieselbe Lehre wie im
    # Multipass-Runner: Die Existenz einer Datei ist kein Beleg für ihren Inhalt — ein
    # gescheiterter Lauf darf sich nicht an den Bytes von gestern gesundmelden.
    roh_datei.unlink(missing_ok=True)
    bericht.unlink(missing_ok=True)

    report = {"status": "error", "error": None, "roh_datei": None,
              "breite": None, "hoehe": None, "blender": bpy.app.version_string}
    try:
        import numpy as np

        quelle = bpy.data.images.load(str(a.exr))
        # Non-Color: Die Zahlen im EXR sind Meter, keine Farben. Ohne diesen Schalter
        # dürfte die Farbverwaltung sie unterwegs umrechnen — aus 27.3 m würde dann
        # eine andere, gleich plausible Zahl.
        quelle.colorspace_settings.name = "Non-Color"
        breite, hoehe = quelle.size
        if breite <= 0 or hoehe <= 0:
            raise RuntimeError(f"Blender liest die EXR als {breite}x{hoehe}")

        puffer = np.empty(breite * hoehe * KANAELE, dtype=np.float32)
        quelle.pixels.foreach_get(puffer)
        tiefe = puffer[0::KANAELE]

        # Blenders Pixelpuffer beginnt in der UNTEREN Bildzeile. Die EXR-Datei und jedes
        # PNG beginnen oben. Ohne diese Spiegelung wäre die Tiefenkarte gegenüber allen
        # anderen Ausgaben senkrecht gekippt — und zwar unauffällig, weil das Ergebnis
        # weiterhin wie eine Tiefenkarte aussähe.
        tiefe = tiefe.reshape(hoehe, breite)[::-1].reshape(-1)

        # Ausdrücklich little-endian: Der Leser auf der anderen Seite dreht nur dann, wenn
        # seine Maschine anders herum rechnet. Ohne festgelegte Bytefolge hinge das
        # Ergebnis an der Architektur beider Seiten.
        tiefe.astype("<f4").tofile(str(roh_datei))

        gueltig = np.isfinite(tiefe) & (tiefe > 0.0) & (tiefe < HINTERGRUND_AB_M)
        report.update({
            "status": "ok",
            "roh_datei": str(roh_datei),
            "breite": int(breite),
            "hoehe": int(hoehe),
            "n_werte": int(tiefe.size),
            "dtype": "<f4",
            "reihenfolge": "zeilenweise von oben (wie in der EXR-Datei und im PNG)",
            "quelle_exr": str(a.exr),
            "n_geometriepixel": int(gueltig.sum()),
            "min_m": float(tiefe[gueltig].min()) if gueltig.any() else None,
            "max_m": float(tiefe[gueltig].max()) if gueltig.any() else None,
        })
    except Exception as fehler:                          # Fehler als Report, nicht als Traceback
        # Der Aufrufer liest JSON, keinen stderr-Text. Ein Traceback wäre für ihn ein
        # leerer Report plus Rauschen; so bekommt er einen Satz, der die Ursache nennt.
        report["error"] = f"{type(fehler).__name__}: {fehler}"

    bericht.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("EXR_REPORT " + json.dumps(report, ensure_ascii=False))
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
