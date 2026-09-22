#!/usr/bin/env python3
"""Die Oberfläche von Visbox — **eine dünne Schicht, und sie bleibt dünn.**

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
import hmac
import json
import secrets
import sys
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# DER KERN WIRD IMPORTIERT, NICHT UMGEKEHRT. Diese Richtung ist die ganze Regel 4: Die
# Bibliothek weiss von dieser Datei nichts und laeuft ohne sie vollstaendig.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import inspect                                                  # noqa: E402

from aiimaging import arbeitsgang, glbbox, importeur, kette, projekt   # noqa: E402

#: Nur die eigene Maschine. Siehe Modulkopf.
VORGABE_ADRESSE = "127.0.0.1"

#: Eine Zahl ohne Bedeutung, weit weg von allem Üblichen — damit sie nicht zufällig
#: auf einem Anschluss landet, auf dem schon etwas anderes lauscht.
VORGABE_ANSCHLUSS = 8731

SEITE = Path(__file__).resolve().parent / "seite.html"

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

#: Was an jeder abgelegten Skizze mitgeht, solange der Entwurfsmodus nicht rechnen kann.
#:
#: **Er steht hier und nicht in der Seite**, weil er eine Aussage über die Bibliothek ist
#: und keine über die Anzeige. *Eine Bestellung, die angenommen und nicht ausgeliefert
#: wird, ist schlimmer als eine abgelehnte: Die Ablehnung sieht man.* Angenommen wird sie
#: trotzdem — die Zeichnung ist das, was der Mensch getan hat, und sie geht nicht
#: verloren, nur weil die Maschine sie noch nicht einlösen kann.
HINWEIS_SKIZZE_OHNE_WEG = (
    "Abgelegt, aber NICHT gerechnet: Das Vorgabe-Bildmodell nimmt kein Eingangsbild an "
    "(gemessen, auf-20260919-123). Die Zeichnung liegt in der Mappe und wartet.")


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


def _skizzenname(gewuenscht) -> str:
    """Ein Dateiname für eine Zeichnung — **aus dem Zeitpunkt, nie aus dem Wunsch.**

    Der Wunsch kommt aus einem Browser und damit von aussen. Ihn als Dateinamen zu
    nehmen hiesse, jemand anderem zu erlauben, zu bestimmen, wo geschrieben wird —
    dieselbe Lücke, die :func:`bildpfad` beim Lesen schliesst, nur in die andere
    Richtung.

    Er geht darum **nicht verloren, sondern in die Bemerkung**: Was der Mensch gemeint
    hat, bleibt lesbar; was auf die Platte geschrieben wird, bestimmt diese Funktion.
    """
    stempel = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    return f"skizze-{stempel}.png"


#: Der Name, unter dem sich ein Mensch anmeldet. Ein Name allein schützt nichts — er
#: steht hier, weil ein Browser bei der einfachen Anmeldung nach beidem fragt.
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

    # ------------------------------------------------------------------ schreiben
    def beginne(self, ordner, schritte_gesamt=None) -> None:
        with self.sperre:
            self.__init__()
            self.laeuft = True
            self.ordner = str(ordner)
            self.begonnen = time.time()
            self.schritte_gesamt = schritte_gesamt

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
                    "status": ereignis.get("status"),
                    "aus_cache": ereignis.get("aus_cache"),
                    "dauer_s": ereignis.get("dauer_s"),
                })
                self.schritt = None
            elif art == "schritt":
                self.schritt = ereignis.get("schritt")

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
        if name in NICHT_EINSTELLBAR:
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
        if name in NICHT_EINSTELLBAR:
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


def _bild_fuer_die_flaeche(eintrag: dict, ordner=None) -> dict:
    """Ein Bildeintrag, wie ihn die Seite braucht — **samt seinem Vorbehalt.**

    Hier steht die einzige Stelle, an der diese Datei etwas *entscheidet*, und sie
    entscheidet nichts über die Sache, sondern über die **Anzeige**: welches der drei
    Zeichen ein Bild bekommt.

        Ein ungeprüftes Bild darf nie aussehen wie ein bestandenes — und auch nicht wie
        gar nichts.

    Der UI-Worker hat am 03.09.2026 genau das gemeldet: Die Bildkachel zeigte bei
    fehlender Prüfung **kein** Abzeichen. *Kein Abzeichen sieht aus wie kein Problem.*
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
    }


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
        "bilder": [_bild_fuer_die_flaeche(b, ordner) for b in (p.get("bilder") or [])],
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
# Der Anschluss — vier Wege, und jeder ruft genau eine Funktion der Bibliothek
# ======================================================================================

