"""Auftragsverwaltung mit Freigabe: einstellen darf jeder, starten nur ein Token.

Warum dieses Modul existiert
----------------------------
KosmoOrbits Ausführungspfad ist **read-only und fail-closed** (siehe
``docs/EINBINDUNG_KOSMOORBIT_2026-08-14.md`` §3.3). Generieren und Bewerten gelten dort
als Lesen; Schreiben nicht. Ein GPU-Render ist aber beides: Er legt Dateien an und
belegt für Minuten die Grafikkarte. Er kann darum **kein gewöhnliches read-only-Werkzeug**
sein — und die Naht wird dreigeteilt:

===================  =======================================================  ===========
Schritt              Wirkung                                                  Im Cockpit
===================  =======================================================  ===========
``enqueue``          legt einen Auftrag ab, rührt die GPU nicht an            zulässig
``query``            liest Status und Ergebnis                                zulässig
*Ausführung*         Scheduler, nur bei Freigabe und freier GPU               nicht
===================  =======================================================  ===========

Dieses Modul ist die Ablage darunter: ``baue_job``/``schreibe_job`` sind das ``enqueue``,
``lies_job``/``liste_jobs`` sind das ``query``. Die Ausführung selbst steht nicht hier —
sie gehört in einen Scheduler, der diese Ablage liest.

Der eine Satz, an dem alles hängt
---------------------------------
**Der Status folgt allein dem Freigabe-Token.** Kein Aufrufer kann ``queued`` setzen —
weder über ``baue_job`` (dort entscheidet ausschliesslich ``ist_gueltiges_token``) noch
über ``setze_status`` (das ``queued`` ausdrücklich verweigert). Der einzige Weg nach
``queued`` führt durch ``freigeben`` mit gültigem Token.

Das ist der Freeze-Schutz: Ein Sprachmodell, das an dieser Bibliothek hängt, soll
Aufträge **einstellen** können, ohne Hardware **blockieren** zu können. Ein Modell, das
sich selbst die Freigabe erteilen könnte, wäre kein Gate, sondern eine Formalität.

Abhängigkeiten: keine. Reine stdlib — wie ``contracts.py``, aus demselben Grund: Die
Ablage muss überall lesbar sein, auch dort, wo weder GPU noch Blender existieren.
Insbesondere kein ``import bpy`` und kein ``import ifcopenshell`` (Regel 1 und 2).
"""
from __future__ import annotations

import copy
import json
import os
import re
import secrets
import tempfile
from datetime import datetime, timezone
from pathlib import Path

#: Version des Ablageformats. Wie ``contracts.SCHEMA_ID`` mitgeschrieben, damit ein
#: Scheduler eine fremde Generation von Auftragsdateien erkennt statt sie zu raten.
JOB_SCHEMA_ID = "aiimaging.render-job/v1"

STATUS_AWAITING = "awaiting_approval"
STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_ERROR = "error"
STATUS_CANCELLED = "cancelled"

#: Alle bekannten Status. Was hier nicht steht, wird nicht geschrieben — ein Tippfehler
#: im Status wäre sonst ein Auftrag, den kein Scheduler je wieder anfasst.
ALLE_STATUS: frozenset[str] = frozenset({
    STATUS_AWAITING, STATUS_QUEUED, STATUS_RUNNING,
    STATUS_DONE, STATUS_ERROR, STATUS_CANCELLED,
})

#: Endzustände: von hier führt kein Übergang mehr hinaus. Ein abgeschlossener Auftrag,
#: der wieder ``running`` werden kann, wäre ein zweiter GPU-Lauf ohne zweite Freigabe.
ENDZUSTAENDE: frozenset[str] = frozenset({STATUS_DONE, STATUS_ERROR, STATUS_CANCELLED})

#: Der erlaubte Statusgraph. Bewusst als Datenstruktur und nicht als Kette von ``if``:
#: So ist er lesbar, prüfbar und im Test aufzählbar.
UEBERGAENGE: dict[str, frozenset[str]] = {
    STATUS_AWAITING: frozenset({STATUS_QUEUED, STATUS_CANCELLED}),
    STATUS_QUEUED: frozenset({STATUS_RUNNING, STATUS_CANCELLED}),
    STATUS_RUNNING: frozenset({STATUS_DONE, STATUS_ERROR, STATUS_CANCELLED}),
    STATUS_DONE: frozenset(),
    STATUS_ERROR: frozenset(),
    STATUS_CANCELLED: frozenset(),
}

