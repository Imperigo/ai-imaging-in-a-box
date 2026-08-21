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
#: * :data:`WORKER_CLOUD` — der Worker an KosmoOrbit. Hat **unser Repo nicht**; er baut
#:   an der Vis-Oberfläche. Was er tun soll, betrifft **ihren** Vertrag und ihre
#:   Oberfläche, nie unseren Code.
#:
#: Die Trennung ist nicht Ordnungsliebe: Ein Messauftrag an den Cloud-Worker wäre
#: unerfüllbar (keine GPU, keine Geometrie), und ein Vertragsauftrag an die HomeStation
#: liefe ins Leere (sie kann ihr Schema nicht ändern).
WORKER_LOCAL = "local"
WORKER_CLOUD = "cloud"
WORKER = (WORKER_LOCAL, WORKER_CLOUD)

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
                 worker: str = WORKER_LOCAL,
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
    """Auftrag ins Repo legen — atomar, damit kein halber Auftrag eingecheckt wird."""
    maengel = pruefe_auftrag(satz)
    if maengel:
        raise AuftragError("Auftrag unvollständig: " + "; ".join(maengel))

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
            saetze.append(json.loads(pfad.read_text(encoding="utf-8")))
        except json.JSONDecodeError as e:
            raise AuftragError(f"Auftrag {pfad.name} ist unlesbar: {e}") from e
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
    """Ergebnis ins Repo legen — atomar."""
    if satz.get("schema") != SCHEMA_ERGEBNIS:
        raise AuftragError(f"Falsches Schema: {satz.get('schema')!r}")
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


def unerledigt(repo_wurzel) -> list[dict]:
    """Aufträge, zu denen noch kein Ergebnis vorliegt."""
    return [a for a in offene_auftraege(repo_wurzel)
            if lies_ergebnis(a["auftrag_id"], repo_wurzel) is None]
