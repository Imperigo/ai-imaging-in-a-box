"""Der **Assistent** — er schlägt vor, und er rechnet nie (Plan v0.1.7, Strom D).

Was er ist
----------
Ein Gespräch mit einem Sprachmodell am Heim-PC (Ollama, :data:`VORGABE_MODELL`), das drei
**Werkzeuge** kennt: Standpunkt, Bildauftrag, Varianten. Jedes Werkzeug erzeugt **nur
einen Vorschlag** — einen Satz Einstellungen, die die Nutzerin auf einer Karte sieht.
Gerechnet wird erst, wenn sie «Anwenden» drückt (Entscheide 37, 41, 48, 57; Blatt 14).

Die drei Dinge, die dieses Modul **nicht** tut, und warum sie hier stehen
---------------------------------------------------------------------------
* **Es rechnet nie in** :func:`frage`. ``frage`` kennt keinen Weg zum Rechnen: Es nimmt
  keinen Starter entgegen und ruft weder :mod:`aiimaging.arbeitsgang` noch die Kette
  auf. Das einzige, was ein Bild auslöst, ist :func:`anwenden` — und das ruft der
  Mensch, nicht das Sprachmodell. *Ein Assistent, der «nur kurz» selbst rechnet, hat das
  Urteil darüber, was gerechnet wird, an ein Modell abgegeben, das sich nicht
  verantworten kann.* Bewacht in ``tests/test_assistent.py`` (Mutationsprobe).
* **Es zeigt nie, was das Modell «denkt».** Gemessen am Heim-PC (``auf-20261001-213``):
  Bei ``qwen3:30b`` schaltet ``think: false`` das Denken **nicht** ab — englischer
  Gedankentext landet dann in ``content``. Mit ``think: true`` liegt er sauber im Feld
  ``thinking``. Gelesen wird darum mit ``think: true``, gezeigt wird nur ``content``, und
  was dort trotzdem in ``<think>`` steht, wird entfernt.
* **Es rechnet nicht neben dem Bildmodell.** Sprachmodell (25,1 GB laut Ollama
  ``/api/ps``, gemessen ``auf-20261001-218``; die frühere Angabe 18,7 GB war die Grösse
  der Datei, nicht der Belegung) und Bildmodell (25,5 GB) passen nicht zugleich auf die
  32-GB-Karte. :func:`anwenden` **entlädt** das Sprachmodell (``keep_alive: 0``,
  gemessen 0,16 s), **bevor** es den Lauf startet; und während ein Bild rechnet oder das
  Bildmodell noch auf der Karte liegt, antwortet :func:`frage` nicht (``bild_rechnet``,
  ``bildmodell_geladen``).

Was er nicht darf, steht auch auf der Karte (Blatt 14): das Urteil am Bild ändern, eine
Prüfung überspringen, etwas ohne «Anwenden» rechnen. Keines der drei Werkzeuge hat ein
Feld dafür — ``qa`` und die Schwellen sind keine Werkzeugfelder.

Regel 1 für Sprachmodelle
-------------------------
Geladen wird nur ein Modell aus :data:`ERLAUBTE_MODELLE` — jedes mit Lizenz und Beleg.
Llama, Gemma und Qwen2.5-3B/72B sind ausgeschlossen (``docs/VORFUEHRFASSUNG_2026-10-01.md``).
**Ollama** (MIT) ist ein externes Programm am Heim-PC und wird nicht mitgeliefert; dieses
Modul spricht mit ihm über HTTP, nur mit der Standardbibliothek (``urllib``).

Regel 4
-------
Alles hier ist ohne Oberfläche aufrufbar::

    from aiimaging import assistent
    r = assistent.frage("Zeig das Haus von Süd-Ost, Abendlicht, drei Varianten.")
    r["vorschlag"]["saetze"]
    assistent.anwenden(r["vorschlag"], starte=lambda e, v: ...)

Der Server der Oberfläche reicht nur durch; er steht ausserhalb des Kerns.
"""
from __future__ import annotations

import http.client
import inspect
import json
import math
import os
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from aiimaging import arbeitsgang, kameras, kette, sprache

__all__ = [
    "AssistentError", "NichtErreichbar", "AntwortAbgebrochen", "ZeitUeberschritten",
    "Ollama",
    "ERLAUBTE_MODELLE", "AUSGESCHLOSSENE_MODELLE", "VORGABE_ADRESSE", "VORGABE_MODELL",
    "UMGEBUNG_ADRESSE", "UMGEBUNG_MODELL", "STANDPUNKT_FELDER", "WERKZEUGE",
    "STAND_BEREIT", "STAND_LAEDT", "STAND_FEHLT", "STAND_AUS", "STAENDE",
    "RECHENZEIT_JE_VARIANTE_S", "FRIST_FRAGE_GESAMT_S",
    "SATZ_BILD_RECHNET", "SATZ_BILDMODELL_GELADEN", "SATZ_FRIST_ABGELAUFEN",
    "anwenden", "frage", "frage_mit_werkzeugen", "pruefe_werkzeugliste", "SYSTEMTEXT_KNOTEN",
    "SATZ_NUR_ARCHITEKT", "KENNUNG_FELDER", "ERFUNDEN_FELDER",
    "SCHRITTE_HOECHSTENS", "ERGEBNIS_HOECHSTENS", "WERKZEUGE_HOECHSTENS", "kontext_der_mappe", "pruefe_adresse", "pruefe_sprachmodell",
    "pruefe_vorschlag",
    "stand",
    "EIGENES_MODELL", "KOSMO_ROLLENKARTE", "GESCHUETZTE_ANFAENGE", "geschuetzt",
    "DATEI_FRAGE_LAEUFT", "frage_vermerkt", "frage_laeuft_in", "entlade_wenn_nur_eigenes",
    "gib_karte_frei", "FRIST_KARTE_FREI_S", "FRIST_KARTE_LEER_S", "TAKT_KARTE_LEER_S",
]


class AssistentError(ValueError):
    """Ein Satz für den Menschen — warum der Assistent hier nicht weiterkommt."""


class NichtErreichbar(AssistentError):
    """Ollama antwortet nicht (aus, falsche Adresse, kein Netz)."""


class AntwortAbgebrochen(NichtErreichbar):
    """Ollama begann zu antworten und brach ab (``IncompleteRead``, ``BadStatusLine``).

    Für die Frage ist das «nicht erreichbar» (503, derselbe Weg). **Beim Entladen nicht:**
    Dort heisst «nicht erreichbar» «es hält nichts auf der Karte» — wer aber halb
    antwortet, läuft, und ob er entladen hat, ist nicht bekannt. Darum eine eigene Klasse,
    an der :meth:`Ollama.entlade` sie unterscheidet.
    """


class ZeitUeberschritten(AssistentError):
    """Ollama antwortete nicht innerhalb der Frist — es läuft, aber zu langsam."""


class _Abweisung(Exception):
    """Ein Werkzeugaufruf, der kein Vorschlag wird — mit dem Satz, warum."""


# ============================================================ der Anschluss an Ollama

#: Ollama am Heim-PC, auf der eigenen Maschine. **Nicht** über die Weiterleitung von
#: KosmoOrbit (``/llm``) — die gehört drüben (Plan v0.1.7, Strom D).
VORGABE_ADRESSE = "http://127.0.0.1:11434"

#: Umgebungsvariable für eine andere Adresse (z. B. ein anderer Anschluss).
UMGEBUNG_ADRESSE = "AIIMAGING_OLLAMA"

#: Umgebungsvariable für ein anderes Modell — nur eines aus :data:`ERLAUBTE_MODELLE`.
UMGEBUNG_MODELL = "AIIMAGING_SPRACHMODELL"

#: **Das eigene Modell der Visbox** (Owner-Entscheid 106d, 20.10.2026): ``qwen3:14b``,
#: Apache-2.0, schon in :data:`ERLAUBTE_MODELLE`. Bis dahin stand hier ``qwen3:30b`` — am
#: Heim-PC gemessen (``auf-20261001-213``), aber das ist Kosmos «Leiter»-Modell, und Visbox
#: entlud es beim Anwenden. Seither hat Visbox ein eigenes, und nur dieses entlädt sie.
VORGABE_MODELL = "qwen3:14b"

#: Das Modell, das Visbox entladen darf — ihr eigenes (Entscheid 106d). Ein anderes,
#: auch per :data:`UMGEBUNG_MODELL` eingestelltes, wird nie entladen.
EIGENES_MODELL = VORGABE_MODELL

#: **Kosmos Rollenkarte** — die Modelle, die KosmoOrbit am Heim-PC hält. Der Assistent der
#: Visbox entlädt sie nie (Entscheid 106d). **Ausnahme seit Entscheid 127 (22.10.2026):** Vor
#: einem Bildauftrag gibt :func:`gib_karte_frei` jedes geladene Modell frei, auch diese. *Herkunft:* KosmoOrbit ``packages/kosmo-ai/src/staffelung.ts``,
#: abgeschrieben am 20.10.2026 — ändert sich die Karte drüben, gehört sie hier nachgetragen.
KOSMO_ROLLENKARTE = {
    "meister": "kosmo-qwen3.6:35b-a3b",
    "leiter": "qwen3:30b",
    "zeichner": "qwen3-coder:30b",
    "seher": "qwen2.5vl:7b",
}

#: Namensanfänge, die nie entladen werden: Kosmos eigene Modelle und ``gpt-oss``.
GESCHUETZTE_ANFAENGE = ("kosmo-", "gpt-oss")


def geschuetzt(modell) -> str | None:
    """Warum Visbox dieses Modell **nicht** entladen darf — oder ``None``, wenn sie darf.

    Sie darf genau ihr eigenes (:data:`EIGENES_MODELL`). Kosmos Modelle, ``gpt-oss`` und
    jedes andere bleiben auf der Karte, wie es auch eingestellt ist (Entscheid 106d).

    Das gilt für den **Assistenten** (``Ollama.entlade``, :func:`entlade_wenn_nur_eigenes`).
    Vor einem **Bildauftrag** gilt Entscheid 127: :func:`gib_karte_frei` gibt alles frei.
    """
    name = str(modell or "").strip().lower()
    basis = name[:-len(":latest")] if name.endswith(":latest") else name
    for rolle, kosmo in KOSMO_ROLLENKARTE.items():
        if basis == kosmo:
            return (f"{name} ist ein Modell von KosmoOrbit (Rolle «{rolle}») — Visbox "
                    f"entlädt es nie.")
    for anfang in GESCHUETZTE_ANFAENGE:
        if basis.startswith(anfang):
            return f"{name} gehört nicht Visbox ({anfang}…) — Visbox entlädt es nie."
    if basis != EIGENES_MODELL:
        return (f"{name} ist nicht das eigene Modell der Visbox ({EIGENES_MODELL}) — "
                f"entladen wird nur dieses.")
    return None

_BELEG = ("Lizenzdatei und Modellkarte gelesen am 01.10.2026; "
          "docs/VORFUEHRFASSUNG_2026-10-01.md, «Das Sprachmodell — geprüft nach Regel 1»")

#: Die Modelle, die geladen werden dürfen — **je mit Lizenz und Beleg** (Regel 1). Ein
#: Modell, das hier nicht steht, wird abgewiesen, auch wenn es am Heim-PC liegt.
ERLAUBTE_MODELLE = {
    "qwen3:30b": {"lizenz": "Apache-2.0", "gewichte": "Qwen/Qwen3-30B-A3B",
                  "beleg": _BELEG},
    "qwen3:14b": {"lizenz": "Apache-2.0", "gewichte": "Qwen/Qwen3-14B", "beleg": _BELEG},
    "gpt-oss:20b": {"lizenz": "Apache-2.0", "gewichte": "openai/gpt-oss-20b",
                    "beleg": _BELEG},
}

#: Ausgeschlossen, mit dem Grund — damit die Abweisung den Grund nennt und nicht nur «nein».
#: Verglichen wird der Anfang des Namens (``llama3.1:8b`` ist ein Llama).
AUSGESCHLOSSENE_MODELLE = (
    ("llama", "Llama Community License"),
    ("gemma", "Gemma Terms of Use"),
    ("qwen2.5", "Qwen-Lizenzen (Qwen2.5-3B, Qwen2.5-72B)"),
)

#: Fristen in Sekunden — **gesetzt, nicht gemessen**. Der Stand muss schnell sein (er
#: steht in der Startzeile); eine Antwort mit Denken darf dauern (kalt gemessen: erste
#: Antwort nach 2,5 s, mit Denken länger).
FRIST_STAND_S = 2.0
FRIST_ANTWORT_S = 300.0
FRIST_ENTLADEN_S = 30.0

#: Wie lange :func:`frage` **mit allen Runden zusammen** dauern darf — **gesetzt**. Die
#: Frist je Runde (:data:`FRIST_ANTWORT_S`) begrenzt eine Runde, nicht drei: Bis zum
#: 01.10.2026 konnte eine Frage 3 × 300 s laufen, und die Mac-App gibt nach 330 s auf
#: (``AssistentAnschluss.frist`` in ``ipad/VisboxMac/…/Assistentenleiste.swift``). Sie
#: sähe dann einen Leitungsfehler statt eines Satzes. 240 s lässt 90 s Abstand für
#: Leitung, Prüfung und Antwort; gemessen braucht eine Frage 4 bis 30 s
#: (``auf-20261001-218``).
FRIST_FRAGE_GESAMT_S = 240.0

#: Der Satz, wenn die Gesamtfrist abläuft, bevor ein Vorschlag steht.
SATZ_FRIST_ABGELAUFEN = (
    f"Der Assistent hat in {FRIST_FRAGE_GESAMT_S:.0f} s keine Antwort gefunden — bitte "
    f"noch einmal fragen, kürzer oder mit weniger auf einmal.")


def pruefe_sprachmodell(name) -> dict:
    """Darf dieses Modell geladen werden? ``{modell, lizenz, gewichte, beleg}`` — oder
    :class:`AssistentError` mit dem Satz, warum nicht."""
    if not isinstance(name, str) or not name.strip():
        raise AssistentError("Es ist kein Sprachmodell genannt.")
    modell = name.strip().lower()
    if modell in ERLAUBTE_MODELLE:
        return {"modell": modell, **ERLAUBTE_MODELLE[modell]}
    for anfang, lizenz in AUSGESCHLOSSENE_MODELLE:
        if modell.startswith(anfang):
            raise AssistentError(
                f"Das Sprachmodell {modell} ist ausgeschlossen: {lizenz} — keine der "
                f"zugelassenen Lizenzen (Regel 1). Zugelassen: "
                f"{', '.join(ERLAUBTE_MODELLE)}.")
    raise AssistentError(
        f"Das Sprachmodell {modell} ist nicht nach Regel 1 geprüft und wird nicht geladen. "
        f"Zugelassen: {', '.join(ERLAUBTE_MODELLE)}.")


def pruefe_adresse(adresse) -> str:
    """Eine Adresse für Ollama: ``http(s)://rechner:anschluss``, ohne Pfad. Sonst Satz.

    **Nur http und https.** ``urllib`` öffnet auch ``file://`` — eine Adresse aus einer
    Umgebungsvariable wäre sonst ein Weg, Dateien des Heim-PC zu lesen.
    """
    if not isinstance(adresse, str) or not adresse.strip():
        raise AssistentError("Die Adresse von Ollama ist leer.")
    teile = urllib.parse.urlsplit(adresse.strip())
    if teile.scheme not in ("http", "https") or not teile.netloc:
        raise AssistentError(
            "Die Adresse von Ollama beginnt mit http:// oder https:// und nennt einen "
            "Rechner (Vorgabe: http://127.0.0.1:11434).")
    if teile.path not in ("", "/") or teile.query or teile.fragment:
        raise AssistentError(
            "Die Adresse von Ollama trägt keinen Pfad — nur Rechner und Anschluss.")
    return f"{teile.scheme}://{teile.netloc}"


# OHNE STELLVERTRETER (Proxy). Ollama steht am Heim-PC oder im eigenen Netz; eine
# Umgebungsvariable `http_proxy` schickte die Frage sonst ueber einen fremden Rechner.
_OEFFNER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _oeffne(anfrage: urllib.request.Request, frist: float) -> bytes:
    """Die eine Stelle, an der dieses Modul ins Netz geht. Proben ersetzen sie."""
    with _OEFFNER.open(anfrage, timeout=frist) as antwort:
        return antwort.read()


class Ollama:
    """Ein Sprachmodell über Ollama — Adresse und Modell geprüft beim Bau.

    Dieselbe Form erwartet :func:`frage` von jedem Sprachmodell (in Proben ein Ersatz):
    ``modell``, ``chat(nachrichten, werkzeuge)``, ``vorhandene()``, ``geladene()``,
    ``entlade()``.
    """

    def __init__(self, adresse: str | None = None, modell: str | None = None):
        self.adresse = pruefe_adresse(
            adresse or os.environ.get(UMGEBUNG_ADRESSE) or VORGABE_ADRESSE)
        self.modell = pruefe_sprachmodell(
            modell or os.environ.get(UMGEBUNG_MODELL) or VORGABE_MODELL)["modell"]

    def _rufe(self, methode: str, pfad: str, rumpf: dict | None = None, *,
              frist: float) -> dict:
        daten = None if rumpf is None else json.dumps(rumpf).encode("utf-8")
        kopf = {"Content-Type": "application/json"} if daten is not None else {}
        anfrage = urllib.request.Request(self.adresse + pfad, data=daten, method=methode,
                                         headers=kopf)
        try:
            roh = _oeffne(anfrage, frist)
        except urllib.error.HTTPError as fehler:
            # NUR DER ZUSTANDSCODE, NICHT DER SATZ VON OLLAMA (Durchsicht 01.10.2026). Er
            # ging bis zur Mac-App durch, und Ollamas Fehler zu Modelldateien nennen Pfade
            # unter `~/.ollama` — mit dem Benutzernamen des Heim-PC (Regel 3). Wer den
            # Grund braucht, findet ihn im Protokoll von Ollama am Heim-PC.
            raise AssistentError(
                f"Ollama lehnte die Anfrage ab (Zustand {fehler.code}). Den Grund nennt das "
                f"Protokoll von Ollama am Heim-PC.") from None
        except (TimeoutError, socket.timeout):
            raise ZeitUeberschritten(
                f"Ollama antwortete nicht innerhalb von {frist:.0f} s.") from None
        except http.client.HTTPException:
            # EINE HALBE ANTWORT (`IncompleteRead`, `BadStatusLine`): Ollama brach mitten
            # in der Antwort ab, etwa weil es neu startete. Bis zum 01.10.2026 fiel das
            # durch alle Fänge und kam als Absturz der Anfrage statt als Satz.
            raise AntwortAbgebrochen(
                "Ollama brach die Antwort ab — am Heim-PC startet es vielleicht gerade neu. "
                "Bitte gleich noch einmal fragen.") from None
        except (urllib.error.URLError, OSError) as fehler:
            if isinstance(getattr(fehler, "reason", None), (TimeoutError, socket.timeout)):
                raise ZeitUeberschritten(
                    f"Ollama antwortete nicht innerhalb von {frist:.0f} s.") from None
            # KEINE ADRESSE IM SATZ: Er geht bis in die Startzeile am Mac (Regel 3).
            raise NichtErreichbar(
                "Ollama antwortet nicht — am Heim-PC läuft es nicht, oder die Adresse "
                "stimmt nicht.") from None
        try:
            wert = json.loads(roh or b"{}")
        except ValueError:
            raise AssistentError("Die Antwort von Ollama war kein JSON.") from None
        if not isinstance(wert, dict):
            raise AssistentError("Die Antwort von Ollama war kein JSON-Objekt.")
        return wert

    def chat(self, nachrichten: list, werkzeuge: list, *, frist: float | None = None) -> dict:
        """Eine Runde ``/api/chat`` — **mit** ``think: true`` (siehe Modulkopf).

        Gibt die Botschaft (``message``) zurück, wie sie kam; was davon gezeigt wird,
        entscheidet :func:`frage`. ``frist``: was von der Gesamtfrist der Frage übrig ist
        (höchstens :data:`FRIST_ANTWORT_S`).
        """
        frist = FRIST_ANTWORT_S if frist is None else max(0.1, min(frist, FRIST_ANTWORT_S))
        antwort = self._rufe("POST", "/api/chat", {
            "model": self.modell, "messages": nachrichten, "tools": werkzeuge,
            "think": True, "stream": False}, frist=frist)
        botschaft = antwort.get("message")
        if not isinstance(botschaft, dict):
            raise AssistentError("Ollama antwortete ohne Botschaft.")
        return botschaft

    def vorhandene(self) -> list[str]:
        """Die Modelle, die am Heim-PC liegen (``/api/tags``)."""
        return _namen(self._rufe("GET", "/api/tags", frist=FRIST_STAND_S))

    def geladene(self) -> list[str]:
        """Die Modelle, die gerade auf der Grafikkarte liegen (``/api/ps``)."""
        return _namen(self._rufe("GET", "/api/ps", frist=FRIST_STAND_S))

    def entlade(self) -> dict:
        """Das Sprachmodell von der Grafikkarte nehmen (``keep_alive: 0``).

        ``{"entladen": True|False|None, "satz"}``. ``False`` heisst: Es ist nicht das eigene
        Modell der Visbox (:func:`geschuetzt`) — dann wird gar nicht gefragt. ``None``
        heisst: Ollama antwortet nicht —
        dann hält es auch nichts auf der Karte, das sich entladen liesse, und der Lauf
        darf beginnen. Lehnt Ollama dagegen ab, wird geworfen: Dann ist nicht bekannt, ob
        die Karte frei ist, und ein Bild daneben liefe in den Speicherrand.
        """
        # NUR DAS EIGENE MODELL (Entscheid 106d): Ist ein anderes eingestellt — Kosmos
        # «Leiter» etwa, per Umgebungsvariable —, bleibt es auf der Karte, mit Satz.
        # `entladen: False` hält den Lauf nicht an; ob der Speicher reicht, prüft der Abholer.
        grund = geschuetzt(self.modell)
        if grund is not None:
            return {"entladen": False, "satz": f"Nicht entladen: {grund}"}
        try:
            self._rufe("POST", "/api/generate", {"model": self.modell, "keep_alive": 0},
                       frist=FRIST_ENTLADEN_S)
        except AntwortAbgebrochen:
            # ES LAEUFT, aber ob es entladen hat, ist offen — siehe `AntwortAbgebrochen`.
            raise AssistentError(
                "Ollama brach beim Entladen ab — ob das Sprachmodell noch auf der "
                "Grafikkarte liegt, ist nicht bekannt. Es wird nicht gerechnet; bitte "
                "noch einmal «Anwenden».") from None
        except NichtErreichbar:
            return {"entladen": None,
                    "satz": "Ollama antwortet nicht — es war nichts zu entladen."}
        return {"entladen": True,
                "satz": f"Das Sprachmodell {self.modell} ist entladen; die Grafikkarte "
                        f"gehört dem Bild."}


