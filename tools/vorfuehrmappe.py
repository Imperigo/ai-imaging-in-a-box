#!/usr/bin/env python3
"""VORFÜHRMAPPE — vorher gerechnete Bilder für den Vorführmodus der Mac-App.

Plan v0.1.7, Strom C1; Entscheide 40 und 49. Antwortet der Heim-PC nicht, zeigt die
Mac-App von selbst Bilder, die vorher gerechnet wurden — **mit dem Prüfzeichen, das sie am
Tag des Rechnens trugen, und dem Datum daneben** (Blatt 13b). Dieses Werkzeug legt den
Ordner an, den die App dafür mitbringt:

    python3 tools/vorfuehrmappe.py --ordner PROJEKT --nach ZIEL [--titel T]
                                   [--bild NAME …] [--blick NAME=TEXT …]
    python3 tools/vorfuehrmappe.py --beispiel ZIEL [--titel T]

``--ordner`` nimmt die Bilder einer gerechneten Mappe (am Heim-PC, nach einem Lauf),
``--beispiel`` erzeugt **ohne GPU** eine kleine Mappe aus grauen Platzhaltern — für die
Proben und für die App, bis der Heim-PC die echte gerechnet hat.

Das Format (``visbox.vorfuehrmappe/v1``)
---------------------------------------
Ein Ordner mit ``vorfuehrmappe.json`` und den Bilddateien daneben, nur PNG::

    {"schema": "visbox.vorfuehrmappe/v1", "titel": …, "art": …, "platzhalter": bool,
     "gerechnet_am": "JJJJ-MM-TT" | null, "erstellt_am": "JJJJ-MM-TT", "satz": …,
     "bilder": [{"datei": …, "blick": … | null, "gerechnet_am": … | null, "satz": …,
                 "flaeche": {…}}]}

``flaeche`` ist **das Bild, wie die Fläche es zeigt** — die Felder aus
``GET /api/projekt`` (``docs/VISBOX_PROTOKOLL.md`` §4), die die App in ``Mappenbild``
liest und aus denen ``Mappenbild.pruefzeichen`` das Zeichen macht. Die App benutzt im
Vorführmodus **dieselbe Ableitung** wie live: Ein Bild trägt dort dasselbe Zeichen, weil
es aus denselben Feldern auf demselben Weg entsteht, nicht weil jemand es nachgebaut hat.

Warum dieses Werkzeug ``oberflaeche/server.py`` lädt
---------------------------------------------------
Welches Zeichen ein Bild bekommt, entscheidet ``_bild_fuer_die_flaeche`` im Server — es ist
die einzige Stelle, an der der Server etwas entscheidet, und zwar über die Anzeige. Eine
Abschrift hier liefe still auseinander; eine Auslagerung in ``src/aiimaging/`` hiesse,
den Server während des Vollbaus umzubauen, an dem zur selben Zeit der Assistent (Strom D)
arbeitet. Geladen wird darum das Modul selbst, wie es die Proben tun. Regel 4 bleibt
gewahrt: Der Server importiert nur die Standardbibliothek und :mod:`aiimaging`, kein
Fenster-Werkzeug, und es läuft dabei keiner — geladen wird eine Funktion, nicht die
Oberfläche. Und die Richtung stimmt: Das Werkzeug liest den Server, der Kern weiss von
beidem nichts.

Regel 3 — was nicht in die Mappe geht
-------------------------------------
Die Mappe geht ins App-Bündel und damit an jeden, der die App lädt. Darum:

* **Nur Dateinamen, nie Pfade.** ``herkunft`` (Prompt, Knoten, Pfade relativ zur Mappe),
  ``basis`` und ``vorhanden`` gehen nicht mit — das Zeichen braucht sie nicht.
* **Jeder Text wird abgesucht**: absolute und heimrelative Pfade, Laufwerksbuchstaben,
  der Projektordner, der Heimatordner, Benutzer- und Rechnername. Ein Fund bricht ab und
  nennt Bild und Feld — **es wird nicht still gekürzt**: *eine Säuberung, die nicht sagt,
  dass sie stattfand, ist von keiner zu unterscheiden.*
* **Die PNG-Begleitdaten werden abgestreift** (Textblöcke, Zeitstempel, Farbprofile mit
  Namen). Ein Bildprogramm schreibt dort gern Pfad, Prompt und Rechnernamen hinein.
"""
from __future__ import annotations

