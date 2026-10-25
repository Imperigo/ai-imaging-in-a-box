#!/usr/bin/env python3
"""Eine IFC neutralisieren — als Kopie, die Eingabe bleibt unberührt (Auftrag 354).

Die dünne Schicht über :func:`aiimaging.seams.ifc_neutralisieren`; die Arbeit macht der
Runner im `.venv-ifc` (``src/aiimaging/runners/ifc_neutral_runner.py``). Getilgt werden
Namen, Texte, Adressen, Klassifikationen, Beschriftungen und die Georeferenz; die Geometrie
bleibt, wo sie ist.

    python tools/ifc_neutralisieren.py <ein.ifc> <aus.ifc> [--bericht b.json] [--ueberschreiben]
                                       [--ursprung | --ohne-ursprung]
                                       [--versatz-schreiben V.json | --versatz-lesen V.json]

``--ursprung`` ist **Vorgabe**: Liegt das Modell in Landeskoordinaten, wird es als Ganzes an
einen lokalen Ursprung geschoben (Versatz auf 100 m gerundet, nie im Bericht). Ohne das
verriete die Geometrie den Ort, und glb, Blender und die Auto-Kameras rechneten weit
draussen. ``--ohne-ursprung`` lässt die Lage, wie sie ist, und warnt nur.

**Zwei Dateien desselben Orts** (Situationsmodell und Umgebungsbauten, 25.10.2026): die erste mit
``--versatz-schreiben V.json``, die zweite mit ``--versatz-lesen V.json`` — dann liegen beide um denselben
Versatz verschoben und passen aufeinander. ``V.json`` liegt **ausserhalb des Repos** (das Werkzeug weist einen
Pfad im Repo ab) und geht nie weiter: ihr Wert ist die Lage.

Ausgabe: der Bericht als JSON — **nur Zahlen und Klassen**, nie ein Text aus der Datei
und nie ein Pfad. Rückgabewert:

* 0 — geschrieben, 0 Resttexte
* 3 — geschrieben, aber Resttexte gefunden: **die Kopie nicht weitergeben**
* 2 — Aufruf falsch (Ziel = Eingabe, Ziel vorhanden, Endung)
* 1 — Lauf gescheitert (venv fehlt, Datei nicht lesbar)
* 4 — Lage passt nicht zur Versatzdatei (eine Datei lokal, die andere in Landeskoordinaten): nichts
  geschrieben — die Lage beider prüfen

Die schlechte Nachricht steht auch hier: Neutralisieren tilgt Texte, nicht die Form. Ein
echtes Grundstück bleibt an seiner Gestalt erkennbar.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import seams  # noqa: E402

#: Rückgabewerte — einmal benannt, damit Auftrag und Tests dieselben Zahlen lesen.
OK, GESCHEITERT, AUFRUF_FALSCH, RESTTEXTE, LAGE_WIDERSPRUCH = 0, 1, 2, 3, 4


def urteil(bericht: dict) -> tuple[int, str]:
    """Rückgabewert und ein Satz zum Bericht — ohne ifcopenshell, ohne Werte aus der Datei."""
    rest = (bericht.get("resttexte") or {})
    anzahl = rest.get("anzahl")
    if not isinstance(anzahl, int):
        return GESCHEITERT, "Der Bericht nennt keine Restprüfung — die Kopie gilt als ungeprüft."
    bauteile = bericht.get("n_bauteile") or {}
    satz = (f"{bericht.get('n_entfernt_summe', 0)} Einträge entfernt, "
            f"{bericht.get('n_umbenannt', 0)} umbenannt, Bauteile "
            f"{bauteile.get('vorher')} → {bauteile.get('nachher')}, "
            f"Georeferenz {'entfernt' if bericht.get('georeferenz_entfernt') else 'keine'}, "
            f"Ursprung {'verschoben' if (bericht.get('ursprung') or {}).get('verschoben') else 'nicht verschoben'}.")
    if anzahl:
        stellen = ", ".join(f"{s['klasse']}.{s['attribut']} ×{s['anzahl']}"
                            for s in rest.get("stellen", []))
        return RESTTEXTE, (f"{anzahl} Resttexte ({stellen}) — die Kopie NICHT weitergeben. "
                           + satz)
    return OK, "0 Resttexte. " + satz


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("ein", help="die IFC mit Namen (wird nur gelesen)")
    ap.add_argument("aus", help="die neutrale Kopie (.ifc)")
    ap.add_argument("--bericht", default=None, help="Bericht zusätzlich als JSON-Datei")
    ap.add_argument("--ueberschreiben", action="store_true",
                    help="ein vorhandenes Ziel ersetzen")
    ap.add_argument("--ursprung", dest="ursprung", action="store_true", default=True,
                    help="aus Landeskoordinaten an einen lokalen Ursprung schieben (Vorgabe)")
    ap.add_argument("--ohne-ursprung", dest="ursprung", action="store_false",
                    help="die Lage nicht verschieben, nur warnen")
    versatz = ap.add_mutually_exclusive_group()
    versatz.add_argument("--versatz-schreiben", default=None,
                         help="den benutzten Versatz in diese LOKALE Datei schreiben (ausserhalb des Repos)")
    versatz.add_argument("--versatz-lesen", default=None,
                         help="um denselben Versatz wie die erste Datei verschieben (ihre Versatzdatei)")
    a = ap.parse_args(argv)
    ein, aus = Path(a.ein), Path(a.aus)
    if ein.suffix.lower() != ".ifc" or aus.suffix.lower() != ".ifc":
        print("Eingabe und Ziel müssen auf .ifc enden.", file=sys.stderr)
        return AUFRUF_FALSCH
    if ein.exists() and ein.resolve() == aus.resolve():
        print("Ziel und Eingabe sind dieselbe Datei — die Eingabe bleibt unberührt.",
              file=sys.stderr)
        return AUFRUF_FALSCH
    if aus.exists() and not a.ueberschreiben:
        print("Das Ziel gibt es schon; ersetzen nur mit --ueberschreiben.", file=sys.stderr)
        return AUFRUF_FALSCH
    try:
        extra = {k: v for k, v in (("versatz_lesen", a.versatz_lesen),
                                    ("versatz_schreiben", a.versatz_schreiben)) if v}
        bericht = seams.ifc_neutralisieren(ein, aus, ueberschreiben=a.ueberschreiben,
                                           ursprung=a.ursprung, **extra)
    except seams.LageWiderspruch as e:
        print(str(e), file=sys.stderr)
        return LAGE_WIDERSPRUCH
    except seams.SeamError as e:
        print(str(e), file=sys.stderr)
        return GESCHEITERT
    text = json.dumps(bericht, indent=2, ensure_ascii=False)
    if a.bericht:
        Path(a.bericht).write_text(text + "\n", encoding="utf-8")
    print(text)
    code, satz = urteil(bericht)
    print(satz, file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