def _namen(antwort: dict) -> list[str]:
    modelle = antwort.get("models")
    if not isinstance(modelle, list):
        raise AssistentError("Ollama nannte keine Modellliste.")
    namen = []
    for m in modelle:
        if isinstance(m, dict):
            for feld in ("name", "model"):
                if isinstance(m.get(feld), str):
                    namen.append(m[feld].strip().lower())
    return namen


def _enthalten(modell: str, namen) -> bool:
    """``qwen3:30b`` in einer Liste von Ollama — ohne Kennzeichen gilt ``:latest``."""
    gesucht = {modell, modell if ":" in modell else modell + ":latest"}
    return any(n in gesucht for n in namen)


# ============================================== die Grafikkarte vor einem Bild freigeben

#: Wie lange :func:`gib_karte_frei` für Abfrage und Freigaben **zusammen** brauchen darf —
#: **gesetzt, nicht gemessen**. Gemessen ist das Freigeben eines Modells mit 0,16 s
#: (``auf-20261001-218``); ein Ollama, das hängt, soll den Bildauftrag nicht aufhalten.
FRIST_KARTE_FREI_S = 8.0

#: Wie lange danach gewartet wird, bis Ollama die Karte leer meldet (``/api/ps``) — gesetzt.
FRIST_KARTE_LEER_S = 5.0

#: Takt dieses Wartens in Sekunden.
TAKT_KARTE_LEER_S = 0.25


class _Anschluss:
    """Nur die Adresse von Ollama — für Anfragen, die kein eigenes Sprachmodell brauchen.

    :class:`Ollama` prüft beim Bau das **eigene** Modell gegen Regel 1. Zum Freigeben
    braucht es keines: Freigegeben wird, was Ollama selbst als geladen meldet, und das
    Freigeben lädt nichts. Derselbe Weg ins Netz (:meth:`Ollama._rufe`, :func:`_oeffne`).
    """

    _rufe = Ollama._rufe

    def __init__(self, adresse: str | None = None):
        self.adresse = pruefe_adresse(
            adresse or os.environ.get(UMGEBUNG_ADRESSE) or VORGABE_ADRESSE)


def _mib(wert) -> int | None:
    if isinstance(wert, bool) or not isinstance(wert, (int, float)) or wert < 0:
        return None
    return int(round(wert / 2**20))


def _gb(mib) -> str:
    return "?" if mib is None else f"{mib / 1024:.1f}".replace(".", ",") + " GB"


def _geladene_mit_groesse(anschluss, frist: float) -> list[dict]:
    """``/api/ps`` mit Grösse: je Modell einmal ``{modell, groesse_mib, vram_mib, eigen}``.

    Ollama nennt je Modell ``name`` und ``model`` (auf-20261021-300, N3) — gezählt wird jedes
    Modell einmal. ``eigen`` heisst: das Modell des Visbox-Assistenten (:func:`geschuetzt`).
    """
    antwort = anschluss._rufe("GET", "/api/ps", frist=frist)
    modelle = antwort.get("models")
    if not isinstance(modelle, list):
        raise AssistentError("Ollama nannte keine Modellliste.")
    aus, gesehen = [], set()
    for m in modelle:
        if not isinstance(m, dict):
            continue
        name = m.get("model") if isinstance(m.get("model"), str) else m.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        name = name.strip()
        grund = name.lower()
        grund = grund[:-len(":latest")] if grund.endswith(":latest") else grund
        if grund in gesehen:
            continue
        gesehen.add(grund)
        aus.append({"modell": name, "groesse_mib": _mib(m.get("size")),
                    "vram_mib": _mib(m.get("size_vram")), "eigen": geschuetzt(name) is None})
    return aus


def _gib_ein_modell_frei(anschluss, modell: str, frist: float) -> None:
    """``keep_alive: 0`` für **ein** geladenes Modell — sonst nichts.

    Zuerst über ``/api/generate`` (gemessen, ``auf-20261001-218``). Lehnt Ollama das ab —
    ein Modell, das nicht erzeugt, sondern nur einbettet oder nur spricht —, über
    ``/api/chat`` mit leerer Nachrichtenliste: Beide Wege laden nichts und rechnen nichts,
    sie setzen nur die Haltezeit auf null. Wirft :class:`AssistentError`, wenn beide
    scheitern; ein Ollama, das nicht antwortet oder hängt, wird nicht ein zweites Mal gefragt.
    """
    rumpf = {"model": modell, "keep_alive": 0}
    try:
        anschluss._rufe("POST", "/api/generate", rumpf, frist=frist)
    except (NichtErreichbar, ZeitUeberschritten):
        raise
    except AssistentError:
        anschluss._rufe("POST", "/api/chat", {**rumpf, "messages": []}, frist=frist)


def gib_karte_frei(*, adresse: str | None = None, frist_s: float = FRIST_KARTE_FREI_S,
                   leer_frist_s: float = FRIST_KARTE_LEER_S, _uhr=None, _warte=None) -> dict:
    """**Vor jedem Bildauftrag:** alle Modelle, die Ollama auf der Grafikkarte hält,
    freigeben — auch fremde — und kurz warten, bis Ollama die Karte leer meldet.

    **Owner-Entscheid 127 (über die Zentrale, 22.10.2026, Option A):** In der Demo hat
    Visbox Vorrang auf der 32-GB-Karte des Heim-PCs. Anlass: Generalprobe 327 — Bildmodell
    27,9 GB und ein Sprachmodell eines anderen Programms 22 GB passen nicht zugleich auf die
    Karte. Das andere Programm lädt sein Modell danach bei Bedarf selbst neu; der Assistent
    der Visbox ebenso (bei der nächsten Frage).

    **Was hier geschieht, und nur das:** ``GET /api/ps``; je gemeldetes Modell
    ``keep_alive: 0`` (:func:`_gib_ein_modell_frei`); dann ``/api/ps`` im Takt
    :data:`TAKT_KARTE_LEER_S`, bis es leer ist oder :data:`FRIST_KARTE_LEER_S` abläuft.
    Kein Modell wird geladen, keines gelöscht, an keinem etwas eingestellt. Was Ollama nicht
    als geladen meldet, wird nicht angefragt — ein ``keep_alive: 0`` an ein nicht geladenes
    Modell würde es erst laden.

    **Wirft nie.** Fehlt Ollama, hängt es oder antwortet es Unlesbares, läuft der Bildauftrag
    weiter wie bisher; der Befund sagt es (``ollama: aus | haengt | fehler``). Ob der Speicher
    dann reicht, prüft der Abholer wie bisher (``_speicher_reicht``, Bildeingang-Prüfung).

    Returns:
        ``{ollama, freigegeben, nicht_freigegeben, danach_leer, noch_geladen, dauer_s, satz}``.
        ``ollama`` ist ``leer`` (nichts geladen), ``freigegeben`` (alles frei, Karte leer),
        ``teilweise`` (etwas blieb oder kam wieder), ``aus``, ``haengt`` oder ``fehler``.
        ``freigegeben`` und ``nicht_freigegeben`` sind Listen ``{modell, groesse_mib,
        vram_mib, eigen}`` (``nicht_freigegeben`` mit ``satz``). ``danach_leer`` ist
        ``None``, wenn nach den Freigaben keine Auskunft mehr kam.
    """
    uhr = _uhr or time.monotonic
    warte = _warte or time.sleep
    beginn = uhr()
    aus = {"ollama": None, "freigegeben": [], "nicht_freigegeben": [], "danach_leer": None,
           "noch_geladen": [], "dauer_s": None, "satz": ""}

    def rest() -> float:
        return frist_s - (uhr() - beginn)

    def fertig(zustand: str, satz: str) -> dict:
        aus.update(ollama=zustand, dauer_s=round(max(0.0, uhr() - beginn), 2), satz=satz)
        return aus

    try:
        anschluss = _Anschluss(adresse)
    except AssistentError as fehler:
        return fertig("fehler", f"Grafikkarte nicht freigegeben: {fehler}")
    try:
        vorher = _geladene_mit_groesse(anschluss, max(0.1, min(FRIST_STAND_S, rest())))
    except (ZeitUeberschritten, AntwortAbgebrochen):
        return fertig("haengt", "Ollama antwortet nicht rechtzeitig — nichts freigegeben; der "
                                "Bildauftrag läuft trotzdem.")
    except NichtErreichbar:
        return fertig("aus", "Ollama läuft nicht — es hält nichts auf der Grafikkarte, "
                             "nichts freizugeben.")
    except AssistentError as fehler:
        return fertig("fehler", f"Ollama gab keine lesbare Auskunft ({fehler}) — nichts "
                                f"freigegeben; der Bildauftrag läuft trotzdem.")
    if not vorher:
        aus["danach_leer"] = True
        return fertig("leer", "Ollama hielt kein Modell auf der Grafikkarte — nichts "
                              "freizugeben.")

    haengt = False
    for m in vorher:
        if haengt or rest() <= 0:
            aus["nicht_freigegeben"].append({**m, "satz": "Frist abgelaufen — nicht gefragt."})
            continue
        try:
            _gib_ein_modell_frei(anschluss, m["modell"], max(0.1, min(FRIST_ENTLADEN_S, rest())))
        except (ZeitUeberschritten, NichtErreichbar) as fehler:
            # Wer hier nicht antwortet, antwortet beim nächsten Modell auch nicht.
            haengt = True
            aus["nicht_freigegeben"].append({**m, "satz": str(fehler)})
        except AssistentError as fehler:
            aus["nicht_freigegeben"].append({**m, "satz": str(fehler)})
        else:
            aus["freigegeben"].append(m)

    noch = None
    if not haengt:
        ende = uhr() + max(0.0, leer_frist_s)
        while True:
            try:
                noch = _geladene_mit_groesse(anschluss, FRIST_STAND_S)
            except AssistentError:
                noch = None
                break
            if not noch or uhr() >= ende:
                break
            warte(TAKT_KARTE_LEER_S)
    aus["danach_leer"] = None if noch is None else not noch
    aus["noch_geladen"] = [m["modell"] for m in noch or ()]

    def liste(modelle) -> str:
        return ", ".join(f"{m['modell']} ({_gb(m['vram_mib'] if m['vram_mib'] is not None else m['groesse_mib'])}, "
                         f"{'Assistent der Visbox' if m['eigen'] else 'anderes Programm'})"
                         for m in modelle)

    teile = []
    if aus["freigegeben"]:
        teile.append(f"Grafikkarte für das Bild freigegeben: {liste(aus['freigegeben'])}")
    if aus["nicht_freigegeben"]:
        teile.append(f"nicht freigegeben: {liste(aus['nicht_freigegeben'])}")
    dauer = f"{max(0.0, uhr() - beginn):.1f}".replace(".", ",")
    if aus["danach_leer"] is True:
        teile.append(f"Ollama meldet die Karte nach {dauer} s leer")
    elif aus["danach_leer"] is False:
        teile.append(f"nach {dauer} s liegt noch {', '.join(aus['noch_geladen'])} auf der Karte")
    else:
        teile.append(f"danach keine Auskunft von Ollama ({dauer} s)")
    zustand = ("freigegeben" if aus["danach_leer"] is True and not aus["nicht_freigegeben"]
               else "teilweise")
    return fertig(zustand, "; ".join(teile) + ". Die Sprachmodelle laden bei der nächsten "
                                              "Frage selbst wieder.")


# ======================================================================= der Stand

STAND_BEREIT = "bereit"
STAND_LAEDT = "laedt"
STAND_FEHLT = "fehlt"
STAND_AUS = "aus"
STAENDE = (STAND_BEREIT, STAND_LAEDT, STAND_FEHLT, STAND_AUS)

#: Der Satz, wenn ein Bild rechnet — in :func:`frage` als Absage, in :func:`stand` als Zustand.
SATZ_BILD_RECHNET = (
    "Gerade rechnet ein Bild. Bildmodell und Sprachmodell passen nicht zugleich auf die "
    "Grafikkarte — der Assistent antwortet wieder, wenn das Bild fertig ist.")

#: Der Satz, wenn das Bildmodell **nach** einem Lauf noch auf der Karte liegt und sich
#: nicht freigeben liess (``auf-20261001-218``: 25,3 GB im Prozess des Dienstes). Fragen
#: hiesse dann, das Sprachmodell daneben zu laden — und beide passen nicht.
SATZ_BILDMODELL_GELADEN = (
    "Das Bildmodell liegt nach dem letzten Lauf noch auf der Grafikkarte und liess sich "
    "nicht freigeben. Neben ihm passt das Sprachmodell nicht — die Fläche am Heim-PC neu "
    "starten, dann antwortet der Assistent wieder.")


def stand(*, sprachmodell=None, bild_rechnet: bool = False,
          bildmodell_geladen: bool = False) -> dict:
    """Für die Startzeile: ``{"stand", "modell", "satz"}`` — **liest nur**, lädt nichts.

    * ``aus`` — Ollama antwortet nicht.
    * ``fehlt`` — Ollama antwortet, das Modell liegt nicht da (oder ist nicht zugelassen).
    * ``laedt`` — das Modell liegt da, aber gerade rechnet ein Bild, oder das Bildmodell
      liegt nach einem Lauf noch auf der Karte (``bildmodell_geladen``, eigener Satz);
      danach wird es wieder geladen (es teilt sich die Karte nicht mit dem Bildmodell).
    * ``bereit`` — es antwortet. Ob es schon auf der Karte liegt (sofort) oder bei der
      ersten Frage geladen wird (gemessen: kalt 2,4 s, nach einem Bild 3,8 s), sagt der
      Satz. **Warum das nicht «laedt» heisst:** Ollama nimmt ein Modell nach einer Pause
      selbst von der Karte, und nach jedem «Anwenden» tut es dieser Assistent. Hiesse das
      «laedt», bliebe die Eingabe danach gesperrt — und nichts lüde es je wieder.
    """
    try:
        modell = sprachmodell if sprachmodell is not None else Ollama()
        name = pruefe_sprachmodell(getattr(modell, "modell", None))["modell"]
    except AssistentError as fehler:
        return {"stand": STAND_FEHLT, "modell": None, "satz": str(fehler)}
    try:
        vorhanden = modell.vorhandene()
    except NichtErreichbar:
        return {"stand": STAND_AUS, "modell": name,
                "satz": "Ollama antwortet am Heim-PC nicht — der Assistent ist aus. "
                        "Bilder gehen trotzdem."}
    except AssistentError as fehler:
        return {"stand": STAND_AUS, "modell": name, "satz": str(fehler)}
    if not _enthalten(name, vorhanden):
        return {"stand": STAND_FEHLT, "modell": name,
                "satz": f"Das Sprachmodell {name} liegt am Heim-PC nicht vor "
                        f"(dort: ollama pull {name})."}
    if bild_rechnet:
        return {"stand": STAND_LAEDT, "modell": name, "satz": SATZ_BILD_RECHNET}
    if bildmodell_geladen:
        # NICHT «bereit» (Befund auf-20261001-218): Bei 6,1 GB frei hiess es «bereit»,
        # und die naechste Frage haette 25,1 GB daneben geladen.
        return {"stand": STAND_LAEDT, "modell": name, "satz": SATZ_BILDMODELL_GELADEN}
    try:
        geladen = _enthalten(name, modell.geladene())
    except AssistentError:
        geladen = False
    return {"stand": STAND_BEREIT, "modell": name,
            "satz": (f"Der Assistent ist bereit ({name})." if geladen else
                     f"Der Assistent ist bereit ({name}); die erste Antwort dauert einige "
                     f"Sekunden länger, weil das Modell erst geladen wird.")}


# ===================================================================== die Werkzeuge

#: Die Felder des Standpunkts — **jedes ein Feld von** :func:`aiimaging.kette.baue_kette`.
#: ``kamera`` (das Richtungskürzel) gehört dazu: Augenhöhe, Eckwinkel und Kameramodus
#: wirken nur mit ihm (``kette.standpunkt_widerspruch``).
STANDPUNKT_FELDER = ("kamera", "kamera_modus", "rahmung", "augenhoehe", "bias_grad",
                     "auge", "blick_auf", "brennweite")

#: Was beim Wechsel der Quelle **ausdrücklich geleert** wird (``None`` = Vorgabe). Die
#: Einstellungen eines Laufs legen sich über die der Mappe; stünde dort ein Auge und
#: schlüge der Assistent eine Richtung vor, wäre der Standpunkt zweimal bestellt, und der
#: Lauf scheiterte erst am Blender-Knoten. Gelesen wird das von ``arbeitsgang.rechne``
#: (``{**mappe, **lauf}``) und ``baue_kette`` (``None`` heisst nicht angefasst).
_LEEREN_BEI_RICHTUNG = ("auge", "blick_auf", "innenraum")
_LEEREN_BEI_HAND = ("kamera", "kamera_modus", "augenhoehe", "bias_grad", "deckungsgrad",
                    "innenraum")

#: Wie die Karte eine Richtung nennt (Kürzel aus ``kameras.RICHTUNGEN``).
RICHTUNGSNAMEN = {
    "n": "von Norden", "e": "von Osten", "s": "von Süden", "w": "von Westen",
    "nNE": "von Norden, zur Nordost-Ecke gedreht", "nNW": "von Norden, zur Nordwest-Ecke gedreht",
    "eEN": "von Osten, zur Nordost-Ecke gedreht", "eES": "von Osten, zur Südost-Ecke gedreht",
    "sSE": "von Süden, zur Südost-Ecke gedreht", "sSW": "von Süden, zur Südwest-Ecke gedreht",
    "wWS": "von Westen, zur Südwest-Ecke gedreht", "wWN": "von Westen, zur Nordwest-Ecke gedreht",
}

#: Die zwei Rahmungen, die die Kette unterscheidet: ``bauwerk`` (Vorgabe, rahmt nach dem
#: Gebäude) und alles andere — hier ``szene`` (rahmt nach der ganzen Szene).
RAHMUNGEN = ("bauwerk", "szene")

#: Längste Bildauftrag-Zeile — **gesetzt, nicht gemessen**: Ein Bildauftrag ist eine Reihe
#: Stichworte; was länger ist, ist eher ein Aufsatz des Modells als ein Auftrag.
BILDAUFTRAG_HOECHSTENS = 600

_RICHTUNGSTEXT = ", ".join(f"{k} ({v})" for k, v in RICHTUNGSNAMEN.items())

