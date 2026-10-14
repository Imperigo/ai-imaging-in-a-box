"""**Modell laden** — eine Datei, die der Mensch wählt, wird zu einer Mappe am Heim-PC.

Owner-Entscheid 90 (14.10.2026, gezeichnet auf Blatt 21 der Entwurfsfläche): Der
Modell-Knoten der Knotenansicht bekommt «Datei laden …». Bis dahin kam ein Modell nur über
einen **Pfad** herein (``arbeitsgang.lege_an``, ``POST /api/anlegen``) — wer am Mac sass,
musste wissen, wo am Heim-PC die Datei liegt. Jetzt kommt die Datei selbst, als Bytes, und
dieses Modul entscheidet, wohin sie gehört.

Drei Entscheide, alle am Blatt
------------------------------
**90a · Die neue Mappe liegt neben der Start-Mappe.** Neben der Mappe, mit der der Server
gestartet wurde (``--ordner``), also in ihrem Elternordner. Der Name kommt aus dem
Dateinamen, bereinigt auf Buchstaben, Ziffern, ``-`` und ``_`` (:func:`mappenname`). Liegt
dort schon ein Ordner dieses Namens, der **nicht** dieselbe Datei trägt, wird ``-2``,
``-3`` … angehängt — nie in einen fremden Ordner hineingeschrieben.

**90b · Dieselbe Datei noch einmal ist eine neue Fassung, keine neue Mappe.** Gleicher
Dateiname → gleiche Mappe; das Modell wird dort ersetzt
(:func:`aiimaging.arbeitsgang.ersetze_modell`), Bilder, Skizzen und Läufe bleiben.

**90c · Ein geschlossenes Format bekommt einen Satz, der weiterhilft.** Eine ArchiCAD-Datei
(``.pln``) kann niemand ausser ArchiCAD lesen. Statt «Format unbekannt» sagt
:data:`GESCHLOSSENE_FORMATE`, wie man aus ArchiCAD eine IFC macht.

Wo die Datei liegt
------------------
In der Mappe unter ``quelle/f<N>/<dateiname>`` — ``N`` ist die Fassung. Das bricht mit
dem ersten Entscheid von :mod:`aiimaging.projekt` («das Projekt schluckt das Modell
nicht»), und zwar mit Grund: Eine hochgeladene Datei **hat am Heim-PC keinen anderen
Ort.** Ihr Original liegt beim Menschen auf seinem Rechner; was hier liegt, ist die
einzige Fassung, aus der die Mappe rechnen kann. Ältere Fassungen werden nach dem Wechsel
gelöscht (ihr Eintrag in ``modell_fassungen`` bleibt) — sonst wüchse die Mappe mit jedem
Laden einer 500-MB-IFC um 500 MB.

Regel 4: alles aus reinem Python aufrufbar; der Server ruft :func:`lade` und reicht den
Zustand weiter, mehr nicht.
"""
from __future__ import annotations

import json
import re
import shutil
import time
import unicodedata
from pathlib import Path

from aiimaging import arbeitsgang, importeur, projekt, seams

__all__ = [
    "GESCHLOSSENE_FORMATE", "GROESSTE_DATEI_BYTE", "ModellLadenError", "QUELLORDNER",
    "anzeige_formate", "annehmen", "herkunft_von", "lade", "mappenname", "pruefe_dateiname",
    "ziel_fuer",
]


class ModellLadenError(ValueError):
    """Die Anfrage selbst taugt nicht (kein Dateiname, ein Pfad statt eines Namens, keine
    Start-Mappe) — **nicht** die Datei. Eine Datei, die nicht durchkommt, ist ein Befund
    und kommt als Zustand ``fehler`` zurück."""


#: Der Ordner in der Mappe, in dem die geladenen Dateien liegen (je Fassung ``f<N>/``).
QUELLORDNER = "quelle"

#: Wie gross eine Datei höchstens sein darf — dieselbe Grenze wie für ein Modell, das die
#: Knotenansicht zur Rechnung schickt (``knotenweg.MAX_MODELL_BYTES``). GESETZT: Die
#: grösste IFC der Messreihe vom 18.08.2026 lag deutlich darunter.
GROESSTE_DATEI_BYTE = 768 * 1024 * 1024

