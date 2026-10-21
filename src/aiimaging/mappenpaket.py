"""DAS MAPPENPAKET — eine Mappe des Heim-PC, so beschrieben, dass der Mac sie holen kann.

Warum es dieses Modul gibt («Visbox eigenständig», Schritt 3, 21.10.2026)
----------------------------------------------------------------------
Seit Owner-Entscheid 103 (20.10.2026) liegt die Mappe **am Mac**; der Heim-PC rechnet nur noch.
Bis dahin lagen alle Mappen am Heim-PC. Damit keine Arbeit verloren geht, holt die Mac-App eine
bestehende Mappe **einmal** an den Mac («An den Mac holen», Blatt 28 Feld 3, Blatt 36). Dafür
braucht sie drei Auskünfte, und dieses Modul ist ihr ganzer Inhalt; der Server reicht nur durch
(Regel 4):

1. :func:`mappen_am_heim` — welche Mappen hier liegen (nur Namen, keine Pfade: Regel 3).
2. :func:`paket` — was in einer Mappe steckt: die Auskunft der Knotenansicht
   (:func:`aiimaging.knotenweg.mappe_fuer_knoten`), der gesicherte Graph, die Projektdatei und
   die Liste der Dateien (Modell, Skizzen, Bilder) mit ihrer Grösse.
3. :func:`datei` — eine Datei daraus, **nur** wenn sie in dieser Liste steht.

Was dieses Modul NICHT tut
--------------------------
Es verschiebt und löscht nichts. Die Mappe bleibt am Heim-PC liegen, wie sie ist — als
Zwillingsmappe: Skizzen vom iPad kommen bis Schritt 4 weiter dort an, und ein Skizzen-Auftrag
aus der Mappe am Mac wird dort gerechnet (der Mac nennt sie mit ``X-Mappe-Heim``, siehe
:func:`finde`). *Ein Holen, das die Quelle wegräumt, wäre ein Umzug ohne Rückweg.*

Woher die Namen kommen
----------------------
Eine Mappe ist ein Ordner mit ``projekt.json``. Gesucht wird an den Orten, an denen der Server
sie anlegt oder öffnet: die Start-Mappe, die zuletzt geöffnete, ihre Nachbarn (``modell-laden``
legt eine neue Mappe **neben** die Start-Mappe) und der Rückfall-Ordner
(:func:`aiimaging.modellladen.mappen_ordner`). Die Kennung ist der Ordnername; trägt ihn eine
zweite Mappe an einem anderen Ort, gilt die erste in dieser Reihenfolge, und die Liste sagt es
(``doppelt``).

Abhängigkeiten: nur die Standardbibliothek und :mod:`aiimaging`. Kein Netz, keine Oberfläche.
"""
from __future__ import annotations

from pathlib import Path

from . import knotenweg, projekt

#: Das Format der Paketauskunft — der Mac liest nur dieses.
FORMAT = "visbox.mappenpaket/v1"

#: Wie die glb im Paket heisst — fest, egal wie sie am Heim-PC heisst (eine Mappe hat eine).
MODELL_WEG = "modell.glb"

#: Wie lang eine Kennung höchstens ist (wie ein Mappenname, :data:`modellladen.NAME_HOECHSTENS`).
KENNUNG_HOECHSTENS = 60

#: Die Endungen, die als Skizze oder Bild mitgehen — dieselben wie auf der Seite (``BILDTYPEN``).
BILDENDUNGEN = (".png", ".jpg", ".jpeg", ".webp")

#: Höchstens so viele Mappen nennt die Liste — eine Liste, die niemand durchsieht, hilft nicht.
LISTE_HOECHSTENS = 200


class MappenpaketError(ValueError):
    """Eine Anfrage passt nicht — mit Satz und Zustandscode wie :class:`knotenweg.KnotenwegError`."""

    def __init__(self, satz: str, code: int = 400):
        super().__init__(satz)
        self.code = code