class Flaeche(BaseHTTPRequestHandler):
    """Übersetzt Anfragen in Bibliotheksaufrufe. Mehr tut sie nicht."""

    ordner: Path | None = None
    kennwort: str | None = None
    server_version = "Visbox"
    sys_version = ""

    # ------------------------------------------------------------------- die Tuer
    def _darf_herein(self) -> bool:
        """Jede Anfrage geht hier durch — **auch die nach der Seite selbst.**

        Eine Anmeldung, die nur die Daten schützt und die Seite freigibt, schützt nichts:
        Die Seite fragt die Daten ja gerade ab. *Eine Tür, die nur einen von zwei Wegen
        bewacht, ist keine Tür.*
        """
        if pruefe_anmeldung(self.headers.get("Authorization"), self.kennwort):
            return True
        roh = json.dumps(
            {"fehler": "Nicht angemeldet. Benutzername und Kennwort stehen im Fenster, "
                       "in dem Visbox gestartet wurde."},
            ensure_ascii=False).encode("utf-8")
        self.send_response(401)
        # DER BROWSER FRAGT ERST, WENN ER DAS HIER SIEHT. Ohne diesen Kopf bekaeme der
        # Benutzer eine Fehlermeldung statt eines Anmeldefensters.
        self.send_header("WWW-Authenticate", 'Basic realm="Visbox", charset="UTF-8"')
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(roh)))
        self.end_headers()
        self.wfile.write(roh)
        return False

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
        if weg.path in ("/", "/index.html"):
            roh = SEITE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(roh)))
            self.end_headers()
            self.wfile.write(roh)
            return

        if weg.path == "/api/projekt":
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
            return

        if weg.path == "/api/fortschritt":
            self._sende(LAUFSTAND.sicht())
            return

        if weg.path == "/bild":
            self._bild(urllib.parse.parse_qs(weg.query))
            return

        self._fehler(f"Unbekannter Weg: {weg.path}", 404)

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
        if weg == "/api/anlegen":
            self._anlegen(wunsch)
        elif weg == "/api/einstellungen":
            self._einstellungen(wunsch)
        elif weg == "/api/skizze":
            self._skizze(wunsch)
        elif weg == "/api/rechne":
            self._rechne(wunsch)
        else:
            self._fehler(f"Unbekannter Weg: {weg}", 404)

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
        """
        ordner = wunsch.get("ordner") or self.ordner
        roh = wunsch.get("png_base64") or ""
        if not ordner or not roh:
            self._fehler("Es fehlt der Projektordner oder die Zeichnung.")
            return

        try:
            bytes_ = pruefe_skizzenbytes(roh)
        except FlaechenError as fehler:
            self._fehler(str(fehler))
            return

        try:
            ziel = Path(ordner) / _skizzenname(wunsch.get("name"))
            p = projekt.oeffne(Path(ordner))["projekt"]
            ziel.write_bytes(bytes_)
            bemerkung = _bemerkung(wunsch.get("bemerkung"), wunsch.get("name"))
            projekt.vermerke_skizze(
                p, skizze=ziel.name, ueber=wunsch.get("ueber") or None,
                bemerkung=bemerkung)
            try:
                projekt.speichere(p, Path(ordner))
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
                frisch = projekt.oeffne(Path(ordner))["projekt"]
                projekt.vermerke_skizze(
                    frisch, skizze=ziel.name, ueber=wunsch.get("ueber") or None,
                    bemerkung=bemerkung)
                projekt.speichere(frisch, Path(ordner))
        except projekt.ProjektError as fehler:
            self._fehler(str(fehler))
            return
        except OSError as fehler:
            self._fehler(f"Die Zeichnung liess sich nicht schreiben: {fehler}")
            return

        self._sende({"abgelegt": True, "skizze": ziel.name,
                     "hinweis": HINWEIS_SKIZZE_OHNE_WEG})

    def _rechne(self, wunsch: dict) -> None:
        """Ruft :func:`aiimaging.arbeitsgang.rechne` — **mit den echten Ausführern.**

        Fehlen Blender, Gewichte oder die Grafikkarte, scheitert der Lauf, und der
        Fehlschlag kommt als Satz zurück. **Eine Attrappe einzusetzen, damit hier etwas
        erscheint, wäre die schlimmste Zeile dieser Datei:** Es entstünden Bilder und
        Urteile, die nichts gemessen haben, und niemand sähe ihnen das an.
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

        einstellungen = dict(wunsch.get("einstellungen") or {})
        # WIE VIELE SCHRITTE ES INSGESAMT WERDEN, muss VOR dem Lauf feststehen — sonst
        # gibt es einen Zaehler ohne Nenner, und ein Zaehler ohne Nenner ist eine Zahl
        # ohne Auskunft.
        gesamt = _schritte_gesamt(Path(ordner), einstellungen)

        LAUFSTAND.beginne(ordner, schritte_gesamt=gesamt)
        faden = threading.Thread(
            target=_rechne_im_hintergrund,
            args=(Path(ordner), bool(wunsch.get("trotz_aenderung")), einstellungen),
            daemon=True)
        faden.start()

        # SOFORT ANTWORTEN. Bis zum 21.09.2026 blieb diese Anfrage offen, bis der ganze
        # Lauf fertig war — Minuten. Ein Browser zeigt in der Zeit nichts an und laeuft
        # irgendwann in seine eigene Frist.
        self._sende({"gestartet": True, "schritte_gesamt": gesamt})