WERKZEUGE = [
    {"type": "function", "function": {
        "name": "standpunkt_vorschlagen",
        "description": (
            "Schlägt vor, woher die Kamera auf das Gebäude schaut. Entweder eine "
            "Himmelsrichtung («kamera»), dann dürfen «augenhoehe», «bias_grad» und "
            "«kamera_modus» dazu — oder ein Standpunkt von Hand («auge» und «blick_auf» in "
            "Metern), dann ohne «kamera». Nie beides. Rechnet nichts; die Nutzerin "
            "entscheidet mit «Anwenden»."),
        "parameters": {"type": "object", "properties": {
            "kamera": {"type": "string", "enum": list(kameras.RICHTUNGSFOLGE),
                       "description": "Richtung, aus der die Kamera schaut: "
                                      + _RICHTUNGSTEXT + "."},
            "augenhoehe": {"type": "number",
                           "description": "Augenhöhe in Metern, z. B. 1.6 für "
                                          "Fussgängersicht. Nur mit «kamera»."},
            "bias_grad": {"type": "number",
                          "description": "Bei einer Eckrichtung: wie weit zur Ecke gedreht, "
                                         "in Grad (30 = Hauptfassade führt, 45 = echte "
                                         "Ecke). Nur mit «kamera»."},
            "kamera_modus": {"type": "string", "enum": list(kameras.MODI),
                             "description": "«shift»: senkrechte Kanten bleiben senkrecht; "
                                            "«gekippt»: Kamera geneigt. Nur mit «kamera»."},
            "rahmung": {"type": "string", "enum": list(RAHMUNGEN),
                        "description": "«bauwerk»: Bild nach dem Gebäude rahmen; «szene»: "
                                       "nach der ganzen Szene."},
            "auge": {"type": "array", "items": {"type": "number"},
                     "description": "Standpunkt von Hand: [x, y, z] in Metern. Nur ohne "
                                    "«kamera»."},
            "blick_auf": {"type": "array", "items": {"type": "number"},
                          "description": "Wohin die Kamera schaut: [x, y, z] in Metern. Nur "
                                         "mit «auge»."},
            "brennweite": {"type": "number",
                           "description": "Brennweite in Millimetern (Kleinbild), z. B. 24 "
                                          "oder 35."},
        }, "required": []}}},
    {"type": "function", "function": {
        "name": "bildauftrag_vorschlagen",
        "description": (
            "Schlägt vor, was das Bild zeigen soll: Licht, Stimmung, Umgebung, Material — "
            "auf ENGLISCH, als kurze Stichworte mit Kommas, z. B. «evening light, street "
            "view, residential building». Er ERSETZT den bisherigen Bildauftrag der Mappe "
            "ganz: Übernimm dessen Gegenstand (das Gebäude, seine Lage, seine Umgebung), "
            "übersetzt ins Englische, und ändere nur, worum die Nutzerin bittet. Die Form "
            "des Gebäudes kommt aus dem Modell, nicht aus diesem Text. Rechnet nichts."),
        "parameters": {"type": "object", "properties": {
            "prompt": {"type": "string",
                       "description": "Der Bildauftrag auf Englisch, Stichworte mit Kommas."},
        }, "required": ["prompt"]}}},
    {"type": "function", "function": {
        "name": "varianten_vorschlagen",
        "description": (
            "Schlägt vor, mehrere Bilder derselben Einstellung zu rechnen, die sich nur im "
            "Startwert unterscheiden (2 bis 8). Rechnet nichts."),
        "parameters": {"type": "object", "properties": {
            "anzahl": {"type": "integer", "description": "Wie viele Bilder, 2 bis 8."},
            "startwert": {"type": "integer",
                          "description": "Erster Startwert (0 oder grösser); die weiteren "
                                         "zählen hoch. Weglassen: der der Mappe."},
        }, "required": ["anzahl"]}}},
]

_WERKZEUGNAMEN = tuple(w["function"]["name"] for w in WERKZEUGE)

SYSTEMTEXT = (
    "Du bist der Assistent einer Bild-App für Architektinnen und Architekten. Aus einem "
    "3D-Modell entsteht ein Bild; du hilfst, es einzustellen. Du rechnest nie selbst ein "
    "Bild: Du machst mit den Werkzeugen einen Vorschlag, und gerechnet wird erst, wenn die "
    "Nutzerin «Anwenden» drückt. Benutze nur die Werkzeuge, die zur Bitte passen. Den "
    "Bildauftrag schreibst du auf Englisch. Antworte danach in ein bis zwei kurzen Sätzen "
    "auf Deutsch, in Schweizer Schreibung (ss statt ß). Behaupte nie, ein Bild sei gerechnet "
    "oder geprüft. Ein Urteil über ein Bild änderst du nicht, und keine Prüfung lässt du "
    "aus — das kannst und darfst du nicht. Antwortet ein Werkzeug mit «Abgewiesen:», "
    "korrigiere den Vorschlag oder sage kurz, warum es nicht geht. Ist ein Ort unklar "
    "(etwa «von der Strasse her»), frage kurz nach, auf welcher Seite sie liegt, statt eine "
    "Himmelsrichtung zu raten.")


def _zahl(feld: str, wert, *, positiv: bool = True) -> float:
    """Eine endliche Zahl — auch aus einem Text wie ``"1.6"``, den Modelle gern schicken."""
    if isinstance(wert, str):
        try:
            wert = float(wert.strip())
        except ValueError:
            raise _Abweisung(f"«{feld}» ist eine Zahl, war {wert!r}.") from None
    if isinstance(wert, bool) or not isinstance(wert, (int, float)) or not math.isfinite(wert):
        raise _Abweisung(f"«{feld}» ist eine Zahl, war {wert!r}.")
    if positiv and wert <= 0:
        raise _Abweisung(f"«{feld}» ist grösser als null, war {wert!r}.")
    return float(wert)


def _ganz(feld: str, wert) -> int:
    if isinstance(wert, str) and wert.strip().lstrip("-").isdigit():
        wert = int(wert.strip())
    if isinstance(wert, float) and wert.is_integer():
        wert = int(wert)
    if isinstance(wert, bool) or not isinstance(wert, int):
        raise _Abweisung(f"«{feld}» ist eine ganze Zahl, war {wert!r}.")
    return wert


def _punkt(feld: str, wert) -> list[float]:
    if not isinstance(wert, (list, tuple)) or len(wert) != 3:
        raise _Abweisung(f"«{feld}» ist ein Punkt aus drei Zahlen [x, y, z] in Metern, "
                         f"war {wert!r}.")
    return [_zahl(feld, w, positiv=False) for w in wert]


def _nur_bekannte(werkzeug: str, argumente: dict, kettenname: dict) -> None:
    """Nur die Felder dieses Werkzeugs — und jedes davon ein echtes Feld der Kette.

    ``kettenname`` sagt je Werkzeugfeld, wie es in :func:`aiimaging.kette.baue_kette`
    heisst (``None``: kein Feld der Kette, z. B. die Anzahl der Varianten, die an
    ``/api/rechne`` geht und dort geprüft wird).
    """
    fremd = sorted(set(argumente) - set(kettenname))
    if fremd:
        raise _Abweisung(f"Diese Felder kennt «{werkzeug}» nicht: {', '.join(fremd)}. "
                         f"Bekannt sind: {', '.join(kettenname)}.")
    # GEGEN DIE ECHTEN FELDER DER KETTE, nicht nur gegen die eigene Liste: Benennt die
    # Kette ein Feld um, faellt der Vorschlag hier und nicht erst beim Rechnen.
    felder = set(inspect.signature(kette.baue_kette).parameters)
    nicht_in_kette = sorted(k for k in argumente
                            if kettenname[k] is not None and kettenname[k] not in felder)
    if nicht_in_kette:
        raise _Abweisung(f"Diese Felder kennt die Bildkette nicht: "
                         f"{', '.join(nicht_in_kette)}.")


_STANDPUNKT_IN_DER_KETTE = {f: f for f in STANDPUNKT_FELDER}
_BILDAUFTRAG_IN_DER_KETTE = {"prompt": "prompt"}
_VARIANTEN_IN_DER_KETTE = {"anzahl": None, "startwert": "seed"}


def _standpunkt(argumente: dict, mappe: dict | None = None) -> dict:
    """Die Felder eines Standpunkts → Einstellungen samt geleerter Gegenquelle.

    ``mappe``: die Einstellungen der Mappe, über die sich der Vorschlag legt — geprüft
    wird **das, was der Lauf sehen wird** (``{**mappe, **vorschlag}``, dieselbe Reihenfolge
    wie :func:`aiimaging.arbeitsgang.rechne`), nicht der Vorschlag allein. Ohne Mappe gilt
    der Vorschlag allein.
    """
    _nur_bekannte("standpunkt_vorschlagen", argumente, _STANDPUNKT_IN_DER_KETTE)
    felder = {k: v for k, v in argumente.items() if v is not None}
    if not felder:
        raise _Abweisung("Der Standpunkt ist leer — mindestens «kamera» oder «auge».")
    e: dict = {}
    if "kamera" in felder:
        if felder["kamera"] not in kameras.RICHTUNGEN:
            raise _Abweisung(f"«kamera» ist eine dieser Richtungen: "
                             f"{', '.join(kameras.RICHTUNGSFOLGE)} — war {felder['kamera']!r}.")
        e["kamera"] = felder["kamera"]
    if "kamera_modus" in felder:
        if felder["kamera_modus"] not in kameras.MODI:
            raise _Abweisung(f"«kamera_modus» ist {' oder '.join(kameras.MODI)} — war "
                             f"{felder['kamera_modus']!r}.")
        e["kamera_modus"] = felder["kamera_modus"]
    if "rahmung" in felder:
        if felder["rahmung"] not in RAHMUNGEN:
            raise _Abweisung(f"«rahmung» ist {' oder '.join(RAHMUNGEN)} — war "
                             f"{felder['rahmung']!r}.")
        e["rahmung"] = felder["rahmung"]
    if "augenhoehe" in felder:
        e["augenhoehe"] = _zahl("augenhoehe", felder["augenhoehe"])
    if "bias_grad" in felder:
        e["bias_grad"] = _zahl("bias_grad", felder["bias_grad"])
        try:
            kameras.richtungen(e["bias_grad"])
        except ValueError as fehler:
            raise _Abweisung(str(fehler)) from None
    if "brennweite" in felder:
        e["brennweite"] = _zahl("brennweite", felder["brennweite"])
    for feld in ("auge", "blick_auf"):
        if feld in felder:
            e[feld] = _punkt(feld, felder[feld])
    # GELEERT WIRD NUR, WAS DER VORSCHLAG NICHT SELBST NENNT: Schlaegt er «kamera» und
    # «auge» zugleich vor, soll die Pruefung unten den Widerspruch sehen, statt dass das
    # Leeren ihn still aufloest.
    if "kamera" in e:
        e.update({k: None for k in _LEEREN_BEI_RICHTUNG if k not in e})
    elif "auge" in e:
        e.update({k: None for k in _LEEREN_BEI_HAND if k not in e})
    # GEGEN DIE MAPPE GEPRUEFT, nicht gegen den Vorschlag allein (Durchsicht 01.10.2026).
    # Allein geprueft wurde «1,6 m Augenhoehe» bei einer Mappe, die schon eine Richtung
    # traegt, abgewiesen («ohne Kameraweg»), obwohl der Lauf sie mit der Richtung der
    # Mappe gerechnet haette; und «Brennweite 24» bei einer Mappe mit Innenraum ging
    # durch und scheiterte erst am Blender-Knoten («Standpunkt zweimal bestellt»). Die
    # Leerungen oben gehoeren dazu: Sie legen sich wie im Lauf ueber die Mappe.
    gesamt = {**(mappe or {}), **e}
    if (gesamt.get("auge") is None) != (gesamt.get("blick_auf") is None) \
            and gesamt.get("kamera") is None:
        raise _Abweisung("Ein Standpunkt von Hand braucht beides: «auge» und «blick_auf».")
    # DIE REGELN DER KETTE, nicht eigene: zweimal bestellt, oder ohne den Weg, auf dem es
    # wirkt (z. B. «auge» zusammen mit «kamera_modus»).
    widerspruch = kette.standpunkt_widerspruch(gesamt)
    if widerspruch is not None:
        raise _Abweisung(widerspruch)
    return e


def _bildauftrag(argumente: dict) -> dict:
    _nur_bekannte("bildauftrag_vorschlagen", argumente, _BILDAUFTRAG_IN_DER_KETTE)
    prompt = argumente.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise _Abweisung("Der Bildauftrag («prompt») ist leer.")
    prompt = " ".join(prompt.split())
    if len(prompt) > BILDAUFTRAG_HOECHSTENS:
        raise _Abweisung(f"Der Bildauftrag ist länger als {BILDAUFTRAG_HOECHSTENS} Zeichen "
                         f"— kürzer, als Stichworte.")
    return {"prompt": prompt}


def _varianten(argumente: dict) -> dict:
    _nur_bekannte("varianten_vorschlagen", argumente, _VARIANTEN_IN_DER_KETTE)
    if argumente.get("anzahl") is None:
        raise _Abweisung("Wie viele Varianten («anzahl»), ist nicht gesagt.")
    anzahl = _ganz("anzahl", argumente["anzahl"])
    # DIE GRENZEN DER BIBLIOTHEK, nicht eigene — dieselben wie bei POST /api/rechne.
    try:
        arbeitsgang.pruefe_varianten(anzahl, arbeitsgang.VARIANTEN_STARTWERTE)
    except arbeitsgang.ArbeitsgangError as fehler:
        raise _Abweisung(str(fehler)) from None
    teil = {"varianten": anzahl}
    if argumente.get("startwert") is not None:
        startwert = _ganz("startwert", argumente["startwert"])
        if startwert < 0:
            raise _Abweisung(f"«startwert» ist 0 oder grösser, war {startwert}.")
        teil["seed"] = startwert
    return teil


_PRUEFER = {"standpunkt_vorschlagen": _standpunkt, "bildauftrag_vorschlagen": _bildauftrag,
            "varianten_vorschlagen": _varianten}


# ============================================================================ der Vorschlag

#: Rechenzeit je Variante in Sekunden, die **ganze Kette** (Blender, Bild, Prüfung) —
#: **angesetzt nach Messung**, ``auf-20261001-218`` C2/C3: drei Varianten über «Anwenden»
#: im Mittel 10,7 s je Variante (die erste mit Multipass 14,7 s, die weiteren je 8,6 s),
#: Gewichte im Plattencache. Angesetzt ist die langsamere erste, aufgerundet auf 15 s —
#: so der Vorschlag des Heim-PC; kalt dauert es länger (Bild allein kalt 15,0 s,
#: ``auf-20261001-213``). ``None`` hiesse wieder «nicht gemessen», und die Karte sagte es.
#:
#: **Nachgezogen nach ``auf-20261001-221`` B1 (01.10.2026):** drei Varianten über «Anwenden» am
#: Dienst in 29,3 s, also knapp 10 s je Variante samt Laden — die 15 s waren zu vorsichtig, und
#: die Karte sagte für 20 s wie für 50 s «etwa 1 Minute». Jetzt 10 s.
RECHENZEIT_JE_VARIANTE_S: float | None = 10.0

#: Wechsel Sprachmodell → Bildmodell und zurück, gemessen ``auf-20261001-218`` C2:
#: entladen 0,16 s, wieder antworten nach 4,4 s. Er kommt zur Rechenzeit dazu.
WECHSEL_S = 4.6


def _zahltext(z: float) -> str:
    return f"{z:g}"


def _saetze(e: dict, varianten: int | None) -> list[str]:
    """Die Zeilen der Karte (Blatt 14) — aus den geprüften Einstellungen, nicht aus dem
    Text des Modells."""
    saetze = []
    teile = []
    if e.get("kamera") is not None:
        teile.append(f"Standpunkt {RICHTUNGSNAMEN[e['kamera']]} ({e['kamera']})")
    elif e.get("auge") is not None:
        auge = ", ".join(_zahltext(z) for z in e["auge"])
        ziel = ", ".join(_zahltext(z) for z in e["blick_auf"])
        teile.append(f"Standpunkt von Hand: Auge ({auge}) m, Blick auf ({ziel}) m")
    if e.get("augenhoehe") is not None:
        teile.append(f"{_zahltext(e['augenhoehe'])} m Augenhöhe")
    if e.get("bias_grad") is not None:
        teile.append(f"{_zahltext(e['bias_grad'])}° zur Ecke")
    if e.get("kamera_modus") == kameras.MODUS_SHIFT:
        teile.append("senkrechte Kanten bleiben senkrecht")
    elif e.get("kamera_modus") == kameras.MODUS_GEKIPPT:
        teile.append("Kamera geneigt")
    if e.get("brennweite") is not None:
        teile.append(f"Brennweite {_zahltext(e['brennweite'])} mm")
    if e.get("rahmung") is not None:
        teile.append("gerahmt nach dem Gebäude" if e["rahmung"] == "bauwerk"
                     else "gerahmt nach der ganzen Szene")
    if teile:
        saetze.append(" · ".join(teile))
    if e.get("prompt") is not None:
        saetze.append(f"Bildauftrag: «{e['prompt']}»")
        if sprache.sieht_englisch_aus(e["prompt"])["englisch"] is False:
            saetze.append("Der Bildauftrag sieht nicht englisch aus — das Bildmodell "
                          "versteht Englisch deutlich besser.")
    if varianten is not None:
        if e.get("seed") is not None:
            saetze.append(f"{varianten} Varianten, Startwerte {e['seed']}–"
                          f"{e['seed'] + varianten - 1}")
        else:
            saetze.append(f"{varianten} Varianten, Startwerte fortlaufend ab dem der Mappe")
    elif e.get("seed") is not None:
        saetze.append(f"Startwert {e['seed']}")
    return saetze


def _rechenzeit(varianten: int | None) -> dict:
    if RECHENZEIT_JE_VARIANTE_S is None:
        return {"sekunden": None,
                "satz": "Rechenzeit am Heim-PC: noch nicht gemessen."}
    sekunden = RECHENZEIT_JE_VARIANTE_S * (varianten or 1) + WECHSEL_S
    # UNTER EINER MINUTE IN SEKUNDEN (Befund 221): «etwa 1 Minute» für 20 s wie für 50 s sagt
    # nichts. Aufgerundet auf zehn — lieber früher fertig als später als gesagt.
    if sekunden < 60:
        zehner = max(10, math.ceil(sekunden / 10) * 10)
        satz = f"Rechenzeit etwa {zehner} Sekunden am Heim-PC."
    else:
        minuten = max(1, round(sekunden / 60))
        satz = f"Rechenzeit etwa {minuten} Minute{'n' if minuten != 1 else ''} am Heim-PC."
    return {"sekunden": round(sekunden), "satz": satz}


def _vorschlag(e: dict, varianten: int | None) -> dict:
    return {"einstellungen": e, "varianten": varianten,
            "saetze": _saetze(e, varianten), "rechenzeit": _rechenzeit(varianten)}


def pruefe_vorschlag(vorschlag, mappe: dict | None = None) -> tuple[dict, int | None]:
    """Ein Vorschlag, **wie er von der Leitung zurückkommt** → ``(einstellungen, varianten)``.

    Er wird **neu geprüft**, mit denselben Prüfern wie beim Vorschlagen — er kam über das
    Netz und kann alles enthalten. Angewendet wird nur, was ein Werkzeug auch hätte
    vorschlagen können; die Einstellungen werden aus den Prüfern neu gebaut, nicht
    übernommen. ``mappe`` wie bei :func:`frage` — der Standpunkt wird gegen die
    Einstellungen der Mappe geprüft, über die er sich legt.
    """
    if not isinstance(vorschlag, dict):
        raise AssistentError("Es fehlt der Vorschlag (ein Objekt mit «einstellungen» und "
                             "«varianten»).")
    e = vorschlag.get("einstellungen") or {}
    if not isinstance(e, dict):
        raise AssistentError("Die Einstellungen des Vorschlags sind ein Objekt.")
    leerbar = set(_LEEREN_BEI_RICHTUNG) | set(_LEEREN_BEI_HAND)
    erlaubt = set(STANDPUNKT_FELDER) | leerbar | {"prompt", "seed"}
    fremd = sorted(set(e) - erlaubt)
    if fremd:
        raise AssistentError(f"Diese Einstellungen schlägt der Assistent nie vor: "
                             f"{', '.join(fremd)} — der Vorschlag wird nicht angewendet.")
    nur_leer = sorted(k for k in set(e) - set(STANDPUNKT_FELDER) - {"prompt", "seed"}
                      if e[k] is not None)
    if nur_leer:
        raise AssistentError(f"Diese Einstellungen leert der Assistent nur: "
                             f"{', '.join(nur_leer)}.")
    neu: dict = {}
    varianten = vorschlag.get("varianten")
    try:
        standpunkt = {k: e[k] for k in STANDPUNKT_FELDER if e.get(k) is not None}
        if standpunkt:
            neu.update(_standpunkt(standpunkt, mappe))
        if e.get("prompt") is not None:
            neu.update(_bildauftrag({"prompt": e["prompt"]}))
        if varianten is not None or e.get("seed") is not None:
            if varianten is not None:
                teil = _varianten({"anzahl": varianten, "startwert": e.get("seed")})
                varianten = teil.pop("varianten")
            else:
                teil = {"seed": _ganz("startwert", e["seed"])}
                if teil["seed"] < 0:
                    raise _Abweisung("Der Startwert ist 0 oder grösser.")
            neu.update(teil)
    except _Abweisung as a:
        raise AssistentError(str(a)) from None
    if not neu and varianten is None:
        raise AssistentError("Der Vorschlag ist leer — es gibt nichts anzuwenden.")
    return neu, varianten


