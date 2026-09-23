#!/usr/bin/env python3
"""Die Oberfläche der App (Webseite und Server für das iPad) — **eine dünne Schicht, und
sie bleibt dünn.** Wie die App heisst, steht nicht hier, sondern in :data:`NAME`.

Sie liegt ausserhalb von ``src/aiimaging/``, weil Regel 4 jeden Oberflächen-Import im Kern
verbietet. Warum das keine Ordnungsfrage ist, steht in ``LIESMICH.md`` daneben.

Womit sie gebaut ist, und warum mit so wenig
--------------------------------------------
Mit ``http.server`` aus der Standardbibliothek und einer HTML-Seite, die nebenan liegt.
Kein Web-Rahmenwerk, kein Fenster-Werkzeugkasten, kein Skript von einem fremden Server.

* **Regel 1** schliesst die naheliegenden Fenster-Werkzeugkästen aus: PyQt ist GPL,
  PySide ist LGPL — und eine Oberfläche hinter einer Prozessgrenze ist keine.
* **Das Ziel ist ein Ein-Klick-Download.** Was zum Start eine Netzverbindung braucht,
  ist keiner. Eine Schriftart von einem fremden Server ist eine Netzverbindung.
* **Und jedes Rahmenwerk ist eine Abhängigkeit**, die mit installiert, gepflegt und
  lizenzgeprüft sein will. Für eine Fläche, die vier Dinge anzeigt, ist das ein
  schlechter Tausch.

Was dieses Modul ausdrücklich NICHT tut
---------------------------------------
Es rechnet nicht, misst nicht und urteilt nicht. **Jede Antwort, die es gibt, hat eine
Funktion aus** :mod:`aiimaging` **geliefert.** Stünde hier eine Schwelle, ein Urteil oder
eine Umrechnung, wäre dieselbe Fähigkeit an zwei Stellen — und eine davon ohne Oberfläche
nicht erreichbar. ``tests/test_oberflaeche.py`` hält das fest.

Sie hört nur auf ``127.0.0.1``
------------------------------
Hier liegen die Gebäudemodelle von jemandem. Eine Fläche, die von aussen erreichbar ist,
gibt sie weiter — auch wenn niemand das wollte. Der Vorgabewert ist darum die eigene
Maschine, und eine andere Adresse muss ausdrücklich gesetzt werden.

    python3 oberflaeche/server.py --ordner <projektordner>
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import hmac
import html
import math
import importlib.util
import json
import re
import secrets
import socket
import sys
import threading
import time
import urllib.parse
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# DER KERN WIRD IMPORTIERT, NICHT UMGEKEHRT. Diese Richtung ist die ganze Regel 4: Die
# Bibliothek weiss von dieser Datei nichts und laeuft ohne sie vollstaendig.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import inspect                                                  # noqa: E402

from aiimaging import (arbeitsgang, glbbox, importeur, kette, kopplung,   # noqa: E402
                       projekt)

#: Nur die eigene Maschine. Siehe Modulkopf.
VORGABE_ADRESSE = "127.0.0.1"

#: Eine Zahl ohne Bedeutung, weit weg von allem Üblichen — damit sie nicht zufällig
#: auf einem Anschluss landet, auf dem schon etwas anderes lauscht.
VORGABE_ANSCHLUSS = 8731

SEITE = Path(__file__).resolve().parent / "seite.html"

#: Die Koppelseite (Entscheid 26) — **ohne Anmeldung erreichbar, darum ohne jeden Inhalt
#: aus dem Projekt.** Ein Zahlenfeld, ein Knopf, ein Satz. Sie schickt die Zahl an
#: ``POST /api/verbinden`` und zeigt, was zurückkommt: im Erfolgsfall Benutzer und
#: Kennwort, **einmal** — der Browser fragt danach beim Öffnen der Fläche, und dort
#: werden sie eingetragen.
#:
#: Sie steht hier und nicht in einer Datei daneben, damit an ihr nichts nachgeladen werden
#: kann: kein Skript, keine Schrift, kein Bild — auch nicht von diesem Server. Eine Seite
#: vor der Tür, die etwas hinter der Tür nachlädt, bekäme es nicht (401) oder, schlimmer,
#: bekäme es doch.
#:
#: **``__NAME__`` wird beim Ausliefern durch :data:`NAME` ersetzt** (Befund der
#: Durchsicht D-SERVER, 22.09.2026): Hier stand der Name der App fest eingeschrieben —
#: die Stelle, die beim Umbenennen in KosmoSketch (Entscheid 34) niemand findet.
#:
#: **Und sie sagt nur, was im Browser stimmt** (derselbe Befund): Der Erfolgssatz lautete
#: «Dieses Gerät merkt sich die Anmeldung» — ein Browser merkt sich nichts, was ihm
#: niemand zu merken gibt. Hier steht darum, was der Mensch jetzt tun muss.
KOPPELSEITE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__NAME__ — Gerät verbinden</title>
<style>
  :root { --grund: #14161a; --feld: #1c1f26; --rand: #2b3038; --schrift: #e6e8ec;
          --leise: #9aa2ae; --bestanden: #4ea373; --durchgefallen: #e2776f; }
  body { margin: 0; background: var(--grund); color: var(--schrift);
         font: 16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
  main { max-width: 420px; margin: 12vh auto; padding: 24px; background: var(--feld);
         border: 1px solid var(--rand); border-radius: 10px; }
  h1 { font-size: 18px; margin: 0 0 8px; }
  p { color: var(--leise); margin: 0 0 16px; }
  input { font: 600 28px/1 ui-monospace, Menlo, monospace; letter-spacing: .3em;
          width: 100%; box-sizing: border-box; padding: 12px; text-align: center;
          background: var(--grund); color: var(--schrift); border: 1px solid var(--rand);
          border-radius: 8px; }
  button { margin-top: 12px; width: 100%; min-height: 60px; font: inherit; font-weight: 600;
           background: var(--grund); color: var(--schrift); border: 1px solid var(--leise);
           border-radius: 8px; cursor: pointer; }
  #satz { margin-top: 14px; min-height: 1.5em; }
  .gut { color: var(--bestanden); } .schlecht { color: var(--durchgefallen); }
  dl { display: grid; grid-template-columns: auto 1fr; gap: 4px 12px; margin: 12px 0; }
  dt { color: var(--leise); } dd { margin: 0; font-family: ui-monospace, Menlo, monospace;
                                   overflow-wrap: anywhere; }
  a { color: var(--schrift); }
</style>
</head>
<body>
<main>
  <h1>Dieses Gerät verbinden</h1>
  <p>Die sechsstellige Zahl steht im Fenster, in dem __NAME__ auf dem Rechner gestartet wurde.</p>
  <input id="zahl" inputmode="numeric" autocomplete="one-time-code" maxlength="6"
         pattern="[0-9]*" aria-label="Sechsstellige Zahl">
  <button id="los" type="button">Verbinden</button>
  <div id="satz" role="status"></div>
  <div id="zugang" hidden>
    <dl><dt>Benutzer</dt><dd id="benutzer"></dd><dt>Kennwort</dt><dd id="kennwort"></dd></dl>
    <p>Hier erscheinen sie nur dieses eine Mal. Jetzt aufschreiben oder im Browser
       speichern lassen: Beim Öffnen der Fläche fragt er danach. Ob er sie sich merkt,
       entscheidet der Browser, nicht diese Seite.</p>
    <a href="/">Zur Fläche</a>
  </div>
</main>
<script>
"use strict";
const $ = (id) => document.getElementById(id);
async function verbinden() {
  $("satz").className = ""; $("satz").textContent = "prüft …";
  try {
    const antwort = await fetch("/api/verbinden", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({pin: $("zahl").value}),
    });
    const d = await antwort.json();
    const gut = d.verbunden === true;
    $("satz").className = gut ? "gut" : "schlecht";
    $("satz").textContent = d.satz || d.fehler || "Keine Antwort.";
    if (gut) {
      $("benutzer").textContent = d.benutzer; $("kennwort").textContent = d.kennwort;
      $("zugang").hidden = false; $("los").disabled = true;
    }
  } catch (f) {
    $("satz").className = "schlecht";
    $("satz").textContent = "Der Rechner antwortet nicht: " + f;
  }
}
$("los").addEventListener("click", verbinden);
$("zahl").addEventListener("keydown", (e) => { if (e.key === "Enter") verbinden(); });
</script>
</body>
</html>
"""

#: Endungen, die diese Fläche als Bild ausliefert, mit ihrem Medientyp.
#:
#: **Eine Positivliste und keine Sperrliste.** Eine Sperrliste ist immer unvollständig —
#: sie kennt nur, woran jemand schon gedacht hat. Diese hier sagt, was hinausgeht, und
#: alles andere geht nicht hinaus, auch wenn es im Projektordner liegt.
BILDTYPEN = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


#: Wie gross eine Zeichnung höchstens sein darf, die über die Fläche hereinkommt.
#:
#: **Zwei Megabyte, und die Zahl ist eine Setzung mit Begründung.** Eine
#: Bildschirmzeichnung im iPad-Format (2048 x 1536) als PNG mit wenigen Strichen liegt
#: weit darunter; ein versehentlich hereingereichtes Foto liegt darüber. Der Riegel
#: trennt genau diese zwei Fälle.
#:
#: *Er greift, BEVOR geschrieben wird.* Ein Riegel, der erst beim Schreiben greift, hat
#: schon geschrieben.
SKIZZE_GROESSENRIEGEL = 2 * 1024 * 1024

#: Was an jeder abgelegten Skizze mitgeht: **abgelegt ist nicht gerechnet.**
#:
#: **Er steht hier und nicht in der Seite**, weil er eine Aussage über die Bibliothek ist
#: und keine über die Anzeige. *Eine Bestellung, die angenommen und nicht ausgeliefert
#: wird, ist schlimmer als eine abgelehnte: Die Ablehnung sieht man.* Angenommen wird sie
#: trotzdem — die Zeichnung ist das, was der Mensch getan hat, und sie geht nicht
#: verloren, nur weil die Maschine sie noch nicht einlösen kann.
#:
#: **Seit dem 22.09.2026 gibt es den Weg zum Rechnen** (``POST /api/rechne-skizze``, über
#: :func:`aiimaging.arbeitsgang.rechne_skizze`). Nichts rechnet von selbst (Entscheid 11);
#: und auf dem Vorgabe-Bildmodell kommt die Zeichnung beim Rechnen **nicht an** — das steht
#: dann als Hinweis am Bild, nicht nur hier.
HINWEIS_SKIZZE_OHNE_WEG = (
    "Abgelegt, aber NICHT gerechnet: Die Zeichnung liegt in der Mappe und wartet, bis "
    "jemand «Rechnen lassen» wählt. Auf dem Vorgabe-Bildmodell kommt sie dabei nicht an "
    "(gemessen, auf-20260919-123) — das Bild trägt dann den Hinweis «Skizze nicht "
    "angekommen».")


#: Die acht Byte, an denen ein PNG erkennbar ist. **Am Inhalt, nicht an der Endung** —
#: derselbe Grundsatz wie am Einlass für die Modelldateien: Der Name kommt von aussen,
#: was wirklich da ist, sagen die Bytes.
PNG_KENNUNG = b"\x89PNG\r\n\x1a\n"


def pruefe_skizzenbytes(roh_base64: str) -> bytes:
    """Aus dem, was der Browser schickt, die Bytes der Zeichnung — oder eine Absage.

    **Eigene Funktion, damit eine Probe sie rufen kann.** Der erste Wurf hatte diese drei
    Prüfungen im Anfragebehandler stehen, und die Probe darüber verglich nur die
    Reihenfolge im Quelltext. Eine Mutationsprobe hat den Grössenriegel danach
    ausgeschaltet — **die Probe blieb grün**, denn die Zeile stand ja noch da, sie tat nur
    nichts mehr.

        *Ein Wächter, der die Stellung einer Zeile prüft statt ihrer Wirkung, prüft den
        Text und nicht das Programm.*

    Raises:
        FlaechenError: mit dem Satz, der dem Menschen gesagt wird.
    """
    try:
        bytes_ = base64.b64decode(roh_base64, validate=True)
    except (ValueError, binascii.Error):
        raise FlaechenError(
            "Die Zeichnung liess sich nicht lesen — sie kam nicht als gültiges "
            "Base64 an.") from None

    if not bytes_.startswith(PNG_KENNUNG):
        raise FlaechenError(
            "Was ankam, ist kein PNG. Die Fläche legt nur ab, was sie auch erkennt.")

    if len(bytes_) > SKIZZE_GROESSENRIEGEL:
        raise FlaechenError(
            f"Die Zeichnung ist {len(bytes_) // 1024} KB gross, erlaubt sind "
            f"{SKIZZE_GROESSENRIEGEL // 1024}. Ein Riegel, der erst beim Schreiben "
            f"greift, hat schon geschrieben.")

    return bytes_


def _bemerkung(bemerkung, gewuenschter_name) -> str:
    """Die Bemerkung des Menschen — **samt dem Namen, den er der Zeichnung geben wollte.**

    Der Wunschname taugt nicht als Dateiname (siehe :func:`_skizzenname`), aber er ist
    das Einzige, was jemand über seine eigene Zeichnung gesagt hat. *Ihn wegzuwerfen,
    weil er an einer Stelle unbrauchbar ist, wirft ihn auch an der Stelle weg, an der er
    etwas sagt.*
    """
    teile = [str(bemerkung).strip() if bemerkung else ""]
    if gewuenschter_name and str(gewuenschter_name).strip():
        teile.append(f"gewünschter Name: {str(gewuenschter_name).strip()}")
    return " · ".join(t for t in teile if t)


def _stempel() -> str:
    """Der Zeitpunkt im Dateinamen einer Skizze (Weltzeit, auf die Sekunde).

    Eine eigene Funktion, damit eine Probe zwei Skizzen **in dieselbe Sekunde** legen
    kann — der Fall, um den es in :func:`_skizzenname` geht, ist sonst Glückssache.
    """
    return time.strftime("%Y%m%d-%H%M%S", time.gmtime())


def _skizzenname(gewuenscht, belegt=()) -> str:
    """Ein Dateiname für eine Zeichnung — **aus dem Zeitpunkt, nie aus dem Wunsch.**

    Der Wunsch kommt aus einem Browser und damit von aussen. Ihn als Dateinamen zu
    nehmen hiesse, jemand anderem zu erlauben, zu bestimmen, wo geschrieben wird —
    dieselbe Lücke, die :func:`bildpfad` beim Lesen schliesst, nur in die andere
    Richtung.

    Er geht darum **nicht verloren, sondern in die Bemerkung**: Was der Mensch gemeint
    hat, bleibt lesbar; was auf die Platte geschrieben wird, bestimmt diese Funktion.

    **Und der Name ist eindeutig** (Befund 22.09.2026): Bis dahin hiess jede Skizze einer
    Sekunde gleich, und die zweite überschrieb die erste **still** — Datei weg, Mappe mit
    zwei Einträgen auf dieselbe Zeichnung. Ist der Name in ``belegt``, bekommt er eine
    Nummer (``skizze-…-2.png``). Dass die Datei nicht schon auf der Platte liegt, sichert
    erst das Schreiben selbst (:func:`_lege_skizze_ab`) — ein Nachsehen vorher wäre ein
    Blick, zwischen dem und dem Schreiben ein anderer schreiben kann.
    """
    grund = f"skizze-{_stempel()}"
    name, nummer = f"{grund}.png", 2
    while name in belegt:
        name, nummer = f"{grund}-{nummer}.png", nummer + 1
    return name


