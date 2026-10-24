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
import secrets
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

from . import bruecke, glbbox, kosmo_szene, projekt

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


def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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


def lege_an(ablage, szene: dict, modell, dateiname: str | None = None,
            *, kennung: str | None = None, mappe: str | None = None,
            mappe_pfad=None, am_mac: str | None = None) -> dict:
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
        am_mac: Der Name der **Mappe am Mac**, aus der bestellt wurde (``X-Mappe-Am-Mac``),
            sonst ``None``. Mit ihm ist
            ``mappe_pfad`` nur ihr Zwilling hier (oder ``None``). Fehlt die Skizze dort, sagt
            der Satz, dass sie nur am Mac liegt (:data:`SATZ_SKIZZE_NUR_AM_MAC`, Befund F4).

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
    skizze = _pruefe_skizze(szene, mappe_pfad, am_mac=am_mac)

    job_id = kennung or f"vis-{int(time.time())}-{secrets.token_hex(3)}"
    if not kosmo_szene.ist_fremde_job_id(job_id):
        raise KnotenwegError(f"Keine Auftragskennung: {job_id!r}.")
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
    if skizze is not None:
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
        "created_at": _jetzt(),
        **({"mappe": str(mappe)} if mappe else {}),
        bruecke.FELD_MELDUNG: "Wartet auf Freigabe — erst ein Klick auf «Freigeben» "
                              "schickt den Auftrag an die Grafikkarte.",
    }
    _schreibe(ordner / bruecke.DATEI_LAUFZETTEL, zettel)
    return zettel


#: Der Satz, wenn eine Variante ohne Modell kommt und die Grundlage hier fehlt. Seit
#: auf-20261020-289 (B2) mit dem vereinbarten Wortlaut «nicht bekannt» — wie der Satz des
#: Abholers, wenn ein Modell mitkam (bis dahin hiess es an der Tür «nicht zu finden»).
SATZ_GRUNDLAGE_FEHLT = (
    "Die Variante kam ohne Modell, und die Grundlage {kennung} ist hier nicht bekannt (kein "
    "Auftrag auf diesem Heim-PC hat sie gerechnet, oder sein Modell ist weg). Bitte zuerst "
    "«Grundlage rendern» — oder die Variante mit Modell schicken.")


def _modell_fuer_variante(ablage, szene: dict) -> Path:
    """Das Modell für einen Auftrag ohne Modelldatei — nur mit ``vis.grundlage``, sonst Satz."""
    vis = szene.get("vis") if isinstance(szene.get("vis"), dict) else {}
    kennung = vis.get("grundlage")
    if not kennung:
        raise KnotenwegError("Ein Auftrag braucht die Felder «scene» und «model» — ohne "
                             "Modell nur als Variante einer Grundlage (vis.grundlage).")
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
#: und ``skizzen_lesen`` zeigten sie), nur der Zwilling hier hatte sie nie bekommen. Die Mac-App
#: schickt eine Skizze beim Bestellen noch nicht mit (PLAN: nach der Demo).
SATZ_SKIZZE_NUR_AM_MAC = (
    "Die Skizze {name!r} liegt nur am Mac (Mappe «{mappe}») — der Heim-PC hat sie nicht "
    "bekommen: Eine Skizze aus einer Mappe am Mac reist beim Bestellen noch nicht mit. "
    "Bis das kommt: am Mac unter «Mappen …» «Ohne Mappe am Mac» wählen, die Skizze am iPad "
    "neu senden und das Bild dann bestellen — so liegt sie am Heim-PC und lässt sich rechnen.")


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
    if name not in {s["name"] for s in skizzen}:
        if am_mac:
            # BEFUND F4: Die Liste des Knotens kommt aus der Mappe am Mac; fehlt die Skizze im
            # Zwilling hier, liegt sie dort — sie ist nicht verworfen, nur nie hergekommen.
            raise KnotenwegError(SATZ_SKIZZE_NUR_AM_MAC.format(name=name, mappe=am_mac))
        raise KnotenwegError(
            f"Die Skizze {name!r} steht nicht (mehr) in der Mappe «{Path(mappe_pfad).name}» — "
            f"verworfen oder nie abgelegt. Am Knoten «Skizze vom iPad» eine andere wählen.")
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


def freigeben(ablage, job_id: str, token, *, durch: str | None = None) -> dict:
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
        return _freigeben_gesperrt(pfad, job_id, token, durch)


def _freigeben_gesperrt(pfad, job_id, token, durch) -> dict:
    zettel = json.loads(pfad.read_text(encoding="utf-8"))
    erwartet = str(zettel.get("approval_token") or "")
    if not erwartet or not hmac.compare_digest(str(token or ""), erwartet):
        raise KnotenwegError("Freigabe abgewiesen: Der Token fehlt oder passt nicht.", 403)
    if zettel.get("status") != bruecke.STATUS_AWAITING:
        return zettel
    zettel["status"] = bruecke.STATUS_QUEUED
    zettel["updated_at"] = _jetzt()
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
        fassung, bauteile, standpunkte}`` — ``glb`` ist der
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
               "standpunkte": None}
    if glb is None or not Path(glb).is_file():
        antwort["glb"] = None
        # SEIT ENTSCHEID 90 sagt der Satz, wo es weitergeht: am Modell-Knoten selbst.
        antwort["grund"] = (f"Die Mappe «{Path(ordner).name}» hat noch kein Modell — "
                            "«Datei laden …» holt eines herein.")
        return antwort
    achse = einfuhr.get("hochachse") if einfuhr.get("hochachse_steht_fest") else "Y"
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
    liste = [
        {"name": name, "titel": e.get("titel"), "erzeugt": e.get("erzeugt"),
         "ueber": e.get("ueber"), "stand": e.get("stand"),
         "bemerkung": (e.get("bemerkung") if isinstance(e.get("bemerkung"), str)
                       and e.get("bemerkung").strip() else None),
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
    namen = ", ".join(GRUNDLAGE_FELDNAMEN.get(f, f) for f in abweichend)
    return (f"Die Grundlage {kennung} passt nicht zu dieser Variante: {namen} "
            f"{'weicht' if len(abweichend) == 1 else 'weichen'} ab. Eine Variante entsteht "
            f"aus DERSELBEN Grundlage — bitte «Grundlage rendern» mit diesen Werten, oder die "
            f"Werte der Grundlage bestellen.")