import argparse
import getpass
import importlib.util
import json
import re
import socket
import struct
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL / "src"))

from aiimaging import bildschreiben, projekt  # noqa: E402

SCHEMA = "visbox.vorfuehrmappe/v1"
MAPPENDATEI = "vorfuehrmappe.json"

#: Die Felder eines Bildes, wie die Fläche sie zeigt **und** die App sie liest
#: (``Mappenbild.init`` in ``ipad/Visbox.swiftpm/Kern/Pruefzeichen.swift``, ohne
#: ``vorhanden``). ``tests/test_vorfuehrmappe.py`` hält die Liste gegen beide Seiten.
FELDER_DER_FLAECHE = (
    "bild", "schicht", "zeichen", "satz", "erzeugt", "score", "schwelle", "titel",
    "entwurf", "variantengruppe", "hinweise", "skizze_nicht_angekommen", "skizze_hinweis",
    "vorher", "unterlage_hinweis", "standpunkt_vorgabe",
)

#: Was die Fläche zeigt, aber **nicht** in die Mappe geht — mit Grund:
#: ``herkunft`` trägt Prompt, Knoten und Pfade relativ zur Mappe (Regel 3), ``basis`` das
#: geerbte Urteil (für das Zeichen ohne Belang, und es trüge wieder eine Herkunft),
#: ``vorhanden`` gilt für den Projektordner und nicht für die Mappe — ob die Datei in der
#: Mappe liegt, sieht die App dort selbst nach.
NICHT_IN_DIE_MAPPE = ("herkunft", "basis", "vorhanden")

#: Ein Dateiname in der Mappe: ein Name, kein Weg.
DATEINAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,120}\.png")

#: Der Satz an jedem gerechneten Bild — er sagt, wofür das Zeichen gilt.
SATZ_GERECHNET = ("Am Heim-PC gerechnet am {datum}. Das Zeichen ist das vom Tag des "
                  "Rechnens; heute ist nichts daran neu gemessen.")

#: Der Satz an der ganzen Mappe, wenn sie aus einem Projekt kommt.
SATZ_MAPPE = ("Vorher gerechnete Bilder aus einem synthetischen Projekt (Regel 3). "
              "Jedes trägt das Zeichen vom Tag, an dem es gerechnet wurde.")

PNG_KENNUNG = b"\x89PNG\r\n\x1a\n"

#: Die PNG-Blöcke, die mitgehen. **Eine Positivliste**, wie ``server.BILDTYPEN``: Was
#: nicht hier steht — ``tEXt``, ``zTXt``, ``iTXt``, ``eXIf``, ``tIME``, ``iCCP`` (trägt
#: einen frei gewählten Namen) und jeder unbekannte Block — bleibt draussen.
PNG_BLOECKE = {b"IHDR", b"PLTE", b"tRNS", b"IDAT", b"IEND", b"gAMA", b"cHRM", b"sRGB",
               b"sBIT", b"pHYs"}


class MappenFehler(Exception):
    """Eine Mappe, die so nicht entsteht — mit einem Satz für einen Menschen."""


# ===================================================================== der Server

def _server():
    """``oberflaeche/server.py`` als Modul — warum geladen und nicht abgeschrieben, steht
    im Modulkopf."""
    pfad = WURZEL / "oberflaeche" / "server.py"
    spez = importlib.util.spec_from_file_location("vorfuehrmappe_flaeche", pfad)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


# ============================================================ Regel 3, abgesucht

#: Pfadformen, die in keinem Text der Mappe stehen dürfen.
_PFADMUSTER = (
    (re.compile(r"(?:^|[\s\"'(\[=:,;])/[^\s/]+/"), "ein absoluter Pfad"),
    (re.compile(r"~[/\\]"), "ein heimrelativer Pfad"),
    (re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]"), "ein Laufwerkspfad"),
    (re.compile(r"\\\\[^\s\\]+\\"), "ein Netzpfad"),
)