# ============================================================================== fragen

#: Grenzen der Eingabe — **gesetzt, nicht gemessen**: lang genug für eine Bitte und ein
#: Gespräch, kurz genug, dass eine Anfrage das Modell nicht minutenlang beschäftigt.
NACHRICHT_HOECHSTENS = 2000
VERLAUF_HOECHSTENS = 40
VERLAUF_TEXT_HOECHSTENS = 4000

#: Wie oft das Modell nach einem Werkzeugergebnis weiterreden darf — **gesetzt**: einmal
#: vorschlagen, einmal auf eine Abweisung reagieren, einmal antworten.
RUNDEN_HOECHSTENS = 3

_ROLLEN = {"mensch": "user", "assistent": "assistant"}

_DENKEN = re.compile(r"<think>.*?</think>", re.S | re.I)


def _ohne_denken(text) -> str:
    """Nur, was gezeigt werden darf — nie der Gedankentext (siehe Modulkopf)."""
    if not isinstance(text, str):
        return ""
    text = _DENKEN.sub("", text)
    klein = text.lower()
    if "</think>" in klein:
        text = text[klein.rindex("</think>") + len("</think>"):]
        klein = text.lower()
    if "<think>" in klein:
        text = text[:klein.index("<think>")]
    return text.strip()


def _pruefe_verlauf(verlauf) -> list[dict]:
    """``[{"von": "mensch"|"assistent", "text": …}]`` → Ollama-Nachrichten.

    **Nur diese zwei Rollen.** Eine Rolle «system» oder «tool» aus dem Netz wäre ein Weg,
    dem Modell eine Anweisung unterzuschieben, die wie die eigene aussieht.
    """
    if verlauf is None:
        return []
    if not isinstance(verlauf, (list, tuple)):
        raise AssistentError("Der Verlauf ist eine Liste von Beiträgen.")
    if len(verlauf) > VERLAUF_HOECHSTENS:
        raise AssistentError(f"Der Verlauf hat mehr als {VERLAUF_HOECHSTENS} Beiträge — "
                             f"bitte nur die letzten {VERLAUF_HOECHSTENS} schicken.")
    nachrichten = []
    for beitrag in verlauf:
        if (not isinstance(beitrag, dict) or beitrag.get("von") not in _ROLLEN
                or not isinstance(beitrag.get("text"), str)):
            raise AssistentError("Ein Beitrag im Verlauf ist {«von»: «mensch» oder "
                                 "«assistent», «text»: …}.")
        if len(beitrag["text"]) > VERLAUF_TEXT_HOECHSTENS:
            raise AssistentError(f"Ein Beitrag im Verlauf ist länger als "
                                 f"{VERLAUF_TEXT_HOECHSTENS} Zeichen.")
        nachrichten.append({"role": _ROLLEN[beitrag["von"]],
                            "content": _ohne_denken(beitrag["text"])
                            if beitrag["von"] == "assistent" else beitrag["text"]})
    return nachrichten


def _lies_aufruf(aufruf) -> tuple[str, dict]:
    funktion = aufruf.get("function") if isinstance(aufruf, dict) else None
    if not isinstance(funktion, dict):
        raise _Abweisung("Der Werkzeugaufruf war nicht lesbar.")
    name = funktion.get("name")
    argumente = funktion.get("arguments")
    if isinstance(argumente, str):
        try:
            argumente = json.loads(argumente or "{}")
        except ValueError:
            raise _Abweisung("Die Angaben zum Werkzeug waren kein JSON.") from None
    if argumente is None:
        argumente = {}
    if not isinstance(argumente, dict):
        raise _Abweisung("Die Angaben zum Werkzeug sind ein Objekt.")
    if name not in _PRUEFER:
        raise _Abweisung(f"Ein Werkzeug «{name}» gibt es nicht; es gibt "
                         f"{', '.join(_WERKZEUGNAMEN)}.")
    return name, argumente


#: Die Angaben der Mappe, die den Standpunkt betreffen — die Felder der Werkzeuge und die
#: zwei, die nur die Mappe trägt (``innenraum``, ``deckungsgrad``).
_STANDPUNKT_DER_MAPPE = (*STANDPUNKT_FELDER, "innenraum", "deckungsgrad")


def _angabe_fuer_das_modell(feld: str, wert) -> str:
    """Eine Angabe der Mappe als kurzer Text — **nur Zahlen und Kürzel**, kein freier Text.

    Der Innenraum wird nur genannt, nicht beschrieben: Sein Wert kann den Namen eines
    Raumes aus dem Modell tragen, und den braucht das Sprachmodell nicht.
    """
    if feld == "innenraum":
        return "innenraum (Standpunkt aus einem Raum gerechnet)"
    if feld == "kamera" and wert in RICHTUNGSNAMEN:
        return f"kamera «{wert}» ({RICHTUNGSNAMEN[wert]})"
    if isinstance(wert, bool) or isinstance(wert, (int, float)):
        return f"{feld} {_zahltext(wert)}"
    if isinstance(wert, (list, tuple)) and all(
            isinstance(z, (int, float)) and not isinstance(z, bool) for z in wert):
        return f"{feld} [{', '.join(_zahltext(z) for z in wert)}]"
    if isinstance(wert, str) and re.fullmatch(r"[A-Za-z_]{1,20}", wert):
        return f"{feld} «{wert}»"
    return f"{feld} (gesetzt)"


def kontext_der_mappe(mappe) -> str | None:
    """Was das Sprachmodell über die Mappe wissen muss — **ohne Pfade** (Regel 3).

    Zwei Dinge, beide aus Befunden vom 01.10.2026: welche Standpunktangaben die Mappe
    schon trägt (sonst schlägt es einen Standpunkt vor, der sich mit ihr widerspricht und
    abgewiesen wird), und den bisherigen Bildauftrag (``auf-20261001-218``, Satz 1: Der
    vorgeschlagene Bildauftrag ersetzte den der Mappe ganz, «Haus am Hang» fiel weg).

    **Was eine Probe davon prüfen kann, ist nur die Übergabe** — dass es im Systemtext
    steht. Ob das Modell den Gegenstand dann behält, sagt erst eine Messung am Heim-PC.
    """
    if not isinstance(mappe, dict):
        return None
    angaben = [_angabe_fuer_das_modell(f, mappe[f]) for f in _STANDPUNKT_DER_MAPPE
               if mappe.get(f) is not None]
    zeilen = []
    if angaben:
        zeilen.append("Die Mappe trägt schon diese Standpunktangaben; sie gelten weiter, "
                      "solange dein Vorschlag sie nicht ersetzt: " + ", ".join(angaben) + ".")
        if mappe.get("innenraum"):
            zeilen.append("Weil der Standpunkt aus einem Innenraum kommt, passt eine "
                          "Brennweite, Augenhöhe oder ein Eckwinkel allein nicht dazu — nur "
                          "ein ganzer neuer Standpunkt («kamera» oder «auge» mit "
                          "«blick_auf») ersetzt ihn.")
    else:
        zeilen.append("Die Mappe trägt keine Standpunktangaben. Augenhöhe, Eckwinkel und "
                      "Kameramodus brauchen darum eine «kamera».")
    prompt = mappe.get("prompt")
    if isinstance(prompt, str) and prompt.strip():
        prompt = " ".join(prompt.split())[:BILDAUFTRAG_HOECHSTENS]
        zeilen.append(f"Bisheriger Bildauftrag der Mappe: «{prompt}». Ein neuer Bildauftrag "
                      f"ersetzt ihn ganz — behalte seinen Gegenstand und ändere nur, worum "
                      f"die Nutzerin bittet.")
    else:
        zeilen.append("Die Mappe hat noch keinen Bildauftrag.")
    return " ".join(zeilen)


def _chat(modell, nachrichten: list, frist: float, werkzeuge: list | None = None) -> dict:
    """Eine Runde — mit dem Rest der Gesamtfrist, **wenn das Sprachmodell eine kennt.**

    :class:`Ollama` nimmt ``frist``; ein Ersatz in einer Probe oder ein anderes Modell mit
    der alten Form ``chat(nachrichten, werkzeuge)`` nicht. Für die gilt die Gesamtfrist
    zwischen den Runden (in :func:`frage`), und keines wird abgewiesen, nur weil es die
    Frist nicht annimmt.
    """
    try:
        nimmt_frist = "frist" in inspect.signature(modell.chat).parameters
    except (TypeError, ValueError):
        nimmt_frist = False
    liste = WERKZEUGE if werkzeuge is None else werkzeuge
    if nimmt_frist:
        return modell.chat(nachrichten, liste, frist=frist)
    return modell.chat(nachrichten, liste)


def frage(nachricht, verlauf=(), *, sprachmodell=None, bild_rechnet: bool = False,
          bildmodell_geladen: bool = False, mappe: dict | None = None,
          werkzeuge=None, schritte=()) -> dict:
    """Eine Bitte an den Assistenten → ``{"antwort", "vorschlag"?}``. **Rechnet nie.**

    ``antwort`` ist nur, was das Modell als Antwort schrieb (``content``), nie sein
    Gedankentext. ``vorschlag`` gibt es, wenn ein Werkzeug einen gültigen Vorschlag
    machte: ``{"einstellungen", "varianten", "saetze", "rechenzeit"}`` — ``einstellungen``
    sind Felder von ``baue_kette`` (``None`` heisst: für diesen Lauf auf die Vorgabe
    zurück), ``varianten`` geht an ``/api/rechne``. Angewendet wird er mit
    :func:`anwenden`, von einem Menschen.

    Args:
        nachricht: Was die Nutzerin schrieb.
        verlauf: Frühere Beiträge, ``[{"von": "mensch"|"assistent", "text"}]``.
        sprachmodell: Vorgabe :class:`Ollama` (Adresse und Modell aus der Umgebung). In
            Proben ein Ersatz mit derselben Form.
        bild_rechnet: Rechnet gerade ein Bild? Dann wird nicht gefragt — das Modell
            würde neben dem Bildmodell geladen, und beide passen nicht auf die Karte.
        bildmodell_geladen: Liegt das Bildmodell nach einem Lauf noch auf der Karte
            (:func:`aiimaging.render.gib_grafikspeicher_frei` konnte es nicht freigeben)?
            Dann ebenso nicht.
        mappe: Die Einstellungen der Mappe. Der Standpunkt wird gegen sie geprüft (was
            der Lauf sehen wird), und das Modell erfährt, was sie schon trägt
            (:func:`kontext_der_mappe`). ``None``: Vorschlag allein, ohne Kontext.

    Alle Runden zusammen haben :data:`FRIST_FRAGE_GESAMT_S`. Läuft sie ab, kommt ein
    schon geprüfter Vorschlag mit einem Satz dazu zurück; ohne Vorschlag ein Satz
    (:class:`AssistentError`) — kein Hänger.

    **Mit** ``werkzeuge`` (Plan KI-Bedienung Stufe 5, 21.10.2026): der Assistent bedient die
    Knotenansicht mit **derselben Werkzeugliste wie Claude**, die die Mac-App mitschickt — siehe
    :func:`frage_mit_werkzeugen`. Ohne bleibt alles wie bisher (die drei Vorschlagswerkzeuge).

    Raises:
        AssistentError: mit dem Satz für den Menschen (leer, zu lang, Modell nicht
            zugelassen, Ollama lehnt ab, ein Bild rechnet, Gesamtfrist abgelaufen).
            :class:`NichtErreichbar`, wenn Ollama nicht antwortet.
    """
    if not isinstance(nachricht, str) or not nachricht.strip():
        raise AssistentError("Es fehlt die Nachricht — was soll das Bild zeigen?")
    if len(nachricht) > NACHRICHT_HOECHSTENS:
        raise AssistentError(f"Die Nachricht ist länger als {NACHRICHT_HOECHSTENS} Zeichen.")
    if werkzeuge is not None:
        return frage_mit_werkzeugen(nachricht, verlauf, werkzeuge=werkzeuge, schritte=schritte,
                                    sprachmodell=sprachmodell, bild_rechnet=bild_rechnet,
                                    bildmodell_geladen=bildmodell_geladen)
    frueher = _pruefe_verlauf(verlauf)
    if bild_rechnet:
        raise AssistentError(SATZ_BILD_RECHNET)
    if bildmodell_geladen:
        raise AssistentError(SATZ_BILDMODELL_GELADEN)
    modell = sprachmodell if sprachmodell is not None else Ollama()
    pruefe_sprachmodell(getattr(modell, "modell", None))

    # DER KONTEXT DER MAPPE IM SELBEN SYSTEMTEXT, nicht als zweite Systemnachricht: Wie
    # eine Chatvorlage eine zweite behandelt, ist je Modell verschieden.
    kontext = kontext_der_mappe(mappe)
    system = SYSTEMTEXT if kontext is None else SYSTEMTEXT + "\n\n" + kontext
    nachrichten = ([{"role": "system", "content": system}] + frueher
                   + [{"role": "user", "content": nachricht.strip()}])
    pruefer = dict(_PRUEFER)
    pruefer["standpunkt_vorschlagen"] = lambda argumente: _standpunkt(argumente, mappe)
    standpunkt = bildauftrag = varianten_teil = None
    letzte_abweisung: dict[str, str | None] = {}
    antwort = ""
    ende = time.monotonic() + FRIST_FRAGE_GESAMT_S
    abgelaufen = False
    for _ in range(RUNDEN_HOECHSTENS):
        rest = ende - time.monotonic()
        if rest <= 0:
            abgelaufen = True
            break
        try:
            botschaft = _chat(modell, nachrichten, rest)
        except ZeitUeberschritten:
            # DIE RUNDE BEKAM NUR DEN REST DER GESAMTFRIST — ihr Ablauf ist deren Ablauf.
            abgelaufen = True
            break
        if not isinstance(botschaft, dict):
            raise AssistentError("Das Sprachmodell antwortete ohne Botschaft.")
        inhalt = _ohne_denken(botschaft.get("content"))
        aufrufe = botschaft.get("tool_calls") or []
        if not isinstance(aufrufe, list):
            aufrufe = []
        antwort = inhalt or antwort
        if not aufrufe:
            break
        # ZURUECK AN DAS MODELL NUR, WAS ES SAGTE UND AUFRIEF — nie sein Denken.
        nachrichten.append({"role": "assistant", "content": inhalt,
                            "tool_calls": [{"function": a.get("function")}
                                           for a in aufrufe if isinstance(a, dict)]})
        for aufruf in aufrufe:
            name = None
            try:
                name, argumente = _lies_aufruf(aufruf)
                teil = pruefer[name](argumente)
            except _Abweisung as a:
                letzte_abweisung[name or "?"] = str(a)
                ergebnis = f"Abgewiesen: {a}"
            else:
                letzte_abweisung[name] = None
                if name == "standpunkt_vorschlagen":
                    standpunkt = teil
                elif name == "bildauftrag_vorschlagen":
                    bildauftrag = teil
                else:
                    varianten_teil = teil
                ergebnis = ("Vorschlag notiert (noch nicht gerechnet): "
                            + json.dumps(teil, ensure_ascii=False))
            nachrichten.append({"role": "tool", "tool_name": name or "?",
                                "content": ergebnis})

    if abgelaufen and not (standpunkt or bildauftrag or varianten_teil or antwort):
        raise AssistentError(SATZ_FRIST_ABGELAUFEN)
    offen = [s for s in letzte_abweisung.values() if s]
    if offen:
        antwort = (antwort + "\n\n" if antwort else "") + "Nicht übernommen: " + " ".join(offen)
    if abgelaufen:
        # WAS SCHON GEPRUEFT IST, BLEIBT — nur die Antwort dazu fehlt. Gesagt wird es,
        # damit ein knapper Satz nicht wie die ganze Antwort aussieht.
        antwort = ((antwort + "\n\n" if antwort else "")
                   + f"Die Frist von {FRIST_FRAGE_GESAMT_S:.0f} s ist abgelaufen; was bis "
                     f"dahin vorgeschlagen war, steht hier, mehr kam nicht.")
    ergebnis: dict = {}
    if standpunkt or bildauftrag or varianten_teil:
        e = {**(standpunkt or {}), **(bildauftrag or {})}
        anzahl = None
        if varianten_teil:
            anzahl = varianten_teil["varianten"]
            if "seed" in varianten_teil:
                e["seed"] = varianten_teil["seed"]
        ergebnis["vorschlag"] = _vorschlag(e, anzahl)
        if not antwort:
            antwort = "Mein Vorschlag steht darunter — gerechnet wird erst mit «Anwenden»."
    elif not antwort:
        antwort = "Dazu habe ich keinen Vorschlag."
    return {"antwort": antwort, **ergebnis}


# ============================================== mit der Werkzeugliste der Knotenansicht

#: **Stufe 5 des Plans «KI-Bedienung»** (``docs/PLAN_KI_BEDIENUNG_2026-10-20.md``, 21.10.2026):
#: Der Assistent bekommt dieselbe Werkzeugliste wie Claude über MCP — die Werkzeuge der
#: Knotenansicht (``vis_*``, ``graph_lesen``, ``vis_paket``), Blick und Maus, die der Mac-App. Die
#: Liste schickt die Mac-App mit (sie hält sie, wie für Claude); die **Schleife** steht hier:
#: Das Modell ruft Werkzeuge, dieser Kern prüft die Aufrufe und gibt sie als ``schritte_offen``
#: zurück; die Mac-App führt sie in der Knotenansicht aus (als Urheber «assistent» — dort gilt
#: dieselbe Regel wie für Claude: Karte, Coop oder Voll; Löschen und Rendern immer Karte; die
#: Grafikkarte gibt nie eine KI frei) und fragt mit den Ergebnissen (``schritte``) weiter.
#:
#: *Warum die Schleife nicht ganz hier läuft:* Die Werkzeuge wirken in der Knotenansicht am Mac,
#: nicht am Heim-PC. Jede Anfrage ist darum **eine** Runde des Modells; was es bisher tat, kommt
#: mit der nächsten Anfrage zurück. Die Grenzen (wie viele Schritte, wie lang ein Ergebnis) gelten
#: hier, an einer Stelle — die Mac-App zählt nicht nach.

#: So viele Werkzeuge nimmt eine Liste höchstens — **gesetzt** (heute rund 25).
WERKZEUGE_HOECHSTENS = 64
#: So gross darf die Liste als JSON sein — **gesetzt**: Sie geht bei jeder Runde ans Modell.
WERKZEUGLISTE_ZEICHEN_HOECHSTENS = 120_000
#: So viele Werkzeugschritte darf eine Frage machen — **gesetzt**. Danach antwortet das Modell
#: ohne Werkzeuge (es bekommt keine mehr angeboten) und sagt, was es tat.
SCHRITTE_HOECHSTENS = 12
#: So lang darf das Ergebnis eines Schritts sein, das ans Modell geht — **gesetzt**; länger wird
#: gekürzt (``graph_lesen`` eines grossen Graphen ist lang, das Kontextfenster nicht).
ERGEBNIS_HOECHSTENS = 6000
#: So lang darf eine Beschreibung sein.
BESCHREIBUNG_HOECHSTENS = 4000

_WERKZEUGNAME = re.compile(r"[A-Za-z0-9_-]{1,64}")
#: **Nie ein Werkzeug des Assistenten**, auch wenn eine Liste es nennte: was freigibt. Die
#: Grafikkarte gibt ein Mensch am Render-Knoten frei (Entscheid 106b); die Liste der Mac-App hat
#: kein solches Werkzeug — diese Wache hält es auch für eine falsche Liste fest.
_NIE_ALS_WERKZEUG = re.compile(r"freig|approv|gpu", re.I)