#: Höchstens so viele Zeichen hat ein Mappenname — ein Dateiname kann beliebig lang sein,
#: ein Ordnername auf manchen Platten nicht.
NAME_HOECHSTENS = 60

#: Formate, die kein anderes Programm lesen kann als das, das sie schreibt — mit dem Satz,
#: der sagt, wie man daraus eine Datei macht, die hier hereinkommt (Entscheid 90c).
GESCHLOSSENE_FORMATE: dict[str, str] = {
    ".pln": ("ArchiCAD-Dateien sind ein geschlossenes Format. In ArchiCAD: Ablage → "
             "Sichern unter → IFC, dann die IFC laden."),
    ".pla": ("ArchiCAD-Archive sind ein geschlossenes Format. In ArchiCAD öffnen, dann "
             "Ablage → Sichern unter → IFC, und die IFC laden."),
    ".rvt": ("Revit-Dateien sind ein geschlossenes Format. In Revit: Datei → Exportieren → "
             "IFC, dann die IFC laden."),
}

#: Anzeigenamen der Endungen, für die Zeile unter dem Knopf. Was hier fehlt, erscheint mit
#: seiner Endung in Grossbuchstaben (``.abc`` → «ABC») — die Liste der Formate ist
#: :data:`aiimaging.importeur.WEGE`, nicht diese Tafel.
_ANZEIGE = {".ifc": "IFC", ".glb": "glb/glTF", ".gltf": "glb/glTF", ".dae": "Collada",
            ".usd": "USD", ".usdc": "USD", ".usda": "USD", ".abc": "Alembic"}

#: Woraus ein Modell kam, für «Szene: N Bauteile (aus …)».
_HERKUNFT = {".glb": "glb", ".gltf": "glTF", ".usdc": "USD", ".usda": "USD"}

_UMLAUTE = {"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue", "ß": "ss"}


def anzeige_formate() -> list[str]:
    """Die Formate, die hereinkommen — aus :data:`importeur.WEGE`, in dessen Reihenfolge,
    ohne Doppel. Die Formate, die nur manche Blender-Fassungen lesen
    (:data:`importeur.FASSUNGSABHAENGIG`), stehen am Ende."""
    vorne, hinten = [], []
    for endung in importeur.WEGE:
        name = _ANZEIGE.get(endung, endung[1:].upper())
        liste = hinten if endung in importeur.FASSUNGSABHAENGIG else vorne
        if name not in vorne and name not in hinten:
            liste.append(name)
    return vorne + hinten


def annehmen() -> str:
    """Für ``<input type="file" accept>``: alle Endungen, die hereinkommen — **und** die
    geschlossenen, damit ihr Satz (90c) überhaupt erscheinen kann. Ein Wähler, der eine
    ``.pln`` gar nicht anbietet, lässt den Menschen ratlos statt beraten."""
    return ",".join([*importeur.WEGE, *GESCHLOSSENE_FORMATE])


def herkunft_von(dateiname) -> str | None:
    """«IFC», «glb», «OBJ» … — woraus ein Modell kam. ``None`` ohne Endung."""
    endung = Path(str(dateiname or "")).suffix.lower()
    if not endung:
        return None
    return _HERKUNFT.get(endung, endung[1:].upper())