def _lege_skizze_ab(ordner: Path, bytes_: bytes, belegt) -> Path:
    """Die Zeichnung unter einem **neuen** Namen schreiben — nie über eine vorhandene.

    Geschrieben wird mit ``"xb"``: Das Betriebssystem legt die Datei nur an, wenn es sie
    noch nicht gibt, und sagt es sonst (``FileExistsError``). Dann kommt die nächste
    Nummer. *Ein Nachsehen, ob der Name frei ist, und ein Schreiben danach sind zwei
    Schritte; «anlegen, wenn frei» ist einer.*
    """
    belegt = set(belegt)
    for _ in range(1000):
        ziel = ordner / _skizzenname(None, belegt)
        try:
            with open(ziel, "xb") as datei:
                datei.write(bytes_)
        except FileExistsError:
            belegt.add(ziel.name)
            continue
        return ziel
    raise OSError("Für diese Sekunde gibt es schon tausend Skizzen — kein freier Name.")


def _belegte_namen(p: dict) -> set:
    """Was die Mappe schon nennt — Skizzen und Bilder. Auch eine Datei, die fehlt, bleibt
    belegt: Ihr Name zeigt in der Mappe weiter auf sie."""
    namen = {str(e.get("skizze")) for e in (p.get("skizzen") or []) if isinstance(e, dict)}
    namen |= {str(e.get("bild")) for e in (p.get("bilder") or []) if isinstance(e, dict)}
    return namen


#: Welche Form ein Schlüssel gegen Doppelsendung haben darf: 8 bis 128 Zeichen aus
#: Buchstaben, Ziffern, Punkt, Bindestrich, Unterstrich. Eine UUID der App passt; ein
#: Schlüssel wie «1» nicht — er wäre nicht eindeutig, und genau das ist seine Aufgabe.
SCHLUESSEL_FORM = re.compile(r"[A-Za-z0-9._-]{8,128}")


class Eingangsbuch:
    """Welche Skizzen-Schlüssel schon angekommen sind — **und was ihnen geantwortet wurde.**

    **Der Anlass** (Entscheid 12/28, Parkfach der App): Das iPad schickt eine Skizze, die
    Verbindung reisst, bevor die Antwort ankommt. Das Gerät weiss nicht, ob sie drüben
    liegt, und schickt sie noch einmal. Ohne dieses Buch lägen dann zwei Dateien in der
    Mappe, und der Mensch sähe dieselbe Zeichnung doppelt in der Warteschlange.

    Mit ihm gilt: **Derselbe Schlüssel zweimal → dieselbe Antwort, keine zweite Datei.**
    Derselbe Schlüssel mit einer **anderen** Zeichnung wird abgewiesen — sonst ginge die
    zweite Zeichnung still verloren, weil sie für eine Wiederholung gehalten wurde.

    **Was es NICHT leistet, und es steht hier, damit es niemand für geleistet hält:** Das
    Buch liegt im Arbeitsspeicher. Nach einem Neustart des Servers erkennt es keinen
    Schlüssel wieder, und eine Wiederholung legt dann eine zweite Datei an. Dafür müsste
    der Schlüssel in der Mappe stehen — an der Skizze, über
    :func:`aiimaging.projekt.vermerke_skizze`, also in der Bibliothek und nicht hier
    (offener Posten an den Kern, 22.09.2026). Es behält die letzten
    :data:`HOECHSTENS` Schlüssel.
    """

    HOECHSTENS = 512

    def __init__(self):
        # EINE SPERRE UEBER DAS GANZE ABLEGEN, nicht nur ueber das Nachschlagen: Sonst
        # saehen zwei gleichzeitige Wiederholungen beide «noch nicht da» und legten beide ab.
        self.sperre = threading.Lock()
        self._eintraege: OrderedDict = OrderedDict()

    @staticmethod
    def _schluessel(ordner, schluessel: str) -> tuple:
        return (str(Path(ordner).resolve()), schluessel)

    def nachsehen(self, ordner, schluessel: str):
        """``(abdruck, antwort)`` des ersten Eingangs, oder ``None``."""
        return self._eintraege.get(self._schluessel(ordner, schluessel))

    def vermerke(self, ordner, schluessel: str, abdruck: str, antwort: dict) -> None:
        k = self._schluessel(ordner, schluessel)
        self._eintraege[k] = (abdruck, dict(antwort))
        self._eintraege.move_to_end(k)
        while len(self._eintraege) > self.HOECHSTENS:
            self._eintraege.popitem(last=False)


#: Das eine Eingangsbuch dieser Fläche — wie der Laufstand für alle Anfragen dasselbe.
EINGANG = Eingangsbuch()


#: Der Name, unter dem sich ein Mensch anmeldet. Ein Name allein schützt nichts — er
#: steht hier, weil ein Browser bei der einfachen Anmeldung nach beidem fragt.
#: Der Weg, über den ein Gerät zum ersten Mal hereinkommt — der einzige ohne Anmeldung.
WEG_VERBINDEN = "/api/verbinden"

# DIE UEBRIGEN WEGE, je als Konstante. Sie stehen hier, damit die Gegenseite (die
# iPad-App, `ipad/VisboxKern/.../Wege.swift`) gegen das MODUL geprueft werden kann und
# nicht gegen einen Suchtreffer im Quelltext (`tests/test_ipad_geruest.py`).
WEG_SEITE = "/"
WEG_SEITE_LANG = "/index.html"
WEG_PROJEKT = "/api/projekt"
WEG_FORTSCHRITT = "/api/fortschritt"
WEG_BILD = "/bild"
WEG_ANLEGEN = "/api/anlegen"
WEG_EINSTELLUNGEN = "/api/einstellungen"
WEG_SKIZZE = "/api/skizze"
WEG_RECHNE = "/api/rechne"
# SEIT DEM 22.09.2026 — die Faehigkeiten, die die Bibliothek fuer die App bekommen hat
# (Entscheide 19, 30, 31, 32). Jeder ruft genau eine Funktion aus `aiimaging`.
WEG_BENENNEN = "/api/benennen"
WEG_ABBRECHEN = "/api/abbrechen"
WEG_RECHNE_SKIZZE = "/api/rechne-skizze"
#: Die Koppelseite (Entscheid 26) — neben ``WEG_VERBINDEN`` der einzige Weg, der ohne
#: Anmeldung durchkommt, und nur, solange eine Kopplung offen ist. Siehe ``_darf_herein``.
WEG_KOPPELN = "/koppeln"

BENUTZER = "visbox"

#: Wie lang ein selbst erzeugtes Kennwort ist. 32 Zeichen aus ``secrets`` sind mehr, als
#: ein Heimnetz je erraten würde, und kurz genug, um es einmal abzutippen.
KENNWORTLAENGE = 32


def erzeuge_kennwort() -> str:
    """Ein Kennwort, das **niemand sich ausgedacht hat.**

    ``secrets`` und nicht ``random``: Der zweite erzeugt Zahlen, die für ein Würfelspiel
    genügen und für ein Kennwort nicht — seine Folge lässt sich aus wenigen Werten
    fortrechnen. *Ein Zufall, der sich fortrechnen lässt, ist keiner.*
    """
    return secrets.token_urlsafe(KENNWORTLAENGE)[:KENNWORTLAENGE]


def pruefe_anmeldung(kopfzeile, kennwort: str | None) -> bool:
    """Darf diese Anfrage herein?

    Args:
        kopfzeile: Der ``Authorization``-Kopf der Anfrage, oder ``None``.
        kennwort: Das erwartete Kennwort. ``None`` heisst **keine Anmeldung verlangt** —
            das ist der Zustand auf ``127.0.0.1``, wo ohnehin nur diese Maschine
            herankommt.

    **Verglichen wird mit** ``hmac.compare_digest`` **und nicht mit** ``==``. Ein
    gewöhnlicher Vergleich bricht beim ersten falschen Zeichen ab und braucht dadurch
    messbar unterschiedlich lange — daraus lässt sich ein Kennwort Zeichen für Zeichen
    erraten, ohne es je ganz zu kennen. *Ein Vergleich, dessen Dauer vom Inhalt abhängt,
    verrät den Inhalt.*

    **Was diese Anmeldung NICHT leistet, und es steht hier, damit es niemand für geleistet
    hält:** Sie läuft über gewöhnliches HTTP. Kennwort und Bilder gehen **unverschlüsselt**
    durch das Netz; wer im selben WLAN mitliest, liest mit. Sie hält Geräte fern, die
    zufällig im selben Netz sind — nicht jemanden, der dort mithört.
    """
    if kennwort is None:
        return True
    if not str(kennwort).strip():
        # NICHT «dann eben keine Anmeldung». Ein leeres Kennwort als «keines» zu lesen
        # macht aus einem Tippfehler eine offene Tuer — und zwar lautlos.
        #
        #     *Die gefaehrlichste Abkuerzung ist die, die aus einem Fehler einen
        #     zulaessigen Zustand macht.*
        #
        # `baue_server` faengt den Fall heute schon. Er steht hier trotzdem, weil diese
        # Funktion auch allein gerufen werden kann — und ein Riegel, der nur an einer von
        # zwei Tueren haengt, bewacht die andere nicht.
        raise FlaechenError(
            "Ein leeres Kennwort ist kein Kennwort. Entweder keines verlangen (None) "
            "oder eines setzen — beides zugleich gibt es nicht.")
    if not kopfzeile or not kopfzeile.startswith("Basic "):
        return False
    try:
        roh = base64.b64decode(kopfzeile[6:], validate=True).decode("utf-8")
    except (ValueError, binascii.Error, UnicodeDecodeError):
        return False
    name, _, gegeben = roh.partition(":")
    # BEIDE VERGLEICHE LAUFEN IMMER. Ein `and` waere hier eine Abkuerzung, die bei
    # falschem Namen frueher zurueckkaeme — und damit wieder eine Dauer, die etwas verraet.
    stimmt_name = hmac.compare_digest(name, BENUTZER)
    stimmt_wort = hmac.compare_digest(gegeben, kennwort)
    return stimmt_name and stimmt_wort


class Laufstand:
    """Was ein laufender Auftrag von sich preisgibt — **und was er ausdrücklich nicht weiss.**

    **Der Anlass:** Ein Lauf über die Kette dauert Minuten und meldete bis zum 21.09.2026
    gar nichts, bis er fertig war. Die Seite stand still.

        *Ein Fortschritt, den niemand sieht, sieht aus wie ein Absturz.*

    **Die Auflage, um die es dabei geht, ist aber eine andere**, und sie ist die
    eigentliche Arbeit an dieser Klasse: Es gibt in diesem Projekt **zwei** Sorten von
    Lebenszeichen, und sie dürfen nie gleich aussehen.

    ``belegt``
        Gezählte Diffusionsschritte. Es steht fest, wie viele es insgesamt sind, und jeder
        einzelne wurde wirklich gerechnet. Hier ist ein Anteil ehrlich.

    ``unbelegt``
        Ein Knoten läuft — mehr ist nicht bekannt. Ein Blender-Lauf meldet ein
        *Lebens*zeichen und keinen Fortschritt; wie weit er ist, weiss niemand.

    **Darum gibt es hier keinen Prozentsatz über den ganzen Lauf.** Er müsste die Dauer
    der Knoten gegeneinander gewichten, und die ist nicht bekannt — eine Zahl, die
    aussähe wie eine Messung und geraten wäre. *Ein erfundener Balken ist dasselbe wie
    ein grünes Abzeichen an einem ungeprüften Bild.*
    """

    def __init__(self):
        self.sperre = threading.Lock()
        self.laeuft = False
        self.ordner = None
        self.begonnen = None
        self.knoten = None
        self.knotenart = None
        self.nummer = None
        self.von = None
        self.knoten_begonnen = None
        self.schritt = None
        self.schritte_gesamt = None
        self.fertige = []
        self.ergebnis = None
        self.fehler = None
        # ABGEBROCHEN WIRD ZWISCHEN ZWEI KNOTEN (Entscheid 31). Das Feld sagt nur, dass es
        # VERLANGT ist; ob es gewirkt hat, steht nach dem Lauf in `ergebnis.abgebrochen`.
        # Kam der Wunsch nach dem letzten Knoten, lief der Lauf regulaer zu Ende — und das
        # darf nicht aussehen wie ein Abbruch.
        self.abbruch = False
        #: Bei einer Variantenreihe: ``{nummer, von, gruppe}`` der laufenden Variante.
        self.variante = None
        #: Was bestellt ist: ``{art, entwurf, varianten, skizzen}`` — zur Anzeige.
        self.bestellung = None

    # ------------------------------------------------------------------ schreiben
    def beginne(self, ordner, schritte_gesamt=None, bestellung=None) -> None:
        with self.sperre:
            sperre = self.sperre
            self.__init__()
            # DIESELBE SPERRE BEHALTEN. `__init__` legte eine neue an — und wer die alte
            # gerade haelt (dieser Aufruf), gaebe danach eine Sperre frei, die niemand mehr
            # benutzt.
            self.sperre = sperre
            self.laeuft = True
            self.ordner = str(ordner)
            self.begonnen = time.time()
            self.schritte_gesamt = schritte_gesamt
            self.bestellung = dict(bestellung) if bestellung else None

    def verlange_abbruch(self) -> bool:
        """Den Abbruch verlangen. ``False``, wenn gar nichts läuft."""
        with self.sperre:
            if not self.laeuft:
                return False
            self.abbruch = True
            return True

    def abbruch_verlangt(self) -> bool:
        """Die Frage, die die Kette vor jedem Knoten stellt (``abbrechen`` in
        :func:`aiimaging.arbeitsgang.rechne`)."""
        with self.sperre:
            return self.abbruch

    def melde(self, ereignis: dict) -> None:
        """Ein Ereignis aus der Kette. Wird aus dem Rechenfaden gerufen."""
        with self.sperre:
            art = ereignis.get("art")
            if art == "knoten_beginnt":
                self.knoten = ereignis.get("knoten")
                self.knotenart = ereignis.get("knotenart")
                self.nummer = ereignis.get("nummer")
                self.von = ereignis.get("von")
                self.knoten_begonnen = time.time()
                self.schritt = None
            elif art == "knoten_fertig":
                self.fertige.append({
                    "knoten": ereignis.get("knoten"),
                    "knotenart": ereignis.get("knotenart"),
                    # AUCH «abgebrochen» (Entscheid 31): ein Knoten, der wegen des Abbruchs
                    # nicht mehr begann. Er meldet sich fertig, ohne je begonnen zu haben.
                    "status": ereignis.get("status"),
                    "aus_cache": ereignis.get("aus_cache"),
                    "dauer_s": ereignis.get("dauer_s"),
                    "variante": (self.variante or {}).get("nummer"),
                })
                self.schritt = None
            elif art == "schritt":
                self.schritt = ereignis.get("schritt")
            elif art == "variante_beginnt":
                # EINE NEUE VARIANTE: Die Knotennummern beginnen wieder bei eins, und der
                # Schrittzaehler auch. Ohne dieses Feld saehe die zweite Variante aus wie
                # ein Lauf, der rueckwaerts geht.
                self.variante = {"nummer": ereignis.get("nummer"),
                                 "von": ereignis.get("von"),
                                 "gruppe": ereignis.get("gruppe")}
                self.knoten = None
                self.knotenart = None
                self.nummer = None
                self.von = None
                self.schritt = None

    def beende(self, ergebnis=None, fehler=None) -> None:
        with self.sperre:
            self.laeuft = False
            self.ergebnis = ergebnis
            self.fehler = fehler
            self.knoten = None
            self.schritt = None

    # ---------------------------------------------------------------------- lesen
    def sicht(self) -> dict:
        """Was die Seite anzeigt — **mit der Herkunft jeder Angabe.**"""
        with self.sperre:
            jetzt = time.time()
            belegt = self.schritt is not None and bool(self.schritte_gesamt)
            return {
                "laeuft": self.laeuft,
                "ordner": self.ordner,
                "seit_s": round(jetzt - self.begonnen, 1) if self.begonnen else None,
                "knoten": self.knoten,
                "knotenart": self.knotenart,
                "nummer": self.nummer,
                "von": self.von,
                "knoten_seit_s": (round(jetzt - self.knoten_begonnen, 1)
                                  if self.knoten_begonnen and self.laeuft else None),
                "schritt": self.schritt,
                "schritte_gesamt": self.schritte_gesamt,
                # DIE HERKUNFT DES LEBENSZEICHENS, und sie steht als eigenes Feld da.
                # Eine Anzeige, die «laeuft» und «ist bei Schritt 5 von 8» gleich
                # darstellt, behauptet Fortschritt, wo nur Leben ist.
                "art_des_zeichens": "belegt" if belegt else "unbelegt",
                "fertige": list(self.fertige),
                "ergebnis": self.ergebnis,
                "fehler": self.fehler,
                "abbruch_verlangt": self.abbruch,
                "variante": dict(self.variante) if self.variante else None,
                "bestellung": dict(self.bestellung) if self.bestellung else None,
            }


