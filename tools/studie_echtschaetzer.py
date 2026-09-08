#!/usr/bin/env python3
"""DIE FALLTABELLE MIT ECHTEM TIEFENSCHAETZER — `auf-20260907-81`.

**Wozu es diese Studie gibt.** `docs/PAARSCHWELLEN_OBERGRENZE_2026-09-01.md` rechnet
dieselbe Tabelle mit **gebauten** Ist-Karten und meldet in allen acht Kurven
``genuegt_als_kalibrierung: false`` — der Fehler des Schaetzers kommt dort gar nicht vor.
Diese Studie aendert **genau eine** Sache und sonst nichts:

    Die Ist-Karte kommt nicht mehr aus der Soll-Karte, sondern aus dem
    Beauty-Bild, geschaetzt mit `depth-anything-v2-small`.

Alles andere ist woertlich uebernommen — dieselben vier Szenen, dieselben vier
Richtungen, dieselbe Aufloesung, dieselben elf Faelle mit denselben von Hand vergebenen
Etiketten (``studie_paarmasse.faelle``, unveraendert importiert), dieselbe Saat, dieselbe
Dublettenpruefung. *Eine Aenderung je Lauf, sonst misst man zwei Dinge und weiss nachher
nicht, welches gewirkt hat.*

**Die Polaritaet wechselt mit.** Die gebauten Karten waren Tiefen in Metern
(``POLARITAET_TIEFE``, +1). Der Schaetzer liefert **Disparitaet** — nah = gross. Es gilt
die *gemessene* Polaritaet des Paares aus Schaetzer und unserer Soll-Konvention,
``geometrie_qa.GEMESSENE_POLARITAET`` = −1 (24 Laeufe, `auf-20260820-23`). Das ist keine
zweite Aenderung, sondern die Folge der ersten.

**Was die Uebernahme der elf Faelle kostet, und warum es trotzdem so herum richtig ist.**
``faelle()`` fuellt bei ``versatz_*`` und ``gedreht_90`` die leergeschobenen Spalten mit
der Hintergrundmarke 1e10. Auf einer Soll-Karte in Metern heisst das «unendlich weit»; auf
einer Disparitaetskarte waere «weit» ein *kleiner* Wert, die Marke ist dort also
sinnverkehrt. Die Marke wird trotzdem nicht angefasst — geaendert wird nur die Herkunft
der Karte —, aber jede Zeile fuehrt ``n_marke_in_maske`` mit: die Zahl der **gewerteten**
Punkte, die die Marke wirklich tragen. Ist sie null, hat der Einwand die Messung nicht
beruehrt; ist sie es nicht, steht die Zahl da und niemand muss raten.

Ebenso mitgefuehrt und nicht weggerechnet: ``bauwerk_weg`` ist hier auf **allen** Szenen
messbar, nicht nur auf ``gelaende``. Der Grund ist keine bessere Messung, sondern eine
Eigenschaft der Schaetzung: Sie kennt keine Hintergrundmarke und liefert auch fuer den
Himmel eine gewoehnliche endliche Zahl. Damit findet ``_boden_statt_bauwerk`` immer einen
Ersatzwert, und ρ ist immer definiert.

    .venv-render/bin/python tools/studie_echtschaetzer.py build/echt

Ergebnis: ``roh.json`` (die Falltabelle) und ``kurven.json`` im angegebenen Verzeichnis.
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from studie_ersatzkalibrierung import (                            # noqa: E402
    AUFLOESUNG, DIAGONAL, DUBLETTE_STELLEN, FRONTAL, SAAT, SAMPLES, SZENEN,
    _bericht, dubletten, gruppe,
)
from studie_paarmasse import HINTERGRUND_M, faelle                 # noqa: E402
from aiimaging import bildlesen, geometrie_qa, paarschwellen, tiefenschaetzer  # noqa: E402
from aiimaging import maske as maske_modul                         # noqa: E402

SCHAETZER = tiefenschaetzer.VORGABE_TIEFENSCHAETZER

#: Der Vorbehalt, der an jede Trennkurve dieser Studie geht. Er ist ein **anderer** als
#: der der Ersatzkalibrierung: Dort war die Ist-Karte gebaut, hier ist sie geschaetzt.
#: Was bleibt, ist die Herkunft des BILDES — es ist ein Blender-Render und kein erzeugtes
#: Bild. Der Schaetzerfehler steht damit drin, der Fehler des Bildmodells nicht.
VORBEHALT_RENDER_STATT_ERZEUGT = (
    "ECHTER SCHAETZER, ABER GERENDERTES BILD: Die Ist-Karte ist mit "
    "depth-anything-v2-small aus dem Beauty-Pass geschaetzt, das Bild selbst kommt aber "
    "aus Blender und nicht aus dem Bildmodell. Der Fehler des SCHAETZERS steht in diesen "
    "Zahlen, der Fehler der BILDERZEUGUNG nicht. Die elf Stoerungen sind auf die "
    "geschaetzte Karte gerechnet, nicht auf das Bild."
)


def _zeichen() -> int:
    """Das **gemessene** Vorzeichen fuer dieses Schaetzer/Soll-Paar. Kein Rateschluss."""
    z = geometrie_qa.GEMESSENE_POLARITAET.get(SCHAETZER)
    if z is None:
        raise SystemExit(
            f"Fuer {SCHAETZER!r} ist keine Polaritaet gemessen. Ohne sie waere 'gerichtet' "
            f"None und die ganze Tabelle unbrauchbar — es wird nicht geraten."
        )
    return z


def sammle(wurzel: Path, modell) -> tuple[list[dict], list[dict]]:
    """Alle Zeilen der Studie — je Szene, Richtung und Fall eine. Plus die Schaetzkoepfe."""
    zeilen: list[dict] = []
    koepfe: list[dict] = []
    zeichen = _zeichen()

    for name, kw, mit_gelaende in SZENEN:
        for kamera in FRONTAL + DIAGONAL:
            bericht = _bericht(name, kw, mit_gelaende, kamera, wurzel)
            soll, breite, hoehe = bildlesen.tiefen_aus_report(bericht)
            gebaut = maske_modul.maske_aus_bericht(bericht,
                                                   gelaende_erwartet=mit_gelaende)
            maske = gebaut.get("maske")
            if maske is None:
                # KEIN STILLES WEGLASSEN: eine Zeile mit dem Grund, nicht eine fehlende.
                koepfe.append({"szene": name, "kamera": kamera,
                               "gruppe": gruppe(kamera), "status": "keine_maske",
                               "grund": str(gebaut.get("grund"))})
                print(f"!! {name}/{kamera}: keine Maske — {gebaut.get('grund')}")
                continue

            beauty = bericht.get("beauty_png")
            if not beauty:
                koepfe.append({"szene": name, "kamera": kamera,
                               "gruppe": gruppe(kamera), "status": "kein_beauty",
                               "grund": "Der Multipass-Bericht nennt kein beauty_png."})
                print(f"!! {name}/{kamera}: kein Beauty-Bild im Bericht")
                continue

            schaetzung = tiefenschaetzer.schaetze_tiefe(
                beauty, schaetzer=SCHAETZER, modell=modell,
                hintergrund_strategie=tiefenschaetzer.HG_KEINE,
                breite=breite, hoehe=hoehe)
            if schaetzung["status"] != tiefenschaetzer.STATUS_OK:
                koepfe.append({"szene": name, "kamera": kamera,
                               "gruppe": gruppe(kamera), "status": schaetzung["status"],
                               "grund": str(schaetzung.get("error"))})
                print(f"!! {name}/{kamera}: Schaetzung {schaetzung['status']} — "
                      f"{schaetzung.get('error')}")
                continue

            basis = list(schaetzung["tiefen"])
            n_maske = sum(1 for x in maske if x)
            n_boden = sum(1 for w, m in zip(soll, maske)
                          if (not m) and w < HINTERGRUND_M)
            endlich = [w for w in basis if w < HINTERGRUND_M]
            koepfe.append({
                "szene": name, "kamera": kamera, "gruppe": gruppe(kamera),
                "status": "ok", "grund": "",
                "breite": breite, "hoehe": hoehe,
                "geometrieanteil": round(n_maske / len(maske), 4),
                "bodenanteil": round(n_boden / len(maske), 4),
                "schaetzung_min": round(min(endlich), 6) if endlich else None,
                "schaetzung_max": round(max(endlich), 6) if endlich else None,
                "schaetzung_dauer_s": round(float(schaetzung.get("dauer_s") or 0.0), 3),
            })
            print(f"{name:<9} {kamera:<5} {gruppe(kamera):<9} {breite}x{hoehe}  "
                  f"Geometrieanteil {n_maske / len(maske):.4f}  "
                  f"Bodenanteil {n_boden / len(maske):.4f}  "
                  f"Schaetzung [{min(endlich):.3f} .. {max(endlich):.3f}]")

            # DIE SAAT WIRD JE RICHTUNG ZURUECKGESETZT — wie in der Ersatzkalibrierung,
            # damit ein Unterschied zwischen zwei Richtungen nicht von einem Unterschied
            # zwischen zwei Wuerfen kommt.
            wuerfel = random.Random(SAAT)
            for art, gut, ist in faelle(basis, maske, breite, hoehe, wuerfel):
                rho = geometrie_qa.rho_ueber_maske(soll, ist, maske, polaritaet=zeichen)
                kante = geometrie_qa.kante_an_maskengrenze(ist, maske, breite=breite,
                                                           polaritaet=zeichen)
                anteil = geometrie_qa.anteil_grenze_mit_kante(ist, maske, breite=breite)
                himmel = geometrie_qa.himmel_hinter_umriss(soll, maske, breite=breite)
                urteil = geometrie_qa.paarurteil(rho, kante, anteil_ergebnis=anteil,
                                                 himmel_ergebnis=himmel)
                marke = sum(1 for w, m in zip(ist, maske) if m and w >= HINTERGRUND_M)
                zeilen.append({
                    "fall_id": f"{name}-{kamera}-{art}", "gut": gut,
                    "szene": name, "kamera": kamera, "gruppe": gruppe(kamera),
                    "art": art,
                    "rho": rho.get("gerichtet"),
                    # ACHTUNG, SCHLUESSELNAME: `rho_ueber_maske` liefert das rohe
                    # Spearman unter `rho` und das polaritaetsbereinigte unter
                    # `gerichtet` — nicht unter `spearman`. Am 08.09.2026 stand hier
                    # `spearman`, und die Spalte war in allen 176 Zeilen still `None`.
                    "rho_roh": rho.get("rho"),
                    "kantenanteil": anteil.get("anteil"),
                    "paarurteil_bestanden": urteil.get("bestanden"),
                    "paarurteil_gemessen": urteil.get("gemessen"),
                    "paarurteil_zustaendig": urteil.get("zustaendig"),
                    "paarurteil_traeger": urteil.get("traeger"),
                    "geometrieanteil": round(n_maske / len(maske), 4),
                    "bodenanteil": round(n_boden / len(maske), 4),
                    "n_marke_in_maske": marke,
                })
    return zeilen, koepfe


def _satz(zeilen: list[dict], schluessel: str) -> list[dict]:
    return [{"fall_id": z["fall_id"], "gut": z["gut"], "wert": z[schluessel],
             "szene": z["szene"], "kamera": z["kamera"]} for z in zeilen]


def kurven(zeilen: list[dict]) -> dict:
    """Je Gruppe und Groesse eine Trennkurve — roh und entdoppelt, acht insgesamt."""
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
                zusatz_vorbehalte=(VORBEHALT_RENDER_STATT_ERZEUGT,))
            aus["kurven"][f"{name}/{zustand}/kantenanteil"] = paarschwellen.trennkurve(
                _satz(satz, "kantenanteil"), paarschwellen.KANDIDATEN_KANTENANTEIL,
                groesse="kantenanteil",
                zusatz_vorbehalte=(VORBEHALT_RENDER_STATT_ERZEUGT,))
    return aus


def fenster(zeilen: list[dict], schluessel: str = "rho") -> dict:
    """Das fehlerfreie Fenster je Richtungsgruppe — V2, gerechnet aus V1 und sonst nichts."""
    aus = {}
    for name in ("frontal", "diagonal"):
        gut = [z[schluessel] for z in zeilen
               if z["gruppe"] == name and z["gut"] and z[schluessel] is not None]
        schlecht = [z[schluessel] for z in zeilen
                    if z["gruppe"] == name and not z["gut"] and z[schluessel] is not None]
        if not gut or not schlecht:
            aus[name] = {"trennt_sauber": None, "n_gut": len(gut),
                         "n_schlecht": len(schlecht)}
            continue
        hoch, tief = max(schlecht), min(gut)
        aus[name] = {
            "hoechster_schlechter": round(hoch, 4),
            "niedrigster_guter": round(tief, 4),
            "trennt_sauber": hoch < tief,
            "fenster": (round(hoch, 4), round(tief, 4)) if hoch < tief else None,
            "n_gut": len(gut), "n_schlecht": len(schlecht),
        }
    return aus


def kosten_der_schwelle(zeilen: list[dict], schwelle: float = 0.80) -> dict:
    """V3 — wie oft die heutige Schwelle einen GUTEN Fall sperrt, je Gruppe."""
    aus = {}
    for name in ("frontal", "diagonal"):
        g = [z for z in zeilen if z["gruppe"] == name and z["gut"]]
        s = [z for z in zeilen if z["gruppe"] == name and not z["gut"]]
        gesperrt = [z for z in g if z["rho"] is not None and z["rho"] < schwelle]
        durch = [z for z in s if z["rho"] is not None and z["rho"] >= schwelle]
        aus[name] = {
            "schwelle": schwelle,
            "gute_zeilen": len(g),
            "gute_messbar": sum(1 for z in g if z["rho"] is not None),
            "falsch_gesperrt": len(gesperrt),
            "falsch_gesperrte_faelle": [
                {"fall_id": z["fall_id"], "rho": round(z["rho"], 4)}
                for z in sorted(gesperrt, key=lambda z: z["rho"])],
            "schlechte_zeilen": len(s),
            "schlechte_messbar": sum(1 for z in s if z["rho"] is not None),
            "falsch_bestanden": len(durch),
            "falsch_bestandene_faelle": [
                {"fall_id": z["fall_id"], "rho": round(z["rho"], 4)}
                for z in sorted(durch, key=lambda z: -z["rho"])],
        }
    return aus


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    wurzel = Path(argv[0]) if argv else Path("build/echt")
    wurzel.mkdir(parents=True, exist_ok=True)

    beginn = time.time()
    print(f"Schaetzer {SCHAETZER}, gemessene Polaritaet {_zeichen()} "
          f"({AUFLOESUNG} px, {SAMPLES} Samples, Saat {SAAT})")
    modell = tiefenschaetzer.lade_modell(SCHAETZER)

    zeilen, koepfe = sammle(wurzel, modell)
    (wurzel / "roh.json").write_text(json.dumps(zeilen, indent=1), encoding="utf-8")
    (wurzel / "koepfe.json").write_text(json.dumps(koepfe, indent=1), encoding="utf-8")

    ergebnis = kurven(zeilen)
    ergebnis["fenster_rho"] = fenster(zeilen, "rho")
    ergebnis["fenster_kantenanteil"] = fenster(zeilen, "kantenanteil")
    ergebnis["kosten_080"] = kosten_der_schwelle(zeilen, 0.80)
    ergebnis["schaetzer"] = SCHAETZER
    ergebnis["polaritaet"] = _zeichen()
    ergebnis["dubletten_stellen"] = DUBLETTE_STELLEN
    ergebnis["dauer_s"] = round(time.time() - beginn, 1)
    (wurzel / "kurven.json").write_text(json.dumps(ergebnis, indent=1, default=list),
                                        encoding="utf-8")

    print(f"\nDUBLETTEN: {ergebnis['dubletten']['n']} von {len(zeilen)} Zeilen "
          f"wiederholen ein Wertepaar ihrer Gruppe")
    for schluessel, kurve in ergebnis["kurven"].items():
        print(f"\n===== {schluessel} " + "=" * (60 - len(schluessel)))
        print(paarschwellen.bericht(kurve))
    print(f"\nFENSTER rho: {json.dumps(ergebnis['fenster_rho'])}")
    print(f"KOSTEN 0.80: frontal falsch_gesperrt="
          f"{ergebnis['kosten_080']['frontal']['falsch_gesperrt']}, "
          f"diagonal falsch_gesperrt="
          f"{ergebnis['kosten_080']['diagonal']['falsch_gesperrt']}")
    print(f"\n{len(zeilen)} Zeilen -> {wurzel}: roh.json, koepfe.json, kurven.json "
          f"({ergebnis['dauer_s']} s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
