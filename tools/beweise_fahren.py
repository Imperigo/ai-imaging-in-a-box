#!/usr/bin/env python3
"""Fährt die Beweisskripte unter ``tools/beweis/`` — **eines nach dem anderen**.

Warum seriell, und es ist keine Vorsicht
-----------------------------------------
Am 26.08.2026 sind an einem Tag **drei** Läufe rot geworden — zweimal
``test_bauwerksbox``, einmal ``test_kette`` —, und alle drei hatten dieselbe Ursache:
Es lief nebenher ein zweiter Blender. Nachgemessen (Sitzung 13, Abschnitt «Eine Messung
über diese Umgebung, nicht über den Code»): Allein läuft dieselbe Sammlung **fünf von
fünf** grün; der Herzschlagfaden verhungert unter Last länger als seine Frist, und die
Wache tötet einen gesunden Lauf.

Daraus wurde eine Arbeitsregel, und dieses Werkzeug ist sie in ausführbarer Form:
**Nie zwei Blender-Läufe gleichzeitig.** Die Beweisskripte entstehen parallel, sie laufen
seriell.

Was es tut
----------
Es sucht ``tools/beweis/*.py``, führt sie in der Reihenfolge ihrer Nummer aus, und sagt
je Skript, was dabei herauskam: welche Bilder entstanden sind, wie lange es dauerte, und
ob es gescheitert ist. **Ein gescheitertes Skript hält die Reihe nicht an** — sonst
entschiede das erste kaputte, wie viele Beweise es gibt.

Was es NICHT tut
----------------
Es beurteilt kein Bild. Ob ein Beweis trägt, entscheidet, wer ihn ansieht — dieses
Werkzeug stellt nur sicher, dass er unter fairen Bedingungen entstanden ist.

    python tools/beweise_fahren.py
    python tools/beweise_fahren.py --nur 02 09 14
    python tools/beweise_fahren.py --liste
    python tools/beweise_fahren.py --json
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
BEWEISE = WURZEL / "tools" / "beweis"
AUSGABE = WURZEL / "build" / "beweis"

#: Wieviel Zeit ein einzelner Beweis bekommt. Grosszügig: Ein Multipass kostet auf der
#: CPU dieser Umgebung rund 97 s je Kamera, und ein Beweis darf mehrere fahren.
FRIST_S = 1800


def skripte(nur: list[str] | None = None) -> list[Path]:
    """Die Beweisskripte, nach Nummer geordnet.

    Die Nummer steht im Dateinamen (``02_knoten_multipass.py``) und ist die
    Reihenfolge — nicht das Änderungsdatum. *Eine Reihenfolge, die von der Platte
    abhängt, ist beim nächsten Klon eine andere.*
    """
    if not BEWEISE.is_dir():
        return []
    gefunden = sorted(p for p in BEWEISE.glob("*.py") if not p.name.startswith("_"))
    if nur:
        gefunden = [p for p in gefunden if p.name.split("_")[0] in nur]
    return gefunden


def _bilder(ordner: Path) -> list[str]:
    if not ordner.is_dir():
        return []
    return sorted(p.name for p in ordner.rglob("*.png"))


def _raeume_ab(ordner: Path) -> list[str]:
    """Den Ausgabeordner leeren, **bevor** das Skript läuft — und sagen, was weg war.

    Ohne das ist die dritte Fehlerart dieses Projekts offen: Ein Skript wird geändert,
    schreibt nur noch vier statt sechs Bilder, und die zwei alten liegen weiter da. Der
    Fahrer zählt sechs, der Bericht meldet sechs, und **zwei davon beweisen eine Fassung,
    die es nicht mehr gibt.** Genau so sah der liegengebliebene Blender-Report aus.

    Gelöscht wird ausschliesslich der Ordner **dieses** Beweises, nie ``AUSGABE`` selbst.
    """
    if not ordner.is_dir():
        return []
    weg = sorted(p.name for p in ordner.rglob("*") if p.is_file())
    shutil.rmtree(ordner)
    return weg


def fahre(pfad: Path, *, frist_s: int = FRIST_S) -> dict:
    """Ein Skript ausführen und berichten, was dabei herauskam.

    Gemessen wird, **was auf der Platte liegt** — nicht, was das Skript behauptet. Ein
    Skript, das «geschrieben» meldet und nichts schreibt, ist in diesem Projekt schon
    zweimal vorgekommen (der liegengebliebene Report, die Dateigrösse als Beleg).

    Und der Ordner wird **vorher geleert**: Was danach darin liegt, ist ohne Ausnahme aus
    diesem Lauf. Ein Beweisbild aus einer früheren Fassung des Skripts ist keine
    Kleinigkeit — es ist ein Beleg für etwas, das so nicht mehr gebaut wird.
    """
    kennung = pfad.stem
    ziel = AUSGABE / kennung
    geraeumt = _raeume_ab(ziel)
    beginn = time.monotonic()
    try:
        lauf = subprocess.run(
            [sys.executable, str(pfad)],
            cwd=WURZEL, capture_output=True, text=True, timeout=frist_s,
            env={**_umgebung()},
        )
        code, ausgabe, fehler = lauf.returncode, lauf.stdout, lauf.stderr
    except subprocess.TimeoutExpired:
        code, ausgabe, fehler = -1, "", f"Frist von {frist_s} s überschritten"
    dauer = time.monotonic() - beginn

    nachher = _bilder(ziel)
    return {
        "beweis": kennung,
        "code": code,
        "dauer_s": round(dauer, 1),
        "bilder": nachher,
        # `geraeumt` sagt, was aus einem frueheren Lauf weggeraeumt wurde. Die Zeile ist
        # kein Buchhaltungsschmuck: Schreibt ein Skript nach einer Aenderung eine Datei
        # NICHT mehr, taucht sie hier auf und in `bilder` nicht — und genau dieser
        # Unterschied faellt sonst niemandem auf.
        "geraeumt": geraeumt,
        "verschwunden": sorted(set(geraeumt) - set(nachher)),
        "ordner": str(ziel.relative_to(WURZEL)),
        # Die letzten Zeilen genügen: Wer die ganze Ausgabe braucht, fährt das Skript
        # selbst. Was hier steht, soll auf einen Blick sagen, woran es lag.
        "ausgabe": "\n".join(ausgabe.strip().splitlines()[-8:]),
        "fehler": "\n".join(fehler.strip().splitlines()[-12:]),
    }


def _umgebung() -> dict:
    import os
    umg = dict(os.environ)
    # Die Beweise liegen unter tools/ und importieren `aiimaging` aus src/. Den Pfad
    # setzt sonst jedes Skript selbst — hier steht er einmal, damit ein vergessener
    # `sys.path`-Eintrag nicht wie ein fehlendes Modul aussieht.
    pfade = [str(WURZEL / "src")]
    if umg.get("PYTHONPATH"):
        pfade.append(umg["PYTHONPATH"])
    umg["PYTHONPATH"] = ":".join(pfade)
    return umg


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--nur", nargs="*", metavar="NR",
                   help="nur diese Beweisnummern, z. B. --nur 02 09")
    p.add_argument("--liste", action="store_true", help="nur zeigen, was gefahren würde")
    p.add_argument("--frist-s", type=int, default=FRIST_S)
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)

    liste = skripte(a.nur)
    if not liste:
        print("Keine Beweisskripte unter tools/beweis/.")
        return 1

    if a.liste:
        for pfad in liste:
            print(f"  {pfad.relative_to(WURZEL)}")
        print(f"\n{len(liste)} Beweise, seriell zu fahren.")
        return 0

    AUSGABE.mkdir(parents=True, exist_ok=True)
    print(f"{len(liste)} Beweise, SERIELL — nie zwei Blender-Laeufe gleichzeitig.\n")

    berichte = []
    for i, pfad in enumerate(liste, 1):
        print(f"[{i}/{len(liste)}] {pfad.name} ...", flush=True)
        bericht = fahre(pfad, frist_s=a.frist_s)
        berichte.append(bericht)
        marke = "ok " if bericht["code"] == 0 else "FEHL"
        print(f"        {marke} {bericht['dauer_s']:>7.1f}s  "
              f"{len(bericht['bilder'])} Bilder in {bericht['ordner']}")
        if bericht["verschwunden"]:
            # Eine Datei, die es im vorigen Lauf gab und jetzt nicht mehr: entweder hat
            # das Skript sie abgeschafft (dann ist es richtig) oder es kommt nicht mehr
            # bis dorthin (dann ist es ein Fehlschlag, der wie ein Erfolg aussieht).
            print(f"        NICHT MEHR GESCHRIEBEN: "
                  f"{', '.join(bericht['verschwunden'])}")
        if bericht["code"] != 0 and bericht["fehler"]:
            for zeile in bericht["fehler"].splitlines()[-4:]:
                print(f"          | {zeile}")

    if a.json:
        print(json.dumps(berichte, ensure_ascii=False, indent=1))
        return 0

    gelungen = [b for b in berichte if b["code"] == 0]
    mit_bild = [b for b in berichte if b["bilder"]]
    leer = [b for b in berichte if b["code"] == 0 and not b["bilder"]]
    bilder = sum(len(b["bilder"]) for b in berichte)

    print(f"\nGELAUFEN: {len(gelungen)} von {len(berichte)}")
    print(f"BILDER:   {bilder} in {len(mit_bild)} Ordnern")
    if leer:
        # Der gefaehrlichere der beiden Fehlschlaege: Rueckgabe 0 und nichts auf der
        # Platte sieht in jeder Zusammenfassung wie ein Erfolg aus.
        print(f"OHNE BILD, aber Rueckgabe 0: {', '.join(b['beweis'] for b in leer)}")
        print("   Ein Skript, das gelingt und nichts schreibt, ist kein Beweis.")
    for b in berichte:
        if b["code"] != 0:
            print(f"GESCHEITERT: {b['beweis']} (Code {b['code']})")
    return 0 if len(gelungen) == len(berichte) and not leer else 1


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
