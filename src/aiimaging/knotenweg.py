"""DER KNOTENWEG — die Brücken-Schnittstelle, die die Knotenansicht aus KosmoOrbit anspricht.

Warum es dieses Modul gibt (E26, 24.09.2026)
--------------------------------------------
Die Knotenansicht ist eine wörtliche Kopie des Vis-Werkzeugs von KosmoOrbit
(``kosmovis/``). Sie bestellt Bilder so, wie sie es dort tut: über die HTTP-Schnittstelle
der Brücke (``POST /jobs`` mit Szene und Modell, dann ``/approve``, Abfragen, Bilder unter
``/artifacts``). Damit sie in Visbox **unverändert** läuft, bietet unser Server dieselbe
Schnittstelle an — und dieses Modul ist ihr ganzer Inhalt; der Server reicht nur durch
(Regel 4).

Warum die Ablage die Form der Brücke hat
----------------------------------------
Jeder Auftrag landet als ``<ablage>/vis-<zeit>-<sechs Hex>/`` mit ``job.json``,
``render-scene.json`` und ``model.glb`` — **genau die Form, die** :mod:`aiimaging.bruecke`
**liest und der Abholer schon bedient.** Es entsteht darum kein zweiter Ausführer: Wer die
Aufträge rechnen lassen will, startet den Abholer auf diese Ablage
(``tools/abholen.py --store <ablage>``), und das Ergebnis kommt als ``render-result.json``
zurück, das die Knotenansicht liest. Eine eigene Übersetzung an dieser Stelle wäre
dieselbe Fachlogik ein zweites Mal.

Der eine Unterschied zur fremden Brücke — und er ist der Grund für die Freigabe-Marke
-------------------------------------------------------------------------------------
Die fremde Brücke setzt einen Auftrag vorgabegemäss sofort auf ``queued``, mit einem Token,
den sie sich selbst ausstellt (:mod:`aiimaging.bruecke`, Modulkopf). **Hier beginnt jeder
Auftrag auf** ``awaiting_approval``. Auf ``queued`` geht er erst, wenn ein Mensch in der
Knotenansicht «Freigeben» drückt — dann schreibt :func:`freigeben` die Marke
:data:`FELD_FREIGABE`, und :func:`aiimaging.bruecke.lies_auftrag` erkennt daran eine
**menschliche** Freigabe. Ohne Marke gilt weiter, was dort steht: Ein Token, den eine
Maschine sich selbst gibt, ist keine Freigabe.

Abhängigkeiten: nur die Standardbibliothek und :mod:`aiimaging`. Kein ``bpy`` (Regel 2),
keine Oberfläche (Regel 4).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import re
import secrets
import struct
import shutil
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from . import bruecke, contracts, glbbox, kosmo_szene, projekt

#: Die Marke einer menschlichen Freigabe im Laufzettel. Die fremde Brücke schreibt sie nie;
#: sie entsteht allein in :func:`freigeben`.
FELD_FREIGABE = bruecke.FELD_FREIGABE_KNOTEN

#: Die Formate, die dieser Weg annimmt — die zwei, die :mod:`aiimaging.bruecke` als
#: Modelldatei kennt. Die fremde Brücke nimmt auch ``gltf``/``fbx``/``blend``; unsere
#: Ablage könnte sie danach nicht lesen, und ein Auftrag, der angenommen und nie gelesen
#: wird, ist schlimmer als einer, der mit Satz abgewiesen wird.
FORMATE = {".glb": "glb", ".ifc": "ifc"}

#: Deckel je Modell und je Auftrag — dieselben Zahlen wie die fremde Brücke
#: (``MAX_UPLOAD_MODEL_BYTES``, 768 MB), damit ein Modell, das dort durchgeht, hier auch
#: durchgeht.
MAX_MODELL_BYTES = 768 * 1024 * 1024

#: Die Endzustände. Ein Abbruch ändert sie nicht mehr.
ENDZUSTAENDE = (bruecke.STATUS_DONE, bruecke.STATUS_ERROR, bruecke.STATUS_CANCELLED)

#: Wo der Auftrag einer SKIZZE den Pfad seiner Mappe vermerkt (Owner-Entscheid 96, 15.10.2026).
#:
#: **Warum eine eigene Datei und nicht der Laufzettel:** Der Laufzettel geht über ``GET
#: /jobs/{id}`` in den Browser, und ein Plattenpfad trägt den Rechnernamen nach aussen
#: (Regel 3) — der Laufzettel nennt darum seit dem 14.10.2026 nur den NAMEN der Mappe. Der
#: Abholer braucht aber den Pfad, um die Skizze dort zu rechnen, wo sie liegt. Der Punkt am
#: Anfang ist die Sperre: :func:`artefakt` liefert keinen Namen aus, der mit einem Punkt
#: beginnt — die Datei bleibt auf dem Heim-PC.
DATEI_MAPPE = ".mappe.json"


class KnotenwegError(ValueError):
    """Eine Anfrage passt nicht — mit Satz und dem Zustandscode, den der Server sendet."""

    def __init__(self, satz: str, code: int = 400):
        super().__init__(satz)
        self.code = code


def _jetzt(_uhr=None) -> str:
    """Die Zeit fuer Laufzettel — aus derselben Uhr wie die Zaehlung der Vollautomatik.

    Ergebnis 357 (S4): ``freigeben`` nahm die echte Uhr, ``lege_an`` und ``voll_stand`` die
    einsetzbare der Proben — der Vermerk ``am`` nach dem Freigeben lag darum Wochen neben der
    Zeit der Probe. Ohne ``_uhr`` gilt ``time.time`` wie ueberall.
    """
    return datetime.fromtimestamp((_uhr or time.time)(), timezone.utc).isoformat(
        timespec="seconds")


def _schreibe(ziel: Path, inhalt: dict) -> None:
    daneben = ziel.with_suffix(ziel.suffix + ".teil")
    daneben.write_text(json.dumps(inhalt, indent=2, ensure_ascii=False), encoding="utf-8")
    daneben.replace(ziel)


def auftragsordner(ablage, job_id: str) -> Path:
    """Der Ordner eines Auftrags — **nur** für eine Kennung in der Form der Brücke.

    Die Kennung kommt aus der Adresse einer Anfrage. Wer hier ``../`` oder einen fremden
    Namen hineinschreibt, bekommt einen Satz, keinen Ordner.
    """
    if not kosmo_szene.ist_fremde_job_id(job_id):
        raise KnotenwegError(f"Keine Auftragskennung: {job_id!r}.", 404)
    ordner = Path(ablage) / job_id
    if not (ordner / bruecke.DATEI_LAUFZETTEL).is_file():
        raise KnotenwegError(f"Auftrag {job_id} unbekannt.", 404)
    return ordner


def _format(szene: dict, dateiname: str | None) -> str:
    """Das Format der Modelldatei — dieselbe Vorrangregel wie die fremde Brücke.

    Die Angabe in der Szene (``geometry.format``) schlägt die Dateiendung; widersprechen
    sich beide, wird abgewiesen statt umetikettiert.
    """
    geometrie = szene.get("geometry") if isinstance(szene.get("geometry"), dict) else {}
    gemeldet = str(geometrie.get("format") or "").strip().lower()
    abgeleitet = FORMATE.get(Path(dateiname or "").suffix.lower(), "")
    if gemeldet and abgeleitet and gemeldet != abgeleitet:
        raise KnotenwegError(
            f"Die Szene sagt Format {gemeldet!r}, die Datei heisst {dateiname!r}. Es wird "
            f"nicht umetikettiert.")
    gewaehlt = gemeldet or abgeleitet
    if gewaehlt not in FORMATE.values():
        raise KnotenwegError(
            f"Format {gewaehlt or 'unbekannt'!r} nimmt dieser Weg nicht an — nur "
            f"{', '.join(sorted(FORMATE.values()))}.")
    return gewaehlt


# --------------------------------------------------------------------------------------
# Vollautomatik ohne Klick (Owner-Entscheid 146, 24.10.2026)
# --------------------------------------------------------------------------------------

#: Höchstens so viele Läufe **ohne Klick** in :data:`VOLL_FENSTER_S` — über alle Geräte, gezählt
#: hier, am Heim-PC (Owner-Entscheid 146, Variante A «Alles ohne Klick, Grenzen bleiben»; die Zahl aus
#: Entscheid 134). Die Mac-App fragt vorher (``GET /bruecke/voll``); durchgesetzt wird es hier, beim
#: Anlegen — ein Gerät, das nicht fragt oder falsch zählt, bekommt trotzdem nicht mehr.
VOLL_GRENZE = 5
#: Das gleitende Fenster: die letzten 60 Minuten, nicht die volle Uhrstunde.
VOLL_FENSTER_S = 3600
#: Der Kopf, mit dem die Mac-App einen Auftrag in der Selbständigkeit «Voll» ansagt. Die
#: Knotenansicht kann ihn nicht setzen (die Mac-App reicht nur ``content-type``, ``accept`` und
#: ``x-kosmo-token`` der Seite weiter, ``Knotenwege.koepfeHinaus``).
KOPF_OHNE_KLICK = "X-Visbox-Ohne-Klick"
WERT_OHNE_KLICK = "voll"
#: Wie die Freigabe-Marke eines Laufs ohne Klick ihren Weg nennt.
FREIGABE_DURCH_VOLL = "Vollautomatik ohne Klick (Entscheid 146)"
#: Dasselbe für ein Bild aus einer Skizze mit offener Lizenz (Entscheid 153) — Ergebnis 368 (4):
#: Die Marke nannte 146, ``visbox_voll`` 153; jetzt nennen beide 153.
FREIGABE_DURCH_VOLL_SKIZZE = "Vollautomatik ohne Klick (Entscheid 153, Bild aus Skizze)"
#: Der Zustand im Laufzettel, wenn ein Lauf ohne Klick nicht ging — er wartet dann auf «Freigeben».
FELD_VOLL = "visbox_voll"
ZUSTAND_FREI = "frei"
ZUSTAND_GRENZE = "voll_grenze_erreicht"
ZUSTAND_LIZENZ = "voll_lizenz"
#: Ergebnis 351 B5: Ein Auftrag, der an der Grenze oder Lizenz wartete und danach von Hand
#: freigegeben wurde — der alte Zustand stimmt nicht mehr und bleibt nur unter ``vorher``.
ZUSTAND_VON_HAND = "von_hand_freigegeben"

#: Die Sperre um Zählen und Anlegen — ein Prozess (der Dienst, mehrere Fäden).
_VOLL_SPERRE = threading.Lock()
#: Die Datei, über die sich mehrere Prozesse an derselben Ablage absprechen (``flock``).
_VOLL_SPERRDATEI = ".visbox-voll"


def voll_bildmodelle() -> tuple[str, ...]:
    """Die Vertragskürzel, die in «Voll» ohne Klick rechnen dürfen.

    Die Kürzel des Vertrags, deren Eintrag im Register kommerziell zulässig ist
    (``backbone.pruefe_lizenz``) und weder ``nur_forschung`` noch ``lizenz_offen`` trägt —
    gerechnet, nicht abgeschrieben. Die Knotenansicht hält dieselbe Liste (``voll-render.ts``,
    ``VOLL_BILDMODELLE``); ``tests/test_voll_ohne_klick.py`` hält beide gleich.
    """
    from . import backbone as _backbone
    frei = []
    for kuerzel, unser in kosmo_szene.BACKBONE_VON_FREMD.items():
        try:
            eintrag = _backbone.hole(unser)
        except _backbone.BackboneError:
            continue
        if eintrag.nur_forschung or eintrag.lizenz_offen:
            continue
        if _backbone.pruefe_lizenz(unser).get("zulaessig"):
            frei.append(kuerzel)
    return tuple(sorted(frei))


#: ENTSCHEID 153 (Owner, 25.10.2026, über die Zentrale): «Ja, Qwen-Image darf für Skizzen in
#: Vollautomatik ohne Klick laufen.» Die Vertragskürzel, die AUS EINER SKIZZE zusätzlich zu
#: :func:`voll_bildmodelle` ohne Klick rechnen dürfen — ausdrücklich genannt, nicht aus «offene
#: Lizenz» abgeleitet: Die Freigabe gilt für dieses Modell, nicht für jedes mit offener Lizenz.
#: Nie Vorgabe (E128 Auflage 1): Ohne Wahl rechnet eine Skizze auf ``z-image-turbo``.
VOLL_SKIZZE_LIZENZ_OFFEN = ("qwen-image-2.1",)


def voll_skizzen_bildmodelle() -> tuple[str, ...]:
    """Die Kürzel aus :data:`VOLL_SKIZZE_LIZENZ_OFFEN`, die im Register stehen, ``lizenz_offen``
    tragen und **nicht** ``nur_forschung`` sind (Entscheid 153) — gerechnet, nicht abgeschrieben.

    Steht ein Eintrag einmal anders im Register (Lizenz gelöst, oder zur Forschung
    zurückgestuft), fällt er hier heraus: gelöst gehört er zu :func:`voll_bildmodelle`, zur
    Forschung zurückgestuft rechnet er wieder nur nach einem Klick.
    """
    from . import backbone as _backbone
    frei = []
    for kuerzel in VOLL_SKIZZE_LIZENZ_OFFEN:
        unser = kosmo_szene.BACKBONE_VON_FREMD.get(kuerzel)
        if unser is None:
            continue
        try:
            eintrag = _backbone.hole(unser)
        except _backbone.BackboneError:
            continue
        if eintrag.lizenz_offen and not eintrag.nur_forschung:
            frei.append(kuerzel)
    return tuple(frei)


def voll_lizenz_mangel(szene: dict) -> str | None:
    """Warum dieser Auftrag NICHT ohne Klick rechnen darf (Lizenz) — ``None``: darf.

    Nur Blender (``vis.skip``) braucht kein Bildmodell und ist darum von der LIZENZ befreit —
    **nicht von der Grenze**: Auch ein Lauf nur mit Blender zählt zu den :data:`VOLL_GRENZE` je
    Stunde und wartet bei erreichter Grenze (Ergebnis 351 B4; so gebaut, Zählregel unverändert).
    Sonst gilt das bestellte Bildmodell
    (``vis.backbone``, ohne Angabe die Vorgabe des Vertrags ``z-image-turbo``); ein Modell mit
    Forschungs- oder offener Lizenz (heute Qwen-Image 2.1) oder ein unbekanntes rechnet nur nach
    einem Klick. ``vis.research_only`` ebenso.

    **Ausnahme Entscheid 153 (25.10.2026):** ein Bild aus einer Skizze (``skizze``) mit einem
    Modell aus :func:`voll_skizzen_bildmodelle` (heute Qwen-Image 2.1) darf ohne Klick — gezählt
    wie jeder andere Lauf, markiert wie bisher.
    """
    vis = szene.get("vis") if isinstance(szene.get("vis"), dict) else {}
    if vis.get("skip") is True:
        return None
    if vis.get("research_only") is True:
        return "Der Auftrag ist als «nur Forschung» bestellt — er rechnet nur nach einem Klick."
    bm = vis.get("backbone")
    bm = "z-image-turbo" if bm is None else bm
    # ENTSCHEID 153 (Owner, 25.10.2026): «Ja, Qwen-Image darf für Skizzen in Vollautomatik ohne Klick
    # laufen.» NUR ein Bild AUS EINER SKIZZE, nur die Modelle aus `voll_skizzen_bildmodelle` (offene
    # Lizenz nach E128, nie «nur Forschung») — die Grenze je Stunde zaehlt weiter, und die Marke
    # `lizenz_offen` / `engine_license_open` bleibt am Lauf (E128 Auflage 2, unveraendert).
    if szene.get("skizze") is not None and bm in voll_skizzen_bildmodelle():
        return None
    if not isinstance(bm, str) or bm not in voll_bildmodelle():
        return (f"Das Bildmodell {bm!r} hat eine offene oder Forschungs-Lizenz (oder ist hier nicht "
                f"zulässig) — ohne Klick rechnen nur {', '.join(voll_bildmodelle())}. "
                f"«Freigeben» am Knoten startet ihn.")
    return None


def _zeit(text) -> float | None:
    try:
        return datetime.fromisoformat(str(text).replace("Z", "+00:00")).timestamp()
    except (TypeError, ValueError):
        return None


def _laeufe_ohne_klick(ablage, jetzt: float) -> list[float]:
    """Wann in den letzten :data:`VOLL_FENSTER_S` Sekunden ein Lauf ohne Klick freigegeben wurde."""
    ordner = Path(ablage)
    if not ordner.is_dir():
        return []
    zeiten = []
    for d in ordner.iterdir():
        if not (d.is_dir() and kosmo_szene.ist_fremde_job_id(d.name)):
            continue
        # Der Name trägt die Anlegezeit (``vis-<Sekunden>-…``) — ältere Ordner gar nicht erst lesen.
        teile = d.name.split("-")
        if len(teile) >= 2 and teile[1].isdigit() and int(teile[1]) < jetzt - VOLL_FENSTER_S - 300:
            continue
        try:
            zettel = json.loads((d / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        marke = zettel.get(FELD_FREIGABE) if isinstance(zettel, dict) else None
        if not (isinstance(marke, dict) and marke.get("ohne_klick") is True):
            continue
        am = _zeit(marke.get("am"))
        if am is not None and jetzt - VOLL_FENSTER_S < am <= jetzt + 60:
            zeiten.append(am)
    return sorted(zeiten)


def _uhrzeit(ts: float) -> str:
    """Die Ortszeit des Heim-PC als «HH:MM» für den Satz — AUFGERUNDET auf die nächste Minute.

    Ergebnis 351 B6: Abgeschnitten nannte der Satz «wieder frei ab 13:40», frei war es erst um
    13:40:49 — bis zu 59 s zu früh. Wer zur genannten Minute bestellt, soll nicht wieder an die
    Grenze stossen. Die genaue Zeit steht weiter in ``wieder_frei_ab`` (ISO, Sekunden).
    """
    return datetime.fromtimestamp(math.ceil(ts / 60) * 60).strftime("%H:%M")


def voll_stand(ablage, *, _uhr=None) -> dict:
    """Wie viele Läufe ohne Klick die letzte Stunde hatte, und ob noch einer geht — ``GET /bruecke/voll``.

    Returns:
        ``{grenze, fenster_s, laeufe, frei, zustand, wieder_frei_ab, satz, bildmodelle}``.
        ``wieder_frei_ab`` ist die ISO-Zeit, ab der wieder einer geht (``None``: jetzt).
    """
    jetzt = (_uhr or time.time)()
    zeiten = _laeufe_ohne_klick(ablage, jetzt)
    frei = len(zeiten) < VOLL_GRENZE
    wieder = None
    if not frei:
        # GLEITEND: frei wird es, sobald der älteste der letzten fünf aus der Stunde fällt.
        wieder = zeiten[len(zeiten) - VOLL_GRENZE] + VOLL_FENSTER_S
    satz = (f"Vollautomatik: {len(zeiten)} von {VOLL_GRENZE} Läufen ohne Klick in der letzten Stunde."
            if frei else
            f"Grenze erreicht: {VOLL_GRENZE} Läufe ohne Klick in der letzten Stunde — wieder frei ab "
            f"{_uhrzeit(wieder)}. Bis dahin wird jeder Lauf eine Karte und wartet auf «Freigeben» — "
            f"auch «Grundlage rendern» (nur Blender) zählt mit.")
    return {"grenze": VOLL_GRENZE, "fenster_s": VOLL_FENSTER_S, "laeufe": len(zeiten), "frei": frei,
            "zustand": ZUSTAND_FREI if frei else ZUSTAND_GRENZE,
            "wieder_frei_ab": (datetime.fromtimestamp(wieder, timezone.utc).isoformat(timespec="seconds")
                               if wieder is not None else None),
            "satz": satz, "bildmodelle": list(voll_bildmodelle()),
            # Entscheid 153: zusätzlich, NUR für ein Bild aus einer Skizze.
            "skizzen_bildmodelle": list(voll_skizzen_bildmodelle())}


def _voll_entscheid(ablage, szene: dict, _uhr) -> tuple[bool, dict]:
    """Darf DIESER Auftrag ohne Klick in die Reihe? ``(ja, vermerk)`` — unter der Sperre gerufen."""
    mangel = voll_lizenz_mangel(szene)
    if mangel:
        return False, {"zustand": ZUSTAND_LIZENZ, "satz": mangel}
    stand = voll_stand(ablage, _uhr=_uhr)
    if not stand["frei"]:
        return False, {"zustand": ZUSTAND_GRENZE, "satz": stand["satz"],
                       "wieder_frei_ab": stand["wieder_frei_ab"], "laeufe": stand["laeufe"],
                       "grenze": VOLL_GRENZE}
    vermerk = {"zustand": ZUSTAND_FREI, "laeufe": stand["laeufe"] + 1, "grenze": VOLL_GRENZE}
    vis = szene.get("vis") if isinstance(szene.get("vis"), dict) else {}
    if szene.get("skizze") is not None and vis.get("backbone") in voll_skizzen_bildmodelle():
        # ENTSCHEID 153: ohne Klick, aber nicht still — der Laufzettel sagt, warum es ging und
        # dass die Lizenz offen bleibt (die Marke am Ergebnis setzt der Lauf selbst, E128).
        vermerk["entscheid"] = "153"
        vermerk["satz"] = SATZ_VOLL_SKIZZE_LIZENZ_OFFEN.format(modell=vis.get("backbone"))
    return True, vermerk


#: Der Satz im Laufzettel, wenn ein Bild aus einer Skizze nach Entscheid 153 mit offener Lizenz
#: ohne Klick in die Reihe ging.
SATZ_VOLL_SKIZZE_LIZENZ_OFFEN = (
    "Ohne Klick nach Entscheid 153 (Bild aus Skizze) — das Bildmodell {modell} hat eine offene "
    "Lizenz (E128): Das Bild ist markiert und nicht für eine Veröffentlichung freigegeben.")


def lege_an(ablage, szene: dict, modell, dateiname: str | None = None,
            *, kennung: str | None = None, mappe: str | None = None,
            mappe_pfad=None, am_mac: str | None = None, ohne_klick: bool = False,
            skizze_anlage: dict | None = None, _uhr=None) -> dict:
    """Einen Auftrag annehmen: drei Dateien in einen neuen Ordner, Status wartet auf Freigabe.

    Args:
        ablage: Wohin die Aufträge kommen — derselbe Ordner, den der Abholer liest.
        szene: ``render-scene/v1`` wie von der Knotenansicht gesendet.
        modell: Die Bytes der Modelldatei — oder der :class:`~pathlib.Path` einer Datei, die
            :func:`teile_formular` schon in die Ablage geschrieben hat (sie wird in den Auftrag
            verschoben, nicht kopiert) — oder ``None``: **nur für eine Variante**
            (``vis.grundlage``). Dann nimmt der Auftrag das Modell des Laufs, der die
            Grundlage gelegt hat (:func:`modell_der_grundlage`); fehlt es auf diesem
            Rechner, wird mit Satz abgewiesen (409) — nie gewartet.
        dateiname: Der Name, unter dem sie geschickt wurde — nur Rückfall fürs Format.
        kennung: Nur für Proben; sonst wie bei der Brücke aus Uhrzeit und Zufall.
        mappe: Der NAME der Mappe, aus der bestellt wurde (nur der Ordnername, kein Pfad —
            Regel 3). **Warum (Prüfung 14.10.2026, Visbox-Plan «Was die Knoten tun»):** Die
            Ablage ist die eine, beim Start des Servers bestimmte (``<Start-Mappe>/knotenweg``
            oder ``--auftragsablage``) — der Abholer liest genau sie. Seit «Datei laden …»
            (Entscheid 90) bestellt die Knotenansicht aber auch aus Mappen, die erst danach
            entstanden sind; ihre Aufträge liegen richtig in derselben Ablage, nur sagte
            nichts mehr, zu welcher Mappe ein Bild gehört. Der Laufzettel sagt es jetzt.
        mappe_pfad: Der PFAD derselben Mappe — nur gebraucht, wenn die Szene eine Skizze
            trägt (``skizze``, Owner-Entscheid 96): Dann wird sie dort gerechnet, wo sie liegt,
            und der Pfad steht in :data:`DATEI_MAPPE` neben dem Auftrag, nie im Laufzettel.
            Eine Skizze ohne Mappe, oder eine, die in der Mappe nicht (mehr) steht, wird mit
            Satz abgewiesen — angenommen und erst am Heim-PC gescheitert wäre schlimmer.
        ohne_klick: Die Mac-App sagt «Voll» an (Kopf :data:`KOPF_OHNE_KLICK`, Owner-Entscheid
            146): Dann geht der Auftrag **sofort** auf ``queued`` — mit der Marke
            :data:`FELD_FREIGABE` (``ohne_klick: True``) —, wenn das Bildmodell eine zulässige
            Lizenz hat und die Grenze von :data:`VOLL_GRENZE` Läufen je Stunde (über alle
            Geräte, hier gezählt) nicht erreicht ist. Sonst bleibt er wie jeder andere auf
            ``awaiting_approval``, und :data:`FELD_VOLL` sagt, warum (mit ``wieder_frei_ab``).
        am_mac: Der Name der **Mappe am Mac**, aus der bestellt wurde (``X-Mappe-Am-Mac``),
            sonst ``None``. Mit ihm ist
            ``mappe_pfad`` nur ihr Zwilling hier (oder ``None``). Fehlt die Skizze dort, sagt
            der Satz, dass sie nur am Mac liegt (:data:`SATZ_SKIZZE_NUR_AM_MAC`, Befund F4) —
            ausser sie reist mit (``skizze_anlage``).
        skizze_anlage: Die mitgeschickte Skizze einer Mappe am Mac (:func:`lies_skizzen_anlage`,
            Demobefund 25.10.2026) — nur mit ``am_mac`` gelesen. Hat der Zwilling hier die
            Skizze nicht, wird sie geprüft (:func:`_anlage_statt_zwilling`) und in den Auftrag
            gelegt; der Abholer baut daraus die Mappe (:func:`mappe_aus_anlage`).

    Returns:
        Der Laufzettel, wie er in ``job.json`` steht — mit ``approval_token``, den nur der
        Absender bekommt und mit dem er freigibt.
    """
    if not isinstance(szene, dict):
        raise KnotenwegError("Die Szene ist kein JSON-Objekt.")
    # PASST DIE VARIANTE ZUR GRUNDLAGE? Schon hier, nicht erst beim Rechnen (Wunsch des
    # Integrators, auf-20261020-292 Punkt 10) — 409 mit Satz, kein Ordner angelegt.
    unpassend = grundlage_passt_nicht(ablage, szene)
    if unpassend:
        raise KnotenwegError(unpassend, 409)
    # EIN WIDERSPRUCH DER BESTELLUNG schon hier, nicht erst nach «Freigeben» (Ergebnis 357, S3):
    # 400 mit demselben Satz, den sonst der Abholer schreibt — kein Ordner angelegt.
    widerspruch = kosmo_szene.widersprueche_beim_annehmen(szene)
    if widerspruch:
        raise KnotenwegError("Der Auftrag hat Mängel, die einen Lauf verbieten:\n- "
                             + "\n- ".join(widerspruch), 400)
    aus_grundlage = None
    if modell is None:
        aus_grundlage = _modell_fuer_variante(ablage, szene)
        groesse = aus_grundlage.stat().st_size
        dateiname = aus_grundlage.name
        # Das Format ist das der Datei, die da liegt — die Seite hat keine geschickt.
        szene = dict(szene, geometry={**(szene.get("geometry") if isinstance(
            szene.get("geometry"), dict) else {}), "format": FORMATE[aus_grundlage.suffix]})
    elif isinstance(modell, Path):
        groesse = modell.stat().st_size if modell.is_file() else 0
    else:
        groesse = len(modell)
    if not groesse:
        raise KnotenwegError("Die Modelldatei ist leer.")
    if groesse > MAX_MODELL_BYTES:
        raise KnotenwegError(
            f"Die Modelldatei ist {groesse / 1e6:.0f} MB gross; angenommen werden bis "
            f"{MAX_MODELL_BYTES / 1e6:.0f} MB.", 413)
    fmt = _format(szene, dateiname)
    # DIE SKIZZE REIST MIT (Demobefund 25.10.2026): aus einer Mappe am Mac, deren Zwilling hier sie
    # nicht hat. Ohne Mappe am Mac zaehlt eine Anlage nicht — dann gilt der Weg wie bisher.
    anlage = None
    if am_mac and skizze_anlage is not None and szene.get("skizze") is not None:
        anlage = _anlage_statt_zwilling(ablage, szene, mappe_pfad, skizze_anlage)
    skizze = anlage["name"] if anlage else _pruefe_skizze(szene, mappe_pfad, am_mac=am_mac)

    job_id = kennung or f"vis-{int((_uhr or time.time)())}-{secrets.token_hex(3)}"
    if not kosmo_szene.ist_fremde_job_id(job_id):
        raise KnotenwegError(f"Keine Auftragskennung: {job_id!r}.")
    if not ohne_klick:
        return _lege_an_ordner(ablage, szene, job_id, modell, aus_grundlage, fmt, skizze,
                               mappe, mappe_pfad, None, _uhr, anlage=anlage)
    # ZAEHLEN UND ANLEGEN UNTER EINER SPERRE: Zwei Geraete, die zugleich den fuenften Lauf
    # bestellen, saehen sonst beide «4 von 5» und bekaemen beide einen.
    Path(ablage).mkdir(parents=True, exist_ok=True)
    with _VOLL_SPERRE, bruecke.laufzettel_sperre(Path(ablage) / _VOLL_SPERRDATEI):
        ja, vermerk = _voll_entscheid(ablage, szene, _uhr)
        return _lege_an_ordner(ablage, szene, job_id, modell, aus_grundlage, fmt, skizze,
                               mappe, mappe_pfad, (ja, vermerk), _uhr, anlage=anlage)


def _lege_an_ordner(ablage, szene, job_id, modell, aus_grundlage, fmt, skizze, mappe,
                    mappe_pfad, voll, _uhr, *, anlage: dict | None = None) -> dict:
    """Der Ordner des Auftrags mit seinen drei Dateien — ``voll``: ``(ohne Klick?, vermerk)``."""
    ordner = Path(ablage) / job_id
    ordner.mkdir(parents=True, exist_ok=False)

    modellpfad = ordner / (bruecke.DATEI_MODELL_IFC if fmt == "ifc" else bruecke.DATEI_MODELL)
    if aus_grundlage is not None:
        # Ein harter Verweis kostet nichts und keinen Platz; geht er nicht (anderes
        # Laufwerk), eine Kopie. Die Datei des ersten Laufs bleibt unberührt.
        try:
            os.link(aus_grundlage, modellpfad)
        except OSError:
            shutil.copyfile(aus_grundlage, modellpfad)
    elif isinstance(modell, Path):
        os.replace(modell, modellpfad)
    else:
        modellpfad.write_bytes(modell)
    szene = dict(szene)
    # WIE DIE BRUECKE: Pfad und Ausgabeort setzt der Server, nie der Absender. Ein
    # mitgeschicktes `out` koennte sonst in einen fremden Ordner zeigen.
    szene["geometry"] = {**(szene.get("geometry") if isinstance(szene.get("geometry"), dict)
                            else {}), "path": str(modellpfad), "format": fmt}
    szene["out"] = str(ordner / "out")
    _schreibe(ordner / bruecke.DATEI_SZENE, szene)
    if anlage is not None:
        # DIE SKIZZE KAM MIT: kein Mappenpfad — die Mappe baut der Abholer im Auftrag.
        _schreibe_anlage(ordner, anlage)
    elif skizze is not None:
        _schreibe(ordner / DATEI_MAPPE, {"pfad": str(Path(mappe_pfad).resolve())})

    vis = szene.get("vis") if isinstance(szene.get("vis"), dict) else {}
    stil = szene.get("style") if isinstance(szene.get("style"), dict) else {}
    zettel = {
        "job_id": job_id,
        "status": bruecke.STATUS_AWAITING,
        "scene": str(ordner / bruecke.DATEI_SZENE),
        "approval_token": f"{bruecke.TOKEN_VORSATZ}{secrets.token_hex(4)}",
        "idle_window_only": True,
        "requested_engine": "cycles" if vis.get("skip") else "ki",
        "requested_style": stil.get("mode", "none"),
        "created_at": _jetzt(_uhr),
        **({"mappe": str(mappe)} if mappe else {}),
        # Was der Heim-PC von der Skizze weiss — sichtbar, ohne Pfad (Regel 3).
        **({"skizze_mitgereist": {
            "name": anlage["name"], "unterlage": anlage.get("ueber"),
            "unterlage_von": (None if anlage.get("ueber") is None else
                              "mitgeschickt" if not isinstance(anlage.get("unterlage"), Path)
                              else "heim-pc"),
            # Ergebnis 368 (5): genommen wurde ein anderes Bild derselben Kamera — welches.
            **({"unterlage_ersatz": anlage["unterlage"].name}
               if isinstance(anlage.get("unterlage"), Path) and anlage.get("ueber")
               and anlage["unterlage"].name != str(anlage["ueber"]).rsplit("/", 1)[-1] else {}),
            "standpunkt": SATZ_STANDPUNKT_UNTERLAGE.format(
                kamera=anlage["standpunkt"]["kamera"]) if anlage.get("standpunkt")
            else None}} if anlage is not None else {}),
        bruecke.FELD_MELDUNG: "Wartet auf Freigabe — erst ein Klick auf «Freigeben» "
                              "schickt den Auftrag an die Grafikkarte.",
    }
    if voll is not None:
        ja, vermerk = voll
        zettel[FELD_VOLL] = vermerk
        if ja:
            # OHNE KLICK IN DIE REIHE (Entscheid 146): dieselbe Marke wie «Freigeben», mit dem Weg
            # und `ohne_klick` — daran zaehlt `voll_stand` die Stunde.
            zettel["status"] = bruecke.STATUS_QUEUED
            am = datetime.fromtimestamp((_uhr or time.time)(), timezone.utc).isoformat(
                timespec="seconds")
            zettel["updated_at"] = am
            durch = (FREIGABE_DURCH_VOLL_SKIZZE if vermerk.get("entscheid") == "153"
                     else FREIGABE_DURCH_VOLL)
            zettel[FELD_FREIGABE] = {"am": am, "durch": durch, "ohne_klick": True}
            zettel.pop(bruecke.FELD_MELDUNG, None)
        else:
            zettel[bruecke.FELD_MELDUNG] = (
                f"Wartet auf Freigabe — nicht ohne Klick: {vermerk['satz']}")
    _schreibe(ordner / bruecke.DATEI_LAUFZETTEL, zettel)
    return zettel


#: Der Satz, wenn eine Variante ohne Modell kommt und die Grundlage hier fehlt. Seit
#: auf-20261020-289 (B2) mit dem vereinbarten Wortlaut «nicht bekannt» — wie der Satz des
#: Abholers, wenn ein Modell mitkam (bis dahin hiess es an der Tür «nicht zu finden»).
#: Ohne Modell und ohne Grundlage kein Auftrag (400) — die Tür, durch die sonst ein KI-Bild ohne
#: Blender-Grundlage käme (Masstreue, A0051).
SATZ_OHNE_MODELL_UND_GRUNDLAGE = ("Ein Auftrag braucht die Felder «scene» und «model» — ohne "
                                  "Modell nur als Variante einer Grundlage (vis.grundlage).")
SATZ_GRUNDLAGE_FEHLT = (
    "Die Variante kam ohne Modell, und die Grundlage {kennung} ist hier nicht bekannt (kein "
    "Auftrag auf diesem Heim-PC hat sie gerechnet, oder sein Modell ist weg). Bitte zuerst "
    "«Grundlage rendern» — oder die Variante mit Modell schicken.")


def _modell_fuer_variante(ablage, szene: dict) -> Path:
    """Das Modell für einen Auftrag ohne Modelldatei — nur mit ``vis.grundlage``, sonst Satz."""
    vis = szene.get("vis") if isinstance(szene.get("vis"), dict) else {}
    kennung = vis.get("grundlage")
    if not kennung:
        raise KnotenwegError(SATZ_OHNE_MODELL_UND_GRUNDLAGE)
    if not (isinstance(kennung, str) and kosmo_szene.GRUNDLAGE_KENNUNG.match(kennung)):
        raise KnotenwegError(f"'vis.grundlage' ist {kennung!r} und keine Kennung einer "
                             f"Grundlage (gl- und 16 Hexzeichen).")
    gefunden = modell_der_grundlage(ablage, kennung)
    if gefunden is None or gefunden.suffix not in FORMATE:
        raise KnotenwegError(SATZ_GRUNDLAGE_FEHLT.format(kennung=kennung), 409)
    return gefunden


#: Der Satz, wenn eine Skizze aus einer MAPPE AM MAC bestellt wird, die der Heim-PC nicht hat
#: (Befund F4, Mac-Demolauf 0.3.54, 24.10.2026). Bis dahin hiess es «steht nicht (mehr) in der
#: Mappe … verworfen oder nie abgelegt» — falsch: Die Skizze lag in der Mappe am Mac (der Knoten
#: und ``skizzen_lesen`` zeigten sie), nur der Zwilling hier hatte sie nie bekommen. Seit dem
#: Demobefund vom 25.10.2026 reist die Skizze mit (:func:`lies_skizzen_anlage`); der Satz bleibt
#: für eine Knotenansicht, die sie noch nicht mitschickt (ältere Mac-App).
SATZ_SKIZZE_NUR_AM_MAC = (
    "Die Skizze {name!r} liegt nur am Mac (Mappe «{mappe}») — der Heim-PC hat sie nicht "
    "bekommen: Sie kam beim Bestellen nicht mit (das kann erst die neue Mac-App — bitte "
    "aktualisieren). Bis dahin: am Mac unter «Mappen …» «Ohne Mappe am Mac» wählen, die Skizze am iPad "
    "neu senden und das Bild dann bestellen — so liegt sie am Heim-PC und lässt sich rechnen.")


#: Befund F4 (Demolauf 24.10.2026): eine Skizze ohne Anweisung und ohne Prompt — beim Annehmen
#: abgewiesen (400), statt nach dem Lauf mit «prompt fehlt oder ist leer (None)».
SATZ_SKIZZE_OHNE_ANWEISUNG = (
    "Die Skizze trägt keine Anweisung, und am Render-Knoten steht kein Prompt — bitte am "
    "Prompt-Knoten beschreiben, was entstehen soll.")


# ============================================== Die Skizze reist mit (Demobefund 25.10.2026)
#
# ANLASS (Mac 0.3.66, iPad 0.3.66, Mappe am Mac «haus-am-hang»): Die Skizze vom iPad lag in der
# Mappe am Mac, «Bild aus Skizze» kam mit :data:`SATZ_SKIZZE_NUR_AM_MAC` zurück — in einer Mappe am
# Mac ging «Bild aus Skizze» überhaupt nicht. Seither schickt die Knotenansicht bei einer Mappe am
# Mac die Skizze mit (Felder :data:`FELD_SKIZZE_PNG`, :data:`FELD_UNTERLAGE_PNG`,
# :data:`FELD_SKIZZE_INFO` im selben Formular wie Szene und Modell). Der Heim-PC legt sie in den
# Auftrag (:data:`ORDNER_SKIZZE_AM_MAC`), und der Abholer baut daraus vor dem Lauf eine Mappe im
# Auftrag (:func:`mappe_aus_anlage`) — gerechnet wird dann genau wie in einer Mappe am Heim-PC
# (:func:`aiimaging.abholer.skizzenlauf`, :func:`aiimaging.arbeitsgang.rechne_skizze`).

#: Die Felder des Formulars (``POST /bruecke/jobs``) — nur mit ``X-Mappe-Am-Mac`` gelesen.
FELD_SKIZZE_PNG = "skizze_png"
FELD_UNTERLAGE_PNG = "unterlage_png"
FELD_SKIZZE_INFO = "skizze_info"
#: Höchstens so gross ist eine Skizze oder ihre Unterlage — wie jedes Feld des Formulars
#: (:data:`FELD_HOECHSTENS`, 16 MB; eine Skizze vom iPad hat 1–5 MB).
SKIZZE_ANLAGE_HOECHSTENS = 16 * 1024 * 1024
#: Höchstens so lang ist eine Kante der Skizze oder Unterlage (Bildpunkte).
SKIZZE_KANTE_HOECHSTENS = 8192
#: Höchstens so lang ist die Bemerkung, die mitreist.
SKIZZE_BEMERKUNG_HOECHSTENS = 4000
#: Wo die Anlage im Auftrag liegt — ein Ordner mit Punkt: :func:`artefakt` liefert nur flache
#: Namen aus, nie etwas darunter.
ORDNER_SKIZZE_AM_MAC = ".skizze-am-mac"
DATEI_ANLAGE = "anlage.json"
DATEI_ANLAGE_SKIZZE = "skizze.png"
DATEI_ANLAGE_UNTERLAGE = "unterlage.png"
#: Die Mappe, die der Abholer im Auftrag aus der Anlage baut.
ORDNER_SKIZZENMAPPE = ".skizzenmappe"
#: Ein Bild eines Auftrags in der Mappe am Mac: ``bilder/<auftrag>/<kamera>__<ebene>.png``
#: (``Mappenkern.auftragsweg`` der Mac-App).
UNTERLAGE_AUS_AUFTRAG = re.compile(r"^bilder/(vis-[0-9]+-[0-9a-f]{6})/([^/]+\.png)$")

#: Die Zeile, wenn der Standpunkt aus dem Bild unter der Skizze kommt (Entscheid 96b).
SATZ_STANDPUNKT_UNTERLAGE = "Standpunkt vom Bild unter der Skizze ({kamera})"

#: Der Satz, wenn der Auftrag der Unterlage hier liegt, aber kein Bild derselben Kamera in ihm.
SATZ_UNTERLAGE_NICHT_IM_AUFTRAG = (
    "Die Skizze {name!r} wurde auf {ueber!r} gezeichnet. Der Auftrag liegt auf dem Heim-PC, aber "
    "die Datei {datei!r} fehlt in ihm, und auch kein anderes Bild derselben Kamera (im Auftrag: "
    "{vorhanden}). Die Unterlage mitschicken (am Mac das Bild öffnen und neu bestellen).")

#: Der Satz, wenn eine Unterlage genannt ist, aber weder mitkam noch hier liegt.
SATZ_UNTERLAGE_FEHLT = (
    "Die Skizze {name!r} wurde auf {ueber!r} gezeichnet, aber dieses Bild kam nicht mit und "
    "liegt auf dem Heim-PC nicht — ohne ihre Unterlage wird sie nicht gerechnet (vor einem "
    "neutralen Grund wäre es eine andere Bestellung). Das Bild am Mac öffnen und neu bestellen.")


def _png_kante(daten: bytes, was: str) -> tuple[int, int]:
    """``(breite, hoehe)`` eines PNG — oder :class:`KnotenwegError` (400) mit Satz."""
    if not isinstance(daten, (bytes, bytearray)) or len(daten) < 33 \
            or bytes(daten[:8]) != b"\x89PNG\r\n\x1a\n" or bytes(daten[12:16]) != b"IHDR":
        raise KnotenwegError(f"{was} ist kein PNG-Bild.")
    if len(daten) > SKIZZE_ANLAGE_HOECHSTENS:
        raise KnotenwegError(f"{was} ist {len(daten) / 1e6:.0f} MB gross; angenommen werden bis "
                             f"{SKIZZE_ANLAGE_HOECHSTENS // (1024 * 1024)} MB.", 413)
    breite, hoehe = struct.unpack(">II", bytes(daten[16:24]))
    if not (0 < breite <= SKIZZE_KANTE_HOECHSTENS and 0 < hoehe <= SKIZZE_KANTE_HOECHSTENS):
        raise KnotenwegError(f"{was} hat {breite} x {hoehe} Bildpunkte — erwartet sind 1 bis "
                             f"{SKIZZE_KANTE_HOECHSTENS} je Kante.")
    return breite, hoehe


def standpunkt_der_unterlage(ueber) -> dict | None:
    """Von wo das Bild unter einer Skizze aus einer Mappe am Mac gerechnet wurde — Entscheid 96b.

    Die Mappe am Mac legt die Bilder eines Auftrags unter ``bilder/<auftrag>/<kamera>__<ebene>.png``
    ab; die Kamera steht im Namen. Ist sie eine der zwölf Richtungen (``kameras.RICHTUNGEN``, auch
    als deutsches Kürzel), ist der Standpunkt ``{"kamera": <kürzel>}`` — sonst ``None`` (nicht
    bekannt, **nicht geraten**: Dann gilt der Standpunkt der Mappe, und das wird gesagt).
    """
    from . import kameras
    treffer = UNTERLAGE_AUS_AUFTRAG.match(ueber) if isinstance(ueber, str) else None
    if treffer is None or "__" not in treffer.group(2):
        return None
    kuerzel, _ = kameras.kuerzel_lesen(treffer.group(2).split("__", 1)[0])
    return {"kamera": kuerzel} if kuerzel in kameras.RICHTUNGEN else None


#: Ebenen, die nie als Unterlage taugen (sie zeigen kein Bild des Hauses).
_KEINE_UNTERLAGE = ("tiefe", "material-id", "material_id", "maske")
#: Bilder, die als Unterlage nur ganz zuletzt taugen — sie sind nicht das fertige Bild (Ergebnis 371).
_UNTERLAGE_ZULETZT = ("vorschau", "teilbild")


def unterlage_in_der_ablage(ablage, ueber) -> Path | None:
    """Das Bild ``bilder/<auftrag>/<name>`` der Mappe am Mac, wie es HIER im Auftrag liegt — der
    Heim-PC hat es gerechnet. ``None``, wenn der Name nicht passt oder der Auftrag hier fehlt.

    **Ergebnis 368 (5):** Ein Grundbild ohne ``render.passes`` hat kein
    ``<kamera>__schoenbild.png`` im Auftrag — die Brücke antwortete 400, obwohl der Auftrag
    da war. Fehlt die genannte Datei, nimmt sie das Bild **derselben Kamera**, das der Lauf
    geschrieben hat: erst das fertige (Schönbild, ``<kamera>.png``, ein Bild aus ``images`` des
    Ergebnisses mit der Kamera im Namen, Beauty), dann andere ``<kamera>__…png`` ohne
    Tiefe/Material-ID/Maske, Vorschau und Teilbild zuletzt (Ergebnis 371). Gleiche Kamera heisst
    gleiche Rahmung.
    """
    treffer = UNTERLAGE_AUS_AUFTRAG.match(ueber) if isinstance(ueber, str) else None
    if treffer is None or ablage is None:
        return None
    job, name = treffer.group(1), treffer.group(2)
    try:
        return artefakt(ablage, job, name)
    except KnotenwegError:
        pass
    try:
        ordner = auftragsordner(ablage, job)
    except KnotenwegError:
        return None
    kamera = name.split("__", 1)[0] if "__" in name else None
    if not kamera:
        return None
    # DIE REIHENFOLGE (Ergebnis 371): Zuerst das fertige Bild der Kamera — Schönbild, dann
    # `<kamera>.png`, dann ein Bild aus `images` des Ergebnisses, dann Beauty-Varianten —, eine
    # Vorschau oder ein Teilbild nur ganz zuletzt. 371 bekam `sSW__vorschau.png` statt des fertigen
    # `sSW.png`, weil die Namen alphabetisch kamen.
    try:
        bilder = json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(
            encoding="utf-8")).get("images") or []
    except (OSError, ValueError, AttributeError):
        bilder = []
    eigene = sorted(d.name for d in ordner.glob(f"{kamera}__*.png")
                    if not any(t in d.name for t in _KEINE_UNTERLAGE))
    spaet = [n for n in eigene if any(t in n for t in _UNTERLAGE_ZULETZT)]
    kandidaten = [f"{kamera}__schoenbild.png", f"{kamera}.png"]
    kandidaten += [b for b in bilder if isinstance(b, str) and kamera in b
                   and not any(t in b for t in _KEINE_UNTERLAGE + _UNTERLAGE_ZULETZT)]
    kandidaten += [n for n in eigene if "beauty" in n and n not in spaet]
    kandidaten += [n for n in eigene if n not in spaet]
    kandidaten += spaet
    for kandidat in kandidaten:
        try:
            return artefakt(ablage, job, kandidat)
        except KnotenwegError:
            continue
    return None


def _bilder_im_auftrag(ablage, ueber) -> list[str] | None:
    """Die flachen PNG-Namen im Auftrag der Unterlage — für den Satz, wenn nichts passt."""
    treffer = UNTERLAGE_AUS_AUFTRAG.match(ueber) if isinstance(ueber, str) else None
    if treffer is None or ablage is None:
        return None
    try:
        ordner = auftragsordner(ablage, treffer.group(1))
    except KnotenwegError:
        return None
    return sorted(d.name for d in ordner.glob("*.png") if not d.name.startswith("."))


def lies_skizzen_anlage(felder: dict) -> dict | None:
    """Die Anlage aus den Feldern des Formulars — ``None``, wenn keine Skizze mitkam.

    Nur die Form; ob sie gilt, prüft :func:`lege_an`. ``felder`` wie von :func:`teile_formular`.
    """
    png = (felder.get(FELD_SKIZZE_PNG) or (None, None))[1]
    if png is None:
        return None
    try:
        info = json.loads((felder.get(FELD_SKIZZE_INFO) or (None, b"{}"))[1] or b"{}")
    except ValueError as fehler:
        raise KnotenwegError(f"Die Angaben zur Skizze sind kein JSON: {fehler}") from fehler
    if not isinstance(info, dict):
        raise KnotenwegError("Die Angaben zur Skizze sind kein JSON-Objekt.")
    return {"png": png, "unterlage": (felder.get(FELD_UNTERLAGE_PNG) or (None, None))[1],
            "ueber": info.get("ueber"), "bemerkung": info.get("bemerkung")}


def _anlage_statt_zwilling(ablage, szene: dict, mappe_pfad, anlage: dict) -> dict | None:
    """Die geprüfte Anlage einer Skizze aus einer Mappe am Mac — oder ``None``: Der Zwilling hier
    hat sie schon (dann gilt der alte Weg, unverändert).

    Geprüft wird, **ohne dem Absender etwas zu glauben**: der Name (A1, relativ, ohne ``..``), die
    Skizze und eine mitgeschickte Unterlage sind PNG bis :data:`SKIZZE_ANLAGE_HOECHSTENS` und
    :data:`SKIZZE_KANTE_HOECHSTENS`, die Unterlage ist ebenfalls ein relativer Name auf ``.png``,
    und es gibt eine Anweisung (wie :func:`_pruefe_skizze`). Kam die Unterlage nicht mit, wird sie
    hier gesucht (:func:`unterlage_in_der_ablage`); fehlt sie auch hier, wird abgewiesen.
    """
    roh = szene.get("skizze") if isinstance(szene.get("skizze"), dict) else {}
    name = roh.get("name")
    mangel = kosmo_szene.skizzenname_mangel(name)
    if mangel is not None:
        raise KnotenwegError(f"Die Skizze der Bestellung ist abgewiesen: {mangel}")
    if mappe_pfad:
        try:
            im_zwilling = any(s["name"] == name for s in skizzen_der_mappe(
                projekt.oeffne(mappe_pfad)["projekt"], hoechstens=10**6))
        except projekt.ProjektError:
            im_zwilling = False
        if im_zwilling:
            return None
    _png_kante(anlage.get("png"), "Die mitgeschickte Skizze")
    ueber = anlage.get("ueber")
    if ueber is not None:
        if not isinstance(ueber, str) or not ueber.lower().endswith(".png"):
            raise KnotenwegError(f"Die Unterlage der Skizze ist {ueber!r} — erwartet ist der Name "
                                 f"eines PNG-Bilds in der Mappe.")
        mangel = kosmo_szene.skizzenname_mangel(ueber)
        if mangel is not None:
            raise KnotenwegError(f"Die Unterlage der Skizze ist abgewiesen: "
                                 f"{mangel.replace('Der Name der Skizze', 'Ihr Name')}")
    unterlage = anlage.get("unterlage")
    if unterlage is not None and ueber is None:
        raise KnotenwegError("Eine Unterlage kam mit, aber die Skizze nennt kein Bild, auf das sie "
                             "gezeichnet wurde.")
    if unterlage is not None:
        _png_kante(unterlage, "Die mitgeschickte Unterlage")
    elif ueber is not None:
        unterlage = unterlage_in_der_ablage(ablage, ueber)
        if unterlage is None:
            vorhanden = _bilder_im_auftrag(ablage, ueber)
            if vorhanden is not None:
                # DER AUFTRAG IST DA, NUR DAS BILD NICHT (Ergebnis 368 (5)): genau sagen, was fehlt.
                raise KnotenwegError(SATZ_UNTERLAGE_NICHT_IM_AUFTRAG.format(
                    name=name, ueber=ueber, datei=ueber.rsplit("/", 1)[-1],
                    vorhanden=", ".join(vorhanden[:12]) or "keine Bilder"))
            raise KnotenwegError(SATZ_UNTERLAGE_FEHLT.format(name=name, ueber=ueber))
        if unterlage.stat().st_size > SKIZZE_ANLAGE_HOECHSTENS:
            raise KnotenwegError("Die Unterlage im Auftrag ist zu gross für eine Skizze.", 413)
        with unterlage.open("rb") as datei:
            _png_kante(datei.read(64), "Die Unterlage im Auftrag")
    bemerkung = anlage.get("bemerkung")
    if bemerkung is not None and (not isinstance(bemerkung, str)
                                  or len(bemerkung) > SKIZZE_BEMERKUNG_HOECHSTENS):
        raise KnotenwegError(f"Die Bemerkung der Skizze ist kein Text bis "
                             f"{SKIZZE_BEMERKUNG_HOECHSTENS} Zeichen.")
    stil = szene.get("style") if isinstance(szene.get("style"), dict) else {}
    if not any(isinstance(t, str) and t.strip()
               for t in (roh.get("anweisung"), projekt.bemerkung_ohne_name(bemerkung),
                         stil.get("prompt"))):
        raise KnotenwegError(SATZ_SKIZZE_OHNE_ANWEISUNG)
    return {"name": name, "png": anlage["png"], "unterlage": unterlage, "ueber": ueber,
            "bemerkung": bemerkung, "standpunkt": standpunkt_der_unterlage(ueber)}


def _schreibe_anlage(ordner: Path, anlage: dict) -> None:
    """Die geprüfte Anlage in den Auftrag: Skizze, Unterlage (falls da), ``anlage.json``."""
    ziel = ordner / ORDNER_SKIZZE_AM_MAC
    ziel.mkdir()
    (ziel / DATEI_ANLAGE_SKIZZE).write_bytes(bytes(anlage["png"]))
    unterlage = anlage.get("unterlage")
    if isinstance(unterlage, Path):
        shutil.copyfile(unterlage, ziel / DATEI_ANLAGE_UNTERLAGE)
    elif unterlage is not None:
        (ziel / DATEI_ANLAGE_UNTERLAGE).write_bytes(bytes(unterlage))
    _schreibe(ziel / DATEI_ANLAGE, {
        "name": anlage["name"], "ueber": anlage.get("ueber"),
        "bemerkung": anlage.get("bemerkung"),
        "unterlage": DATEI_ANLAGE_UNTERLAGE if unterlage is not None else None,
        "standpunkt": anlage.get("standpunkt")})


def anlage_des_auftrags(ordner) -> dict | None:
    """Die Angaben der mitgereisten Skizze (``anlage.json``) — ``None`` ohne Anlage."""
    try:
        daten = json.loads((Path(ordner) / ORDNER_SKIZZE_AM_MAC / DATEI_ANLAGE).read_text(
            encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return daten if isinstance(daten, dict) else None


#: Die Aufloesung einer Bestellung ohne ``render.resolution`` — dieselbe Vorgabe wie beim Lesen
#: der Szene (``kosmo_szene``: «es gilt 1600x1000»).
AUFLOESUNG_VORGABE = (1600, 1000)


def aufloesung_der_bestellung(ordner) -> dict:
    """``{"aufloesung": breite, "hoehe": hoehe}`` aus ``render.resolution`` der Szene im Auftrag —
    sonst :data:`AUFLOESUNG_VORGABE`. Nur ganze Zahlen von 16 bis 8192, sonst die Vorgabe."""
    try:
        szene = json.loads((Path(ordner) / bruecke.DATEI_SZENE).read_text(encoding="utf-8"))
        roh = ((szene.get("render") or {}).get("resolution")) if isinstance(szene, dict) else None
        b, h = (int(roh[0]), int(roh[1])) if isinstance(roh, (list, tuple)) and len(roh) == 2 \
            else AUFLOESUNG_VORGABE
    except (OSError, ValueError, TypeError, AttributeError):
        b, h = AUFLOESUNG_VORGABE
    if not (16 <= b <= SKIZZE_KANTE_HOECHSTENS and 16 <= h <= SKIZZE_KANTE_HOECHSTENS):
        b, h = AUFLOESUNG_VORGABE
    return {"aufloesung": b, "hoehe": h}


def mappe_aus_anlage(ordner, *, up_axis: str = "Y", _lege_an=None) -> Path | None:
    """Die Mappe für eine mitgereiste Skizze, im Auftrag gebaut — ``None`` ohne Anlage.

    Aus dem Modell des Auftrags (:func:`aiimaging.arbeitsgang.lege_an`, wie «Datei laden …»), mit
    der Skizze unter ihrem Namen, der Unterlage unter ``ueber`` als Bild der Mappe — samt dem
    Standpunkt aus :func:`standpunkt_der_unterlage` unter ``herkunft.standpunkt``, damit
    :func:`aiimaging.projekt.standpunkt_fuer_skizze` ihn findet (Entscheid 96b) — und der
    Bemerkung. Danach ist es eine Mappe wie jede am Heim-PC. Schon gebaut: dieselbe.

    ``up_axis``: die Hochachse, unter der der Heim-PC die glb dieses Auftrags rechnet (der
    Abholer: die des Auftrags, sonst ``ANGENOMMENE_HOCHACHSE`` «Y» — dieselbe Annahme wie für das
    Grundbild, auf das gezeichnet wurde). Für eine IFC nicht gesetzt: Sie trägt sie selbst.

    Raises:
        KnotenwegError: Name oder Unterlage verlassen die Mappe (A1, nochmals geprüft), oder das
            Modell des Auftrags fehlt.
    """
    from . import arbeitsgang
    ordner = Path(ordner)
    angaben = anlage_des_auftrags(ordner)
    if angaben is None:
        return None
    wurzel = ordner / ORDNER_SKIZZENMAPPE
    if (wurzel / projekt.PROJEKTDATEI).is_file():
        return wurzel
    name, ueber = angaben.get("name"), angaben.get("ueber")
    for wert in (name, ueber):
        if wert is not None and kosmo_szene.skizzenname_mangel(wert) is not None:
            raise KnotenwegError(f"Die mitgereiste Skizze ist abgewiesen: "
                                 f"{kosmo_szene.skizzenname_mangel(wert)}")
    modell = next((ordner / n for n in (bruecke.DATEI_MODELL, bruecke.DATEI_MODELL_IFC)
                   if (ordner / n).is_file()), None)
    if modell is None:
        raise KnotenwegError("Für die mitgereiste Skizze fehlt das Modell des Auftrags.")
    # NORMALISIERT (Generalprobe 373, S11): Die Annahme des Abholers heisst «Y_UP»; die Mappe
    # liest die Einstellung roh, und nicht jeder Leser normalisiert (Fehlerklasse 08.10.2026).
    try:
        achse = contracts.normalize_up_axis(up_axis)
    except contracts.ContractError as fehler:
        raise KnotenwegError(f"Die Hochachse für die mitgereiste Skizze ist unbrauchbar: "
                             f"{fehler}") from fehler
    einstellungen = {"up_axis": achse} if modell.name == bruecke.DATEI_MODELL else {}
    # DIE AUFLOESUNG DER BESTELLUNG (Ergebnis 368): ohne sie rechnete die Mappe mit der Vorgabe
    # 512 x 512. Das Seitenverhaeltnis kommt danach aus der Unterlage
    # (`arbeitsgang.format_der_skizze`), die lange Seite von hier.
    einstellungen.update(aufloesung_der_bestellung(ordner))
    (_lege_an or arbeitsgang.lege_an)(wurzel, modell, name="Skizze aus der Mappe am Mac",
                                      einstellungen=einstellungen)
    p = projekt.oeffne(wurzel)["projekt"]

    def _hinein(weg: str, quelle: Path) -> None:
        ziel = (wurzel / weg).resolve()
        if not ziel.is_relative_to(wurzel.resolve()):
            raise KnotenwegError(f"{weg!r} verlässt die Mappe.")
        ziel.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(quelle, ziel)

    anlage = ordner / ORDNER_SKIZZE_AM_MAC
    _hinein(name, anlage / DATEI_ANLAGE_SKIZZE)
    if ueber is not None and angaben.get("unterlage"):
        _hinein(ueber, anlage / DATEI_ANLAGE_UNTERLAGE)
        herkunft = ({"standpunkt": dict(angaben["standpunkt"])}
                    if isinstance(angaben.get("standpunkt"), dict) else None)
        projekt.vermerke_bild(p, bild=ueber, schicht="ai-imaging-layer", herkunft=herkunft)
    projekt.vermerke_skizze(p, skizze=name, ueber=ueber if angaben.get("unterlage") else None,
                            bemerkung=angaben.get("bemerkung") or "")
    projekt.speichere(p, wurzel)
    return wurzel


def _pruefe_skizze(szene: dict, mappe_pfad, *, am_mac: str | None = None) -> str | None:
    """Der Name der Skizze, die die Szene bestellt — oder ``None`` ohne Skizze.

    Geprüft wird nur, was hier schon feststeht: Es gibt eine Mappe, und die Skizze steht in
    ihr (nicht verworfen). Ob sie sich rechnen lässt — Unterlage, Anweisung, Datei —, prüft
    :func:`aiimaging.arbeitsgang.rechne_skizze` am Heim-PC, mit denselben Sätzen wie auf der
    Seite. Die Form (``quelle``, ``name``) prüft :func:`aiimaging.kosmo_szene.lies_szene`;
    hier nur so weit, dass ein Name nachzuschlagen ist.
    """
    roh = szene.get("skizze")
    if roh is None:
        return None
    name = roh.get("name") if isinstance(roh, dict) else None
    if not isinstance(name, str) or not name.strip():
        raise KnotenwegError(f"Die Skizze der Bestellung nennt keine Datei: {roh!r}.")
    # AUFLAGE A1 (Integrator, 15.10.2026): ein relativer Pfad IN der Mappe — schon beim Annehmen
    # geprueft, unabhaengig vom Vertrag drueben, und bevor irgendetwas nachgeschlagen wird.
    mangel = kosmo_szene.skizzenname_mangel(name)
    if mangel is not None:
        raise KnotenwegError(f"Die Skizze der Bestellung ist abgewiesen: {mangel}")
    if am_mac and not mappe_pfad:
        # MAPPE AM MAC OHNE ZWILLING HIER: «Mappe öffnen» wäre falsch — sie ist offen, am Mac.
        raise KnotenwegError(SATZ_SKIZZE_NUR_AM_MAC.format(name=name, mappe=am_mac))
    if not mappe_pfad:
        raise KnotenwegError(
            "Eine Skizze lässt sich nur aus einer offenen Mappe bestellen — dieser Auftrag "
            "kam ohne Mappe. Die Mappe auf der Visbox-Seite öffnen und neu ausführen.")
    try:
        skizzen = skizzen_der_mappe(projekt.oeffne(mappe_pfad)["projekt"], hoechstens=10**6)
    except projekt.ProjektError as fehler:
        raise KnotenwegError(f"Die Mappe liess sich nicht öffnen: {fehler}") from fehler
    eintrag = next((s for s in skizzen if s["name"] == name), None)
    if eintrag is None:
        if am_mac:
            # BEFUND F4: Die Liste des Knotens kommt aus der Mappe am Mac; fehlt die Skizze im
            # Zwilling hier, liegt sie dort — sie ist nicht verworfen, nur nie hergekommen.
            raise KnotenwegError(SATZ_SKIZZE_NUR_AM_MAC.format(name=name, mappe=am_mac))
        raise KnotenwegError(
            f"Die Skizze {name!r} steht nicht (mehr) in der Mappe «{Path(mappe_pfad).name}» — "
            f"verworfen oder nie abgelegt. Am Knoten «Skizze vom iPad» eine andere wählen.")
    # BEFUND F4 (Demolauf 24.10.2026): OHNE ANWEISUNG SCHON BEIM ANNEHMEN ABWEISEN, nicht erst nach
    # Freigabe und Lauf. Es gilt, was der Abholer nimmt (`abholer.anweisung_der_skizze`): die
    # Anweisung der Bestellung, sonst die Bemerkung der Skizze (ohne «gewünschter Name: …»), sonst
    # der Prompt der Bestellung. Fehlt alles, entstuende nichts — der Satz sagt, was zu tun ist.
    anweisung = roh.get("anweisung") if isinstance(roh, dict) else None
    stil = szene.get("style") if isinstance(szene.get("style"), dict) else {}
    if not any(isinstance(t, str) and t.strip()
               for t in (anweisung, eintrag.get("bemerkung"), stil.get("prompt"))):
        raise KnotenwegError(SATZ_SKIZZE_OHNE_ANWEISUNG)
    return name


def mappe_des_auftrags(ordner) -> Path | None:
    """Der Pfad der Mappe, den :func:`lege_an` bei einer Skizze vermerkt hat — oder ``None``.

    ``None`` heisst: Der Auftrag trägt keinen Vermerk (keine Skizze, oder er kam nicht über
    die Knotenansicht von Visbox). Ein unlesbarer Vermerk ist ebenfalls ``None`` — der
    Abholer sagt dann, dass die Mappe fehlt, statt zu raten.
    """
    datei = Path(ordner) / DATEI_MAPPE
    try:
        pfad = json.loads(datei.read_text(encoding="utf-8")).get("pfad")
    except (OSError, ValueError, AttributeError):
        return None
    return Path(pfad) if isinstance(pfad, str) and pfad else None


def lies(ablage, job_id: str) -> dict:
    """Laufzettel, und das Ergebnis dazu, sobald es daliegt — wie ``GET /jobs/{id}``."""
    ordner = auftragsordner(ablage, job_id)
    zettel = json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
    ergebnis = ordner / bruecke.DATEI_ERGEBNIS
    if ergebnis.is_file():
        zettel["result"] = json.loads(ergebnis.read_text(encoding="utf-8"))
    return zettel


def liste(ablage, hoechstens: int = 50) -> list[dict]:
    """Die jüngsten Aufträge zuerst — wie ``GET /jobs``."""
    ordner = Path(ablage)
    if not ordner.is_dir():
        return []
    saetze = []
    for d in sorted(ordner.iterdir(), reverse=True):
        zettel = d / bruecke.DATEI_LAUFZETTEL
        if d.is_dir() and kosmo_szene.ist_fremde_job_id(d.name) and zettel.is_file():
            try:
                saetze.append(json.loads(zettel.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
        if len(saetze) >= hoechstens:
            break
    return saetze


#: Die Herkunft einer Freigabe, wenn der Aufrufer keine nennt — neutral, weil
#: ``/approve`` aus der Knotenansicht wie über die API gleich aussieht (Geräteprobe der
#: HomeStation, 20.10.2026: bis dahin stand hier immer «Klick in der Knotenansicht»).
FREIGABE_DURCH_NEUTRAL = "freigegeben (/approve)"


def freigeben(ablage, job_id: str, token, *, durch: str | None = None, _uhr=None) -> dict:
    """Ein Mensch hat «Freigeben» gedrückt: wartend → in der Reihe, mit Marke.

    ``durch`` sagt, über welchen Weg die Freigabe kam, soweit der Aufrufer es **weiss**
    (der Server nennt das Gerät aus ``X-Geraet``). Ohne Angabe steht
    :data:`FREIGABE_DURCH_NEUTRAL` — nicht «Klick in der Knotenansicht», denn denselben Weg
    nimmt auch ein Aufruf über die API.

    Der Token muss der sein, den :func:`lege_an` ausgegeben hat (Vergleich in konstanter
    Zeit). Ein Auftrag, der nicht wartet, bleibt unverändert — kein stiller Zustandssprung,
    wie bei der Brücke.
    """
    ordner = auftragsordner(ablage, job_id)
    pfad = ordner / bruecke.DATEI_LAUFZETTEL
    with bruecke.laufzettel_sperre(pfad):
        return _freigeben_gesperrt(pfad, job_id, token, durch, _uhr)


def _freigeben_gesperrt(pfad, job_id, token, durch, _uhr=None) -> dict:
    zettel = json.loads(pfad.read_text(encoding="utf-8"))
    erwartet = str(zettel.get("approval_token") or "")
    if not erwartet or not hmac.compare_digest(str(token or ""), erwartet):
        raise KnotenwegError("Freigabe abgewiesen: Der Token fehlt oder passt nicht.", 403)
    if zettel.get("status") != bruecke.STATUS_AWAITING:
        return zettel
    zettel["status"] = bruecke.STATUS_QUEUED
    zettel["updated_at"] = _jetzt(_uhr)
    # ERGEBNIS 351 B5: Wartete der Auftrag an der Grenze oder Lizenz der Vollautomatik, ist dieser
    # Zustand mit dem Klick ueberholt — er bleibt nur als `vorher`, damit niemand einen frei-
    # gegebenen Lauf fuer «Grenze erreicht» haelt. Ein Klick zaehlt nicht zur Grenze (146).
    alt = zettel.get(FELD_VOLL)
    if isinstance(alt, dict) and alt.get("zustand") in (ZUSTAND_GRENZE, ZUSTAND_LIZENZ):
        zettel[FELD_VOLL] = {"zustand": ZUSTAND_VON_HAND, "am": zettel["updated_at"],
                             "vorher": alt.get("zustand"),
                             "satz": "Von Hand freigegeben — der Zustand der Vollautomatik "
                                     f"(«{alt.get('zustand')}») ist überholt; ein Klick zählt "
                                     f"nicht zu den {VOLL_GRENZE} Läufen ohne Klick je Stunde."}
    zettel[FELD_FREIGABE] = {"am": zettel["updated_at"],
                             "durch": str(durch).strip() if durch and str(durch).strip()
                             else FREIGABE_DURCH_NEUTRAL}
    # DER WARTEGRUND GEHT MIT DER FREIGABE WEG. Auf `queued` liest die Knotenansicht eine
    # Meldung als «abgeholt, zurückgestellt» — also als Wort des Abholers. Nachgestellt am
    # 24.09.2026 mit einem Satz «Freigegeben — wartet …»: Die Ansicht zeigte «zurückgestellt»,
    # obwohl niemand etwas zurückgestellt hatte. Ab hier spricht nur noch der Abholer.
    zettel.pop(bruecke.FELD_MELDUNG, None)
    _schreibe(pfad, zettel)
    return zettel


def abbrechen(ablage, job_id: str) -> dict:
    """Kooperativer Abbruch, wie bei der Brücke: Endzustände bleiben, was sie sind."""
    ordner = auftragsordner(ablage, job_id)
    pfad = ordner / bruecke.DATEI_LAUFZETTEL
    # UNTER DERSELBEN SPERRE WIE DER ABHOLER (Geraeteprobe 20.10.2026) — sonst konnte ein
    # Fortschritt, der davor gelesen hatte, `running` ueber dieses `cancelled` schreiben.
    with bruecke.laufzettel_sperre(pfad):
        zettel = json.loads(pfad.read_text(encoding="utf-8"))
        if zettel.get("status") not in ENDZUSTAENDE:
            zettel["status"] = bruecke.STATUS_CANCELLED
            zettel["updated_at"] = _jetzt()
            zettel[bruecke.FELD_MELDUNG] = "Vom Nutzer abgebrochen."
            _schreibe(pfad, zettel)
    return zettel


def artefakt(ablage, job_id: str, name: str) -> Path:
    """Eine Datei aus dem Auftragsordner — nur ein blosser Name, nichts darüber hinaus."""
    ordner = auftragsordner(ablage, job_id)
    if not name or "/" in name or "\\" in name or name.startswith("."):
        raise KnotenwegError(f"Kein Dateiname: {name!r}.", 404)
    ziel = ordner / name
    try:
        ziel.resolve().relative_to(ordner.resolve())
    except ValueError:
        raise KnotenwegError(f"Kein Dateiname: {name!r}.", 404) from None
    if not ziel.is_file():
        raise KnotenwegError(f"Im Auftrag {job_id} liegt keine Datei {name!r}.", 404)
    return ziel


#: Wie alt der letzte Puls sein darf, bevor der Abholer als «steht» gilt (Sekunden).
#:
#: **Aus dem gemessenen Takt abgeleitet** (auf-20260924-170 B3): Die HomeStation startet
#: den Abholer als systemd-Benutzertimer mit ``OnUnitInactiveSec=30s``, also 30 s nach dem
#: Ende des vorigen Durchgangs; gemessen 30,3–30,5 s zwischen zwei Pulsen. Vier Takte
#: lassen drei ausgefallene Durchgänge zu, bevor «steht» gemeldet wird. Ein langer Lauf
#: ist davon nicht betroffen: Solange ein Auftrag auf ``running`` steht, heisst es
#: «arbeitet». Bis dahin standen hier 300 s, gesetzt.
PULS_TAKT_S = 30
PULS_FRIST_S = 4 * PULS_TAKT_S

#: Die Zustände, die ``services.abholer.zustand`` annehmen kann.
ABHOLER_ZUSTAENDE = ("nie_gesehen", "arbeitet", "wartet", "laeuft_leer", "steht")


def abholer_zustand(ablage, *, _uhr=None) -> dict:
    """Was der Abholer zuletzt getan hat — aus seiner Pulsdatei und den Laufzetteln.

    ================  ==========================================================
    ``nie_gesehen``   Keine Pulsdatei. Der Abholer lief nie gegen diese Ablage —
                      oder er schaut in eine andere.
    ``arbeitet``      Ein Auftrag steht auf ``running``.
    ``steht``         Der letzte Puls ist älter als :data:`PULS_FRIST_S`.
    ``wartet``        Er läuft und hat Aufträge gesehen, die er liegenliess — der Grund
                      steht je Auftrag in ``message``.
    ``laeuft_leer``   Er läuft und hatte nichts zu tun.
    ================  ==========================================================
    """
    if ablage is None:
        return {"zustand": "nie_gesehen", "zuletzt": None, "alter_s": None,
                "frist_s": PULS_FRIST_S, "grund": "Keine Ablage eingestellt."}
    ordner = Path(ablage)
    jetzt = (_uhr or time.time)()
    try:
        puls = json.loads((ordner / "abholer-puls.json").read_text(encoding="utf-8"))
        zuletzt = float(puls["zuletzt_epoch_s"])
    except (OSError, ValueError, KeyError, TypeError):
        return {"zustand": "nie_gesehen", "zuletzt": None, "alter_s": None,
                "frist_s": PULS_FRIST_S,
                "grund": ("Kein Lebenszeichen des Abholers in dieser Ablage. Entweder läuft "
                          "er nicht, oder er schaut in eine andere Ablage.")}
    alter = round(max(0.0, jetzt - zuletzt), 1)
    laeuft = bool(bruecke.offene_auftraege(ordner, nur_status=(bruecke.STATUS_RUNNING,))) \
        if ordner.is_dir() else False
    if laeuft:
        zustand = "arbeitet"
    elif alter > PULS_FRIST_S:
        zustand = "steht"
    elif puls.get("liegengelassen"):
        zustand = "wartet"
    else:
        zustand = "laeuft_leer"
    return {"zustand": zustand, "zuletzt": puls.get("zuletzt"), "alter_s": alter,
            "frist_s": PULS_FRIST_S,
            "letzter_durchgang": {k: puls.get(k) for k in
                                  ("gesehen", "verarbeitet", "liegengelassen", "fehler",
                                   "waisen")},
            "grund": ""}


def gesundheit(ablage, *, _uhr=None) -> dict:
    """Die Antwort auf ``/health`` — dieselben Felder wie die Brücke, nichts vorgetäuscht.

    Sprach-, Einbettungs- und Sprachmodell-Dienste gibt es in Visbox nicht; sie stehen auf
    ``False``. Eine Grafikkarten-Angabe fehlt, wie bei der Brücke ohne echte Abfrage.

    **Neu seit dem 24.09.2026 (B161/B8):** ``abholer`` — ob der Abholer läuft, leer ist,
    wartet, arbeitet oder steht (:func:`abholer_zustand`). Neben ``services`` und nicht
    darin: Ihr Vertrag (``BridgeHealth``, ``bridge-api.ts``) führt dort nur Wahrheitswerte,
    und ein Block dazwischen wäre ein Formbruch. Als Nachbar von ``gpu`` liest ihr
    nicht-strenges Schema ihn als unbekannt und lässt die Antwort gültig.
    """
    return {
        "ok": True,
        "version": "1.0.0-visbox",
        # «jobstore» heisst hier: Es ist eine Ablage eingestellt. Der Ordner selbst entsteht
        # mit dem ersten Auftrag — vorher leer anzulegen hiesse, in eine Mappe zu schreiben,
        # die nur angesehen wurde.
        "services": {"jobstore": ablage is not None,
                     "ollama": False, "stt": False,
                     "tts": False, "embed": False},
        "abholer": abholer_zustand(ablage, _uhr=_uhr),
    }


def glb_der_mappe(ordner) -> Path | None:
    """Nur der Pfad der glb einer Mappe — ``None``, wenn sie keine hat.

    Für ``GET /knoten/modell.glb`` (20.10.2026): :func:`mappe_fuer_knoten` liest dafür
    Hüllbox und Standpunkte aus der ganzen Datei, die hier nur ausgeliefert wird. Dieselbe
    Herkunft (``import.glb`` der Projektdatei), ohne den Rest.
    """
    einfuhr = projekt.oeffne(ordner)["projekt"].get("import") or {}
    glb = projekt.loese_pfad(einfuhr.get("glb"), ordner) if einfuhr.get("glb") else None
    return Path(glb) if glb is not None and Path(glb).is_file() else None


def mappe_fuer_knoten(ordner) -> dict:
    """Was die Knotenansicht über das Modell der offenen Mappe wissen muss.

    Returns:
        ``{name, glb, huellbox_m, hochachse, grund, huellbox_vermerk, mappe, herkunft,
        fassung, bauteile, standpunkte, glb_bytes}`` — ``glb`` ist der
        Pfad der glb-Datei der Mappe oder ``None``; ``huellbox_m`` die Hüllbox der gebauten
        Substanz in Weltkoordinaten (Meter, Z oben) oder ``None``; ``grund`` sagt einem
        Menschen, warum etwas fehlt, und ist leer, wenn nichts fehlt.
    """
    from aiimaging.modellladen import herkunft_von

    auf = projekt.oeffne(ordner)
    p = auf["projekt"]
    einfuhr = p.get("import") or {}
    glb = projekt.loese_pfad(einfuhr.get("glb"), ordner) if einfuhr.get("glb") else None
    antwort = {"name": p.get("name"), "glb": str(glb) if glb else None,
               "huellbox_m": None, "hochachse": einfuhr.get("hochachse"), "grund": "",
               "huellbox_vermerk": "",
               # FUER DEN MODELL-KNOTEN (Entscheid 90, Blatt 21): «Szene: N Bauteile (aus
               # IFC)», die Mappe und ihre Fassung. `bauteile` ist die Zahl der Teile mit
               # Geometrie in der glb (ein IFC-Bauteil ist dort ein Teil) — `None`, solange
               # die glb nicht gelesen ist.
               "mappe": Path(ordner).name,
               "herkunft": herkunft_von((p.get("modell") or {}).get("pfad")),
               "fassung": projekt.modellfassung(p),
               "bauteile": None,
               # ENTSCHEID 95 (14.10.2026, Blatt 25): die Skizzen der Mappe fuer den Knoten
               # «Skizze vom iPad», die neueste zuerst — gelesen aus der Mappe, ohne glb.
               "skizzen": skizzen_der_mappe(p),
               # VIDEO-BEFUND L4-4 (21.10.2026): die von Hand gesetzten Standpunkte der Bilder
               # als «gesicherte Blicke» fuer den Knoten «Kamera» — gelesen aus der Mappe, ohne glb.
               "blicke": blicke_der_mappe(p),
               # ENTSCHEID 92: die drei Standpunkte des Abholers vorab (`heim_standpunkte`).
               "standpunkte": None,
               # A0004: wurde die glb der Mappe nach dem letzten Speichern von Hand ersetzt?
               # `satz` ist nur dann gefuellt; der Modell-Knoten zeigt ihn.
               "glb_stand": projekt.glb_stand(p, ordner),
               # DER FINGERABDRUCK DER AUSKUNFT (A0063, Befund 7 des Demolaufs 31.10.2026):
               # die Grösse genau der glb, aus der Bauteile, Hüllbox und Standpunkte gelesen
               # sind. Die Mappe am Mac legt diese Antwort in `mappe.json` ab und liefert sie
               # danach selbst aus; liegt daneben eine andere `modell.glb`, erkennt sie daran,
               # dass die Auskunft zu einem anderen Modell gehört. `None` ohne glb.
               "glb_bytes": None}
    if glb is None or not Path(glb).is_file():
        antwort["glb"] = None
        # SEIT ENTSCHEID 90 sagt der Satz, wo es weitergeht: am Modell-Knoten selbst.
        antwort["grund"] = (f"Die Mappe «{Path(ordner).name}» hat noch kein Modell — "
                            "«Datei laden …» holt eines herein.")
        return antwort
    achse = einfuhr.get("hochachse") if einfuhr.get("hochachse_steht_fest") else "Y"
    antwort["glb_bytes"] = Path(glb).stat().st_size
    try:
        box = glbbox.bauwerksbox(glb, up_axis=achse or "Y")
    except glbbox.GlbError as fehler:
        antwort["grund"] = f"Die Hüllbox liess sich nicht lesen: {fehler}"
        return antwort
    antwort["bauteile"] = box.get("n_knoten")
    antwort["huellbox_m"] = box.get("bbox_bauwerk") or box.get("bbox_szene")
    # DER VERMERK DER BOX IST FACHSPRACHE (welche Regel das Gelaende getrennt hat) — er
    # geht mit, aber nicht in `grund`, den die Seite einem Menschen zeigt.
    antwort["huellbox_vermerk"] = box.get("note") or ""
    antwort["standpunkte"] = heim_standpunkte(glb, achse or "Y", szene_box=box.get("bbox_szene"))
    return antwort


#: Die Namen der drei festen Richtungen des Abholers (:data:`aiimaging.abholer.AUTO_RICHTUNGEN`)
#: für einen Menschen — so stehen sie am Auto-Kamera-Knoten.
#: Seit dem 20.10.2026 alle zwölf (Knoten «Kamera»: Chips N, NO, O, SO, S, SW, W, NW und die
#: vier übrigen Diagonalen) — die Zuordnung der Chips steht im Bauplan (F2).
RICHTUNGSNAMEN = {"n": ("Nord", "frontal"), "e": ("Ost", "frontal"),
                  "s": ("Süd", "frontal"), "w": ("West", "frontal"),
                  "nNE": ("Nordost", "über Eck"), "nNW": ("Nordwest", "über Eck"),
                  "sSE": ("Südost", "über Eck"), "sSW": ("Südwest", "über Eck"),
                  "eEN": ("Ost-Nordost", "über Eck"), "eES": ("Ost-Südost", "über Eck"),
                  "wWS": ("West-Südwest", "über Eck"), "wWN": ("West-Nordwest", "über Eck")}

#: Das Seitenverhältnis, mit dem die Knotenansicht bestellt, wenn am Render-Knoten keine
#: Auflösung gewählt ist (1600 × 1000, `vis-jobs.ts`). Der Abholer rechnet die Kamera mit dem
#: Seitenverhältnis des Laufs; eine andere gewählte Auflösung verschiebt den Abstand etwas.
SEITENVERHAELTNIS_VORGABE = 1600 / 1000


#: Welche Seitenverhältnisse ``GET /knoten/standpunkte`` annimmt — dieselben Kanten wie eine
#: Bestellung (``kosmo_szene.REGEL_KANTE`` lässt 16 … 65'536 zu), grob begrenzt.
SEITENVERHAELTNIS_GRENZEN = (0.05, 20.0)


def heim_standpunkte(glb, up_axis: str = "Y", *, szene_box=None, kameras_auto=None,
                     seitenverhaeltnis=None) -> dict:
    """Die drei Standpunkte, die der Abholer ohne mitgeschickte Kameras rechnet — VORAB.

    **Anlass (Owner-Entscheid 92, 14.10.2026, Blatt 23):** Der Auto-Kamera-Knoten in Visbox
    war leer («Keine Geometrie im Modell — nichts abzuleiten»), obwohl der Heim-PC für jedes
    Bild drei feste Richtungen rechnet. Knoten und Heim-PC sollen dasselbe zeigen.

    **Dieselbe Rechnung, nicht eine zweite:** :data:`aiimaging.abholer.AUTO_RICHTUNGEN`, die
    Box wie ``abholer._rahmung_fuer`` (nach dem Bauwerk, :func:`aiimaging.glbbox.rahmungsbox`,
    sonst die Szene), der Ausschnitt wie ``abholer._ausschnitt_ohne_box``, und
    :func:`aiimaging.kameras.kamerasatz` — genau der Aufruf des Blender-Vorlaufs.

    **Was der Heim-PC danach noch tut** und hier nicht geht: Er zieht eine verdeckte Kamera
    zurück (``kameras.ziehe_bis_frei``, braucht die Szene in Blender). Der Abstand kann dort
    also grösser werden; Richtung und Blickziel bleiben.

    **Was das NICHT ist:** eine Bestellung. Der Auftrag trägt weiter ``cameras: "auto"``, und
    der Heim-PC rechnet diese drei selbst — mit dem Objektiv-Shift, den eine mitgeschickte
    Kamera nicht tragen kann (``CameraSpec`` kennt keinen Shift).

    **Seit dem 20.10.2026 mit den Parametern des Knotens «Kamera»** (``kameras_auto``, die
    Form aus :func:`aiimaging.kosmo_szene.kameras_auto_aus_szene`): Richtungen, Augenhöhe,
    Brennweite, «Haus füllt» oder fester Abstand, Perspektive — dieselben Werte, mit denen
    der Abholer rechnet (``abholer.kamerawerte_des_auftrags``). Ohne: die drei Richtungen des
    Abholers mit den Vorgaben, wie bisher.

    **Seit auf-20261020-292 (Befund B4) mit dem Seitenverhältnis des Auftrags**
    (``seitenverhaeltnis`` = Breite/Höhe der bestellten Auflösung). Bis dahin rechnete
    dieser Weg immer mit :data:`SEITENVERHAELTNIS_VORGABE`, der Heim-PC aber mit dem des
    Laufs — bei 960 × 592 lag das Auge 1,06 m daneben. Ohne Angabe gilt weiter die Vorgabe.

    Returns:
        ``{standpunkte: [{kuerzel, name, art, abstand_m, auge, blick_auf, shift_y,
        vollstaendig, begruendung}], satz, seitenverhaeltnis}`` — Weltkoordinaten in Metern, Z oben. Leer mit ``satz``, wenn
        sich keine Box lesen liess. Nie eine Ausnahme: Ein Knoten ohne Vorschau ist kein Grund,
        die Mappe nicht zu zeigen.
    """
    from . import abholer, kameras  # spät: nur, wer die Mappe fragt, braucht sie

    rahmung = glbbox.rahmungsbox(glb, up_axis=up_axis)
    box = rahmung.get("box") or szene_box
    if box is None:
        # OHNE BAUWERKSBOX rahmt der Vorlauf nach allen Netzen der Szene — hier dieselbe Box
        # aus der glb, ohne Blender.
        try:
            box = glbbox.bauwerksbox(glb, up_axis=up_axis).get("bbox_szene")
        except (glbbox.GlbError, OSError, ValueError):
            box = None
    if box is None:
        return {"standpunkte": [], "satz": "Ohne lesbare Hüllbox kein Vorschlag — der Heim-PC "
                                           "rechnet die drei Richtungen trotzdem selbst."}
    verhaeltnis = (float(seitenverhaeltnis) if seitenverhaeltnis is not None
                   else SEITENVERHAELTNIS_VORGABE)
    werte = abholer.kamerawerte_des_auftrags(
        {"kameras_auto": kameras_auto}, auto_richtungen=abholer.AUTO_RICHTUNGEN,
        brennweite_mm=None, kamera_modus=kameras.MODUS_SHIFT, deckungsgrad=None,
        augenhoehe=None)
    zusatz = {name: wert for name, wert in (
        ("brennweite_mm", werte["brennweite_mm"]), ("modus", werte["kamera_modus"]),
        ("deckungsgrad", werte["deckungsgrad"]), ("augenhoehe_m", werte["augenhoehe"]),
        ("abstand_fest_m", werte["abstand_fest_m"])) if wert is not None}
    # EIN SITUATIONSMODELL AUS DER VOGELSCHAU (24.10.2026) — dieselbe Regel wie der Abholer
    # (`abholer.vogelschau_der_auto_kameras`), damit die Kegel zeigen, was gerechnet wird.
    if abholer.VOGELSCHAU_AUTO:
        vogel = abholer.vogelschau_der_auto_kameras(
            glb, up_axis, werte["richtungen"], brennweite_mm=werte["brennweite_mm"],
            seitenverhaeltnis=verhaeltnis, szene_box=szene_box)
        if vogel is not None:
            aus = []
            for a in vogel["aufgaben"]:
                richtung = a["vogelschau"]["richtung"]
                name = RICHTUNGSNAMEN.get(richtung, (richtung, ""))[0]
                aus.append({"kuerzel": a["kuerzel"], "name": f"Vogelschau {name}",
                            "art": "von oben", "abstand_m": round(a["vogelschau"]["abstand_m"], 1),
                            "auge": [round(float(v), 3) for v in a["auge"]],
                            "blick_auf": [round(float(v), 3) for v in a["blick_auf"]],
                            "shift_y": 0.0, "brennweite_mm": float(a["brennweite_mm"]),
                            "vollstaendig": True, "begruendung": a["vogelschau"]["satz"]})
            return {"standpunkte": aus,
                    "satz": ("Situationsmodell — der Heim-PC rechnet die Richtungen aus der "
                             "Vogelschau. Vorschau."),
                    "seitenverhaeltnis": round(verhaeltnis, 6)}
    try:
        satz = kameras.kamerasatz(
            box, kuerzel=list(werte["richtungen"]),
            seitenverhaeltnis=verhaeltnis,
            ausschnitt=bool(rahmung.get("box") or rahmung.get("szene_ist_bauwerk")),
            **zusatz)
    except ValueError as fehler:
        return {"standpunkte": [], "satz": f"Kein Vorschlag aus dieser Hüllbox: {fehler}"}
    aus = []
    for k in satz["kameras"]:
        name, art = RICHTUNGSNAMEN.get(k["kuerzel"], (k["kuerzel"], ""))
        aus.append({"kuerzel": k["kuerzel"], "name": name, "art": art,
                    "abstand_m": round(float(k["abstand_m"]), 1),
                    "auge": [round(float(v), 3) for v in k["auge"]],
                    "blick_auf": [round(float(v), 3) for v in k["blick_auf"]],
                    "shift_y": round(float(k["shift_y"]), 5),
                    "brennweite_mm": float(k["brennweite_mm"]),
                    "vollstaendig": bool(k["vollstaendig"]),
                    "begruendung": str(k.get("begruendung") or "")})
    nach = "dem Bauwerk" if rahmung.get("box") else "der ganzen Szene"
    return {"standpunkte": aus,
            "satz": f"Rechnet der Heim-PC aus der Hüllbox ({nach}) — Vorschau.",
            "seitenverhaeltnis": round(verhaeltnis, 6)}


def standpunkte_abfrage(ordner, frage: dict) -> dict:
    """``GET /knoten/standpunkte?richtungen=s,sSE&augenhoehe=1.7&brennweite=35&fuellt=0.7``
    (oder ``abstand=40`` statt ``fuellt``, dazu ``perspektive=senkrecht|frei``) — die Kegel
    des Knotens «Kamera», mit denselben Parametern gerechnet wie der Auftrag.

    **Die Auflösung des Auftrags** (auf-20261020-292, B4): ``aufloesung=960x600`` (oder
    ``breite=960&hoehe=600``, oder ``seitenverhaeltnis=1.6``) — ohne Angabe 1600 × 1000.
    Das Seitenverhältnis geht in den Bildwinkel und damit in den Abstand ein.

    Geprüft wird mit derselben Funktion wie die Bestellung
    (:func:`aiimaging.kosmo_szene.kameras_auto_aus_szene`) — eine zweite Prüfung liefe
    auseinander. ``frage`` ist ``parse_qs``-Form (Listen) oder einfache Werte.

    Returns:
        ``{standpunkte, satz, kameras_auto}`` — ``kameras_auto`` mit den Vorgaben, wie
        gerechnet.

    Raises:
        KnotenwegError: 400 bei einem Parameter, der nicht stimmt (mit dem Satz der
            Prüfung), 404 ohne Modell in der Mappe.
    """
    from . import kosmo_szene  # spät: wie heim_standpunkte

    def wert(name):
        roh = (frage or {}).get(name)
        if isinstance(roh, (list, tuple)):
            roh = roh[0] if roh else None
        return roh if roh not in ("", None) else None

    def zahl(name):
        roh = wert(name)
        if roh is None:
            return None
        try:
            return float(roh)
        except (TypeError, ValueError):
            return roh                    # die Pruefung meldet es mit Satz

    bestellt: dict = {}
    richtungen = wert("richtungen")
    bestellt["richtungen"] = ([r for r in str(richtungen).split(",") if r]
                              if richtungen is not None else list(abholer_richtungen()))
    for name, feld in (("augenhoehe", "augenhoehe_m"), ("brennweite", "brennweite_mm")):
        if zahl(name) is not None:
            bestellt[feld] = zahl(name)
    if "brennweite_mm" in bestellt and isinstance(bestellt["brennweite_mm"], float) \
            and bestellt["brennweite_mm"].is_integer():
        bestellt["brennweite_mm"] = int(bestellt["brennweite_mm"])
    if zahl("abstand") is not None and zahl("fuellt") is not None:
        raise KnotenwegError("Entweder «fuellt» (Haus füllt) oder «abstand» (fest in m), "
                             "nicht beides.", 400)
    if zahl("abstand") is not None:
        bestellt["abstand"] = {"art": "fest", "meter": zahl("abstand")}
    elif zahl("fuellt") is not None:
        bestellt["abstand"] = {"art": "auto", "fuellt": zahl("fuellt")}
    if wert("perspektive") is not None:
        bestellt["perspektive"] = wert("perspektive")
    maengel: list = []
    gelesen = kosmo_szene.kameras_auto_aus_szene(bestellt, maengel=maengel)
    if maengel:
        raise KnotenwegError(" ".join(maengel), 400)
    verhaeltnis = _seitenverhaeltnis_der_frage(wert, zahl)
    auf = projekt.oeffne(ordner)["projekt"]
    einfuhr = auf.get("import") or {}
    glb = glb_der_mappe(ordner)
    if glb is None:
        raise KnotenwegError(f"Die Mappe «{Path(ordner).name}» hat noch kein Modell.", 404)
    achse = einfuhr.get("hochachse") if einfuhr.get("hochachse_steht_fest") else "Y"
    antwort = heim_standpunkte(glb, achse or "Y", kameras_auto=gelesen,
                               seitenverhaeltnis=verhaeltnis)
    antwort["kameras_auto"] = gelesen
    return antwort


def _seitenverhaeltnis_der_frage(wert, zahl) -> float | None:
    """Breite/Höhe aus ``aufloesung=BxH``, ``breite``+``hoehe`` oder ``seitenverhaeltnis``.

    ``None`` ohne Angabe (dann die Vorgabe). Raises :class:`KnotenwegError` 400 mit Satz.
    """
    import math  # noqa: PLC0415
    angaben = [n for n in ("aufloesung", "seitenverhaeltnis") if wert(n) is not None]
    if wert("breite") is not None or wert("hoehe") is not None:
        angaben.append("breite/hoehe")
    if len(angaben) > 1:
        raise KnotenwegError(f"Nur eine Angabe zur Bildgrösse: {', '.join(angaben)}.", 400)
    roh = None
    if wert("aufloesung") is not None:
        teile = str(wert("aufloesung")).lower().replace("×", "x").split("x")
        try:
            b, h = (float(t) for t in teile)
        except (TypeError, ValueError):
            raise KnotenwegError(f"«aufloesung» ist {wert('aufloesung')!r} — erwartet "
                                 f"Breite x Höhe, etwa 960x600.", 400) from None
        roh = b / h if h > 0 and b > 0 else float("nan")
    elif angaben == ["breite/hoehe"]:
        b, h = zahl("breite"), zahl("hoehe")
        if not all(isinstance(v, float) for v in (b, h)):
            raise KnotenwegError("«breite» und «hoehe» gehören zusammen und sind Zahlen.", 400)
        roh = b / h if h > 0 and b > 0 else float("nan")
    elif angaben:
        roh = zahl("seitenverhaeltnis")
        if not isinstance(roh, float):
            raise KnotenwegError(f"«seitenverhaeltnis» ist {roh!r} und keine Zahl.", 400)
    if roh is None:
        return None
    unten, oben = SEITENVERHAELTNIS_GRENZEN
    if not (math.isfinite(roh) and unten <= roh <= oben):
        raise KnotenwegError(f"Seitenverhältnis {roh} liegt nicht zwischen {unten} und "
                             f"{oben}.", 400)
    return roh


def abholer_richtungen() -> tuple:
    """Die Richtungen des Abholers ohne Bestellung (:data:`aiimaging.abholer.AUTO_RICHTUNGEN`)."""
    from . import abholer
    return tuple(abholer.AUTO_RICHTUNGEN)


#: Wie viele Skizzen der Knoten «Skizze vom iPad» zur Wahl bekommt — die neuesten.
SKIZZEN_HOECHSTENS = 24


#: Höchstens so viele Blicke stehen in der Auswahl des Knotens «Kamera».
BLICKE_HOECHSTENS = 24


def _dreier(wert) -> list[float] | None:
    if (isinstance(wert, (list, tuple)) and len(wert) == 3
            and all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
                    for v in wert)):
        return [float(v) for v in wert]
    return None


def blicke_der_mappe(p: dict, hoechstens: int = BLICKE_HOECHSTENS) -> list[dict]:
    """Die von Hand gesetzten Standpunkte der Bilder einer Mappe — für den Knoten «Kamera».

    **Anlass (Video-Befund L4-4, 21.10.2026):** Ein gesicherter Blick kam nicht im Kamera-Knoten
    an. Der Knoten bietet jetzt gesicherte Blicke als Auswahl an (Reiter «Blick»). In Visbox gibt
    es keinen Entwurf, in dem man Blicke sichert — aber jedes Bild der Mappe trägt seit dem
    15.10.2026 seinen Standpunkt (``herkunft.standpunkt``, Entscheid 96b). Wo dort **Auge und
    Blickpunkt** stehen (am Grundriss gesetzt, oder vom Bild unter einer Skizze vom iPad
    übernommen), ist das ein gewählter Blick; ein aus einer Richtung gerechneter Standpunkt
    («von Süden») ist keiner und fehlt.

    Gleiche Standpunkte stehen einmal (der neueste Eintrag gibt den Namen). Die Brennweite ist
    die des Bildes; fehlt sie, die, mit der der Heim-PC gerechnet hat
    (:data:`aiimaging.kameras.BRENNWEITE_MM`) — **geraten wird nicht**.

    Returns:
        ``[{id, name, bild, auge, blick_auf, brennweite_mm, erzeugt}]`` — ``id`` ist
        ``bild:<Bild der Mappe>`` und bleibt, auch wenn der Titel des Bildes sich ändert (der
        Knoten hält die Kennung, nicht den Namen; Wunsch von KosmoDraw, v0.1.10). Weltkoordinaten des
        Heim-PCs (Meter, Z oben), der neueste zuerst, höchstens ``hoechstens``.
    """
    from aiimaging.kameras import BRENNWEITE_MM  # spät: wie heim_standpunkte

    gesehen: dict[tuple, dict] = {}
    for b in p.get("bilder") or []:
        if not isinstance(b, dict) or not b.get("bild"):
            continue
        herkunft = b.get("herkunft") if isinstance(b.get("herkunft"), dict) else {}
        sp = herkunft.get("standpunkt") if isinstance(herkunft.get("standpunkt"), dict) else {}
        auge, ziel = _dreier(sp.get("auge")), _dreier(sp.get("blick_auf"))
        if auge is None or ziel is None:
            continue
        bw = sp.get("brennweite")
        brennweite = (float(bw) if isinstance(bw, (int, float)) and not isinstance(bw, bool)
                      and 5 <= bw <= 300 else BRENNWEITE_MM)
        titel = b.get("titel") if isinstance(b.get("titel"), str) and b.get("titel").strip() else None
        eintrag = {"id": f"bild:{b['bild']}",
                   "name": titel.strip() if titel else Path(str(b["bild"])).stem,
                   "bild": str(b["bild"]), "auge": auge, "blick_auf": ziel,
                   "brennweite_mm": brennweite, "erzeugt": b.get("erzeugt")}
        schluessel = (tuple(round(v, 3) for v in auge), tuple(round(v, 3) for v in ziel),
                      round(brennweite, 2))
        vorher = gesehen.get(schluessel)
        if vorher is None or str(eintrag["erzeugt"] or "") >= str(vorher["erzeugt"] or ""):
            gesehen[schluessel] = eintrag
    liste = sorted(gesehen.values(), key=lambda x: str(x.get("erzeugt") or ""), reverse=True)
    # Ein Name steht einmal — der ältere gleichnamige bekommt eine Nummer.
    namen: dict[str, int] = {}
    for e in liste:
        n = namen.get(e["name"], 0) + 1
        namen[e["name"]] = n
        if n > 1:
            e["name"] = f"{e['name']} ({n})"
    return liste[:max(0, int(hoechstens))]


def skizzen_der_mappe(p: dict, hoechstens: int = SKIZZEN_HOECHSTENS) -> list[dict]:
    """Die Skizzen einer Mappe für den Knoten «Skizze vom iPad» — **die neueste zuerst**.

    **Anlass (Owner-Entscheide 95/95a, 14.10.2026, Blatt 25):** Die Knotenansicht ist die
    Arbeitsfläche zum Rendern (Entscheid 94), die Skizzen vom iPad standen aber nur auf der
    Visbox-Seite. Der Knoten nimmt von selbst die neueste; eine ältere wählt man am Knoten.

    Verworfene Skizzen fehlen — sie sind nicht mehr gemeint. Jede Skizze steht einmal (die
    Mappe vermerkt dieselbe Zeichnung bei jedem Zustandswechsel neu); es gilt ihr letzter
    Eintrag. Kein Pfad: nur der Dateiname der Mappe, den ``/knoten/skizze?name=`` ausliefert.

    **Seit dem 15.10.2026 dazu** ``bemerkung`` (Entscheid 96a: sie ist die Anweisung, wenn die
    Skizze am Render-Knoten hängt — ``None``, wenn keine geschrieben ist; der Knoten sagt dann
    vorher, dass nichts gesendet wird) und ``standpunkt`` (Entscheid 96b: ``"bild"`` — das Bild
    entsteht vom Standpunkt der Unterlage; ``"mappe"`` — von dem der Mappe, siehe
    :func:`aiimaging.projekt.standpunkt_fuer_skizze`).

    Returns:
        ``[{name, titel, erzeugt, ueber, stand, bemerkung, standpunkt}]``, höchstens
        ``hoechstens``.
    """
    letzte: dict[str, dict] = {}
    for e in p.get("skizzen") or []:
        if isinstance(e, dict) and e.get("skizze"):
            letzte[str(e["skizze"])] = e
    # BEFUND F4 (Demolauf 24.10.2026): Die Bemerkung geht OHNE den angehaengten «gewünschter
    # Name: …» hinaus — der ist keine Anweisung (`projekt.bemerkung_ohne_name`); steht nur er da,
    # ist es keine Bemerkung, und der Knoten nimmt den Prompt (96c). Der Name geht nicht verloren:
    # Er ist der Titel, solange die Skizze keinen eigenen hat.
    liste = [
        {"name": name,
         "titel": e.get("titel") or projekt.gewuenschter_name(e.get("bemerkung")) or None,
         "erzeugt": e.get("erzeugt"),
         "ueber": e.get("ueber"), "stand": e.get("stand"),
         "bemerkung": projekt.bemerkung_ohne_name(e.get("bemerkung")) or None,
         "standpunkt": projekt.standpunkt_fuer_skizze(p, e.get("ueber"))["von"]}
        for name, e in letzte.items() if e.get("stand") != projekt.SKIZZE_VERWORFEN
    ]
    liste.sort(key=lambda x: str(x.get("erzeugt") or ""), reverse=True)
    return liste[:max(0, int(hoechstens))]


# ====================================================== Der Graph der Mappe (15.10.2026)
#
# ANLASS (auf-20261015-286): In Visbox lebt das Dokument der Knotenansicht nur in der Seite —
# nach dem Neuladen war der Graph weg. Er wird darum je Mappe auf dem Heim-PC gesichert und
# beim Öffnen wieder gelegt. Gesichert werden NUR die Render-Graphen (Eintraege der Art
# ``visgraph``), nicht das Modell: das kommt weiter aus der Mappe selbst.

#: Wo der Graph in der Mappe liegt.
GRAPH_DATEI = "knotengraph.json"
#: Höchstens so gross darf er sein — ein Graph aus Knoten und Linien ist Text, kein Modell.
GRAPH_HOECHSTENS = 2 * 1024 * 1024
#: Das Format, damit eine spätere Fassung eine alte Datei erkennt.
GRAPH_FORMAT = "visbox.knotengraph/v1"


def pruefe_graphen(graphen) -> list[dict]:
    """Nur eine Liste von Render-Graphen (``kind == "visgraph"``, mit ``id``, ``nodes``,
    ``edges``) — alles andere wird abgewiesen, nicht still gefiltert."""
    if not isinstance(graphen, list):
        raise KnotenwegError("Der Graph der Mappe muss eine Liste sein.")
    for g in graphen:
        if not (isinstance(g, dict) and g.get("kind") == "visgraph" and isinstance(g.get("id"), str)
                and isinstance(g.get("nodes"), list) and isinstance(g.get("edges"), list)):
            raise KnotenwegError("Im Graph der Mappe steht etwas, das kein Render-Graph ist.")
    return graphen


#: Der Stand einer Mappe ohne gesicherten Graph (§231 Nachtrag).
GRAPH_STAND_LEER = "leer"

#: Der Satz, wenn ein anderes Gerät den Graph inzwischen gesichert hat (§231 Nachtrag).
SATZ_ANDERES_GERAET = ("Ein anderes Gerät hat den Graph dieser Mappe inzwischen geändert — nicht "
                       "überschrieben. Die Knotenansicht neu laden, dann weiterarbeiten.")


def graph_stand(ordner) -> str:
    """Der Stand des gesicherten Graphen: ein Fingerabdruck der Datei (16 Zeichen), ohne Datei
    :data:`GRAPH_STAND_LEER`. Ändert ein anderes Gerät den Graph, ändert sich der Stand."""
    ziel = Path(ordner) / GRAPH_DATEI
    try:
        return hashlib.sha256(ziel.read_bytes()).hexdigest()[:16]
    except FileNotFoundError:
        return GRAPH_STAND_LEER


def schreibe_graph(ordner, graphen, stand=None) -> dict:
    """Die Render-Graphen in die Mappe schreiben (ganz ersetzt, über eine Zwischendatei).

    ``stand``: der Stand, auf dem die Seite gearbeitet hat (aus :func:`lies_graph`). Weicht er
    vom jetzigen ab, hat ein anderes Gerät inzwischen gesichert — dann wird **nicht**
    überschrieben (409, :data:`SATZ_ANDERES_GERAET`). Ohne ``stand`` wie bisher (ältere Seiten).
    """
    pruefe_graphen(graphen)
    if stand is not None and stand != graph_stand(ordner):
        raise KnotenwegError(SATZ_ANDERES_GERAET, 409)
    roh = json.dumps({"format": GRAPH_FORMAT, "graphen": graphen}, ensure_ascii=False)
    if len(roh.encode("utf-8")) > GRAPH_HOECHSTENS:
        raise KnotenwegError("Der Graph ist zu gross, um ihn zu sichern.", 413)
    ziel = Path(ordner) / GRAPH_DATEI
    zwischen = ziel.with_suffix(".json.neu")
    zwischen.write_text(roh, encoding="utf-8")
    zwischen.replace(ziel)
    return {"gesichert": len(graphen), "stand": graph_stand(ordner)}


def lies_graph(ordner) -> dict:
    """``{graphen: [...]}`` aus der Mappe — leer, wenn noch keiner gesichert ist. Eine
    unlesbare Datei heisst leer mit Satz, nicht Absturz: Der Architekt fängt dann neu an."""
    ziel = Path(ordner) / GRAPH_DATEI
    if not ziel.is_file():
        return {"graphen": [], "satz": None}
    try:
        daten = json.loads(ziel.read_text(encoding="utf-8"))
        if daten.get("format") != GRAPH_FORMAT:
            raise ValueError(f"unbekanntes Format {daten.get('format')!r}")
        return {"graphen": pruefe_graphen(daten.get("graphen")), "satz": None}
    except (OSError, ValueError, AttributeError, KnotenwegError) as fehler:
        return {"graphen": [], "satz": f"Der gesicherte Graph liess sich nicht lesen ({fehler})."}


def lies_graph_mit_stand(ordner) -> dict:
    """:func:`lies_graph` mit dem Stand, auf dem die Seite danach arbeitet (§231 Nachtrag)."""
    stand = graph_stand(ordner)
    return {**lies_graph(ordner), "stand": stand}


# ================================================ Das Formular, gestreamt (20.10.2026)
#
# ANLASS: «Der Heim-PC ist nicht erreicht: Er hat nicht rechtzeitig geantwortet.» bei jeder
# Variante. Der Server las den GANZEN Rumpf in den Speicher und zerlegte ihn mit dem E-Mail-
# Leser der Standardbibliothek — beides unter der Reihe, also mit dem ganzen Server
# angehalten; der E-Mail-Leser ist fuer grosse Teile langsam. Hier wird der Rumpf in Stuecken
# gelesen, die Datei geht unmittelbar in eine Datei neben der Ablage, und im Speicher bleiben
# nur die kleinen Felder.

#: Wie gross ein Feld ohne Datei sein darf (die Szene ist Text).
FELD_HOECHSTENS = 16 * 1024 * 1024
#: Wie gross der Kopf eines Teils sein darf.
_TEILKOPF_HOECHSTENS = 16 * 1024
#: In welchen Stuecken gelesen wird.
_STUECK = 1024 * 1024


def _grenze_aus(inhaltstyp: str) -> bytes:
    """Die Grenzmarke (``boundary``) aus ``Content-Type`` — oder ein Satz."""
    typ = str(inhaltstyp or "")
    if not typ.lower().startswith("multipart/form-data"):
        raise KnotenwegError(
            "Ein Auftrag kommt als Formular (multipart/form-data) mit Szene und Modell.")
    for teil in typ.split(";")[1:]:
        name, _, wert = teil.strip().partition("=")
        if name.strip().lower() == "boundary":
            wert = wert.strip()
            if len(wert) >= 2 and wert[0] == wert[-1] == '"':
                wert = wert[1:-1]
            if wert and len(wert) <= 200:
                return wert.encode("latin-1")
    raise KnotenwegError("Das Formular liess sich nicht zerlegen: keine Grenzmarke.")


def _kopf_des_teils(roh: bytes) -> tuple[str | None, str | None]:
    """``(name, dateiname)`` aus den Kopfzeilen eines Teils (``Content-Disposition``)."""
    name = dateiname = None
    for zeile in roh.decode("utf-8", "replace").split("\r\n"):
        feld, _, wert = zeile.partition(":")
        if feld.strip().lower() != "content-disposition":
            continue
        for stueck in wert.split(";")[1:]:
            schluessel, _, w = stueck.strip().partition("=")
            w = w.strip()
            if len(w) >= 2 and w[0] == w[-1] == '"':
                w = w[1:-1]
            if schluessel.strip().lower() == "name":
                name = w
            elif schluessel.strip().lower() == "filename":
                dateiname = w
    return name, dateiname


def teile_formular(quelle, laenge: int, inhaltstyp: str, *, ordner=None,
                   datei_felder=(), hoechstens_datei: int = MAX_MODELL_BYTES,
                   hoechstens_feld: int = FELD_HOECHSTENS) -> dict:
    """Ein ``multipart/form-data``-Rumpf aus einem Strom → ``{feld: (dateiname, inhalt)}``.

    Liest höchstens ``laenge`` Bytes aus ``quelle`` (``.read(n)``), in Stücken. Die Felder in
    ``datei_felder`` werden **unmittelbar** in eine eigene Datei in ``ordner`` geschrieben
    (Name mit Punkt vorn, damit :func:`artefakt` sie nie ausliefert); ihr ``inhalt`` ist dann
    der :class:`~pathlib.Path` dorthin. Alle anderen Felder bleiben als ``bytes`` im Speicher.

    **Wer eine Datei bekommt, räumt sie auch weg** — :func:`lege_an` verschiebt sie in den
    Auftrag; scheitert vorher etwas, löscht der Aufrufer sie (:func:`raeume_formular`). Geht
    hier etwas schief, sind die angelegten Dateien schon wieder gelöscht.

    Raises:
        KnotenwegError: kein Formular, unvollständig, oder ein Teil zu gross (413).
    """
    marke = _grenze_aus(inhaltstyp)
    trenner = b"\r\n--" + marke
    rest = [int(laenge)]
    puffer = bytearray(b"\r\n")         # damit auch die erste Marke «\r\n--» beginnt
    ende_erreicht = [False]
    felder: dict = {}
    angelegt: list[Path] = []

    def nachladen() -> bool:
        if rest[0] <= 0:
            return False
        stueck = quelle.read(min(_STUECK, rest[0]))
        if not stueck:
            rest[0] = 0
            return False
        rest[0] -= len(stueck)
        puffer.extend(stueck)
        return True

    def bis(marke_: bytes, hoechstens: int) -> bytes:
        """Alles bis zur Marke (ohne sie) — nur für kleine Stücke (Präambel, Kopf)."""
        while True:
            i = puffer.find(marke_)
            if i >= 0:
                vorne = bytes(puffer[:i])
                del puffer[:i + len(marke_)]
                return vorne
            if len(puffer) > hoechstens or not nachladen():
                raise KnotenwegError("Das Formular liess sich nicht zerlegen.")

    try:
        bis(trenner, _TEILKOPF_HOECHSTENS + 2)          # die Präambel
        while True:
            while len(puffer) < 2 and nachladen():
                pass
            if bytes(puffer[:2]) == b"--":
                ende_erreicht[0] = True
                break
            kopf = bis(b"\r\n\r\n", _TEILKOPF_HOECHSTENS)
            name, dateiname = _kopf_des_teils(kopf.lstrip(b" \t\r\n"))
            als_datei = name in datei_felder
            if als_datei:
                if ordner is None:
                    raise KnotenwegError("Für die Datei des Formulars fehlt ein Ordner.", 500)
                Path(ordner).mkdir(parents=True, exist_ok=True)
                ziel = Path(ordner) / f".eingang-{secrets.token_hex(8)}"
                angelegt.append(ziel)
                senke = ziel.open("wb")
                grenze_ = hoechstens_datei
            else:
                senke = bytearray()
                grenze_ = hoechstens_feld
            groesse = 0
            try:
                while True:
                    i = puffer.find(trenner)
                    if i >= 0:
                        stueck, weiter = bytes(puffer[:i]), i + len(trenner)
                    else:
                        # Den Schwanz behalten: Die Marke kann über zwei Stücke reichen.
                        behalten = len(trenner) - 1
                        stueck = bytes(puffer[:max(0, len(puffer) - behalten)])
                        weiter = len(stueck)
                    groesse += len(stueck)
                    if groesse > grenze_:
                        raise KnotenwegError(
                            f"Der Teil «{name}» ist zu gross — angenommen werden bis "
                            f"{grenze_ // (1024 * 1024)} MB.", 413)
                    if isinstance(senke, bytearray):
                        senke.extend(stueck)
                    else:
                        senke.write(stueck)
                    del puffer[:weiter]
                    if i >= 0:
                        break
                    if not nachladen():
                        raise KnotenwegError("Das Formular ist unvollständig angekommen.")
            finally:
                if not isinstance(senke, bytearray):
                    senke.close()
            if name:
                if name in felder and als_datei:
                    raeume_formular({name: felder[name]})
                felder[name] = (dateiname, ziel if als_datei else bytes(senke))
    except BaseException:
        for pfad in angelegt:
            try:
                pfad.unlink()
            except OSError:
                pass
        raise
    # Was nach der Schlussmarke noch kommt (Epilog), wird gelesen und verworfen — sonst
    # laege es in der Leitung vor der naechsten Anfrage.
    while rest[0] > 0 and nachladen():
        puffer.clear()
    if not ende_erreicht[0]:
        raise KnotenwegError("Das Formular ist unvollständig angekommen.")
    return felder


def raeume_formular(felder: dict) -> None:
    """Die Dateien wegräumen, die :func:`teile_formular` angelegt hat und niemand übernahm."""
    for _, inhalt in (felder or {}).values():
        if isinstance(inhalt, Path):
            try:
                inhalt.unlink()
            except OSError:
                pass


def modell_der_grundlage(ablage, kennung: str, *, hoechstens: int = 500) -> Path | None:
    """Die Modelldatei des Auftrags, der die Grundlage ``kennung`` gerechnet hat — oder ``None``.

    **Wofür (Variante ohne Hochladen, 20.10.2026):** Eine Variante (``vis.grundlage``)
    rechnet kein Blender, der Abholer braucht das Modell aber weiter (Modellstand, Rahmung,
    Bestand). Statt es mit jeder Variante neu zu schicken, nimmt der Auftrag das Modell des
    Laufs, der die Grundlage gelegt hat. Gefunden wird er an seinem Ergebnis
    (``render-result.json``, ``grundlage.id``), die jüngsten zuerst; gesucht wird in
    höchstens ``hoechstens`` Aufträgen.
    """
    d = auftrag_der_grundlage(ablage, kennung, hoechstens=hoechstens)
    if d is None:
        return None
    for name in (bruecke.DATEI_MODELL, bruecke.DATEI_MODELL_IFC):
        if (d / name).is_file():
            return d / name
    return None


def auftrag_der_grundlage(ablage, kennung: str, *, hoechstens: int = 500,
                          mit_modell: bool = True) -> Path | None:
    """Der Auftragsordner, dessen Ergebnis die Grundlage ``kennung`` nennt — die jüngsten
    zuerst, mit Modelldatei (``mit_modell``). ``None``, wenn keiner da ist."""
    ordner = Path(ablage)
    if not ordner.is_dir() or not kosmo_szene.GRUNDLAGE_KENNUNG.match(str(kennung or "")):
        return None
    gesehen = 0
    for d in sorted(ordner.iterdir(), reverse=True):
        if not (d.is_dir() and kosmo_szene.ist_fremde_job_id(d.name)):
            continue
        gesehen += 1
        if gesehen > hoechstens:
            break
        ergebnis = d / bruecke.DATEI_ERGEBNIS
        if not ergebnis.is_file():
            continue
        try:
            gl = (json.loads(ergebnis.read_text(encoding="utf-8")) or {}).get("grundlage")
        except (OSError, ValueError, AttributeError):
            continue
        if not (isinstance(gl, dict) and gl.get("id") == kennung):
            continue
        if not mit_modell or any((d / name).is_file()
                                 for name in (bruecke.DATEI_MODELL, bruecke.DATEI_MODELL_IFC)):
            return d
    return None


def umgebung_der_grundlage(ablage, kennung: str):
    """Die gelesene Stimmung der Grundlage ``kennung`` (``umgebung`` ihrer Szene, ``None`` ohne
    Stimmung) — oder :data:`kosmo_szene.UMGEBUNG_UNBEKANNT`, wenn ihr Auftrag hier nicht
    liegt oder sich nicht lesen lässt (Befund 340). Gesucht wie in :func:`grundlage_passt_nicht`.
    """
    d = auftrag_der_grundlage(ablage, kennung, mit_modell=False)
    if d is None or not (d / bruecke.DATEI_SZENE).is_file():
        return kosmo_szene.UMGEBUNG_UNBEKANNT
    try:
        roh = dict(json.loads((d / bruecke.DATEI_SZENE).read_text(encoding="utf-8")))
        if not isinstance(roh.get("geometry"), dict) or not roh["geometry"].get("path"):
            roh["geometry"] = {"path": "grundlage.glb", "format": "glb"}
        return kosmo_szene.lies_szene(roh).get("umgebung")
    except Exception:                                      # noqa: BLE001 — wie oben
        return kosmo_szene.UMGEBUNG_UNBEKANNT


#: Wie die Felder der Grundlage-Prüfung im Satz heissen (für den Architekten, nicht für uns).
GRUNDLAGE_FELDNAMEN = {"aufloesung": "Bildbreite", "hoehe": "Bildhöhe", "samples": "Samples",
                       "kameras": "Kameras", "kameras_auto": "Kamera (Richtungen, Abstand, "
                       "Brennweite)", "umgebung": "Stimmung", "materialien": "Materialien"}


def grundlage_passt_nicht(ablage, szene: dict) -> str | None:
    """Der Satz, wenn eine Variante nicht zu ihrer Grundlage passt — ``None`` sonst.

    **Anlass (Wunsch des Integrators, auf-20261020-292 Punkt 10):** Eine Variante mit anderer
    Stimmung, anderen Materialien oder anderer Kamera als ihre Grundlage wurde angenommen und
    erst beim Rechnen abgewiesen (``abholer.lies_grundlage``) — nach Freigabe und Warten.
    Jetzt schon beim Anlegen, mit 409 und demselben Grund.

    Verglichen wird die Szene des Auftrags, der die Grundlage gerechnet hat, mit der neuen —
    beide durch :func:`aiimaging.kosmo_szene.lies_szene`, Feld für Feld nach
    ``abholer.GRUNDLAGE_MUSS_PASSEN``. Ist der Grundlage-Auftrag hier nicht zu finden oder
    nicht lesbar, sagt diese Prüfung nichts (``None``) — dann bleibt es bei der Prüfung beim
    Rechnen; abgewiesen wird nur, was hier sicher nicht passt.
    """
    from . import abholer  # noqa: PLC0415 — spät, wie heim_standpunkte
    vis = szene.get("vis") if isinstance(szene.get("vis"), dict) else {}
    kennung = vis.get("grundlage")
    if not (isinstance(kennung, str) and kosmo_szene.GRUNDLAGE_KENNUNG.match(kennung)):
        return None
    d = auftrag_der_grundlage(ablage, kennung, mit_modell=False)
    if d is None or not (d / bruecke.DATEI_SZENE).is_file():
        return None
    try:
        alt = json.loads((d / bruecke.DATEI_SZENE).read_text(encoding="utf-8"))
        ersatz = {"path": "grundlage.glb", "format": "glb"}

        def gelesen(roh, **wie):
            roh = dict(roh)
            if not isinstance(roh.get("geometry"), dict) or not roh["geometry"].get("path"):
                roh["geometry"] = ersatz
            return kosmo_szene.lies_szene(roh, **wie)

        vorher = gelesen(alt)
        # DAS LICHT DER VARIANTE (Befund 340): Die Stimmung der Grundlage geht mit — weicht das
        # bestellte Licht davon ab, verwirft `lies_szene` die Grundlage, statt hier 409.
        jetzt = gelesen(szene, umgebung_der_grundlage=vorher.get("umgebung"))
    except Exception:                                      # noqa: BLE001 — siehe Docstring
        return None
    if jetzt.get("grundlage_verworfen"):
        # N6 (22.10.2026): Die Variante traegt eine andere Stimmung; der Heim-PC rechnet ihr
        # eine eigene Grundlage (`kosmo_szene.stimmung_der_variante`) — kein Widerspruch.
        # Befund 340: ebenso, wenn das bestellte Licht selbst ein anderes ist
        # (`kosmo_szene.licht_der_variante`).
        return None
    # Eine Teilmenge der Kameras passt (Geräteprobe R56, `abholer.kameras_weichen_ab`).
    abweichend = abholer.grundlage_weicht_ab(vorher, jetzt)
    if not abweichend:
        return None
    if abweichend == ["kameras_auto"] and vorher.get("kameras_auto") is None \
            and not abholer.grundlage_weicht_ab(vorher, jetzt, abholer.AUTO_RICHTUNGEN):
        # Mac-Probe 0.3.66: Die Grundlage rechnete die Richtungen des Abholers (ohne
        # `cameras_auto`, :data:`abholer.AUTO_RICHTUNGEN` — dieselbe Rechnung wie
        # `heim_standpunkte`), die Variante bestellt einige davon mit den Vorgaben. Das passt; der
        # Abholer prueft es noch einmal an den Kameras, die die Grundlage wirklich gerechnet hat.
        return None
    namen = ", ".join(GRUNDLAGE_FELDNAMEN.get(f, f) for f in abweichend)
    return (f"Die Grundlage {kennung} passt nicht zu dieser Variante: {namen} "
            f"{'weicht' if len(abweichend) == 1 else 'weichen'} ab. Eine Variante entsteht "
            f"aus DERSELBEN Grundlage — bitte «Grundlage rendern» mit diesen Werten, oder die "
            f"Werte der Grundlage bestellen.")