def pruefe_dateiname(dateiname) -> str:
    """Der Dateiname, wie er ankommt — geprüft, nicht umgebaut.

    Abgewiesen wird, was **kein Name** ist: leer, ein Pfad (``/``, ``\\``, ``..``), ein
    Name, der mit einem Punkt beginnt (versteckt), Steuerzeichen, oder länger als 200
    Zeichen. Der Browser schickt nur den Namen; ein Pfad an dieser Stelle hiesse, dass
    jemand anderes als der Browser schickt.

    Raises:
        ModellLadenError: mit einem Satz für den Menschen.
    """
    name = str(dateiname or "").strip()
    if not name:
        raise ModellLadenError("Die Datei kam ohne Namen an.")
    if ("/" in name or "\\" in name or name in (".", "..") or name.startswith(".")
            or any(ord(z) < 32 for z in name) or len(name) > 200):
        raise ModellLadenError(
            "Der Dateiname taugt nicht als Name einer Datei (kein Pfad, kein Punkt am "
            "Anfang, höchstens 200 Zeichen).")
    if not Path(name).suffix:
        raise ModellLadenError(
            "Die Datei hat keine Endung — woran zu erkennen wäre, was sie ist. Formate: "
            + ", ".join(anzeige_formate()) + ".")
    return name


def mappenname(dateiname) -> str:
    """Der Name der Mappe aus dem Dateinamen (Entscheid 90a): nur Buchstaben, Ziffern,
    ``-`` und ``_``.

    Umlaute werden ausgeschrieben (``Bürohaus`` → ``Buerohaus``), Akzente fallen weg,
    alles andere wird zu ``-``, mehrere hintereinander zu einem. Bleibt nichts übrig, heisst
    die Mappe ``modell``.
    """
    stamm = Path(str(dateiname or "")).stem
    stamm = "".join(_UMLAUTE.get(z, z) for z in stamm)
    # AKZENTE FALLEN WEG (é → e), jedes andere fremde Zeichen wird ein Trenner — sonst
    # klebten «Café—Entwurf» zu «CafeEntwurf» zusammen.
    stamm = "".join("" if unicodedata.combining(z) else (z if z.isascii() else "-")
                    for z in unicodedata.normalize("NFKD", stamm))
    stamm = re.sub(r"[^A-Za-z0-9_-]+", "-", stamm)
    stamm = re.sub(r"-{2,}", "-", stamm).strip("-_")
    return stamm[:NAME_HOECHSTENS].rstrip("-_") or "modell"


def _traegt_dieselbe_datei(ordner: Path, dateiname: str) -> bool:
    """Ist ``ordner`` eine Mappe, deren Modell eine Datei dieses Namens ist?"""
    try:
        p = projekt.oeffne(ordner)["projekt"]
    except projekt.ProjektError:
        return False
    pfad = (p.get("modell") or {}).get("pfad") or ""
    return Path(str(pfad).replace("\\", "/")).name.casefold() == dateiname.casefold()


def ziel_fuer(eltern, dateiname) -> tuple[Path, bool]:
    """Wohin eine Datei dieses Namens gehört: ``(mappe, ersetzen)``.

    ``ersetzen`` ist ``True``, wenn dort schon eine Mappe mit **derselben Datei** liegt
    (90b). Sonst der erste freie Name aus ``<name>``, ``<name>-2``, ``<name>-3`` … —
    ein vorhandener Ordner, der nicht dieselbe Datei trägt (eine andere Mappe, ein
    fremder Ordner), wird nie angefasst.
    """
    eltern = Path(eltern)
    dateiname = pruefe_dateiname(dateiname)
    name = mappenname(dateiname)
    for nummer in range(1, 1000):
        kandidat = eltern / (name if nummer == 1 else f"{name}-{nummer}")
        if not kandidat.exists():
            return kandidat, False
        if _traegt_dieselbe_datei(kandidat, dateiname):
            return kandidat, True
    raise ModellLadenError(
        f"Neben der Start-Mappe liegen schon 999 Ordner namens «{name}…» — bitte aufräumen "
        f"oder die Datei umbenennen.")


def _fehler(satz: str, **mehr) -> dict:
    return {"stand": "fehler", "satz": satz, "mappe": None, "ersetzt": False, **mehr}


