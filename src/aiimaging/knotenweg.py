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

import hmac
import json
import secrets
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


def lege_an(ablage, szene: dict, modell: bytes, dateiname: str | None = None,
            *, kennung: str | None = None, mappe: str | None = None,
            mappe_pfad=None) -> dict:
    """Einen Auftrag annehmen: drei Dateien in einen neuen Ordner, Status wartet auf Freigabe.

    Args:
        ablage: Wohin die Aufträge kommen — derselbe Ordner, den der Abholer liest.
        szene: ``render-scene/v1`` wie von der Knotenansicht gesendet.
        modell: Die Bytes der Modelldatei.
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

    Returns:
        Der Laufzettel, wie er in ``job.json`` steht — mit ``approval_token``, den nur der
        Absender bekommt und mit dem er freigibt.
    """
    if not isinstance(szene, dict):
        raise KnotenwegError("Die Szene ist kein JSON-Objekt.")
    if not modell:
        raise KnotenwegError("Die Modelldatei ist leer.")
    if len(modell) > MAX_MODELL_BYTES:
        raise KnotenwegError(
            f"Die Modelldatei ist {len(modell) / 1e6:.0f} MB gross; angenommen werden bis "
            f"{MAX_MODELL_BYTES / 1e6:.0f} MB.", 413)
    fmt = _format(szene, dateiname)
    skizze = _pruefe_skizze(szene, mappe_pfad)

    job_id = kennung or f"vis-{int(time.time())}-{secrets.token_hex(3)}"
    if not kosmo_szene.ist_fremde_job_id(job_id):
        raise KnotenwegError(f"Keine Auftragskennung: {job_id!r}.")
    ordner = Path(ablage) / job_id
    ordner.mkdir(parents=True, exist_ok=False)

    modellpfad = ordner / (bruecke.DATEI_MODELL_IFC if fmt == "ifc" else bruecke.DATEI_MODELL)
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


def _pruefe_skizze(szene: dict, mappe_pfad) -> str | None:
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
    if not mappe_pfad:
        raise KnotenwegError(
            "Eine Skizze lässt sich nur aus einer offenen Mappe bestellen — dieser Auftrag "
            "kam ohne Mappe. Die Mappe auf der Visbox-Seite öffnen und neu ausführen.")
    try:
        skizzen = skizzen_der_mappe(projekt.oeffne(mappe_pfad)["projekt"], hoechstens=10**6)
    except projekt.ProjektError as fehler:
        raise KnotenwegError(f"Die Mappe liess sich nicht öffnen: {fehler}") from fehler
    if name not in {s["name"] for s in skizzen}:
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


def freigeben(ablage, job_id: str, token) -> dict:
    """Ein Mensch hat «Freigeben» gedrückt: wartend → in der Reihe, mit Marke.

    Der Token muss der sein, den :func:`lege_an` ausgegeben hat (Vergleich in konstanter
    Zeit). Ein Auftrag, der nicht wartet, bleibt unverändert — kein stiller Zustandssprung,
    wie bei der Brücke.
    """
    ordner = auftragsordner(ablage, job_id)
    pfad = ordner / bruecke.DATEI_LAUFZETTEL
    zettel = json.loads(pfad.read_text(encoding="utf-8"))
    erwartet = str(zettel.get("approval_token") or "")
    if not erwartet or not hmac.compare_digest(str(token or ""), erwartet):
        raise KnotenwegError("Freigabe abgewiesen: Der Token fehlt oder passt nicht.", 403)
    if zettel.get("status") != bruecke.STATUS_AWAITING:
        return zettel
    zettel["status"] = bruecke.STATUS_QUEUED
    zettel["updated_at"] = _jetzt()
    zettel[FELD_FREIGABE] = {"am": zettel["updated_at"], "durch": "Klick in der Knotenansicht"}
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
RICHTUNGSNAMEN = {"s": ("Süd", "frontal"), "sSE": ("Südost", "über Eck"),
                  "nNW": ("Nordwest", "über Eck")}