def pruefe_kennung(kennung) -> str:
    """Eine Kennung ist ein blosser Ordnername: kein Pfad, kein Punkt am Anfang, nicht leer."""
    if not isinstance(kennung, str) or not kennung.strip():
        raise MappenpaketError("Es fehlt der Name der Mappe (?mappe=…).", 400)
    k = kennung.strip()
    if ("/" in k or "\\" in k or "\0" in k or k.startswith(".")
            or len(k) > KENNUNG_HOECHSTENS):
        raise MappenpaketError(f"Kein Mappenname: {kennung!r}.", 400)
    return k


def _ist_mappe(ordner: Path) -> bool:
    return (ordner / projekt.PROJEKTDATEI).is_file()


def _orte(start, zuletzt, rueckfall) -> list[Path]:
    """Die Ordner, in denen Mappen liegen können — in fester Reihenfolge, ohne Doppel."""
    gesehen: set[str] = set()
    aus: list[Path] = []

    def dazu(p: Path) -> None:
        try:
            schluessel = str(p.resolve())
        except OSError:
            return
        if schluessel not in gesehen and p.is_dir() and _ist_mappe(p):
            gesehen.add(schluessel)
            aus.append(p)

    einzelne = [Path(x) for x in (start, zuletzt) if x]
    for p in einzelne:
        dazu(p)
    eltern = [p.parent for p in einzelne] + ([Path(rueckfall)] if rueckfall else [])
    for eltern_ordner in eltern:
        try:
            kinder = sorted(c for c in Path(eltern_ordner).iterdir() if c.is_dir())
        except OSError:
            continue
        for kind in kinder:
            if not kind.name.startswith("."):
                dazu(kind)
    return aus


def _rueckfall():
    from .modellladen import mappen_ordner                     # noqa: PLC0415
    return mappen_ordner()


def mappen_am_heim(start=None, zuletzt=None, *, rueckfall=None) -> dict:
    """Die Mappen am Heim-PC — **nur Namen**, für «Noch am Heim-PC» am Mac.

    Args:
        start: Die Mappe, mit der der Server lief (``--ordner``), oder ``None``.
        zuletzt: Die zuletzt geöffnete Mappe, oder ``None``.
        rueckfall: Der Rückfall-Ordner; ohne Angabe :func:`aiimaging.modellladen.mappen_ordner`.

    Returns:
        ``{format, mappen: [{mappe, name, modell, skizzen, bilder, geaendert, doppelt}]}`` —
        ``mappe`` ist die Kennung (Ordnername), ``name`` der Name in der Projektdatei.
    """
    orte = _orte(start, zuletzt, rueckfall if rueckfall is not None else _rueckfall())
    zeilen: dict[str, dict] = {}
    for ordner in orte:
        kennung = ordner.name
        if kennung in zeilen:
            zeilen[kennung]["doppelt"] = True
            continue
        try:
            p = projekt.oeffne(ordner)["projekt"]
        except projekt.ProjektError:
            continue
        try:
            geaendert = (ordner / projekt.PROJEKTDATEI).stat().st_mtime
        except OSError:
            geaendert = None
        zeilen[kennung] = {
            "mappe": kennung,
            "name": p.get("name") or kennung,
            "modell": knotenweg.glb_der_mappe(ordner) is not None,
            "skizzen": len(_skizzen(p, ordner)),
            "bilder": len(_bilder(p, ordner)),
            "geaendert_epoch_s": geaendert,
            "doppelt": False,
        }
        if len(zeilen) >= LISTE_HOECHSTENS:
            break
    return {"format": FORMAT, "mappen": list(zeilen.values())}


def finde(kennung, start=None, zuletzt=None, *, rueckfall=None) -> Path:
    """Der Ordner der Mappe mit dieser Kennung — derselbe, den :func:`mappen_am_heim` nennt."""
    k = pruefe_kennung(kennung)
    for ordner in _orte(start, zuletzt, rueckfall if rueckfall is not None else _rueckfall()):
        if ordner.name == k:
            return ordner
    raise MappenpaketError(f"Eine Mappe «{k}» gibt es auf diesem Heim-PC nicht.", 404)