#: Präfix des Freigabe-Tokens. Ein sprechendes Präfix statt eines beliebigen Geheimnisses,
#: damit in Protokollen und Fehlermeldungen sichtbar bleibt, **wozu** freigegeben wurde.
TOKEN_PRAEFIX = "CONFIRMED_RENDER_"

#: Form einer Auftragskennung: ``vis-<JJJJMMTTHHMMSS>-<6 hex>``.
JOB_ID_MUSTER = re.compile(r"^vis-\d{14}-[0-9a-f]{6}$")

#: Zeichen, die eine Kennung als Dateiname tragen darf. Eine Positivliste, kein Verbot
#: einzelner böser Zeichen: Verbotslisten übersieht man, Positivlisten nicht.
JOB_ID_ERLAUBT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

#: Endung der Auftragsdateien. Temporäre Dateien tragen sie bewusst **nicht** (siehe
#: ``schreibe_job``), damit ``liste_jobs`` einen halb geschriebenen Auftrag nie sieht.
DATEI_ENDUNG = ".json"


class JobError(ValueError):
    """Eingabe oder Ablage verletzt die Auftragsregeln. Laut statt stillschweigend."""


class UebergangError(JobError):
    """Ein Statuswechsel ist nicht erlaubt. Eigene Klasse, weil er anders zu behandeln ist:

    Ein verbotener Übergang ist selten ein Programmierfehler und meistens ein Rennen —
    zwei Scheduler greifen nach demselben Auftrag, oder ein Nutzer bricht ab, während
    der Lauf endet. So etwas fängt man gezielt ab; einen fehlenden Pflichtwert nicht.
    """


def _jetzt() -> str:
    """Aktuelle Zeit als ISO-8601 in UTC, sekundengenau.

    UTC und nicht Ortszeit: Auftragsdateien wandern zwischen Cockpit, Scheduler und
    Rechenknoten. Eine Ortszeit ohne Zone wäre beim Vergleich zweier Aufträge schlicht
    falsch — und zweimal im Jahr auch rückwärts laufend.
    """
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def neue_job_id(zeitstempel: str | None = None, zufall: str | None = None) -> str:
    """Neue Auftragskennung der Form ``vis-<JJJJMMTTHHMMSS>-<6 hex>``.

    Der Zeitstempel macht die Kennung im Dateisystem grob sortierbar, der Zufallsteil
    macht sie eindeutig: Zwei Aufträge in derselben Sekunde sind bei einem Cockpit mit
    Stapelverarbeitung der Normalfall, nicht die Ausnahme.

    Beide Teile sind injizierbar, damit die Funktion prüfbar ist. Ein Test, der eine
    zufällige Kennung nur auf ihr Muster prüfen kann, prüft die Hälfte.

    Args:
        zeitstempel: 14 Ziffern ``JJJJMMTTHHMMSS``; ``None`` → jetzt (UTC).
        zufall: 6 Zeichen aus ``0-9a-f``; ``None`` → kryptografischer Zufall.

    Raises:
        JobError: injizierte Teile passen nicht zur Form — lieber hier auffallen als
            später in einer Kennung, die kein Scheduler wiedererkennt.
    """
    if zeitstempel is None:
        zeitstempel = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    if zufall is None:
        # 3 Byte → 6 Hexzeichen. `secrets` und nicht `random`: Die Kennung landet in
        # Dateinamen, die ein zweiter Prozess anlegt — vorhersagbare Namen laden dazu
        # ein, sie vorwegzunehmen.
        zufall = secrets.token_hex(3)

    if not re.fullmatch(r"\d{14}", str(zeitstempel)):
        raise JobError(f"zeitstempel muss 14 Ziffern JJJJMMTTHHMMSS sein, war {zeitstempel!r}")
    if not re.fullmatch(r"[0-9a-f]{6}", str(zufall)):
        raise JobError(f"zufall muss 6 Hexzeichen (0-9a-f) sein, war {zufall!r}")

    return f"vis-{zeitstempel}-{zufall}"


