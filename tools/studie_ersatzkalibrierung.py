#!/usr/bin/env python3
"""ERSATZKALIBRIERUNG der Paarschwellen — vier Szenen, vier Richtungen, elf Fälle.

**Wozu es diese Studie gibt** (01.09.2026, Owner-Entscheid): Die echte Kalibrierung
liegt als `auf-20260827-61` bei der HomeStation und braucht dort GPU-Zeit und einen
echten Tiefenschätzer. Bis sie zurückkommt, wird dieselbe Tabelle **hier** gerechnet —
mit gebauten statt geschätzten Ist-Karten.

**Das Ergebnis ist eine Obergrenze und keine Kalibrierung.** Der Fehler des Schätzers
kommt nicht vor; er trägt ein festes Ortsfeld, das allein 95,75 % der Varianz auf einem
leeren Bild erklärt. Was hier scheitert, scheitert mit einem echten Schätzer erst recht;
was hier gelingt, ist damit **nicht** bestätigt. Der Vorbehalt wird nicht nur in den
Text geschrieben, sondern an :func:`aiimaging.paarschwellen.trennkurve` übergeben —
darum kann keine dieser Tabellen sich selbst ``genuegt_als_kalibrierung`` nennen.

**Der Aufbau folgt den eigenen Befunden vom 27./28.08.:**

* **Vier Szenen** statt der geforderten drei. Fällt eine aus, ist die Messung noch gültig.
* **Vier Richtungen, zwei frontal und zwei diagonal**, und die Tabelle wird **je Gruppe
  getrennt** gerechnet: Auf frontalen Richtungen fielen 5 von 20 guten Fällen unter
  ``PAAR_RHO_SCHWELLE``, auf diagonalen keiner (`docs/RICHTUNGEN_2026-08-28.md`).
* **Die Dublettenprüfung läuft mit.** Am 27.08. waren 23 von 33 Fallarten über zwei
  Kameras auf vier Stellen punktgleich — symmetrische Bauwerke sehen von zwei Seiten
  gleich aus, und punktgleiche Zeilen blähen jede Fallzahl auf, ohne etwas zu belegen.
  Jede Gruppe wird darum **zweimal** ausgewertet: roh und entdoppelt.

    python tools/studie_ersatzkalibrierung.py build/ersatz

Ergebnis und Auswertung: `docs/PAARSCHWELLEN_OBERGRENZE_2026-09-01.md`.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from make_test_ifc import erzeuge_ifc                              # noqa: E402
from studie_paarmasse import HERZSCHLAG_S, HINTERGRUND_M, faelle   # noqa: E402
from aiimaging import bildlesen, geometrie_qa, paarschwellen, seams  # noqa: E402
from aiimaging import maske as maske_modul                         # noqa: E402

#: Vier Szenen: der Quader, das zweite Bauwerk, der Quader mit Gelände, der Quader mit
#: Räumen. ``hochbau`` und ``mit_raeumen`` schliessen einander aus (`make_test_ifc`),
#: darum stehen sie in zwei getrennten Zeilen und nicht in einer.
SZENEN = (
    ("quader", {}, False),
    ("hochbau", {"hochbau": True}, False),
    ("gelaende", {"mit_gelaende": True}, True),
    ("raeume", {"mit_raeumen": True}, False),
)

#: Zwei frontale und zwei diagonale Richtungen. Nicht vier frontale: Die Gruppe ist die
#: Auswertungseinheit, und zwei Gruppen zu je zwei Richtungen erfüllen ``MINDEST_KAMERAS``
#: je Gruppe — vier frontale hätten die diagonale Gruppe leer gelassen.
FRONTAL = ("s", "w")
DIAGONAL = ("sSE", "nNE")

AUFLOESUNG = 192
SAMPLES = 6
SAAT = 20260901

#: Auf so viele Stellen wird verglichen, wenn zwei Zeilen auf Punktgleichheit geprüft
#: werden. Vier Stellen sind die Genauigkeit, in der die Zahlen auch im Bericht stehen —
#: was dort nicht mehr zu unterscheiden ist, darf hier nicht als zwei Belege zählen.
DUBLETTE_STELLEN = 4

#: Der Vorbehalt, der an jede Trennkurve dieser Studie übergeben wird. Er steht hier als
#: Konstante und nicht als Zeichenkette an vier Stellen, damit er nicht an dreien
#: verschwindet, wenn ihn jemand an einer ändert.
VORBEHALT_PERFEKTE_KARTEN = (
    "PERFEKTE KARTEN, KEIN SCHAETZER: Die Ist-Karten sind gebaut, nicht geschaetzt. "
    "Was hier scheitert, scheitert mit einem echten Tiefenschaetzer erst recht; was "
    "hier gelingt, ist damit NICHT bestaetigt. Diese Kurve ist eine Obergrenze und "
    "ersetzt auf-20260827-61 nicht."
)


def gruppe(kamera: str) -> str:
    """Frontal oder diagonal — die Auswertungseinheit dieser Studie."""
    return "frontal" if kamera in FRONTAL else "diagonal"


def _bericht(name: str, kw: dict, mit_gelaende: bool, kamera: str, wurzel: Path) -> dict:
    """Multipass für eine Szene und eine Richtung, mit Zwischenspeicher über den Pfad."""
    ifc = wurzel / f"{name}.ifc"
    glb = wurzel / f"{name}.glb"
    if not glb.exists():
        erzeuge_ifc(ifc, schema="IFC4", **kw)
        seams.ifc_zu_glb(ifc, glb)

    aus = wurzel / f"{name}_{kamera}"
    datei = aus / "blender-report.json"
    if datei.exists():
        return json.loads(datei.read_text(encoding="utf-8"))

    zusatz = {}
    if mit_gelaende:
        # Ohne die Bauwerksbox rahmt die Kamera die ganze Platte und der Bau wird ein
        # Fleck. Ein Vorlauf in 64 Punkten kostet weniger als eine falsche Messreihe.
        vor = seams.glb_zu_multipass(glb, aus, up_axis="Y", aufloesung=64, samples=1,
                                     kamera=kamera, herzschlag_takt_s=HERZSCHLAG_S)
        if vor.get("bbox_bauwerk"):
            zusatz["kamera_huellbox"] = vor["bbox_bauwerk"]
    return seams.glb_zu_multipass(glb, aus, up_axis="Y", aufloesung=AUFLOESUNG,
                                  samples=SAMPLES, kamera=kamera,
                                  herzschlag_takt_s=HERZSCHLAG_S, **zusatz)


def sammle(wurzel: Path) -> list[dict]:
    """Alle Zeilen der Studie — je Szene, Richtung und Fall eine."""
    zeilen: list[dict] = []
    for name, kw, mit_gelaende in SZENEN:
        for kamera in FRONTAL + DIAGONAL:
            bericht = _bericht(name, kw, mit_gelaende, kamera, wurzel)
            soll, breite, hoehe = bildlesen.tiefen_aus_report(bericht)
            gebaut = maske_modul.maske_aus_bericht(bericht,
                                                  gelaende_erwartet=mit_gelaende)
            maske = gebaut.get("maske")
            if maske is None:
                print(f"!! {name}/{kamera}: keine Maske — {gebaut.get('grund')}")
                continue
            n_maske = sum(1 for x in maske if x)
            print(f"{name:<9} {kamera:<5} {gruppe(kamera):<9} {breite}x{hoehe}  "
                  f"Geometrieanteil {n_maske / len(maske):.4f}")

            # DIE SAAT WIRD JE RICHTUNG ZURUECKGESETZT — sonst bekaeme die zweite Kamera
            # anderes Rauschen als die erste, und ein Unterschied zwischen zwei
            # Richtungen waere nicht mehr von einem Unterschied zwischen zwei Wuerfen zu
            # trennen. Uebernommen aus `studie_richtungen`, wo genau das der Punkt war.
            wuerfel = random.Random(SAAT)
            for art, gut, ist in faelle(soll, maske, breite, hoehe, wuerfel):
                rho = geometrie_qa.rho_ueber_maske(
                    soll, ist, maske, polaritaet=geometrie_qa.POLARITAET_TIEFE)
                anteil = geometrie_qa.anteil_grenze_mit_kante(ist, maske, breite=breite)
                zeilen.append({
                    "fall_id": f"{name}-{kamera}-{art}", "gut": gut,
                    "szene": name, "kamera": kamera, "gruppe": gruppe(kamera),
                    "art": art,
                    "rho": rho.get("gerichtet"),
                    "kantenanteil": anteil.get("anteil"),
                    "geometrieanteil": round(n_maske / len(maske), 4),
                })
    return zeilen


def dubletten(zeilen: list[dict]) -> dict:
    """Welche Zeilen auf :data:`DUBLETTE_STELLEN` Stellen punktgleich sind.

    Verglichen wird das Paar ``(rho, kantenanteil)`` **innerhalb einer Fallart und einer
    Gruppe**. Zwei Szenen, die von zwei Richtungen dieselben Zahlen liefern, sind ein
    Beleg und nicht zwei — und ohne diese Prüfung sähe die Fallzahl doppelt so gut aus,
    ohne dass eine einzige Zahl falsch gerechnet wäre.

    Returns:
        ``gruppen`` je Schlüssel die Liste der ``fall_id`` mit demselben Wertepaar,
        ``n_dubletten`` die Zahl der Zeilen, die dabei ihren Erstling wiederholen, und
        ``ist_vertreter`` eine Liste von Wahrheitswerten **in der Reihenfolge der
        Eingabe** — wahr für die Zeile, die ihr Wertepaar zuerst gebracht hat.

    **Die Auskunft hängt an der Position und nicht an der ``fall_id``.** Zwei Zeilen mit
    derselben Kennung wären ein Datenfehler, aber sie dürfen die Entdopplung nicht
    stillschweigend verfälschen: Über die Kennung gefiltert hätte eine wiederholte
    Kennung sieben Zeilen durchgelassen, wo eine hingehört.
    """
    gesehen: dict[tuple, list[str]] = {}
    ist_vertreter: list[bool] = []
    for z in zeilen:
        schluessel = (
            z["gruppe"], z["art"],
            None if z["rho"] is None else round(z["rho"], DUBLETTE_STELLEN),
            None if z["kantenanteil"] is None
            else round(z["kantenanteil"], DUBLETTE_STELLEN),
        )
        ist_vertreter.append(schluessel not in gesehen)
        gesehen.setdefault(schluessel, []).append(z["fall_id"])
    mehrfach = {k: v for k, v in gesehen.items() if len(v) > 1}
    return {
        "gruppen": [{"gruppe": k[0], "art": k[1], "rho": k[2], "kantenanteil": k[3],
                     "fall_ids": v} for k, v in sorted(mehrfach.items(),
                                                       key=lambda p: p[1][0])],
        "n_dubletten": sum(len(v) - 1 for v in mehrfach.values()),
        "ist_vertreter": ist_vertreter,
    }


def _satz(zeilen: list[dict], schluessel: str) -> list[dict]:
    return [{"fall_id": z["fall_id"], "gut": z["gut"], "wert": z[schluessel],
             "szene": z["szene"], "kamera": z["kamera"]} for z in zeilen]


def kurven(zeilen: list[dict]) -> dict:
    """Je Gruppe und Grösse eine Trennkurve — roh und entdoppelt, acht insgesamt."""
    d = dubletten(zeilen)
    aus: dict = {"dubletten": {"n": d["n_dubletten"], "gruppen": d["gruppen"]},
                 "kurven": {}}
    for name in ("frontal", "diagonal"):
        paare = [(z, v) for z, v in zip(zeilen, d["ist_vertreter"])
                 if z["gruppe"] == name]
        roh = [z for z, _ in paare]
        entdoppelt = [z for z, v in paare if v]
        for zustand, satz in (("roh", roh), ("entdoppelt", entdoppelt)):
            if not satz:
                continue
            aus["kurven"][f"{name}/{zustand}/rho"] = paarschwellen.trennkurve(
                _satz(satz, "rho"), paarschwellen.KANDIDATEN_RHO,
                groesse="rho_maske_gerichtet",
                zusatz_vorbehalte=(VORBEHALT_PERFEKTE_KARTEN,))
            aus["kurven"][f"{name}/{zustand}/kantenanteil"] = paarschwellen.trennkurve(
                _satz(satz, "kantenanteil"), paarschwellen.KANDIDATEN_KANTENANTEIL,
                groesse="kantenanteil",
                zusatz_vorbehalte=(VORBEHALT_PERFEKTE_KARTEN,))
    return aus


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    wurzel = Path(argv[0]) if argv else Path("build/ersatz")
    wurzel.mkdir(parents=True, exist_ok=True)

    zeilen = sammle(wurzel)
    (wurzel / "roh.json").write_text(json.dumps(zeilen, indent=1), encoding="utf-8")

    ergebnis = kurven(zeilen)
    (wurzel / "kurven.json").write_text(
        json.dumps({"dubletten": ergebnis["dubletten"],
                    "kurven": ergebnis["kurven"]}, indent=1, default=list),
        encoding="utf-8")

    print(f"\nDUBLETTEN: {ergebnis['dubletten']['n']} von {len(zeilen)} Zeilen "
          f"wiederholen ein Wertepaar ihrer Gruppe")
    for schluessel, kurve in ergebnis["kurven"].items():
        print(f"\n===== {schluessel} " + "=" * (60 - len(schluessel)))
        print(paarschwellen.bericht(kurve))
    print(f"\n{len(zeilen)} Zeilen -> {wurzel}: roh.json und kurven.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
