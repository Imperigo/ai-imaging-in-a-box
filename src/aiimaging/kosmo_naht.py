"""Übersetzung an der Naht — unsere Felder in die Protokollnamen des Ökosystems.

Warum es dieses Modul gibt
--------------------------
Die Ökosystem-Durchsicht vom 18.08.2026 (`docs/OEKOSYSTEM_2026-08-18.md`, Kapitel 7) hat
zwölf Stellen gefunden, an denen unsere Feldnamen und die des ArchitekturKosmos
auseinandergehen. Der Phase-0-Befund macht daraus keinen Schönheitsfehler:

    **KosmoOrbit verdrahtet Knoten über Feldnamen-Gleichheit — und meldet keinen Fehler,
    wenn die Kante nicht entsteht.**

Ein `resolution`-Knoten davor, und wir rendern still in 512 px weiter. Ein
durchgereichtes `owner_approval_token`, und der Auftrag bleibt auf `awaiting_approval` —
die Freigabe wirkt einfach nicht. Kein Schaden, kein Absturz, kein Hinweis.

Übersetzen, nicht umbenennen
-----------------------------
Unsere Bibliothek ist auf Deutsch, und das bleibt so: An den Begriffen dieses Projekts
hängen Begründungen, und eine Registry umzubenennen, weil ein Nachbarsystem andere Wörter
benutzt, verlöre sie. **Die Feldnamen an der Naht sind aber weder Deutsch noch Englisch,
sondern ein Protokoll.** Ein Protokoll übernimmt man; ein Vokabular nicht.

Darum steht die Übersetzung hier, an einer Stelle, und nicht verstreut in den Modulen.
Dasselbe Muster wie :func:`aiimaging.gate.als_kosmovis_verdikt`, nur für die
Auftragsseite.

Das Token bleibt, wo es hingehört: nirgends
--------------------------------------------
Der Vertrag `VIS-JOB-INFRA-KONTRAKT-2026-06-17` erwartet das Freigabe-Token **in der
Auftragsdatei**. Unsere `jobs.py` legt es bewusst nie ab — eine Auftragsdatei ist für
jeden lesbar, der das Verzeichnis sieht, und ein Token ist eine Befugnis. Wer es dort
hinschreibt, verteilt die Befugnis mit.

**Owner-Entscheid vom 18.08.2026: Wir bleiben bei unserer Regel.** :func:`als_kosmo_auftrag`
nimmt das Token als **Argument** entgegen und setzt es allein in den übersetzten Satz —
im Augenblick des Übergangs, aus dem Gedächtnis des Aufrufers. Auf unserer Seite entsteht
dadurch keine Datei, die es enthält.

Der Preis ist benannt: Der übersetzte Satz *ist* dann eine Datei mit einem Token darin,
sobald ihn jemand schreibt. Diese Naht macht die Weitergabe möglich und nicht
unvermeidlich — sie verschiebt die Entscheidung dorthin, wo sie hingehört, statt sie
durch eine Vorgabe vorwegzunehmen.
"""
from __future__ import annotations

import re

from aiimaging import jobs

#: Unser Auftragsfeld → Feld des Vertrags. Nur die Namen, die wirklich abweichen.
JOB_FELDER: dict[str, str] = {
    "art": "kind",
    "erstellt": "created_at",
    "geaendert": "updated_at",
    "ergebnis": "outputs",
    "fehler": "error",
}

#: Unser MCP-Eingabefeld → Feld des Ökosystems.
MCP_FELDER: dict[str, str] = {
    "aufloesung": "resolution",
    "approval_token": "owner_approval_token",
    "out_dir": "output_dir",
}

#: Deren Kennungsmuster: `vis-<unix_ts>-<6hex>`. Unsere 14-stellige Form besteht darin;
#: ihre zehnstellige besteht bei uns **nicht** — die Unverträglichkeit ist einseitig.
FREMDES_JOB_ID_MUSTER = re.compile(r"^vis-\d+-[0-9a-f]{6}$")

#: Umgebungsvariable, unter der das Ökosystem sein Auftragsverzeichnis führt.
FREMDES_JOB_VERZEICHNIS_ENV = "KOSMOVIS_RENDER_JOBS_DIR"


class NahtError(ValueError):
    """Ein Satz lässt sich nicht verlustfrei übersetzen."""