def lade(start_mappe, dateiname, inhalt: bytes, *, melder=None, timeout: float | None = None,
         _starte=None) -> dict:
    """Eine geladene Datei zu einer Mappe machen — neu (90a) oder als neue Fassung (90b).

    Args:
        start_mappe: Die Mappe, mit der der Server gestartet wurde. Die neue Mappe kommt
            in ihren **Elternordner**.
        dateiname: Der Name der Datei, wie der Browser ihn schickt.
        inhalt: Die Bytes.
        melder: Bekommt ``{"schritt": …, "satz": …}`` vor jedem Schritt — für den Knoten.

    Returns:
        ``{stand, satz, mappe, ersetzt, fassung, herkunft, import}``. ``stand`` ist
        ``"geladen"`` oder ``"fehler"``; ``mappe`` der Pfad der Mappe (oder ``None``).
        **Eine Datei, die nicht durchkommt, wirft nicht** — sie ist ein Befund, und ihr
        Satz steht in ``satz``. Eine neu angelegte Mappe wird dann wieder entfernt: Eine
        leere Mappe, die nur eine Absage enthält, sähe neben den anderen aus wie eine
        Arbeit.

    Raises:
        ModellLadenError: keine Start-Mappe, der Dateiname taugt nicht, die Datei ist zu
            gross.
    """
    if not start_mappe:
        raise ModellLadenError(
            "Der Heim-PC weiss nicht, wohin die Mappe soll: Er läuft ohne Start-Mappe. Mit "
            "--ordner starten — die neue Mappe kommt daneben.")
    dateiname = pruefe_dateiname(dateiname)
    if len(inhalt) > GROESSTE_DATEI_BYTE:
        raise ModellLadenError(
            f"Die Datei ist zu gross — angenommen werden Modelle bis "
            f"{GROESSTE_DATEI_BYTE // (1024 * 1024)} MB.")
    endung = Path(dateiname).suffix.lower()
    herkunft = herkunft_von(dateiname)

    if endung in GESCHLOSSENE_FORMATE:
        return _fehler(GESCHLOSSENE_FORMATE[endung], herkunft=herkunft)
    if not importeur.kann_importieren(endung):
        return _fehler(
            f"Für {endung} hat Visbox keinen Weg. Es kommen herein: "
            f"{', '.join(anzeige_formate())}. Die meisten CAD-Programme können IFC oder "
            f"glTF (.glb) ausgeben.", herkunft=herkunft)
    if not inhalt:
        return _fehler("Die Datei ist leer.", herkunft=herkunft)
    satz = _durchgereicht_untauglich(endung, inhalt)
    if satz:
        return _fehler(satz, herkunft=herkunft)

    eltern = Path(start_mappe).resolve().parent
    mappe, ersetzen = ziel_fuer(eltern, dateiname)
    fassung = (projekt.modellfassung(projekt.oeffne(mappe)["projekt"]) + 1) if ersetzen else 1
    ablage = mappe / QUELLORDNER / f"f{fassung}"
    neu_angelegt = not mappe.exists()

    def melde(schritt: str, satz: str) -> None:
        if melder is not None:
            try:
                melder({"schritt": schritt, "satz": satz})
            except Exception:                      # noqa: BLE001 — ein Melder haelt nichts an
                pass

    def schritte(ereignis: dict) -> None:
        if ereignis.get("schritt") == "umwandeln":
            melde("umwandeln", "IFC wird gelesen — Bauteile und Räume, das dauert länger."
                  if endung == ".ifc" else "Das Modell wird übernommen …"
                  if importeur.weg_fuer_endung(endung) == importeur.WEG_DURCHGEREICHT
                  else "Das Modell wird umgewandelt …")
        elif ereignis.get("schritt") == "raeume":
            melde("raeume", "Die Räume der IFC werden gelesen …")

    beginn = time.monotonic()
    melde("ablegen", "Die Datei wird in die Mappe gelegt …")
    try:
        ablage.mkdir(parents=True, exist_ok=True)
        quelle = ablage / dateiname
        quelle.write_bytes(inhalt)
        if ersetzen:
            ergebnis = arbeitsgang.ersetze_modell(mappe, quelle, timeout=timeout,
                                                  melder=schritte, _starte=_starte)
            angenommen = ergebnis["ersetzt"]
        else:
            ergebnis = arbeitsgang.lege_an(mappe, quelle, name=mappe.name, timeout=timeout,
                                           melder=schritte, _starte=_starte)
            angenommen = ergebnis["import_bericht"]["status"] == "ok"
    except (arbeitsgang.ArbeitsgangError, projekt.ProjektError, importeur.ImporteurError,
            seams.SeamError, OSError) as fehler:
        _raeume_auf(mappe if neu_angelegt else ablage)
        return _fehler(str(fehler), herkunft=herkunft)

    innen = (ergebnis["import_bericht"].get("bericht") or {}).get("status")
    if angenommen and neu_angelegt and innen not in (None, "ok"):
        # EIN WEG, DER «FERTIG» SAGT UND IM EIGENEN BERICHT «FEHLER» — nicht angenommen.
        # (Nur bei einer neuen Mappe: eine ersetzte ist dann schon geschrieben, und ihr
        # die Datei unter den Fuessen wegzuziehen, waere schlimmer.)
        _raeume_auf(mappe)
        return _fehler(str((ergebnis["import_bericht"].get("bericht") or {}).get("error")
                           or "Die Umwandlung hat kein Modell ergeben."), herkunft=herkunft)
    if not angenommen:
        bericht = ergebnis["import_bericht"]
        _raeume_auf(mappe if neu_angelegt else ablage)
        satz = " ".join(t for t in (bericht.get("grund"), bericht.get("naechster_schritt")) if t)
        return _fehler(satz or "Die Datei kam nicht durch.", herkunft=herkunft)

    # DIE AELTEREN FASSUNGEN RAEUMEN — die Datei, nicht ihr Eintrag (siehe Modulkopf).
    for alt in (mappe / QUELLORDNER).glob("f*"):
        if alt.is_dir() and alt != ablage:
            _raeume_auf(alt)
    return {
        "stand": "geladen",
        "satz": (f"Neue Fassung {fassung} in der Mappe «{mappe.name}» — Bilder und Skizzen "
                 f"bleiben." if ersetzen else f"Mappe «{mappe.name}» angelegt."),
        "mappe": mappe,
        "ersetzt": ersetzen,
        "fassung": fassung,
        "herkunft": herkunft,
        "dauer_s": round(time.monotonic() - beginn, 1),
        "import": ergebnis["projekt"].get("import"),
    }