#: Der eine Laufstand dieser Fläche. Es gibt **einen** Lauf zur Zeit, und das ist eine
#: Entscheidung: Zwei gleichzeitige Läufe auf derselben Mappe schrieben beide in dieselbe
#: Projektdatei, und der zweite überschriebe die Bilder des ersten.
LAUFSTAND = Laufstand()


class FlaechenError(Exception):
    """Eine Anfrage, die diese Fläche nicht beantwortet — mit einem Satz für einen Menschen."""


def bildpfad(ordner, name: str) -> Path:
    """Den Pfad zu einem Bild **innerhalb** des Projektordners — oder eine Absage.

    **Warum diese Funktion so viel Text hat für drei Zeilen Arbeit.** Von dem Augenblick
    an, in dem diese Fläche Dateien ausliefert, entscheidet sie darüber, was von der
    Platte dieses Rechners in einen Browser geht. Sie hört zwar nur auf ``127.0.0.1`` —
    aber *eine zweite Sperre, die nur dann nötig wird, wenn die erste fällt, ist genau die
    Sperre, die man baut, solange nichts passiert ist.*

    Vier Absagen, und jede fängt etwas anderes:

    **1 · Kein absoluter Pfad.** ``/etc/passwd`` als Name wäre sonst ein gültiger Name.
    ``Path.joinpath`` ersetzt bei einem absoluten Teil den ganzen bisherigen Pfad —
    aus ``ordner / "/etc/passwd"`` wird ``/etc/passwd``, ohne dass irgendetwas auffällt.

    **2 · Kein Aufstieg.** ``..`` in irgendeinem Teil führt aus dem Ordner heraus.

    **3 · Danach trotzdem noch einmal nachsehen, wohin es wirklich zeigt.** Die ersten
    beiden Prüfungen lesen den *Namen*; ein Verweis (Symlink) im Ordner kann trotzdem
    irgendwohin zeigen. ``resolve()`` folgt ihm, und erst das Ergebnis wird verglichen.
    *Ein Name sagt, wie etwas heisst, nicht wo es liegt.*

    .. important::
       **Die dritte ist die tragende, und die ersten beiden fangen nichts, was sie
       durchliesse.** Das ist gemessen und nicht vermutet: Eine Mutationsprobe am
       21.09.2026 hat Prüfung 1 und 2 ausgeschaltet — **alle Proben blieben grün**, weil
       ``resolve()`` sowohl den absoluten Pfad als auch den Aufstieg aus dem Ordner
       herausfallen lässt.

       Sie bleiben trotzdem stehen, und zwar aus **einem** Grund: für die **Meldung**.
       Wer ``/etc/passwd`` eingibt, bekommt «zeigt aus dem Projektordner heraus» statt
       eines Satzes über Verweise, die hier keine Rolle spielen.

       *Ein Wächter, der nichts fängt, was der nächste nicht auch fängt, ist kein zweiter
       Wächter. Hier ist er eine bessere Auskunft — und das steht dran, damit ihn niemand
       für Sicherheit hält, die er nicht leistet.*

    **4 · Nur die Endungen aus** :data:`BILDTYPEN`. Die Projektdatei liegt im selben
    Ordner, und sie ist kein Bild.

    Raises:
        FlaechenError: mit dem Satz, der dem Benutzer gesagt wird.
    """
    wurzel = Path(ordner).resolve()
    roh = Path(name)

    if roh.is_absolute() or ".." in roh.parts:
        raise FlaechenError(
            f"{name!r} zeigt aus dem Projektordner heraus. Diese Fläche liefert nur, was "
            f"im Projekt selbst liegt.")

    ziel = (wurzel / roh).resolve()
    if ziel != wurzel and wurzel not in ziel.parents:
        raise FlaechenError(
            f"{name!r} liegt nicht im Projektordner. (Ein Verweis darin kann anderswohin "
            f"zeigen — darum wird der aufgelöste Pfad verglichen, nicht der Name.)")

    if ziel.suffix.lower() not in BILDTYPEN:
        raise FlaechenError(
            f"{ziel.suffix or 'ohne Endung'} wird nicht als Bild ausgeliefert. "
            f"Erlaubt sind: {', '.join(sorted(BILDTYPEN))}.")

    if not ziel.is_file():
        raise FlaechenError(
            f"{name!r} steht in der Mappe, die Datei gibt es nicht (mehr). Das Projekt "
            f"nennt sie weiter — gelöscht wird hier nichts hinter dem Rücken.")

    return ziel



# ======================================================================================
# Was die Fläche zu sehen bekommt — und es kommt vollständig aus der Bibliothek
# ======================================================================================

def _knotenbaum(graph) -> list[dict]:
    """Der Knotenbaum in der Reihenfolge, in der gerechnet wird.

    **Die Reihenfolge kommt aus dem Graphen selbst** (``topologische_reihenfolge``) und
    nicht aus einer Sortierung hier. Eine eigene Reihenfolge wäre eine zweite Wahrheit
    darüber, was wann gerechnet wird — und sie sähe genauso plausibel aus.
    """
    return [{"id": kid,
             "art": graph.knoten[kid].art,
             "eingaenge": list(graph.knoten[kid].eingaenge),
             # Die Parameter werden GEZEIGT und nicht gedeutet. Was davon eine Einstellung
             # ist und was eine Ableitung, weiss die Bibliothek; hier steht es, wie es ist.
             "params": {k: v for k, v in sorted(graph.knoten[kid].params.items())}}
            for kid in graph.topologische_reihenfolge()]


#: Was der Aufrufer **nicht** einstellt, weil das Projekt es selbst weiss.
#:
#: Sie kommen aus dem Import und stehen in der Mappe. Sie hier anzubieten hiesse, zwei
#: Quellen für dieselbe Angabe zu haben — und die falsche gewänne genau dann, wenn
#: jemand sie einmal angefasst und danach vergessen hat.
NICHT_EINSTELLBAR = ("ifc_path", "glb_path", "bbox")


def _angeboten(name: str, einstellungen: dict) -> bool:
    """Ob die Flaeche ein Feld der Kette anbietet.

    Die Messschalter (:data:`aiimaging.kette.MESSSCHALTER`) erschienen am 23.09.2026 von
    selbst als gewoehnliche Felder, weil diese Datei die Felder aus der Kette liest. Sie
    sind fuer Messungen, nicht fuer den Alltag — **aber ein gesetzter Schalter bleibt
    sichtbar.** Eine Mappe, die anders rechnet, als ihre Anzeige sagt, waere schlimmer
    als ein Feld zu viel.
    """
    if name in NICHT_EINSTELLBAR:
        return False
    return name not in kette.MESSSCHALTER or name in einstellungen


def _probewert(vorgabe, annotation=""):
    """Ein Wert, mit dem sich ausprobieren lässt, wo ein Feld landet.

    Er wird nie gespeichert und nie gerechnet — er dient einem Bau, der sofort verworfen
    wird. Der Typ folgt der Vorgabe; ist sie ``None``, folgt er der **Annotation**, denn
    ``baue_kette`` rechnet manche Felder beim Bauen um (``float(hintergrund)``), und ein
    Text scheitert dort.
    """
    if isinstance(vorgabe, bool):
        return not vorgabe
    if isinstance(vorgabe, (int, float)):
        return vorgabe + 1
    if isinstance(vorgabe, str):
        return vorgabe + " " if vorgabe else "probe"
    if vorgabe is None:
        text = str(annotation)
        if "bool" in text:
            return True
        if "float" in text:
            return 0.5
        if "int" in text:
            return 2
    return "probe"


#: Ein Feld wirkt auf **einen** Knoten — dort steht seine Knoten-ID.
WIRKT_AUF_KNOTEN = "knoten"
#: Es entscheidet, **welche Knoten es gibt** (``qa`` schaltet die Prüfung ab).
WIRKT_AUF_BAU = "bau"
#: Die Probe hat **nichts** gesehen. *Weder ja noch nein* — die dritte Antwort, angewandt
#: auf die Frage, wo ein Bedienfeld hingehört.
WIRKT_UNBEKANNT = "unbekannt"


def _wo_landet(einstellungen: dict, graph, glb: str | None) -> dict[str, tuple]:
    """Welches Feld wirkt wo — **ausprobiert, am Wert erkannt, und ehrlich, wenn nicht.**

    Drei Anläufe waren nötig, und alle drei Fehlschläge sind dieselbe Familie:

    **1 · Den gebauten Graphen ablesen.** Zu schwach: Ein Feld, das noch nicht gesetzt
    ist, steht in keinem Knoten. **16 von 34** landeten im Sammelbecken, darunter der
    Sonnenstand — *und das Unbenutzte ist genau das, was jemand als Nächstes sucht.*

    **2 · Je Feld bauen und die Parameter-NAMEN vergleichen.** Besser (16 → 4), aber blind
    für jedes Feld, das im Knoten anders heisst: ``qa_schwelle`` landet dort als
    ``schwelle``.

    **3 · Die Werte vergleichen.** Findet auch die umbenannten — und deckte dabei zwei
    eigene Fehler auf, die bis dahin unter «kein Knoten» verschwunden waren:

    * ``up_axis`` wurde mit dem Probewert ``"Y "`` gebaut, und die Prüfung normalisiert ihn
      zu ``"Y"`` zurück. **Es änderte sich nichts**, und das Feld galt als wirkungslos.
      *Eine Probe, deren Wert unterwegs zurückverwandelt wird, misst nicht die Wirkung,
      sondern die Normalisierung.*
    * ``qa=False`` **entfernt den Prüfknoten**. Ein Vergleich, der nur die vorhandenen
      Knoten ansieht, bemerkt einen entfallenen nicht.

    Beides steht jetzt als eigene Antwort da (:data:`WIRKT_AUF_BAU`,
    :data:`WIRKT_UNBEKANNT`) statt in einem Sammelbecken, in dem drei verschiedene Gründe
    gleich aussahen.

    Returns:
        ``{name: (wohin, knoten_id_oder_None)}``.
    """
    if graph is None or not glb:
        return {}

    grund = dict(einstellungen)
    grund.pop("ifc_path", None)

    def bild(g) -> dict[str, dict]:
        return {kid: dict(g.knoten[kid].params) for kid in g.knoten}

    vorher = bild(graph)
    wo: dict[str, tuple] = {}
    for name, p in inspect.signature(kette.baue_kette).parameters.items():
        if not _angeboten(name, einstellungen):
            continue
        vorgabe = None if p.default is inspect.Parameter.empty else p.default
        probe = dict(grund)
        probe[name] = _probewert(einstellungen.get(name, vorgabe), p.annotation)
        try:
            nachher = bild(kette.baue_kette(glb_path=glb, **probe))
        except Exception:
            # Ein Feld, dessen Probebau nicht durchgeht, bleibt unbekannt. Es zu raten
            # waere schlimmer als es offenzulassen.
            wo[name] = (WIRKT_UNBEKANNT, None)
            continue

        if set(nachher) != set(vorher):
            # ES GIBT DANACH ANDERE KNOTEN. Das Feld bestimmt die Form des Baums, nicht
            # den Inhalt eines Knotens — und das ist eine eigene Auskunft, keine fehlende.
            wo[name] = (WIRKT_AUF_BAU, None)
            continue

        geaendert = [kid for kid in nachher if nachher[kid] != vorher.get(kid)]
        if len(geaendert) == 1:
            wo[name] = (WIRKT_AUF_KNOTEN, geaendert[0])
        else:
            # KEINE ODER MEHRERE. Wirkt ein Feld auf mehrere Knoten, gehoert es an keinen
            # einzelnen — es unter einen zu schreiben hiesse, die anderen zu verschweigen.
            # Wirkt es auf keinen, hat diese Probe nichts gesehen, und genau das steht da.
            #
            # DER FALL «MEHRERE» IST HEUTE NICHT BELEGT, und das gehoert hierhin statt in
            # eine Zusage: In der jetzigen Kette aendert **kein einziges** Feld mehr als
            # einen Knoten. Die Mutationsprobe dazu faellt darum nicht — `len(...) == 1`
            # durch `if geaendert:` zu ersetzen aendert an keinem Ergebnis etwas.
            #
            #     *Ein Zweig ohne Fall ist kein bewachter Zweig. Er ist eine Vorkehrung,
            #     und sie hier als geprueft auszugeben waere dieselbe Sorte Beruhigung,
            #     gegen die an diesem Tag schon dreimal etwas stand.*
            #
            # Er bleibt trotzdem: Ein Feld, das zwei Knoten anfasst, ist jederzeit
            # baubar, und dann waere die Alternative, es willkuerlich einem zuzuschlagen.
            wo[name] = (WIRKT_AUF_BAU if geaendert else WIRKT_UNBEKANNT, None)
    return wo