def _innen(ordner: Path, name) -> str | None:
    """Der Weg einer Datei relativ zur Mappe — nur, wenn sie **in** ihr liegt und da ist."""
    if not isinstance(name, str) or not name.strip():
        return None
    roh = Path(name)
    ziel = roh if roh.is_absolute() else ordner / roh
    try:
        rel = ziel.resolve().relative_to(ordner.resolve())
    except (OSError, ValueError):
        return None
    if not ziel.is_file() or ziel.suffix.lower() not in BILDENDUNGEN:
        return None
    weg = rel.as_posix()
    if any(teil.startswith(".") for teil in rel.parts):
        return None
    return weg


def _skizzen(p: dict, ordner: Path) -> list[str]:
    wege: list[str] = []
    for e in p.get("skizzen") or []:
        weg = _innen(ordner, e.get("skizze")) if isinstance(e, dict) else None
        if weg and weg not in wege:
            wege.append(weg)
    return wege


def _bilder(p: dict, ordner: Path) -> list[str]:
    wege: list[str] = []
    for e in p.get("bilder") or []:
        weg = _innen(ordner, e.get("bild")) if isinstance(e, dict) else None
        if weg and weg not in wege:
            wege.append(weg)
    return wege


def _dateien(ordner: Path, p: dict) -> list[dict]:
    """Die Dateien des Pakets: ``[{weg, art, bytes}]`` — Modell zuerst, dann Skizzen, Bilder."""
    aus: list[dict] = []
    glb = knotenweg.glb_der_mappe(ordner)
    if glb is not None:
        aus.append({"weg": MODELL_WEG, "art": "modell", "bytes": glb.stat().st_size})
    for art, wege in (("skizze", _skizzen(p, ordner)), ("bild", _bilder(p, ordner))):
        for weg in wege:
            if weg == MODELL_WEG:
                continue
            aus.append({"weg": weg, "art": art, "bytes": (ordner / weg).stat().st_size})
    return aus


def paket(ordner) -> dict:
    """Was der Mac braucht, um die Mappe bei sich anzulegen.

    Returns:
        ``{format, mappe, name, knoten, graph, projekt, dateien}``. ``knoten`` ist die Antwort
        von ``GET /knoten/mappe`` (mit ``glb`` als Wahrheitswert, nie einem Pfad — Regel 3); der
        Mac liefert sie danach selbst aus. ``projekt`` ist die Projektdatei, wie sie gespeichert
        ist (gesäubert beim Schreiben, :func:`aiimaging.projekt.speichere`). ``dateien`` nennt
        jede Datei mit ``weg`` (relativ zur Mappe), ``art`` und ``bytes``.
    """
    ordner = Path(ordner)
    p = projekt.oeffne(ordner)["projekt"]
    knoten = knotenweg.mappe_fuer_knoten(ordner)
    knoten["glb"] = bool(knoten["glb"])
    return {
        "format": FORMAT,
        "mappe": ordner.name,
        "name": p.get("name") or ordner.name,
        "knoten": knoten,
        "graph": knotenweg.lies_graph(ordner),
        "projekt": p,
        "dateien": _dateien(ordner, p),
    }


def datei(ordner, weg) -> Path:
    """Eine Datei des Pakets — **nur** ein Weg aus :func:`paket` (``dateien``), sonst Absage."""
    ordner = Path(ordner)
    if not isinstance(weg, str) or not weg:
        raise MappenpaketError("Es fehlt der Weg der Datei (?weg=…).", 400)
    p = projekt.oeffne(ordner)["projekt"]
    if weg == MODELL_WEG:
        glb = knotenweg.glb_der_mappe(ordner)
        if glb is None:
            raise MappenpaketError("Die Mappe hat kein Modell.", 404)
        return glb
    if weg not in set(_skizzen(p, ordner)) | set(_bilder(p, ordner)):
        raise MappenpaketError(f"Diese Datei gehört nicht zum Paket der Mappe: {weg!r}.", 404)
    return ordner / weg