#: Das Seitenverhältnis, mit dem die Knotenansicht bestellt, wenn am Render-Knoten keine
#: Auflösung gewählt ist (1600 × 1000, `vis-jobs.ts`). Der Abholer rechnet die Kamera mit dem
#: Seitenverhältnis des Laufs; eine andere gewählte Auflösung verschiebt den Abstand etwas.
SEITENVERHAELTNIS_VORGABE = 1600 / 1000


def heim_standpunkte(glb, up_axis: str = "Y", *, szene_box=None) -> dict:
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

    Returns:
        ``{standpunkte: [{kuerzel, name, art, abstand_m, auge, blick_auf, vollstaendig,
        begruendung}], satz}`` — Weltkoordinaten in Metern, Z oben. Leer mit ``satz``, wenn
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
    try:
        satz = kameras.kamerasatz(
            box, kuerzel=list(abholer.AUTO_RICHTUNGEN),
            seitenverhaeltnis=SEITENVERHAELTNIS_VORGABE,
            ausschnitt=bool(rahmung.get("box") or rahmung.get("szene_ist_bauwerk")))
    except ValueError as fehler:
        return {"standpunkte": [], "satz": f"Kein Vorschlag aus dieser Hüllbox: {fehler}"}
    aus = []
    for k in satz["kameras"]:
        name, art = RICHTUNGSNAMEN.get(k["kuerzel"], (k["kuerzel"], ""))
        aus.append({"kuerzel": k["kuerzel"], "name": name, "art": art,
                    "abstand_m": round(float(k["abstand_m"]), 1),
                    "auge": [round(float(v), 3) for v in k["auge"]],
                    "blick_auf": [round(float(v), 3) for v in k["blick_auf"]],
                    "vollstaendig": bool(k["vollstaendig"]),
                    "begruendung": str(k.get("begruendung") or "")})
    nach = "dem Bauwerk" if rahmung.get("box") else "der ganzen Szene"
    return {"standpunkte": aus,
            "satz": f"Rechnet der Heim-PC aus der Hüllbox ({nach}) — Vorschau."}


#: Wie viele Skizzen der Knoten «Skizze vom iPad» zur Wahl bekommt — die neuesten.
SKIZZEN_HOECHSTENS = 24


def skizzen_der_mappe(p: dict, hoechstens: int = SKIZZEN_HOECHSTENS) -> list[dict]:
    """Die Skizzen einer Mappe für den Knoten «Skizze vom iPad» — **die neueste zuerst**.

    **Anlass (Owner-Entscheide 95/95a, 14.10.2026, Blatt 25):** Die Knotenansicht ist die
    Arbeitsfläche zum Rendern (Entscheid 94), die Skizzen vom iPad standen aber nur auf der
    Visbox-Seite. Der Knoten nimmt von selbst die neueste; eine ältere wählt man am Knoten.

    Verworfene Skizzen fehlen — sie sind nicht mehr gemeint. Jede Skizze steht einmal (die
    Mappe vermerkt dieselbe Zeichnung bei jedem Zustandswechsel neu); es gilt ihr letzter
    Eintrag. Kein Pfad: nur der Dateiname der Mappe, den ``/knoten/skizze?name=`` ausliefert.

    Returns:
        ``[{name, titel, erzeugt, ueber, stand}]``, höchstens ``hoechstens``.
    """
    letzte: dict[str, dict] = {}
    for e in p.get("skizzen") or []:
        if isinstance(e, dict) and e.get("skizze"):
            letzte[str(e["skizze"])] = e
    liste = [
        {"name": name, "titel": e.get("titel"), "erzeugt": e.get("erzeugt"),
         "ueber": e.get("ueber"), "stand": e.get("stand")}
        for name, e in letzte.items() if e.get("stand") != projekt.SKIZZE_VERWORFEN
    ]
    liste.sort(key=lambda x: str(x.get("erzeugt") or ""), reverse=True)
    return liste[:max(0, int(hoechstens))]