def _kennungen_der_maschine(ordner: Path | None) -> list[tuple[str, str]]:
    """Was von dieser Maschine nicht in die Mappe darf: ``[(text, was)]``."""
    gesucht: list[tuple[str, str]] = []
    if ordner is not None:
        gesucht.append((str(Path(ordner).resolve()), "der Projektordner"))
    try:
        gesucht.append((str(Path.home()), "der Heimatordner"))
    except (RuntimeError, KeyError):
        pass
    try:
        gesucht.append((getpass.getuser(), "der Benutzername"))
    except (KeyError, OSError):
        pass
    rechner = socket.gethostname()
    gesucht += [(rechner, "der Rechnername"), (rechner.split(".")[0], "der Rechnername")]
    # ZU KURZ ODER ZU ALLGEMEIN, UM ETWAS ZU VERRATEN — und zu allgemein, um ohne
    # Fehlalarm gesucht zu werden («/» als Heimatordner, «root» in einem Behaelter).
    return [(t, w) for t, w in gesucht if t and len(t) >= 3 and t not in ("/", "localhost")]


def regel3_funde(wert, kennungen=(), *, ort: str = "") -> list[str]:
    """Jeder Text in ``wert`` (rekursiv, auch Schlüssel), der einen Pfad oder eine
    Kennung dieser Maschine trägt — als Satz ``"<ort>: <was>"``. Leer heisst: nichts
    gefunden."""
    funde: list[str] = []
    if isinstance(wert, str):
        for muster, was in _PFADMUSTER:
            if muster.search(wert):
                funde.append(f"{ort or 'Text'}: {was} in {wert[:80]!r}")
        for text, was in kennungen:
            if re.search(r"(?<![A-Za-z0-9])" + re.escape(text) + r"(?![A-Za-z0-9])",
                         wert, re.I):
                funde.append(f"{ort or 'Text'}: {was}")
    elif isinstance(wert, dict):
        for k, v in wert.items():
            funde += regel3_funde(k, kennungen, ort=f"{ort}.{k}" if ort else str(k))
            funde += regel3_funde(v, kennungen, ort=f"{ort}.{k}" if ort else str(k))
    elif isinstance(wert, (list, tuple)):
        for i, v in enumerate(wert):
            funde += regel3_funde(v, kennungen, ort=f"{ort}[{i}]")
    return funde


# ================================================================= PNG ohne Beiwerk

def ohne_begleitdaten(roh: bytes) -> bytes:
    """Ein PNG, von dem nur die Blöcke aus :data:`PNG_BLOECKE` bleiben.

    Raises:
        MappenFehler: kein PNG, oder ein Block reicht über das Dateiende.
    """
    if not roh.startswith(PNG_KENNUNG):
        raise MappenFehler("Das ist kein PNG (die Kennung am Anfang fehlt).")
    aus, stelle = bytearray(PNG_KENNUNG), len(PNG_KENNUNG)
    while stelle < len(roh):
        if stelle + 12 > len(roh):
            raise MappenFehler("Das PNG bricht mitten in einem Block ab.")
        laenge = struct.unpack(">I", roh[stelle:stelle + 4])[0]
        art = roh[stelle + 4:stelle + 8]
        ende = stelle + 12 + laenge
        if ende > len(roh):
            raise MappenFehler(f"Der Block {art!r} reicht über das Dateiende.")
        if art in PNG_BLOECKE:
            aus += roh[stelle:ende]
        stelle = ende
        if art == b"IEND":
            break
    return bytes(aus)


# ============================================================== Mappe aus Projekt

def _tag(zeit) -> str | None:
    """``JJJJ-MM-TT`` aus einer Zeit des Servers, oder ``None`` — nie geraten."""
    if isinstance(zeit, str) and re.match(r"\d{4}-\d{2}-\d{2}(?:T|$)", zeit):
        return zeit[:10]
    return None


def _tag_lesbar(tag: str) -> str:
    j, m, t = tag.split("-")
    return f"{t}.{m}.{j}"