# ── Auflösung: Zahl gegen Zeichenkette ───────────────────────────────────────────────

def aufloesung_zu_resolution(aufloesung: int) -> str:
    """Unsere Kantenlänge → deren ``"BxH"``.

    Unsere `aufloesung` ist **eine ganze Zahl** (Kantenlänge, quadratisch), deren
    `resolution` eine **Zeichenkette** ``"1920x1440"``. Selbst nach dem Umbenennen wäre
    der Typ noch verschieden — das ist der Grund, warum eine Umbenennung allein nicht
    genügt hätte.
    """
    if isinstance(aufloesung, bool) or not isinstance(aufloesung, int) or aufloesung < 1:
        raise NahtError(f"aufloesung: ganze Zahl ab 1 erwartet, war {aufloesung!r}.")
    return f"{aufloesung}x{aufloesung}"


def resolution_zu_aufloesung(resolution) -> dict:
    """Deren ``"BxH"`` → unsere Kantenlänge, **mit benanntem Verlust**.

    Der Vorgabewert des Ökosystems ist ``"1920x1440"`` — **nicht quadratisch**. Unser
    Feld kennt nur eine Kantenlänge; eine der beiden Zahlen geht also verloren, und
    stillschweigend die erste zu nehmen wäre genau die Sorte Reparatur, die dieses
    Projekt nicht macht.

    Returns:
        ``{aufloesung, breite, hoehe, verlustfrei, hinweis}``. ``aufloesung`` ist die
        **kleinere** der beiden Kanten: Wer ein Bild in eine kleinere Fläche zwingt,
        verliert Rand; wer es vergrössert, erfindet Fläche. Von beidem ist das erste
        ehrlicher.
    """
    if not isinstance(resolution, str):
        raise NahtError(f"resolution: Zeichenkette 'BxH' erwartet, war {resolution!r}.")
    treffer = re.fullmatch(r"\s*(\d+)\s*[xX×]\s*(\d+)\s*", resolution)
    if not treffer:
        raise NahtError(
            f"resolution {resolution!r} ist nicht als 'BxH' lesbar. Der Vorgabewert des "
            f"Ökosystems ist '1920x1440'."
        )
    breite, hoehe = int(treffer.group(1)), int(treffer.group(2))
    if breite < 1 or hoehe < 1:
        raise NahtError(f"resolution {resolution!r}: beide Kanten müssen positiv sein.")
    verlustfrei = breite == hoehe
    return {
        "aufloesung": min(breite, hoehe),
        "breite": breite,
        "hoehe": hoehe,
        "verlustfrei": verlustfrei,
        "hinweis": None if verlustfrei else (
            f"{breite}x{hoehe} ist nicht quadratisch, unser `aufloesung` kennt aber nur "
            f"eine Kantenlänge. Genommen wird die kleinere ({min(breite, hoehe)}); die "
            f"längere Kante geht verloren. Wer das nicht will, rendert quadratisch und "
            f"beschneidet danach."
        ),
    }


#: Statuswerte, die eine erteilte Freigabe voraussetzen.
FREIGABE_VORAUSGESETZT = (jobs.STATUS_QUEUED, jobs.STATUS_RUNNING,
                          jobs.STATUS_DONE, jobs.STATUS_ERROR)


def satz_ist_freigegeben_laut_status(status) -> bool:
    """Setzt dieser Status eine erteilte Freigabe voraus?

    `awaiting_approval` und `cancelled` tun es nicht; alles andere schon — ein Auftrag
    kommt nur über die Freigabe in die Warteschlange. Die Frage ist nötig, weil Status
    und Token nach einer Übersetzung auseinanderlaufen können, ohne dass es auffällt.
    """
    return status in FREIGABE_VORAUSGESETZT


# ── Aufträge ─────────────────────────────────────────────────────────────────────────