def bedienfelder(einstellungen: dict, graph=None, glb: str | None = None) -> list[dict]:
    """Was sich einstellen lässt — **gelesen aus der Bibliothek, nicht hier aufgezählt.**

    Die Namen, die Vorgaben und die Zuordnung zu den Knoten kommen aus
    :func:`aiimaging.kette.baue_kette` und aus dem gebauten Graphen. Eine Liste an dieser
    Stelle wäre in dem Augenblick veraltet, in dem die Bibliothek etwas dazubekommt.

        *Genau so ist am 21.09.2026 die Lücke entstanden, in der elf Bestellungen über
        einen der beiden Wege nicht erreichbar waren.* Eine Oberfläche mit einer
        handgeschriebenen Feldliste macht denselben Fehler ein drittes Mal — und diesmal
        sähe ihn niemand, weil er nur fehlt und nichts kaputtmacht.

    Returns:
        Je Feld ``{name, vorgabe, wert, gesetzt, knoten}``. ``knoten`` ist die Knoten-ID,
        in deren Parametern der Name im **gebauten** Graphen auftaucht, oder ``None`` —
        *dann wirkt das Feld auf den Bau des Graphen und nicht auf einen einzelnen
        Knoten*, und die Fläche sagt das so.
    """
    wo = _wo_landet(einstellungen, graph, glb)

    felder = []
    for name, p in inspect.signature(kette.baue_kette).parameters.items():
        if not _angeboten(name, einstellungen):
            continue
        vorgabe = None if p.default is inspect.Parameter.empty else p.default
        felder.append({
            "name": name,
            "vorgabe": vorgabe if isinstance(vorgabe, (str, int, float, bool, type(None)))
                       else str(vorgabe),
            "wert": einstellungen.get(name),
            # GESETZT IST NICHT DASSELBE WIE «hat einen Wert». Ein Feld, das der Vorgabe
            # entspricht, aber ausdruecklich gesetzt wurde, bleibt gesetzt — sonst
            # verschwaende ein bewusster Entscheid beim naechsten Speichern.
            "gesetzt": name in einstellungen,
            "knoten": wo.get(name, (WIRKT_UNBEKANNT, None))[1],
            # DREI ANTWORTEN STATT EINES SAMMELBECKENS. «Kein Knoten» hiess bisher
            # dreierlei: es formt den Baum, es wirkt auf mehrere, oder wir wissen es
            # nicht. Sie sahen gleich aus, und das ist genau die Verwechslung, gegen die
            # dieses Projekt ueberall sonst anschreibt.
            "wirkt_auf": wo.get(name, (WIRKT_UNBEKANNT, None))[0],
        })
    return felder


def _bild_fuer_die_flaeche(eintrag: dict, ordner=None, *, bilder_der_mappe=None) -> dict:
    """Ein Bildeintrag, wie ihn die Seite braucht — **samt seinem Vorbehalt.**

    Hier steht die einzige Stelle, an der diese Datei etwas *entscheidet*, und sie
    entscheidet nichts über die Sache, sondern über die **Anzeige**: welches der drei
    Zeichen ein Bild bekommt.

        Ein ungeprüftes Bild darf nie aussehen wie ein bestandenes — und auch nicht wie
        gar nichts.

    Der UI-Worker hat am 03.09.2026 genau das gemeldet: Die Bildkachel zeigte bei
    fehlender Prüfung **kein** Abzeichen. *Kein Abzeichen sieht aus wie kein Problem.*

    ``bilder_der_mappe`` sind die Einträge unter ``bilder`` derselben Mappe. Ohne sie
    (und ohne ``ordner``) bleibt ``vorher`` ``None`` — siehe :func:`_vorher`.
    """
    urteil = eintrag.get("geometrie_bestanden")
    basis = eintrag.get("basis") or None

    # OB ES DIE DATEI UEBERHAUPT GIBT, und zwar als eigene Angabe.
    #
    # Seit die Flaeche Bilder ZEIGT, gibt es einen Zustand, den es vorher nicht gab: Die
    # Mappe nennt ein Bild, und die Datei ist weg — verschoben, geloescht, ein Ordner
    # umbenannt. In einer Liste aus Namen sah das aus wie jedes andere Bild.
    #
    #     *Ein Name ohne Datei sieht in einer Liste genauso aus wie einer mit.*
    #
    # `None` heisst hier UNBEKANNT und nicht «weg»: Ohne Ordner ist die Frage nicht
    # gestellt worden. Das ist dieselbe Dreiteilung wie ueberall sonst.
    vorhanden = None
    if ordner is not None and eintrag.get("bild"):
        try:
            bildpfad(ordner, str(eintrag["bild"]))
            vorhanden = True
        except FlaechenError:
            vorhanden = False
    if urteil is True:
        zeichen, satz = "bestanden", "Die Geometrieprüfung ist bestanden."
    elif urteil is False:
        zeichen, satz = "durchgefallen", "Die Geometrieprüfung ist nicht bestanden."
    else:
        zeichen = "nicht-gemessen"
        # DER GRUND KOMMT AUS DEM EINTRAG, nicht aus einem Satz hier. Ein allgemeiner
        # Satz an dieser Stelle waere bequem und in der Haelfte der Faelle falsch.
        satz = (eintrag.get("herkunft") or {}).get("grund") or "NICHT GEMESSEN."
    return {
        "bild": eintrag.get("bild"),
        "schicht": eintrag.get("schicht"),
        "zeichen": zeichen,
        "satz": satz,
        "erzeugt": eintrag.get("erzeugt"),
        "herkunft": eintrag.get("herkunft") or {},
        "vorhanden": vorhanden,
        # DAS GEERBTE URTEIL BLEIBT EIN EIGENES FELD (E20). Es in `zeichen` zu mischen
        # hiesse, ein Bild der zweiten Stufe als geprueft anzuzeigen — genau der Fehler,
        # gegen den dieses Projekt seit Wochen anschreibt.
        "basis": basis,
        # DIE ZAHL ZUM ZEICHEN (Entscheid 16: «Farbe, Wort und Zahl»), aus der Pruefung,
        # die das Urteil gefaellt hat — gelesen, nicht gerechnet. `None` heisst nicht
        # gemessen, auch bei einem aelteren Eintrag, der die Felder nicht fuehrt; nie 0.
        #
        # UND NUR NEBEN EINEM URTEIL (Befund der Durchsicht D-KERN, 22.09.2026): Die
        # Bibliothek schreibt seither keine Zahl mehr ohne Urteil an ein Bild; eine Mappe
        # aus der Zeit davor kann sie aber tragen. Neben «nicht gemessen» laese sie sich
        # wie eine Messung.
        "score": (_zahl_oder_nichts(eintrag.get("score"))
                  if urteil is True or urteil is False else None),
        "schwelle": (_zahl_oder_nichts(eintrag.get("schwelle"))
                     if urteil is True or urteil is False else None),
        # DER EIGENE NAME (Entscheid 19). `None`: benannt nach der Zeit, wie die Datei.
        "titel": eintrag.get("titel"),
        # ENTWURF — NICHT GEPRUEFT (Entscheid 30). Ein eigenes Feld und KEIN viertes
        # Zeichen: `zeichen` bleibt «nicht-gemessen», denn gemessen wurde nicht. Das blaue
        # Zeichen der App entsteht an diesem Feld, nicht an einem Satz, den sie deuten
        # muesste. Aeltere Eintraege fuehren es nicht — dann `None`, nicht «kein Entwurf».
        "entwurf": eintrag.get("entwurf") if isinstance(eintrag.get("entwurf"), bool)
                   else None,
        "variantengruppe": eintrag.get("variantengruppe") or None,
        # DAS VORHER ZUM VERGLEICH (Entscheid 17): das Bild, ueber das skizziert wurde.
        # Seit dem 23.09.2026; die App liest das Feld (`Mappenbild.vorher`).
        "vorher": _vorher(eintrag, ordner, bilder_der_mappe),
        **_hinweise_zum_bild(eintrag),
    }


def _vorher(eintrag: dict, ordner, bilder_der_mappe):
    """Der Name des Bildes, **über das skizziert wurde** — oder ``None``.

    Gelesen aus ``herkunft.unterlage.bild``: Dort legt ``_eingangsbild`` in
    ``src/aiimaging/arbeitsgang.py`` die Unterlage ab, auf die die Skizze gesetzt wurde
    (``skizzen[].ueber`` zur Zeit des Laufs). ``herkunft.skizze`` allein ist **nicht** das Vorher — das wäre die Zeichnung,
    nicht das Bild.

    **Nur der Name eines Bildes, das in dieser Mappe liegt** — sonst ``None``:

    * es steht unter ``bilder`` der Mappe (ein Name, den die Mappe nicht mehr führt, ist
      kein Bild dieser Mappe, auch wenn die Datei noch liegt);
    * :func:`bildpfad` nimmt ihn an — im Projektordner, eine Bildendung, die Datei ist da;
    * er ist nicht das Bild selbst.

    **Nie ein Pfad**: Zurück geht genau der Name, wie er in der Mappe steht, und die App
    holt die Bytes unter ihm über ``GET /bild``. ``None`` heisst: keine Unterlage (auch
    «ohne Unterlage auf Grau»), ein älteres Bild ohne ``herkunft.unterlage``, oder die
    Unterlage ist nicht (mehr) zu haben. Ohne ``ordner`` wird nicht nachgesehen — dann
    ebenfalls ``None`` statt eines ungeprüften Namens.
    """
    herkunft = eintrag.get("herkunft") or {}
    unterlage = herkunft.get("unterlage") if isinstance(herkunft, dict) else None
    name = unterlage.get("bild") if isinstance(unterlage, dict) else None
    if not isinstance(name, str) or not name.strip() or name == eintrag.get("bild"):
        return None
    if ordner is None or not any(isinstance(b, dict) and b.get("bild") == name
                                 for b in (bilder_der_mappe or [])):
        return None
    try:
        bildpfad(ordner, name)
    except FlaechenError:
        return None
    return name


def _zahl_oder_nichts(wert):
    """Eine endliche Zahl, oder ``None``. Ein Wahrheitswert ist hier keine Zahl."""
    if isinstance(wert, bool) or not isinstance(wert, (int, float)):
        return None
    return float(wert) if math.isfinite(float(wert)) else None


#: Der feste Anfang des Satzes, mit dem der Nachrender sagt, dass die Skizze beim Modell
#: nicht ankam — **aus der Bibliothek gelesen**, nicht hier abgeschrieben. Sie hat ihm
#: dafür einen festen Anfang gegeben, «damit eine Anzeige ihn erkennen kann, ohne den
#: Rest zu deuten».
SKIZZE_NICHT_ANGEKOMMEN = kette.HINWEIS_SKIZZE_NICHT_ANGEKOMMEN.split(":")[0]


def _hinweise_zum_bild(eintrag: dict) -> dict:
    """Die Hinweise der Bildstufe am Bild — und ob die Skizze beim Modell ankam.

    ``hinweise`` ist die Liste aus ``herkunft.messung.hinweise``, oder ``None``, wenn der
    Eintrag keine Messung trägt (älter als der 22.09.2026, oder der Knoten meldete
    nichts). **Leer heisst gemessen und ohne Hinweis; ``None`` heisst nicht gemessen.**

    ``skizze_hinweis`` ist der Satz der Bibliothek dazu, oder ``None``.
    ``skizze_nicht_angekommen`` hat drei Antworten:

    * ``True`` — das Bild kam aus einer Skizze, und die Bildstufe sagt, sie kam nicht an
      (Befund ``auf-20260919-123``: Das Vorgabemodell nimmt kein Ausgangsbild an). Das Bild
      ist dann aus Tiefenkarte und Text gerechnet, **was hineingezeichnet war, steckt
      nicht darin** — und genau das muss neben dem Bild stehen.
    * ``False`` — aus einer Skizze, gemessen, und kein solcher Hinweis.
    * ``None`` — kein Skizzenbild, oder nicht gemessen. Die Frage stellt sich nicht bzw.
      ist nicht beantwortet.
    """
    herkunft = eintrag.get("herkunft") or {}
    messung = herkunft.get("messung") if isinstance(herkunft.get("messung"), dict) else None
    roh = (messung or {}).get("hinweise")
    hinweise = [str(h) for h in roh] if isinstance(roh, (list, tuple)) else None
    angekommen, satz = None, None
    if herkunft.get("skizze") and hinweise is not None:
        satz = next((h for h in hinweise if h.startswith(SKIZZE_NICHT_ANGEKOMMEN)), None)
        angekommen = satz is not None
    unterlage = _unterlage_hinweis(herkunft)
    if unterlage is not None and hinweise is not None and unterlage not in hinweise:
        # HINTEN ANGEHAENGT, nicht vorne: Der Satz «SKIZZE NICHT ANGEKOMMEN» steht
        # zuvorderst, und die App verlaesst sich darauf nicht, aber die Webseite zeigt die
        # Liste in dieser Reihenfolge.
        #
        # UND NUR AN EINE LISTE, NIE AN `None`: `hinweise: null` heisst «die Bildstufe
        # hat nichts gemeldet». Ein Satz vom Server machte daraus eine Liste, und die
        # Anzeige sagte nicht mehr «nicht gemessen». Dann traegt ihn `unterlage_hinweis`
        # allein.
        hinweise = hinweise + [unterlage]
    # DER SATZ SELBST GEHT MIT (`skizze_hinweis`), damit die Anzeige ihn nicht an seinem
    # Anfang wiedererkennen muss — der Anfang stuende sonst ein zweites Mal in der Seite.
    return {"hinweise": hinweise, "skizze_nicht_angekommen": angekommen,
            "skizze_hinweis": satz, "unterlage_hinweis": unterlage}


def _unterlage_hinweis(herkunft: dict):
    """Der Satz zur Unterlage eines Skizzenbilds — **nur, wenn er etwas zu sagen hat.**

    Die Bibliothek legt an jedes Bild aus einer Skizze ``herkunft.unterlage`` mit einem
    ``grund`` (``_eingangsbild`` in ``src/aiimaging/arbeitsgang.py``). Bis zum 23.09.2026
    zeigte ihn niemand (Durchsicht der Welle 2): Dass eine Skizze **gestreckt** auf ihr Bild gesetzt wurde oder
    **ohne Unterlage auf Grau** gerechnet, stand nur in der Mappe. Beides ändert, was das
    Bild bedeutet — ein verzerrter Balkon, ein Haus vor einem Grau statt vor seinem Bild.

    Zurück kommt der ``grund`` der Bibliothek, unverändert (derselbe Grundsatz wie beim
    Satz zum Zeichen: *der Grund kommt aus dem Eintrag*), in zwei Fällen:

    * ``gestreckt`` ist ``True``;
    * ``bild`` ist ``None`` — ohne Unterlage, auf Grau.

    Sonst ``None``: kein Skizzenbild, ein älteres ohne ``herkunft.unterlage``, oder Blatt
    auf Bild ohne Streckung — dann gibt es nichts, was neben dem Bild stehen müsste.
    Fehlt der ``grund``, steht ein Satz von hier da, damit der Fall nicht verschwindet.
    """
    u = herkunft.get("unterlage") if herkunft.get("skizze") else None
    if not isinstance(u, dict):
        return None
    grund = u.get("grund") if isinstance(u.get("grund"), str) and u.get("grund") else None
    if u.get("gestreckt") is True:
        return grund or ("Die Skizze wurde auf ihre Unterlage GESTRECKT — sie hat nicht "
                         "dasselbe Seitenverhältnis wie das Bild.")
    if "bild" in u and u.get("bild") is None:
        return grund or "Ohne Unterlage gezeichnet — gerechnet auf neutralem Grau."
    return None


