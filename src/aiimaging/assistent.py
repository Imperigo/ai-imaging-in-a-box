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

from aiimaging import arbeitsgang, kameras, kette, sprache

__all__ = [
    "AssistentError", "NichtErreichbar", "AntwortAbgebrochen", "ZeitUeberschritten",
    "Ollama",
    "ERLAUBTE_MODELLE", "AUSGESCHLOSSENE_MODELLE", "VORGABE_ADRESSE", "VORGABE_MODELL",
    "UMGEBUNG_ADRESSE", "UMGEBUNG_MODELL", "STANDPUNKT_FELDER", "WERKZEUGE",
    "STAND_BEREIT", "STAND_LAEDT", "STAND_FEHLT", "STAND_AUS", "STAENDE",
    "RECHENZEIT_JE_VARIANTE_S", "FRIST_FRAGE_GESAMT_S",
    "SATZ_BILD_RECHNET", "SATZ_BILDMODELL_GELADEN", "SATZ_FRIST_ABGELAUFEN",
    "anwenden", "frage", "kontext_der_mappe", "pruefe_adresse", "pruefe_sprachmodell",
    "pruefe_vorschlag",
    "stand",
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

#: Gemessen am Heim-PC (``auf-20261001-213``): liegt da, deutsche Werkzeugaufrufe 3 von 3.
VORGABE_MODELL = "qwen3:30b"

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

        ``{"entladen": True|None, "satz"}``. ``None`` heisst: Ollama antwortet nicht —
        dann hält es auch nichts auf der Karte, das sich entladen liesse, und der Lauf
        darf beginnen. Lehnt Ollama dagegen ab, wird geworfen: Dann ist nicht bekannt, ob
        die Karte frei ist, und ein Bild daneben liefe in den Speicherrand.
        """
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


def _chat(modell, nachrichten: list, frist: float) -> dict:
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
    if nimmt_frist:
        return modell.chat(nachrichten, WERKZEUGE, frist=frist)
    return modell.chat(nachrichten, WERKZEUGE)


def frage(nachricht, verlauf=(), *, sprachmodell=None, bild_rechnet: bool = False,
          bildmodell_geladen: bool = False, mappe: dict | None = None) -> dict:
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

    Raises:
        AssistentError: mit dem Satz für den Menschen (leer, zu lang, Modell nicht
            zugelassen, Ollama lehnt ab, ein Bild rechnet, Gesamtfrist abgelaufen).
            :class:`NichtErreichbar`, wenn Ollama nicht antwortet.
    """
    if not isinstance(nachricht, str) or not nachricht.strip():
        raise AssistentError("Es fehlt die Nachricht — was soll das Bild zeigen?")
    if len(nachricht) > NACHRICHT_HOECHSTENS:
        raise AssistentError(f"Die Nachricht ist länger als {NACHRICHT_HOECHSTENS} Zeichen.")
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
    entlade()
    return starte(einstellungen, varianten)
