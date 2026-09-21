#!/usr/bin/env python3
"""BEWEIS 31 — Der Weg des PRODUKTS, nicht der Kette darunter.

Was diesen Beweis von Beweis 20 unterscheidet
---------------------------------------------
Beweis 20 fährt ``kette.baue_kette`` und ``kette.fuehre_aus`` mit den echten Ausführern.
Das ist die **Kette**. Seit dem 21.09.2026 geht das Produkt aber einen anderen Weg
darüber:

    Modelldatei  →  einlass.pruefe        (kommt das überhaupt herein?)
                 →  importeur.importiere  (umwandeln, Treue prüfen)
                 →  projekt.neu           (die Mappe anlegen)
                 →  arbeitsgang.rechne    (Kette fahren UND jedes Urteil eintragen)
                 →  projekt.speichere     (morgen dort weitermachen)

Diese fünf Stufen hat **noch nie ein echter Lauf gesehen**. Sie sind mit Attrappen
geprüft, und Attrappen beantworten die eine Frage nicht, um die es hier geht:

    *Hält der Weg, den ein Mensch wirklich geht — und nicht der, den die Tests gehen?*

Genau dieser Unterschied hat in diesem Projekt schon zweimal einen Fehler versteckt: am
07.09.2026 zwischen Auftragsattrappe und echter Auftragsdatei, und am 21.09.2026 noch
einmal an derselben Stelle.

Was hier bewiesen wird
----------------------
1. **Eine Modelldatei geht durch die Tür und wird zur Mappe.** Mit Bericht: über welchen
   Weg sie hereinkam, und was dabei NICHT geprüft wurde.
2. **Die Mappe übersteht das Schliessen.** Geschrieben, neu geöffnet, und der Modellstand
   wird gegen den Fingerabdruck geprüft — nicht gegen den Dateinamen.
3. **Der Lauf trägt jedes Bild samt Urteil ein**, und ein nicht gemessenes Urteil steht
   als ``None`` da und nicht als «in Ordnung».
4. **Der Fortschritt kommt an.** Jeder Knoten meldet Beginn und Ende; die Bildstufe zählt
   ihre Schritte. Das ist der einzige belegte Fortschritt dieses Projekts.
5. **Ein verändertes Modell hält den Lauf an** — ohne ``trotz_aenderung`` gibt es kein
   Urteil gegen ein anderes Gebäude unter dem alten Namen.

Was dieser Beweis NICHT leistet
-------------------------------
**Ohne Blender, Gewichte und GPU fährt er mit Attrappen** — und sagt das in jeder Zeile
seiner Ausgabe. Dann belegt er die fünf Stufen des Produkts und **nicht** das Bild.

Auf der HomeStation (``--echt``) fährt dieselbe Datei mit den echten Ausführern. Erst
dort ist der Weg wirklich belegt.

    *Ein Beweis, der auf der Maschine ohne Gerät dasselbe meldet wie auf der mit, belegt
    das Gerät nicht.*
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))

from aiimaging import arbeitsgang, einlass, kette, projekt   # noqa: E402

#: Was eine Attrappenstufe schreibt, damit die nächste etwas vorfindet. Echte Dateien,
#: keine behaupteten Pfade — ein Pfad ohne Datei ergäbe beim nächsten Lauf einen
#: Fehltreffer im Zwischenspeicher, und der Beweis bewiese das Gegenteil.
MINI_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d49444154789c636060600000000400012734270a0000000049454e44ae426082")


def _attrappen():
    """Ausführer ohne Gerät — **und sie sagen es.**

    Jede Stufe schreibt echte Dateien und meldet ``attrappe: True``. Das Feld wandert bis
    in die Mappe: *Ein Lauf ohne Gerät, dem man das nicht ansieht, ist schlimmer als
    keiner.*
    """
    def stufe(felder):
        def f(*, knoten, eingaben, out_dir):
            ziel = Path(out_dir)
            ziel.mkdir(parents=True, exist_ok=True)
            antwort = {"status": "ok", "attrappe": True}
            for name, datei in felder.items():
                (ziel / datei).write_bytes(MINI_PNG)
                antwort[name] = str(ziel / datei)
            return antwort
        return f

    def geometrie(*, knoten, eingaben, out_dir):
        ziel = Path(out_dir)
        ziel.mkdir(parents=True, exist_ok=True)
        glb = ziel / "modell.glb"
        glb.write_bytes(b"glTF\x02\x00\x00\x00")
        return {"status": "ok", "attrappe": True, "glb_path": str(glb), "up_axis": "Y",
                "bbox": [[0, 0, 0], [8.0, 5.0, 3.25]]}

    def qa(*, knoten, eingaben, out_dir):
        # NICHT GEMESSEN, und das ist hier die Wahrheit: Ohne Tiefenschaetzer gibt es
        # kein Urteil. `None` heisst NICHT GEMESSEN und nie «in Ordnung».
        return {"status": "ok", "attrappe": True, "bestanden": None,
                "grund": "Attrappe: ohne Tiefenschaetzer wurde nichts gemessen."}

    return {
        kette.ART_GEOMETRIE: geometrie,
        kette.ART_MULTIPASS: stufe({"depth_png": "tiefe.png", "beauty_png": "beauty.png"}),
        kette.ART_RENDER: stufe({"bild_png": "bild.png"}),
        kette.ART_QA: qa,
    }


def _synthetische_ifc(ziel: Path) -> Path:
    """Ein Bauwerk, das im Repo erzeugt wird — Regel 3.

    Kein Kundenmodell, kein Büroprojekt, und nichts, was von aussen kommt.
    """
    import subprocess
    pfad = ziel / "bauwerk.ifc"
    lauf = subprocess.run(
        [sys.executable, str(WURZEL / "tools" / "make_test_ifc.py"), str(pfad)],
        capture_output=True, text=True, timeout=120)
    if lauf.returncode != 0 or not pfad.is_file():
        raise SystemExit(f"Die synthetische IFC liess sich nicht erzeugen:\n{lauf.stderr[-800:]}")
    return pfad


def main(ziel_arg: str | None = None, echt: bool = False) -> int:
    ziel = Path(ziel_arg) if ziel_arg else WURZEL / "build" / "beweis" / Path(__file__).stem
    ziel.mkdir(parents=True, exist_ok=True)
    marke = "ECHT (Blender, Gewichte, GPU)" if echt else "ATTRAPPEN — ohne Geraet"
    print(f"BEWEIS 31 — Der Weg des Produkts.   Ausfuehrer: {marke}\n")

    quelle = _synthetische_ifc(ziel)
    print(f"1  Die Tuer          {quelle.name}")
    befund = einlass.sichte(quelle)
    print(f"     brauchbar={befund['brauchbar']}  format={befund.get('format')}  "
          f"hochachse={befund.get('hochachse')} (steht fest: "
          f"{befund.get('hochachse_steht_fest')})")
    if not befund["brauchbar"]:
        print(f"     ABGEWIESEN: {befund['grund']}")
        return 1

    mappe = ziel / "projekt"
    if mappe.exists():
        import shutil
        shutil.rmtree(mappe)
    mappe.mkdir(parents=True)

    print(f"\n2  Die Mappe        {mappe.name}/")
    angelegt = arbeitsgang.lege_an(
        mappe, quelle, name="Beweis 31",
        einstellungen={"prompt": "ein Wohnhaus, Morgenlicht", "seed": 0, "schritte": 8})
    einfuhr = angelegt["projekt"]["import"]
    print(f"     weg={einfuhr['weg']}  status={einfuhr['status']}  treue={einfuhr['treue']}")
    print(f"     hochachse={einfuhr['hochachse']}  steht_fest={einfuhr['hochachse_steht_fest']}")
    if einfuhr["status"] != "ok":
        print(f"     Der Import ist nicht durchgekommen: {einfuhr.get('grund')}")
        print(f"     Naechster Schritt: {einfuhr.get('naechster_schritt')}")
        return 1

    print(f"\n3  Wieder geoeffnet")
    auf = projekt.oeffne(mappe)
    print(f"     modell_stand={auf['modell_stand']}   {auf['modell_grund'][:64]}")
    if auf["modell_stand"] != projekt.MODELL_UNVERAENDERT:
        print("     Das Modell gilt als veraendert, obwohl niemand es angefasst hat.")
        return 1

    print(f"\n4  Der Lauf")
    ereignisse: list[dict] = []
    lauf = arbeitsgang.rechne(
        mappe, melder=ereignisse.append,
        ausfuehrer=None if echt else _attrappen())
    for e in ereignisse:
        if e["art"] == "knoten_fertig":
            speicher = " (aus dem Speicher)" if e.get("aus_cache") else ""
            print(f"     {e['nummer']}/{e['von']}  {e['knotenart']:10s} "
                  f"{e['status']}{speicher}")
    schritte = [e for e in ereignisse if e["art"] == "schritt"]
    print(f"     gezaehlte Diffusionsschritte: {len(schritte)}"
          + ("" if schritte else "   (keine — die Bildstufe hat keine gemeldet)"))

    print(f"\n5  Was in der Mappe steht")
    p = projekt.oeffne(mappe)["projekt"]
    for b in p.get("bilder") or []:
        urteil = b["geometrie_bestanden"]
        wort = {True: "bestanden", False: "durchgefallen", None: "NICHT GEMESSEN"}[urteil]
        print(f"     [{wort:14s}] {b['bild']}   schicht={b['schicht']}")
    if not (p.get("bilder") or []):
        print("     KEIN EINZIGES BILD eingetragen — dann hat der Lauf nichts geliefert.")
        return 1

    print(f"\n6  Das veraenderte Modell haelt an")
    quelle.write_bytes(quelle.read_bytes() + b"\n")   # eine Byte-Aenderung genuegt
    try:
        arbeitsgang.rechne(mappe, ausfuehrer=None if echt else _attrappen())
    except arbeitsgang.ArbeitsgangError as fehler:
        erste = str(fehler).splitlines()[0]
        print(f"     ANGEHALTEN: {erste[:96]}")
    else:
        print("     NICHT ANGEHALTEN — das Modell ist ein anderes, und es wurde "
              "trotzdem gerechnet.")
        return 1

    bericht = {
        "beweis": Path(__file__).stem,
        "ausfuehrer": "echt" if echt else "attrappen",
        "import": einfuhr,
        "knoten": [e for e in ereignisse if e["art"] == "knoten_fertig"],
        "schritte_gezaehlt": len(schritte),
        "bilder": [{"bild": b["bild"], "schicht": b["schicht"],
                    "geometrie_bestanden": b["geometrie_bestanden"]}
                   for b in (p.get("bilder") or [])],
        "modell_geaendert_haelt_an": True,
    }
    (ziel / "bericht.json").write_text(
        json.dumps(bericht, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nDER WEG DES PRODUKTS HAELT — fuenf Stufen, {len(bericht['bilder'])} Bild(er), "
          f"{len(schritte)} gezaehlte Schritte.")
    if not echt:
        print("MIT ATTRAPPEN GEFAHREN: Belegt sind die fuenf Stufen, NICHT das Bild.\n"
              "Auf der HomeStation mit --echt fahren.")
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    argumente = [a for a in sys.argv[1:] if a != "--echt"]
    raise SystemExit(main(argumente[0] if argumente else None, echt="--echt" in sys.argv))