def ist_gueltiges_token(token) -> bool:
    """Ist ``token`` eine gültige Freigabe?

    Gültig ist genau ``CONFIRMED_RENDER_<etwas>`` mit nicht-leerem ``<etwas>``. Das
    blosse Präfix zählt **nicht**: Es ist der Wert, der beim Abtippen, beim Kürzen einer
    Log-Zeile oder beim Zusammenbauen aus einer leeren Variablen (``PRAEFIX + kennung``
    mit leerer ``kennung``) entsteht. Genau solche Beinahe-Token dürfen keine GPU starten.

    Die Prüfung ist bewusst gross-/kleinschreibungsempfindlich und ohne jede Toleranz —
    hier gilt nicht die Nachsicht von ``contracts.normalize_up_axis``. Dort war Toleranz
    richtig, weil zwei Erzeuger dasselbe meinten; hier wäre sie eine Aufweichung des
    einzigen Gates, das die Hardware schützt (fail-closed).

    Alles, was kein ``str`` ist — ``None``, Zahlen, Objekte mit hübschem ``__str__`` —
    ist ungültig, statt vorher durch ``str()`` gedreht zu werden.
    """
    if not isinstance(token, str):
        return False
    if not token.startswith(TOKEN_PRAEFIX):
        return False
    return bool(token[len(TOKEN_PRAEFIX):].strip())


def _pruefe_job_id(job_id) -> str:
    """Kennung als Dateiname absichern.

    Eine ``job_id`` wird zu einem Pfad. Käme sie aus einem Sprachmodell oder über MCP
    herein, wäre ``../../etwas`` ein Schreibzugriff ausserhalb der Auftragsablage und
    ``a/b`` ein Auftrag in einem Unterverzeichnis, den ``liste_jobs`` nie sieht. Beides
    wird hier abgewiesen, nicht bereinigt: Eine stillschweigend umgeschriebene Kennung
    passte nicht mehr zu der, die der Aufrufer in der Hand hält.

    Raises:
        JobError: leer, kein ``str``, oder als Dateiname untauglich.
    """
    if not isinstance(job_id, str):
        raise JobError(f"job_id muss ein str sein, war {type(job_id).__name__}")
    if not job_id:
        raise JobError("job_id ist leer.")
    if not JOB_ID_ERLAUBT.fullmatch(job_id):
        raise JobError(
            f"job_id {job_id!r} ist als Dateiname untauglich. Erlaubt sind Buchstaben, "
            f"Ziffern, '.', '_' und '-'; das erste Zeichen muss Buchstabe oder Ziffer "
            f"sein. Damit sind Pfadtrenner, '..' und versteckte Dateien ausgeschlossen."
        )
    # Gürtel und Hosenträger: Selbst wenn die Positivliste je erweitert wird, muss die
    # Kennung ihr eigener Basisname bleiben — sonst zeigt sie aus dem Verzeichnis hinaus.
    if job_id != os.path.basename(job_id) or job_id in (os.curdir, os.pardir):
        raise JobError(f"job_id {job_id!r} zeigt aus dem Auftragsverzeichnis hinaus.")
    return job_id


def _pruefe_status(status) -> str:
    """Status gegen ``ALLE_STATUS`` prüfen."""
    if status not in ALLE_STATUS:
        raise JobError(f"unbekannter Status {status!r}; bekannt: {sorted(ALLE_STATUS)}")
    return status


def _pfad(job_id: str, verzeichnis) -> Path:
    """Dateipfad eines Auftrags — erst nach ``_pruefe_job_id``."""
    return Path(verzeichnis) / f"{_pruefe_job_id(job_id)}{DATEI_ENDUNG}"


#: Schlüsselnamen, unter denen ein Freigabe-Token in `params` geraten könnte — unserer
#: und der des Ökosystems (`docs/OEKOSYSTEM_2026-08-18.md`, Kap. 7.2).
TOKEN_SCHLUESSEL = ("approval_token", "owner_approval_token", "token")


