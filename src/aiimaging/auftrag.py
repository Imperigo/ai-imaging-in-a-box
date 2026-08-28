"""Aufträge an die HomeStation — über das Repo als Übergabeort.

Warum es das gibt
-----------------
Der Container, in dem entwickelt wird, hat keine GPU und keine Modellgewichte. Die
HomeStation hat beides (RTX 5090, 32 GB VRAM, Ryzen 9 9950X, 96 GB RAM, Modelle unter
`/ai`). Beide sehen dasselbe Git-Repo — also ist das Repo der Übergabeort: Hier wird ein
Auftrag abgelegt, dort ausgeführt, das Ergebnis kommt zurück.

Kein Netzwerkdienst, kein offener Port, keine Anmeldedaten. Ein Auftrag ist eine Datei,
ein Ergebnis ist eine Datei. Das ist dieselbe Haltung wie bei den Prozessgrenzen: die
einfachste Form, die trägt.

Die Spannung mit Regel 3 — und wie sie aufgelöst wird
-----------------------------------------------------
Regel 3 verbietet echte Projektdaten im Repo: keine IFC aus echten Aufträgen, keine
Renders, keine darauf trainierten Gewichte. Ein Auftrag darf die Geometrie also **nicht
mitbringen**.

Deshalb:

* Ein Auftrag **verweist** auf Geometrie, die auf der HomeStation liegt
  (``geometrie_pfad``, z.B. unter ``/ai/``), oder er lässt die synthetische Testgeometrie
  **vor Ort erzeugen** (``synthetisch: true``) — dann reist gar nichts.
* Ein Ergebnis trägt **nur Zahlen**: Messwerte, Urteile, Laufzeiten, Dateinamen. Niemals
  Bilder, niemals Geometrie. Die Bilder bleiben auf der HomeStation.

Das ist keine Einschränkung, sondern genau das, was gebraucht wird: Für die
Schwellenstudie (Phase 4) zählen die Messwerte, nicht die Bilder.

Hardware-Auflagen, die mitreisen müssen
---------------------------------------
Die RTX 5090 löst unter ungebremster Volllast die Netzteil-Schutzschaltung aus. Aus dem
Vorläuferprojekt sind zwei Auflagen belegt, die jeder Auftrag mitführt:

* **400-W-Cap** (``leistungsgrenze_w``) — vor dem Lauf zu setzen.
* **GPU-Leerlauf-Gate** (``nur_bei_leerlauf``) — nur starten, wenn die Karte frei ist;
  im Zweifel nicht starten (fail-closed).

Beide werden hier nur **mitgeführt und deklariert**, nicht durchgesetzt — durchsetzen
kann sie nur, wer die Hardware sieht. Der Ausführende auf der HomeStation ist dafür
verantwortlich, und `tools/homeworker.py` tut es.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

#: **Es gibt zwei Worker, und sie können nicht dasselbe.** Ein Auftrag, der nicht sagt,
#: an wen er geht, landet bei niemandem — oder schlimmer, beim Falschen.
#:
#: * :data:`WORKER_LOCAL` — die HomeStation. Hat GPU, Blender, `.venv-ifc`, unser Repo.
#:   Misst, rendert, prüft. Liest ``auftraege/offen/`` und legt Ergebnisse daneben.
#: * :data:`WORKER_CLOUD` — der Worker an KosmoOrbit. Hat **unser Repo nicht**; er hält
#:   den Vertrag und die Warteschlange der Vis-Seite. Was er tun soll, betrifft **ihren**
#:   Vertrag, nie unseren Code.
#: * :data:`WORKER_UI` — der Kosmo-UI-Worker. **Seit dem 26.08.2026 zuständig für die
#:   ganze Oberfläche von KosmoOrbit** (Owner-Hinweis). Er hat unser Repo **als Quelle**
#:   — ein Auftrag in ``auftraege/offen/`` erreicht ihn also über git, ohne Umweg über
#:   den Chat.
#:
#: Die Trennung ist nicht Ordnungsliebe: Ein Messauftrag an den Cloud-Worker wäre
#: unerfüllbar (keine GPU, keine Geometrie), ein Vertragsauftrag an die HomeStation liefe
#: ins Leere (sie kann ihr Schema nicht ändern), und ein Oberflächenauftrag an einen von
#: beiden landete bei jemandem, der die Oberfläche nicht mehr baut.
#:
#: **Warum `ui` und `cloud` getrennt bleiben, obwohl beide „drüben" sind:** Der Vertrag
#: und die Oberfläche sind zwei Gegenstände. *Welchen Feldnamen ein QA-Block je Kamera
#: bekommt*, ist eine Vertragsfrage; *ob neben der Zahl ihr Vorbehalt steht*, eine
#: Oberflächenfrage. Sie an dieselbe Stelle zu schicken hiesse, dass eine von beiden
#: liegen bleibt, weil sie nicht zum Auftrag des Lesers gehört.
#: * :data:`WORKER_KERN` — **diese Entwicklungssitzung selbst.** Seit dem 28.08.2026
#:   (Owner-Entscheid), und der Anlass ist eine Fehladressierung: Die HomeStation wollte
#:   etwas von *uns* — eine Änderung an ``homeworker.py`` — und musste den Auftrag an
#:   ``cloud`` schicken, weil es für uns keine Adresse gab. Dort hätte ``auftragspost``
#:   ihn folgerichtig in das fremde Repo gelegt.
#:
#:   *Drei Empfänger und kein Absender: Die Vokabel kannte nur eine Richtung. Ein Auftrag
#:   ohne Adresse wird erfunden, und eine erfundene Adresse führt irgendwohin.*
WORKER_LOCAL = "local"
WORKER_CLOUD = "cloud"
WORKER_UI = "ui"
WORKER_KERN = "kern"
WORKER = (WORKER_LOCAL, WORKER_CLOUD, WORKER_UI, WORKER_KERN)

SCHEMA_AUFTRAG = "aiimaging.homeworker-auftrag/v1"
SCHEMA_ERGEBNIS = "aiimaging.homeworker-ergebnis/v1"

#: Verzeichnisse im Repo. Bewusst im Repo und nicht in `/tmp` — sie sind der Übergabeort.
VERZ_OFFEN = "auftraege/offen"
VERZ_ERGEBNISSE = "auftraege/ergebnisse"

#: Belegte Auflagen der HomeStation (KosmoVis-Bericht 2026-06-30).
LEISTUNGSGRENZE_W = 400
GPU_LEERLAUF_W = 120
GPU_LEERLAUF_MEM_GB = 8

ARTEN = frozenset({"multipass", "render", "qa"})

_ID_MUSTER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class AuftragError(ValueError):
    """Ein Auftrag oder Ergebnis verletzt den Vertrag."""


def _jetzt() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def neue_auftrag_id(zeitstempel: str | None = None, laufnummer: int = 1) -> str:
    """Form: ``auf-<JJJJMMTT>-<NN>``. Beide Teile injizierbar, damit Tests reproduzierbar sind."""
    stamp = zeitstempel or datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"auf-{stamp}-{laufnummer:02d}"


def _pruefe_id(auftrag_id) -> str:
    """Eine Kennung ist ein Name, kein Pfad.

    Positivliste statt Verbotsliste: Verbotslisten übersehen immer etwas, und die
    Kennung wird zum Dateinamen im Repo.
    """
    if not isinstance(auftrag_id, str) or not _ID_MUSTER.match(auftrag_id):
        raise AuftragError(
            f"Unzulässige Auftrags-Kennung {auftrag_id!r}. Erlaubt sind Buchstaben, "
            f"Ziffern, Punkt, Bindestrich und Unterstrich; kein '/' und kein '..'."
        )
    if Path(auftrag_id).name != auftrag_id:
        raise AuftragError(f"Kennung {auftrag_id!r} ist ein Pfad, kein Name.")
    return auftrag_id


def baue_auftrag(*, auftrag_id: str, art: str, beschreibung: str,
                 worker: str = WORKER_LOCAL, anweisung: str | None = None,
                 synthetisch: bool = True, geometrie_pfad: str | None = None,
                 params: dict | None = None,
                 leistungsgrenze_w: int = LEISTUNGSGRENZE_W,
                 nur_bei_leerlauf: bool = True) -> dict:
    """Einen Auftrag bauen, der ohne Rückfragen ausführbar ist.

    Args:
        art: ``multipass`` (nur Blender), ``render`` (mit Bildmodell), ``qa`` (nur Messen).
        worker: :data:`WORKER_LOCAL` oder :data:`WORKER_CLOUD`. Vorgabe ist die
            HomeStation, weil sie bis zum 22.08.2026 die einzige war — aber die Angabe
            gehört ausdrücklich in jeden neuen Auftrag. Ein Messauftrag an den
            Cloud-Worker wäre unerfüllbar, ein Vertragsauftrag an die HomeStation liefe
            ins Leere.
        anweisung: **Was zu tun ist, vollständig** — die Schritte, ihre Reihenfolge, was
            zurückkommen soll und was ausdrücklich nicht getan werden soll. Steht sie hier,
            bleibt ``beschreibung`` die Überschrift.

            *Warum das ein eigenes Feld ist, seit dem 26.08.2026:* `CLAUDE.md` verlangt
            seit dem 22.08.2026, dass der Auftrag seine Anweisung **in sich** trägt — kein
            „siehe Dokument XY", denn ein Auftrag, der auf etwas verweist, das der Worker
            erst suchen muss, ist ein halber Auftrag. Aus derselben Regel stammt das
            Pflichtfeld ``worker``. **Das ist damals in den Code gelangt, die Anweisung
            nicht:** Vier Tage lang trugen die Aufträge sie im Fliesstext von
            ``beschreibung``, wo sich kein Leser auf sie verlassen kann, und diese
            Funktion konnte das geltende Format gar nicht bauen. Nachgetragen am
            26.08.2026 zusammen mit `tests/test_auftraege.py`, dem Wächter über den
            wirklichen Dateien.

            ``None`` lässt das Feld weg — für die Form vor dem 26.08., bei der die
            Anweisung in ``beschreibung`` steht.
        synthetisch: ``True`` = die Testgeometrie wird vor Ort erzeugt, es reist nichts.
            ``False`` verlangt ``geometrie_pfad`` auf der HomeStation.
        geometrie_pfad: Pfad **auf der HomeStation**, nie eine Datei im Repo (Regel 3).

    Raises:
        AuftragError: bei unbekannter Art, fehlender Geometriequelle — oder wenn jemand
            versucht, echte Geometrie über das Repo zu schicken.
    """
    _pruefe_id(auftrag_id)
    if art not in ARTEN:
        raise AuftragError(f"Unbekannte Art {art!r}. Bekannt: {', '.join(sorted(ARTEN))}")
    if not beschreibung or not beschreibung.strip():
        raise AuftragError(
            "Ein Auftrag braucht eine Beschreibung. Wer ihn später liest — auch eine "
            "frische Sitzung auf der HomeStation — muss ohne Rückfrage verstehen, worum es geht."
        )
    if not synthetisch and not geometrie_pfad:
        raise AuftragError(
            "Ohne 'synthetisch' braucht der Auftrag einen 'geometrie_pfad' auf der "
            "HomeStation. Geometrie darf nicht über das Repo reisen (Regel 3)."
        )
    if synthetisch and geometrie_pfad:
        raise AuftragError(
            "'synthetisch' und 'geometrie_pfad' zugleich ist mehrdeutig — genau eine "
            "Geometriequelle angeben."
        )

    return {
        "schema": SCHEMA_AUFTRAG,
        "worker": worker,
        "auftrag_id": auftrag_id,
        "art": art,
        "beschreibung": beschreibung.strip(),
        # Nur aufnehmen, wenn wirklich eine da ist: Ein leeres `anweisung` sähe aus wie
        # ein gefuelltes Feld und waere schlimmer als gar keins.
        **({"anweisung": anweisung.strip()} if anweisung and anweisung.strip() else {}),
        "erstellt": _jetzt(),
        "geometrie": {
            "synthetisch": bool(synthetisch),
            "pfad": geometrie_pfad,
            "erzeugen_mit": "python3 tools/make_test_ifc.py build/testbau.ifc" if synthetisch else None,
        },
        "params": dict(params or {}),
        "auflagen": {
            # Nur deklariert, nicht durchgesetzt — durchsetzen kann sie nur, wer die
            # Hardware sieht. `tools/homeworker.py` tut es.
            "leistungsgrenze_w": int(leistungsgrenze_w),
            "nur_bei_leerlauf": bool(nur_bei_leerlauf),
            "leerlauf_schwelle_w": GPU_LEERLAUF_W,
            "leerlauf_schwelle_mem_gb": GPU_LEERLAUF_MEM_GB,
            "hinweis": "RTX 5090 löst ohne Leistungsgrenze unter Volllast die "
                       "Netzteil-Schutzschaltung aus. Im Zweifel nicht starten.",
        },
        "rueckgabe": {
            "verzeichnis": VERZ_ERGEBNISSE,
            "nur_zahlen": True,
            "hinweis": "Nur Messwerte, Urteile und Dateinamen zurückgeben. KEINE Bilder, "
                       "KEINE Geometrie — Regel 3. Die Bilder bleiben auf der HomeStation.",
        },
    }


def pruefe_auftrag(satz: dict) -> list[str]:
    """Einen Auftrag gegen den Vertrag prüfen. Leere Liste heisst in Ordnung."""
    maengel: list[str] = []
    if not isinstance(satz, dict):
        return ["Auftrag ist kein Objekt."]
    if satz.get("schema") != SCHEMA_AUFTRAG:
        maengel.append(f"Falsches Schema: {satz.get('schema')!r} statt {SCHEMA_AUFTRAG!r}")
    for feld in ("auftrag_id", "art", "beschreibung", "geometrie", "auflagen"):
        if not satz.get(feld):
            maengel.append(f"Pflichtfeld {feld!r} fehlt")
    if satz.get("art") and satz["art"] not in ARTEN:
        maengel.append(f"Unbekannte Art {satz['art']!r}")
    # `worker` ist seit dem 22.08.2026 Pflicht. Ohne die Angabe weiss niemand, wer den
    # Auftrag ausführen soll — und die beiden können nicht dasselbe.
    if "worker" not in satz:
        maengel.append(
            f"Kein 'worker'. Pflicht seit 22.08.2026: {WORKER_LOCAL!r} (HomeStation, hat "
            f"GPU und Repo) oder {WORKER_CLOUD!r} (KosmoOrbit, hat unser Repo NICHT). Ein "
            f"Auftrag ohne Empfänger landet bei niemandem.")
    elif satz["worker"] not in WORKER:
        maengel.append(
            f"Unbekannter worker {satz['worker']!r}; bekannt: {', '.join(WORKER)}")
    geom = satz.get("geometrie") or {}
    if isinstance(geom, dict) and not geom.get("synthetisch") and not geom.get("pfad"):
        maengel.append("Geometriequelle fehlt: weder synthetisch noch Pfad")
    return maengel


def schreibe_auftrag(satz: dict, repo_wurzel) -> Path:
    """Auftrag ins Repo legen — atomar, damit kein halber Auftrag eingecheckt wird.

    **Regel 3 wird hier durchgesetzt und nicht bloss erwähnt:** Benutzernamen in Pfaden
    werden durch :data:`NUTZER_ERSATZ` ersetzt, und die Zahl der Ersetzungen steht danach
    als ``regel3_ersetzt`` in der Datei. Bis zum 24.08.2026 wurde ein Auftrag darauf
    **überhaupt nicht** geprüft — :func:`_wehre_bilddaten_ab` lief nur über Ergebnisse.
    """
    maengel = pruefe_auftrag(satz)
    if maengel:
        raise AuftragError("Auftrag unvollständig: " + "; ".join(maengel))
    satz, _ = regel3_saeubern(satz)

    ziel_verz = Path(repo_wurzel) / VERZ_OFFEN
    ziel_verz.mkdir(parents=True, exist_ok=True)
    ziel = ziel_verz / f"{_pruefe_id(satz['auftrag_id'])}.json"

    text = json.dumps(satz, indent=2, ensure_ascii=False) + "\n"
    fd, temp = tempfile.mkstemp(dir=str(ziel_verz), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temp, ziel)
    except BaseException:
        Path(temp).unlink(missing_ok=True)
        raise
    return ziel


def offene_auftraege(repo_wurzel) -> list[dict]:
    """Alle offenen Aufträge lesen, älteste zuerst.

    Ein fehlendes Verzeichnis ist kein Fehler — vor dem ersten Auftrag gibt es keines,
    und ein pollender Ausführender soll deswegen nicht abbrechen.
    """
    verz = Path(repo_wurzel) / VERZ_OFFEN
    if not verz.is_dir():
        return []
    saetze = []
    for pfad in sorted(verz.glob("*.json")):
        try:
            satz = json.loads(pfad.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise AuftragError(f"Auftrag {pfad.name} ist unlesbar: {e}") from e

        # DIE VERTRAGSPRUEFUNG AUCH AUF DEM LESEWEG — Vorschlag der HomeStation
        # (auf-20260828-64, V4), und der Anlass ist ihr eigener Fehler: Ihr `auf-63` trug
        # eine Art, die es nicht gibt, und kein `rueckgabe`-Feld. Die Datei kam an
        # `schreibe_auftrag` VORBEI in den Ordner und hat eine ganze Testsammlung rot
        # gemacht — zwei Tage lang, und niemand sah warum.
        #
        # GEMELDET UND NICHT GEWORFEN: Ein kaputter Auftrag darf die anderen
        # zweiundsechzig nicht blockieren. Wer liest, bekommt die Liste; was daran fehlt,
        # steht in `maengel` daneben. *Eine Pruefung, die den ganzen Ordner unlesbar
        # macht, wird abgeschaltet.*
        maengel = pruefe_auftrag(satz)
        if maengel:
            satz["maengel"] = maengel
        saetze.append(satz)
    return sorted(saetze, key=lambda s: s.get("erstellt", ""))


def baue_ergebnis(*, auftrag_id: str, status: str, messwerte: dict | None = None,
                  urteil: dict | None = None, dauer_s: float | None = None,
                  umgebung: dict | None = None, fehler: str | None = None) -> dict:
    """Ein Ergebnis bauen — **nur Zahlen**, siehe Modul-Docstring.

    Raises:
        AuftragError: wenn jemand versucht, Bilddaten zurückzugeben.
    """
    _pruefe_id(auftrag_id)
    if status not in {"ok", "fehler", "abgelehnt", "uebersprungen"}:
        raise AuftragError(f"Unbekannter Status {status!r}")

    satz = {
        "schema": SCHEMA_ERGEBNIS,
        "auftrag_id": auftrag_id,
        "status": status,
        "beendet": _jetzt(),
        "dauer_s": dauer_s,
        "messwerte": dict(messwerte or {}),
        "urteil": dict(urteil or {}),
        "umgebung": dict(umgebung or {}),
        "fehler": fehler,
    }
    _wehre_bilddaten_ab(satz)
    return satz


#: Pfadmuster, in denen ein **Benutzername** steckt. Regel 3, dritter Absatz.
#:
#: **Der Anlass ist ein Fund im eigenen Repo** (24.08.2026): In fünf Ergebnisdateien und
#: einem Sitzungsprotokoll stand seit dem 18.08. der Klarname des Owners — hereingekommen
#: nicht durch Nachlässigkeit beim Schreiben, sondern durch **Blender-Fehlertexte**, die
#: den vollen Pfad des Skripts mitbringen. Niemand hat ihn dort hingeschrieben; er ist
#: mitgereist.
#:
#: :func:`_wehre_bilddaten_ab` sah genau diese Felder an — aber nur auf Binärdaten und
#: Länge. Ein Name in einem Pfad ist beides nicht.
#:
#: Am selben Tag hat die HomeStation denselben Fehler auf ihrer Seite gefunden und von
#: Hand behoben (*«die Anleitung zur Regel verletzte die Regel»*). Von Hand heisst: beim
#: nächsten Mal wieder.
HEIMATMUSTER = (
    r"(/home/)([^/\s\"']+)",
    r"(/Users/)([^/\s\"']+)",
    r"([Cc]:\\Users\\)([^\\\s\"']+)",
)

#: Was anstelle des Namens steht. Der **Rest des Pfades bleibt** — er ist die Auskunft.
NUTZER_ERSATZ = "<nutzer>"


def ohne_kennungen(text: str) -> tuple[str, int]:
    """Benutzernamen aus Pfaden entfernen, den Rest des Pfades behalten.

    ``/home/vorname-nachname/projekt/datei.py`` → ``/home/<nutzer>/projekt/datei.py``

    **Warum ersetzen und nicht ablehnen.** Diese Namen stecken in Fehlertexten, und ein
    Fehlertext ist die wertvollste Zeile eines fehlgeschlagenen Laufs. Ihn zurückzuweisen
    hiesse, die Messung wegzuwerfen, um die Regel einzuhalten — und die nächste
    Rückmeldung käme dann von Hand gekürzt oder gar nicht.

    **Und warum es trotzdem keine stille Reparatur ist:** :func:`schreibe_auftrag` und
    :func:`schreibe_ergebnis` schreiben die Zahl der Ersetzungen in den Satz. Wer eine
    Datei liest, sieht, dass etwas ersetzt wurde.

    Returns:
        ``(text, anzahl)``.
    """
    import re

    gesamt = 0
    for muster in HEIMATMUSTER:
        text, n = re.subn(muster, lambda m: m.group(1) + NUTZER_ERSATZ, text)
        gesamt += n
    return text, gesamt


def _kennungen_ersetzen(wert):
    """Rekursiv durch den Satz — Zeichenketten, Listen, Wörterbücher, auch Schlüssel."""
    if isinstance(wert, str):
        return ohne_kennungen(wert)
    if isinstance(wert, dict):
        neu, gesamt = {}, 0
        for k, v in wert.items():
            k2, nk = _kennungen_ersetzen(k) if isinstance(k, str) else (k, 0)
            v2, nv = _kennungen_ersetzen(v)
            neu[k2] = v2
            gesamt += nk + nv
        return neu, gesamt
    if isinstance(wert, list):
        paare = [_kennungen_ersetzen(v) for v in wert]
        return [w for w, _ in paare], sum(n for _, n in paare)
    if isinstance(wert, tuple):
        paare = [_kennungen_ersetzen(v) for v in wert]
        return tuple(w for w, _ in paare), sum(n for _, n in paare)
    return wert, 0


def regel3_saeubern(satz: dict) -> tuple[dict, int]:
    """Den ganzen Satz von Benutzernamen befreien und die Zahl zurückgeben.

    Der Satz wird **nicht** an Ort und Stelle geändert — eine Funktion, die ihr Argument
    umschreibt, macht aus einer Prüfung eine Nebenwirkung.

    Raises:
        AuftragError: ``satz`` ist kein Wörterbuch.
    """
    if not isinstance(satz, dict):
        raise AuftragError(f"satz ist kein Wörterbuch: {type(satz).__name__}")
    sauber, n = _kennungen_ersetzen(satz)
    if n:
        sauber["regel3_ersetzt"] = n
    return sauber, n


def _wehre_bilddaten_ab(satz: dict) -> None:
    """Regel 3 in ausführbarer Form: Bilddaten dürfen nicht ins Repo.

    Geprüft wird auf eingebettete Binärdaten (base64-Blöcke) und auf auffällig lange
    Zeichenketten. Ein Dateiname ist erlaubt und erwünscht — der Inhalt nicht.
    """
    def _pruefe(wert, pfad: str):
        if isinstance(wert, str):
            if len(wert) > 2048:
                raise AuftragError(
                    f"Feld {pfad} ist {len(wert)} Zeichen lang — das sieht nach "
                    f"eingebetteten Daten aus. Ergebnisse tragen nur Zahlen und "
                    f"Dateinamen (Regel 3)."
                )
            if wert.startswith("data:") or wert.startswith("iVBORw0KGgo"):
                raise AuftragError(
                    f"Feld {pfad} enthält eingebettete Bilddaten. Die Bilder bleiben "
                    f"auf der HomeStation (Regel 3)."
                )
        elif isinstance(wert, dict):
            for k, v in wert.items():
                _pruefe(v, f"{pfad}.{k}")
        elif isinstance(wert, (list, tuple)):
            for i, v in enumerate(wert):
                _pruefe(v, f"{pfad}[{i}]")

    for feld in ("messwerte", "urteil", "umgebung"):
        _pruefe(satz.get(feld), feld)


def schreibe_ergebnis(satz: dict, repo_wurzel) -> Path:
    """Ergebnis ins Repo legen — atomar.

    **Und hier greift Regel 3 am ehesten**, denn hier kommen die Fehlertexte an: Ein
    Blender-Traceback bringt den vollen Pfad des Skripts mit, und darin steht der
    Benutzername. Genau so sind am 18.08.2026 fünf Ergebnisdateien mit dem Klarnamen des
    Owners in dieses öffentliche Repo gelangt — hingeschrieben hat ihn niemand.
    """
    if satz.get("schema") != SCHEMA_ERGEBNIS:
        raise AuftragError(f"Falsches Schema: {satz.get('schema')!r}")
    satz, _ = regel3_saeubern(satz)
    _wehre_bilddaten_ab(satz)

    ziel_verz = Path(repo_wurzel) / VERZ_ERGEBNISSE
    ziel_verz.mkdir(parents=True, exist_ok=True)
    ziel = ziel_verz / f"{_pruefe_id(satz['auftrag_id'])}.json"

    text = json.dumps(satz, indent=2, ensure_ascii=False) + "\n"
    fd, temp = tempfile.mkstemp(dir=str(ziel_verz), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temp, ziel)
    except BaseException:
        Path(temp).unlink(missing_ok=True)
        raise
    return ziel


def lies_ergebnis(auftrag_id: str, repo_wurzel) -> dict | None:
    """Das Ergebnis zu einem Auftrag lesen — ``None``, solange keines vorliegt."""
    pfad = Path(repo_wurzel) / VERZ_ERGEBNISSE / f"{_pruefe_id(auftrag_id)}.json"
    if not pfad.is_file():
        return None
    return json.loads(pfad.read_text(encoding="utf-8"))


#: Die fünf Zustände eines Auftrags. **Sie werden ABGELEITET, nie gesetzt.**
#:
#: **Der Befund kommt vom Gerät** (`auf-20260828-64`, 28.08.2026): 63 Aufträge in
#: ``offen/``, 44 Ergebnisse, **40 Paare** — vierzig Aufträge lagen dort mit einem
#: Ergebnis daneben. Und ``0 von 63`` trugen ein ``status``-Feld.
#:
#: *Ein Ordner, der von Hand gepflegt werden muss, verfällt. Ein Zustand, der sich aus
#: dem Vorhandensein eines Ergebnisses ableitet, verfällt nicht.*
#:
#: **Warum fünf und nicht zwei** (Owner-Entscheid 28.08.2026): «Ergebnis da» und
#: «beantwortet» sind nicht dasselbe. Gemessen: Von zwei ``cloud``-Aufträgen mit Ergebnis
#: waren **zwei von zwei** Weiterleitungsvermerke und keine Antworten. Ein Auftrag, dessen
#: Ergebnis ``fehler`` sagt, ist gerechnet worden — beantwortet ist er nicht.
ZUSTAND_OFFEN = "offen"
ZUSTAND_BEANTWORTET = "beantwortet"
ZUSTAND_GERECHNET = "gerechnet, nicht beantwortet"
ZUSTAND_WEITERGEREICHT = "weitergereicht"
ZUSTAND_ZURUECKGEZOGEN = "zurueckgezogen"

ZUSTAENDE = (ZUSTAND_OFFEN, ZUSTAND_BEANTWORTET, ZUSTAND_GERECHNET,
             ZUSTAND_WEITERGEREICHT, ZUSTAND_ZURUECKGEZOGEN)

#: Welche Zustände als **noch nicht beantwortet** gelten.
#:
#: ``weitergereicht`` gehört dazu: Der Auftrag liegt dann bei jemand anderem, aber die
#: Frage ist offen. ``zurueckgezogen`` gehört **nicht** dazu — sie ist gegenstandslos, und
#: das ist etwas anderes als unbeantwortet.
UNBEANTWORTET = (ZUSTAND_OFFEN, ZUSTAND_GERECHNET, ZUSTAND_WEITERGEREICHT)

#: Ergebnis-Status, die einen Auftrag NICHT beantworten. ``ok`` fehlt hier — nur er tut es.
_NICHT_BEANTWORTET = {"fehler", "abgelehnt", "uebersprungen"}


def zustand(auftrag_id: str, repo_wurzel) -> str:
    """Der abgeleitete Zustand eines Auftrags — aus seinem Ergebnis, nicht aus einem Feld.

    ======================================  ==================================
    Ergebnis                                Zustand
    ======================================  ==================================
    keines                                  ``offen``
    ``status: ok``                          ``beantwortet``
    ``fehler`` / ``abgelehnt`` /            ``gerechnet, nicht beantwortet``
    ``uebersprungen``
    ``art: weitergereicht…``                ``weitergereicht``
    ``art: zurueckgezogen``                 ``zurueckgezogen``
    ======================================  ==================================

    **Die beiden letzten sind nicht erfunden, beide Fälle liegen belegt vor** — ein
    zurückgezogener Auftrag (`auf-56`) und zwei Weiterleitungsvermerke, die als Antwort
    gezählt wurden und keine waren.

    *Die Reihenfolge ist wichtig: `art` wird VOR `status` gelesen. Ein Weiterleitungs-
    vermerk trägt ``status: ok`` — er ist trotzdem keine Antwort, und genau diese
    Verwechslung hat die Zählung verfälscht.*
    """
    ergebnis = lies_ergebnis(auftrag_id, repo_wurzel)
    if ergebnis is None:
        return ZUSTAND_OFFEN

    art = str(ergebnis.get("art") or "")
    if art.startswith("weitergereicht"):
        return ZUSTAND_WEITERGEREICHT
    if art.startswith("zurueckgezogen") or art.startswith("abgelehnt"):
        return ZUSTAND_ZURUECKGEZOGEN
    if str(ergebnis.get("status")) in _NICHT_BEANTWORTET:
        return ZUSTAND_GERECHNET
    return ZUSTAND_BEANTWORTET


def zustaende(repo_wurzel) -> dict[str, str]:
    """Der Zustand **jedes** Auftrags — die Zählung, die der Ordner nicht führt."""
    return {a["auftrag_id"]: zustand(a["auftrag_id"], repo_wurzel)
            for a in offene_auftraege(repo_wurzel)}


def unerledigt(repo_wurzel) -> list[dict]:
    """Aufträge, die **nicht beantwortet** sind — nicht bloss: ohne Ergebnisdatei.

    **Bis zum 28.08.2026 hiess das «ohne Ergebnis», und das war zu grob.** Gemessen
    (`auf-20260828-64`): Von zwei ``cloud``-Aufträgen mit Ergebnis waren zwei von zwei
    Weiterleitungsvermerke; ein weiteres trug ``status: erledigt`` mit leeren Messwerten.
    Sie galten als erledigt und waren es nicht.

    *Ein Ergebnis zu haben heisst nicht, beantwortet zu sein.*
    """
    return [a for a in offene_auftraege(repo_wurzel)
            if zustand(a["auftrag_id"], repo_wurzel) in UNBEANTWORTET]