def grundriss(glb, up_axis) -> dict:
    """Die Hüllbox des **Bauwerks** — damit ein Mensch den Standpunkt anklicken kann.

    Bis zum 21.09.2026 war der Standpunkt über diese Fläche nur als **drei getippte
    Zahlen** erreichbar. Das ist derselbe Satz wie immer, nur von der anderen Seite:

        *Was nur über das Eintippen von Koordinaten erreichbar ist, wird nicht benutzt.*

    Gelesen wird mit :func:`aiimaging.glbbox.bauwerksbox` — **ohne Blender**, hier, in
    Sekundenbruchteilen. Zurück kommt die Box in Weltkoordinaten mit Z oben; der Grundriss
    ist damit die X/Y-Ebene und die Höhe Z.

    Returns:
        ``{bbox, grund, schrumpfung}``. ``bbox`` ist ``None``, wenn sich nichts lesen
        liess — **und ``grund`` sagt dann warum.** Eine leere Fläche ohne Grund sähe aus
        wie ein Fehler der Anzeige.
    """
    if not glb:
        return {"bbox": None, "grund": "Dieses Projekt hat keine umgewandelte Geometrie.",
                "schrumpfung": None}
    if not up_axis:
        return {"bbox": None, "schrumpfung": None,
                "grund": ("Welche Achse oben ist, steht für dieses Modell nicht fest — "
                          "ohne das lässt sich kein Grundriss zeichnen. Oben unter "
                          "up_axis 'Y' oder 'Z' angeben.")}
    try:
        befund = glbbox.bauwerksbox(glb, up_axis=up_axis)
    except glbbox.GlbError as fehler:
        # DER SATZ DER BIBLIOTHEK, unveraendert. Er erklaert unter anderem, warum es fuer
        # Z-up keine geratene Umrechnung gibt.
        return {"bbox": None, "grund": str(fehler), "schrumpfung": None}
    except OSError as fehler:
        return {"bbox": None, "grund": f"Die glb liess sich nicht lesen: {fehler}",
                "schrumpfung": None}

    return {
        "bbox": befund.get("bbox_bauwerk"),
        # DIE SZENENBOX WIRD NICHT ERSATZWEISE GENOMMEN. Sie enthaelt das Gelaende, und
        # ein Grundriss, in dem das Bauwerk ein Fleck in einer Wiese ist, laedt zu einem
        # Standpunkt ein, der am Haus vorbeisieht.
        "grund": befund.get("note") or "",
        "schrumpfung": befund.get("schrumpfung"),
    }


def sicht(ordner) -> dict:
    """Alles, was die Seite über ein Projekt zeigt — in einem Stück.

    Raises:
        projekt.ProjektError: Kein Projekt an diesem Ort. Der Satz geht unverändert an die
            Seite; er ist für einen Menschen geschrieben und braucht hier keine zweite
            Fassung.
    """
    auf = projekt.oeffne(ordner)
    p = auf["projekt"]
    einfuhr = p.get("import") or {}

    # DER KNOTENBAUM WIRD GEBAUT, NICHT GESPEICHERT. Er ist keine Eigenschaft des
    # Projekts, sondern eine der Einstellungen — und er soll zeigen, was beim NAECHSTEN
    # Lauf gerechnet wuerde, nicht was beim letzten gerechnet wurde.
    # DIE ANGABE IN DER MAPPE IST RELATIV — hier wird sie wieder zu einem Pfad auf
    # dieser Platte. Siehe `projekt.loese_pfad`.
    glb = str(projekt.loese_pfad(einfuhr.get("glb"), ordner)) if einfuhr.get("glb") else None

    baum, baum_fehler, graph = [], None, None
    if glb:
        args = dict(p.get("einstellungen") or {})
        args.pop("ifc_path", None)
        if not args.get("up_axis") and einfuhr.get("hochachse_steht_fest"):
            args["up_axis"] = einfuhr["hochachse"]
        try:
            graph = kette.baue_kette(glb_path=glb, **args)
            baum = _knotenbaum(graph)
        except kette.KettenError as fehler:
            # NUR DER SATZ, OHNE DEN TYPNAMEN. Die Fehler der Bibliothek sind fuer einen
            # Menschen geschrieben — «prompt fehlt oder ist leer … ohne ihn ist nicht
            # beschrieben, was entstehen soll». Ein vorangestelltes `KettenError:` macht
            # daraus wieder eine Programmmeldung, und die Zielgruppe hoert bei
            # Programmmeldungen auf zu lesen.
            baum_fehler = str(fehler)
        except Exception as fehler:
            # ALLES ANDERE MIT TYPNAMEN, und das ist kein Widerspruch: Ein Fehler, den
            # dieses Projekt nicht vorhergesehen hat, ist fuer niemanden geschrieben. Dann
            # ist der Typ die einzige Spur, und sie wegzulassen hiesse, die Fehlersuche
            # gegen die Lesbarkeit einer Meldung zu tauschen, die ohnehin nicht hilft.
            baum_fehler = f"{type(fehler).__name__}: {fehler}"

    return {
        "name": p.get("name"),
        "ordner": str(ordner),
        # DIE STANDNUMMER DER MAPPE (22.09.2026). Wer benennt, schickt sie als `von_stand`
        # zurueck — dann wird abgewiesen statt ueberschrieben, wenn inzwischen jemand
        # anderes geschrieben hat (`projekt.benenne`). `None`: eine Mappe von vorher.
        "stand_nr": p.get("stand_nr") if isinstance(p.get("stand_nr"), int) else None,
        "modell": {
            "pfad": (p.get("modell") or {}).get("pfad"),
            "stand": auf["modell_stand"],
            "grund": auf["modell_grund"],
            "einlass": (p.get("modell") or {}).get("einlass") or {},
        },
        "import": einfuhr,
        "einstellungen": p.get("einstellungen") or {},
        "knotenbaum": baum,
        "knotenbaum_fehler": baum_fehler,
        "bedienfelder": bedienfelder(p.get("einstellungen") or {}, graph, glb=glb),
        "bilder": [_bild_fuer_die_flaeche(b, ordner, bilder_der_mappe=p.get("bilder") or [])
                   for b in (p.get("bilder") or [])],
        # DIE SKIZZEN, unveraendert aus der Mappe. Kein Urteil, keine Umrechnung — die
        # Flaeche reicht durch, was die Bibliothek fuehrt.
        "skizzen": p.get("skizzen") or [],
        # DER GRUNDRISS, damit der Standpunkt anklickbar wird statt tippbar.
        "grundriss": grundriss(
            glb,
            (p.get("einstellungen") or {}).get("up_axis")
            or (einfuhr.get("hochachse") if einfuhr.get("hochachse_steht_fest") else None)),
        "laeufe": p.get("laeufe") or [],
        # WAS DIESE FLAECHE NICHT KANN, steht in ihr selbst und nicht nur im LIESMICH.
        # Eine Flaeche, die ihre Grenzen nur in einer Datei daneben nennt, hat sie fuer
        # ihren Benutzer nicht genannt.
        "formate": sorted(importeur.WEGE),
    }


# ======================================================================================
# Der Anschluss — die Wege, und jeder ruft genau eine Funktion der Bibliothek
# ======================================================================================

#: Welcher POST-Weg welche Methode von :class:`Flaeche` ruft — **eine Tafel statt einer
#: Kette aus ``if``/``elif``.**
#:
#: Der Anlass ist kein Stil, sondern die Arbeitsteilung (22.09.2026): Mehrere Einheiten
#: bekommen neue Wege, und jede davon haette dieselbe Kette an derselben Stelle
#: verlaengert. Zwei solche Aenderungen stossen beim Zusammenfuehren zusammen, und die
#: haeufigste Aufloesung verliert einen Zweig — der Weg ist dann gebaut und antwortet
#: 404. *Genau das ist diesem Projekt mit dem ersten Verbinden schon einmal passiert.*
#: Eine Tafel bekommt je Weg **eine eigene Zeile**; zwei neue Zeilen stossen nicht
#: zusammen.
#:
#: Eingetragen wird der **Methodenname** und nicht die Methode selbst: So bleibt die Tafel
#: oberhalb der Klasse lesbar, und ``tests/test_ipad_geruest.py`` prueft, dass jeder Name
#: wirklich eine Methode ist.
WEGTAFEL = {
    WEG_ANLEGEN: "_anlegen",
    WEG_EINSTELLUNGEN: "_einstellungen",
    WEG_SKIZZE: "_skizze",
    WEG_RECHNE: "_rechne",
    WEG_VERBINDEN: "_verbinden",
    WEG_BENENNEN: "_benennen",
    WEG_ABBRECHEN: "_abbrechen",
    WEG_RECHNE_SKIZZE: "_rechne_skizze",
}

#: Dasselbe fuer die lesenden Wege (GET). Jede Methode bekommt den zerlegten Weg
#: (``urllib.parse.urlparse``) und liest daraus, was sie braucht.
WEGTAFEL_LESEN = {
    WEG_SEITE: "_seite",
    WEG_SEITE_LANG: "_seite",
    WEG_PROJEKT: "_projekt",
    WEG_FORTSCHRITT: "_fortschritt",
    WEG_BILD: "_bild_anfrage",
    WEG_KOPPELN: "_koppelseite",
}