#: **Geschärft nach dem Messauftrag 305** (21.10.2026, Befunde B3–B6): Das Modell riet die Kennung
#: eines neuen Knotens, erfand eine Stimmung, sagte bei «Gib die Grafikkarte frei» nicht, wer
#: freigibt, und meldete «gelöscht», wo nur eine Karte lag. Der Satz bittet um alles vier — und
#: weil eine Bitte an ein 14-B-Modell keine Gewähr ist, prüft der Kern dieselben vier Punkte
#: selbst (:func:`_pruefe_angaben`, :func:`_berichtige_antwort`). **Der Systemsatz lebt nur hier**;
#: die Mac-App (``Assistentengespraech``) führt die Gesprächsregeln (eine Karte, Längen), nicht
#: den Satz an das Modell.
#:
#: **Ohne wörtliches Beispiel seit auf-20261021-319** (B1): Der Satz nannte als Beispiel
#: «Das Löschen ist als Karte A-1 vorgeschlagen», und qwen3:14b schrieb ihn in F1 (Stimmung),
#: F2 (Rendern) und F3 (Freigeben) als Schlussantwort ab, obwohl nichts gelöscht wurde. Ein
#: kleines Modell kopiert Beispielsätze; die Regel steht darum ohne Beispiel, und der Kern
#: verwirft einen Satz, der eine fremde Karte oder ein Löschen ohne Löschschritt nennt
#: (:func:`_ohne_fremde_karten`). Ebenso weg: «verbinde ihn in der nächsten Runde» — ein neuer
#: Knoten, der nur als Karte vorliegt, hat auch dort keine Kennung (319 B2); verbunden wird im
#: Paket.
SYSTEMTEXT_KNOTEN = (
    "Du bist der Assistent der Bild-App Visbox für Architektinnen und Architekten. Du bedienst "
    "die Knotenansicht, in der aus einem 3D-Modell über Knoten (Modell, Kamera, Stimmung, "
    "Render) ein Bild entsteht — mit denselben Werkzeugen wie Claude. "
    "Kennungen (graphId, nodeId, from, to, edgeId) rätst du nie: Lies zuerst den Graph "
    "(graph_lesen) und nimm nur Kennungen, die in einem Ergebnis stehen. Soll ein neuer Knoten "
    "verbunden werden, lege Knoten und Verbindung zusammen in EINEM vis_paket an («$neu:0» ist "
    "der neue Knoten) — einzeln geht es nicht: Ein neuer Knoten hat noch keine Kennung, auch "
    "nicht in der nächsten Runde, solange er nur als Karte vorliegt. Antwortet ein Werkzeug mit "
    "«VORSCHLAG … liegt als Karte», ist die Kennung darin die Kennung der KARTE, nicht eines "
    "Knotens: Nimm sie nie als from, to oder nodeId. Arbeite im bestehenden Graph aus graph_lesen; einen neuen "
    "Graph (vis_graphErstellen) legst du nur an, wenn ausdrücklich darum gebeten wird oder "
    "graph_lesen keinen findet. "
    "Erfinde nichts, was weder die Nutzerin sagte noch im Graph steht: keine Stimmung, keine "
    "Auflösung, keine Güte, keine Kamera. Fehlt eine Angabe, lass sie weg — dann gilt, was am "
    "Knoten steht. Tu nur, worum gebeten wurde. "
    "Löschen und Rendern sind immer eine Karte. Antwortet ein Werkzeug mit «VORSCHLAG … liegt "
    "als Karte», ist das richtig so — schlage dasselbe nicht noch einmal vor, und nenne es "
    "danach «vorgeschlagen», nie «gelöscht», «geändert» oder «gerechnet» — auch nicht mit der Karte "
    "im selben Satz. Nenne dabei nur, was ein Werkzeug in diesem Gespräch wirklich als Karte "
    "gemeldet hat: dessen Handlung und dessen Kartenkennung, keine andere. Ausgeführt ist es "
    "erst, wenn der Architekt die Karte anwendet. "
    "Wird um ein Bild gebeten («Rechne», «Render», «mach ein Bild»), stelle den Auftrag mit "
    "vis_render am Render-Knoten aus dem Graph — nur mit den Angaben, die genannt wurden. Das ist "
    "kein Freigeben und erlaubt: der Auftrag wird eine Karte. "
    "Freigeben kann nur der Architekt, am Render-Knoten mit «Freigeben» — du nicht, und kein "
    "Werkzeug kann es. Nur wenn nach dem Freigeben oder der Grafikkarte gefragt wird, sage: "
    "«Freigeben kann nur der Architekt.» "
    "Behaupte nie, ein Bild sei gerechnet oder geprüft. Antwortet ein Werkzeug mit «FEHLER» "
    "oder «VERWEIGERT», korrigiere den Aufruf oder sage kurz, warum es nicht geht; beginne deine "
    "Antwort selbst nie mit «FEHLER». Antworte am Ende in ein bis drei kurzen Sätzen auf "
    "Deutsch, in Schweizer Schreibung (ss statt ß), und sage, was du getan oder vorgeschlagen "
    "hast.")

#: Die Felder, in denen ein Werkzeug der Knotenansicht eine **Kennung** nimmt (Befund B6).
KENNUNG_FELDER = ("graphId", "nodeId", "from", "to", "edgeId")
#: Diese Werkzeuge nehmen keine bestehende Kennung (lesen, schauen, neu anlegen) oder prüfen sie
#: selbst Schritt für Schritt (``vis_paket``).
_OHNE_KENNUNGSPRUEFUNG = frozenset({"graph_lesen", "vis_graphErstellen", "visbox_blick",
                                    "visbox_maus", "vis_paket"})
#: Die freien Angaben am Render-Knoten, die das Modell nicht erfinden darf (Befund B4): steht der
#: Wert weder in der Frage noch im Verlauf noch in einem Ergebnis, wird der Aufruf abgewiesen.
ERFUNDEN_FELDER = {"vis_render": ("stimmungPreset", "backbone", "guete", "aufloesung",
                                  "kameraWahl", "seed", "grundlage")}
#: Wer bittet, die Grafikkarte freizugeben, hört diesen Satz — vom Kern, nicht vom Modell (B3).
SATZ_NUR_ARCHITEKT = "Freigeben kann nur der Architekt, am Render-Knoten mit «Freigeben» — ich nicht."
_FRAGE_NACH_FREIGABE = re.compile(r"frei\s?geb|freigab|\bgib\b.*\bfrei\b|grafikkarte|\bgpu\b", re.I)
_KARTE = re.compile(r"^VORSCHLAG\s+(\S+)\s+liegt als Karte")
#: Eine Kartenkennung in einem beliebigen Ergebnis (auch mitten im Text, auch in einem Paket).
_KARTE_IRGENDWO = re.compile(r"VORSCHLAG\s+([A-Za-z]+-\d+)\b[.:,]?\s+liegt als Karte")
#: Dieselbe Karte samt dem, was sie vorschlägt («… beim Architekten: Knoten «Modell» löschen.»).
_KARTE_MIT_WAS = re.compile(
    r"VORSCHLAG\s+([A-Za-z]+-\d+)\b[.:,]?\s+liegt als Karte[^:.]*(?::\s*([^.]{1,160}))?")
#: Wer ausdrücklich um einen NEUEN Graph bittet (auf-20261021-314, B3 F1): Nur dann, oder wenn
#: graph_lesen keinen fand, geht vis_graphErstellen durch.
_FRAGE_NACH_NEUEM_GRAPH = re.compile(
    r"\b(?:neu|weiter|zweit|eigen|separat|leer)\w*\s+(?:\w+[\s-]+)?(?:render-?)?"
    r"(?:graph|node-tree|knotenbaum)"
    r"|\b(?:graph|node-tree|knotenbaum)\w*\s+(?:\w+\s+){0,2}(?:anlegen|erstell\w*)\b"
    r"|\b(?:leg|erstell)\w*\s+(?:einen|ein)\s+(?:\w+\s+)?(?:graph|node-tree|knotenbaum)\w*\b", re.I)
_KEIN_GRAPH = "Kein Render-Graph im Projekt"
#: Was ein Schritt eines Pakets neu anlegt — worauf «$neu:N» darum zeigen darf.
_NEU_ART = {"vis_graphErstellen": "graph", "vis_nodeSetzen": "knoten", "vis_verbinden": "kante"}
_FELD_ART = {"graphId": "graph", "nodeId": "knoten", "from": "knoten", "to": "knoten", "edgeId": "kante"}
_NEU_VERWEIS = re.compile(r"^\$neu:(\d+)$")
#: Angehängt an jedes Ergebnis, das nur eine Karte meldet, bevor es ans Modell geht (B3 F4).
SATZ_KARTE_NICHT_GETAN = ("(Hinweis des Kerns: noch NICHT ausgeführt — nenne es «vorgeschlagen», "
                          "nicht «gelöscht», «geändert» oder «gerechnet».)")
#: Wer um ein Bild bittet (auf-20261021-310, B2): «Rechne jetzt das Bild.» rief kein Werkzeug.
_FRAGE_NACH_BILD = re.compile(
    r"\brechne\w*|\brender(?:e|n|st)?\b(?![-\w])|\bbilder?\b(?![-\w])", re.I)
#: Der Anstoss, wenn das Modell bei einer Bitte um ein Bild kein Werkzeug ruft (B2) — einmal je
#: Anfrage. Er verlangt nichts Erfundenes: die Prüfung der Angaben gilt weiter.
SATZ_BILD_ANSTOSS = (
    "Gebeten wurde um ein Bild. Stelle den Auftrag mit vis_render am Render-Knoten (Kennungen "
    "aus graph_lesen; ist der Graph noch nicht gelesen, lies ihn zuerst) — nur mit genannten "
    "Angaben, sonst ohne. Das ist kein Freigeben: Der Auftrag wird eine Karte, freigeben kann "
    "nur der Architekt.")
#: Ein Satz, der eine Handlung als **getan** meldet (Befund B5).
_GETAN = re.compile(
    r"\b(wurde|wurden|ist|sind|habe|hat|haben)\b[^.!?]*?\b(gelöscht|entfernt|gerechnet|"
    r"gerendert|geändert|angelegt|verbunden|angeschlossen|erstellt|gesetzt|hinzugefügt|"
    r"verschoben|getrennt|eingestellt)\b", re.I)
_NUR_LESEN = frozenset({"graph_lesen", "visbox_blick"})


def _kommt_vor(wert: str, text: str) -> bool:
    return re.search(r"(?<![A-Za-z0-9_-])" + re.escape(wert) + r"(?![A-Za-z0-9_-])", text) is not None


def _karten_in(getan) -> set[str]:
    """Die Kennungen der Karten, die die Schritte dieser Frage gemeldet haben («A-1», …)."""
    return {m.group(1) for s in getan or () for m in _KARTE_IRGENDWO.finditer(str(s.get("ergebnis", "")))}


def _neuer_graph_erlaubt(nachricht: str, getan) -> bool:
    """Darf ``vis_graphErstellen`` hinaus? Nur auf ausdrückliche Bitte, oder wenn graph_lesen
    keinen Graph fand (auf-20261021-314, B3 F1: «Leg eine Stimmung an und verbinde sie mit dem
    Render-Knoten» baute einen neuen Graph «Stimmung Abend», statt n2 in g1 zu erreichen)."""
    if _FRAGE_NACH_NEUEM_GRAPH.search(nachricht or ""):
        return True
    return any(sch.get("werkzeug") == "graph_lesen" and _KEIN_GRAPH in str(sch.get("ergebnis", ""))
               for sch in getan or ())


#: Wer einen neuen Knoten setzt und ihn in derselben Runde einzeln verbinden will (319 B2).
SATZ_GLEICH_VERBINDEN = (
    "Ein neuer Knoten und seine Verbindung gehen nur zusammen: Lege beides in EINEM vis_paket an "
    "— Schritt 0 vis_nodeSetzen, Schritt 1 vis_verbinden mit «$neu:0» als from oder to und dem "
    "bestehenden Knoten aus graph_lesen auf der anderen Seite. Einzeln hat der neue Knoten noch "
    "keine Kennung.")


SATZ_KEIN_NEUER_GRAPH = (
    "Gebeten wurde nicht um einen neuen Graph. Lies den bestehenden mit graph_lesen und arbeite "
    "dort (graphId und den Render-Knoten aus dem Ergebnis); soll ein neuer Knoten gleich "
    "verbunden werden, lege beides in einem vis_paket an («$neu:0»).")


def _pruefe_paket(argumente: dict, bekannt: str, karten, neuer_graph_erlaubt: bool) -> str | None:
    """Die Schritte eines ``vis_paket`` wie Einzelaufrufe prüfen (auf-20261021-314, B3 F1).

    Bis dahin ging ein Paket ungeprüft hinaus: «$neu:0» als graphId zeigte auf einen
    neuen Knoten, «$neu:1» als to auf den Verbinde-Schritt selbst. «$neu:N» muss auf einen
    FRÜHEREN Schritt zeigen, der das Passende neu anlegt (Graph, Knoten, Kante); jede andere
    Kennung muss bekannt sein wie bei einem Einzelaufruf.
    """
    schritte = argumente.get("schritte")
    if not isinstance(schritte, list) or not schritte:
        return None                      # die Form prüft die Knotenansicht (Probelauf)
    for nr, sch in enumerate(schritte):
        if not isinstance(sch, dict):
            continue
        befehl, args = sch.get("befehl"), sch.get("argumente") or {}
        if not isinstance(args, dict):
            continue
        if befehl == "vis_graphErstellen" and not neuer_graph_erlaubt:
            return f"Schritt {nr} (vis_graphErstellen): {SATZ_KEIN_NEUER_GRAPH}"
        roh = {}
        for feld in KENNUNG_FELDER:
            wert = args.get(feld)
            treffer = _NEU_VERWEIS.match(wert.strip()) if isinstance(wert, str) else None
            if treffer is None:
                if wert is not None:
                    roh[feld] = wert
                continue
            ziel = int(treffer.group(1))
            art = _NEU_ART.get((schritte[ziel] or {}).get("befehl")) \
                if ziel < nr and isinstance(schritte[ziel], dict) else None
            if art != _FELD_ART[feld]:
                was = {"graph": "einen neuen Graph", "knoten": "einen neuen Knoten",
                       "kante": "eine neue Kante"}[_FELD_ART[feld]]
                return (f"Schritt {nr} ({befehl}): «{wert}» als {feld} muss auf einen früheren "
                        f"Schritt zeigen, der {was} anlegt — Schritt {ziel} tut das nicht. "
                        f"Die graphId des bestehenden Graphs steht im Ergebnis von graph_lesen.")
        if befehl not in _OHNE_KENNUNGSPRUEFUNG and isinstance(befehl, str):
            grund = _pruefe_angaben(befehl, roh, bekannt, karten)
            if grund is not None:
                return f"Schritt {nr} ({befehl}): {grund}"
    return None


def _pruefe_angaben(name: str, argumente: dict, bekannt: str,
                    karten: frozenset | set = frozenset()) -> str | None:
    """Ein Grund zum Abweisen, wenn der Aufruf eine Kennung rät oder eine Angabe erfindet.

    ``bekannt`` ist, was das Modell wissen **kann**: die Frage, der Verlauf und die Ergebnisse der
    Schritte dieser Frage. Eine Kennung, die dort nicht steht, ist geraten (B6); eine Stimmung,
    die dort nicht steht, erfunden (B4). Das Modell bekommt den Grund und darf korrigieren.
    """
    if name not in _OHNE_KENNUNGSPRUEFUNG:
        # EINE KARTE IST KEIN KNOTEN (auf-20261021-310, B1): «A-1» stand im Ergebnis von
        # vis_nodeSetzen und galt darum als bekannt — vis_verbinden {from: 'A-1'} ging durch.
        for feld in KENNUNG_FELDER:
            wert = argumente.get(feld)
            if isinstance(wert, str) and wert.strip() in karten:
                return (f"«{wert.strip()}» ({feld}) ist die Kennung einer KARTE (eines Vorschlags), "
                        f"nicht eines Knotens — den Knoten gibt es erst, wenn der Architekt die "
                        f"Karte anwendet. Verbinde nur Knoten aus graph_lesen; soll ein neuer "
                        f"Knoten gleich verbunden werden, lege beides in einem vis_paket an "
                        f"(«$neu:0»).")
        for feld in KENNUNG_FELDER:
            wert = argumente.get(feld)
            if (isinstance(wert, (str, int)) and not isinstance(wert, bool) and str(wert).strip()
                    and not _kommt_vor(str(wert).strip(), bekannt)):
                return (f"Die Kennung «{wert}» ({feld}) steht in keinem Ergebnis dieser Frage. "
                        f"Kennungen nie raten: lies sie mit graph_lesen (einen neuen Knoten aus "
                        f"dem Ergebnis von vis_nodeSetzen) und rufe dann erneut.")
    for feld in ERFUNDEN_FELDER.get(name, ()):
        if feld not in argumente:
            continue
        wert = argumente[feld]
        for teil in (wert if isinstance(wert, list) else [wert]):
            if (isinstance(teil, (str, int, float)) and not isinstance(teil, bool) and str(teil).strip()
                    and not _kommt_vor(str(teil).strip().lower(), bekannt.lower())):
                return (f"Die Angabe «{feld}: {json.dumps(wert, ensure_ascii=False)}» nannte "
                        f"niemand und sie steht nicht im Graph. Nichts erfinden: lass «{feld}» "
                        f"weg — dann gilt, was am Knoten steht.")
    return None


_SCHEMA_TYPEN = {
    "string": lambda w: isinstance(w, str),
    "integer": lambda w: isinstance(w, int) and not isinstance(w, bool),
    "number": lambda w: (isinstance(w, (int, float)) and not isinstance(w, bool)
                         and math.isfinite(float(w))),
    "boolean": lambda w: isinstance(w, bool),
    "array": lambda w: isinstance(w, list),
    "object": lambda w: isinstance(w, dict),
}


#: Die grösste Kantenlänge einer bestellten Auflösung — DIESELBE wie
#: :data:`aiimaging.kosmo_szene.KANTE_HOECHSTENS` (Blender: 4 bis 65'536). Hier abgeschrieben,
#: weil der Assistent nur wenige Module einbinden darf (``tests/test_assistent.py``); eine Probe
#: in ``tests/test_nach320.py`` hält beide gleich.
KANTE_HOECHSTENS = 1 << 16


def _passt_zum_schema(wert, schema, *, feld: str = "") -> str | None:
    """Ein Grund, wenn ``wert`` nicht zu den erlaubten Werten des Schemas passt — sonst ``None``.

    **Warum (auf-20261021-320, B2):** ``aufloesung`` wurde nur darauf geprüft, ob jemand die
    Zahlen nannte — nie, ob sie erlaubt sind. Geprüft wird, was die Liste der Knotenansicht
    selbst sagt (Typ, ``enum``, Grenzen, Länge einer Liste, ihre Glieder), bei ``aufloesung``
    dazu die eine Kantenregel des Kerns (:data:`KANTE_HOECHSTENS`).
    """
    if not isinstance(schema, dict):
        return None
    typ = schema.get("type")
    typen = typ if isinstance(typ, list) else ([typ] if isinstance(typ, str) else [])
    if typen and not any(_SCHEMA_TYPEN.get(t, lambda _w: True)(wert) for t in typen):
        return f"«{feld}» ist kein {' oder '.join(typen)}"
    if "enum" in schema and isinstance(schema["enum"], list) and wert not in schema["enum"]:
        return f"«{feld}» ist keiner der erlaubten Werte ({', '.join(map(str, schema['enum']))})"
    if isinstance(wert, (int, float)) and not isinstance(wert, bool):
        for schluessel, verletzt in (("minimum", lambda g: wert < g),
                                     ("maximum", lambda g: wert > g),
                                     ("exclusiveMinimum", lambda g: wert <= g),
                                     ("exclusiveMaximum", lambda g: wert >= g)):
            grenze = schema.get(schluessel)
            if isinstance(grenze, (int, float)) and not isinstance(grenze, bool) and verletzt(grenze):
                return f"«{feld}» verletzt {schluessel} {grenze}"
        if feld.startswith("aufloesung") and wert > KANTE_HOECHSTENS:
            return f"«{feld}» ist grösser als {KANTE_HOECHSTENS} Bildpunkte"
    if isinstance(wert, list):
        if isinstance(schema.get("minItems"), int) and len(wert) < schema["minItems"]:
            return f"«{feld}» hat weniger als {schema['minItems']} Werte"
        if isinstance(schema.get("maxItems"), int) and len(wert) > schema["maxItems"]:
            return f"«{feld}» hat mehr als {schema['maxItems']} Werte"
        for nr, teil in enumerate(wert):
            grund = _passt_zum_schema(teil, schema.get("items"), feld=f"{feld}[{nr}]")
            if grund is not None:
                return grund
    return None


def _ohne_erfundenes(name: str, argumente: dict, bekannt: str,
                     schema: dict | None) -> tuple[dict, list[str]]:
    """Die freien Angaben am Render-Knoten, die niemand nannte oder die nicht erlaubt sind,
    WEGLASSEN statt den Aufruf abzuweisen — ``(argumente ohne sie, [weggelassen])``.

    **Warum (auf-20261021-320, B1):** Die Beschreibung von ``vis_render`` zählt Stimmung,
    Backbone, Güte und Auflösung samt ihren erlaubten Werten auf, und qwen3:14b füllte sie aus
    (F2: ``backbone 'qwen'``, ``guete 'voll'``, ``aufloesung [1024, 768]``; F3 dazu
    ``stimmungPreset 'morgen'``). Der Kern wies je Aufruf EINE ab, das Modell strich je Runde
    eine, und nach drei inneren Runden endete die Frage ohne Karte («Dazu fand ich kein
    passendes Werkzeug»). In 319 war dort noch eine Karte entstanden.

    **Warum Weglassen sicher ist:** Die Felder sind im Schema frei (nicht ``required``); ohne
    sie gilt, was am Knoten steht — derselbe Satz, den die Abweisung dem Modell sagte. Der
    Auftrag wird ohnehin eine Karte, die der Architekt sieht, bevor etwas rechnet. Kennungen
    (``graphId``, ``nodeId``) werden NICHT weggelassen: eine geratene Kennung bleibt ein Grund
    zum Abweisen (:func:`_pruefe_angaben`).
    """
    felder = ERFUNDEN_FELDER.get(name, ())
    if not felder or not isinstance(argumente, dict):
        return argumente, []
    eigenschaften = (schema or {}).get("properties") if isinstance(schema, dict) else None
    eigenschaften = eigenschaften if isinstance(eigenschaften, dict) else {}
    neu, weg = dict(argumente), []
    for feld in felder:
        if feld not in neu:
            continue
        wert = neu[feld]
        if wert is None:
            del neu[feld]
            continue
        text = json.dumps(wert, ensure_ascii=False)
        grund = _passt_zum_schema(wert, eigenschaften.get(feld), feld=feld)
        if grund is None:
            for teil in (wert if isinstance(wert, list) else [wert]):
                if (isinstance(teil, (str, int, float)) and not isinstance(teil, bool)
                        and str(teil).strip()
                        and not _kommt_vor(str(teil).strip().lower(), bekannt.lower())):
                    grund = "nannte niemand"
                    break
        else:
            grund = "nicht erlaubt"
        if grund is not None:
            del neu[feld]
            weg.append(f"{feld} {text} ({grund})")
    return neu, weg


