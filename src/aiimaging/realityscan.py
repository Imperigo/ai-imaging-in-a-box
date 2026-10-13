"""REALITYSCAN-BRÜCKE — die Umgebung als Netz aus den **Fotos** (Owner-Entscheid 81, 13.10.2026).

Warum es dieses Modul gibt
--------------------------
Der offene Splat-Weg (gsplat + Open3D, :func:`aiimaging.seams.splat_zu_netz`) deckt am echten
Splat nur rund 10 % der Umgebung (``auf-20261013-276``/``-277``, Protokoll 74 §88–§90): Die
erwartete Tiefe eines trainierten Splats ist entlang der Strahlen breit verteilt, und weder
Filter noch Masken schliessen die Löcher. Owner-Entscheid 81: Die Umgebung kommt als echtes
Netz aus den **Fotos** der Aufnahme, über **Epic RealityScan 2.1** — das der Owner am Heim-PC
selbst installiert (Linux-Paket, läuft in mitgeliefertem Wine).

Die vier Auflagen (CLAUDE.md, «Fremdprogramme, vom Nutzer installiert», Entscheid 79)
------------------------------------------------------------------------------------
1. **Nie mitgeliefert.** Hier steht kein Binary, kein Installer, kein Download — nur der
   Aufruf eines Programms, das schon da ist.
2. **Nur als Prozess, nur auf dem Rechner des Lizenznehmers.** Eingeschaltet wird die Brücke
   **ausdrücklich**, mit :data:`REALITYSCAN_ENV` (Pfad zu ``realityscan-cli``). **Es gibt keine
   automatische Suche** nach einer Installation, mit Absicht: Eine Suche fände RealityScan
   auch auf einem Rechner, auf dem es jemand anderes für sich installiert hat — etwa auf einem
   Dienstrechner, der Aufträge von KosmoOrbit für Kunden rechnet. Das wäre Nutzung durch
   Dritte (EULA §1.2 c/d). Die Variable setzt der Lizenznehmer selbst für seinen eigenen
   Dienst; damit ist jede Benutzung eine bewusste Einrichtung, nie ein Zufallsfund.
3. **Nie Voraussetzung.** Fehlt etwas oder scheitert der Lauf, sagt
   :func:`aiimaging.seams.kontext_vorbereiten` den Grund (ohne Pfad) und nimmt den offenen
   Weg; der bleibt der Rückfall.
4. **Deklariert** im ``NOTICE`` («nicht ausgeliefert, vom Nutzer installiert»).

Was hier steht — nur die Standardbibliothek (Regel 4)
-----------------------------------------------------
* :func:`wine_pfad` — ein Linux-Pfad in der Schreibweise, die das Windows-Programm unter Wine
  versteht (``Z:\\…``; Wine bildet ``Z:`` auf ``/`` ab).
* :func:`colmap_als_text` — die Aufnahme (binär, COLMAP 3 oder 4 mit Rig) im **Textformat von
  COLMAP 3** (``cameras.txt``, ``images.txt``, ``points3D.txt``), das ``-importColmap`` liest.
  Je Bild seine eigene Pose; das Rig fällt weg, weil COLMAP 3 keines kennt.
* :func:`finde_bilder` — die Fotos nach der Konvention ``<sparse/0>/../../images``, geprüft
  gegen die Bildnamen der Aufnahme.
* :func:`kommando` — die Befehlsfolge, **nur aus Befehlen der Dokumentation** (gelesen
  13.10.2026). Was dort nicht steht, ist eine offene Frage für den Heim-PC
  (``betrieb/REALITYSCAN_BRUECKE.md``), kein erfundener Befehl.
* :func:`realityscan_zu_netz` — Lauf, Prüfung des Exports, Zwischenspeicher, Bericht ohne Pfad.
* :func:`lage_befund` — liegt das Netz dort, wo die Aufnahme liegt? Sonst wird es **nicht**
  benutzt (Grund ``lage``): RealityScan könnte neu gelagert oder skaliert haben.

Was offen ist
-------------
Steht gesammelt in :data:`OFFENE_FRAGEN` und in ``betrieb/REALITYSCAN_BRUECKE.md``. Alle Zahlen
unter «GESETZT» sind gesetzt, nicht gemessen; gemessen wird am Heim-PC.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import posixpath
import re
import shutil
import struct
import subprocess
import tempfile
import time
from pathlib import Path

from aiimaging import kontext_netz as _kn

__all__ = [
    "AUSGABE_ZEICHEN", "BILDER_WEG", "BILDER_WEGE", "BILDER_WEG_COLMAP", "BILDER_WEG_ORDNER",
    "COLMAP_MIT_PUNKTEN", "EXE_VORGABE", "FASSUNG", "FLUECHTIGE_URSACHEN",
    "GESAMTFRIST_REALITYSCAN_S", "LAGE_ECKEN_MAX", "LAGE_MASSSTAB_MAX", "LAGE_NAH_MIN",
    "LAGE_PROBEN", "LAGE_ZELLE_REL", "MODELL_NAME", "OFFENE_FRAGEN", "REALITYSCAN_ENV",
    "REALITYSCAN_EXE_ENV", "REALITYSCAN_EXPORT_XML_ENV", "REALITYSCAN_SPEICHER_ENV",
    "RealityScanError", "SATZ_REALITYSCAN", "URSACHE_AUFNAHME", "URSACHE_AUS",
    "URSACHE_BILDER", "URSACHE_EINRICHTUNG", "URSACHE_EXPORT", "URSACHE_GELIEFERT",
    "URSACHE_LAGE", "URSACHE_LAUF", "WEG", "ZIEL_DREIECKE",
    "colmap_als_text", "einrichtung", "eingeschaltet", "finde_bilder", "kommando",
    "lage_befund", "lage_pruefen", "lies_ecken", "nah_anteil", "ohne_pfade",
    "pruefe_export", "realityscan_schluessel", "realityscan_zu_netz", "treffer_maengel",
    "wine_pfad",
]


class RealityScanError(RuntimeError):
    """RealityScan wurde nicht benutzt — mit Grund (ohne Pfad) und Ursache (ein Wort).

    ``ursache`` ist einer der Werte ``URSACHE_*``; ``bericht`` trägt, wo es einen gibt, die
    Kennzahlen des Laufs (etwa die Lage-Zahlen bei ``lage``).
    """

    def __init__(self, grund: str, ursache: str, bericht: dict | None = None):
        super().__init__(grund)
        self.grund = grund
        self.ursache = ursache
        self.bericht = bericht


# ======================================================================================
# Einrichtung — nur ausdrücklich (Auflage 2)
# ======================================================================================

#: Pfad zu ``realityscan-cli``. **Gesetzt heisst eingeschaltet** — sonst nichts.
REALITYSCAN_ENV = "AIIMAGING_REALITYSCAN"
#: Pfad zur ``RealityScan.exe`` (Linux-Pfad); ohne Angabe :data:`EXE_VORGABE`.
REALITYSCAN_EXE_ENV = "AIIMAGING_REALITYSCAN_EXE"
#: Pfad zur **Export-Parameterdatei** (XML), die der Owner einmal im Programm anlegt. Pflicht:
#: Ihr Format ist nicht dokumentiert, und eine erfundene Datei wäre eine Behauptung.
REALITYSCAN_EXPORT_XML_ENV = "AIIMAGING_REALITYSCAN_EXPORT_XML"
#: Ablage der Netze; sonst ``~/.cache/aiimaging/realityscan-netz``.
REALITYSCAN_SPEICHER_ENV = "AIIMAGING_REALITYSCAN_SPEICHER"

#: Wo das Linux-Paket die Windows-Anwendung ablegt (Doku RealityScan 2.1 für Linux, gelesen
#: 13.10.2026). Eine **Vorgabe** für einen Pfad, den der Nutzer ohnehin eingerichtet hat —
#: keine Suche: Ist die Datei nicht da, ist die Brücke nicht eingerichtet.
EXE_VORGABE = ("/opt/realityscan/support/realityscan/drive_c/Program Files/Epic Games/"
               "RealityScan/RealityScan.exe")

#: Der Wert von ``kontext.weg``, wenn die Umgebung aus RealityScan kommt.
WEG = "realityscan"

#: Der Satz für ``verdict.hinweise`` (Auftrag 13.10.2026): Wer das Bild sieht, soll wissen,
#: dass die Umgebung aus einem Programm stammt, das nicht im Produkt ist.
SATZ_REALITYSCAN = ("UMGEBUNG aus den Fotos (RealityScan, vom Nutzer installiert) — "
                    "nicht im Produkt ausgeliefert.")

#: Warum RealityScan nicht benutzt wurde — ein Wort, für Vermerk und Zwischenspeicher.
URSACHE_AUS = "aus"                    # nicht eingeschaltet
URSACHE_EINRICHTUNG = "einrichtung"    # eingeschaltet, aber unvollständig
URSACHE_AUFNAHME = "aufnahme"          # keine COLMAP-Aufnahme zum Splat
URSACHE_BILDER = "bilder"              # Fotos fehlen
URSACHE_LAUF = "lauf"                  # Programm gescheitert, Frist, kein Export
URSACHE_EXPORT = "export"              # Export da, aber kein farbiges Netz
URSACHE_LAGE = "lage"                  # Netz liegt nicht bei der Aufnahme
URSACHE_GELIEFERT = "geliefert"        # Netz geliefert, nichts zu rechnen

#: Ursachen, nach denen ein gespeicherter Multipass **kein** Treffer ist, sobald RealityScan
#: eingeschaltet ist (:func:`treffer_maengel`): Sie hängen an der Einrichtung oder am
#: Zufall eines Laufs, nicht am Inhalt der Eingänge. ``None`` steht für Einträge von vor
#: dieser Brücke.
FLUECHTIGE_URSACHEN = frozenset({None, URSACHE_AUS, URSACHE_EINRICHTUNG, URSACHE_LAUF})


def eingeschaltet() -> bool:
    """Ist :data:`REALITYSCAN_ENV` gesetzt (nicht leer)? Nur das — geprüft wird in
    :func:`einrichtung`."""
    return bool(os.environ.get(REALITYSCAN_ENV, "").strip())


def einrichtung() -> dict:
    """Was eingerichtet ist — und, wenn etwas fehlt, ein Grund **ohne Pfad** (Regel 3).

    Returns:
        ``{eingeschaltet, bereit, cli, exe, export_xml, grund, ursache}`` — die Pfade nur für
        den Lauf, nie für einen Bericht.
    """
    aus = {"eingeschaltet": eingeschaltet(), "bereit": False, "cli": None, "exe": None,
           "export_xml": None, "grund": None, "ursache": None}
    if not aus["eingeschaltet"]:
        aus.update(grund=f"RealityScan nicht eingeschaltet ({REALITYSCAN_ENV} nicht gesetzt).",
                   ursache=URSACHE_AUS)
        return aus
    cli = os.environ[REALITYSCAN_ENV].strip()
    exe = os.environ.get(REALITYSCAN_EXE_ENV, "").strip() or EXE_VORGABE
    xml = os.environ.get(REALITYSCAN_EXPORT_XML_ENV, "").strip()
    fehlt = []
    if not os.path.isabs(cli) or not os.path.isfile(cli):
        fehlt.append(f"{REALITYSCAN_ENV} zeigt auf keine Datei (absoluter Pfad zu "
                     "realityscan-cli erwartet)")
    elif not os.access(cli, os.X_OK):
        fehlt.append(f"{REALITYSCAN_ENV}: realityscan-cli ist nicht ausfuehrbar")
    if not os.path.isabs(exe) or not os.path.isfile(exe):
        fehlt.append("RealityScan.exe nicht gefunden"
                     + (f" ({REALITYSCAN_EXE_ENV} pruefen)"
                        if os.environ.get(REALITYSCAN_EXE_ENV, "").strip()
                        else " am dokumentierten Ort; " + REALITYSCAN_EXE_ENV + " setzen"))
    if not xml:
        fehlt.append(f"{REALITYSCAN_EXPORT_XML_ENV} nicht gesetzt — die Export-Parameterdatei "
                     "legt der Nutzer einmal im Programm an (betrieb/REALITYSCAN_BRUECKE.md)")
    elif not os.path.isabs(xml) or not os.path.isfile(xml):
        fehlt.append(f"{REALITYSCAN_EXPORT_XML_ENV} zeigt auf keine Datei")
    if fehlt:
        aus.update(grund="RealityScan eingeschaltet, aber nicht eingerichtet: "
                         + "; ".join(fehlt) + ".", ursache=URSACHE_EINRICHTUNG)
        return aus
    aus.update(bereit=True, cli=cli, exe=exe, export_xml=xml)
    return aus


# ======================================================================================
# GESETZT — nicht gemessen (13.10.2026). Messauftrag am Heim-PC.
# ======================================================================================

#: Gesamtfrist eines Laufs, in Sekunden. GESETZT: Ausrichten und Netz aus 960 Fotos dauern
#: auf einer Desktop-GPU eher Viertelstunden als Minuten; vier Stunden lassen Luft und
#: begrenzen einen hängenden Lauf. Über ``AIIMAGING_ZEITFAKTOR`` umgerechnet wie alle
#: Gesamtfristen (:func:`aiimaging.seams.zeitfaktor`).
GESAMTFRIST_REALITYSCAN_S = 4 * 3600

#: Auf so viele Dreiecke wird das Netz vereinfacht (``-simplify``). GESETZT, **dieselbe Zahl
#: wie beim offenen Weg** (:data:`aiimaging.kontext_netz.ZIEL_DREIECKE`) und aus demselben
#: Grund: Blender rendert eine halbe Million Dreiecke ohne Mühe; mehr kostet Ladezeit je Kamera.
ZIEL_DREIECKE = _kn.ZIEL_DREIECKE

#: Der Name des Modells für ``-exportModel``. GESETZT nach dem Beispiel der Doku (ein Netz,
#: kein ``-simplify``). **Offen:** Ob ``-simplify`` ein neues Modell anlegt (dann hiesse das
#: vereinfachte vielleicht «Model 2»). Der Bericht vergleicht darum die Dreieckszahl mit
#: :data:`ZIEL_DREIECKE` (``netz.vereinfacht``) — die HomeStation sieht es am ersten Lauf.
MODELL_NAME = "Model 1"

#: Wie die Fotos in die Szene kommen. **Offen** (am Heim-PC zu prüfen): ob ``-importColmap``
#: die Bilder selbst lädt oder nur die Posen zu Bildern, die schon in der Szene sind — und ob
#: ihre Namen mit Unterordner (``back/0031.jpg``) dann zu den geladenen passen.
#: ``addFolder``: zuerst ``-addFolder <images>`` mit ``appIncSubdirs=true``, dann
#: ``-importColmap``; ``importColmap``: nur ``-importColmap``. GESETZT auf ``addFolder``,
#: weil die Doku das Hinzufügen von Bildern nur so zeigt.
BILDER_WEG_ORDNER = "addFolder"
BILDER_WEG_COLMAP = "importColmap"
BILDER_WEGE = (BILDER_WEG_ORDNER, BILDER_WEG_COLMAP)
BILDER_WEG = BILDER_WEG_ORDNER

#: Ob ``points3D.txt`` die Punkte samt Spuren trägt (und ``images.txt`` die 2D-Punkte).
#: GESETZT auf ja: Das ist die getreue Umschrift der Aufnahme, wie ``colmap model_converter``
#: sie schreibt. **Offen**, ob ``-importColmap`` die Punkte braucht; leer wäre schneller.
COLMAP_MIT_PUNKTEN = True

#: Die Lageprüfung (:func:`lage_befund`). GESETZT, nicht gemessen:
#: * Zellgrösse der Nachbarschaftssuche, als Anteil der Diagonale der COLMAP-Punkte (P2–P98)
#:   — 1 %, dieselbe Grössenordnung wie ``kontext_netz.GLEICH_MEDIAN_MAX``. Eine Probe zählt
#:   als «nah», wenn in ihrer Zelle oder einer der 26 Nachbarzellen ein Bezugspunkt liegt.
#: * Mindestanteil «nah» — die Hälfte. Ein neu gelagertes oder skaliertes Netz liegt fast
#:   nirgends bei der Aufnahme (Anteil nahe 0); ein richtig gelagertes verliert nur, was es
#:   nicht rekonstruiert hat (Himmel, Ausreisser, die gefilmte Person).
#: * Höchstes Verhältnis der Diagonalen Netz ↔ COLMAP-Punkte, in beide Richtungen — 2.
LAGE_ZELLE_REL = 0.01
LAGE_NAH_MIN = 0.5
LAGE_MASSSTAB_MAX = 2.0
#: Stichproben: COLMAP- und Splat-Punkte, Ecken des Netzes.
LAGE_PROBEN = 20000
LAGE_ECKEN_MAX = 200000

#: Wie viel der Ausgabe des Programms im Bericht steht (je Strom, die letzten Zeichen).
AUSGABE_ZEICHEN = 2000

#: Codestand der Brücke; steht im Speicherschlüssel. Hochzählen, wenn bei gleichen Eingängen
#: ein anderes Netz entstünde (andere Befehlsfolge).
FASSUNG = 1

#: Was am Heim-PC zu prüfen ist, bevor die Brücke als eingebaut gilt — genau formuliert,
#: damit ein Auftrag sie wörtlich übernehmen kann. Steht auch in
#: ``betrieb/REALITYSCAN_BRUECKE.md``.
OFFENE_FRAGEN = (
    "Wo liegt realityscan-cli nach der Installation des .deb/.rpm (z. B. "
    "/opt/realityscan/bin/realityscan-cli oder im PATH), und reicht es die Argumente einzeln "
    "an Wine weiter (Pfade mit Leerzeichen, ohne Shell)?",
    "Wie wird die Epic-Lizenz headless aktiviert? Laeuft -headless ohne angemeldete "
    "Sitzung, oder verlangt der erste Start eine Anmeldung in der Oberflaeche?",
    "Laedt -importColmap die Bilder selbst, oder braucht es vorher -addFolder <images> mit "
    "appIncSubdirs=true? Passen die Bildnamen mit Unterordner (back/0031.jpg) zu den "
    "geladenen Bildern, und gegen welchen Ordner loest RealityScan sie auf (Ordner der "
    "images.txt oder der Bilder)?",
    "Welche der drei Textdateien erwartet -importColmap (images.txt oder cameras.txt), und "
    "braucht es points3D.txt mit Spuren oder genuegt sie leer?",
    "Behaelt RealityScan nach -importColmap und -align die Lage und den Massstab der "
    "Aufnahme, oder lagert es neu? (Die Lagepruefung faengt es ab; dann wird das Netz nicht "
    "benutzt.) Gibt es eine Einstellung, die die importierten Posen festhaelt?",
    "Legt -simplify ein neues Modell an? Wenn ja: Wie heisst es (Model 2?), und exportiert "
    "-exportModel \"Model 1\" dann das unvereinfachte Netz (Bericht netz.vereinfacht)?",
    "Welche Einstellungen braucht die Export-Parameterdatei fuer PLY mit Eckpunktfarben "
    "(red/green/blue) und unveraenderten Koordinaten (kein Verschieben, kein Massstab, keine "
    "Achsendrehung)? Schreibt der Export binaer oder ASCII?",
    "Welche Fassung meldet das Programm in seiner Ausgabe (Zeile mit 'RealityScan x.y')?",
    "Wie lange dauert der Lauf mit 960 Bildern, und reicht die Frist von 4 h?",
    "Format von -exportRegistration: Liesse sich daraus eine Ausrichtung (Umeyama-Verfahren) "
    "zur Aufnahme rechnen, falls RealityScan neu lagert? (Nicht gebaut.)",
)


# ======================================================================================
# Pfade für Wine, und Pfade aus Texten
# ======================================================================================

def wine_pfad(p) -> str:
    """Ein **absoluter** Linux-Pfad in Windows-Schreibweise für Wine: ``/a/b`` → ``Z:\\a\\b``.

    Wine bildet das Laufwerk ``Z:`` auf das Wurzelverzeichnis ``/`` ab (RealityScan-Doku für
    Linux). Der Pfad wird normalisiert (``..``, doppelte Schrägstriche); ein Backslash oder ein
    Anführungszeichen im Namen ist unter Windows-Schreibweise nicht darstellbar und wird
    abgewiesen statt verfälscht.

    Raises:
        RealityScanError: relativ, oder mit ``\\`` / ``"`` im Namen.
    """
    s = str(p)
    if not s.startswith("/"):
        raise RealityScanError("Fuer Wine braucht es einen absoluten Pfad.", URSACHE_LAUF)
    if "\\" in s or '"' in s:
        raise RealityScanError("Ein Pfad mit Backslash oder Anfuehrungszeichen laesst sich "
                               "unter Wine nicht schreiben.", URSACHE_LAUF)
    norm = "/" + posixpath.normpath(s).lstrip("/")
    return "Z:" + norm.replace("/", "\\")


_POSIX_PFAD = re.compile(r"(?<![\w.:/\\<>])/(?:[^\s'\"/\\:<>]+/)*[^\s'\"/\\:<>]+/?")
_WINDOWS_PFAD = re.compile(r"\b[A-Za-z]:\\(?:[^\s'\"\\<>]+\\)*[^\s'\"\\<>]*")


def _kurz(treffer: re.Match) -> str:
    teile = [t for t in re.split(r"[/\\]", treffer.group(0)) if t and not t.endswith(":")]
    name = teile[-1] if teile else ""
    # NUR DATEINAMEN BLEIBEN: Ein Ordnername am Ende kann ein Benutzerkonto sein
    # (``/home/<name>``) — Regel 3.
    return f"<pfad>/{name}" if "." in name else "<pfad>"


def ohne_pfade(text, ersatz: dict[str, str] | None = None) -> str:
    """Pfade aus einem Text nehmen (Regel 3): erst die bekannten (``ersatz``: Pfad →
    Platzhalter, auch in Wine-Schreibweise), dann jeder übrige absolute Pfad — Linux oder
    Windows — bis auf seinen Dateinamen."""
    s = str(text or "")
    paare = []
    for pfad, platz in (ersatz or {}).items():
        if not pfad:
            continue
        paare.append((str(pfad), platz))
        try:
            paare.append((wine_pfad(pfad), platz))
        except RealityScanError:
            pass
    for pfad, platz in sorted(paare, key=lambda pp: -len(pp[0])):
        s = s.replace(pfad, platz)
        if pfad[:1].isalpha() and pfad[1:2] == ":":          # Wine schreibt auch klein
            s = s.replace(pfad[0].lower() + pfad[1:], platz)
    s = _WINDOWS_PFAD.sub(_kurz, s)
    return _POSIX_PFAD.sub(_kurz, s)


# ======================================================================================
# Die Aufnahme als COLMAP-Text
# ======================================================================================

#: COLMAP schreibt eine fehlende Zuordnung eines 2D-Punkts binär als grösste uint64, im Text
#: als −1 (COLMAP-Doku «Output Format»).
_KEIN_PUNKT = (1 << 64) - 1


def _zahl(w: float) -> str:
    # repr ist die kürzeste Schreibweise, die beim Lesen dieselbe Zahl ergibt — dieselbe
    # Genauigkeit wie COLMAP mit 17 Stellen, ohne Rundung.
    return repr(float(w))


def _bilder_2d(ordner: Path):
    """Je Bild ``(nr, [(x, y, punkt3d), …])`` in der Reihenfolge der Datei — binär oder Text."""
    p = _kn._datei(ordner, "images")
    if p.suffix == ".bin":
        with open(p, "rb") as datei:
            le = _kn._Leser(datei)
            (n,) = le.lies("Q")
            for _ in range(n):
                (nr,) = le.lies("I")
                le.ueberspringe(7 * 8 + 4)                 # Pose und Kamera: aus lies_aufnahme
                le.name()
                (n2d,) = le.lies("Q")
                roh = datei.read(24 * n2d)
                if len(roh) != 24 * n2d:
                    raise _kn.KontextNetzError("images.bin endet in den 2D-Punkten.")
                punkte = [(x, y, -1 if pid == _KEIN_PUNKT else int(pid))
                          for x, y, pid in struct.iter_unpack("<ddQ", roh)]
                yield nr, punkte
        return
    zeilen = _kn._textzeilen(p)
    for i in range(0, len(zeilen), 2):
        t = zeilen[i].split()
        if not t:
            continue
        w = zeilen[i + 1].split() if i + 1 < len(zeilen) else []
        yield int(t[0]), [(float(w[k]), float(w[k + 1]), int(w[k + 2]))
                          for k in range(0, len(w) - 2, 3)]


def _punkte_3d(ordner: Path):
    """Je Punkt ``(nr, x, y, z, r, g, b, fehler, [(bild, idx), …])`` — binär oder Text."""
    p = _kn._datei(ordner, "points3D")
    if p is None:
        return
    if p.suffix == ".bin":
        with open(p, "rb") as datei:
            le = _kn._Leser(datei)
            (n,) = le.lies("Q")
            for _ in range(n):
                nr, x, y, z, r, g, b, fehler, n_spur = le.lies("Q3d3BdQ")
                roh = datei.read(8 * n_spur)
                if len(roh) != 8 * n_spur:
                    raise _kn.KontextNetzError("points3D.bin endet in einer Spur.")
                yield nr, x, y, z, r, g, b, fehler, list(struct.iter_unpack("<II", roh))
        return
    for zeile in _kn._textzeilen(p):
        t = zeile.split()
        if not t:
            continue
        spur = [(int(t[k]), int(t[k + 1])) for k in range(8, len(t) - 1, 2)]
        yield (int(t[0]), float(t[1]), float(t[2]), float(t[3]), int(t[4]), int(t[5]),
               int(t[6]), float(t[7]), spur)


def colmap_als_text(aufnahme, ziel, *, mit_punkten: bool = COLMAP_MIT_PUNKTEN) -> dict:
    """Die Aufnahme als ``cameras.txt``, ``images.txt``, ``points3D.txt`` (COLMAP-3-Textformat).

    Das Format ist das der COLMAP-Dokumentation («Output Format → Text Format»):

    * ``cameras.txt`` — je Kamera ``CAMERA_ID MODEL WIDTH HEIGHT PARAMS[]``;
    * ``images.txt`` — je Bild **zwei** Zeilen: ``IMAGE_ID QW QX QY QZ TX TY TZ CAMERA_ID
      NAME``, dann ``POINTS2D[]`` als ``X Y POINT3D_ID`` (leer erlaubt);
    * ``points3D.txt`` — je Punkt ``POINT3D_ID X Y Z R G B ERROR TRACK[]`` mit
      ``TRACK[]`` als ``IMAGE_ID POINT2D_IDX``.

    **Je Bild seine eigene Pose** (``cam_from_world``), auch beim Rig: COLMAP 4 schreibt sie
    fertig in ``images`` (:func:`aiimaging.kontext_netz.lies_aufnahme`); ``rigs``/``frames``
    entfallen, COLMAP 3 kennt sie nicht. **Bildnamen unverändert** (``back/0031.jpg``).

    Args:
        mit_punkten: ``False`` schreibt ``points3D.txt`` leer und die 2D-Zeilen leer
            (:data:`COLMAP_MIT_PUNKTEN`, offene Frage).

    Returns:
        ``{images_txt, bilder, kameras, punkte3d, beobachtungen, rig}`` — ``images_txt`` ist
        ein Pfad für den Lauf, nie für den Bericht.

    Raises:
        RealityScanError: Aufnahme nicht lesbar, oder ein Bildname mit Leerzeichen (im
            Textformat endet der Name am Leerzeichen).
    """
    o, z = Path(aufnahme), Path(ziel)
    try:
        a = _kn.lies_aufnahme(o)
    except _kn.KontextNetzError as fehler:
        raise RealityScanError(f"Aufnahme nicht lesbar: {fehler}", URSACHE_AUFNAHME) from fehler
    leer = [b["name"] for b in a["bilder"].values() if re.search(r"\s", b["name"])]
    if leer:
        raise RealityScanError(f"{len(leer)} Bildname(n) mit Leerzeichen — im COLMAP-Text "
                               "nicht darstellbar.", URSACHE_AUFNAHME)
    z.mkdir(parents=True, exist_ok=True)
    try:
        with open(z / "cameras.txt", "w", encoding="utf-8", newline="\n") as d:
            d.write("# Camera list with one line of data per camera:\n"
                    "#   CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]\n"
                    f"# Number of cameras: {len(a['kameras'])}\n")
            for nr in sorted(a["kameras"]):
                k = a["kameras"][nr]
                d.write(f"{nr} {k['modell']} {k['breite']} {k['hoehe']} "
                        + " ".join(_zahl(w) for w in k["params"]) + "\n")
        # Zwei Durchgänge über die 2D-Punkte: Der Kopf nennt ihre mittlere Zahl, wie COLMAP.
        beobachtungen = (sum(len(pk) for _, pk in _bilder_2d(o)) if mit_punkten else 0)
        n_bilder = len(a["bilder"])
        with open(z / "images.txt", "w", encoding="utf-8", newline="\n") as d:
            d.write("# Image list with two lines of data per image:\n"
                    "#   IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME\n"
                    "#   POINTS2D[] as (X, Y, POINT3D_ID)\n"
                    f"# Number of images: {n_bilder}, mean observations per image: "
                    f"{_zahl(beobachtungen / max(1, n_bilder))}\n")
            for nr, punkte in _bilder_2d(o):
                if nr not in a["bilder"]:
                    raise RealityScanError(f"Bild {nr} fehlt beim zweiten Lesen.",
                                           URSACHE_AUFNAHME)
                b = a["bilder"][nr]
                d.write(f"{nr} " + " ".join(_zahl(w) for w in (*b["q"], *b["t"]))
                        + f" {b['kamera']} {b['name']}\n")
                d.write(" ".join(f"{_zahl(x)} {_zahl(y)} {pid}" for x, y, pid in punkte)
                        + "\n" if mit_punkten else "\n")
        n_punkte = spuren = 0
        if mit_punkten:
            for *_, spur in _punkte_3d(o):
                n_punkte += 1
                spuren += len(spur)
        with open(z / "points3D.txt", "w", encoding="utf-8", newline="\n") as d:
            d.write("# 3D point list with one line of data per point:\n"
                    "#   POINT3D_ID, X, Y, Z, R, G, B, ERROR, TRACK[] as "
                    "(IMAGE_ID, POINT2D_IDX)\n"
                    f"# Number of points: {n_punkte}, mean track length: "
                    f"{_zahl(spuren / max(1, n_punkte))}\n")
            if mit_punkten:
                for nr, x, y, zz, r, g, b, fehler, spur in _punkte_3d(o):
                    d.write(f"{nr} {_zahl(x)} {_zahl(y)} {_zahl(zz)} {r} {g} {b} "
                            f"{_zahl(fehler)}"
                            + "".join(f" {bild} {idx}" for bild, idx in spur) + "\n")
    except (_kn.KontextNetzError, struct.error, ValueError, IndexError, OSError) as fehler:
        raise RealityScanError(f"Aufnahme nicht als Text schreibbar: {type(fehler).__name__}: "
                               f"{ohne_pfade(fehler)}", URSACHE_AUFNAHME) from fehler
    return {"images_txt": str(z / "images.txt"), "bilder": n_bilder,
            "kameras": len(a["kameras"]), "punkte3d": n_punkte,
            "beobachtungen": beobachtungen, "rig": a["rig"]}


# ======================================================================================
# Die Fotos
# ======================================================================================

def finde_bilder(aufnahme, bilder=None) -> dict:
    """Die Fotos der Aufnahme — nach der Konvention ``<sparse/0>/../../images``.

    So liegt es am Heim-PC (nachgesehen 13.10.2026): ``<lauf>/sparse/0`` und
    ``<lauf>/images/{front,back,left,right}/NNNN.jpg``, die Bildnamen der Aufnahme relativ zu
    ``<lauf>/images``. Erst neben dem Pfad, wie er kommt, dann neben seinem Ziel (Verweise,
    wie bei :func:`aiimaging.kontext_netz.aufnahme_kandidaten`).

    **Alle** Bilder der Aufnahme müssen da sein: Mit einem Teil ergäbe RealityScan ein
    anderes Netz, als der Speicherschlüssel verspricht.

    Args:
        bilder: ein Ordner ausdrücklich, statt der Konvention.

    Returns:
        ``{gefunden, ordner, anzahl, fehlend, beispiele, sha256, grund}`` — ``ordner`` nur für
        den Lauf; ``beispiele`` sind Bildnamen (relativ, ohne Pfad); ``sha256`` über Namen
        und Grössen (für den Speicherschlüssel).
    """
    leer = {"gefunden": False, "ordner": None, "anzahl": 0, "fehlend": 0, "beispiele": [],
            "sha256": None, "grund": None}
    try:
        namen = sorted(b["name"] for b in _kn.lies_aufnahme(aufnahme)["bilder"].values())
    except _kn.KontextNetzError as fehler:
        return dict(leer, grund=f"Aufnahme nicht lesbar: {ohne_pfade(fehler)}")
    if bilder is not None:
        kandidaten = [Path(bilder)]
    else:
        a = Path(aufnahme)
        kandidaten = []
        for q in (a, _kn._aufgeloest(a)):
            k = q.parent.parent / "images"
            if k not in kandidaten:
                kandidaten.append(k)
    bester = None
    for ordner in kandidaten:
        if not ordner.is_dir():
            continue
        groessen, fehlend = [], []
        for name in namen:
            p = ordner / name
            if p.is_file():
                groessen.append((name, p.stat().st_size))
            else:
                fehlend.append(name)
        if not fehlend:
            summe = hashlib.sha256("\n".join(f"{n} {g}" for n, g in groessen)
                                   .encode("utf-8")).hexdigest()
            return {"gefunden": True, "ordner": ordner, "anzahl": len(namen), "fehlend": 0,
                    "beispiele": [], "sha256": summe, "grund": None}
        if bester is None or len(fehlend) < len(bester):
            bester = fehlend
    if bester is None:
        return dict(leer, anzahl=len(namen),
                    grund=("Bilderordner nicht gefunden" + (" (ausdruecklich genannt)"
                           if bilder is not None else " (Konvention <sparse/0>/../../images)")
                           + "."))
    return dict(leer, anzahl=len(namen), fehlend=len(bester), beispiele=bester[:3],
                grund=f"{len(bester)} von {len(namen)} Bildern der Aufnahme fehlen im "
                      f"Bilderordner (z. B. {', '.join(bester[:3])}).")


# ======================================================================================
# Die Befehlsfolge
# ======================================================================================

def kommando(*, cli, exe, bilder, images_txt, netz_ply, export_xml,
             ziel_dreiecke: int = ZIEL_DREIECKE, bilder_weg: str = BILDER_WEG,
             modell: str = MODELL_NAME) -> list[str]:
    """Die Befehlsfolge für ``realityscan-cli`` — als **Liste**, für ``subprocess`` ohne Shell.

    **Keine Anführungszeichen in den Elementen:** Die Doku zeigt ``"…"`` für die Shell; als
    Liste kommt jedes Element als ein Argument an, auch mit Leerzeichen (``Program Files``).
    Ein Anführungszeichen im Element käme als Zeichen an und machte den Pfad falsch.

    Die Reihenfolge (Doku RealityScan, Befehlszeile, gelesen 13.10.2026):
    ``-headless`` (nur als erster Befehl erlaubt), ``-newScene``, ``-set appIncSubdirs=true``
    (Unterordner bei ``-addFolder``), die Bilder (:data:`BILDER_WEG`), ``-importColmap``,
    ``-align``, ``-selectMaximalComponent``, ``-setReconstructionRegionAuto``,
    ``-calculateNormalModel``, ``-simplify``, ``-calculateVertexColors``, ``-exportModel``,
    ``-quit``. Alle Pfade für das Programm als ``Z:``-Pfade (:func:`wine_pfad`); ``exe`` ist
    der Linux-Pfad, wie ihn ``realityscan-cli`` laut Doku erwartet.

    Raises:
        RealityScanError: unbekannter Bilderweg oder keine positive Dreieckszahl.
    """
    if bilder_weg not in BILDER_WEGE:
        raise RealityScanError(f"Bilderweg {bilder_weg!r} unbekannt (erlaubt: "
                               f"{', '.join(BILDER_WEGE)}).", URSACHE_EINRICHTUNG)
    if int(ziel_dreiecke) <= 0:
        raise RealityScanError("ziel_dreiecke muss positiv sein.", URSACHE_EINRICHTUNG)
    cmd = [str(cli), str(exe), "-headless", "-newScene", "-set", "appIncSubdirs=true"]
    if bilder_weg == BILDER_WEG_ORDNER:
        cmd += ["-addFolder", wine_pfad(bilder)]
    cmd += ["-importColmap", wine_pfad(images_txt),
            "-align", "-selectMaximalComponent", "-setReconstructionRegionAuto",
            "-calculateNormalModel",
            "-simplify", str(int(ziel_dreiecke)),
            "-calculateVertexColors",
            "-exportModel", str(modell), wine_pfad(netz_ply), wine_pfad(export_xml),
            "-quit"]
    return cmd


# ======================================================================================
# Das exportierte Netz lesen und prüfen
# ======================================================================================

def _vertex_form(kopf: dict, name: str) -> tuple[str, list[str], int]:
    """``(struct-Form, Namen, Bytes)`` des ersten Elements — es muss ``vertex`` sein."""
    elemente = kopf["elemente"]
    if not elemente or elemente[0]["name"] != "vertex":
        raise RealityScanError(f"{name!r}: das erste PLY-Element ist nicht 'vertex'.",
                               URSACHE_EXPORT)
    form, namen = "", []
    for e in elemente[0]["eigenschaften"]:
        if e["typ"] == "list":
            raise RealityScanError(f"{name!r}: Liste unter den Ecken.", URSACHE_EXPORT)
        form += _kn.PLY_TYPEN[e["typ"]][0]
        namen.append(e["name"])
    rand = "<" if kopf["format"] == "binary_little_endian" else ">"
    return rand + form, namen, struct.calcsize(rand + form)


def lies_ecken(pfad, *, hoechstens: int = LAGE_ECKEN_MAX, voll: bool = True,
               dicht: bool = False) -> dict:
    """Ecken einer PLY lesen: Stichprobe, Hüllbox, Farbe — nur die Standardbibliothek.

    Args:
        voll: ``True`` liest alle Ecken (genaue Hüllbox, für das Netz); ``False`` springt zu
            den Stichproben (für einen grossen Splat, dessen Hüllbox hier nicht gebraucht wird).
        dicht: nur Punkte mit Deckkraft ≥ :data:`aiimaging.kontext_netz.DECKKRAFT_DICHT`
            (Splat); ohne ``opacity`` alle.

    Returns:
        ``{n, probe, lo, hi, farbe, eigenschaften}`` — ``farbe`` heisst ``red``, ``green``,
        ``blue`` sind Eigenschaften der Ecken.

    Raises:
        RealityScanError: nicht lesbar.
    """
    p = Path(pfad)
    try:
        kopf = _kn.lies_ply_kopf(p)
    except _kn.KontextNetzError as fehler:
        raise RealityScanError(str(fehler), URSACHE_EXPORT) from fehler
    vertex = _kn._element(kopf, "vertex")
    if vertex is None:
        raise RealityScanError(f"{p.name!r} hat keine Ecken.", URSACHE_EXPORT)
    namen_alle = [e["name"] for e in vertex["eigenschaften"]]
    n = vertex["anzahl"]
    schritt = max(1, -(-n // max(1, int(hoechstens))))
    probe: list[tuple[float, float, float]] = []
    lo = [math.inf] * 3
    hi = [-math.inf] * 3

    def nimm(i: int, werte: dict) -> None:
        punkt = (float(werte["x"]), float(werte["y"]), float(werte["z"]))
        if voll:
            for k in range(3):
                lo[k] = min(lo[k], punkt[k])
                hi[k] = max(hi[k], punkt[k])
        if i % schritt == 0:
            if dicht and "opacity" in werte:
                o = float(werte["opacity"])
                if 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, o)))) < _kn.DECKKRAFT_DICHT:
                    return
            probe.append(punkt)

    if not {"x", "y", "z"} <= set(namen_alle):
        raise RealityScanError(f"{p.name!r}: Ecken ohne x/y/z.", URSACHE_EXPORT)
    try:
        if kopf["format"] == "ascii":
            with open(p, "rb") as datei:
                datei.seek(kopf["kopf_bytes"])
                for i in range(n):
                    t = datei.readline().split()
                    nimm(i, dict(zip(namen_alle, t)))
        else:
            form, namen, groesse = _vertex_form(kopf, p.name)
            st = struct.Struct(form)
            with open(p, "rb") as datei:
                datei.seek(kopf["kopf_bytes"])
                if voll:
                    i = 0
                    block = 1 << 16
                    while i < n:
                        k = min(block, n - i)
                        roh = datei.read(k * groesse)
                        if len(roh) != k * groesse:
                            raise RealityScanError(f"{p.name!r} endet in den Ecken.",
                                                   URSACHE_EXPORT)
                        for werte in st.iter_unpack(roh):
                            nimm(i, dict(zip(namen, werte)))
                            i += 1
                else:
                    for i in range(0, n, schritt):
                        datei.seek(kopf["kopf_bytes"] + i * groesse)
                        roh = datei.read(groesse)
                        if len(roh) != groesse:
                            raise RealityScanError(f"{p.name!r} endet in den Ecken.",
                                                   URSACHE_EXPORT)
                        nimm(i, dict(zip(namen, st.unpack(roh))))
    except (OSError, ValueError, struct.error, KeyError) as fehler:
        raise RealityScanError(f"{p.name!r}: Ecken nicht lesbar ({type(fehler).__name__}).",
                               URSACHE_EXPORT) from fehler
    return {"n": n, "probe": probe[:max(1, int(hoechstens))],
            "lo": lo if voll and n else None, "hi": hi if voll and n else None,
            "farbe": {"red", "green", "blue"} <= set(namen_alle),
            "eigenschaften": namen_alle}


def pruefe_export(pfad) -> dict:
    """Ist der Export das, was die Blender-Stufe lädt? PLY **mit Flächen** (``element face``,
    daran erkennt sie ein Netz) **und Eckpunktfarbe** (``red``/``green``/``blue``).

    Returns:
        ``{datei, bytes, sha256, ecken, dreiecke, format, huellbox, probe}``.

    Raises:
        RealityScanError: ``lauf``, wenn keine Datei da ist (das Programm hat nicht
            exportiert); ``export``, wenn sie da ist, aber keine Flächen oder keine Farbe trägt.
    """
    p = Path(pfad)
    if not p.is_file() or p.stat().st_size == 0:
        raise RealityScanError("RealityScan hat kein Netz exportiert (keine Datei).",
                               URSACHE_LAUF)
    try:
        kopf = _kn.lies_ply_kopf(p)
    except _kn.KontextNetzError as fehler:
        raise RealityScanError(f"Der Export ist keine lesbare PLY: {fehler} Die "
                               "Export-Parameterdatei muss PLY waehlen.",
                               URSACHE_EXPORT) from fehler
    if not _kn.ist_netz(kopf):
        raise RealityScanError("Der Export traegt keine Flaechen (element face) — die "
                               "Blender-Stufe erkennt daran ein Netz.", URSACHE_EXPORT)
    ecken = lies_ecken(p, voll=True)
    if not ecken["farbe"]:
        raise RealityScanError("Der Export traegt keine Eckpunktfarbe (red/green/blue) — die "
                               "Export-Parameterdatei muss Farben je Ecke schreiben.",
                               URSACHE_EXPORT)
    kennzahlen = _kn.netz_kennzahlen(p)
    return {"datei": p.name, "bytes": kennzahlen["bytes"], "sha256": kennzahlen["sha256"],
            "ecken": kennzahlen["ecken"], "dreiecke": kennzahlen["dreiecke"],
            "format": kopf["format"],
            "huellbox": [[round(v, 6) for v in ecken["lo"]], [round(v, 6) for v in ecken["hi"]]],
            "probe": ecken["probe"]}


# ======================================================================================
# Die Lage
# ======================================================================================

def _robuste_box(punkte) -> tuple[list[float], list[float]]:
    lo, hi = [], []
    for k in range(3):
        werte = sorted(p[k] for p in punkte)
        lo.append(_kn._perzentil(werte, _kn.ANTEIL_UNTEN))
        hi.append(_kn._perzentil(werte, _kn.ANTEIL_OBEN))
    return lo, hi


def _diagonale(lo, hi) -> float:
    return math.sqrt(sum((hi[k] - lo[k]) ** 2 for k in range(3)))


def nah_anteil(proben, bezug, zelle: float) -> float:
    """Welcher Anteil der ``proben`` einen ``bezug``-Punkt in der eigenen oder einer der 26
    Nachbarzellen hat (Würfel der Kante ``zelle``). 0 ohne Proben oder Bezug.

    Ein Gitter statt eines Suchbaums: Die Standardbibliothek hat keinen, und für «liegt etwas
    in der Nähe?» genügt die Zelle — linear in der Zahl der Punkte.
    """
    liste = list(proben)
    if not liste or not bezug or not zelle > 0:
        return 0.0
    belegt = {(math.floor(b[0] / zelle), math.floor(b[1] / zelle), math.floor(b[2] / zelle))
              for b in bezug}
    nachbarn = [(i, j, k) for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1)]
    nah = 0
    for p in liste:
        c = (math.floor(p[0] / zelle), math.floor(p[1] / zelle), math.floor(p[2] / zelle))
        if any((c[0] + i, c[1] + j, c[2] + k) in belegt for i, j, k in nachbarn):
            nah += 1
    return nah / len(liste)


def lage_befund(*, ecken, punkte, splat_punkte=None) -> dict:
    """Liegt das Netz dort, wo die Aufnahme liegt? Das Urteil aus Punkten — ohne Pfad.

    Dieselbe Haltung wie :func:`aiimaging.kontext_netz.gleichheit_befund`: alles **relativ
    zur Diagonale** der COLMAP-Punkte (P2–P98), weil die Einheiten der Aufnahme keine Meter
    sind; und **nicht prüfbar ist nicht bestanden**.

    Geprüft wird:

    1. ``nah_colmap`` — Anteil der COLMAP-Punkte (im robusten Bereich) mit einer Ecke des
       Netzes in der Nähe (:func:`nah_anteil`, Zelle :data:`LAGE_ZELLE_REL` × Diagonale),
       mindestens :data:`LAGE_NAH_MIN`. Eine Verschiebung, Drehung oder Skalierung durch
       RealityScan trennt Netz und Punkte fast überall.
    2. ``massstab`` — Diagonale des Netzes zu der der Punkte, höchstens
       :data:`LAGE_MASSSTAB_MAX` in beide Richtungen.
    3. ``nah_splat`` (nur mit ``splat_punkte``) — Anteil der Ecken mit einer dichten
       Splat-Mitte in der Nähe, mindestens :data:`LAGE_NAH_MIN`: Das Netz geht in Blender
       mit der **Matrix des Splats**; liegt es nicht beim Splat, steht es am falschen Ort.

    Returns:
        ``{passt, nah_colmap, nah_splat, massstab, mitte_rel, n_ecken, n_punkte, n_splat,
        schwellen, grund}``.
    """
    schwellen = {"zelle_rel": LAGE_ZELLE_REL, "nah_min": LAGE_NAH_MIN,
                 "massstab_max": LAGE_MASSSTAB_MAX}
    ecken, punkte = list(ecken), list(punkte)
    splat = None if splat_punkte is None else list(splat_punkte)
    aus = {"passt": False, "nah_colmap": None, "nah_splat": None, "massstab": None,
           "mitte_rel": None, "n_ecken": len(ecken), "n_punkte": len(punkte),
           "n_splat": None if splat is None else len(splat), "schwellen": schwellen,
           "grund": None}
    if len(punkte) < 4:
        aus["grund"] = ("Die Aufnahme hat keine COLMAP-Punkte (points3D) — ob das Netz bei "
                        "ihr liegt, ist nicht pruefbar.")
        return aus
    if len(ecken) < 4:
        aus["grund"] = "Das Netz hat zu wenige Ecken fuer eine Lagepruefung."
        return aus
    lo_p, hi_p = _robuste_box(punkte)
    lo_m, hi_m = _robuste_box(ecken)
    d_p, d_m = _diagonale(lo_p, hi_p), _diagonale(lo_m, hi_m)
    if not (d_p > 0 and math.isfinite(d_p)):
        aus["grund"] = "Die COLMAP-Punkte haben keine Ausdehnung."
        return aus
    zelle = LAGE_ZELLE_REL * d_p
    innen = [p for p in punkte if all(lo_p[k] <= p[k] <= hi_p[k] for k in range(3))]
    aus["nah_colmap"] = round(nah_anteil(innen, ecken, zelle), 4)
    aus["massstab"] = round(d_m / d_p, 4)
    mitte_p = [(lo_p[k] + hi_p[k]) / 2 for k in range(3)]
    mitte_m = [(lo_m[k] + hi_m[k]) / 2 for k in range(3)]
    aus["mitte_rel"] = round(_diagonale(mitte_p, mitte_m) / d_p, 4)
    if splat is not None:
        aus["nah_splat"] = round(nah_anteil(ecken, splat, zelle), 4)
    gruende = []
    if aus["nah_colmap"] < LAGE_NAH_MIN:
        gruende.append(f"nur {aus['nah_colmap']:.0%} der COLMAP-Punkte haben das Netz in der "
                       f"Naehe (mindestens {LAGE_NAH_MIN:.0%})")
    if not (1.0 / LAGE_MASSSTAB_MAX <= aus["massstab"] <= LAGE_MASSSTAB_MAX):
        gruende.append(f"Diagonale des Netzes {aus['massstab']:.2f}-mal die der Aufnahme "
                       f"(erlaubt 1/{LAGE_MASSSTAB_MAX:g} bis {LAGE_MASSSTAB_MAX:g})")
    if aus["nah_splat"] is not None and aus["nah_splat"] < LAGE_NAH_MIN:
        gruende.append(f"nur {aus['nah_splat']:.0%} der Ecken liegen beim Splat "
                       f"(mindestens {LAGE_NAH_MIN:.0%})")
    if gruende:
        aus["grund"] = ("Das Netz aus RealityScan liegt nicht bei der Aufnahme (neu gelagert "
                        "oder skaliert?): " + "; ".join(gruende) + ".")
    else:
        aus["passt"] = True
    return aus


def lage_pruefen(ecken, aufnahme, splat=None) -> dict:
    """:func:`lage_befund` mit den Punkten der Aufnahme und, wenn genannt, des Splats."""
    try:
        punkte = _kn.lies_punkte3d(aufnahme, LAGE_PROBEN)
    except _kn.KontextNetzError:
        punkte = []
    splat_punkte = None
    if splat is not None:
        try:
            if _kn.art_der_datei(splat) == "splat":
                splat_punkte = lies_ecken(splat, hoechstens=LAGE_PROBEN, voll=False,
                                          dicht=True)["probe"]
        except (_kn.KontextNetzError, RealityScanError):
            splat_punkte = None
    return lage_befund(ecken=ecken, punkte=punkte, splat_punkte=splat_punkte)


# ======================================================================================
# Der Lauf
# ======================================================================================

def _speicher(speicher) -> Path:
    if speicher is not None:
        return Path(speicher)
    if (env := os.environ.get(REALITYSCAN_SPEICHER_ENV)):
        return Path(env)
    wurzel = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(wurzel) / "aiimaging" / "realityscan-netz"


def _datei_sha(pfad) -> str:
    summe = hashlib.sha256()
    with open(pfad, "rb") as datei:
        for stueck in iter(lambda: datei.read(1 << 20), b""):
            summe.update(stueck)
    return summe.hexdigest()


def realityscan_schluessel(*, aufnahme_sha: str, bilder_sha: str, export_xml_sha: str,
                           parameter: dict) -> str:
    """Der Speicherschlüssel eines Netzes: sha256 der Aufnahme (``cameras``/``images``/
    ``frames``/``rigs``), der Bildnamen samt Grössen, des **Inhalts** der Export-Parameterdatei
    und der Parameter (Fassung, Befehlsfolge, Zahlen).

    Der Inhalt, nicht der Pfad (wie :func:`aiimaging.seams.splat_schluessel`): Andere Fotos,
    eine andere Exportdatei oder eine andere Befehlsfolge ergeben ein anderes Netz.
    """
    inhalt = {"aufnahme": aufnahme_sha, "bilder": bilder_sha, "export_xml": export_xml_sha,
              "parameter": parameter}
    text = json.dumps(inhalt, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


_FASSUNG_AUSGABE = re.compile(r"RealityScan[^\d\n]{0,24}(\d+\.\d+(?:\.\d+){0,3})")


def _programm_fassung(*texte) -> str | None:
    for t in texte:
        if (m := _FASSUNG_AUSGABE.search(str(t or ""))):
            return m.group(1)
    return None


def _aus_speicher(netz: Path, bericht_datei: Path) -> dict | None:
    if not bericht_datei.is_file():
        return None
    try:
        bericht = json.loads(bericht_datei.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(bericht, dict):
        return None
    if bericht.get("status") == "ungueltig":
        return bericht
    if bericht.get("status") != "ok" or not netz.is_file():
        return None
    try:
        if _kn.netz_kennzahlen(netz)["sha256"] != (bericht.get("netz") or {}).get("sha256"):
            return None
    except _kn.KontextNetzError:
        return None
    return bericht


def realityscan_zu_netz(aufnahme, *, ziel=None, speicher=None, bilder=None, splat=None,
                        bilder_weg: str = BILDER_WEG, ziel_dreiecke: int = ZIEL_DREIECKE,
                        mit_punkten: bool = COLMAP_MIT_PUNKTEN,
                        timeout: float = GESAMTFRIST_REALITYSCAN_S, _starte=None) -> dict:
    """Aufnahme + Fotos → farbiges Netz (PLY) über RealityScan — als Prozess, mit Prüfung.

    **Zwischengespeichert** nach :func:`realityscan_schluessel`: Ein Lauf dauert Stunden, der
    Abholer fragt je Auftrag. Gespeichert wird auch ein Export, der **da, aber unbrauchbar**
    ist (Ursache ``export``) — er hängt an der Exportdatei, und deren Inhalt steht im
    Schlüssel; ein neuer Lauf brächte dasselbe. **Nicht** gespeichert wird ein gescheiterter
    Lauf (Ursache ``lauf``: Frist, Absturz, Lizenz) — der kann beim nächsten Mal gelingen.

    Nach dem Export (und bei jedem Treffer) prüft :func:`lage_pruefen`, ob das Netz bei der
    Aufnahme liegt (und beim Splat, wenn ``splat`` genannt ist). Liegt es daneben, wird es
    nicht benutzt (Ursache ``lage``); das Netz bleibt im Speicher, die Prüfung ist billig.

    Args:
        aufnahme: der COLMAP-Ordner (``sparse/0``).
        ziel: wohin das Netz zusätzlich kopiert wird; sonst bleibt es im Speicher.
        speicher: Ablage; sonst :data:`REALITYSCAN_SPEICHER_ENV`, sonst
            ``~/.cache/aiimaging/realityscan-netz``.
        bilder: der Bilderordner ausdrücklich; sonst :func:`finde_bilder`.
        splat: der Splat, gegen dessen dichte Punkte die Lage zusätzlich geprüft wird.
        _starte: Test-Naht wie in :mod:`aiimaging.seams` — ``(cmd, timeout) → CompletedProcess``.

    Returns:
        Bericht **ohne Pfade** — ``{status, fassung, programm, zeiten_s, netz, aufnahme,
        bilder, export_xml, parameter, ausgabe, lage, zwischenspeicher}`` — und dazu
        ``netz_ply`` (Pfad, nur für den Multipass; geht nie nach aussen).

    Raises:
        RealityScanError: mit ``ursache`` und Grund ohne Pfad.
    """
    from aiimaging import seams as _seams                  # spät: seams lädt dieses Modul

    t0 = time.monotonic()
    e = einrichtung()
    if not e["bereit"]:
        raise RealityScanError(e["grund"], e["ursache"])
    o = Path(aufnahme)
    if not _kn.ist_aufnahme_ordner(o):
        raise RealityScanError("Keine COLMAP-Aufnahme (images und cameras fehlen).",
                               URSACHE_AUFNAHME)
    fund = finde_bilder(o, bilder)
    if not fund["gefunden"]:
        raise RealityScanError(fund["grund"], URSACHE_BILDER)
    try:
        aufnahme_sha = _kn.aufnahme_fingerabdruck(o)["sha256"]
        xml_sha = _datei_sha(e["export_xml"])
    except (_kn.KontextNetzError, OSError) as fehler:
        raise RealityScanError(ohne_pfade(fehler), URSACHE_AUFNAHME) from fehler
    parameter = {"fassung": FASSUNG, "bilder_weg": bilder_weg,
                 "ziel_dreiecke": int(ziel_dreiecke), "modell": MODELL_NAME,
                 "mit_punkten": bool(mit_punkten)}
    schluessel = realityscan_schluessel(aufnahme_sha=aufnahme_sha, bilder_sha=fund["sha256"],
                                        export_xml_sha=xml_sha, parameter=parameter)
    ordner = _speicher(speicher) / schluessel
    netz = ordner / "netz.ply"
    bericht_datei = ordner / "bericht.json"
    ersatz = {str(e["cli"]): "<realityscan-cli>", str(e["exe"]): "<RealityScan.exe>",
              str(e["export_xml"]): "<export.xml>", str(fund["ordner"]): "<bilder>",
              str(o): "<aufnahme>", str(ordner): "<speicher>"}

    bericht = _aus_speicher(netz, bericht_datei)
    if bericht is not None and bericht.get("status") == "ungueltig":
        raise RealityScanError(f"{bericht.get('grund')} (aus dem Speicher; eine andere "
                               "Export-Parameterdatei ergibt einen neuen Lauf)",
                               URSACHE_EXPORT, bericht)
    if bericht is not None:
        bericht["zwischenspeicher"] = {"treffer": True, "schluessel": schluessel}
        probe = lies_ecken(netz, voll=False)["probe"]
    else:
        frist = float(timeout) * _seams.zeitfaktor()
        starte = _starte or _seams._default_starte
        ordner.mkdir(parents=True, exist_ok=True)
        try:
            with tempfile.TemporaryDirectory(dir=ordner, prefix="lauf-") as roh:
                roh = Path(roh)
                ersatz[str(roh)] = "<arbeit>"
                t_text = time.monotonic()
                text = colmap_als_text(o, roh / "colmap", mit_punkten=mit_punkten)
                roh_netz = roh / "netz.ply"
                cmd = kommando(cli=e["cli"], exe=e["exe"], bilder=fund["ordner"],
                               images_txt=text["images_txt"], netz_ply=roh_netz,
                               export_xml=e["export_xml"], ziel_dreiecke=ziel_dreiecke,
                               bilder_weg=bilder_weg)
                t_lauf = time.monotonic()
                try:
                    ergebnis = starte(cmd, frist)
                except subprocess.TimeoutExpired as fehler:
                    raise RealityScanError(f"RealityScan nach {frist:.0f} s abgebrochen "
                                           "(Frist).", URSACHE_LAUF) from fehler
                except OSError as fehler:
                    raise RealityScanError(f"RealityScan liess sich nicht starten: "
                                           f"{ohne_pfade(fehler, ersatz)}",
                                           URSACHE_LAUF) from fehler
                t_ende = time.monotonic()
                ausgabe = {"stdout": ohne_pfade(ergebnis.stdout, ersatz)[-AUSGABE_ZEICHEN:],
                           "stderr": ohne_pfade(ergebnis.stderr, ersatz)[-AUSGABE_ZEICHEN:]}
                if ergebnis.returncode != 0:
                    raise RealityScanError(
                        f"RealityScan endete mit Code {ergebnis.returncode}: "
                        f"{(ausgabe['stderr'] or ausgabe['stdout'])[-400:]}", URSACHE_LAUF,
                        {"ausgabe": ausgabe})
                bericht = {
                    "status": "ok", "fassung": FASSUNG,
                    "programm": {"fassung": _programm_fassung(ergebnis.stdout,
                                                              ergebnis.stderr)},
                    "zeiten_s": {"umschrift_s": round(t_lauf - t_text, 3),
                                 "lauf_s": round(t_ende - t_lauf, 3)},
                    "aufnahme": {"sha256": aufnahme_sha, "bilder": text["bilder"],
                                 "kameras": text["kameras"], "rig": text["rig"],
                                 "punkte3d": text["punkte3d"],
                                 "beobachtungen": text["beobachtungen"]},
                    "bilder": {"anzahl": fund["anzahl"], "sha256": fund["sha256"]},
                    "export_xml": {"sha256": xml_sha},
                    "parameter": parameter, "ausgabe": ausgabe,
                }
                try:
                    export = pruefe_export(roh_netz)
                except RealityScanError as fehler:
                    if fehler.ursache == URSACHE_EXPORT:
                        # GESPEICHERT, damit ein unbrauchbarer Export nicht bei jedem Auftrag
                        # Stunden kostet; der Schluessel haengt an der Exportdatei.
                        bericht.update(status="ungueltig", grund=fehler.grund)
                        bericht_datei.write_text(json.dumps(bericht, ensure_ascii=False,
                                                            indent=1), encoding="utf-8")
                        fehler.bericht = bericht
                    raise
                probe = export.pop("probe")
                export["vereinfacht"] = export["dreiecke"] <= int(1.1 * int(ziel_dreiecke))
                bericht["netz"] = export
                os.replace(roh_netz, netz)
                bericht_datei.write_text(json.dumps(bericht, ensure_ascii=False, indent=1),
                                         encoding="utf-8")
        except BaseException:
            try:
                ordner.rmdir()                        # nur, wenn leer
            except OSError:
                pass
            raise
        bericht["zwischenspeicher"] = {"treffer": False, "schluessel": schluessel}

    bericht["lage"] = lage_pruefen(probe, o, splat)
    bericht.setdefault("zeiten_s", {})["gesamt_s"] = round(time.monotonic() - t0, 3)
    if not bericht["lage"]["passt"]:
        raise RealityScanError(bericht["lage"]["grund"], URSACHE_LAGE, bericht)
    ausgabe_pfad = netz
    if ziel is not None:
        ausgabe_pfad = Path(ziel)
        ausgabe_pfad.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(netz, ausgabe_pfad)
    bericht["netz_ply"] = str(ausgabe_pfad)
    return bericht


# ======================================================================================
# Zwischenspeicher des Multipass
# ======================================================================================

def treffer_maengel(kontext_weg) -> str | None:
    """Warum ein gespeicherter Multipass **kein** Treffer ist, gemessen an RealityScan — oder
    ``None``.

    **Anlass** (13.10.2026): Der Schlüssel des Kettenknotens kennt den Splat, nicht den Weg,
    auf dem seine Umgebung entstand. Ohne diese Regel bliebe nach dem Einschalten ein altes
    Netz des offenen Wegs ein Treffer — und das Bild zeigte die Löcher, die RealityScan
    schliessen soll. Darum, wie bei den Kugeln (``kette._cache_maengel``):

    * aus RealityScan, aber RealityScan ist **aus** → kein Treffer (abgeschaltet heisst
      abgeschaltet);
    * nicht aus RealityScan, RealityScan ist **ein**, und der Eintrag entstand ohne einen
      Versuch, der am Inhalt hing (:data:`FLUECHTIGE_URSACHEN`) → kein Treffer.

    Ursachen, die am Inhalt hängen (``aufnahme``, ``bilder``, ``export``, ``lage``,
    ``geliefert``), bleiben Treffer: Ein neuer Lauf brächte dasselbe.
    """
    weg = (kontext_weg or {}).get("weg") if isinstance(kontext_weg, dict) else None
    ursache = (kontext_weg or {}).get("realityscan_ursache") if isinstance(kontext_weg,
                                                                            dict) else None
    an = eingeschaltet()
    if weg == WEG and not an:
        return ("Umgebung aus RealityScan, RealityScan inzwischen ausgeschaltet — kein "
                "Treffer.")
    if weg != WEG and an and ursache in FLUECHTIGE_URSACHEN:
        return ("RealityScan eingeschaltet, die Umgebung entstand ohne RealityScan-Versuch "
                "(oder nach einem gescheiterten Lauf) — kein Treffer, damit RealityScan greift.")
    return None