def aus_projekt(ordner, *, titel: str | None = None, bilder=None,
                blicke: dict | None = None) -> tuple[dict, dict[str, bytes], list[str]]:
    """Die Mappe aus einem gerechneten Projekt — ``(mappe, {datei: bytes}, hinweise)``.

    Die Felder je Bild kommen aus :func:`server.sicht` — **dieselbe Antwort, die die Fläche
    und die App bekommen.** ``bilder`` wählt Bilder und Reihenfolge (ein genannter Name, der
    fehlt, ist ein Fehler); ohne Wahl gehen alle mit, deren Datei da ist, und die übrigen
    stehen in ``hinweise``.

    Raises:
        MappenFehler: kein Projekt, ein genanntes Bild fehlt oder ist kein PNG, oder ein
            Text trägt einen Pfad oder eine Kennung dieser Maschine (Regel 3).
    """
    server = _server()
    ordner = Path(ordner)
    try:
        sicht = server.sicht(ordner)
    except projekt.ProjektError as fehler:
        raise MappenFehler(str(fehler)) from fehler
    eintraege = {b.get("bild"): b for b in sicht.get("bilder") or [] if b.get("bild")}
    blicke = dict(blicke or {})
    hinweise: list[str] = []

    if bilder:
        unbekannt = [n for n in bilder if n not in eintraege]
        if unbekannt:
            raise MappenFehler(f"Nicht in der Mappe: {', '.join(unbekannt)}. Die Mappe "
                               f"nennt: {', '.join(sorted(eintraege)) or 'keine Bilder'}.")
        gewaehlt = [eintraege[n] for n in bilder]
    else:
        gewaehlt = []
        for e in eintraege.values():
            if e.get("vorhanden") is True:
                gewaehlt.append(e)
            else:
                hinweise.append(f"übersprungen, die Datei fehlt: {e['bild']}")
    fremde = sorted(set(blicke) - {e["bild"] for e in gewaehlt})
    if fremde:
        raise MappenFehler(f"--blick für ein Bild, das nicht mitgeht: {', '.join(fremde)}.")
    if not gewaehlt:
        raise MappenFehler("Kein Bild mit Datei in dieser Mappe — die Vorführmappe wäre leer.")

    dateien: dict[str, bytes] = {}
    namen: dict[str, str] = {}
    for e in gewaehlt:
        name = e["bild"]
        try:
            pfad = server.bildpfad(ordner, name)
        except server.FlaechenError as fehler:
            raise MappenFehler(str(fehler)) from fehler
        datei = Path(name).name
        if pfad.suffix.lower() != ".png" or not DATEINAME.fullmatch(datei):
            raise MappenFehler(
                f"{datei}: In die Vorführmappe gehen nur PNG mit einem schlichten Namen "
                f"(Buchstaben, Ziffern, Punkt, Strich) — nur bei PNG werden die Begleitdaten "
                f"hier sicher abgestreift.")
        # GLEICHE NAMEN AUS VERSCHIEDENEN ORDNERN: Die Bildstufe nennt ihr Bild nach dem
        # Startwert (`render_0.png`), und jeder Lauf legt es in seinen eigenen Ordner der
        # Mappe. Flach in der Vorführmappe hiessen zwei Blicke gleich — das zweite bekommt
        # eine Nummer, nach der Reihenfolge der Mappe, und behält sonst seinen Namen.
        stamm, n = datei[:-len(".png")], 2
        while datei in dateien:
            datei = f"{stamm}-{n}.png"
            n += 1
        dateien[datei] = ohne_begleitdaten(pfad.read_bytes())
        namen[name] = datei

    eintraege_der_mappe = []
    for e in gewaehlt:
        flaeche = {k: e.get(k) for k in FELDER_DER_FLAECHE}
        flaeche["bild"] = namen[e["bild"]]
        # DAS VORHER NUR, WENN ES MITGEHT: ein Name, unter dem die Mappe nichts hat, wäre
        # ein Verweis ins Leere — und auf dem Heim-PC ein Weg in die Mappe dort.
        flaeche["vorher"] = namen.get(e.get("vorher"))
        tag = _tag(e.get("erzeugt"))
        eintraege_der_mappe.append({
            "datei": namen[e["bild"]],
            "blick": blicke.get(e["bild"]) or e.get("titel"),
            "gerechnet_am": tag,
            "satz": (SATZ_GERECHNET.format(datum=_tag_lesbar(tag)) if tag else
                     "Am Heim-PC gerechnet; wann, steht in der Mappe nicht. Das Zeichen "
                     "ist das vom Tag des Rechnens."),
            "flaeche": flaeche,
        })
    tage = [b["gerechnet_am"] for b in eintraege_der_mappe if b["gerechnet_am"]]
    mappe = {
        "schema": SCHEMA,
        "titel": titel or sicht.get("name") or "Vorführmappe",
        "art": "Beispielmappe",
        "platzhalter": False,
        "gerechnet_am": max(tage) if tage else None,
        "erstellt_am": datetime.now(timezone.utc).date().isoformat(),
        "satz": SATZ_MAPPE,
        "bilder": eintraege_der_mappe,
    }
    funde = regel3_funde(mappe, _kennungen_der_maschine(ordner))
    if funde:
        raise MappenFehler("Regel 3 — die Mappe trüge, was nicht hinaus darf, und wird "
                           "nicht geschrieben:\n  " + "\n  ".join(funde))
    return mappe, dateien, hinweise


