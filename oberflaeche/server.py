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
import json
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# DER KERN WIRD IMPORTIERT, NICHT UMGEKEHRT. Diese Richtung ist die ganze Regel 4: Die
# Bibliothek weiss von dieser Datei nichts und laeuft ohne sie vollstaendig.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import arbeitsgang, importeur, kette, projekt   # noqa: E402

#: Nur die eigene Maschine. Siehe Modulkopf.
VORGABE_ADRESSE = "127.0.0.1"

#: Eine Zahl ohne Bedeutung, weit weg von allem Üblichen — damit sie nicht zufällig
#: auf einem Anschluss landet, auf dem schon etwas anderes lauscht.
VORGABE_ANSCHLUSS = 8731

SEITE = Path(__file__).resolve().parent / "seite.html"


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


def _bild_fuer_die_flaeche(eintrag: dict) -> dict:
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
        # DAS GEERBTE URTEIL BLEIBT EIN EIGENES FELD (E20). Es in `zeichen` zu mischen
        # hiesse, ein Bild der zweiten Stufe als geprueft anzuzeigen — genau der Fehler,
        # gegen den dieses Projekt seit Wochen anschreibt.
        "basis": basis,
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
    baum, baum_fehler = [], None
    if einfuhr.get("glb"):
        args = dict(p.get("einstellungen") or {})
        args.pop("ifc_path", None)
        if not args.get("up_axis") and einfuhr.get("hochachse_steht_fest"):
            args["up_axis"] = einfuhr["hochachse"]
        try:
            baum = _knotenbaum(kette.baue_kette(glb_path=einfuhr["glb"], **args))
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
        "bilder": [_bild_fuer_die_flaeche(b) for b in (p.get("bilder") or [])],
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
    server_version = "Visbox"
    sys_version = ""

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

        self._fehler(f"Unbekannter Weg: {weg.path}", 404)

    # ------------------------------------------------------------------------ handeln
    def do_POST(self) -> None:                       # noqa: N802 — Name der Basisklasse
        laenge = int(self.headers.get("Content-Length") or 0)
        try:
            wunsch = json.loads(self.rfile.read(laenge) or b"{}")
        except ValueError as fehler:
            self._fehler(f"Die Anfrage war nicht lesbar: {fehler}")
            return

        weg = urllib.parse.urlparse(self.path).path
        if weg == "/api/anlegen":
            self._anlegen(wunsch)
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
        try:
            ergebnis = arbeitsgang.rechne(
                Path(ordner), trotz_aenderung=bool(wunsch.get("trotz_aenderung")),
                **(wunsch.get("einstellungen") or {}))
        except (arbeitsgang.ArbeitsgangError, projekt.ProjektError,
                kette.KettenError) as fehler:
            self._fehler(str(fehler))
            return
        self._sende({"status": ergebnis["lauf"].get("status"),
                     "vermerkt": ergebnis["vermerkt"],
                     "modell_stand": ergebnis["modell_stand"],
                     "error": ergebnis["lauf"].get("error")})


def baue_server(*, ordner=None, adresse: str = VORGABE_ADRESSE,
                anschluss: int = VORGABE_ANSCHLUSS) -> HTTPServer:
    """Den Server bauen, **ohne ihn zu starten** — damit ein Test ihn prüfen kann.

    *Eine Funktion, die baut und sofort losläuft, ist von aussen nicht prüfbar* — und
    was nicht prüfbar ist, wird nicht geprüft.
    """
    klasse = type("FlaecheMitOrdner", (Flaeche,),
                  {"ordner": Path(ordner) if ordner else None})
    return HTTPServer((adresse, anschluss), klasse)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Die Oberfläche von Visbox.")
    ap.add_argument("--ordner", default=None, help="Projektordner, der beim Start gezeigt wird")
    ap.add_argument("--adresse", default=VORGABE_ADRESSE,
                    help="Vorgabe 127.0.0.1 — nur die eigene Maschine. Siehe LIESMICH.")
    ap.add_argument("--anschluss", type=int, default=VORGABE_ANSCHLUSS)
    a = ap.parse_args(argv)

    server = baue_server(ordner=a.ordner, adresse=a.adresse, anschluss=a.anschluss)
    print(f"Visbox läuft auf http://{a.adresse}:{a.anschluss}  (Strg-C beendet)")
    if a.adresse != VORGABE_ADRESSE:
        print("ACHTUNG: Diese Fläche ist von aussen erreichbar. Hier liegen "
              "Gebäudemodelle — sie werden damit weitergegeben.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBeendet.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
