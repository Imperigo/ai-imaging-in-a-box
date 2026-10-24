"""Umfeld — freie 3D-Modelle (Bäume, Büsche, Autos), Wiese und Strasse um das Haus.

**Anlass:** Owner-Wunsch vom 24.10.2026: *«Ein neuer Knoten, mit dem Claude und Visbox selbst gute,
hochwertige, freie 3D-Assets aus verlässlichen Online-Datenbanken holen und die Szene des
Grundmodells direkt und sauber mit Autos, Strassen, Bäumen, Büschen und grünen Landschaften
auffrischen.»* Entscheid 97a sagt, wozu: möglichst viel modelliert und der KI als Grundlage
geliefert — die KI ergänzt.

Was hier steht — alles ohne Blender und ohne Netz prüfbar (Regel 2, Regel 4):

* :data:`ASSETS` und :data:`QUELLEN` — der kuratierte Katalog. Jede Quelle und jedes Asset trägt
  Lizenz und Adresse. **Nur CC0** (:func:`pruefe_lizenz`): Was nicht CC0 ist, weist der Code ab,
  bevor ein Byte geladen wird.
* :func:`freigeschaltet` — der Schalter :data:`SCHALTER_ENV`. **Owner-Entscheid 147 (24.10.2026):** CC0
  gilt auch für 3D-Modelle, unter denselben Bedingungen wie Texturen (am Heim-PC geladen, nie
  ausgeliefert, jede Quelle im NOTICE) — Modelle nur aus Poly Haven, Kenney und Quaternius, kein
  CC-BY, kein Sketchfab. Das Laden ist darum **an** (Vorgabe); ``AIIMAGING_UMFELD_MODELLE=0`` schaltet es
  aus. Texturen dürfen nach Entscheid 107 zudem von ambientCG kommen.
* :func:`hole_asset` — Laden mit Prüfsumme in den Zwischenspeicher am Heim-PC
  (:data:`ORDNER_ENV`, nie ins Repo, Regel 3). Was dort liegt, geht ohne Netz; was fehlt, ergibt
  einen Satz, nie einen Absturz.
* :func:`plane` — der **Platzierungsplan**: rein rechnend, mit Startwert wiederholbar. Nie im
  Haus und nie näher als :data:`ABSTAND_HAUS_M`; nie im **Sichtkegel** einer Kamera auf das Haus
  (das Haus bleibt ganz sichtbar — hier wird die Deckung am Haus gemessen); Bäume und Büsche auf
  dem Gelände in seiner Höhe, Autos auf der Strasse, die Strasse als Streifen auf der Seite der
  ersten Kamera (oder auf einer Strasse, die das Modell schon hat).
* :func:`plane_fuer_glb` — dasselbe aus einer glb: Gelände, Bauwerk und Kameras aus den Lesern,
  die es schon gibt (``glbbox``, ``kosmo_szene.gelaende_in_glb``, ``kameras.kamerasatz``).

**Umfeld, nicht Bauwerk:** Was hier gestellt wird, zählt in der Bauwerksmaske, in der Deckung, im
Umriss und im Kontrast als Umfeld. Der Blender-Runner gibt den Materialien darum Namen, die die
eine Regel dafür erkennt (:func:`aiimaging.maske.ist_umfeld`: Klassenanfang
``IfcGeographicElement``/``IfcCivilElement``) — :func:`material_name` steht hier, damit der
Runner sie nicht selbst erfindet.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import random
import re
import struct
import time
import zipfile
from pathlib import Path

__all__ = [
    "SCHALTER_ENV", "ORDNER_ENV", "KATEGORIEN", "KATEGORIE_LABEL", "DICHTEN", "DICHTE_VORGABE",
    "LIZENZ_CC0", "QUELLEN", "ASSETS", "PAKETE", "ABSTAND_HAUS_M", "SICHT_RAND_M",
    "UmfeldFehler", "LizenzFehler", "GesperrtFehler", "NetzFehler",
    "freigeschaltet", "ordner", "pruefe_lizenz", "asset", "assets_der_kategorie",
    "vorgaben_der_kategorie", "lies_wunsch", "hole_asset", "im_speicher", "hole_plan",
    "plane", "plane_fuer_glb", "lies_glb_umfeld", "material_name", "klasse_der_kategorie",
    "SATZ_GESPERRT", "satz_gesperrt", "katalog_fuer_anzeige", "PLAN_SCHEMA", "DATEI_SCHEMA",
]

#: Der Schalter. Seit Entscheid 147 (24.10.2026) ist das Laden an; ``"0"`` (oder ``aus``/``false``)
#: schaltet es am Heim-PC aus — dann geht nur, was schon im Zwischenspeicher liegt.
SCHALTER_ENV = "AIIMAGING_UMFELD_MODELLE"
#: Der Zwischenspeicher der geladenen Modelle und Texturen — nur am Heim-PC, nie im Repo.
ORDNER_ENV = "AIIMAGING_UMFELD_ORDNER"

KATEGORIEN = ("baeume", "buesche", "wiese", "strasse", "autos")
KATEGORIE_LABEL = {"baeume": "Bäume", "buesche": "Büsche", "wiese": "Wiese",
                   "strasse": "Strasse", "autos": "Autos"}
DICHTEN = ("wenig", "mittel", "viel")
DICHTE_VORGABE = "mittel"
#: Höchstzahl je Kategorie, die eine Bestellung ausdrücklich nennen darf (``anzahl``).
ANZAHL_HOECHSTENS = 30

LIZENZ_CC0 = "CC0-1.0"

#: Die Quellen. Jede ist CC0 als Ganzes — und jedes Asset trägt die Lizenz trotzdem selbst, weil
#: die Prüfung je Asset geschieht (:func:`pruefe_lizenz`).
QUELLEN = {
    "polyhaven": {"name": "Poly Haven", "adresse": "https://polyhaven.com",
                  "api": "https://api.polyhaven.com", "lizenz": LIZENZ_CC0,
                  "lizenz_adresse": "https://polyhaven.com/license"},
    "kenney": {"name": "Kenney", "adresse": "https://kenney.nl", "lizenz": LIZENZ_CC0,
               "lizenz_adresse": "https://creativecommons.org/publicdomain/zero/1.0/"},
    "ambientcg": {"name": "ambientCG", "adresse": "https://ambientcg.com", "lizenz": LIZENZ_CC0,
                  "lizenz_adresse": "https://docs.ambientcg.com/license/"},
    # Entscheid 147: zugelassen, noch kein Asset im Katalog (Downloads nicht stabil adressierbar).
    "quaternius": {"name": "Quaternius", "adresse": "https://quaternius.com", "lizenz": LIZENZ_CC0,
                   "lizenz_adresse": "https://quaternius.com"},
}

#: Entscheid 147 (24.10.2026): woher ein 3D-MODELL kommen darf — genau diese drei, kein CC-BY, kein
#: Sketchfab. Texturen (Wiese, Asphalt) nach Entscheid 107 aus Poly Haven oder ambientCG.
QUELLEN_MODELLE = ("polyhaven", "kenney", "quaternius")
QUELLEN_TEXTUREN = ("polyhaven", "ambientcg")

#: Gepackte Downloads (Zip) mit fester Adresse und Prüfsumme — geprüft am 24.10.2026 aus dem
#: Container. Ändert die Quelle die Datei, stimmt die Prüfsumme nicht mehr, und das Laden weist
#: ab (mit Satz), statt eine ungeprüfte Datei zu nehmen.
PAKETE = {
    "kenney-car-kit": {
        "quelle": "kenney",
        "url": "https://kenney.nl/media/pages/assets/car-kit/1a312ec241-1775131960/kenney_car-kit.zip",
        "sha256": "fac7dacac5c7874348cf19729af3ef205f3d366493edaf0a827d93f4fdf3d0c4",
        "bytes": 4814237, "lizenz_datei": "License.txt",
        "seite": "https://kenney.nl/assets/car-kit"},
    "ambientcg-grass004": {
        "quelle": "ambientcg",
        "url": "https://ambientcg.com/get?file=Grass004_1K-JPG.zip",
        "sha256": "4b63495f459db8481f4d5144e4e9069345c81cf898cc71f2216f5dd3bb344469",
        "bytes": 11003149, "lizenz_datei": None,
        "seite": "https://ambientcg.com/view?id=Grass004"},
}

#: Der Katalog — kuratiert, nicht gesucht. ``vorgabe``: nimmt der Plan, wenn nichts anderes
#: gewählt ist (die schweren Bäume nicht — 215 MB für einen Baum lohnen eine Vorschau nicht).
#: ``bytes``: Grösse des Downloads (1k), gemessen am 24.10.2026. Die langen Achsen der Autos
#: liegen in Blender längs y (Kenney und Poly Haven gleich, gemessen).
#:
#: ``masse``: ``hoehe_m`` (Vegetation, von–bis) oder ``laenge_m`` (Autos); ``radius_m`` ist der
#: Platz, den ein Stück am Boden braucht (Krone, halbe Wagenlänge).
ASSETS = (
    {"id": "tree_small_02", "kategorie": "baeume", "quelle": "polyhaven", "art": "modell",
     "label": "Laubbaum", "lizenz": LIZENZ_CC0, "seite": "https://polyhaven.com/a/tree_small_02",
     "bytes": 100974143, "hoehe_m": (6.5, 9.0), "radius_m": 2.6, "vorgabe": True},
    {"id": "island_tree_02", "kategorie": "baeume", "quelle": "polyhaven", "art": "modell",
     "label": "Laubbaum, licht", "lizenz": LIZENZ_CC0,
     "seite": "https://polyhaven.com/a/island_tree_02",
     "bytes": 46172406, "hoehe_m": (5.5, 8.0), "radius_m": 2.4, "vorgabe": True},
    {"id": "jacaranda_tree", "kategorie": "baeume", "quelle": "polyhaven", "art": "modell",
     "label": "Grosser Laubbaum", "lizenz": LIZENZ_CC0,
     "seite": "https://polyhaven.com/a/jacaranda_tree",
     "bytes": 214609299, "hoehe_m": (9.0, 12.0), "radius_m": 4.0, "vorgabe": False},
    {"id": "searsia_lucida", "kategorie": "buesche", "quelle": "polyhaven", "art": "modell",
     "label": "Busch", "lizenz": LIZENZ_CC0, "seite": "https://polyhaven.com/a/searsia_lucida",
     "bytes": 19816833, "hoehe_m": (1.2, 2.0), "radius_m": 0.9, "vorgabe": True},
    {"id": "shrub_02", "kategorie": "buesche", "quelle": "polyhaven", "art": "modell",
     "label": "Strauch", "lizenz": LIZENZ_CC0, "seite": "https://polyhaven.com/a/shrub_02",
     "bytes": 1966425, "hoehe_m": (0.8, 1.4), "radius_m": 0.7, "vorgabe": True},
    {"id": "kenney-sedan", "kategorie": "autos", "quelle": "kenney", "art": "modell",
     "label": "Limousine", "lizenz": LIZENZ_CC0, "seite": PAKETE["kenney-car-kit"]["seite"],
     "paket": "kenney-car-kit", "datei": "Models/GLB format/sedan.glb",
     "bytes": PAKETE["kenney-car-kit"]["bytes"], "laenge_m": (4.5, 4.8), "radius_m": 2.4,
     "vorgabe": True},
    {"id": "kenney-suv", "kategorie": "autos", "quelle": "kenney", "art": "modell",
     "label": "Geländewagen", "lizenz": LIZENZ_CC0, "seite": PAKETE["kenney-car-kit"]["seite"],
     "paket": "kenney-car-kit", "datei": "Models/GLB format/suv.glb",
     "bytes": PAKETE["kenney-car-kit"]["bytes"], "laenge_m": (4.6, 4.9), "radius_m": 2.5,
     "vorgabe": True},
    {"id": "kenney-van", "kategorie": "autos", "quelle": "kenney", "art": "modell",
     "label": "Lieferwagen", "lizenz": LIZENZ_CC0, "seite": PAKETE["kenney-car-kit"]["seite"],
     "paket": "kenney-car-kit", "datei": "Models/GLB format/van.glb",
     "bytes": PAKETE["kenney-car-kit"]["bytes"], "laenge_m": (5.0, 5.3), "radius_m": 2.7,
     "vorgabe": False},
    {"id": "covered_car", "kategorie": "autos", "quelle": "polyhaven", "art": "modell",
     "label": "Abgedecktes Auto", "lizenz": LIZENZ_CC0,
     "seite": "https://polyhaven.com/a/covered_car",
     "bytes": 2349276, "laenge_m": (4.3, 4.5), "radius_m": 2.3, "vorgabe": False},
    {"id": "Grass004", "kategorie": "wiese", "quelle": "ambientcg", "art": "textur",
     "label": "Rasen", "lizenz": LIZENZ_CC0, "seite": PAKETE["ambientcg-grass004"]["seite"],
     "paket": "ambientcg-grass004", "bytes": PAKETE["ambientcg-grass004"]["bytes"],
     "massstab_m": 2.0, "vorgabe": True},
    {"id": "asphalt_02", "kategorie": "strasse", "quelle": "polyhaven", "art": "textur",
     "label": "Asphalt", "lizenz": LIZENZ_CC0, "seite": "https://polyhaven.com/a/asphalt_02",
     "bytes": 2870804, "massstab_m": 3.0, "vorgabe": True},
)

#: Abstand jedes gestellten Stücks zum Haus (Rand der Krone bzw. des Wagens), in Metern.
ABSTAND_HAUS_M = 2.0
#: Zusätzlicher Rand um jeden Sichtkegel — ein Stück, das den Kegel streift, verdeckt eine Kante.
SICHT_RAND_M = 1.0
#: Abstand der Strasse zum Haus (zusätzlich zu :data:`ABSTAND_HAUS_M`): ein Trottoir.
TROTTOIR_M = 1.0
STRASSE_BREITE_M = 6.0
STRASSE_BREITE_MIN_M = 3.0
#: Abstand zweier Autos längs der Strasse (Mitte zu Mitte), mindestens.
AUTO_ABSTAND_M = 6.5
#: Wie dicht je Stufe: Fläche je Stück in m² (Bäume, Büsche) bzw. Autos je Strasse.
DICHTE_FLAECHE_M2 = {"baeume": {"wenig": 320.0, "mittel": 160.0, "viel": 80.0},
                     "buesche": {"wenig": 120.0, "mittel": 60.0, "viel": 30.0}}
DICHTE_AUTOS = {"wenig": 1, "mittel": 2, "viel": 4}
HOECHSTENS = {"baeume": 25, "buesche": 40, "autos": 12}
#: Versuche je gewünschtem Stück, bevor der Plan aufgibt und es sagt.
VERSUCHE_JE_STUECK = 80
#: Wörter, an denen eine schon modellierte Strasse erkannt wird (auf Wortgrenzen).
STRASSEN_WOERTER = ("strasse", "straße", "strassen", "street", "road", "fahrbahn")
#: Mehr Dreiecke liest der Plan für die Geländehöhe nicht — darüber gilt die Box (mit Satz).
DREIECKE_HOECHSTENS = 400_000

PLAN_SCHEMA = "aiimaging.umfeld-plan/v1"
DATEI_SCHEMA = "aiimaging.umfeld/v1"
HERKUNFT_DATEI = "herkunft.json"
#: Wer wir sind, wenn wir laden — Poly Haven bittet um eine eigene Kennung.
USER_AGENT = "aiimaging-visbox-umfeld/1 (+https://github.com/andrinbau/ai-imaging-in-a-box)"

SATZ_GESPERRT = (
    "Umfeld bestellt, aber das Laden ist am Heim-PC ausgeschaltet ({schalter}). Gerechnet wird mit dem, "
    "was schon im Zwischenspeicher liegt — fehlt es, ohne Bäume, Büsche und Autos.")


class UmfeldFehler(RuntimeError):
    """Etwas am Umfeld ging nicht — immer mit einem Satz, den ein Mensch versteht."""


class LizenzFehler(UmfeldFehler):
    """Ein Asset oder eine Quelle ist nicht CC0 — abgewiesen, bevor geladen wird."""


class GesperrtFehler(UmfeldFehler):
    """Der Schalter ist aus."""


class NetzFehler(UmfeldFehler):
    """Laden ging nicht (kein Netz, falsche Prüfsumme, unerwartete Antwort)."""


# ============================================================ Schalter, Ordner, Lizenz

def freigeschaltet(umgebung=None) -> bool:
    """Ist das Laden am Heim-PC eingeschaltet? Ja, ausser ``AIIMAGING_UMFELD_MODELLE`` ist 0/aus/false
    (Entscheid 147: Vorgabe an)."""
    wert = str((umgebung if umgebung is not None else os.environ).get(SCHALTER_ENV, "")).strip().lower()
    return wert not in ("0", "aus", "false", "nein", "off")


def satz_gesperrt() -> str:
    return SATZ_GESPERRT.format(schalter=f"{SCHALTER_ENV}=0")


def ordner(umgebung=None) -> Path | None:
    wert = (umgebung if umgebung is not None else os.environ).get(ORDNER_ENV)
    return Path(wert) if wert else None


def asset(kennung: str) -> dict:
    for eintrag in ASSETS:
        if eintrag["id"] == kennung:
            return eintrag
    raise UmfeldFehler(f"Kein Asset {kennung!r} im Katalog des Umfelds.")


def assets_der_kategorie(kategorie: str) -> list[dict]:
    return [e for e in ASSETS if e["kategorie"] == kategorie]


def vorgaben_der_kategorie(kategorie: str) -> list[dict]:
    return [e for e in ASSETS if e["kategorie"] == kategorie and e.get("vorgabe")]


def pruefe_lizenz(eintrag: dict) -> None:
    """Weist ab, was nicht CC0 ist — das Asset selbst **und** seine Quelle.

    Die Prüfung steht vor jedem Laden (:func:`hole_asset`) und vor jedem Plan
    (:func:`plane`). Ein Eintrag ohne Lizenz gilt als nicht CC0: Was niemand geprüft hat, ist
    nicht frei.
    """
    lizenz = str(eintrag.get("lizenz") or "")
    quelle = QUELLEN.get(str(eintrag.get("quelle") or ""))
    if lizenz != LIZENZ_CC0:
        raise LizenzFehler(
            f"Asset {eintrag.get('id')!r} trägt die Lizenz {lizenz or 'keine'!r}, nicht "
            f"{LIZENZ_CC0} — abgewiesen. Ins Umfeld kommt nur, was gemeinfrei ist (Regel 1).")
    if quelle is None or quelle.get("lizenz") != LIZENZ_CC0:
        raise LizenzFehler(
            f"Die Quelle {eintrag.get('quelle')!r} von {eintrag.get('id')!r} ist keine "
            f"geprüfte CC0-Quelle — abgewiesen.")
    erlaubt = QUELLEN_MODELLE if eintrag.get("art") == "modell" else QUELLEN_TEXTUREN
    if eintrag.get("quelle") not in erlaubt:
        raise LizenzFehler(
            f"{eintrag.get('id')!r} ({eintrag.get('art')}) kommt von {eintrag.get('quelle')!r} — zugelassen sind "
            f"für Modelle nur {', '.join(QUELLEN_MODELLE)} (Entscheid 147), für Texturen "
            f"{', '.join(QUELLEN_TEXTUREN)} (Entscheid 107). Abgewiesen.")
    if eintrag.get("paket") and eintrag["paket"] not in PAKETE:
        raise LizenzFehler(f"Das Paket {eintrag['paket']!r} hat keine feste Adresse und "
                           f"Prüfsumme — abgewiesen.")


def katalog_fuer_anzeige() -> list[dict]:
    """Der Katalog ohne Heim-PC-Felder — das, was der Knoten zeigt (Lizenz und Quelle je Stück)."""
    return [{"id": e["id"], "kategorie": e["kategorie"], "label": e["label"],
             "quelle": QUELLEN[e["quelle"]]["name"], "lizenz": e["lizenz"], "seite": e["seite"],
             "mb": round(e["bytes"] / 1e6, 1), "vorgabe": bool(e.get("vorgabe"))}
            for e in ASSETS]


def klasse_der_kategorie(kategorie: str) -> str:
    """Der Klassenanfang, an dem :func:`aiimaging.maske.ist_umfeld` das Stück erkennt."""
    return "IfcGeographicElement" if kategorie in ("baeume", "buesche") else "IfcCivilElement"


def material_name(kategorie: str, asset_id: str, nummer: int) -> str:
    """Der Materialname eines gestellten Stücks — von der Maske als Umfeld erkannt.

    ``IfcGeographicElement_Umfeld_baeume_tree_small_02_0`` — der Klassenanfang trägt die
    Erkennung (:data:`aiimaging.maske.UMFELD_KLASSEN`), kein neues Wort in einer Wortliste.
    """
    sauber = re.sub(r"[^A-Za-z0-9_-]+", "-", str(asset_id))
    return f"{klasse_der_kategorie(kategorie)}_Umfeld_{kategorie}_{sauber}_{int(nummer)}"


# ============================================================ der Wunsch aus der Bestellung

def lies_wunsch(roh) -> tuple[dict | None, list[str]]:
    """``vis.umfeld`` → ``({kategorien, dichte, seed, anzahl?}, maengel)``.

    ``None`` ohne Bestellung. Unbekannte Kategorien, Dichten oder Felder sind ein Mangel (sie
    halten den Lauf auf wie jedes unbekannte Feld); eine leere Kategorienliste bestellt nichts
    und ist darum auch ein Mangel — «nichts gewählt» heisst: Feld weglassen.
    """
    if roh is None:
        return None, []
    maengel: list[str] = []
    if not isinstance(roh, dict):
        return None, [f"'vis.umfeld' ist {roh!r} und kein Block {{kategorien, dichte?, seed?, "
                      f"anzahl?}}."]
    fremd = sorted(set(roh) - {"kategorien", "dichte", "seed", "anzahl"})
    if fremd:
        maengel.append(f"Unbekannte Felder in 'vis.umfeld': {', '.join(fremd)}.")
    kat = roh.get("kategorien")
    if not isinstance(kat, list) or not kat or not all(isinstance(k, str) for k in kat):
        maengel.append("'vis.umfeld.kategorien' braucht eine Liste aus "
                       f"{', '.join(KATEGORIEN)} — leer bestellt sie nichts; dann das Feld "
                       f"weglassen.")
        kat = []
    unbekannt = [k for k in kat if k not in KATEGORIEN]
    if unbekannt:
        maengel.append(f"Unbekannte Kategorien in 'vis.umfeld.kategorien': "
                       f"{', '.join(unbekannt)} (bekannt: {', '.join(KATEGORIEN)}).")
    dichte = roh.get("dichte", DICHTE_VORGABE)
    if dichte not in DICHTEN:
        maengel.append(f"'vis.umfeld.dichte' ist {dichte!r}; bekannt sind {', '.join(DICHTEN)}.")
    seed = roh.get("seed", 0)
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= 2147483647:
        maengel.append(f"'vis.umfeld.seed' ist {seed!r} und keine ganze Zahl 0..2147483647.")
    anzahl = roh.get("anzahl")
    if anzahl is not None:
        if not isinstance(anzahl, dict) or any(
                k not in ("baeume", "buesche", "autos") or isinstance(v, bool)
                or not isinstance(v, int) or not 0 <= v <= ANZAHL_HOECHSTENS
                for k, v in anzahl.items()):
            maengel.append(f"'vis.umfeld.anzahl' ist {anzahl!r}; erlaubt sind baeume, buesche, "
                           f"autos mit ganzen Zahlen 0..{ANZAHL_HOECHSTENS}.")
    if maengel:
        return None, maengel
    wunsch = {"kategorien": [k for k in KATEGORIEN if k in kat], "dichte": dichte, "seed": seed}
    if anzahl:
        wunsch["anzahl"] = {k: int(anzahl[k]) for k in ("baeume", "buesche", "autos")
                            if k in anzahl}
    return wunsch, []


# ============================================================ Laden und Zwischenspeicher

def _standard_oeffner(url: str) -> bytes:                       # pragma: no cover — Netz
    import urllib.request
    anfrage = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(anfrage, timeout=120) as antwort:
        return antwort.read()


def _sicherer_teilpfad(teil: str) -> Path:
    """Ein relativer Pfad aus einer fremden Antwort — ohne ``..`` und ohne Wurzel."""
    p = Path(str(teil).replace("\\", "/"))
    if p.is_absolute() or any(t in ("..", "") for t in p.parts) or not p.parts:
        raise NetzFehler(f"Unerwarteter Dateiname in der Antwort der Quelle: {teil!r}.")
    return p


def _schreibe(ziel: Path, daten: bytes) -> None:
    ziel.parent.mkdir(parents=True, exist_ok=True)
    tmp = ziel.with_name(ziel.name + ".tmp")
    tmp.write_bytes(daten)
    tmp.replace(ziel)


def _asset_ordner(wurzel: Path, eintrag: dict) -> Path:
    return Path(wurzel) / eintrag["quelle"] / eintrag["id"]


def im_speicher(kennung: str, *, wurzel=None) -> dict | None:
    """Liegt das Asset vollständig im Zwischenspeicher? Dann seine Herkunft, sonst ``None``."""
    wurzel = Path(wurzel) if wurzel is not None else ordner()
    if wurzel is None:
        return None
    eintrag = asset(kennung)
    herkunft_pfad = _asset_ordner(wurzel, eintrag) / HERKUNFT_DATEI
    try:
        herkunft = json.loads(herkunft_pfad.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    basis = herkunft_pfad.parent
    if not all((basis / d).is_file() for d in herkunft.get("dateien") or ()):
        return None
    return dict(herkunft, ordner=str(basis))


def _polyhaven_modell(eintrag, oeffner) -> dict:
    api = json.loads(oeffner(f"{QUELLEN['polyhaven']['api']}/files/{eintrag['id']}"))
    try:
        haupt = api["gltf"]["1k"]["gltf"]
    except (KeyError, TypeError) as e:
        raise NetzFehler(f"Poly Haven nennt für {eintrag['id']!r} kein glTF in 1k.") from e
    dateien = {f"{eintrag['id']}_1k.gltf": (haupt["url"], haupt.get("md5"))}
    for teil, info in (haupt.get("include") or {}).items():
        dateien[str(_sicherer_teilpfad(teil))] = (info["url"], info.get("md5"))
    return {"dateien": dateien, "haupt": f"{eintrag['id']}_1k.gltf"}


#: Die Karten einer Poly-Haven-Textur, in den Namen der Materialwahl (``materialwahl.KARTEN``).
POLYHAVEN_KARTEN = {"Diffuse": "Color", "Rough": "Roughness", "nor_gl": "NormalGL",
                    "Displacement": "Displacement"}


def _polyhaven_textur(eintrag, oeffner) -> dict:
    api = json.loads(oeffner(f"{QUELLEN['polyhaven']['api']}/files/{eintrag['id']}"))
    dateien, karten = {}, {}
    for fremd, karte in POLYHAVEN_KARTEN.items():
        try:
            info = api[fremd]["1k"]["jpg"]
        except (KeyError, TypeError):
            continue
        name = f"{eintrag['id']}_1k_{karte}.jpg"
        dateien[name] = (info["url"], info.get("md5"))
        karten[karte] = name
    if "Color" not in karten:
        raise NetzFehler(f"Poly Haven nennt für {eintrag['id']!r} keine Farbkarte in 1k.")
    return {"dateien": dateien, "karten": karten}


def _hole_paket(name: str, wurzel: Path, oeffner) -> tuple[Path, int]:
    """Das Zip eines Pakets — aus dem Speicher oder geladen und gegen sha256 geprüft."""
    paket = PAKETE[name]
    ziel = wurzel / "_pakete" / f"{name}.zip"
    if ziel.is_file() and hashlib.sha256(ziel.read_bytes()).hexdigest() == paket["sha256"]:
        return ziel, 0
    daten = oeffner(paket["url"])
    pruef = hashlib.sha256(daten).hexdigest()
    if pruef != paket["sha256"]:
        raise NetzFehler(
            f"Das Paket {name!r} kam mit einer anderen Prüfsumme an ({pruef[:12]}… statt "
            f"{paket['sha256'][:12]}…). Die Quelle hat die Datei geändert — sie wird nicht "
            f"genommen, bis jemand sie neu prüft und die Prüfsumme nachträgt.")
    _schreibe(ziel, daten)
    return ziel, len(daten)


def _aus_paket(eintrag, wurzel: Path, oeffner) -> dict:
    zip_pfad, geladen = _hole_paket(eintrag["paket"], wurzel, oeffner)
    basis = _asset_ordner(wurzel, eintrag)
    paket = PAKETE[eintrag["paket"]]
    with zipfile.ZipFile(zip_pfad) as z:
        namen = z.namelist()
        if eintrag["art"] == "modell":
            # Die glb und die Texturen neben ihr (Kenney: «Textures/colormap.png»).
            ordner_im_zip = eintrag["datei"].rsplit("/", 1)[0] + "/"
            wahl = [eintrag["datei"]] + [n for n in namen if n.startswith(ordner_im_zip + "Textures/")
                                          and not n.endswith("/")]
        else:
            wahl = [n for n in namen if re.search(r"_(Color|Roughness|NormalGL|Displacement)\.jpg$", n)]
        if paket.get("lizenz_datei") and paket["lizenz_datei"] in namen:
            wahl.append(paket["lizenz_datei"])
        if not wahl or (eintrag["art"] == "modell" and eintrag["datei"] not in namen):
            raise NetzFehler(f"Im Paket {eintrag['paket']!r} fehlt, was {eintrag['id']!r} braucht.")
        dateien = []
        for n in wahl:
            rel = _sicherer_teilpfad(n[len(ordner_im_zip):] if eintrag["art"] == "modell"
                                     and n.startswith(ordner_im_zip) else Path(n).name)
            _schreibe(basis / rel, z.read(n))
            dateien.append(str(rel))
    antwort = {"dateien": dateien, "geladen_bytes": geladen}
    if eintrag["art"] == "modell":
        antwort["haupt"] = eintrag["datei"].rsplit("/", 1)[1]
    else:
        antwort["karten"] = {m.group(1): d for d in dateien
                             for m in [re.search(r"_(Color|Roughness|NormalGL|Displacement)\.jpg$", d)]
                             if m}
    return antwort


def hole_asset(kennung: str, *, wurzel=None, oeffner=None, umgebung=None,
               zeit=time.time) -> dict:
    """Ein Asset in den Zwischenspeicher holen — oder es dort finden.

    Returns:
        ``{id, kategorie, quelle, lizenz, seite, ordner, haupt?, karten?, dateien,
        geladen_bytes, aus_speicher}``. ``geladen_bytes`` ist 0, wenn alles schon dalag —
        dann ging kein Byte über das Netz (ohne Netz funktioniert es so).

    Raises:
        LizenzFehler: nicht CC0 (vor jedem Laden).
        GesperrtFehler: der Schalter ist aus und das Asset liegt nicht schon im Speicher.
        NetzFehler: Laden ging nicht — mit Satz.
        UmfeldFehler: kein Zwischenspeicher eingestellt.
    """
    eintrag = asset(kennung)
    pruefe_lizenz(eintrag)
    wurzel = Path(wurzel) if wurzel is not None else ordner(umgebung)
    if wurzel is None:
        raise UmfeldFehler(f"Der Zwischenspeicher des Umfelds ist nicht eingestellt "
                           f"({ORDNER_ENV}). Ohne ihn wird nichts geladen.")
    vorhanden = im_speicher(kennung, wurzel=wurzel)
    if vorhanden is not None:
        return dict(vorhanden, geladen_bytes=0, aus_speicher=True)
    if not freigeschaltet(umgebung):
        raise GesperrtFehler(satz_gesperrt())
    oeffner = oeffner or _standard_oeffner
    basis = _asset_ordner(wurzel, eintrag)
    try:
        if eintrag.get("paket"):
            teil = _aus_paket(eintrag, wurzel, oeffner)
            geladen = teil["geladen_bytes"]
        else:
            teil = (_polyhaven_modell if eintrag["art"] == "modell" else _polyhaven_textur)(
                eintrag, oeffner)
            geladen = 0
            for rel, (url, md5) in teil["dateien"].items():
                daten = oeffner(url)
                if md5 and hashlib.md5(daten).hexdigest() != md5:      # noqa: S324 — Prüfsumme der Quelle
                    raise NetzFehler(f"{eintrag['id']}: {rel} kam mit falscher Prüfsumme an.")
                _schreibe(basis / rel, daten)
                geladen += len(daten)
            teil["dateien"] = list(teil["dateien"])
    except UmfeldFehler:
        raise
    except Exception as e:                                       # noqa: BLE001 — Netz, Zip, JSON
        raise NetzFehler(f"{eintrag['id']} von {QUELLEN[eintrag['quelle']]['name']} nicht "
                         f"geladen: {type(e).__name__}: {e}") from e
    herkunft = {"id": eintrag["id"], "kategorie": eintrag["kategorie"],
                "quelle": eintrag["quelle"], "quelle_name": QUELLEN[eintrag["quelle"]]["name"],
                "lizenz": eintrag["lizenz"], "seite": eintrag["seite"],
                "art": eintrag["art"], "dateien": teil["dateien"],
                "haupt": teil.get("haupt"), "karten": teil.get("karten"),
                "paket": eintrag.get("paket"),
                "sha256_paket": PAKETE[eintrag["paket"]]["sha256"] if eintrag.get("paket") else None,
                "geladen_am": int(zeit())}
    _schreibe(basis / HERKUNFT_DATEI,
              json.dumps(herkunft, ensure_ascii=False, indent=1).encode("utf-8"))
    return dict(herkunft, ordner=str(basis), geladen_bytes=geladen, aus_speicher=False)


def hole_plan(plan: dict, *, wurzel=None, oeffner=None, umgebung=None) -> dict:
    """Alles holen, was ein Plan braucht — jedes Asset einmal; Fehler je Asset als Satz.

    Returns:
        ``{assets: {id: hole_asset(...)}, fehlend: {id: satz}, geladen_bytes, saetze}``.
        Ein Asset, das fehlt, fällt aus dem Bild — die übrigen bleiben. Nie ein Absturz.
    """
    benoetigt = list(dict.fromkeys(
        [p["asset"] for p in plan.get("platzierungen") or ()]
        + [b["asset"] for b in (plan.get("strasse"), plan.get("wiese"))
           if b and b.get("asset")]))
    geholt, fehlend, geladen = {}, {}, 0
    for kennung in benoetigt:
        try:
            ergebnis = hole_asset(kennung, wurzel=wurzel, oeffner=oeffner, umgebung=umgebung)
        except UmfeldFehler as e:
            fehlend[kennung] = str(e)
            continue
        geholt[kennung] = ergebnis
        geladen += int(ergebnis.get("geladen_bytes") or 0)
    saetze = []
    if geladen:
        quellen = sorted({QUELLEN[asset(k)["quelle"]]["name"] for k, g in geholt.items()
                          if g.get("geladen_bytes")})
        saetze.append(f"Geladen: {round(geladen / 1e6, 1)} MB von {', '.join(quellen)} — "
                      f"alles CC0 (gemeinfrei), im Zwischenspeicher am Heim-PC.")
    if geholt and not geladen:
        saetze.append("Alle Modelle lagen schon im Zwischenspeicher — nichts geladen.")
    for kennung, satz in fehlend.items():
        saetze.append(f"Ohne {asset(kennung)['label']} ({kennung}): {satz}")
    return {"assets": geholt, "fehlend": fehlend, "geladen_bytes": geladen, "saetze": saetze}


# ============================================================ Geometrie (rein rechnend)

def _abstand_box(x: float, y: float, box) -> float:
    (x0, y0), (x1, y1) = box
    dx = max(x0 - x, 0.0, x - x1)
    dy = max(y0 - y, 0.0, y - y1)
    return math.hypot(dx, dy)


def _konvexe_huelle(punkte):
    pts = sorted(set((round(p[0], 9), round(p[1], 9)) for p in punkte))
    if len(pts) <= 2:
        return pts

    def kreuz(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    unten, oben = [], []
    for p in pts:
        while len(unten) >= 2 and kreuz(unten[-2], unten[-1], p) <= 0:
            unten.pop()
        unten.append(p)
    for p in reversed(pts):
        while len(oben) >= 2 and kreuz(oben[-2], oben[-1], p) <= 0:
            oben.pop()
        oben.append(p)
    return unten[:-1] + oben[:-1]


def _in_polygon(x, y, poly) -> bool:
    innen = False
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / ((y1 - y0) or 1e-12) + x0:
            innen = not innen
    return innen


def _abstand_strecke(x, y, a, b) -> float:
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    laenge2 = dx * dx + dy * dy
    t = 0.0 if laenge2 == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / laenge2))
    return math.hypot(x - (ax + t * dx), y - (ay + t * dy))


def _abstand_polygon(x, y, poly) -> float:
    """0 im Polygon, sonst der Abstand zum Rand."""
    if len(poly) >= 3 and _in_polygon(x, y, poly):
        return 0.0
    return min(_abstand_strecke(x, y, poly[i], poly[(i + 1) % len(poly)])
               for i in range(len(poly)))


def sichtkegel(auge, haupt_box) -> list[tuple[float, float]]:
    """Der Kegel einer Kamera auf das Haus im Grundriss: Hülle aus Auge und Hausecken."""
    (x0, y0), (x1, y1) = haupt_box
    return _konvexe_huelle([(auge[0], auge[1]), (x0, y0), (x1, y0), (x1, y1), (x0, y1)])


class Gelaende:
    """Das Gelände im Grundriss: wo es ist und wie hoch — aus Dreiecken oder aus Boxen.

    ``dreiecke``: ``[((x,y,z),(x,y,z),(x,y,z)), …]`` in Weltkoordinaten (Z oben). Ohne Dreiecke
    gilt die Oberkante der Boxen (eine flache Platte ist damit richtig, ein Hang nicht — dann
    stellt Blender die Stücke mit einem Strahl nach unten auf die Fläche).
    """

    def __init__(self, boxen, dreiecke=None):
        self.boxen = [((float(lo[0]), float(lo[1]), float(lo[2])),
                       (float(hi[0]), float(hi[1]), float(hi[2]))) for lo, hi in boxen]
        self.dreiecke = list(dreiecke or ())
        self.aus_dreiecken = bool(self.dreiecke)
        self._raster = None
        if self.dreiecke:
            self._raster_bauen()

    @property
    def leer(self) -> bool:
        return not self.boxen

    def ausdehnung(self):
        lo = [min(b[0][i] for b in self.boxen) for i in range(3)]
        hi = [max(b[1][i] for b in self.boxen) for i in range(3)]
        return lo, hi

    def _raster_bauen(self):
        lo, hi = self.ausdehnung()
        n = max(1, int(math.sqrt(len(self.dreiecke))))
        self._zelle = max((hi[0] - lo[0]) / n, (hi[1] - lo[1]) / n, 0.5)
        self._ursprung = (lo[0], lo[1])
        raster: dict = {}
        for idx, (a, b, c) in enumerate(self.dreiecke):
            xs, ys = (a[0], b[0], c[0]), (a[1], b[1], c[1])
            i0, i1 = self._zellnr(min(xs), 0), self._zellnr(max(xs), 0)
            j0, j1 = self._zellnr(min(ys), 1), self._zellnr(max(ys), 1)
            for i in range(i0, i1 + 1):
                for j in range(j0, j1 + 1):
                    raster.setdefault((i, j), []).append(idx)
        self._raster = raster

    def _zellnr(self, wert, achse):
        return int(math.floor((wert - self._ursprung[achse]) / self._zelle))

    def hoehe(self, x: float, y: float):
        """Die Geländehöhe bei (x, y) — ``None`` neben dem Gelände."""
        if self._raster is not None:
            beste = None
            for idx in self._raster.get((self._zellnr(x, 0), self._zellnr(y, 1)), ()):
                a, b, c = self.dreiecke[idx]
                d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
                if abs(d) < 1e-12:
                    continue
                l1 = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (y - c[1])) / d
                l2 = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / d
                l3 = 1.0 - l1 - l2
                if min(l1, l2, l3) >= -1e-9:
                    z = l1 * a[2] + l2 * b[2] + l3 * c[2]
                    beste = z if beste is None else max(beste, z)
            return beste
        oben = [b[1][2] for b in self.boxen
                if b[0][0] <= x <= b[1][0] and b[0][1] <= y <= b[1][1]]
        return max(oben) if oben else None


def _box2(box):
    lo, hi = box
    return ((float(lo[0]), float(lo[1])), (float(hi[0]), float(hi[1])))


def _anzahl_ziel(kategorie, dichte, flaeche, anzahl, strasse_laenge=None):
    if anzahl and kategorie in anzahl:
        return max(0, min(int(anzahl[kategorie]), ANZAHL_HOECHSTENS))
    if kategorie == "autos":
        n = DICHTE_AUTOS[dichte]
        if strasse_laenge is not None:
            n = min(n, max(0, int(strasse_laenge // AUTO_ABSTAND_M)))
        return n
    n = int(round(flaeche / DICHTE_FLAECHE_M2[kategorie][dichte]))
    return max(1 if flaeche > 0 else 0, min(n, HOECHSTENS[kategorie]))


def _auf_seite(seite, lo, hi, gel_lo, gel_hi):
    """Abstand von der Hausseite bis zum Geländerand auf dieser Seite."""
    return {"s": lo[1] - gel_lo[1], "n": gel_hi[1] - hi[1],
            "w": lo[0] - gel_lo[0], "e": gel_hi[0] - hi[0]}[seite]


SEITEN = {"s": (0.0, -1.0), "n": (0.0, 1.0), "w": (-1.0, 0.0), "e": (1.0, 0.0)}
SEITE_WORT = {"s": "Südseite", "n": "Nordseite", "w": "Westseite", "e": "Ostseite"}


def _strasse_planen(haupt, gelaende_lo, gelaende_hi, kameras, hindernisse):
    """Ein Streifen am Geländerand auf der Seite der ersten Kamera — oder ``(None, satz)``."""
    (x0, y0), (x1, y1) = haupt
    mitte = ((x0 + x1) / 2, (y0 + y1) / 2)
    richtung = (0.0, -1.0)
    if kameras:
        auge = kameras[0]["auge"]
        richtung = (auge[0] - mitte[0], auge[1] - mitte[1])
    reihenfolge = sorted(SEITEN, key=lambda s: -(SEITEN[s][0] * richtung[0]
                                                  + SEITEN[s][1] * richtung[1]))
    for seite in reihenfolge:
        frei = _auf_seite(seite, (x0, y0), (x1, y1), gelaende_lo, gelaende_hi)
        breite = min(STRASSE_BREITE_M, frei - ABSTAND_HAUS_M - TROTTOIR_M - 0.3)
        if breite < STRASSE_BREITE_MIN_M:
            continue
        rand = 0.3
        if seite == "s":
            ecken = ((gelaende_lo[0], gelaende_lo[1] + rand),
                     (gelaende_hi[0], gelaende_lo[1] + rand + breite))
        elif seite == "n":
            ecken = ((gelaende_lo[0], gelaende_hi[1] - rand - breite),
                     (gelaende_hi[0], gelaende_hi[1] - rand))
        elif seite == "w":
            ecken = ((gelaende_lo[0] + rand, gelaende_lo[1]),
                     (gelaende_lo[0] + rand + breite, gelaende_hi[1]))
        else:
            ecken = ((gelaende_hi[0] - rand - breite, gelaende_lo[1]),
                     (gelaende_hi[0] - rand, gelaende_hi[1]))
        if any(_ueberlappt(ecken, h, rand=ABSTAND_HAUS_M) for h in hindernisse):
            continue
        achse = "x" if seite in ("s", "n") else "y"
        laenge = (ecken[1][0] - ecken[0][0]) if achse == "x" else (ecken[1][1] - ecken[0][1])
        return {"box": [list(ecken[0]), list(ecken[1])], "seite": seite, "achse": achse,
                "breite_m": round(breite, 2), "laenge_m": round(laenge, 2),
                "aus_modell": None}, None
    return None, ("Keine Strasse: Zwischen Haus und Geländerand ist auf keiner Seite Platz für "
                  f"einen Streifen von mindestens {STRASSE_BREITE_MIN_M:g} m (dazu "
                  f"{ABSTAND_HAUS_M:g} m Abstand und ein Trottoir).")


def _ueberlappt(a, b, rand=0.0) -> bool:
    (ax0, ay0), (ax1, ay1) = a
    (bx0, by0), (bx1, by1) = b
    return not (ax1 + rand <= bx0 or bx1 + rand <= ax0 or ay1 + rand <= by0 or by1 + rand <= ay0)


def plane(*, gelaende: Gelaende, bauwerk_boxen, haupt_box, kameras=(), kategorien=(),
          dichte: str = DICHTE_VORGABE, seed: int = 0, anzahl=None, umfeld_boxen=(),
          strassen_boxen=(), assets_wahl=None) -> dict:
    """Der Platzierungsplan — rein rechnend, mit ``seed`` Stück für Stück wiederholbar.

    Args:
        gelaende: :class:`Gelaende` (Weltkoordinaten, Z oben).
        bauwerk_boxen: Grundriss-Boxen aller Bauteile ``[((x0,y0),(x1,y1)) | (lo3, hi3), …]`` —
            nichts kommt hinein oder näher als :data:`ABSTAND_HAUS_M`.
        haupt_box: die Box des Hauses, auf die die Kameras schauen (Sichtkegel).
        kameras: ``[{kuerzel, auge: [x,y,z]}, …]`` — die erste bestimmt die Strassenseite.
        umfeld_boxen: was schon als Umfeld im Modell steht (Bäume) — wird nicht überstellt.
        strassen_boxen: Strassen, die das Modell schon trägt — dann keine neue.
        assets_wahl: ``{kategorie: [asset_id, …]}`` — sonst die Vorgaben des Katalogs.

    Returns:
        ``{schema, seed, dichte, kategorien, platzierungen, strasse, wiese, zaehlung, ziel,
        sichtkegel, saetze}``.
    """
    if dichte not in DICHTEN:
        raise UmfeldFehler(f"Dichte {dichte!r} unbekannt ({', '.join(DICHTEN)}).")
    kategorien = [k for k in KATEGORIEN if k in set(kategorien)]
    wahl = {}
    for kat in kategorien:
        ids = list((assets_wahl or {}).get(kat) or [e["id"] for e in vorgaben_der_kategorie(kat)])
        for kennung in ids:
            eintrag = asset(kennung)
            pruefe_lizenz(eintrag)
            if eintrag["kategorie"] != kat:
                raise UmfeldFehler(f"{kennung!r} gehört nicht zu {kat!r}.")
        wahl[kat] = ids
    plan = {"schema": PLAN_SCHEMA, "seed": int(seed), "dichte": dichte,
            "kategorien": kategorien, "platzierungen": [], "strasse": None, "wiese": None,
            "zaehlung": {}, "ziel": {}, "sichtkegel": [], "saetze": [],
            "abstand_haus_m": ABSTAND_HAUS_M}
    if not kategorien:
        plan["saetze"].append("Keine Kategorie gewählt — das Umfeld bleibt, wie es ist.")
        return plan
    if gelaende is None or gelaende.leer:
        plan["saetze"].append(
            "Das Modell hat kein Gelände — ohne Boden stellt Visbox keine Bäume, Büsche oder "
            "Autos in die Luft. Ein Gelände im Modell (Rolle «Boden» oder Name «Gelände») "
            "macht das Umfeld möglich.")
        return plan

    rng = random.Random(int(seed))
    boxen = [_box2(b) for b in bauwerk_boxen]
    haupt = _box2(haupt_box)
    umfeld = [_box2(b) for b in umfeld_boxen]
    gel_lo, gel_hi = gelaende.ausdehnung()
    kegel = [{"kuerzel": k.get("kuerzel"), "polygon": [list(p) for p in sichtkegel(k["auge"], haupt)]}
             for k in kameras if k.get("auge") is not None]
    plan["sichtkegel"] = kegel

    def im_kegel(x, y, r):
        return any(_abstand_polygon(x, y, [tuple(p) for p in k["polygon"]]) < r + SICHT_RAND_M
                   for k in kegel)

    # DIE STRASSE (vor allem anderen: die Autos brauchen sie, und Bäume stehen nicht auf ihr).
    strasse = None
    if "strasse" in kategorien or "autos" in kategorien:
        if strassen_boxen:
            sb = max((_box2(b) for b in strassen_boxen),
                     key=lambda b: (b[1][0] - b[0][0]) * (b[1][1] - b[0][1]))
            achse = "x" if (sb[1][0] - sb[0][0]) >= (sb[1][1] - sb[0][1]) else "y"
            laenge = (sb[1][0] - sb[0][0]) if achse == "x" else (sb[1][1] - sb[0][1])
            breite = (sb[1][1] - sb[0][1]) if achse == "x" else (sb[1][0] - sb[0][0])
            strasse = {"box": [list(sb[0]), list(sb[1])], "seite": None, "achse": achse,
                       "breite_m": round(breite, 2), "laenge_m": round(laenge, 2),
                       "aus_modell": True}
            plan["saetze"].append("Die Strasse des Modells genommen — keine neue gelegt.")
        else:
            strasse, satz = _strasse_planen(haupt, gel_lo, gel_hi, kameras, boxen)
            if satz:
                plan["saetze"].append(satz)
        if strasse is not None and "strasse" in kategorien and not strasse["aus_modell"]:
            strasse["asset"] = wahl["strasse"][0]
        if strasse is not None and ("strasse" in kategorien or strasse["aus_modell"]):
            plan["strasse"] = strasse
        elif strasse is not None:
            # Autos ohne bestellte Strasse: sie stehen am Rand, wo eine Strasse waere — die
            # Fläche bleibt Gelände.
            plan["strasse"] = None
    if "wiese" in kategorien:
        plan["wiese"] = {"asset": wahl["wiese"][0],
                         "massstab_m": asset(wahl["wiese"][0]).get("massstab_m", 2.0)}

    belegt: list[tuple[float, float, float]] = []      # (x, y, r)
    strassen_box = _box2(strasse["box"]) if strasse is not None else None
    # Die freie Fläche: Gelände ohne Haus (seine Box, nicht die Summe der Bauteile — Wände
    # im Haus zählten sonst mehrfach) und ohne Strasse.
    flaeche = max(0.0, (gel_hi[0] - gel_lo[0]) * (gel_hi[1] - gel_lo[1])
                  - (haupt[1][0] - haupt[0][0]) * (haupt[1][1] - haupt[0][1])
                  - ((strasse["breite_m"] * strasse["laenge_m"]) if strasse else 0.0))

    def frei(x, y, r, *, auf_strasse=False):
        if not (gel_lo[0] + r * 0.5 <= x <= gel_hi[0] - r * 0.5
                and gel_lo[1] + r * 0.5 <= y <= gel_hi[1] - r * 0.5):
            return False
        if any(_abstand_box(x, y, b) < ABSTAND_HAUS_M + r for b in boxen):
            return False
        if any(_abstand_box(x, y, b) < r * 0.6 for b in umfeld):
            return False
        if im_kegel(x, y, r):
            return False
        if not auf_strasse and strassen_box is not None and \
                _abstand_box(x, y, strassen_box) < r * 0.5 + 0.5:
            return False
        if any(math.hypot(x - bx, y - by) < (r + br) * 0.85 for bx, by, br in belegt):
            return False
        return True

    nr = 0

    def stelle(kat, kennung, x, y, z, drehung, masse, r):
        nonlocal nr
        eintrag = {"nr": nr, "kategorie": kat, "asset": kennung, "x": round(x, 3),
                   "y": round(y, 3), "z": round(z, 3), "drehung_grad": round(drehung, 1),
                   "radius_m": round(r, 2), "variante": rng.randrange(0, 8), **masse}
        plan["platzierungen"].append(eintrag)
        belegt.append((x, y, r))
        nr += 1

    # DIE AUTOS — auf der Strasse (oder dem Streifen, wo sie läge), längs ihrer Achse.
    if "autos" in kategorien:
        ziel = _anzahl_ziel("autos", dichte, flaeche, anzahl,
                            strasse["laenge_m"] if strasse else None)
        plan["ziel"]["autos"] = ziel
        if strasse is None:
            if ziel:
                plan["saetze"].append("Keine Autos: Es gibt keine Strasse, auf der sie stehen "
                                      "könnten.")
        else:
            (sx0, sy0), (sx1, sy1) = _box2(strasse["box"])
            gestellt = 0
            for _ in range(ziel * VERSUCHE_JE_STUECK):
                if gestellt >= ziel:
                    break
                kennung = rng.choice(wahl["autos"])
                e = asset(kennung)
                laenge = rng.uniform(*e["laenge_m"])
                r = laenge / 2.0
                spur = rng.choice((-1, 1))
                if strasse["achse"] == "x":
                    x = rng.uniform(sx0 + r, sx1 - r)
                    y = (sy0 + sy1) / 2 + spur * strasse["breite_m"] / 4
                    drehung = 90.0 if spur < 0 else 270.0
                else:
                    y = rng.uniform(sy0 + r, sy1 - r)
                    x = (sx0 + sx1) / 2 + spur * strasse["breite_m"] / 4
                    drehung = 0.0 if spur > 0 else 180.0
                z = gelaende.hoehe(x, y)
                if z is None or not frei(x, y, min(r, 1.2), auf_strasse=True):
                    continue
                if any(p["kategorie"] == "autos" and math.hypot(p["x"] - x, p["y"] - y)
                       < AUTO_ABSTAND_M for p in plan["platzierungen"]):
                    continue
                stelle("autos", kennung, x, y, z, drehung, {"laenge_m": round(laenge, 2)}, r)
                gestellt += 1

    # DIE BÄUME, DANN DIE BÜSCHE — gestreut auf dem Gelände, in seiner Höhe.
    for kat in ("baeume", "buesche"):
        if kat not in kategorien:
            continue
        ziel = _anzahl_ziel(kat, dichte, flaeche, anzahl)
        plan["ziel"][kat] = ziel
        gestellt = 0
        for _ in range(ziel * VERSUCHE_JE_STUECK):
            if gestellt >= ziel:
                break
            kennung = rng.choice(wahl[kat])
            e = asset(kennung)
            hoehe = rng.uniform(*e["hoehe_m"])
            r = e["radius_m"] * hoehe / e["hoehe_m"][1]
            x = rng.uniform(gel_lo[0], gel_hi[0])
            y = rng.uniform(gel_lo[1], gel_hi[1])
            if not frei(x, y, r):
                continue
            z = gelaende.hoehe(x, y)
            if z is None:
                continue
            stelle(kat, kennung, x, y, z, rng.uniform(0.0, 360.0),
                   {"hoehe_m": round(hoehe, 2)}, r)
            gestellt += 1

    zaehlung = {k: sum(1 for p in plan["platzierungen"] if p["kategorie"] == k)
                for k in ("baeume", "buesche", "autos") if k in kategorien}
    plan["zaehlung"] = zaehlung
    plan["saetze"][:0] = _plan_saetze(plan, kameras)
    return plan


def _mehrzahl(n, eins, viele):
    return f"{n} {eins if n == 1 else viele}"


def _plan_saetze(plan, kameras) -> list[str]:
    z = plan["zaehlung"]
    teile = []
    if "baeume" in z:
        teile.append(_mehrzahl(z["baeume"], "Baum", "Bäume"))
    if "buesche" in z:
        teile.append(_mehrzahl(z["buesche"], "Busch", "Büsche"))
    if "autos" in z:
        teile.append(_mehrzahl(z["autos"], "Auto", "Autos"))
    saetze = []
    if teile:
        saetze.append(("Gestellt: " + ", ".join(teile[:-1]) + (" und " if len(teile) > 1 else "")
                       + teile[-1] + "."))
    s = plan.get("strasse")
    if s and not s.get("aus_modell"):
        saetze.append(f"Eine Strasse von {s['laenge_m']:.0f} m entlang der "
                      f"{SEITE_WORT.get(s['seite'], 'Seite')}, {s['breite_m']:.1f} m breit.")
    if plan.get("wiese"):
        saetze.append("Das Gelände wird Wiese.")
    for kat, ziel in plan["ziel"].items():
        if z.get(kat, 0) >= ziel:
            continue
        if kat == "autos":
            saetze.append(f"Nur {z.get(kat, 0)} von {ziel} Autos fanden Platz — der Rest der "
                          f"Strasse liegt im Blick der Kameras auf das Haus.")
        else:
            saetze.append(f"Nur {z.get(kat, 0)} von {ziel} {KATEGORIE_LABEL[kat]} fanden Platz — "
                          f"um das Haus ist das Gelände knapp.")
    if kameras:
        namen = ", ".join(str(k.get("kuerzel")) for k in kameras if k.get("kuerzel"))
        saetze.append(f"Freigehalten: der Blick der Kamera{'s' if len(kameras) > 1 else ''} "
                      f"{namen} auf das Haus und {ABSTAND_HAUS_M:g} m rund um das Haus.")
    return saetze


# ============================================================ aus einer glb

def _glb_teile(pfad):
    daten = Path(pfad).read_bytes()
    if len(daten) < 20 or struct.unpack_from("<I", daten, 0)[0] != 0x46546C67:
        return json.loads(daten.decode("utf-8")), None
    laenge = struct.unpack_from("<I", daten, 12)[0]
    js = json.loads(daten[20:20 + laenge].decode("utf-8"))
    bin_start = 20 + laenge
    binaer = None
    if len(daten) >= bin_start + 8:
        bin_laenge = struct.unpack_from("<I", daten, bin_start)[0]
        binaer = daten[bin_start + 8:bin_start + 8 + bin_laenge]
    return js, binaer


_KOMPONENTEN = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2),
                5125: ("I", 4), 5126: ("f", 4)}
_ANZAHL = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def _accessor(js, binaer, index):
    acc = js["accessors"][index]
    if "sparse" in acc or "bufferView" not in acc:
        raise ValueError("sparse oder ohne bufferView")
    sicht = js["bufferViews"][acc["bufferView"]]
    if sicht.get("buffer", 0) != 0 or binaer is None:
        raise ValueError("nicht im BIN-Block")
    fmt, groesse = _KOMPONENTEN[acc["componentType"]]
    n = _ANZAHL[acc["type"]]
    schritt = sicht.get("byteStride") or groesse * n
    start = sicht.get("byteOffset", 0) + acc.get("byteOffset", 0)
    werte = []
    for i in range(acc["count"]):
        werte.append(struct.unpack_from(f"<{n}{fmt}", binaer, start + i * schritt))
    return werte


def _dreiecke(js, binaer, namen, hoechstens=DREIECKE_HOECHSTENS):
    """Die Dreiecke der Knoten ``namen`` in Weltkoordinaten (Z oben), oder ``None``."""
    from .glbbox import _EINHEIT, _knotenmatrix, _mal
    knoten = js.get("nodes") or []
    szenen = js.get("scenes") or []
    nummer = js.get("scene", 0)
    wurzeln = (list(szenen[nummer].get("nodes") or []) if 0 <= nummer < len(szenen)
               else list(range(len(knoten))))
    stapel = [(i, _EINHEIT) for i in reversed(wurzeln)]
    gesehen, dreiecke = set(), []
    while stapel:
        index, eltern = stapel.pop()
        if not isinstance(index, int) or not 0 <= index < len(knoten) or index in gesehen:
            continue
        gesehen.add(index)
        n = knoten[index]
        welt = _mal(eltern, _knotenmatrix(n))
        if "mesh" in n and str(n.get("name") or "") in namen:
            for prim in js["meshes"][n["mesh"]].get("primitives") or ():
                if prim.get("mode", 4) != 4 or "POSITION" not in prim.get("attributes", {}):
                    continue
                if "KHR_draco_mesh_compression" in (prim.get("extensions") or {}):
                    return None
                pos = _accessor(js, binaer, prim["attributes"]["POSITION"])
                idx = ([i[0] for i in _accessor(js, binaer, prim["indices"])]
                       if "indices" in prim else list(range(len(pos))))
                welt_pos = []
                for p in pos:
                    v = [welt[i][0] * p[0] + welt[i][1] * p[1] + welt[i][2] * p[2] + welt[i][3]
                         for i in range(3)]
                    welt_pos.append((v[0], -v[2], v[1]))       # glTF Y-oben → Z-oben
                for k in range(0, len(idx) - 2, 3):
                    dreiecke.append((welt_pos[idx[k]], welt_pos[idx[k + 1]], welt_pos[idx[k + 2]]))
                    if len(dreiecke) > hoechstens:
                        return None
        for kind in reversed(n.get("children") or []):
            stapel.append((kind, welt))
    return dreiecke


def _wortweise(name: str) -> list[str]:
    return [w for w in re.split(r"[\s_\-.,;:/\\()\[\]]+", str(name or "").lower()) if w]


def lies_glb_umfeld(pfad, *, up_axis: str = "Y") -> dict:
    """Was der Plan aus einer glb braucht: Gelände, Bauwerk, Hausbox, Umfeld, Strassen.

    Gelände nach denselben Regeln wie die Maske und die Box (``glbbox.bauwerksbox``:
    Namensregel und Formprüfung) und nach der Rolle der Datei (``extras.role``,
    ``kosmo_szene.gelaende_in_glb``). Umfeld nach :func:`aiimaging.maske.ist_umfeld`.
    """
    from . import glbbox, kosmo_szene
    from .maske import ist_umfeld
    js, binaer = _glb_teile(pfad)
    alle = glbbox.knotenboxen(js)["knoten"]
    box = glbbox.bauwerksbox(pfad, up_axis=up_axis)
    rolle = kosmo_szene.gelaende_in_glb(pfad) or {}
    gelaende_namen = set(box.get("gelaende_namen") or ()) | set(rolle.get("knoten") or ())
    welt = {name: glbbox.nach_welt(lo, hi, up_axis=up_axis) for name, lo, hi in alle}
    gel, bau, umfeld, strassen = [], [], [], []
    for name, _, _ in alle:
        if name in gelaende_namen:
            gel.append(name)
        elif any(w in STRASSEN_WOERTER for w in _wortweise(name)):
            strassen.append(name)
        elif ist_umfeld(name):
            umfeld.append(name)
        else:
            bau.append(name)
    dreiecke, hoehe_aus = None, "keine"
    if gel:
        try:
            dreiecke = _dreiecke(js, binaer, set(gel))
        except (KeyError, ValueError, IndexError, struct.error):
            dreiecke = None
        hoehe_aus = "dreiecke" if dreiecke else "box"
    gelaende = Gelaende([welt[n] for n in gel], dreiecke)
    haupt = box.get("bbox_bauwerk")
    return {"gelaende": gelaende, "gelaende_namen": sorted(gel),
            "bauwerk_boxen": [welt[n] for n in bau], "haupt_box": haupt,
            "umfeld_boxen": [welt[n] for n in umfeld], "umfeld_namen": sorted(umfeld),
            "strassen_boxen": [welt[n] for n in strassen], "strassen_namen": sorted(strassen),
            "hoehe_aus": hoehe_aus}


def plane_fuer_glb(pfad, *, wunsch: dict, kameras=None, richtungen=("s", "sSE", "nNW"),
                   up_axis: str = "Y", assets_wahl=None) -> dict:
    """:func:`plane` für eine glb — Gelände, Bauwerk und (ohne ``kameras``) die Auto-Kameras.

    ``kameras`` ``[{kuerzel, auge}]`` in Weltkoordinaten; ohne sie rechnet
    ``kameras.kamerasatz`` die Standpunkte der ``richtungen`` auf der Hausbox — dieselben, die
    der Runner später stellt.
    """
    gelesen = lies_glb_umfeld(pfad, up_axis=up_axis)
    haupt = gelesen["haupt_box"]
    if haupt is None:
        plan = plane(gelaende=None, bauwerk_boxen=(), haupt_box=((0, 0), (0, 0)),
                     kategorien=wunsch.get("kategorien") or (), dichte=wunsch.get("dichte",
                     DICHTE_VORGABE), seed=wunsch.get("seed", 0))
        plan["saetze"] = ["Kein Haus in der Datei erkannt — ohne Haus gibt es kein Umfeld."]
        return plan
    if kameras is None:
        from . import kameras as _kameras
        satz = _kameras.kamerasatz(haupt, kuerzel=list(richtungen))
        kameras = [{"kuerzel": k["kuerzel"], "auge": k["auge"]} for k in satz["kameras"]]
    plan = plane(gelaende=gelesen["gelaende"], bauwerk_boxen=gelesen["bauwerk_boxen"],
                 haupt_box=haupt, kameras=kameras, kategorien=wunsch.get("kategorien") or (),
                 dichte=wunsch.get("dichte", DICHTE_VORGABE), seed=wunsch.get("seed", 0),
                 anzahl=wunsch.get("anzahl"), umfeld_boxen=gelesen["umfeld_boxen"],
                 strassen_boxen=gelesen["strassen_boxen"], assets_wahl=assets_wahl)
    plan["gelaende_namen"] = gelesen["gelaende_namen"]
    plan["hoehe_aus"] = gelesen["hoehe_aus"]
    if gelesen["hoehe_aus"] == "box" and plan["platzierungen"]:
        plan["saetze"].append("Die Geländehöhe kommt aus der Box des Geländes (die Dreiecke "
                              "waren nicht lesbar) — Blender setzt jedes Stück auf die Fläche.")
    return plan


def fuer_blender(plan: dict, geholt: dict) -> dict:
    """Die Datei für den Runner: Plan und je Asset der Pfad am Heim-PC (nie ins Ergebnis)."""
    assets_aus = {}
    for kennung, g in (geholt.get("assets") or {}).items():
        basis = Path(g["ordner"])
        eintrag = asset(kennung)
        assets_aus[kennung] = {
            "kategorie": eintrag["kategorie"], "art": eintrag["art"],
            "datei": str(basis / g["haupt"]) if g.get("haupt") else None,
            "karten": {k: str(basis / v) for k, v in (g.get("karten") or {}).items()},
            "massstab_m": eintrag.get("massstab_m"),
            "materialname": material_name(eintrag["kategorie"], kennung, 0).rsplit("_", 1)[0]}
    plan_aus = dict(plan)
    plan_aus["platzierungen"] = [p for p in plan.get("platzierungen") or ()
                                 if p["asset"] in assets_aus]
    if plan_aus.get("strasse") and plan_aus["strasse"].get("asset") \
            and plan_aus["strasse"]["asset"] not in assets_aus:
        plan_aus["strasse"] = dict(plan_aus["strasse"], asset=None)
    if plan_aus.get("wiese") and plan_aus["wiese"]["asset"] not in assets_aus:
        plan_aus["wiese"] = None
    return {"schema": DATEI_SCHEMA, "plan": plan_aus, "assets": assets_aus}


def bericht_fuer_ergebnis(wunsch: dict | None, plan: dict | None, geholt: dict | None, *,
                          freigeschaltet_jetzt: bool, gestellt: dict | None = None) -> dict:
    """``angewandt.umfeld`` — was bestellt, was gestellt, was geladen, mit Lizenz und Quelle.

    Ohne Pfade (Regel 3). ``gestellt`` ist der Befund des Runners (``umfeld`` im
    Blender-Bericht), wenn eine Kamera gerechnet hat.
    """
    aus = {"bestellt": dict(wunsch or {}), "freigeschaltet": bool(freigeschaltet_jetzt),
           "saetze": []}
    if not freigeschaltet_jetzt and not (geholt or {}).get("assets"):
        aus["saetze"].append(satz_gesperrt())
    if plan is not None:
        aus["geplant"] = dict(plan.get("zaehlung") or {})
        aus["strasse"] = bool(plan.get("strasse"))
        aus["wiese"] = bool(plan.get("wiese"))
        aus["saetze"].extend(plan.get("saetze") or ())
    if geholt is not None:
        aus["assets"] = [{"id": k, "label": asset(k)["label"],
                          "quelle": QUELLEN[asset(k)["quelle"]]["name"],
                          "lizenz": asset(k)["lizenz"], "seite": asset(k)["seite"],
                          "geladen_mb": round((g.get("geladen_bytes") or 0) / 1e6, 2)}
                         for k, g in sorted((geholt.get("assets") or {}).items())]
        aus["geladen_mb"] = round((geholt.get("geladen_bytes") or 0) / 1e6, 2)
        aus["saetze"].extend(geholt.get("saetze") or ())
    if gestellt:
        aus["gestellt"] = dict(gestellt)
    return aus