# ====================================================================== Beispiel

#: Der Tag, an dem die Platzhalter entstanden — fest, damit dieselbe Mappe entsteht.
BEISPIEL_TAG = "2026-10-01"

#: Was am Platzhalter steht, statt dass er wie ein gerechnetes Bild aussieht.
SATZ_PLATZHALTER = ("Platzhalter: graue Flächen statt gerechneter Bilder, die Zeichen von "
                    "Hand gesetzt und nicht gemessen. Die echte Beispielmappe rechnet der "
                    "Heim-PC aus einem synthetischen Testbau.")

#: Die Platzhalter: ``(datei, blick, vermerk, herkunft, (breite, giebelseite))``.
#: ``vermerk`` geht unverändert an :func:`projekt.vermerke_bild` — die Bibliothek prüft
#: dort, dass kein Entwurf ein Urteil und keine Zahl ohne Urteil dasteht.
_BEISPIELE = (
    ("blick-sued-ost.png", "Blick Süd-Ost",
     {"urteil": True, "score": 0.84, "schwelle": 0.65}, {}, (0.46, -1)),
    ("blick-nord-west.png", "Blick Nord-West",
     {"urteil": False, "score": 0.52, "schwelle": 0.65}, {}, (0.40, 1)),
    ("skizze-ueber-den-hof.png", "Skizze über den Hof",
     {"urteil": None}, "SKIZZE", (0.52, 0)),
    ("blick-von-der-strasse.png", "Blick von der Strasse",
     {"urteil": None, "entwurf": True}, "ENTWURF", (0.58, 1)),
    ("blick-sued.png", "Blick Süd",
     {"urteil": True, "score": 0.91, "schwelle": 0.65}, {}, (0.62, 0)),
    ("blick-ost.png", "Blick Ost",
     {"urteil": None}, {"grund": "NICHT GEMESSEN: Die Geometrieprüfung lief in diesem "
                                 "Lauf nicht."}, (0.36, -1)),
)

#: Grösse der Platzhalter (3:2 wie die Kacheln des Blatts 13b) — klein, weil grau.
BEISPIEL_BREITE, BEISPIEL_HOEHE = 240, 160