def _paket_ohne_erfundenes(argumente: dict, bekannt: str,
                           schemas: dict) -> tuple[dict, list[str]]:
    """Dasselbe für die Schritte eines ``vis_paket`` (ein Render-Schritt im Paket)."""
    schritte = argumente.get("schritte") if isinstance(argumente, dict) else None
    if not isinstance(schritte, list):
        return argumente, []
    neu_schritte, weg = [], []
    for sch in schritte:
        if (isinstance(sch, dict) and sch.get("befehl") in ERFUNDEN_FELDER
                and isinstance(sch.get("argumente"), dict)):
            neu_args, w = _ohne_erfundenes(sch["befehl"], sch["argumente"], bekannt,
                                           schemas.get(sch["befehl"]))
            if w:
                sch = dict(sch, argumente=neu_args)
                weg.extend(w)
        neu_schritte.append(sch)
    return (dict(argumente, schritte=neu_schritte) if weg else argumente), weg


#: Wie der Nutzer eine Angabe am Render-Knoten AUSDRÜCKLICH nennt (auf-20261021-321, B1). Nur
#: eindeutiger Wortlaut: die Stimmung mit dem Wort «Stimmung» davor oder als «Abendstimmung»,
#: die Güte mit dem Wort «Güte» daneben (bloss «Vorschau» gilt auch — es heisst nichts anderes),
#: die Auflösung als «1920 x 1080». Ein Wert zählt nur, wenn er im Schema erlaubt ist.
_AUFLOESUNG_GENANNT = re.compile(
    r"(?<!\d)(?<!\d[.,])(\d{2,5})\s*(?:x|×|\*|mal)\s*(\d{2,5})(?!\d|[.,]\d)", re.I)
_GUETE_WORT = r"(?:güte|guete|qualität|qualitaet)"
_GUETE_ALLEIN = frozenset({"vorschau"})


def _genannt_in_der_frage(nachricht: str, schema: dict | None) -> dict:
    """Die freien Angaben an ``vis_render``, die die Frage selbst eindeutig nennt — ``{feld: wert}``.

    **Warum (auf-20261021-321, B1):** «Rechne eine Vorschau mit Stimmung abend in 1920 x 1080.»
    — qwen3:14b übernahm Stimmung und Auflösung, liess die Güte aber fallen; der Kern ergänzte
    nichts (er liess nur weg). Was der Architekt ausdrücklich sagt und erlaubt ist, gehört auf die
    Karte. Mehrdeutiges (zwei Stimmungen, zwei Auflösungen) wird NICHT ergänzt.
    """
    text = nachricht or ""
    eigenschaften = (schema or {}).get("properties") if isinstance(schema, dict) else None
    eigenschaften = eigenschaften if isinstance(eigenschaften, dict) else {}
    aus: dict = {}

    def erlaubt(feld):
        werte = (eigenschaften.get(feld) or {}).get("enum")
        return [w for w in werte if isinstance(w, str)] if isinstance(werte, list) else []

    stimmungen = {w for w in erlaubt("stimmungPreset")
                  if re.search(r"\bstimmung\w*\s+[«\"'„]?" + re.escape(w) + r"\b", text, re.I)
                  or re.search(r"\b" + re.escape(w) + r"stimmung\b", text, re.I)}
    if len(stimmungen) == 1:
        aus["stimmungPreset"] = stimmungen.pop()
    gueten = {w for w in erlaubt("guete")
              if re.search(_GUETE_WORT + r"\s*[:=]?\s*[«\"'„]?" + re.escape(w) + r"\b", text, re.I)
              or re.search(r"\b" + re.escape(w) + r"\w*\s+" + _GUETE_WORT, text, re.I)
              or (w in _GUETE_ALLEIN and re.search(r"\b" + re.escape(w) + r"\b", text, re.I))}
    if len(gueten) == 1:
        aus["guete"] = gueten.pop()
    if "aufloesung" in eigenschaften:
        paare = {(int(a), int(b)) for a, b in _AUFLOESUNG_GENANNT.findall(text)}
        if len(paare) == 1:
            aus["aufloesung"] = list(paare.pop())
    return {f: w for f, w in aus.items()
            if _passt_zum_schema(w, eigenschaften.get(f), feld=f) is None}


def _ergaenze_aus_der_frage(name: str, argumente: dict, nachricht: str,
                            schema: dict | None) -> tuple[dict, list[str]]:
    """Was die Frage eindeutig nennt und der Aufruf nicht trägt, kommt dazu (321 B1).

    Nur an ``vis_render`` und nur, wo das Feld FEHLT — einen Wert, den das Modell gesetzt hat
    und der genannt ist, ersetzt der Kern nicht.
    """
    if name != "vis_render" or not isinstance(argumente, dict):
        return argumente, []
    neu, dazu = dict(argumente), []
    for feld, wert in _genannt_in_der_frage(nachricht, schema).items():
        if feld not in neu:
            neu[feld] = wert
            dazu.append(f"{feld} {json.dumps(wert, ensure_ascii=False)}")
    return neu, dazu


#: Wer ausdrücklich einen Knoten will — dann bleibt der Stimmungs-Knoten neben dem Preset (321 B1).
_FRAGE_NACH_KNOTEN = re.compile(r"knoten|\bnode|\bleg\w*\b|anleg|\bsetz|verbind", re.I)


def _ohne_doppelte_stimmung(argumente: dict, nachricht: str) -> tuple[dict, list[str]]:
    """Im ``vis_paket`` keinen neuen Stimmungs-Knoten neben einem Render-Schritt mit derselben
    Stimmung (``stimmungPreset``) — ``(argumente, [weggelassen])``.

    **Warum (auf-20261021-321, B1):** Auf «Rechne eine Vorschau mit Stimmung abend …» legte das
    Modell im selben Paket einen Stimmungs-Knoten «abend» an, verband ihn mit dem Render-Knoten
    UND setzte ``stimmungPreset 'abend'`` am Auftrag. Doppelt: Der Auftrag trägt die Stimmung
    schon, und der Knoten ändert den Graph, worum niemand bat. Der Knoten und seine Verbindung
    fallen weg; die Verweise «$neu:N» der übrigen Schritte werden nachgezählt. Bat die Frage
    ausdrücklich um einen Knoten («leg … an», «verbinde»), bleibt alles, wie es ist; zeigt ein
    anderer Schritt auf den Knoten, ebenso.
    """
    schritte = argumente.get("schritte") if isinstance(argumente, dict) else None
    if not isinstance(schritte, list) or _FRAGE_NACH_KNOTEN.search(nachricht or ""):
        return argumente, []
    presets = {(sch.get("argumente") or {}).get("stimmungPreset") for sch in schritte
               if isinstance(sch, dict) and sch.get("befehl") == "vis_render"
               and isinstance(sch.get("argumente"), dict)}
    presets.discard(None)
    if not presets:
        return argumente, []

    def verweise(sch) -> set[int]:
        args = sch.get("argumente") if isinstance(sch, dict) else None
        return {int(m.group(1)) for wert in (args or {}).values() if isinstance(wert, str)
                for m in [_NEU_VERWEIS.match(wert.strip())] if m}

    weg: set[int] = set()
    for nr, sch in enumerate(schritte):
        args = sch.get("argumente") if isinstance(sch, dict) else None
        if (not isinstance(args, dict) or sch.get("befehl") != "vis_nodeSetzen"
                or args.get("typ") != "stimmung"
                or (args.get("params") or {}).get("preset") not in presets):
            continue
        nutzer = [k for k, s in enumerate(schritte) if nr in verweise(s)]
        if all(isinstance(schritte[k], dict) and schritte[k].get("befehl") == "vis_verbinden"
               and verweise(schritte[k]) == {nr} for k in nutzer):
            weg.update([nr, *nutzer])
    if not weg or any(verweise(sch) & weg for nr, sch in enumerate(schritte) if nr not in weg):
        return argumente, []

    def nachgezaehlt(sch):
        args = sch.get("argumente")
        if not isinstance(args, dict):
            return sch
        neu = {}
        for feld, wert in args.items():
            m = _NEU_VERWEIS.match(wert.strip()) if isinstance(wert, str) else None
            if m:
                alt = int(m.group(1))
                wert = f"$neu:{alt - sum(1 for k in weg if k < alt)}"
            neu[feld] = wert
        return dict(sch, argumente=neu)

    bleibt = [nachgezaehlt(sch) for nr, sch in enumerate(schritte) if nr not in weg]
    if not bleibt:
        return argumente, []
    presets_weg = sorted({(schritte[k]["argumente"].get("params") or {}).get("preset")
                          for k in weg if schritte[k].get("befehl") == "vis_nodeSetzen"})
    return dict(argumente, schritte=bleibt), [
        f"kein zusätzlicher Stimmungs-Knoten «{p}» — der Render-Auftrag trägt die Stimmung schon"
        for p in presets_weg]


def _paket_ergaenzt(argumente: dict, nachricht: str, schemas: dict) -> tuple[dict, list[str]]:
    """:func:`_ergaenze_aus_der_frage` für die Render-Schritte eines ``vis_paket``."""
    schritte = argumente.get("schritte") if isinstance(argumente, dict) else None
    if not isinstance(schritte, list):
        return argumente, []
    neu_schritte, dazu = [], []
    for sch in schritte:
        if isinstance(sch, dict) and sch.get("befehl") == "vis_render":
            neu_args, d = _ergaenze_aus_der_frage("vis_render", sch.get("argumente"), nachricht,
                                                  schemas.get("vis_render"))
            if d:
                sch = dict(sch, argumente=neu_args)
                dazu.extend(d)
        neu_schritte.append(sch)
    return (dict(argumente, schritte=neu_schritte) if dazu else argumente), dazu


#: Die Werkzeuge der Knotenansicht in der Sprache des Architekten (auf-20261021-322, B1/B2): Ein
#: Werkzeugname wie ``vis_render`` ist ein Wort für das Modell, nicht für den Menschen am Gerät.
ALLTAGSWORT = {
    "graph_lesen": "Graph lesen", "vis_graphErstellen": "Neuer Graph",
    "vis_nodeSetzen": "Knoten setzen", "vis_nodeParametrieren": "Knoten einstellen",
    "vis_nodeSchieben": "Knoten schieben", "vis_verbinden": "Verbinden", "vis_trennen": "Trennen",
    "vis_nodeLoeschen": "Knoten löschen", "vis_nodeKollabieren": "Knoten einklappen",
    "vis_graphLoeschen": "Graph löschen", "vis_render": "Rendern", "vis_varianten": "Varianten",
    "vis_paket": "Paket", "visbox_blick": "Blick", "visbox_maus": "Maus",
}
_WERKZEUGNAME_IM_TEXT = re.compile(r"[`'\"«]?\b(vis_[A-Za-z]+|graph_lesen|visbox_[A-Za-z]+)\b[`'\"»]?")
#: «die Architektin» neben «der Architekt» (322 B4): Die Sätze des Kerns sagen «der Architekt»;
#: die Antwort bleibt dabei. Die Fälle in der Reihenfolge der Prüfung — erst nach Präposition mit
#: Akkusativ, dann Nominativ, Dativ, unbestimmt, zuletzt das blosse Wort. Die Mehrzahl
#: («Architektinnen und Architekten») bleibt stehen.
_ARCHITEKTIN = (
    # «Nutzerin»/«Nutzer» meint hier den Architekten (auf-20261022-324 B1: «Warte auf die
    # Bestätigung der Nutzerin»). Die weibliche Form wird erst «Architektin», die Regeln unten
    # setzen dann den Fall; die männliche Einzahl direkt. Die Mehrzahl («die Nutzer») bleibt.
    (re.compile(r"\b(?:Be)?[Nn]utzerin\b"), lambda m: "Architektin"),
    (re.compile(r"\b([Dd])er\s+(?:Be)?[Nn]utzer\b(?!\w)"), lambda m: f"{m.group(1)}er Architekt"),
    (re.compile(r"\b([Dd])(en|em|es)\s+(?:Be)?[Nn]utzers?\b"), lambda m: f"{m.group(1)}{m.group(2)} Architekten"),
    (re.compile(r"\b(durch|für|gegen|ohne|um|auf|an|über)\s+die\s+Architektin\b", re.I),
     lambda m: f"{m.group(1)} den Architekten"),
    (re.compile(r"\b([Dd])ie\s+Architektin\b"), lambda m: f"{m.group(1)}er Architekt"),
    (re.compile(r"\b([Bb])ei\s+der\s+Architektin\b"), lambda m: f"{m.group(1)}eim Architekten"),
    (re.compile(r"\b([Vv])on\s+der\s+Architektin\b"), lambda m: f"{m.group(1)}om Architekten"),
    (re.compile(r"\b([Zz])ur\s+Architektin\b"), lambda m: f"{m.group(1)}um Architekten"),
    # «der Architektin» ist Dativ nach Präposition und am Satzanfang, sonst Genitiv («der
    # Bestätigung der Architektin» → «des Architekten», auf-20261022-323 B1).
    (re.compile(r"\b(mit|nach|zu|aus|seit|gegenüber|ausser|außer|neben|vor|hinter|unter)\s+der\s+"
                r"Architektin\b", re.I), lambda m: f"{m.group(1)} dem Architekten"),
    (re.compile(r"(^|(?<=[.!?:]\s))Der\s+Architektin\b"), lambda m: f"{m.group(1)}Dem Architekten"),
    (re.compile(r"\bder\s+Architektin\b"), lambda m: "des Architekten"),
    (re.compile(r"\b([Ee])iner\s+Architektin\b"), lambda m: f"{m.group(1)}inem Architekten"),
    (re.compile(r"\b([Ee])ine\s+Architektin\b"), lambda m: f"{m.group(1)}in Architekt"),
    (re.compile(r"\bArchitektin\b"), lambda m: "Architekt"),
)


def fuer_den_architekten(text: str) -> str:
    """Was an den Architekten geht, in seiner Sprache (auf-20261021-322, B2 und B4).

    * Kein Werkzeugname: «über das Werkzeug `vis_render`» wird «über das Werkzeug «Rendern»»
      (:data:`ALLTAGSWORT`; ein unbekanntes ``vis_*`` heisst «Knotenansicht»).
    * Einheitlich «der Architekt», wie die Sätze des Kerns — nicht «die Architektin» daneben.
    """
    if not text:
        return text
    text = _WERKZEUGNAME_IM_TEXT.sub(
        lambda m: f"«{ALLTAGSWORT.get(m.group(1), 'Knotenansicht')}»", text)
    for muster, ersatz in _ARCHITEKTIN:
        text = muster.sub(ersatz, text)
    return text


def _satz_nicht_vorgeschlagen(namen: list[str]) -> str:
    """Was der Kern abwies, in einem Satz für den Architekten — je Werkzeug einmal (322 B1)."""
    teile = [f"«{ALLTAGSWORT.get(n, 'Knotenansicht')}»" for n in dict.fromkeys(namen)]
    return f"Nicht vorgeschlagen: {', '.join(teile)}."


def _doppelte_stimmung_einzeln(knoten_weg: list[dict], offen: list[dict],
                               nachricht: str) -> list[str]:
    """Der Satz aus 321 B1, wenn der abgewiesene Knoten der doppelte Stimmungs-Knoten war (322 B1).

    In 322 F5 rief das Modell Stimmungs-Knoten, Verbindung und Render-Auftrag EINZELN; der Kern
    wies Knoten und Verbindung ab, und übrig blieb genau der Auftrag mit der Stimmung — dasselbe
    Ergebnis wie (b), aber ohne seinen Satz. Bittet die Frage um einen Knoten, gilt es nicht.
    """
    if not knoten_weg or _FRAGE_NACH_KNOTEN.search(nachricht or ""):
        return []
    presets = {(o.get("argumente") or {}).get("stimmungPreset") for o in offen
               if o.get("werkzeug") == "vis_render"}
    presets.discard(None)
    aus = []
    for k in knoten_weg:
        args = k.get("argumente") or {}
        preset = (args.get("params") or {}).get("preset") if isinstance(args, dict) else None
        if args.get("typ") == "stimmung" and preset in presets:
            aus.append(f"kein zusätzlicher Stimmungs-Knoten «{preset}» — der Render-Auftrag "
                       f"trägt die Stimmung schon")
    return aus


def _graph_lesen_ohne_geratene_kennung(argumente: dict, bekannt: str) -> dict:
    """``graph_lesen`` ohne eine geratene ``graphId`` (auf-20261021-322, B3).

    In F3 las das Modell den Graph mit «graph_123» — einer Kennung, die in keinem Ergebnis stand;
    der Kern liess sie durch. Geprüft wird wie bei ``vis_render`` (steht die Kennung in Frage,
    Verlauf oder einem Ergebnis?). Anders als dort wird der Aufruf nicht abgewiesen, sondern die
    Kennung **weggelassen**: ``graph_lesen`` ohne ``graphId`` liest alle Graphen (so beschreibt
    es die Werkzeugliste), das Ergebnis ist also dasselbe oder mehr — und eine Abweisung kostete
    eine der drei inneren Runden (:data:`RUNDEN_HOECHSTENS`). In 322 F3 wäre die Frage damit
    ohne Render-Karte geendet.
    """
    wert = argumente.get("graphId")
    if (isinstance(wert, (str, int)) and not isinstance(wert, bool) and str(wert).strip()
            and not _kommt_vor(str(wert).strip(), bekannt)):
        return {k: v for k, v in argumente.items() if k != "graphId"}
    return argumente


def _satz_weggelassen(weg: list[str]) -> str:
    return (f"Weggelassen, weil niemand es nannte oder es nicht erlaubt ist: {', '.join(weg)} "
            f"— es gilt, was am Knoten steht.")


def _mit_freigabesatz(text: str, nachricht: str) -> str:
    """Wer nach der Freigabe fragt, hört :data:`SATZ_NUR_ARCHITEKT` — auf JEDEM Ausgang.

    **Warum (auf-20261021-320, B3):** In F3 sagte das Modell «Freigeben kann nur der
    Architekt.» in der ersten inneren Runde; der Bild-Anstoss verwarf den Satz, und der Ausgang
    «Dazu fand ich kein passendes Werkzeug» hängte ihn nicht an. Und wo er anhing, fehlte er,
    sobald die Antwort «Render-Knoten» enthielt. Jetzt zählt nur, ob der volle Satz dasteht.
    """
    if not _FRAGE_NACH_FREIGABE.search(nachricht or "") or SATZ_NUR_ARCHITEKT in text:
        return text
    # Der kurze Satz des Modells weicht dem vollen, der sagt, WO freigegeben wird (310 B3).
    text = re.sub(r"\s*Freigeben kann nur der Architekt\b[^.!?]*[.!?]?\s*", " ", text).strip()
    return f"{SATZ_NUR_ARCHITEKT} {text}".strip()


#: Eine Kartenkennung, die ein Satz der Antwort nennt («Karte A-1», «Karten A-1, A-2», «Karte «A-1»»).
_KARTE_GENANNT = re.compile(r"\bKarten?\s+«?([A-Za-z]+-\d+)\b")
_LOESCHEN = re.compile(r"lösch|loesch|entfern", re.I)
_ALS_KARTE_GEMELDET = re.compile(r"\bKarte|vorgeschlagen|vorschlag", re.I)


def _loeschen_in(getan) -> bool:
    """Schlug ein Schritt dieser Frage ein Löschen vor (Werkzeug, Paket-Schritt oder Kartentext)?"""
    for sch in getan or ():
        if "loeschen" in str(sch.get("werkzeug", "")).lower():
            return True
        if "loeschen" in json.dumps(sch.get("argumente") or {}, ensure_ascii=False).lower():
            return True
        if any(_LOESCHEN.search(m.group(2) or "") for m in _KARTE_MIT_WAS.finditer(str(sch.get("ergebnis", "")))):
            return True
    return False