class Flaeche(BaseHTTPRequestHandler):
    """Übersetzt Anfragen in Bibliotheksaufrufe. Mehr tut sie nicht."""

    ordner: Path | None = None
    kennwort: str | None = None
    #: Die offene Kopplung fuer das erste Verbinden, oder ``None``.
    #:
    #: Sie liegt auf der KLASSE und nicht in einer Anfrage: Alle Anfragen teilen sie
    #: sich, und genau das ist gewollt — der Versuchszaehler ist nur dann eine Schranke,
    #: wenn er fuer alle derselbe ist. *Ein Zaehler je Verbindung zaehlt nichts.*
    kopplung_offen = None
    sys_version = ""

    @property
    def server_version(self) -> str:
        """Der Kopf ``Server`` jeder Antwort — der Name aus :data:`NAME`, nicht fest
        eingeschrieben (Durchsicht der Welle 2, 22.09.2026). Eine Eigenschaft statt eines
        Klassenfelds, weil :data:`NAME` erst weiter unten in dieser Datei entsteht."""
        return NAME

    # ------------------------------------------------------------------- die Tuer
    def _darf_herein(self) -> bool:
        """Jede Anfrage geht hier durch — **auch die nach der Seite selbst.**

        Eine Anmeldung, die nur die Daten schützt und die Seite freigibt, schützt nichts:
        Die Seite fragt die Daten ja gerade ab. *Eine Tür, die nur einen von zwei Wegen
        bewacht, ist keine Tür.*
        """
        if pruefe_anmeldung(self.headers.get("Authorization"), self.kennwort):
            return True

        # DER EINE WEG, DER UNANGEMELDET DURCHDARF — und er ist der Weg HINEIN.
        #
        # Ohne ihn gaebe es kein erstes Verbinden: Wer das Kennwort noch nicht hat, kommt
        # an nichts heran, was es ihm geben koennte. Die Oeffnung ist darum so eng wie
        # moeglich gefasst und an vier Bedingungen gebunden:
        #
        #   1. nur dieser eine Pfad,
        #   2. nur POST — ein Aufruf aus der Adresszeile erreicht ihn nicht,
        #   3. nur, solange eine Kopplung offen ist (ohne `--kopplung` gibt es sie nicht),
        #   4. und was dahinter liegt, zaehlt jeden Versuch (`aiimaging.kopplung`).
        #
        # *Eine Tuer, die man zum Hereinkommen braucht, laesst sich nicht abschaffen —
        # aber sie laesst sich auf die Breite eines Menschen bringen.*
        if (self.command == "POST"
                and urllib.parse.urlparse(self.path).path == WEG_VERBINDEN
                and self.kopplung_offen is not None):
            return True
        # DIE ZWEITE OEFFNUNG, und sie fuehrt zur ersten (Entscheid 26, 22.09.2026): die
        # Koppelseite fuer einen Browser, der das Kennwort noch nicht hat. Ohne sie haette
        # die Webflaeche kein erstes Verbinden — der Browser fragt nach einem Kennwort, das
        # er nur ueber `WEG_VERBINDEN` bekommt, und dorthin fuehrt ihn nichts.
        #
        # Enger als die erste: nur GET, nur genau dieser Pfad, und nur, solange die Zahl
        # wirklich noch gilt (`kopplung.stand` sagt «offen»). Eine verbrauchte oder
        # abgelaufene Kopplung zeigt keine Seite mehr, auf der man eine tote Zahl eingibt.
        # Die Seite selbst traegt keine Daten — nur ein Zahlenfeld.
        if (self.command == "GET"
                and urllib.parse.urlparse(self.path).path == WEG_KOPPELN
                and self._kopplung_gilt()):
            return True
        # DER NAME AUS `NAME`, in Satz und Bereich (Durchsicht der Welle 2, 22.09.2026):
        # Hier stand «Visbox» fest — die Stelle, die beim Umbenennen niemand findet.
        roh = json.dumps(
            {"fehler": f"Nicht angemeldet. Benutzername und Kennwort stehen im Fenster, "
                       f"in dem {NAME} gestartet wurde."},
            ensure_ascii=False).encode("utf-8")
        self.send_response(401)
        # DER BROWSER FRAGT ERST, WENN ER DAS HIER SIEHT. Ohne diesen Kopf bekaeme der
        # Benutzer eine Fehlermeldung statt eines Anmeldefensters.
        self.send_header("WWW-Authenticate", f'Basic realm="{_bereich()}", charset="UTF-8"')
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(roh)))
        self.end_headers()
        self.wfile.write(roh)
        return False

    def _kopplung_gilt(self) -> bool:
        """Ob gerade eine Zahl gilt — nicht nur, ob es eine Kopplung gibt."""
        offen = type(self).kopplung_offen
        return offen is not None and kopplung.stand(offen) == kopplung.STAND_OFFEN

    # -------------------------------------------------------------- kleine Handgriffe
    def _sende(self, nutzlast: dict, code: int = 200) -> None:
        roh = json.dumps(nutzlast, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(roh)))
        self.end_headers()
        self.wfile.write(roh)

    def _fehler(self, satz: str, code: int = 400) -> None:
        """Ein Fehlschlag ist ein **Satz**, kein Zustandscode.

        Wer einen Stacktrace liest, hört auf; wer einen Satz liest, weiss, woran er ist.
        Der Satz kommt aus der Bibliothek — sie hat ihn für einen Menschen geschrieben.
        """
        self._sende({"fehler": satz}, code)

    def log_message(self, format, *args):           # noqa: A002 — Signatur der Basisklasse
        """Still. Eine Oberfläche, die bei jedem Klick eine Zeile ins Terminal schreibt,
        macht das Terminal unbrauchbar für das, wofür man es offen hat."""

    # -------------------------------------------------------------------------- lesen
    def do_GET(self) -> None:                        # noqa: N802 — Name der Basisklasse
        if not self._darf_herein():
            return
        weg = urllib.parse.urlparse(self.path)
        methode = WEGTAFEL_LESEN.get(weg.path)
        if methode is None:
            self._fehler(f"Unbekannter Weg: {weg.path}", 404)
            return
        getattr(self, methode)(weg)

    def _seite(self, weg) -> None:
        roh = SEITE.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(roh)))
        self.end_headers()
        self.wfile.write(roh)

    def _koppelseite(self, weg) -> None:
        """Die Koppelseite — **nur, solange eine Zahl gilt.**

        Unangemeldet kommt hierher nur, wer die Tür mit geltender Zahl durchlassen hat.
        Angemeldet ohne geltende Zahl: 404 mit Satz — es gibt nichts zu koppeln, und eine
        Seite mit einem Zahlenfeld, in das keine Zahl passt, wäre ein Bedienelement ohne
        Wirkung.
        """
        if not self._kopplung_gilt():
            self._fehler(f"Auf dieser HomeStation ist gerade kein Verbinden offen. {NAME} "
                         f"mit --kopplung starten, dann gilt die angezeigte Zahl zehn "
                         f"Minuten.", 404)
            return
        roh = KOPPELSEITE.replace("__NAME__", html.escape(NAME)).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(roh)))
        # NICHT AUFHEBEN. Eine Koppelseite aus dem Speicher des Browsers stuende auch
        # dann noch da, wenn die Zahl laengst tot ist.
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(roh)

    def _projekt(self, weg) -> None:
        frage = urllib.parse.parse_qs(weg.query)
        ordner = (frage.get("ordner") or [None])[0] or self.ordner
        if not ordner:
            self._fehler("Kein Projektordner angegeben — mit --ordner starten oder "
                         "oben einen eintragen.", 404)
            return
        try:
            self._sende(sicht(Path(ordner)))
        except projekt.ProjektError as fehler:
            self._fehler(str(fehler), 404)

    def _fortschritt(self, weg) -> None:
        self._sende(LAUFSTAND.sicht())

    def _bild_anfrage(self, weg) -> None:
        self._bild(urllib.parse.parse_qs(weg.query))

    def _bild(self, frage: dict) -> None:
        """Ein Bild aus dem Projektordner ausliefern — und sonst nichts von der Platte.

        Die ganze Entscheidung steht in :func:`bildpfad`; hier wird sie nur befolgt. Eine
        zweite Prüfung an dieser Stelle wäre dieselbe Regel zum zweiten Mal, und die
        zweite veraltet.
        """
        ordner = (frage.get("ordner") or [None])[0] or self.ordner
        name = (frage.get("name") or [None])[0]
        if not ordner or not name:
            self._fehler("Es fehlt der Projektordner oder der Bildname.", 404)
            return
        try:
            ziel = bildpfad(Path(ordner), name)
            roh = ziel.read_bytes()
        except FlaechenError as fehler:
            self._fehler(str(fehler), 404)
            return
        except OSError as fehler:
            self._fehler(f"Das Bild liess sich nicht lesen: {fehler}", 404)
            return

        self.send_response(200)
        self.send_header("Content-Type", BILDTYPEN[ziel.suffix.lower()])
        self.send_header("Content-Length", str(len(roh)))
        # NICHT ZWISCHENSPEICHERN. Ein neuer Lauf schreibt unter denselben Namen, und ein
        # Browser, der das alte Bild behaelt, zeigt ein Ergebnis, das es nicht mehr gibt —
        # neben einem Urteil, das zum neuen gehoert. Das ist schlimmer als langsam.
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(roh)

    # ------------------------------------------------------------------------ handeln
    def do_POST(self) -> None:                       # noqa: N802 — Name der Basisklasse
        if not self._darf_herein():
            return
        laenge = int(self.headers.get("Content-Length") or 0)
        try:
            wunsch = json.loads(self.rfile.read(laenge) or b"{}")
        except ValueError as fehler:
            self._fehler(f"Die Anfrage war nicht lesbar: {fehler}")
            return

        weg = urllib.parse.urlparse(self.path).path
        # DIE TAFEL STATT DER KETTE — siehe `WEGTAFEL`. Wer einen Weg ergaenzt, schreibt
        # dort eine Zeile und hier nichts.
        methode = WEGTAFEL.get(weg)
        if methode is None:
            self._fehler(f"Unbekannter Weg: {weg}", 404)
            return
        getattr(self, methode)(wunsch)

    def _verbinden(self, wunsch: dict) -> None:
        """Das erste Verbinden: eine kurze Zahl gegen das lange Kennwort.

        Was hier passiert, entscheidet :mod:`aiimaging.kopplung` — diese Methode reicht
        nur durch und gibt im Erfolgsfall das Kennwort heraus. **Die Fläche urteilt
        nicht**, sie kennt weder die Frist noch den Versuchszähler.

        **Das Kennwort geht genau einmal über diesen Weg**, und danach ist die Zahl tot.
        Ein Gerät, das es hat, benutzt von da an die gewöhnliche Anmeldung.

        *Ein Weg, über den ein Geheimnis zweimal herauskommt, ist kein Austausch, sondern
        eine Ausgabestelle.*
        """
        offen = type(self).kopplung_offen
        if offen is None:
            # Kann nur erreicht werden, wenn zwischen Tuer und hier die Kopplung
            # geschlossen wurde. Dann ist Ablehnen richtig, nicht Abstuerzen.
            self._fehler("Auf dieser HomeStation ist gerade kein Verbinden offen.", 403)
            return

        antwort = kopplung.pruefe(offen, wunsch.get("pin"))
        if not antwort["angenommen"]:
            # DAS GERAET HOERT DEN UNBESTIMMTEN SATZ, nicht den genauen Grund — sonst
            # halbierte sich die Arbeit dessen, der raet. Der genaue Grund geht an die
            # HomeStation, also in das Fenster, in dem die Flaeche gestartet wurde.
            print(f"  Verbinden abgelehnt: {antwort['grund']} "
                  f"(noch {antwort['versuche_uebrig']} Versuche)")
            self._sende({"verbunden": False,
                         "satz": antwort["satz_fuer_das_geraet"]}, 403)
            return

        print("  Ein Gerät hat sich verbunden. Die Zahl ist damit verbraucht.")
        # DER SATZ SAGT NUR, WAS DER SERVER WEISS (Befund der Durchsicht D-SERVER,
        # 22.09.2026): Hier stand «Dieses Gerät merkt sich die Anmeldung». Die App legt
        # sie in den Schluesselbund, ein Browser auf der Koppelseite nicht von selbst —
        # und ob irgendwer sie aufhebt, kann der Server nicht wissen. Wahr ist fuer beide:
        # Sie kommen nur dieses eine Mal.
        self._sende({"verbunden": True, "benutzer": BENUTZER,
                     "kennwort": self.kennwort,
                     "satz": SATZ_VERBUNDEN})

    def _anlegen(self, wunsch: dict) -> None:
        """Ruft :func:`aiimaging.arbeitsgang.lege_an` — und sonst nichts."""
        ordner, modell = wunsch.get("ordner"), wunsch.get("modell")
        if not ordner or not modell:
            self._fehler("Es fehlt der Projektordner oder die Modelldatei.")
            return
        try:
            ergebnis = arbeitsgang.lege_an(
                Path(ordner), Path(modell), name=wunsch.get("name"),
                einstellungen=wunsch.get("einstellungen") or {})
        except (arbeitsgang.ArbeitsgangError, projekt.ProjektError,
                importeur.ImporteurError) as fehler:
            self._fehler(str(fehler))
            return
        # ABGELEHNT IST KEIN FEHLER, sondern ein Befund — und er steht im Projekt. Ihn
        # hier zu einem Fehler zu machen hiesse, dem Benutzer die Mappe wegzunehmen, in
        # der die Begruendung steht.
        self._sende({"angelegt": True, "import": ergebnis["projekt"]["import"]})

    def _einstellungen(self, wunsch: dict) -> None:
        """Einstellungen ändern — **und vorher die Kette damit bauen lassen.**

        Die Fläche prüft die Werte nicht selbst. Sie legt sie der Bibliothek vor und lässt
        **die** urteilen: Baut :func:`aiimaging.kette.baue_kette` damit einen Graphen, sind
        sie brauchbar; wirft sie, kommt ihr Satz zurück und **es wird nichts gespeichert.**

            *Eine Oberfläche, die eigene Regeln über zulässige Werte kennt, hat dieselbe
            Regel zweimal — und die zweite veraltet, ohne dass jemand es merkt.*

        **Und warum nichts gespeichert wird, wenn es nicht baut:** Ein Projekt, dessen
        Einstellungen keine Kette ergeben, sieht in der Mappe aus wie jedes andere. Der
        Fehler fiele erst beim nächsten Lauf auf — und dann an einer Stelle, die mit ihm
        nichts zu tun hat.
        """
        ordner = wunsch.get("ordner") or self.ordner
        if not ordner:
            self._fehler("Kein Projektordner angegeben.")
            return
        neu_werte = wunsch.get("einstellungen")
        if not isinstance(neu_werte, dict):
            self._fehler("Es fehlen die Einstellungen.")
            return

        try:
            auf = projekt.oeffne(Path(ordner))
        except projekt.ProjektError as fehler:
            self._fehler(str(fehler), 404)
            return

        p = auf["projekt"]
        einfuhr = p.get("import") or {}
        # WAS AUF `None` GESETZT WIRD, WIRD ENTFERNT und nicht als `None` gespeichert.
        # Der Unterschied ist derselbe wie ueberall in diesem Projekt: «nicht gesetzt»
        # heisst «es gilt die Vorgabe», `None` hiesse «ausdruecklich nichts».
        gemischt = dict(p.get("einstellungen") or {})
        for name, wert in neu_werte.items():
            if wert is None:
                gemischt.pop(name, None)
            else:
                gemischt[name] = wert

        if einfuhr.get("glb"):
            probe = dict(gemischt)
            probe.pop("ifc_path", None)
            if not probe.get("up_axis") and einfuhr.get("hochachse_steht_fest"):
                probe["up_axis"] = einfuhr["hochachse"]
            try:
                kette.baue_kette(glb_path=einfuhr["glb"], **probe)
            except kette.KettenError as fehler:
                self._fehler(str(fehler))
                return
            except TypeError as fehler:
                # EIN UNBEKANNTER FELDNAME landet hier — `baue_kette` kennt ihn nicht.
                # Das ist keine Programmmeldung fuer den Benutzer, sondern eine Auskunft
                # ueber seine Eingabe, und sie wird als solche formuliert.
                self._fehler(f"Diese Einstellung kennt das Programm nicht: {fehler}")
                return

        p["einstellungen"] = gemischt
        try:
            projekt.speichere(p, Path(ordner))
        except projekt.ProjektKollision as fehler:
            # HIER WIRD NICHT WIEDERHOLT, und das ist der Unterschied zur Skizze.
            #
            # Eine Skizze kommt DAZU — sie laesst sich auf dem neuen Stand noch einmal
            # eintragen, ohne dass jemandem etwas fehlt. Eine Einstellung ERSETZT: Wer
            # sie auf dem neuen Stand wiederholte, wuerfe die Einstellung des anderen
            # weg, und genau davor soll diese Sperre schuetzen.
            #
            # *Wiederholen darf, was hinzufuegt. Was ersetzt, muss fragen.*
            self._fehler(f"{fehler} Die Seite neu laden zeigt den neuen Stand.")
            return
        except projekt.ProjektError as fehler:
            self._fehler(str(fehler))
            return
        self._sende({"gespeichert": True, "einstellungen": gemischt})

    def _skizze(self, wunsch: dict) -> None:
        """Eine Zeichnung ablegen und in der Mappe vermerken — **die Eingabe von E23.**

        Die Fläche schreibt die Datei und ruft
        :func:`aiimaging.projekt.vermerke_skizze`. Sie entscheidet dabei **nichts** über
        die Skizze: nicht, ob sie etwas taugt, und nicht, was daraus wird.

        **Warum die Bildpunkte hier hereinkommen und nicht ein Pfad.** Bei allem anderen
        gilt in diesem Projekt der umgekehrte Satz — *was als Absicht ankommt, lässt sich
        später anders ausführen.* Eine Zeichnung **ist** aber die Absicht; sie hat vor
        diesem Augenblick keine Datei, weil sie im Browser entstanden ist. Ein Pfad wäre
        hier ein Pfad auf etwas, das es noch nicht gibt.

        **Der Schlüssel gegen Doppelsendung** (``schluessel``, freiwillig, seit dem
        22.09.2026): Kommt derselbe zweimal, geht die erste Antwort noch einmal hinaus, und
        es entsteht keine zweite Datei. Siehe :class:`Eingangsbuch` — auch dafür, was er
        nach einem Neustart nicht mehr weiss.
        """
        ordner = wunsch.get("ordner") or self.ordner
        roh = wunsch.get("png_base64") or ""
        if not ordner or not roh:
            self._fehler("Es fehlt der Projektordner oder die Zeichnung.")
            return
        schluessel = wunsch.get("schluessel")
        if schluessel is not None and (not isinstance(schluessel, str)
                                       or not SCHLUESSEL_FORM.fullmatch(schluessel)):
            self._fehler("Der Schlüssel gegen Doppelsendung hat 8 bis 128 Zeichen aus "
                         "Buchstaben, Ziffern, Punkt, Bindestrich und Unterstrich. Ohne "
                         "Schlüssel schicken geht auch — dann schützt nichts vor einer "
                         "zweiten Datei.")
            return

        try:
            bytes_ = pruefe_skizzenbytes(roh)
        except FlaechenError as fehler:
            self._fehler(str(fehler))
            return

        with EINGANG.sperre:
            abdruck = hashlib.sha256(bytes_).hexdigest()
            if schluessel is not None:
                frueher = EINGANG.nachsehen(ordner, schluessel)
                if frueher is not None and frueher[0] != abdruck:
                    # DERSELBE SCHLUESSEL, EINE ANDERE ZEICHNUNG. Als Wiederholung
                    # behandelt, ginge die zweite Zeichnung still verloren.
                    self._fehler("Dieser Schlüssel ist schon mit einer ANDEREN Zeichnung "
                                 "angekommen. Eine neue Zeichnung braucht einen neuen "
                                 "Schlüssel — abgelegt wurde nichts.")
                    return
                if frueher is not None:
                    self._sende(dict(frueher[1]))
                    return
            antwort = self._lege_ab(Path(ordner), bytes_, wunsch)
            if antwort is None:
                return
            if schluessel is not None:
                antwort["schluessel"] = schluessel
                EINGANG.vermerke(ordner, schluessel, abdruck, antwort)
        self._sende(antwort)

    def _lege_ab(self, ordner: Path, bytes_: bytes, wunsch: dict):
        """Datei schreiben, in der Mappe vermerken, speichern. ``None`` heisst: Die Absage
        ist schon hinausgegangen."""
        try:
            p = projekt.oeffne(ordner)["projekt"]
            ziel = _lege_skizze_ab(ordner, bytes_, _belegte_namen(p))
            bemerkung = _bemerkung(wunsch.get("bemerkung"), wunsch.get("name"))
            projekt.vermerke_skizze(
                p, skizze=ziel.name, ueber=wunsch.get("ueber") or None,
                bemerkung=bemerkung)
            try:
                projekt.speichere(p, ordner)
            except projekt.ProjektKollision:
                # EINMAL WIEDERHOLEN, UND ZWAR HIER UND NICHT BEIM BENUTZER.
                #
                # Die Datei liegt an diesem Punkt schon auf der Platte. Wer jetzt nur
                # meldete «geht nicht», liesse eine Zeichnung zurueck, die es gibt und
                # die in keiner Mappe steht — unsichtbar, und beim naechsten Aufraeumen
                # weg. *Eine Zeichnung, die niemand mehr findet, ist verloren, auch wenn
                # ihre Datei noch da ist.*
                #
                # Wiederholen ist hier unbedenklich, weil ein Vermerk HINZUFUEGT: Auf dem
                # neuen Stand steht danach beides, die Arbeit des anderen und diese
                # Skizze. Genau EINMAL — kommt es zweimal in Folge, laeuft drueben etwas,
                # das schneller schreibt als wir, und dann ist Melden die richtige
                # Antwort.
                frisch = projekt.oeffne(ordner)["projekt"]
                projekt.vermerke_skizze(
                    frisch, skizze=ziel.name, ueber=wunsch.get("ueber") or None,
                    bemerkung=bemerkung)
                projekt.speichere(frisch, ordner)
        except projekt.ProjektError as fehler:
            self._fehler(str(fehler))
            return None
        except OSError as fehler:
            self._fehler(f"Die Zeichnung liess sich nicht schreiben: {fehler}")
            return None
        return {"abgelegt": True, "skizze": ziel.name, "hinweis": HINWEIS_SKIZZE_OHNE_WEG}

    def _benennen(self, wunsch: dict) -> None:
        """Ruft :func:`aiimaging.projekt.benenne` — ein eigener Name für ein Bild oder eine
        Skizze (Entscheid 19). Die Datei behält ihren Namen nach der Zeit.

        **``titel`` muss im Rumpf stehen**, auch als ``null`` (das nimmt den Namen
        zurück). Ein fehlendes Feld als «zurücknehmen» zu lesen hiesse, dass ein
        vergessenes Feld einen Namen löscht.

        **Bei einer Kollision wird nicht wiederholt** — ein Name ersetzt einen anderen,
        und *was ersetzt, muss fragen* (wie bei den Einstellungen).
        """
        ordner = wunsch.get("ordner") or self.ordner
        if not ordner:
            self._fehler("Kein Projektordner angegeben.")
            return
        if "titel" not in wunsch:
            self._fehler("Es fehlt der Name (titel). Mit null wird ein Name "
                         "zurückgenommen — dann gilt wieder der Name nach der Zeit.")
            return
        try:
            ergebnis = projekt.benenne(
                Path(ordner), titel=wunsch.get("titel"), bild=wunsch.get("bild"),
                skizze=wunsch.get("skizze"), von_stand=wunsch.get("von_stand"))
        except projekt.ProjektKollision as fehler:
            self._fehler(f"{fehler} Die Seite neu laden zeigt den neuen Stand.")
            return
        except projekt.ProjektError as fehler:
            self._fehler(str(fehler))
            return
        self._sende({"benannt": True, "eintrag": ergebnis["eintrag"],
                     "stand_nr": ergebnis["projekt"].get("stand_nr")})

    def _abbrechen(self, wunsch: dict) -> None:
        """Den laufenden Lauf anhalten (Entscheid 31) — **zwischen zwei Knoten.**

        Die Fläche setzt nur ein Zeichen; gefragt wird es von
        :func:`aiimaging.kette.fuehre_aus` vor jedem Knoten (``abbrechen``). **Der Knoten,
        der gerade rechnet, rechnet zu Ende** — ein Blender-Lauf oder eine Bildstufe lässt
        sich von aussen nicht mitten im Schritt anhalten, ohne ein halbes Ergebnis zu
        hinterlassen. Was fertig ist, bleibt in der Mappe (Entscheid 14).

        Es gibt **einen** Lauf zur Zeit auf diesem Server; ``ordner`` wird darum nicht
        gebraucht.
        """
        if not LAUFSTAND.verlange_abbruch():
            self._fehler("Es läuft gerade kein Lauf — es gibt nichts abzubrechen.")
            return
        self._sende({"abbruch_verlangt": True,
                     "satz": "Abbruch verlangt. Der Schritt, der gerade rechnet, rechnet zu "
                             "Ende; danach beginnt keiner mehr. Was fertig ist, bleibt in "
                             "der Mappe."})

    def _rechne(self, wunsch: dict) -> None:
        """Ruft :func:`aiimaging.arbeitsgang.rechne` — **mit den echten Ausführern.**

        Fehlen Blender, Gewichte oder die Grafikkarte, scheitert der Lauf, und der
        Fehlschlag kommt als Satz zurück. **Eine Attrappe einzusetzen, damit hier etwas
        erscheint, wäre die schlimmste Zeile dieser Datei:** Es entstünden Bilder und
        Urteile, die nichts gemessen haben, und niemand sähe ihnen das an.

        Seit dem 22.09.2026 auch als **Entwurf** (``entwurf``, Entscheid 30) und als
        **Reihe von Startwerten** (``varianten``, Entscheid 32). Ebenen-Varianten entstehen
        aus Skizzen und gehen über ``WEG_RECHNE_SKIZZE``.
        """
        ordner = wunsch.get("ordner") or self.ordner
        if not ordner:
            self._fehler("Kein Projektordner angegeben.")
            return
        if LAUFSTAND.sicht()["laeuft"]:
            self._fehler("Es läuft schon einer. Zwei Läufe auf derselben Mappe schrieben "
                         "beide in dieselbe Projektdatei — der zweite überschriebe die "
                         "Bilder des ersten.")
            return
        try:
            b = _lies_bestellung(wunsch, skizzenlauf=False)
        except FlaechenError as fehler:
            self._fehler(str(fehler))
            return

        # WIE VIELE SCHRITTE ES INSGESAMT WERDEN, muss VOR dem Lauf feststehen — sonst
        # gibt es einen Zaehler ohne Nenner, und ein Zaehler ohne Nenner ist eine Zahl
        # ohne Auskunft. Bei einer Reihe: je Variante, denn jede zaehlt von vorn.
        gesamt = _schritte_gesamt(Path(ordner), b["einstellungen"], entwurf=b["entwurf"])

        LAUFSTAND.beginne(ordner, schritte_gesamt=gesamt, bestellung={
            "art": "modell", "entwurf": b["entwurf"], "varianten": b["varianten"],
            "skizzen": None})
        faden = threading.Thread(
            target=_rechne_im_hintergrund,
            args=(Path(ordner), b["trotz_aenderung"], b["einstellungen"]),
            kwargs={"entwurf": b["entwurf"], "varianten": b["varianten"]},
            daemon=True)
        faden.start()

        # SOFORT ANTWORTEN. Bis zum 21.09.2026 blieb diese Anfrage offen, bis der ganze
        # Lauf fertig war — Minuten. Ein Browser zeigt in der Zeit nichts an und laeuft
        # irgendwann in seine eigene Frist.
        self._sende({"gestartet": True, "schritte_gesamt": gesamt,
                     "entwurf": b["entwurf"], "varianten": b["varianten"]})

    def _rechne_skizze(self, wunsch: dict) -> None:
        """Ruft :func:`aiimaging.arbeitsgang.rechne_skizze` — eine abgelegte Skizze
        **rechnen lassen** (Entscheid 11: nichts rechnet von selbst).

        ``skizze`` ist ein Dateiname aus der Mappe oder eine Liste von zweien bis acht:
        Dann entsteht je Skizze ein Lauf, als **Ebenen-Reihe** (Entscheid 32). Was die
        Bibliothek an einer Skizze abweist (unbekannt, verworfen, Datei fehlt, keine
        Anweisung), kommt als Satz im Laufstand (``fehler``) — geprüft wird es dort, unter
        der Laufsperre, und nicht ein zweites Mal hier.
        """
        ordner = wunsch.get("ordner") or self.ordner
        if not ordner:
            self._fehler("Kein Projektordner angegeben.")
            return
        if LAUFSTAND.sicht()["laeuft"]:
            self._fehler("Es läuft schon einer. Zwei Läufe auf derselben Mappe schrieben "
                         "beide in dieselbe Projektdatei — der zweite überschriebe die "
                         "Bilder des ersten.")
            return
        try:
            b = _lies_bestellung(wunsch, skizzenlauf=True)
        except FlaechenError as fehler:
            self._fehler(str(fehler))
            return

        gesamt = _schritte_gesamt(Path(ordner), b["einstellungen"], entwurf=b["entwurf"])
        skizzen = b["skizze"] if isinstance(b["skizze"], list) else [b["skizze"]]
        LAUFSTAND.beginne(ordner, schritte_gesamt=gesamt, bestellung={
            "art": "skizze", "entwurf": b["entwurf"],
            "varianten": len(skizzen) if len(skizzen) > 1 else None, "skizzen": skizzen})
        faden = threading.Thread(
            target=_rechne_im_hintergrund,
            args=(Path(ordner), b["trotz_aenderung"], b["einstellungen"]),
            kwargs={"entwurf": b["entwurf"], "skizze": b["skizze"],
                    "anweisung": b["anweisung"]},
            daemon=True)
        faden.start()
        self._sende({"gestartet": True, "schritte_gesamt": gesamt,
                     "entwurf": b["entwurf"], "skizzen": skizzen})