def _durchgereicht_untauglich(endung: str, inhalt: bytes) -> str | None:
    """Ein glb/glTF wird **nicht umgewandelt** (``importeur.WEG_DURCHGEREICHT``) — also prüft
    hier niemand ausser uns, ob es überhaupt eines ist. Ohne diesen Blick entstünde aus einer
    Textdatei namens ``haus.glb`` eine Mappe, deren Modell sich nicht zeigen lässt.

    Und ein ``.gltf`` mit **getrennten Dateien** (``.bin``, Bilder) kommt als einzelne Datei
    nicht vollständig an — die anderen liegen beim Menschen und nicht hier.
    """
    if endung == ".glb" and inhalt[:4] != b"glTF":
        return ("Die Datei heisst .glb, ist aber keine glb (sie beginnt nicht mit «glTF»). "
                "Aus dem Programm, das sie geschrieben hat, noch einmal als glTF 2.0 (.glb) "
                "ausgeben.")
    if endung == ".gltf":
        try:
            js = json.loads(inhalt.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            return "Die Datei heisst .gltf, ist aber kein glTF (kein lesbarer Text)."
        if not isinstance(js, dict) or "asset" not in js:
            return "Die Datei heisst .gltf, ist aber kein glTF (es fehlt die Angabe «asset»)."
        fremd = [q.get("uri") for q in (*(js.get("buffers") or []), *(js.get("images") or []))
                 if isinstance(q, dict) and q.get("uri") and not str(q["uri"]).startswith("data:")]
        if fremd:
            return (f"Diese glTF-Datei verweist auf {len(fremd)} weitere Datei(en) "
                    f"(etwa «{fremd[0]}»), die nicht mitkommen. Als eine Datei ausgeben: "
                    f"glTF 2.0 binär (.glb).")
    return None


def _raeume_auf(ordner: Path) -> None:
    shutil.rmtree(ordner, ignore_errors=True)