def _platzhalterbild(breite_anteil: float, giebel: int) -> list[tuple[int, int, int]]:
    """Ein graues Bild: Himmel, Boden, ein Körper mit Dach — nur Graustufen, damit es nie
    wie ein gerechnetes Bild aussieht."""
    b, h = BEISPIEL_BREITE, BEISPIEL_HOEHE
    boden = int(h * 0.72)
    koerper_b = int(b * breite_anteil)
    links = (b - koerper_b) // 2 + giebel * int(b * 0.08)
    rechts = links + koerper_b
    traufe = int(h * 0.42)
    first = int(h * 0.22)
    mitte = (links + rechts) // 2
    pixel = []
    for y in range(h):
        for x in range(b):
            if y >= boden:
                g = 92
            elif links <= x < rechts and y >= traufe:
                # ZWEI FASSADEN, die eine heller: genug, um einen Körper zu lesen.
                g = 150 if x < mitte else 128
            elif links <= x < rechts and y >= first:
                halb = max(1, (rechts - links) // 2)
                if abs(x - mitte) <= halb * (y - first) / max(1, traufe - first):
                    g = 108
                else:
                    g = 70 + (y * 20) // h
            else:
                g = 70 + (y * 20) // h
            pixel.append((g, g, g))
    return pixel


def beispiel(*, titel: str | None = None) -> tuple[dict, dict[str, bytes]]:
    """Die Platzhalter-Mappe — ``(mappe, {datei: bytes})``, ohne GPU und ohne Projekt.

    Jeder Eintrag geht durch dieselben zwei Stellen wie ein gerechnetes Bild:
    :func:`projekt.vermerke_bild` (die Bibliothek) und ``_bild_fuer_die_flaeche`` (der
    Server). Die Zeichen sind gesetzt, nicht gemessen — darum ``platzhalter: true``, und
    die App sagt es an jedem Bild.
    """
    server = _server()
    skizzensatz = server.kette.HINWEIS_SKIZZE_NICHT_ANGEKOMMEN.format(
        backbone="Das Vorgabemodell", beleg="Befund auf-20260919-123")
    vorlage = {"bilder": []}
    eintraege, dateien = [], {}
    with tempfile.TemporaryDirectory() as tmp:
        for datei, blick, vermerk, herkunft, (anteil, giebel) in _BEISPIELE:
            if herkunft == "SKIZZE":
                herkunft = {"skizze": "skizze-20261001-090000.png",
                            "grund": "NICHT GEMESSEN: Die Geometrieprüfung lief in diesem "
                                     "Lauf nicht.",
                            "messung": {"hinweise": [skizzensatz]}}
            elif herkunft == "ENTWURF":
                herkunft = {"grund": (f"{server.arbeitsgang.ENTWURF_VERMERK}: schnell "
                                      f"gerechnet, ohne Geometrieprüfung (Entscheid 30). "
                                      f"NICHT GEMESSEN — weder bestanden noch "
                                      f"durchgefallen.")}
            projekt.vermerke_bild(vorlage, bild=datei, schicht="ai-imaging-layer",
                                  herkunft=herkunft, **vermerk)
            eintrag = vorlage["bilder"][-1]
            # FESTE ZEITEN: dieselbe Mappe bei jedem Lauf, damit die abgelegte Mappe
            # `ipad/VisboxMac/Beispielmappe/` an der Probe nachgerechnet werden kann.
            eintrag["erzeugt"] = eintrag["zuletzt_vermerkt"] = BEISPIEL_TAG + "T09:00:00Z"
            flaeche_voll = server._bild_fuer_die_flaeche(eintrag)
            flaeche = {k: flaeche_voll.get(k) for k in FELDER_DER_FLAECHE}
            ziel = Path(tmp) / datei
            bildschreiben.schreibe_farb_png(ziel, _platzhalterbild(anteil, giebel),
                                            BEISPIEL_BREITE, BEISPIEL_HOEHE)
            dateien[datei] = ohne_begleitdaten(ziel.read_bytes())
            eintraege.append({
                "datei": datei,
                "blick": blick,
                # NICHT GERECHNET — und darum kein Tag des Rechnens. Ein Datum hier
                # behauptete eine Messung an diesem Tag.
                "gerechnet_am": None,
                "satz": "Platzhalter: graue Fläche, das Zeichen von Hand gesetzt — "
                        "weder gerechnet noch gemessen.",
                "flaeche": flaeche,
            })
    mappe = {
        "schema": SCHEMA,
        "titel": titel or "Testbau",
        "art": "Beispielmappe",
        "platzhalter": True,
        "gerechnet_am": None,
        "erstellt_am": BEISPIEL_TAG,
        "satz": SATZ_PLATZHALTER,
        "bilder": eintraege,
    }
    funde = regel3_funde(mappe)
    if funde:                                                  # pragma: no cover
        raise MappenFehler("Regel 3:\n  " + "\n  ".join(funde))
    return mappe, dateien


# ================================================================== Schreiben

def schreibe(mappe: dict, dateien: dict[str, bytes], nach) -> Path:
    """Die Mappe in ``nach`` schreiben — **ohne Fremdes zu überschreiben.**

    ``nach`` ist leer, gibt es nicht, oder hält eine frühere Vorführmappe; deren Dateien
    werden ersetzt. Liegt dort anderes, wird nichts geschrieben.
    """
    nach = Path(nach)
    if nach.exists() and not nach.is_dir():
        raise MappenFehler(f"{nach.name} ist eine Datei, kein Ordner.")
    alte: set[str] = set()
    if nach.is_dir() and any(nach.iterdir()):
        alt = nach / MAPPENDATEI
        try:
            frueher = json.loads(alt.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            frueher = None
        if not isinstance(frueher, dict) or frueher.get("schema") != SCHEMA:
            raise MappenFehler(
                f"{nach.name} ist nicht leer und hält keine Vorführmappe — es wird nichts "
                f"überschrieben. Einen leeren Ordner angeben.")
        alte = {MAPPENDATEI} | {b.get("datei") for b in frueher.get("bilder") or []
                                if isinstance(b, dict) and isinstance(b.get("datei"), str)}
        fremd = sorted(p.name for p in nach.iterdir() if p.name not in alte)
        if fremd:
            raise MappenFehler(
                f"In {nach.name} liegt mehr als die frühere Vorführmappe "
                f"({', '.join(fremd)}) — es wird nichts überschrieben.")
    nach.mkdir(parents=True, exist_ok=True)
    for name in sorted(alte):
        if DATEINAME.fullmatch(name) or name == MAPPENDATEI:
            (nach / name).unlink(missing_ok=True)
    for name, roh in dateien.items():
        (nach / name).write_bytes(roh)
    ziel = nach / MAPPENDATEI
    ziel.write_text(json.dumps(mappe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return ziel


# ======================================================================= Aufruf

def _blicke(paare) -> dict[str, str]:
    aus = {}
    for paar in paare or []:
        name, gleich, text = paar.partition("=")
        if not gleich or not name or not text.strip():
            raise MappenFehler(f"--blick erwartet NAME=TEXT, war {paar!r}.")
        aus[name] = text.strip()
    return aus


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    quelle = ap.add_mutually_exclusive_group(required=True)
    quelle.add_argument("--ordner", help="der Projektordner einer gerechneten Mappe")
    quelle.add_argument("--beispiel", metavar="ZIEL",
                        help="ohne GPU eine Mappe aus grauen Platzhaltern nach ZIEL legen")
    ap.add_argument("--nach", metavar="ZIEL", help="wohin die Mappe kommt (mit --ordner)")
    ap.add_argument("--titel", help="der Titel der Mappe (Vorgabe: Name des Projekts)")
    ap.add_argument("--bild", nargs="+", metavar="NAME",
                    help="nur diese Bilder, in dieser Reihenfolge (Namen wie in der Mappe)")
    ap.add_argument("--blick", action="append", metavar="NAME=TEXT",
                    help="die Unterschrift eines Bildes, z. B. 'lauf.png=Blick Süd-Ost'")
    a = ap.parse_args(argv)

    try:
        if a.beispiel:
            if a.nach or a.bild or a.blick:
                raise MappenFehler("--nach, --bild und --blick gehören zu --ordner; "
                                   "--beispiel nimmt sein Ziel selbst.")
            mappe, dateien = beispiel(titel=a.titel)
            hinweise, nach = [], a.beispiel
        else:
            if not a.nach:
                raise MappenFehler("--ordner braucht --nach ZIEL.")
            mappe, dateien, hinweise = aus_projekt(a.ordner, titel=a.titel, bilder=a.bild,
                                                   blicke=_blicke(a.blick))
            nach = a.nach
        ziel = schreibe(mappe, dateien, nach)
    except MappenFehler as fehler:
        print(f"vorfuehrmappe: {fehler}", file=sys.stderr)
        return 2
    for h in hinweise:
        print(f"vorfuehrmappe: {h}", file=sys.stderr)
    print(f"{len(mappe['bilder'])} Bilder in {ziel.parent.name}/{ziel.name}"
          + (" — Platzhalter" if mappe["platzhalter"] else ""))
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