def _lies_bestellung(wunsch: dict, *, skizzenlauf: bool) -> dict:
    """Was ein Rechenauftrag bestellt — **in der Form geprüft, nicht im Inhalt.**

    Geprüft wird hier nur, was die Leitung verfälschen kann: ob ein Wahrheitswert einer
    ist (``"nein"`` wäre für Python wahr), ob die Einstellungen ein Objekt sind und nur
    Felder von :func:`aiimaging.kette.baue_kette` tragen. **Was zulässig ist, entscheidet
    die Bibliothek**; die Grenzen einer Reihe werden bei ihr erfragt
    (``arbeitsgang.pruefe_varianten``), damit die Absage sofort kommt und nicht erst im
    Laufstand.

    **Und warum nur Felder der Kette:** ``rechne`` nimmt neben den Kettenfeldern auch
    Ausführer, Speicher und Melder. Über die Einstellungen kämen sie aus dem Netz — ein
    leerer Speicher oder eine fremde Ausführertafel wären dann eine Bestellung von
    aussen, und genau das darf diese Fläche nie weiterreichen.

    Raises:
        FlaechenError: mit dem Satz für den Menschen.
    """
    einstellungen = wunsch.get("einstellungen")
    if einstellungen is None:
        einstellungen = {}
    if not isinstance(einstellungen, dict):
        raise FlaechenError("Die Einstellungen sind ein Objekt aus Namen und Werten.")
    kettenfelder = set(inspect.signature(kette.baue_kette).parameters) - set(NICHT_EINSTELLBAR)
    fremd = sorted(set(einstellungen) - kettenfelder)
    if fremd:
        raise FlaechenError(f"Diese Einstellung kennt das Programm nicht: {', '.join(fremd)}")

    for feld in ("entwurf", "trotz_aenderung"):
        if feld in wunsch and not isinstance(wunsch[feld], bool):
            raise FlaechenError(
                f"{feld} ist wahr oder falsch (true/false) — war {wunsch[feld]!r}.")
    b = {"einstellungen": dict(einstellungen),
         "entwurf": wunsch.get("entwurf", False),
         "trotz_aenderung": wunsch.get("trotz_aenderung", False),
         "varianten": None, "skizze": None, "anweisung": None}

    if not skizzenlauf:
        varianten = wunsch.get("varianten")
        try:
            arbeitsgang.pruefe_varianten(varianten, arbeitsgang.VARIANTEN_STARTWERTE)
        except arbeitsgang.ArbeitsgangError as fehler:
            raise FlaechenError(str(fehler)) from None
        b["varianten"] = varianten
        return b

    if "varianten" in wunsch:
        # NICHT STILL UEBERGANGEN: Wer drei Startwerte einer Skizze bestellt, bekaeme
        # sonst ein Bild und haelt es fuer die erste von dreien.
        raise FlaechenError(
            "Varianten einer Skizze entstehen als Ebenen — eine Liste von Skizzen unter "
            "«skizze», je Skizze ein Lauf. Startwert-Reihen kennt die Bibliothek nur für "
            "das Bild aus dem Modell (POST /api/rechne mit «varianten»).")
    skizze = wunsch.get("skizze")
    if isinstance(skizze, list):
        if not skizze or not all(isinstance(s, str) and s.strip() for s in skizze):
            raise FlaechenError("«skizze» ist ein Dateiname oder eine Liste von "
                                "Dateinamen aus der Mappe.")
        if len(skizze) > 1:
            try:
                arbeitsgang.pruefe_varianten(len(skizze), arbeitsgang.VARIANTEN_EBENEN)
            except arbeitsgang.ArbeitsgangError as fehler:
                raise FlaechenError(str(fehler)) from None
        else:
            skizze = skizze[0]
    elif not isinstance(skizze, str) or not skizze.strip():
        raise FlaechenError("Welche Skizze gerechnet werden soll, ist nicht gesagt "
                            "(«skizze»: ein Dateiname aus der Mappe).")
    anweisung = wunsch.get("anweisung")
    if anweisung is not None and not isinstance(anweisung, str):
        raise FlaechenError("Die Anweisung ist ein Text — was sich am Bild ändern soll.")
    b["skizze"], b["anweisung"] = skizze, anweisung
    return b


def _schritte_gesamt(ordner, einstellungen: dict, *, entwurf: bool = False):
    """Wie viele Diffusionsschritte dieser Lauf rechnen wird — oder ``None``.

    Gelesen wird, was der Lauf wirklich benutzt: erst die Einstellungen der Mappe, dann
    die des Aufrufs — **dieselbe Reihenfolge wie in** :func:`aiimaging.arbeitsgang.rechne`.
    Eine eigene Regel hier wäre dieselbe Regel zweimal, und die zweite veraltet. Beim
    Entwurf rechnet die Bibliothek die Deckelung selbst
    (``arbeitsgang.entwurfsargumente``) — auch sie wird dort geholt, nicht hier
    nachgebaut.

    ``None`` heisst **unbekannt** und nicht null: Ohne Nenner zeigt die Fläche keinen
    Anteil an. *Ein Zähler ohne Nenner ist eine Zahl ohne Auskunft.*
    """
    try:
        aus_mappe = (projekt.oeffne(ordner)["projekt"].get("einstellungen") or {})
    except projekt.ProjektError:
        aus_mappe = {}
    zusammen = {**aus_mappe, **einstellungen}
    if entwurf:
        try:
            zusammen = arbeitsgang.entwurfsargumente(zusammen, einstellungen)
        except arbeitsgang.ArbeitsgangError:
            return None
    wert = zusammen.get("schritte")
    return wert if isinstance(wert, int) and not isinstance(wert, bool) and wert > 0 else None


def _rechne_im_hintergrund(ordner, trotz_aenderung: bool, einstellungen: dict, *,
                           entwurf: bool = False, varianten=None, skizze=None,
                           anweisung=None) -> None:
    """Der Lauf selbst — in einem eigenen Faden, damit die Seite währenddessen antwortet.

    Mit ``skizze`` über :func:`aiimaging.arbeitsgang.rechne_skizze`, sonst über
    :func:`aiimaging.arbeitsgang.rechne`. Beide bekommen den Laufstand als Melder **und
    als Frage nach dem Abbruch** (Entscheid 31).

    **Er fängt alles.** Eine Ausnahme in einem Hintergrundfaden verschwindet sonst
    spurlos: Der Faden endet, der Laufstand bliebe für immer auf «läuft», und die Anzeige
    zeigte bis zum Neustart einen Lauf, den es nicht mehr gibt.

        *Ein Fehler, den niemand sieht, ist schlimmer als einer, der eine Meldung macht.*
    """
    try:
        gemeinsam = {"trotz_aenderung": trotz_aenderung, "melder": LAUFSTAND.melde,
                     "abbrechen": LAUFSTAND.abbruch_verlangt, "entwurf": entwurf}
        if skizze is not None:
            ergebnis = arbeitsgang.rechne_skizze(
                ordner, skizze, anweisung=anweisung, **gemeinsam, **einstellungen)
        else:
            ergebnis = arbeitsgang.rechne(
                ordner, varianten=varianten, **gemeinsam, **einstellungen)
        LAUFSTAND.beende(ergebnis={
            "status": ergebnis["lauf"].get("status"),
            "vermerkt": ergebnis["vermerkt"],
            "modell_stand": ergebnis["modell_stand"],
            "error": ergebnis["lauf"].get("error"),
            # ANGEHALTEN IST NICHT GESCHEITERT (Entscheid 31) — und nicht fertig. Dazu,
            # wie viele Varianten gar nicht erst begannen: Sie fehlen, und das soll man
            # sehen, statt eine Reihe von zwei fuer eine Reihe von drei zu halten.
            "abgebrochen": ergebnis.get("abgebrochen"),
            "bilder": list(ergebnis.get("bilder") or []),
            "variantengruppe": ergebnis.get("variantengruppe"),
            "varianten_nicht_begonnen": ergebnis.get("varianten_nicht_begonnen"),
        })
    except (arbeitsgang.ArbeitsgangError, projekt.ProjektError,
            kette.KettenError) as fehler:
        # DIE FEHLER DER BIBLIOTHEK OHNE TYPNAMEN — sie sind fuer einen Menschen
        # geschrieben.
        LAUFSTAND.beende(fehler=str(fehler))
    except Exception as fehler:                    # noqa: BLE001 — siehe Docstring
        LAUFSTAND.beende(fehler=f"{type(fehler).__name__}: {fehler}")