def _wehre_token_in_params_ab(params) -> None:
    """Regel „das Token landet nie auf der Platte" — auch auf dem Umweg über ``params``.

    **Die Lücke, die eine Testabnahme fand (18.08.2026):** `baue_job` kopiert `params`
    unbesehen und `schreibe_job` schreibt sie. Wer das Token als *Parameter* durchreicht,
    schrieb es damit in die Auftragsdatei — und `freigegeben` blieb trotzdem `False`. Das
    Schlimmste beider Welten: Die Befugnis liegt offen, und wirken tut sie nicht.

    Das ist keine erfundene Gefahr. Der MCP-Vertrag des Ökosystems führt
    `owner_approval_token` als **Eingabefeld**, und Eingabefelder landen bei uns in
    `params`. Der Weg dorthin ist also der normale, nicht der ausgefallene.

    Geprüft wird auf **beides**: den Schlüsselnamen (jemand nennt das Feld so) und den
    Wert (jemand nennt es anders und schreibt trotzdem ein Token hinein). Nur eines von
    beidem zu prüfen liesse die jeweils andere Hälfte offen.

    Raises:
        JobError: mit dem Fundort, damit der Aufrufer nicht suchen muss.
    """
    def _pruefe(wert, pfad: str) -> None:
        if isinstance(wert, dict):
            for schluessel, unterwert in wert.items():
                if str(schluessel).lower() in TOKEN_SCHLUESSEL:
                    raise JobError(
                        f"params{pfad}[{schluessel!r}]: Ein Freigabe-Token gehört nicht "
                        f"in die Parameter. Es würde mit der Auftragsdatei auf die Platte "
                        f"geschrieben — und wirken würde es trotzdem nicht, denn die "
                        f"Freigabe läuft über `approval_token=` bzw. `freigeben()`. "
                        f"Das Token ist eine Befugnis; eine Auftragsdatei ist für jeden "
                        f"lesbar, der das Verzeichnis sieht."
                    )
                _pruefe(unterwert, f"{pfad}[{schluessel!r}]")
        elif isinstance(wert, (list, tuple)):
            for i, unterwert in enumerate(wert):
                _pruefe(unterwert, f"{pfad}[{i}]")
        elif isinstance(wert, str) and wert.startswith(TOKEN_PRAEFIX):
            raise JobError(
                f"params{pfad}: Der Wert beginnt mit {TOKEN_PRAEFIX!r} — das sieht nach "
                f"einem Freigabe-Token aus, und es gehört nicht in die Parameter. "
                f"Geprüft wird der Wert und nicht nur der Schlüsselname: Ein Token unter "
                f"einem harmlosen Namen wäre sonst durchgekommen."
            )

    _pruefe(params, "")


def baue_job(*, job_id: str, art: str, params: dict,
             approval_token: str | None = None,
             idle_window_only: bool = True) -> dict:
    """Auftragssatz bauen — ohne die GPU anzurühren.

    **Der Status folgt allein dem Token.** Ein gültiges ``approval_token`` ergibt
    ``queued``, alles andere ``awaiting_approval``. Es gibt keinen Parameter, mit dem ein
    Aufrufer den Status selbst setzen könnte, und ein ungültiges Token ist kein Fehler,
    sondern schlicht keine Freigabe — fail-closed. Ein ``JobError`` an dieser Stelle
    würde nur dazu verleiten, ihn abzufangen und den Auftrag doch einzustellen.

    ``idle_window_only`` wird nur **mitgeführt**, nicht ausgewertet: Der Scheduler, der
    entscheidet, ob gerade Leerlauffenster ist, kommt später. Das Feld jetzt schon zu
    schreiben, kostet nichts und erspart später eine Wanderung durch alte Auftragsdateien.

    Args:
        job_id: Kennung, üblicherweise aus ``neue_job_id``.
        art: was zu tun ist, z. B. ``"depth"`` oder ``"render"``. Freitext — welche
            Arten es gibt, entscheidet der Scheduler, nicht die Ablage.
        params: Parameter des Auftrags, etwa eine render-scene nach ``contracts``. Wird
            kopiert; spätere Änderungen am übergebenen Objekt erreichen den Auftrag nicht.
        approval_token: Freigabe, falls sie schon vorliegt.
        idle_window_only: Vermerk für den Scheduler.

    Returns:
        Der Auftragssatz als ``dict`` — noch nicht geschrieben.

    Raises:
        JobError: unbrauchbare Kennung, leere ``art`` oder ``params`` kein ``dict``.
    """
    _pruefe_job_id(job_id)
    if not isinstance(art, str) or not art.strip():
        raise JobError("art fehlt oder ist leer.")
    if not isinstance(params, dict):
        raise JobError(f"params muss ein dict sein, war {type(params).__name__}")

    _wehre_token_in_params_ab(params)
    freigegeben = ist_gueltiges_token(approval_token)
    status = STATUS_QUEUED if freigegeben else STATUS_AWAITING
    jetzt = _jetzt()

    return {
        "schema": JOB_SCHEMA_ID,
        "job_id": job_id,
        "art": art,
        # `deepcopy` aus demselben Grund wie in `contracts.validate_render_scene`: Der
        # Aufrufer soll seinen params-Dict weiterverwenden dürfen, ohne den bereits
        # eingestellten Auftrag nachträglich zu verändern.
        "params": copy.deepcopy(params),
        "status": status,
        "idle_window_only": bool(idle_window_only),
        # Nur die Tatsache der Freigabe wird abgelegt, nie das Token selbst. Das Token
        # ist eine Befugnis; eine Auftragsdatei ist für jeden lesbar, der das Verzeichnis
        # sieht. Wer das Token dort ablegt, verteilt die Befugnis mit.
        "freigegeben": freigegeben,
        "freigegeben_am": jetzt if freigegeben else None,
        "erstellt": jetzt,
        "geaendert": jetzt,
        "ergebnis": None,
        "fehler": None,
        # Nur `geaendert` mitzuführen hiesse, bei jedem Wechsel die Vorgeschichte zu
        # überschreiben. Der Verlauf beantwortet die Frage, die man später wirklich
        # stellt: wie lange lag der Auftrag, und wie lange lief er.
        "verlauf": [{"status": status, "zeit": jetzt}],
    }