def als_kosmo_auftrag(satz: dict, *, approval_token: str | None = None) -> dict:
    """Unseren Auftragssatz in die Felder des Vertrags übersetzen.

    Args:
        approval_token: Das Freigabe-Token, **im Augenblick des Übergangs übergeben**.
            ``None`` heisst: Der übersetzte Satz trägt keines, und der fremde Scheduler
            wird den Auftrag nicht freigeben. Das ist kein Versehen, sondern die Vorgabe —
            siehe Modul-Docstring.

            Die Prüfung ist dieselbe wie in ``jobs``: Ein Token, das nicht der Form
            entspricht, wird abgewiesen statt weitergereicht. Ein unbrauchbares Token
            durchzureichen erzeugte einen Auftrag, der später ohne erkennbaren Grund
            liegen bleibt.

    Returns:
        Ein Satz mit den Feldern des Vertrags. ``progress`` und ``phase`` führen wir
        nicht — sie stehen als ``None`` darin, damit ein Leser sie **findet und leer
        sieht**, statt sie zu vermissen. Ein fehlender Schlüssel ist keine Aussage, ein
        leerer schon.

    Raises:
        NahtError: kein Auftragssatz, oder ein unbrauchbares Token.
    """
    if not isinstance(satz, dict) or "job_id" not in satz:
        raise NahtError(
            f"Kein Auftragssatz: {type(satz).__name__}. Erwartet wird die Rückgabe von "
            f"`jobs.baue_job` oder `jobs.lies_job`."
        )
    if approval_token is not None and not jobs.ist_gueltiges_token(approval_token):
        raise NahtError(
            f"approval_token entspricht nicht der Form {jobs.TOKEN_PRAEFIX}… — es wird "
            f"nicht weitergereicht. Ein unbrauchbares Token erzeugte drüben einen "
            f"Auftrag, der ohne erkennbaren Grund liegen bleibt."
        )

    fremd: dict = {"job_id": satz.get("job_id"), "status": satz.get("status"),
                   "idle_window_only": satz.get("idle_window_only")}
    for unser, ihrer in JOB_FELDER.items():
        fremd[ihrer] = satz.get(unser)

    params = dict(satz.get("params") or {})
    if "aufloesung" in params:
        params["resolution"] = aufloesung_zu_resolution(params.pop("aufloesung"))
    fremd["params"] = params

    # Nicht geführt, aber benannt: ein leeres Feld ist eine Aussage, ein fehlendes nicht.
    fremd["progress"] = None
    fremd["phase"] = None

    # Und erst hier, aus dem Argument — nicht aus einer Datei.
    fremd["approval_token"] = approval_token
    return fremd