def baue_server(*, ordner=None, adresse: str = VORGABE_ADRESSE,
                anschluss: int = VORGABE_ANSCHLUSS, kennwort=None,
                kopplung_offen=None) -> HTTPServer:
    """Den Server bauen, **ohne ihn zu starten** — damit ein Test ihn prüfen kann.

    *Eine Funktion, die baut und sofort losläuft, ist von aussen nicht prüfbar* — und
    was nicht prüfbar ist, wird nicht geprüft.

    **Fail-closed an der einzigen Stelle, an der es zählt** (21.09.2026, Owner-Entscheid
    E25): Wer eine andere Adresse als ``127.0.0.1`` wählt, macht diese Fläche im Netz
    erreichbar — und hier liegen die Gebäudemodelle von jemandem. Ohne Kennwort wird sie
    dann **nicht gebaut**.

        *Eine Sperre, die man vergessen kann, ist im entscheidenden Augenblick vergessen.*

    Raises:
        FlaechenError: Nicht-lokale Adresse ohne Kennwort.
    """
    if adresse != VORGABE_ADRESSE and not kennwort:
        raise FlaechenError(
            f"Diese Fläche soll auf {adresse!r} hören und damit im Netz erreichbar sein — "
            f"ohne Kennwort wird das nicht gebaut. Hier liegen Gebäudemodelle, und jedes "
            f"Gerät im selben Netz käme heran.\n"
            f"Mit --kennwort ein eigenes setzen, oder --kennwort-erzeugen und das "
            f"angezeigte verwenden.")

    if kopplung_offen is not None and not kennwort:
        # OHNE KENNWORT GAEBE ES NICHTS ZU TAUSCHEN, und der Weg waere eine Tuer, die ins
        # Leere fuehrt. Abgelehnt statt stillschweigend ignoriert: Wer `--kopplung`
        # schreibt, erwartet, dass es wirkt.
        raise FlaechenError(
            "Verbinden per Zahl ergibt ohne Kennwort keinen Sinn — es gäbe nichts zu "
            "übergeben. Entweder --kennwort/--kennwort-erzeugen dazu, oder --kopplung "
            "weglassen.")

    klasse = type("FlaecheMitOrdner", (Flaeche,),
                  {"ordner": Path(ordner) if ordner else None,
                   "kennwort": kennwort or None,
                   "kopplung_offen": kopplung_offen})
    return HTTPServer((adresse, anschluss), klasse)


# ALLE ADRESSEN DIESES RECHNERS. Man kann auf ihr hoeren, aber sie nicht eintippen: Ein
# iPad, das `http://0.0.0.0:8731` aufruft, spricht mit sich selbst (Befund 22.09.2026).
ALLE_ADRESSEN = "0.0.0.0"

# EINE DOKUMENTATIONSADRESSE (RFC 5737, TEST-NET-1). Sie gehoert niemandem und wird nie
# angesprochen — sie dient nur dazu, das Betriebssystem zu fragen, ueber welche eigene
# Adresse es ins Netz ginge.
_FRAGEZIEL = ("192.0.2.1", 9)

# DER SATZ, WENN DIE ADRESSE NICHT ERMITTELT WURDE. Die dritte Antwort: nicht gemessen ist
# weder 0.0.0.0 noch 127.0.0.1 noch eine geratene Zahl.
NICHT_ERMITTELT = "Adresse im Heimnetz nicht ermittelt — am Rechner nachsehen"


def heimnetz_adresse():
    """Die eigene Adresse auf dem **Standardweg** ins Netz — oder ``None``.

    Im Heimnetz ist das meist die Adresse, unter der ein anderes Gerät diesen Rechner
    erreicht. **Nicht immer:** Mit VPN oder mehreren Netzkarten kann der Standardweg über
    eine andere Karte gehen. Am Gerät unbestätigt (Auftrag an die HomeStation).

    Befund 22.09.2026: ``--im-heimnetz`` druckte ``http://0.0.0.0:…`` — eine Adresse, die
    man nirgends eintippen kann. Wer die Zeile abliest, kam nicht an und wusste nicht warum.

    Gefragt wird das Betriebssystem, nicht das Netz: ``connect`` auf einem UDP-Socket
    **sendet nichts**, es legt nur fest, über welche eigene Adresse ein Paket hinausginge.
    ``getsockname`` liest sie ab.

    ``None`` heisst **nicht ermittelt** — kein Netz, keine Route, oder nur die eigene
    Maschine (``127.…``), die ein iPad nie erreicht. Es wird **nie** geraten.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(_FRAGEZIEL)
            adresse = s.getsockname()[0]
    except OSError:
        return None
    if not adresse or adresse == ALLE_ADRESSEN or adresse.startswith("127."):
        return None
    return adresse


def startzeile(adresse: str, anschluss: int) -> str:
    """Die Zeile, die ein Mensch abliest und ins iPad tippt.

    Hört die Fläche auf allen Adressen, wird die **erreichbare** genannt, nicht die, auf
    der sie hört (Befund 22.09.2026). Lässt sie sich nicht ermitteln, sagt die Zeile das.
    """
    if adresse in (ALLE_ADRESSEN, ""):
        erreichbar = heimnetz_adresse()
        if erreichbar is None:
            return (f"{NAME} läuft auf allen Adressen, Anschluss {anschluss} — "
                    f"{NICHT_ERMITTELT}  (Strg-C beendet)")
        return (f"{NAME} läuft auf http://{erreichbar}:{anschluss}  "
                f"(im Heimnetz; Strg-C beendet)")
    return f"{NAME} läuft auf http://{adresse}:{anschluss}  (Strg-C beendet)"


RUNDRUF_DATEI = Path(__file__).resolve().parent / "rundruf.py"

#: Der Erfolgssatz von ``POST /api/verbinden``. Siehe :meth:`Flaeche._verbinden`.
SATZ_VERBUNDEN = ("Verbunden. Benutzer und Kennwort kommen nur dieses eine Mal über die "
                  "Leitung.")


def _rundruf_modul():
    """``rundruf.py`` von nebenan — geladen **über den Pfad**, nicht über ``import``.

    Diese Datei läuft als Programm (``python3 oberflaeche/server.py``) und wird in den
    Proben als Modul geladen; ein ``import rundruf`` fände die Nachbardatei nur im ersten
    Fall. Und ``tests/test_oberflaeche.py`` lässt in dieser Datei nur Importe aus der
    Standardbibliothek und aus ``aiimaging`` zu — ``rundruf`` ist keines von beiden, obwohl
    es selbst nur die Standardbibliothek benutzt (bewacht in ``tests/test_rundruf.py``).
    """
    geladen = sys.modules.get("rundruf")
    if geladen is not None and Path(getattr(geladen, "__file__", "")).resolve() == RUNDRUF_DATEI:
        return geladen
    spez = importlib.util.spec_from_file_location("rundruf", RUNDRUF_DATEI)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


#: Der Name der App, wie ein Mensch ihn sieht — **aus** ``rundruf.NAME`` und nicht ein
#: zweites Mal eingeschrieben. ``rundruf.NAME`` ist gegen ``Marke.name`` in
#: ``ipad/Visbox.swiftpm/Kern/Marke.swift`` bewacht (``tests/test_rundruf.py``); diese
#: Konstante zusätzlich (``tests/test_durchsicht_kern_server.py``). Seit der Durchsicht
#: D-SERVER (22.09.2026) auf der Koppelseite und in ihrer Absage, seit der Durchsicht der
#: Welle 2 (23.09.2026) auch im Satz und im Bereich der Abweisung (401), im Kopf
#: ``Server``, in der Startzeile und in den Sätzen beim Start — bewacht an der Wirkung in
#: ``tests/test_durchsicht_w2b_kern_server.py``. **Nicht** umgestellt: der Benutzername
#: :data:`BENUTZER` (die App übernimmt ihn aus der Antwort, siehe Protokoll §2) und der
#: Dienstname im Rundruf (``rundruf.DIENST``, gegen ``Marke.dienst`` bewacht).
NAME = _rundruf_modul().NAME


def _bereich() -> str:
    """:data:`NAME` als Wert von ``realm="…"``: Anführungszeichen und Rückstrich
    maskiert, damit ein Name mit ``"`` den Kopf nicht zerbricht."""
    return NAME.replace("\\", "\\\\").replace('"', '\\"')


def starte_rundruf(anschluss: int):
    """Den Rundruf für ``--im-heimnetz`` starten (Entscheid 27) — ``(rundruf, satz)``.

    ``rundruf`` ist ``None``, wenn er nicht läuft; ``satz`` sagt dann **warum**. Ein
    Rundruf, der nicht startet, hält die Fläche nicht auf: Sie ist weiter erreichbar, nur
    muss die Adresse dann am iPad eingetippt werden — und genau das sagt der Satz.

    Die Adresse kommt aus :func:`heimnetz_adresse` — derselben, die die Startzeile nennt.
    """
    modul = _rundruf_modul()
    adresse = heimnetz_adresse()
    try:
        r = modul.starte(anschluss=anschluss, adresse=adresse)
    except modul.RundrufError as fehler:
        return None, (f"  Finden:     kein Rundruf — {fehler} Die Adresse am iPad "
                      f"eintippen.")
    return r, (f"  Finden:     Rundruf läuft ({modul.DIENST}, Anschluss {anschluss}) — "
               f"ein iPad im selben Netz kann die HomeStation suchen statt die Adresse "
               f"einzutippen (am Gerät unbestätigt).")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=f"Die Oberfläche von {NAME}.")
    ap.add_argument("--ordner", default=None, help="Projektordner, der beim Start gezeigt wird")
    # KEINE VORGABE IM PARSER: Nur so ist zu unterscheiden, ob jemand --adresse
    # ausdruecklich geschrieben hat (Befund 22.09.2026, siehe unten).
    ap.add_argument("--adresse", default=None,
                    help="Vorgabe 127.0.0.1 — nur die eigene Maschine. Siehe LIESMICH.")
    ap.add_argument("--anschluss", type=int, default=VORGABE_ANSCHLUSS)
    ap.add_argument("--kennwort", default=None,
                    help="Kennwort für die Anmeldung. Pflicht, sobald --adresse nicht "
                         "127.0.0.1 ist.")
    ap.add_argument("--kennwort-erzeugen", action="store_true",
                    help="Ein zufälliges Kennwort erzeugen und anzeigen.")
    ap.add_argument("--kopplung", action="store_true",
                    help="Eine sechsstellige Zahl anzeigen, mit der sich ein Gerät "
                         "EINMAL verbinden darf. Sie gilt zehn Minuten.")
    ap.add_argument("--im-heimnetz", action="store_true",
                    help="Auf allen Adressen hören, damit ein iPad herankommt. Verlangt "
                         "ein Kennwort — und zeigt an, was das bedeutet.")
    a = ap.parse_args(argv)

    # ZWEI ANGABEN FUER DIESELBE SACHE WERDEN ABGEWIESEN, nicht still geordnet (Befund
    # 22.09.2026): `--im-heimnetz` ueberschrieb eine ausdrueckliche `--adresse`, und wer
    # `--adresse 127.0.0.1` schrieb, stand im Netz, ohne dass gesagt wurde, dass seine
    # Angabe verworfen war. Sagen beide dasselbe (auch `''` heisst «alle Adressen»),
    # gibt es nichts abzuweisen.
    if a.im_heimnetz and a.adresse is not None and a.adresse not in (ALLE_ADRESSEN, ""):
        print(f"--im-heimnetz und --adresse {a.adresse} widersprechen sich: das eine heisst "
              f"«auf allen Adressen hören», das andere nur auf {a.adresse}. "
              f"Bitte nur eines von beiden angeben.")
        return 2
    if a.im_heimnetz:
        adresse = ALLE_ADRESSEN
    else:
        adresse = a.adresse if a.adresse is not None else VORGABE_ADRESSE
    kennwort = a.kennwort
    if getattr(a, "kennwort_erzeugen", False) and not kennwort:
        kennwort = erzeuge_kennwort()

    offen = kopplung.eroeffne() if a.kopplung else None

    try:
        server = baue_server(ordner=a.ordner, adresse=adresse, anschluss=a.anschluss,
                             kennwort=kennwort, kopplung_offen=offen)
    except FlaechenError as fehler:
        # KEIN STACKTRACE. Das ist der eine Fehler, den ein Mensch beim Start wirklich
        # sieht, und er ist fuer ihn geschrieben.
        print(str(fehler))
        return 2

    # DER WIRKLICHE ANSCHLUSS, nicht der verlangte: Bei `--anschluss 0` waehlt das
    # Betriebssystem einen, und die Zeile nannte bisher die 0.
    print(startzeile(adresse, server.server_address[1]))
    if kennwort:
        print(f"  Anmeldung:  Benutzer {BENUTZER!r}   Kennwort {kennwort}")
    if offen is not None:
        minuten = int(kopplung.FRIST_S // 60)
        print(f"  Verbinden:  Zahl {offen.pin}   — gilt {minuten} Minuten, für EIN Gerät")
        print(f"              Auf dem iPad eintippen. Danach ist sie verbraucht; für ein "
              f"zweites Gerät\n"
              f"              {NAME} mit --kopplung neu starten. Nach "
              f"{kopplung.VERSUCHE} Fehlversuchen ist sie tot.")
    if adresse != VORGABE_ADRESSE:
        print("  ACHTUNG: Diese Fläche ist im Netz erreichbar. Sie läuft über "
              "gewöhnliches HTTP —\n"
              "  Kennwort und Bilder gehen UNVERSCHLÜSSELT durch das Netz. Das Kennwort "
              "hält\n"
              "  Geräte fern, die zufällig im selben Netz sind, nicht jemanden, der dort "
              "mithört.")
    # DER RUNDRUF NUR IM HEIMNETZ. Auf 127.0.0.1 kann kein anderes Geraet herein; ein
    # Rundruf luede dann zu einer Verbindung ein, die nicht zustande kommt.
    rundruf = None
    if a.im_heimnetz:
        rundruf, satz = starte_rundruf(server.server_address[1])
        print(satz)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBeendet.")
    finally:
        # ERST DER RUNDRUF, DANN DIE FLAECHE: Er verabschiedet sich im Netz (Gueltigkeit
        # 0), damit kein iPad eine Stunde lang auf eine HomeStation zeigt, die weg ist.
        if rundruf is not None:
            rundruf.beende()
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