def schreibe_job(record: dict, verzeichnis) -> Path:
    """Auftrag **atomar** ablegen und den Pfad zurückgeben.

    Geschrieben wird in eine temporäre Datei im *selben* Verzeichnis, dann ``os.replace``.
    Zwei Gründe, beide praktisch:

    * ``os.replace`` ist innerhalb eines Dateisystems atomar. Ein Scheduler, der
      gleichzeitig liest, sieht entweder den alten oder den neuen Auftrag, nie einen
      halben. Direkt in die Zieldatei zu schreiben hiesse, sie zwischenzeitlich zu leeren.
    * Bricht der Schreibvorgang ab — Platte voll, Prozess getötet, nicht serialisierbarer
      Wert in ``params`` — wird die temporäre Datei entfernt. Es bleibt kein Rest liegen,
      den später jemand für einen gültigen Auftrag hält.

    Die temporäre Datei liegt im Zielverzeichnis (nicht in ``/tmp``), weil ``os.replace``
    über Dateisystemgrenzen hinweg nicht atomar ist. Sie beginnt mit einem Punkt und
    endet nicht auf ``.json``, damit ``liste_jobs`` sie in keinem Fall aufsammelt.

    Raises:
        JobError: Kennung untauglich, Status unbekannt, oder der Satz ist nicht als
            JSON darstellbar.
    """
    if not isinstance(record, dict):
        raise JobError(f"record muss ein dict sein, war {type(record).__name__}")
    job_id = _pruefe_job_id(record.get("job_id"))
    _pruefe_status(record.get("status"))

    verzeichnis = Path(verzeichnis)
    verzeichnis.mkdir(parents=True, exist_ok=True)
    ziel = verzeichnis / f"{job_id}{DATEI_ENDUNG}"

    fd, temporaer = tempfile.mkstemp(dir=verzeichnis, prefix=f".{job_id}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as datei:
            json.dump(record, datei, ensure_ascii=False, indent=2, sort_keys=True)
            datei.write("\n")
            datei.flush()
            # Ohne fsync liegt der Inhalt womöglich nur im Puffer des Betriebssystems,
            # während `os.replace` den Namen schon umgehängt hat. Nach einem Stromausfall
            # stünde dann ein leerer Auftrag da — genau der halbe Zustand, den dieser
            # Umweg verhindern soll.
            os.fsync(datei.fileno())
        os.replace(temporaer, ziel)
    except BaseException as fehler:
        # Auch bei KeyboardInterrupt aufräumen: Ein Nutzer, der Strg-C drückt, soll
        # keinen Dateirest hinterlassen. Der Fehler selbst wird weitergereicht.
        Path(temporaer).unlink(missing_ok=True)
        if isinstance(fehler, (TypeError, ValueError)) and not isinstance(fehler, JobError):
            raise JobError(
                f"Auftrag {job_id} ist nicht als JSON darstellbar: {fehler}. Die Ablage "
                f"muss von fremden Prozessen lesbar bleiben — params gehören als "
                f"einfache Werte hinein, nicht als Python-Objekte."
            ) from fehler
        raise
    return ziel


def lies_job(job_id: str, verzeichnis) -> dict:
    """Einen Auftrag lesen.

    Raises:
        JobError: Kennung untauglich, Auftrag nicht vorhanden oder Datei unlesbar. Ein
            unlesbarer Auftrag wird gemeldet und nicht als leerer Satz zurückgegeben —
            ein Scheduler soll darüber stolpern, nicht darüber hinweggehen.
    """
    pfad = _pfad(job_id, verzeichnis)
    try:
        text = pfad.read_text(encoding="utf-8")
    except FileNotFoundError as fehler:
        raise JobError(f"Auftrag {job_id} nicht gefunden in {Path(verzeichnis)}") from fehler
    try:
        satz = json.loads(text)
    except json.JSONDecodeError as fehler:
        raise JobError(f"Auftrag {job_id} ist kein lesbares JSON: {fehler}") from fehler
    if not isinstance(satz, dict):
        raise JobError(f"Auftrag {job_id} ist kein Objekt, sondern {type(satz).__name__}")
    return satz


def liste_jobs(verzeichnis, status: str | None = None) -> list[dict]:
    """Alle Aufträge, optional auf einen Status gefiltert.

    Sortiert nach Erstellzeit, bei Gleichstand nach Kennung — die Reihenfolge, in der ein
    Scheduler sie abarbeiten will, und stabil genug, um sie in Tests festzunageln.

    Ein nicht vorhandenes Verzeichnis ergibt eine leere Liste, keinen Fehler: Vor dem
    ersten ``schreibe_job`` gibt es die Ablage noch nicht, und ein Scheduler, der im
    Leerlauf nachschaut, soll deswegen nicht abstürzen. Ein *unlesbarer* Auftrag ist
    etwas anderes und fliegt weiterhin (über ``lies_job``).

    Raises:
        JobError: unbekannter Statusfilter — ein Tippfehler dort gäbe sonst still eine
            leere Liste zurück, und die sieht aus wie „nichts zu tun".
    """
    if status is not None:
        _pruefe_status(status)

    verzeichnis = Path(verzeichnis)
    if not verzeichnis.is_dir():
        return []

    gefunden: list[dict] = []
    for pfad in sorted(verzeichnis.glob(f"*{DATEI_ENDUNG}")):
        if pfad.name.startswith("."):
            continue          # temporäre Reste und versteckte Dateien sind keine Aufträge
        satz = lies_job(pfad.name[: -len(DATEI_ENDUNG)], verzeichnis)
        if status is None or satz.get("status") == status:
            gefunden.append(satz)
    return sorted(gefunden, key=lambda s: (str(s.get("erstellt") or ""), str(s.get("job_id") or "")))


def _wechsle(satz: dict, neuer_status: str, *, ergebnis=None, fehler=None) -> dict:
    """Statuswechsel im Speicher vollziehen, nachdem er als erlaubt erkannt wurde."""
    jetzt = _jetzt()
    satz["status"] = neuer_status
    satz["geaendert"] = jetzt
    if ergebnis is not None:
        satz["ergebnis"] = ergebnis
    if fehler is not None:
        satz["fehler"] = fehler
    satz.setdefault("verlauf", []).append({"status": neuer_status, "zeit": jetzt})
    return satz


def _pruefe_uebergang(alt, neu: str) -> None:
    """Übergang gegen ``UEBERGAENGE`` prüfen.

    Raises:
        UebergangError: nicht erlaubt — mit Angabe dessen, was von hier aus ginge.
    """
    if alt not in UEBERGAENGE:
        raise JobError(f"Auftrag trägt unbekannten Status {alt!r} — Ablage beschädigt?")
    if neu in UEBERGAENGE[alt]:
        return
    if alt in ENDZUSTAENDE:
        raise UebergangError(
            f"{alt} ist ein Endzustand; {alt} → {neu} gibt es nicht. Ein abgeschlossener "
            f"Auftrag wird nicht wiederbelebt, sondern neu eingestellt — sonst liefe ein "
            f"zweiter GPU-Lauf auf einer alten Freigabe."
        )
    raise UebergangError(
        f"{alt} → {neu} ist nicht erlaubt. Von {alt} aus: {sorted(UEBERGAENGE[alt]) or 'nichts'}."
    )


def setze_status(job_id: str, neuer_status: str, verzeichnis, *,
                 ergebnis: dict | None = None, fehler: str | None = None) -> dict:
    """Status eines abgelegten Auftrags wechseln und den neuen Satz zurückgeben.

    Nach ``queued`` führt dieser Weg **nicht**. Das ist keine Auslassung, sondern der
    Kern des Gates: Wäre ``setze_status(job_id, "queued", …)`` erlaubt, könnte sich jeder
    Aufrufer — auch ein Sprachmodell mit Dateizugriff — die Freigabe selbst erteilen und
    damit minutenlang die Grafikkarte belegen. Der einzige Weg dorthin ist ``freigeben``
    mit gültigem Token.

    Args:
        ergebnis: Ausgabe des Laufs, üblicherweise beim Wechsel nach ``done``.
        fehler: Fehlertext, üblicherweise beim Wechsel nach ``error``. Beide werden nur
            gesetzt, wenn übergeben — ein späterer Wechsel löscht das Ergebnis nicht.

    Raises:
        JobError: Kennung oder Status untauglich, Auftrag nicht vorhanden.
        UebergangError: Übergang nicht erlaubt (auch bei ``queued``).
    """
    _pruefe_status(neuer_status)
    if neuer_status == STATUS_QUEUED:
        raise UebergangError(
            "queued kann nicht gesetzt werden — nur freigeben() mit gültigem "
            f"{TOKEN_PRAEFIX}…-Token führt dorthin. Genau das ist das Gate zwischen "
            "„Auftrag einstellen\" und „GPU belegen\"."
        )

    satz = lies_job(job_id, verzeichnis)
    _pruefe_uebergang(satz.get("status"), neuer_status)
    _wechsle(satz, neuer_status, ergebnis=ergebnis, fehler=fehler)
    schreibe_job(satz, verzeichnis)
    return satz


def freigeben(job_id: str, token: str, verzeichnis) -> dict:
    """``awaiting_approval`` → ``queued``, ausschliesslich mit gültigem Token.

    Die einzige Tür zum Ausführungspfad. Sie prüft in dieser Reihenfolge:

    1. Token gültig? Sonst ``JobError`` — und die Datei auf der Platte bleibt unberührt.
       Die Prüfung steht vor dem Lesen, damit ein ungültiges Token nicht einmal verrät,
       ob es den Auftrag überhaupt gibt.
    2. Auftrag in ``awaiting_approval``? Sonst ``UebergangError``. Ein bereits
       freigegebener Auftrag wird **nicht** stillschweigend noch einmal freigegeben:
       Eine zweite Freigabe auf einem laufenden Auftrag wäre ein Hinweis darauf, dass
       zwei Stellen dasselbe Gate bedienen — das gehört gemeldet.

    Raises:
        JobError: Token ungültig oder Auftrag nicht vorhanden.
        UebergangError: Auftrag ist nicht (mehr) in ``awaiting_approval``.
    """
    if not ist_gueltiges_token(token):
        raise JobError(
            f"Freigabe abgelehnt: Token muss {TOKEN_PRAEFIX}<etwas> lauten, mit "
            f"nicht-leerem Rest. Ohne gültige Freigabe wird keine GPU belegt."
        )

    satz = lies_job(job_id, verzeichnis)
    _pruefe_uebergang(satz.get("status"), STATUS_QUEUED)

    _wechsle(satz, STATUS_QUEUED)
    satz["freigegeben"] = True
    satz["freigegeben_am"] = satz["geaendert"]
    schreibe_job(satz, verzeichnis)
    return satz


__all__ = [
    "TOKEN_SCHLUESSEL",
    "ALLE_STATUS", "ENDZUSTAENDE", "JOB_ID_MUSTER", "JOB_SCHEMA_ID", "TOKEN_PRAEFIX",
    "UEBERGAENGE",
    "STATUS_AWAITING", "STATUS_CANCELLED", "STATUS_DONE", "STATUS_ERROR",
    "STATUS_QUEUED", "STATUS_RUNNING",
    "JobError", "UebergangError",
    "baue_job", "freigeben", "ist_gueltiges_token", "lies_job", "liste_jobs",
    "neue_job_id", "schreibe_job", "setze_status",
]