def _schritte_gesamt(ordner, einstellungen: dict):
    """Wie viele Diffusionsschritte dieser Lauf rechnen wird — oder ``None``.

    Gelesen wird, was der Lauf wirklich benutzt: erst die Einstellungen der Mappe, dann
    die des Aufrufs — **dieselbe Reihenfolge wie in** :func:`aiimaging.arbeitsgang.rechne`.
    Eine eigene Regel hier wäre dieselbe Regel zweimal, und die zweite veraltet.

    ``None`` heisst **unbekannt** und nicht null: Ohne Nenner zeigt die Fläche keinen
    Anteil an. *Ein Zähler ohne Nenner ist eine Zahl ohne Auskunft.*
    """
    try:
        aus_mappe = (projekt.oeffne(ordner)["projekt"].get("einstellungen") or {})
    except projekt.ProjektError:
        aus_mappe = {}
    wert = {**aus_mappe, **einstellungen}.get("schritte")
    return wert if isinstance(wert, int) and wert > 0 else None


def _rechne_im_hintergrund(ordner, trotz_aenderung: bool, einstellungen: dict) -> None:
    """Der Lauf selbst — in einem eigenen Faden, damit die Seite währenddessen antwortet.

    **Er fängt alles.** Eine Ausnahme in einem Hintergrundfaden verschwindet sonst
    spurlos: Der Faden endet, der Laufstand bliebe für immer auf «läuft», und die Anzeige
    zeigte bis zum Neustart einen Lauf, den es nicht mehr gibt.

        *Ein Fehler, den niemand sieht, ist schlimmer als einer, der eine Meldung macht.*
    """
    try:
        ergebnis = arbeitsgang.rechne(
            ordner, trotz_aenderung=trotz_aenderung, melder=LAUFSTAND.melde,
            **einstellungen)
        LAUFSTAND.beende(ergebnis={
            "status": ergebnis["lauf"].get("status"),
            "vermerkt": ergebnis["vermerkt"],
            "modell_stand": ergebnis["modell_stand"],
            "error": ergebnis["lauf"].get("error"),
        })
    except (arbeitsgang.ArbeitsgangError, projekt.ProjektError,
            kette.KettenError) as fehler:
        # DIE FEHLER DER BIBLIOTHEK OHNE TYPNAMEN — sie sind fuer einen Menschen
        # geschrieben.
        LAUFSTAND.beende(fehler=str(fehler))
    except Exception as fehler:                    # noqa: BLE001 — siehe Docstring
        LAUFSTAND.beende(fehler=f"{type(fehler).__name__}: {fehler}")


def baue_server(*, ordner=None, adresse: str = VORGABE_ADRESSE,
                anschluss: int = VORGABE_ANSCHLUSS, kennwort=None) -> HTTPServer:
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

    klasse = type("FlaecheMitOrdner", (Flaeche,),
                  {"ordner": Path(ordner) if ordner else None,
                   "kennwort": kennwort or None})
    return HTTPServer((adresse, anschluss), klasse)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Die Oberfläche von Visbox.")
    ap.add_argument("--ordner", default=None, help="Projektordner, der beim Start gezeigt wird")
    ap.add_argument("--adresse", default=VORGABE_ADRESSE,
                    help="Vorgabe 127.0.0.1 — nur die eigene Maschine. Siehe LIESMICH.")
    ap.add_argument("--anschluss", type=int, default=VORGABE_ANSCHLUSS)
    ap.add_argument("--kennwort", default=None,
                    help="Kennwort für die Anmeldung. Pflicht, sobald --adresse nicht "
                         "127.0.0.1 ist.")
    ap.add_argument("--kennwort-erzeugen", action="store_true",
                    help="Ein zufälliges Kennwort erzeugen und anzeigen.")
    ap.add_argument("--im-heimnetz", action="store_true",
                    help="Auf allen Adressen hören, damit ein iPad herankommt. Verlangt "
                         "ein Kennwort — und zeigt an, was das bedeutet.")
    a = ap.parse_args(argv)

    adresse = "0.0.0.0" if a.im_heimnetz else a.adresse
    kennwort = a.kennwort
    if getattr(a, "kennwort_erzeugen", False) and not kennwort:
        kennwort = erzeuge_kennwort()

    try:
        server = baue_server(ordner=a.ordner, adresse=adresse, anschluss=a.anschluss,
                             kennwort=kennwort)
    except FlaechenError as fehler:
        # KEIN STACKTRACE. Das ist der eine Fehler, den ein Mensch beim Start wirklich
        # sieht, und er ist fuer ihn geschrieben.
        print(str(fehler))
        return 2

    print(f"Visbox läuft auf http://{adresse}:{a.anschluss}  (Strg-C beendet)")
    if kennwort:
        print(f"  Anmeldung:  Benutzer {BENUTZER!r}   Kennwort {kennwort}")
    if adresse != VORGABE_ADRESSE:
        print("  ACHTUNG: Diese Fläche ist im Netz erreichbar. Sie läuft über "
              "gewöhnliches HTTP —\n"
              "  Kennwort und Bilder gehen UNVERSCHLÜSSELT durch das Netz. Das Kennwort "
              "hält\n"
              "  Geräte fern, die zufällig im selben Netz sind, nicht jemanden, der dort "
              "mithört.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBeendet.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