def _ohne_fremde_karten(saetze: list[str], getan, gespraech: str) -> list[str]:
    """Die Sätze ohne die, die eine Karte nennen, die in diesem Gespräch nicht entstand.

    **Warum (auf-20261021-319, B1):** qwen3:14b schrieb den Beispielsatz des Systemsatzes «Das
    Löschen ist als Karte A-1 vorgeschlagen.» in F1 bis F3 ab — dort wurde nichts gelöscht. Eine
    Bitte im Systemsatz ist bei einem 14-B-Modell keine Gewähr; darum prüft der Kern selbst:

    * Ein Satz, der eine **Kartenkennung** nennt, die weder ein Schritt dieser Frage meldete noch
      im Gespräch (Frage, Verlauf) steht, wird verworfen.
    * Ein Satz, der ein **Löschen als Karte/Vorschlag** meldet, wird verworfen, wenn kein Schritt
      dieser Frage etwas zum Löschen vorschlug — auch wenn die Kennung stimmt (in 319 F1 hiess die
      Stimmungs-Karte tatsächlich A-1).
    """
    bekannt = _karten_in(getan)
    loeschen = _loeschen_in(getan)
    raus = []
    for satz in saetze:
        genannt = [m.group(1) for m in _KARTE_GENANNT.finditer(satz)]
        fremd = [k for k in genannt if k not in bekannt and not _kommt_vor(k, gespraech)]
        falsches_loeschen = (not loeschen and _LOESCHEN.search(satz) is not None
                             and _ALS_KARTE_GEMELDET.search(satz) is not None)
        if fremd or falsches_loeschen:
            continue
        raus.append(satz)
    return raus


def _berichtige_antwort(antwort: str, nachricht: str, getan: list[dict], *,
                        gespraech: str = "") -> str:
    """Die Schlussantwort an das halten, was wirklich geschah (Befunde B3 und B5).

    * «FEHLER:» am Anfang ist die Sprache der Werkzeuge, nicht die an den Menschen — weg.
    * Liegen die Handlungen dieser Frage **nur als Karten** vor, wird ein Satz, der sie als getan
      meldet («wurde gelöscht»), durch den richtigen ersetzt; sind einige direkt geschehen, steht
      der Kartensatz dazu.
    * Wer nach der Freigabe fragt, hört :data:`SATZ_NUR_ARCHITEKT`, was das Modell auch sagte.
    * Ein Satz, der eine Karte nennt, die in diesem Gespräch nicht entstand, oder ein Löschen ohne
      Löschschritt, fällt weg (:func:`_ohne_fremde_karten`, auf-20261021-319 B1). ``gespraech``
      ist der Text von Verlauf und Frage — eine Karte aus einer früheren Frage darf genannt werden.
    """
    text = re.sub(r"^\s*(FEHLER|VERWEIGERT)\s*:\s*", "", antwort or "").strip()
    if text:
        text = " ".join(_ohne_fremde_karten(re.split(r"(?<=[.!?])\s+", text), getan,
                                            f"{nachricht or ''}\n{gespraech}")).strip()
    wirkend = [s for s in getan if s["werkzeug"] not in _NUR_LESEN]
    # Je Schritt die Karten (auch mitten im Text, auch aus einem Paket) samt dem, was sie
    # vorschlagen — der Satz nennt es: «vorgeschlagen als Karte A-2 (Knoten «Modell» löschen)».
    gefunden = [[(m.group(1), (m.group(2) or "").strip()) for m in
                 _KARTE_MIT_WAS.finditer(s["ergebnis"])] for s in wirkend]
    karten = [k for liste in gefunden for k, _ in liste]
    if karten:
        teile = [f"{k} ({w})" if w else k for liste in gefunden for k, w in liste]
        satz_karte = (f"Noch nicht ausgeführt: vorgeschlagen als Karte {', '.join(teile)} — erst "
                      f"«Anwenden» durch den Architekten führt es aus.")
        saetze = re.split(r"(?<=[.!?])\s+", text) if text else []
        # EIN SATZ, DER ES ALS GETAN MELDET, BLEIBT EINE BEHAUPTUNG, AUCH WENN DIE KARTE DANEBEN
        # STEHT (auf-20261021-314, B3 F4: «Der Modell-Knoten wurde gelöscht — es liegt eine
        # Karte beim Architekten.»). Bis dahin schützte das Wort «Karte» irgendwo im Satz. Jetzt
        # gilt nur, was die getan-Form selbst zur Karte macht («habe eine Karte angelegt») oder
        # den Satz als Vorschlag ausweist («vorgeschlagen», «noch nicht», «erst …»).
        behauptet = [s for s in saetze if _behauptet_getan(s)]
        if behauptet and all(gefunden):
            neu, ersetzt = [], False
            for s in saetze:
                if s in behauptet:
                    if not ersetzt:
                        neu.append(satz_karte)
                        ersetzt = True
                    continue
                neu.append(s)
            text = " ".join(neu)
        elif behauptet or not text:
            # Auch wenn nach dem Verwerfen nichts blieb, sagt der Kern, was als Karte liegt.
            text = f"{text} {satz_karte}".strip()
    # JEDE KARTE WIRD GENANNT (auf-20261022-323, B2): In 323 F5 rief das Modell einzeln und
    # neben der Render-Karte ging eine zweite Karte «Knoten einstellen» hinaus, die kein Satz
    # nannte. Ab zwei Karten nennt ein Satz die, die der Text noch nicht nennt.
    if len(karten) >= 2:
        # Ein Satz des Modells, der eine Karte ohne Kennung meldet («liegt als Karte bereit»),
        # fällt weg — die Karten stehen mit Kennung im Text (325 B1: A-2 stand zweimal).
        text = " ".join(s for s in re.split(r"(?<=[.!?])\s+", text)
                        if not (_ALS_KARTE_OHNE_KENNUNG.search(s)
                                and not re.search(r"\b[A-Z]-\d+\b", s))).strip()
        # Klammertext in einer Form: Werkzeugnamen als blosses Alltagswort, ohne «» (324 B2).
        def _was(w, werkzeug):
            w = _WERKZEUGNAME_IM_TEXT.sub(lambda m: ALLTAGSWORT.get(m.group(1), "Knotenansicht"), w)
            return w.strip(" «»") or ALLTAGSWORT.get(werkzeug, "Knotenansicht")
        fehlend = [f"{k} ({_was(w, s['werkzeug'])})"
                   for s, liste in zip(wirkend, gefunden) for k, w in liste if k not in text]
        if fehlend:
            mehr = len(fehlend) > 1
            text = (f"{text} Als {'Karten' if mehr else 'Karte'} vorgeschlagen: {', '.join(fehlend)} "
                    f"— erst «Anwenden» durch den Architekten führt {'sie' if mehr else 'es'} "
                    f"aus.").strip()
    # OHNE KARTE KEINE BESTELLUNG (auf-20261021-321, B6).
    text = _ohne_erfundene_bestellung(text, getan, f"{nachricht or ''}\n{gespraech}")
    # Wer nach der Freigabe fragt, hört den vollen Satz (310 B3; seit 320 B3 auf jedem Ausgang).
    text = _mit_freigabesatz(text, nachricht)
    # BEI EINER RENDER-KARTE SAGT DIE ANTWORT, WER FREIGIBT (auf-20261021-321, B2).
    text = _mit_render_freigabe(text, getan)
    # IN DER SPRACHE DES ARCHITEKTEN (auf-20261021-322, B2/B4): kein Werkzeugname, «der Architekt».
    text = fuer_den_architekten(text)
    return text or "Fertig."


#: Steht unter jeder Antwort, deren Frage eine Render-Karte ergab (auf-20261021-321, B2).
SATZ_RENDER_FREIGABE = ("Gerechnet wird erst, wenn der Architekt die Karte anwendet und am "
                        "Render-Knoten mit «Freigeben» freigibt — ich kann nicht freigeben.")
#: Dasselbe, wenn die Frage zwei oder mehr Karten ergab (auf-20261022-325 B2).
SATZ_RENDER_FREIGABE_MEHR = SATZ_RENDER_FREIGABE.replace("die Karte anwendet", "die Karten anwendet")
#: Ein Satz, der eine Karte meldet, ohne sie zu nennen (325 B1).
_ALS_KARTE_OHNE_KENNUNG = re.compile(r"\bals\s+Karten?\b", re.I)
#: Ersetzt eine behauptete Bestellung, wenn keine Render-Karte entstand (321 B6).
SATZ_KEIN_RENDER_AUFTRAG = ("Ein Render-Auftrag liegt noch nicht vor: In dieser Frage entstand "
                            "keine Karte.")
#: Ersetzt eine behauptete Handlung, wenn in dieser Frage nichts geschah als Lesen (321 B6).
SATZ_NICHTS_GETAN = "Noch nichts geändert oder vorgeschlagen: In dieser Frage entstand keine Karte."
#: Ein Satz über einen Render-Auftrag oder ein Bild …
_UEBER_RENDER = re.compile(r"render(?!-?knoten)|\bbild|\bauftrag", re.I)
#: … der ihn als gestellt, gestartet oder als Karte vorliegend meldet.
_ALS_BESTELLT = re.compile(
    r"\b(?:gestellt|bestellt|gestartet|ausgelöst|ausgeführt|gerechnet|gerendert|erteilt|"
    r"übermittelt|abgeschickt|in auftrag gegeben|vorgeschlagen)\b|\bals\s+karte\b|"
    r"\bliegt\b[^.!?]*\bkarte\b|\bläuft\b", re.I)
#: «— der Render wird dann ausgeführt»: Nach «Anwenden» rechnet noch nichts, erst nach der
#: Freigabe (321 B2). Der Nachsatz fällt weg; :data:`SATZ_RENDER_FREIGABE` sagt es richtig.
_RENDER_NACH_ANWENDEN = re.compile(
    r"\s*[—–-]+\s*(?:der|das|die)\s+(?:render\w*|bild\w*)\s+wird\s+"
    r"(?:dann\s+|danach\s+|sofort\s+|anschliessend\s+)?"
    r"(?:ausgeführt|gerechnet|gestartet|erstellt|gerendert)\b[^.!?]*", re.I)


def _ist_render_schritt(sch) -> bool:
    if sch.get("werkzeug") == "vis_render":
        return True
    if sch.get("werkzeug") == "vis_paket":
        schritte = (sch.get("argumente") or {}).get("schritte")
        return isinstance(schritte, list) and any(
            isinstance(t, dict) and t.get("befehl") == "vis_render" for t in schritte)
    return False


def _render_karte_in(getan) -> bool:
    """Ergab ein Render-Schritt dieser Frage (``vis_render`` oder ein Paket mit ihm) eine Karte?"""
    return any(_ist_render_schritt(sch) and _KARTE_IRGENDWO.search(str(sch.get("ergebnis", "")))
               for sch in getan or ())


def _ohne_erfundene_bestellung(text: str, getan, gespraech: str) -> str:
    """Ohne Karte behauptet die Antwort keine Bestellung (auf-20261021-321, B6).

    **Warum:** Mit dem Ersatz-Sprachmodell (P4) wurden zwei geratene Kennungen abgewiesen, dann
    schrieb das Modell «Ich habe den Render-Auftrag gestellt.» — ohne Karte, und der Satz ging
    unkorrigiert hinaus: :func:`_berichtige_antwort` prüfte getan-Sätze nur, wenn eine Karte da
    war. Jetzt fällt ein Satz, der einen Render-Auftrag als gestellt oder als Karte meldet, weg,
    wenn kein Render-Schritt dieser Frage eine Karte ergab (eine Karte aus dem Gespräch, mit
    ihrer Kennung genannt, darf bleiben); und geschah in dieser Frage nichts als Lesen, fällt
    jeder Satz weg, der eine Handlung als getan meldet. An ihre Stelle tritt der richtige Satz.
    """
    if not text:
        return text
    render_karte = _render_karte_in(getan)
    nur_gelesen = not any(s["werkzeug"] not in _NUR_LESEN for s in getan or ())
    if render_karte and not nur_gelesen:
        return text
    saetze = re.split(r"(?<=[.!?])\s+", text)
    bleibt, ersatz = [], None
    eigene = _karten_in(getan)
    for satz in saetze:
        # Ein Satz mit der Kennung einer Karte, die es gibt (aus dieser Frage oder dem
        # Gespräch), meldet sie richtig — er bleibt.
        frueher = any(m.group(1) in eigene or _kommt_vor(m.group(1), gespraech)
                      for m in _KARTE_GENANNT.finditer(satz))
        if (not render_karte and not frueher and _UEBER_RENDER.search(satz)
                and _meldet_bestellt(satz) and SATZ_NUR_ARCHITEKT not in satz):
            ersatz = SATZ_KEIN_RENDER_AUFTRAG
            continue
        if nur_gelesen and not frueher and _behauptet_getan(satz):
            ersatz = ersatz or SATZ_NICHTS_GETAN
            continue
        bleibt.append(satz)
    if ersatz is None:
        return text
    return " ".join([*bleibt, ersatz]).strip()


#: Eine Verneinung höchstens drei Wörter VOR dem Wort, das sie verneint («ist noch nicht
#: gestellt», «kein Auftrag wurde gestellt» zählt nicht — dort stehen mehr Wörter dazwischen).
_VERNEINT_DAVOR = re.compile(r"\b(?:nicht|nie|niemals|kein\w*)\b(?:\W+\w+){0,3}?\W*$", re.I)
#: «läuft noch nicht», «liegt keine Karte vor»: bei «läuft» und «liegt» steht sie dahinter.
_VERNEINT_DAHINTER = re.compile(r"^\W+(?:\w+\W+)?(?:nicht|nie|kein\w*)\b", re.I)


def _verneint(satz: str, treffer: re.Match) -> bool:
    """Ist das Wort ``treffer`` in ``satz`` verneint? (auf-20261021-322, B2)"""
    if _VERNEINT_DAVOR.search(satz[:treffer.start()]):
        return True
    wort = treffer.group(0).lower()
    if wort.startswith(("läuft", "liegt")):
        return (re.search(r"\b(?:nicht|nie|kein\w*)\b", wort) is not None
                or _VERNEINT_DAHINTER.search(satz[treffer.start() + len(wort.split()[0]):])
                is not None)
    return False


def _meldet_bestellt(satz: str) -> bool:
    """Meldet der Satz eine Bestellung — und nicht ihr Fehlen? (auf-20261021-322, B2)

    **Warum:** In F6 schrieb qwen3:14b richtig «Der Render-Auftrag ist noch nicht gestellt.»;
    die Regel aus 321 B6 strich den Satz, weil «gestellt» darin steht, und hängte ihren eigenen
    an — inhaltlich gleich. Ein Satz, in dem JEDES Bestell-Wort verneint ist, bleibt stehen.
    """
    treffer = list(_ALS_BESTELLT.finditer(satz))
    return bool(treffer) and not all(_verneint(satz, t) for t in treffer)


def _mit_render_freigabe(text: str, getan) -> str:
    """Ergab die Frage eine Render-Karte, sagt die Antwort, dass der Architekt freigibt (321 B2).

    **Warum:** F5 endete mit «Der Architekt kann ihn nun anwenden — der Render wird dann
    ausgeführt.» Das verschweigt die Freigabe am Render-Knoten; nach «Anwenden» liegt nur der
    Auftrag am Knoten. Der Nachsatz fällt weg, :data:`SATZ_RENDER_FREIGABE` steht am Ende —
    ausser der Freigabesatz (:data:`SATZ_NUR_ARCHITEKT`) steht schon da.
    """
    if not _render_karte_in(getan):
        return text
    text = _RENDER_NACH_ANWENDEN.sub("", text or "").strip()
    if SATZ_RENDER_FREIGABE in text or SATZ_RENDER_FREIGABE_MEHR in text or SATZ_NUR_ARCHITEKT in text:
        return text
    satz = SATZ_RENDER_FREIGABE_MEHR if len(_karten_in(getan)) >= 2 else SATZ_RENDER_FREIGABE
    return f"{text} {satz}".strip()


#: Was einen Satz mit getan-Form als Vorschlag ausweist (B3 F4).
_ALS_VORSCHLAG = re.compile(r"vorgeschlagen|vorschlag|noch nicht|nicht ausgeführt|erst\b|sobald|wenn der "
                            r"architekt", re.I)


def _behauptet_getan(satz: str) -> bool:
    """Meldet der Satz eine Handlung als getan? Nicht, wenn die getan-Form selbst die Karte
    betrifft («habe eine Karte angelegt») oder der Satz sie als Vorschlag ausweist."""
    if _ALS_VORSCHLAG.search(satz):
        return False
    # «wurde nicht gelöscht» meldet nichts als getan (322 B2, dieselbe Regel wie bei Bestellungen).
    return any("karte" not in m.group(0).lower()
               and not _VERNEINT_DAVOR.search(satz[:m.start(2)])
               for m in _GETAN.finditer(satz))


#: Was der Kern an die Beschreibung eines Werkzeugs der Knotenansicht HÄNGT, bevor sie ans Modell
#: geht (auf-20261021-320, B1): Die Beschreibung von ``vis_render`` stammt aus der Knotenansicht
#: und zählt Stimmung, Backbone, Güte und Auflösung samt erlaubten Werten auf — qwen3:14b füllte
#: sie aus, obwohl niemand sie nannte. Der Kern lässt Erfundenes ohnehin weg
#: (:func:`_ohne_erfundenes`); der Zusatz spart die Mühe, es erst zu erfinden.
ZUSATZ_BESCHREIBUNG = {
    "vis_render": ("Für «Rechne» oder «Render» genügen graphId und nodeId des Render-Knotens aus "
                   "graph_lesen. Alle anderen Angaben lässt du weg, wenn sie niemand nannte — "
                   "dann gilt, was am Knoten steht; der Kern lässt Erfundenes sonst selbst weg."),
}


SATZ_SCHRITTE_ERSCHOEPFT = (
    "Du hast für diese Frage alle Werkzeugschritte gebraucht. Antworte jetzt ohne Werkzeug: "
    "Sage kurz, was du getan oder vorgeschlagen hast und was noch offen ist.")


def pruefe_werkzeugliste(werkzeuge) -> list[dict]:
    """Die Liste der Mac-App (``[{name, description, inputSchema}]``) → Werkzeuge für Ollama.

    Geprüft wird die **Form**, nicht der Inhalt: Namen wie bei MCP, ein Objekt-Schema, Grössen.
    Ein Werkzeug, das freigibt, wird abgewiesen (:data:`_NIE_ALS_WERKZEUG`).
    """
    if not isinstance(werkzeuge, (list, tuple)) or not werkzeuge:
        raise AssistentError("Die Werkzeugliste ist eine nicht leere Liste.")
    if len(werkzeuge) > WERKZEUGE_HOECHSTENS:
        raise AssistentError(f"Die Werkzeugliste hat mehr als {WERKZEUGE_HOECHSTENS} Werkzeuge.")
    try:
        zeichen = len(json.dumps(werkzeuge, ensure_ascii=False))
    except (TypeError, ValueError):
        raise AssistentError("Die Werkzeugliste ist kein JSON.") from None
    if zeichen > WERKZEUGLISTE_ZEICHEN_HOECHSTENS:
        raise AssistentError(f"Die Werkzeugliste ist länger als "
                             f"{WERKZEUGLISTE_ZEICHEN_HOECHSTENS} Zeichen.")
    raus, namen = [], set()
    for w in werkzeuge:
        if not isinstance(w, dict):
            raise AssistentError("Ein Werkzeug ist {«name», «description», «inputSchema»}.")
        name, beschreibung = w.get("name"), w.get("description", "")
        schema = w.get("inputSchema")
        if not isinstance(name, str) or not _WERKZEUGNAME.fullmatch(name):
            raise AssistentError("Ein Werkzeugname ist 1 bis 64 Zeichen aus Buchstaben, Ziffern, "
                                 "«_» und «-».")
        if _NIE_ALS_WERKZEUG.search(name):
            raise AssistentError(f"«{name}» ist kein Werkzeug des Assistenten — freigeben kann "
                                 f"nur ein Mensch.")
        if name in namen:
            raise AssistentError(f"Das Werkzeug «{name}» steht zweimal in der Liste.")
        if not isinstance(beschreibung, str) or len(beschreibung) > BESCHREIBUNG_HOECHSTENS:
            raise AssistentError(f"Die Beschreibung von «{name}» ist kein Text oder länger als "
                                 f"{BESCHREIBUNG_HOECHSTENS} Zeichen.")
        if not isinstance(schema, dict) or schema.get("type") != "object":
            raise AssistentError(f"Das Schema von «{name}» ist kein Objekt-Schema.")
        namen.add(name)
        if name in ZUSATZ_BESCHREIBUNG:
            beschreibung = f"{beschreibung} {ZUSATZ_BESCHREIBUNG[name]}".strip()
        raus.append({"type": "function", "function": {
            "name": name, "description": beschreibung, "parameters": schema}})
    return raus


def _kuerze(text: str, hoechstens: int) -> str:
    return text if len(text) <= hoechstens else text[:hoechstens - 1] + "…"