def aus_kosmo_auftrag(fremd: dict) -> dict:
    """Die Gegenrichtung: einen fremden Auftragssatz in unsere Felder lesen.

    Sie ist nötig, weil die Kennungen **einseitig** unverträglich sind: Deren Muster
    ``^vis-\\d+-[0-9a-f]{6}$`` nimmt unsere vierzehnstellige Kennung an; unser Muster
    ``^vis-\\d{14}-[0-9a-f]{6}$`` nimmt deren zehnstellige Unix-Zeit **nicht**. Wir lehnen
    fremde Aufträge also ab, sie nehmen unsere an.

    Diese Funktion liest den fremden Satz, ohne die Kennung zu verbiegen. Ob ein so
    gelesener Auftrag bei uns *abgelegt* werden darf, entscheidet weiterhin `jobs` — und
    wird dort scheitern, solange die Kennung nicht passt. **Das ist Absicht:** Eine
    Kennung stillschweigend umzuschreiben hiesse, zwei Systemen dieselbe Sache unter zwei
    Namen zu geben.

    Returns:
        Unsere Feldnamen, plus ``kennung_bei_uns_gueltig`` als ausdrückliche Auskunft.
    """
    if not isinstance(fremd, dict):
        raise NahtError(f"Kein Auftragssatz: {type(fremd).__name__}.")
    unser: dict = {"job_id": fremd.get("job_id"), "status": fremd.get("status"),
                   "idle_window_only": fremd.get("idle_window_only")}
    for unser_name, ihrer in JOB_FELDER.items():
        unser[unser_name] = fremd.get(ihrer)

    params = dict(fremd.get("params") or {})
    hinweise: list[str] = []
    if "resolution" in params:
        gedeutet = resolution_zu_aufloesung(params.pop("resolution"))
        params["aufloesung"] = gedeutet["aufloesung"]
        if gedeutet["hinweis"]:
            hinweise.append(gedeutet["hinweis"])
    unser["params"] = params

    # Die Tatsache der Freigabe übernehmen wir, das Token nicht.
    token = fremd.get("approval_token")
    unser["freigegeben"] = bool(token) and jobs.ist_gueltiges_token(token)
    if token and not unser["freigegeben"]:
        hinweise.append(
            "Der fremde Satz trägt ein `approval_token`, das unserer Form nicht "
            "entspricht — die Freigabe wird NICHT übernommen."
        )

    # DIE STILLE KANTE IN DER EIGENEN NAHT (Testabnahme 18.08.2026).
    #
    # Ein Auftrag mit `status="queued"` ist per Definition freigegeben — sonst stünde er
    # auf `awaiting_approval`. Kommt er ohne brauchbares Token zurück, sagen Status und
    # Freigabe einander widersprechende Dinge, und bisher **schwieg das Ergebnis dazu**.
    #
    # Das ist strukturell exakt der Fehler, gegen den dieses Modul gebaut wurde: nicht ein
    # Abbruch, sondern eine Angabe, die einfach nicht ankommt. Ihn ausgerechnet hier zu
    # haben, war die unangenehmste Art, ihn zu lernen.
    #
    # Repariert wird er NICHT durch Setzen von `freigegeben` — das erfände eine Befugnis
    # aus einem Statuswort. Repariert wird er durch **Sagen**.
    if satz_ist_freigegeben_laut_status(fremd.get("status")) and not unser["freigegeben"]:
        hinweise.append(
            f"Der Satz steht auf {fremd.get('status')!r} — das setzt eine Freigabe "
            f"voraus —, trägt aber kein brauchbares Token. `freigegeben` bleibt darum "
            f"False. Entweder wurde das Token beim Übergang nicht mitgegeben, oder es "
            f"entspricht unserer Form nicht. Der Auftrag bliebe bei uns liegen, ohne "
            f"dass jemand einen Fehler sieht."
        )

    job_id = fremd.get("job_id")
    gueltig = bool(job_id) and bool(jobs.JOB_ID_MUSTER.fullmatch(str(job_id)))
    unser["kennung_bei_uns_gueltig"] = gueltig
    if not gueltig:
        hinweise.append(
            f"Kennung {job_id!r} entspricht nicht unserem Muster "
            f"{jobs.JOB_ID_MUSTER.pattern}. Der Satz ist lesbar, aber bei uns nicht "
            f"ablegbar — und das mit Absicht: Eine Kennung stillschweigend umzuschreiben "
            f"gäbe zwei Systemen dieselbe Sache unter zwei Namen."
        )
    unser["hinweise"] = hinweise
    return unser


def pruefe_kanten(unsere_felder, fremde_felder) -> dict:
    """Welche Kanten entstünden zwischen zwei Feldmengen — und welche nicht?

    Die Nachbildung dessen, was KosmoOrbits `pipelineReadiness` täte, für zwei beliebige
    Knoten. Gedacht für den Fall, den es wirklich gibt: Jemand hängt einen fremden Knoten
    vor unseren und sieht keinen Fehler, weil es keinen gibt — es entsteht nur einfach
    keine Kante.

    Returns:
        ``{verbunden, tot_bei_uns, tot_bei_ihnen, uebersetzbar}``. ``uebersetzbar`` nennt
        die Paare, die **dieses Modul** verbinden kann — der Unterschied zwischen „passt
        nicht" und „passt nicht ohne Übersetzung" ist der ganze Zweck der Übung.
    """
    unsere, fremde = set(unsere_felder), set(fremde_felder)
    tabelle = {**JOB_FELDER, **MCP_FELDER}
    uebersetzbar = sorted(
        f"{u} → {i}" for u, i in tabelle.items() if u in unsere and i in fremde
    )
    return {
        "verbunden": sorted(unsere & fremde),
        "tot_bei_uns": sorted(u for u in unsere - fremde if tabelle.get(u) not in fremde),
        "tot_bei_ihnen": sorted(
            i for i in fremde - unsere
            if i not in {tabelle.get(u) for u in unsere}
        ),
        "uebersetzbar": uebersetzbar,
    }


__all__ = [
    "FREMDES_JOB_ID_MUSTER", "FREMDES_JOB_VERZEICHNIS_ENV", "JOB_FELDER", "MCP_FELDER",
    "NahtError",
    "FREIGABE_VORAUSGESETZT",
    "als_kosmo_auftrag", "aufloesung_zu_resolution", "aus_kosmo_auftrag",
    "satz_ist_freigegeben_laut_status",
    "pruefe_kanten", "resolution_zu_aufloesung",
]
