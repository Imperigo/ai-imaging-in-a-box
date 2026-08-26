"""BRÜCKENAUFTRÄGE — das Dateiformat der fremden Warteschlange lesen und bedienen.

Was die Brücke tut, und was sie NICHT tut
------------------------------------------
Die Brücke der Designzentrale nimmt einen Auftrag entgegen, legt drei Dateien in ein
Verzeichnis und **wartet**. Sie rendert nichts. Sie erwartet, dass jemand ein
``render-result.json`` danebenlegt und den Status hochsetzt::

    <store>/vis-<zeitstempel>-<sechs Hexziffern>/
        model.glb              die Geometrie
        render-scene.json      was gerendert werden soll
        job.json               der Laufzettel: job_id, status, scene, approval_token, …
        out/                   wohin die Ausgabe soll
        → render-result.json   was WIR danebenlegen
        → <bilder>.png         ebenfalls von uns, mit RELATIVEN Namen

Genau diese Rolle spielt ``tools/homeworker.py`` schon für unsere eigenen
Auftragsdateien. Dieses Modul ist die Übersetzung dazwischen — **die kleinste denkbare
Naht zur Demo**, und sie liegt vollständig auf unserer Seite.

Die Statusfolge ist ``queued`` → ``running`` → ``done`` (oder ``error``). Sie ist
dieselbe wie unsere (:mod:`aiimaging.jobs`), was kein Zufall ist: Beide stammen aus
demselben Vertrag.

Der Befund, der hier nicht stillschweigend durchgehen darf
-----------------------------------------------------------
**Die Brücke erzeugt den Freigabe-Token selbst.** In ihrem ``create_job`` steht::

    "approval_token": f"CONFIRMED_RENDER_{secrets.token_hex(4)}"

Jeder Auftrag kommt also mit einer Freigabe an, die **kein Mensch erteilt hat**. Der
Token sieht aus wie unserer, heisst wie unserer und bedeutet etwas anderes.

Für uns ist das kein Formfehler. Unser ``enqueue_render`` lässt einen Auftrag ohne Token
ausdrücklich auf ``awaiting_approval`` liegen und rührt die Grafikkarte nicht an — das
ist der Freeze-Schutz, und er ist der Grund, warum die Leistungsgrenze überhaupt
eingehalten wird. Wer die fremde Warteschlange bedient, hebelt ihn aus, **ohne dass
irgendwo etwas rot wird**.

Darum verlangt :func:`lies_auftrag` eine ausdrückliche Entscheidung des Betreibers
(``fremde_freigabe_gilt``). Ohne sie wird der Auftrag gelesen und als **nicht
freigegeben** gemeldet. Das ist unbequem und richtig: Eine Freigabe, die eine Maschine
sich selbst erteilt, ist keine.

Abhängigkeiten: keine ausser der Standardbibliothek. Kein ``bpy`` (Regel 2), aus Python
heraus ohne Oberfläche aufrufbar (Regel 4). Dieses Modul **rendert nicht** — es liest und
schreibt Dateien; das Rendern bleibt, wo es ist.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from . import kosmo_szene

#: Die Dateinamen der fremden Warteschlange, wörtlich aus ihrer ``main.py``.
DATEI_LAUFZETTEL = "job.json"
DATEI_SZENE = "render-scene.json"
DATEI_ERGEBNIS = "render-result.json"
DATEI_MODELL = "model.glb"

#: Ihre Statuswerte, wörtlich aus ihrem Schema.
STATUS_AWAITING = "awaiting_approval"
STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_ERROR = "error"
STATUS_CANCELLED = "cancelled"
STATUSSE = (STATUS_AWAITING, STATUS_QUEUED, STATUS_RUNNING, STATUS_DONE,
            STATUS_ERROR, STATUS_CANCELLED)

#: Die Form ihrer Verzeichnisnamen. Nur was so heisst, ist ein Auftrag.
VERZEICHNIS_MUSTER = re.compile(r"^vis-\d+-[0-9a-f]{6}$")

#: Vorsatz des Freigabe-Tokens — bei ihnen wie bei uns.
TOKEN_VORSATZ = "CONFIRMED_RENDER_"


class BrueckenError(ValueError):
    """Ein Auftragsverzeichnis ist unbrauchbar, oder eine Antwort passte nicht hinein."""


def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _lies_json(pfad: Path, was: str) -> dict:
    if not pfad.is_file():
        raise BrueckenError(f"{was} fehlt: {pfad}")
    try:
        inhalt = json.loads(pfad.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise BrueckenError(f"{was} ist kein lesbares JSON ({pfad}): {e}") from e
    if not isinstance(inhalt, dict):
        raise BrueckenError(f"{was} ist kein Wörterbuch, sondern {type(inhalt).__name__}.")
    return inhalt


def lies_auftrag(verzeichnis, *, fremde_freigabe_gilt: bool = False) -> dict:
    """Ein Auftragsverzeichnis der fremden Warteschlange lesen.

    Args:
        verzeichnis: Der Ordner ``<store>/vis-…``.
        fremde_freigabe_gilt: Ob der von der **Brücke selbst erzeugte** Freigabe-Token
            als menschliche Freigabe zählen soll. Vorgabe ``False`` — siehe Modulkopf.
            Das ist eine Entscheidung des Betreibers und keine des Programms.

    Returns:
        ``{job_id, status, verzeichnis, szene, laufzettel, modell, ausgabe,
        freigegeben, freigabe_grund, warnungen, maengel}``

        ``szene`` ist die bereits übersetzte Fassung aus
        :func:`aiimaging.kosmo_szene.lies_szene`; ihre ``maengel`` und ``warnungen``
        wandern hier mit hinein.

    Raises:
        BrueckenError: Verzeichnis fehlt, Laufzettel oder Szene fehlen oder sind
            unlesbar. Alles, was sich sinnvoll melden lässt, wird gemeldet statt geworfen
            — geworfen wird nur, wenn es gar nichts zu lesen gibt.
    """
    ordner = Path(verzeichnis)
    if not ordner.is_dir():
        raise BrueckenError(f"Kein Auftragsverzeichnis: {ordner}")

    warnungen: list[str] = []
    maengel: list[str] = []

    if not VERZEICHNIS_MUSTER.match(ordner.name):
        warnungen.append(
            f"Der Ordnername {ordner.name!r} entspricht nicht der Form der fremden "
            f"Warteschlange (vis-<zahl>-<sechs Hexziffern>). Gelesen wird trotzdem — "
            f"aber ihre eigene Auflistung übergeht solche Ordner möglicherweise."
        )

    laufzettel = _lies_json(ordner / DATEI_LAUFZETTEL, "Laufzettel (job.json)")
    job_id = laufzettel.get("job_id")
    if not job_id:
        maengel.append("Der Laufzettel trägt keine 'job_id'. Ohne sie lässt sich kein "
                       "Ergebnis zuordnen.")

    status = laufzettel.get("status")
    if status not in STATUSSE:
        warnungen.append(
            f"Unbekannter Status {status!r}. Bekannt: {', '.join(STATUSSE)}."
        )

    # Der Pfad zur Szene steht im Laufzettel — aber absolut und von einem fremden
    # Rechner. Wir nehmen die Datei NEBEN dem Laufzettel, denn nur die liegt sicher hier.
    szene_pfad = ordner / DATEI_SZENE
    roh = _lies_json(szene_pfad, "Szene (render-scene.json)")
    szene = kosmo_szene.lies_szene(roh)
    warnungen.extend(szene["warnungen"])
    maengel.extend(szene["maengel"])

    modell = ordner / DATEI_MODELL
    if not modell.is_file():
        maengel.append(f"Die Geometrie fehlt: {DATEI_MODELL} liegt nicht im Verzeichnis.")

    freigegeben, grund = _freigabe(laufzettel, fremde_freigabe_gilt)
    if not freigegeben:
        maengel.append(grund)

    return {
        "job_id": job_id,
        "status": status,
        "verzeichnis": ordner,
        "laufzettel": laufzettel,
        "szene": szene,
        "modell": modell if modell.is_file() else None,
        "ausgabe": ordner / "out",
        "freigegeben": freigegeben,
        "freigabe_grund": grund,
        "warnungen": tuple(warnungen),
        "maengel": tuple(maengel),
    }


def _freigabe(laufzettel: dict, fremde_freigabe_gilt: bool) -> tuple[bool, str]:
    """Zählt der Token dieses Auftrags als Freigabe? — und warum.

    Der ganze Kern des Moduls steht in dieser Funktion. Siehe Modulkopf.
    """
    token = laufzettel.get("approval_token")
    if not token:
        return False, ("Der Auftrag trägt keinen Freigabe-Token. Er bleibt liegen — das "
                       "ist der Freeze-Schutz und kein Fehler.")
    if not isinstance(token, str) or not token.startswith(TOKEN_VORSATZ):
        return False, (f"Der Freigabe-Token hat nicht die vereinbarte Form "
                       f"({TOKEN_VORSATZ}…): {token!r}")
    if not fremde_freigabe_gilt:
        return False, (
            "Der Freigabe-Token dieses Auftrags stammt von der Brücke SELBST — ihr "
            "'create_job' erzeugt ihn mit 'secrets.token_hex'. Kein Mensch hat ihn "
            "erteilt. Er sieht aus wie unserer, heisst wie unserer und bedeutet etwas "
            "anderes.\n"
            "Unser 'enqueue_render' lässt einen Auftrag ohne menschliche Freigabe "
            "ausdrücklich liegen und rührt die Grafikkarte nicht an — das ist der Grund, "
            "warum die Leistungsgrenze eingehalten wird. Wer die fremde Warteschlange "
            "bedient, hebelt das aus, ohne dass irgendwo etwas rot wird.\n"
            "Wer das will, sagt es ausdrücklich: fremde_freigabe_gilt=True. Eine "
            "Freigabe, die eine Maschine sich selbst erteilt, ist keine."
        )
    return True, ("Der von der Brücke erzeugte Token gilt auf ausdrückliche Entscheidung "
                  "des Betreibers als Freigabe.")


def offene_auftraege(store, *, nur_status=(STATUS_QUEUED,)) -> list[Path]:
    """Alle Auftragsverzeichnisse eines Ablageorts, die auf Arbeit warten.

    Sortiert nach Verzeichnisnamen — der trägt den Zeitstempel, also ist das die
    Reihenfolge des Eingangs. Ein Auftrag, der zuerst kam, wird zuerst bedient; alles
    andere wäre für den Wartenden nicht nachvollziehbar.

    Verzeichnisse ohne Laufzettel und solche mit unlesbarem Laufzettel werden
    **übersprungen, nicht gemeldet** — sie sind der Normalfall, während die Brücke gerade
    schreibt. Wer sie melden wollte, bekäme bei jedem Durchlauf eine Warnung über einen
    Ordner, der eine Sekunde später in Ordnung ist.
    """
    ordner = Path(store)
    if not ordner.is_dir():
        return []
    treffer = []
    for d in sorted(ordner.iterdir()):
        if not d.is_dir() or not VERZEICHNIS_MUSTER.match(d.name):
            continue
        zettel = d / DATEI_LAUFZETTEL
        if not zettel.is_file():
            continue
        try:
            status = json.loads(zettel.read_text(encoding="utf-8")).get("status")
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            continue
        if nur_status is None or status in nur_status:
            treffer.append(d)
    return treffer


def setze_status(verzeichnis, status: str, *, fehler: str | None = None) -> dict:
    """Den Laufzettel fortschreiben — und nur ihn.

    Der Laufzettel ist das, worauf die fremde Oberfläche schaut. Wer ihn nicht
    fortschreibt, lässt einen Auftrag für immer auf „läuft" stehen; wer ihn zu früh auf
    ``done`` setzt, lässt eine Oberfläche ein Ergebnis suchen, das es nicht gibt.

    Geschrieben wird **atomar** (erst daneben, dann umbenannt). Die fremde Oberfläche
    liest im Sekundentakt; ein halb geschriebener Laufzettel wäre für sie ein
    JSON-Fehler, und sie hätte recht.

    Raises:
        BrueckenError: unbekannter Status, oder der Laufzettel fehlt.
    """
    if status not in STATUSSE:
        raise BrueckenError(
            f"Unbekannter Status {status!r}. Erlaubt: {', '.join(STATUSSE)}. Es wird "
            f"nicht auf einen Vorgabewert zurückgesetzt — welcher gilt, kann dieses "
            f"Modul nicht für den Aufrufer entscheiden."
        )
    ordner = Path(verzeichnis)
    ziel = ordner / DATEI_LAUFZETTEL
    laufzettel = _lies_json(ziel, "Laufzettel (job.json)")
    laufzettel["status"] = status
    laufzettel["updated_at"] = _jetzt()
    if fehler is not None:
        laufzettel["error"] = fehler
    _schreibe_atomar(ziel, laufzettel)
    return laufzettel


def schreibe_ergebnis(verzeichnis, bilder, *, job_id: str | None = None,
                      geometrie_urteil=None, stil_urteil=None, zeiten=None,
                      status: str = STATUS_DONE, uebersprungen: bool = False) -> dict:
    """Das Ergebnis danebenlegen und den Laufzettel fortschreiben — in dieser Reihenfolge.

    **Die Reihenfolge ist die ganze Sorgfalt dieser Funktion.** Die fremde Oberfläche
    liest den Laufzettel; steht dort ``done``, holt sie das Ergebnis. Wer den Laufzettel
    zuerst setzt, erzeugt ein Zeitfenster, in dem sie ein Ergebnis sucht, das noch nicht
    da ist — und einen Fehler meldet, den niemand nachstellen kann.

    Args:
        bilder: Pfade oder Namen der erzeugten Bilder. Sie werden auf **relative Namen**
            gekürzt: Ihre Oberfläche holt sie über einen Endpunkt, der nur den Dateinamen
            kennt (``/jobs/{id}/artifacts/{name}``). Ein absoluter Pfad ginge dort ins
            Leere — und trüge nebenbei einen Rechnernamen nach draussen (Regel 3).
        job_id: Ohne Angabe aus dem Laufzettel gelesen.
        uebersprungen: Der Auftrag trug ``skip: true``. Wird nach
            :func:`aiimaging.kosmo_szene.als_ergebnis` durchgereicht, damit im Ergebnis
            **abbestellt** steht und nicht **ungeprüft** — zwei verschiedene Lagen, und
            nur eine davon verlangt einen zweiten Lauf.

    Returns:
        Das geschriebene Ergebnis, wie es in der Datei steht.
    """
    ordner = Path(verzeichnis)
    laufzettel = _lies_json(ordner / DATEI_LAUFZETTEL, "Laufzettel (job.json)")
    kennung = job_id or laufzettel.get("job_id")
    if not kennung:
        raise BrueckenError(
            "Kein 'job_id' — weder übergeben noch im Laufzettel. Ein Ergebnis ohne "
            "Kennung lässt sich keinem Auftrag zuordnen."
        )

    namen = [Path(b).name for b in (bilder or [])]
    ergebnis = kosmo_szene.als_ergebnis(
        kennung, namen, geometrie_urteil=geometrie_urteil,
        stil_urteil=stil_urteil, zeiten=zeiten, uebersprungen=uebersprungen)

    # ZUERST das Ergebnis, DANN der Laufzettel — siehe Docstring.
    _schreibe_atomar(ordner / DATEI_ERGEBNIS, kosmo_szene.nur_vertragsfelder(ergebnis))
    setze_status(ordner, status)
    return ergebnis


def _schreibe_atomar(ziel: Path, inhalt: dict) -> None:
    """Erst daneben schreiben, dann umbenennen.

    Die fremde Oberfläche liest im Sekundentakt. Ein halb geschriebenes JSON wäre für sie
    ein Fehler, und sie hätte recht — dieselbe Vorsicht wie in ``aiimaging.jobs``.
    """
    ziel = Path(ziel)
    daneben = ziel.with_suffix(ziel.suffix + ".teil")
    daneben.write_text(json.dumps(inhalt, indent=2, ensure_ascii=False), encoding="utf-8")
    daneben.replace(ziel)