def _pruefe_schritte(schritte, namen) -> list[dict]:
    """``[{werkzeug, argumente, ergebnis}]`` — was die Mac-App ausführte, in Reihenfolge."""
    if schritte is None:
        return []
    if not isinstance(schritte, (list, tuple)):
        raise AssistentError("Die Schritte sind eine Liste.")
    if len(schritte) > SCHRITTE_HOECHSTENS:
        raise AssistentError(f"Mehr als {SCHRITTE_HOECHSTENS} Schritte in einer Frage.")
    raus = []
    for sch in schritte:
        if (not isinstance(sch, dict) or sch.get("werkzeug") not in namen
                or not isinstance(sch.get("argumente", {}), dict)
                or not isinstance(sch.get("ergebnis"), str)):
            raise AssistentError("Ein Schritt ist {«werkzeug» aus der Liste, «argumente»: {…}, "
                                 "«ergebnis»: Text}.")
        raus.append({"werkzeug": sch["werkzeug"], "argumente": sch.get("argumente") or {},
                     "ergebnis": _kuerze(sch["ergebnis"], ERGEBNIS_HOECHSTENS)})
    return raus


def frage_mit_werkzeugen(nachricht, verlauf=(), *, werkzeuge, schritte=(), sprachmodell=None,
                         bild_rechnet: bool = False, bildmodell_geladen: bool = False) -> dict:
    """Eine Runde des Assistenten mit der Werkzeugliste der Knotenansicht. **Rechnet nie.**

    Zurück kommt entweder ``{"antwort", "schritte_offen": [{"werkzeug", "argumente"}]}`` — die
    Mac-App führt sie aus und fragt mit ``schritte`` (dieselbe Nachricht, derselbe Verlauf, dazu
    je Schritt ``ergebnis``) weiter — oder ``{"antwort"}``: fertig. ``antwort`` ist dann, was ins
    Gespräch kommt; bei offenen Schritten ein Zwischensatz (kann leer sein).

    Ein Aufruf, den die Liste nicht kennt oder der kein Objekt als Angaben hat, geht **nicht** an
    die Mac-App: Das Modell bekommt hier «Abgewiesen: …» und darf in derselben Anfrage
    korrigieren (höchstens :data:`RUNDEN_HOECHSTENS` Runden).
    """
    if not isinstance(nachricht, str) or not nachricht.strip():
        raise AssistentError("Es fehlt die Nachricht — was soll der Assistent tun?")
    if len(nachricht) > NACHRICHT_HOECHSTENS:
        raise AssistentError(f"Die Nachricht ist länger als {NACHRICHT_HOECHSTENS} Zeichen.")
    frueher = _pruefe_verlauf(verlauf)
    liste = pruefe_werkzeugliste(werkzeuge)
    namen = {w["function"]["name"] for w in liste}
    schemas = {w["function"]["name"]: w["function"].get("parameters") for w in liste}
    getan = _pruefe_schritte(schritte, namen)
    if bild_rechnet:
        raise AssistentError(SATZ_BILD_RECHNET)
    if bildmodell_geladen:
        raise AssistentError(SATZ_BILDMODELL_GELADEN)
    modell = sprachmodell if sprachmodell is not None else Ollama()
    pruefe_sprachmodell(getattr(modell, "modell", None))

    nachrichten = ([{"role": "system", "content": SYSTEMTEXT_KNOTEN}] + frueher
                   + [{"role": "user", "content": nachricht.strip()}])
    # WAS SCHON GESCHAH, IN DER FORM, DIE OLLAMA KENNT: je Schritt der Aufruf des Modells und das
    # Ergebnis des Werkzeugs. Das Ergebnis kommt von der Knotenansicht — es ist Text, nie eine Rolle.
    for sch in getan:
        nachrichten.append({"role": "assistant", "content": "", "tool_calls": [
            {"function": {"name": sch["werkzeug"], "arguments": sch["argumente"]}}]})
        # EINE KARTE IST NICHT GETAN (auf-20261021-314, B3 F4): Das Ergebnis sagte «VORSCHLAG …
        # liegt als Karte», und das Modell schrieb trotzdem «wurde gelöscht — es liegt eine
        # Karte». Der Kern hängt an jedes solche Ergebnis den Satz, wie es heisst.
        inhalt_tool = sch["ergebnis"]
        if _KARTE_IRGENDWO.search(inhalt_tool):
            inhalt_tool = f"{inhalt_tool} {SATZ_KARTE_NICHT_GETAN}"
        nachrichten.append({"role": "tool", "tool_name": sch["werkzeug"],
                            "content": inhalt_tool})
    frei = SCHRITTE_HOECHSTENS - len(getan)
    if frei <= 0:
        nachrichten.append({"role": "user", "content": SATZ_SCHRITTE_ERSCHOEPFT})
    angebot = liste if frei > 0 else []
    # WAS DAS MODELL WISSEN KANN — gegen das werden Kennungen und Angaben geprüft (B4, B6).
    bekannt = "\n".join([nachricht] + [str(m.get("content", "")) for m in frueher]
                         + [sch["ergebnis"] for sch in getan])
    karten = _karten_in(getan)
    gespraech = "\n".join(str(m.get("content", "")) for m in frueher)
    neuer_graph = _neuer_graph_erlaubt(nachricht, getan)
    # BEI EINER BITTE UM EIN BILD EIN ANSTOSS (auf-20261021-310, B2) — nur, wenn vis_render
    # angeboten ist und in dieser Frage noch kein Render-Auftrag steht, und nur einmal.
    anstoss_offen = (bool(angebot) and "vis_render" in namen
                     and _FRAGE_NACH_BILD.search(nachricht) is not None
                     and not any(sch["werkzeug"] in ("vis_render", "vis_paket") for sch in getan))

    ende = time.monotonic() + FRIST_FRAGE_GESAMT_S
    antwort = ""
    abgewiesen: list[tuple[str, str]] = []
    weggelassen: list[str] = []
    ergaenzt: list[str] = []
    ohne_doppelt: list[str] = []
    abgelaufen = False
    for _ in range(RUNDEN_HOECHSTENS):
        rest = ende - time.monotonic()
        if rest <= 0:
            abgelaufen = True
            break
        try:
            botschaft = _chat(modell, nachrichten, rest, angebot)
        except ZeitUeberschritten:
            abgelaufen = True
            break
        if not isinstance(botschaft, dict):
            raise AssistentError("Das Sprachmodell antwortete ohne Botschaft.")
        inhalt = _ohne_denken(botschaft.get("content"))
        antwort = inhalt or antwort
        aufrufe = botschaft.get("tool_calls") or []
        if not isinstance(aufrufe, list) or not aufrufe or not angebot:
            if anstoss_offen and time.monotonic() < ende:
                anstoss_offen = False
                antwort = ""        # der Satz vor dem Anstoss ist keine Antwort auf die Bitte
                nachrichten.append({"role": "assistant", "content": inhalt})
                nachrichten.append({"role": "user", "content": SATZ_BILD_ANSTOSS})
                continue
            return {"antwort": _berichtige_antwort(antwort, nachricht, getan, gespraech=gespraech)}
        offen, abgewiesen = [], []
        for aufruf in aufrufe:
            funktion = aufruf.get("function") if isinstance(aufruf, dict) else None
            name = funktion.get("name") if isinstance(funktion, dict) else None
            argumente = funktion.get("arguments") if isinstance(funktion, dict) else None
            if isinstance(argumente, str):
                try:
                    argumente = json.loads(argumente or "{}")
                except ValueError:
                    argumente = None
            if argumente is None:
                argumente = {}
            # DIE ZWISCHENSAETZE GELTEN NUR FUER EINEN AUFRUF, DER HINAUSGEHT (auf-20261021-322,
            # B3): In F3 liess der Kern an einem vis_render mit geratener Kennung drei Angaben
            # weg, wies den Aufruf dann ab — und «Weggelassen …» ging trotzdem hinaus, über eine
            # Karte, die es nie gab. Jetzt haengen die Saetze am Aufruf und gehen nur mit ihm.
            weg, dazu, doppelt = [], [], []
            # ERFUNDENE FREIE ANGABEN FALLEN WEG, statt den Aufruf abzuweisen (320 B1/B2).
            if name in ERFUNDEN_FELDER and isinstance(argumente, dict):
                argumente, weg = _ohne_erfundenes(name, argumente, bekannt, schemas.get(name))
                # WAS DER NUTZER AUSDRUECKLICH NANNTE, KOMMT DAZU (321 B1).
                argumente, dazu = _ergaenze_aus_der_frage(name, argumente, nachricht,
                                                          schemas.get(name))
            elif name == "vis_paket" and isinstance(argumente, dict):
                argumente, weg = _paket_ohne_erfundenes(argumente, bekannt, schemas)
                argumente, dazu = _paket_ergaenzt(argumente, nachricht, schemas)
                # KEIN STIMMUNGS-KNOTEN NEBEN DEMSELBEN PRESET (321 B1).
                argumente, doppelt = _ohne_doppelte_stimmung(argumente, nachricht)
            elif name == "graph_lesen" and isinstance(argumente, dict):
                # GERATENE KENNUNG AUCH BEIM LESEN (322 B3) — geprüft wie bei vis_render.
                argumente = _graph_lesen_ohne_geratene_kennung(argumente, bekannt)
            if name not in namen:
                abgewiesen.append((name or "?", f"Ein Werkzeug «{name}» gibt es nicht."))
            elif not isinstance(argumente, dict):
                abgewiesen.append((name, "Die Angaben zum Werkzeug sind ein Objekt."))
            elif name == "vis_graphErstellen" and not neuer_graph:
                abgewiesen.append((name, SATZ_KEIN_NEUER_GRAPH))
            elif name == "vis_paket" and (grund := _pruefe_paket(
                    argumente, bekannt, karten, neuer_graph)) is not None:
                abgewiesen.append((name, grund))
            elif (grund := _pruefe_angaben(name, argumente, bekannt, karten)) is not None:
                abgewiesen.append((name, grund))
            else:
                offen.append({"werkzeug": name, "argumente": argumente,
                              "_saetze": (weg, dazu, doppelt)})
        # EIN NEUER KNOTEN UND SEINE VERBINDUNG GEHEN NUR ZUSAMMEN (auf-20261021-319, B2): In F1
        # setzte das Modell die Stimmung und verband sie in derselben Runde mit der geratenen
        # Kennung «n3»; der Kern wies die Verbindung ab, liess den Knoten aber hinaus — er kam als
        # Karte zurück, ohne Kennung, und eine Verbindung zu n2 entstand nie. Jetzt bleibt auch
        # der Knoten hier, und das Modell bekommt in derselben Anfrage den Weg über vis_paket.
        knoten_weg = []
        if (any(o["werkzeug"] == "vis_nodeSetzen" for o in offen)
                and any(n == "vis_verbinden" for n, _ in abgewiesen)):
            knoten_weg = [o for o in offen if o["werkzeug"] == "vis_nodeSetzen"]
            offen = [o for o in offen if o["werkzeug"] != "vis_nodeSetzen"]
            abgewiesen = [(n, SATZ_GLEICH_VERBINDEN if n == "vis_verbinden" else g)
                          for n, g in abgewiesen] + [("vis_nodeSetzen", SATZ_GLEICH_VERBINDEN)]
        if offen:
            # DIE GUELTIGEN GEHEN HINAUS, HOECHSTENS SO VIELE, WIE NOCH FREI SIND — die Mac-App
            # fuehrt sie aus. Eine Abweisung daneben wird nicht still verschluckt — aber der
            # Architekt liest sie in SEINER Sprache, einmal (auf-20261021-322, B1): Bis dahin
            # stand der Abweisungstext an das Modell wörtlich im Zwischensatz, in F5 zweimal.
            for o in offen:
                w, d, dp = o.pop("_saetze")
                weggelassen.extend(w)
                ergaenzt.extend(d)
                ohne_doppelt.extend(dp)
            # Ein abgewiesener Stimmungs-Knoten neben einem Render-Auftrag mit derselben Stimmung
            # ist der doppelte Knoten aus 321 B1, nur einzeln gerufen: Er heisst auch so.
            doppelt_einzeln = _doppelte_stimmung_einzeln(knoten_weg, offen, nachricht)
            ohne_doppelt.extend(doppelt_einzeln)
            nicht = [n for n, _ in abgewiesen
                     if not (doppelt_einzeln and n in ("vis_nodeSetzen", "vis_verbinden"))]
            satz = antwort
            if nicht:
                satz = f"{satz} {_satz_nicht_vorgeschlagen(nicht)}"
            if weggelassen:
                satz = f"{satz} {_satz_weggelassen(list(dict.fromkeys(weggelassen)))}"
            if ergaenzt:
                satz = (f"{satz} Aus deiner Frage übernommen: "
                        f"{', '.join(dict.fromkeys(ergaenzt))}.")
            if ohne_doppelt:
                doppelt_text = "; ".join(dict.fromkeys(ohne_doppelt))
                satz = f"{satz} {doppelt_text[:1].upper()}{doppelt_text[1:]}."
            return {"antwort": fuer_den_architekten(satz.strip()), "schritte_offen": offen[:frei]}
        nachrichten.append({"role": "assistant", "content": inhalt, "tool_calls": [
            {"function": a.get("function")} for a in aufrufe if isinstance(a, dict)]})
        for name, grund in abgewiesen:
            nachrichten.append({"role": "tool", "tool_name": name, "content": f"Abgewiesen: {grund}"})
    if antwort:
        return {"antwort": _berichtige_antwort(antwort, nachricht, getan, gespraech=gespraech)}
    if abgelaufen or not abgewiesen:
        raise AssistentError(SATZ_FRIST_ABGELAUFEN)
    # Auch dieser Ausgang trägt den Freigabesatz (auf-20261021-320, B3).
    # Auch hier nicht der Abweisungstext an das Modell (322 B1), sondern was nicht vorliegt.
    return {"antwort": _mit_freigabesatz(
        "Dazu fand ich kein passendes Werkzeug — nicht vorgeschlagen: "  # klein nach «—» (323 B3)
        + _satz_nicht_vorgeschlagen([abgewiesen[-1][0]]).removeprefix("Nicht vorgeschlagen: "),
        nachricht)}


# =========================================================================== anwenden

def anwenden(vorschlag, *, starte, entlade=None, mappe: dict | None = None):
    """Den Vorschlag rechnen lassen — **erst das Sprachmodell entladen, dann starten.**

    ``starte(einstellungen, varianten)`` ist der Weg, den das Rechnen ohnehin geht (im
    Server: derselbe wie ``POST /api/rechne``); er wird hier nicht nachgebaut. Was er
    zurückgibt, gibt ``anwenden`` zurück.

    ``entlade()`` nimmt das Sprachmodell von der Grafikkarte; Vorgabe ist
    :meth:`Ollama.entlade`. **Wirft es, wird nicht gestartet** — dann ist nicht bekannt, ob
    die Karte frei ist.

    ``mappe`` wie bei :func:`frage`: Der Standpunkt wird gegen die Einstellungen der Mappe
    geprüft, über die er sich legt — sonst scheiterte er erst am Blender-Knoten.

    Raises:
        AssistentError: Der Vorschlag hält der Prüfung nicht stand, oder das Entladen
            scheiterte.
    """
    einstellungen, varianten = pruefe_vorschlag(vorschlag, mappe)
    if entlade is None:
        entlade = Ollama().entlade
    befund = entlade()
    ergebnis = starte(einstellungen, varianten)
    # DER SATZ DES ENTLADENS GEHT MIT (auf-20261020-291): Er wurde hier verworfen, und am Mac
    # kam «Nicht entladen: …» nie an — gerechnet wurde trotzdem, und niemand wusste, warum
    # die Karte voll blieb. Er steht als `entladen` im Ergebnis des Starts.
    return _mit_entladen(ergebnis, befund)


def _mit_entladen(ergebnis, befund):
    """``ergebnis`` (Wörterbuch, oder ``(nutzlast, code)`` wie im Server) um ``entladen``."""
    if not (isinstance(befund, dict) and befund.get("satz")):
        return ergebnis
    eintrag = {"entladen": befund.get("entladen"), "satz": str(befund["satz"])}
    if isinstance(ergebnis, dict):
        return dict(ergebnis, entladen=eintrag)
    if isinstance(ergebnis, tuple) and ergebnis and isinstance(ergebnis[0], dict):
        return (dict(ergebnis[0], entladen=eintrag), *ergebnis[1:])
    return ergebnis


# ================================================ der Abholer und das eigene Modell

#: Die Marke «eine Frage läuft» — eine Datei in der Auftragsablage, die der Server während
#: einer Frage hält (:func:`frage_vermerkt`). Der Abholer ist ein anderer Prozess; die
#: Sperre des Servers (``Flaeche.frage_laeuft``) sieht er nicht.
DATEI_FRAGE_LAEUFT = "assistent-frage.json"

#: Wie alt eine Marke höchstens sein darf, um zu gelten — die ganze Frist einer Frage und
#: eine Minute dazu. Eine ältere Marke ist von einem abgestürzten Server liegen geblieben.
MARKE_GILT_S = FRIST_FRAGE_GESAMT_S + 60.0


class frage_vermerkt:                                    # noqa: N801 — als Satz gelesen
    """``with frage_vermerkt(ablage): …`` — die Marke liegt, solange die Frage läuft.

    Ohne Ablage (``None``) oder bei einem Schreibfehler geschieht nichts; der Abholer sieht
    dann nur die Auslastung der Karte (``tools/abholen.py``).
    """

    def __init__(self, ablage):
        self.datei = Path(ablage) / DATEI_FRAGE_LAEUFT if ablage else None

    def __enter__(self):
        if self.datei is not None:
            try:
                self.datei.parent.mkdir(parents=True, exist_ok=True)
                self.datei.write_text(json.dumps({"seit_epoch_s": time.time()}),
                                      encoding="utf-8")
            except OSError:
                self.datei = None
        return self

    def __exit__(self, *_):
        if self.datei is not None:
            try:
                self.datei.unlink()
            except OSError:
                pass
        return False


def frage_laeuft_in(ablage, *, _uhr=None) -> bool:
    """Liegt in dieser Ablage eine geltende Marke «eine Frage läuft»?"""
    if not ablage:
        return False
    try:
        satz = json.loads((Path(ablage) / DATEI_FRAGE_LAEUFT).read_text(encoding="utf-8"))
        seit = float(satz["seit_epoch_s"])
    except (OSError, ValueError, KeyError, TypeError):
        return False
    return 0.0 <= ((_uhr or time.time)() - seit) <= MARKE_GILT_S


def entlade_wenn_nur_eigenes(*, sprachmodell=None, anfrage_laeuft=None) -> dict:
    """Hält **nur** das eigene Modell der Visbox die Karte, und ohne laufende Anfrage?
    Dann entladen — sonst nicht, mit Satz.

    **Owner-Auflage der HomeStation (20.10.2026, zu Entscheid 106d):** Der Abholer darf ein
    Sprachmodell entladen, statt zu warten — nur das der Visbox, nur ohne laufende Anfrage,
    nie ein Modell von KosmoOrbit. Darum, in dieser Reihenfolge:

    1. Ist das eingestellte Modell überhaupt das eigene (:func:`geschuetzt`)?
    2. Was liegt laut Ollama auf der Karte (``/api/ps``)? Steht dort **irgendein** anderes
       Modell, wird nichts angefasst — der Speicher gehört dann nicht nur uns.
    3. Läuft eine Anfrage (``anfrage_laeuft()``, im Betrieb die Marke des Servers und die
       Auslastung der Karte)? Dann nicht — das nähme einer Antwort das Modell weg.

    Returns:
        ``{"entladen": bool, "satz"}`` — ``True`` nur, wenn wirklich entladen wurde.
    """
    try:
        modell = sprachmodell or Ollama()
    except AssistentError as fehler:
        return {"entladen": False, "satz": f"Kein Sprachmodell einstellbar: {fehler}"}
    grund = geschuetzt(modell.modell)
    if grund is not None:
        return {"entladen": False, "satz": f"Nicht entladen: {grund}"}
    try:
        geladen = modell.geladene()
    except AssistentError as fehler:
        return {"entladen": False, "satz": f"Ollama gab keine Auskunft ({fehler})."}
    if not geladen:
        return {"entladen": False,
                "satz": "Ollama hält kein Modell — der Speicher gehört einem anderen Programm."}
    fremde = [n for n in geladen if not _enthalten(modell.modell, [n])]
    if fremde:
        return {"entladen": False,
                "satz": (f"Auf der Karte liegt nicht nur das Modell der Visbox "
                         f"({len(fremde)} weitere) — es wird nichts entladen.")}
    if anfrage_laeuft is not None and anfrage_laeuft():
        return {"entladen": False,
                "satz": "Der Assistent beantwortet gerade eine Frage — es wird nicht entladen."}
    try:
        aus = modell.entlade()
    except AssistentError as fehler:
        return {"entladen": False, "satz": f"Entladen gescheitert: {fehler}"}
    return {"entladen": aus.get("entladen") is True, "satz": aus.get("satz") or ""}
