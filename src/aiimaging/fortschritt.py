"""FORTSCHRITTSWACHE — merkt, dass ein Lauf steht, statt auf den Gesamt-Timeout zu warten.

Das Problem
-----------
Ein Renderlauf, der abstürzt, meldet sich. Ein Renderlauf, der **hängt**, meldet sich
nicht: Der Prozess lebt, die Grafikkarte ist belegt, und nichts geschieht mehr. Bis
gestern hatte dieses Projekt dagegen nur einen **Gesamt-Timeout** — der greift, aber erst
nach der vollen Frist. Bei ``timeout=1800`` sind das dreissig Minuten Wartezeit für eine
Auskunft, die nach fünf Minuten dieselbe gewesen wäre.

Der Altbestand hat dafür eine Lösung, und beim Lesen fiel auf, dass sie **nicht wirkt**
--------------------------------------------------------------------------------------
``archviz_comfyui_bridge.wait_for_completion`` führt neben dem harten ``max_seconds``
einen ``no_progress_timeout`` von 300 Sekunden. Genau das, was uns fehlte. Nur steht in
seinem Rumpf:

.. code-block:: python

    if (time.time() - last_progress_t) > no_progress_timeout:
        if status in ("running", "queued"):
            print(f"[Bridge] Long {status} — weiter warten")
            last_progress_t = time.time()   # reset
        elif status == "unknown":
            ...
        else:
            raise TimeoutError(...)

**Bei ``running`` und ``queued`` wird die Uhr zurückgestellt statt Alarm zu schlagen.**
Das sind die beiden Zustände, in denen ein hängender Sampler steckt — der Wächter feuert
also nie in dem Fall, für den er gebaut wurde. Übrig bleibt er für ``unknown`` und für
Statuswörter, die das Programm nicht kennt. Der harte ``max_seconds`` fängt den Rest,
also genau das, was wir schon haben.

Die Absicht dahinter ist ehrenwert und im Kommentar nachzulesen: Ein langsamer Sampler
soll nicht fälschlich abgebrochen werden. Aber die Lösung wirft die Fähigkeit weg, statt
das Problem zu lösen.

Woran es wirklich liegt, und was dieses Modul anders macht
----------------------------------------------------------
> **Ein Statuswort ist eine Behauptung, kein Beleg.**

„``running``" heisst: Jemand sagt, es laufe. Ob sich etwas bewegt, steht da nicht drin.
Aus einer unveränderten Behauptung lässt sich **langsam** nicht von **hängend**
unterscheiden — und das ist keine Schwäche der Umsetzung, sondern eine des Signals. Wer
an dieser Stelle abbricht, bricht irgendwann einen gesunden Lauf ab; wer die Uhr
zurückstellt, merkt einen Stillstand nie.

Dieses Modul löst das nicht durch eine klügere Frist, sondern indem es die Frage dorthin
verschiebt, wo sie beantwortbar ist:

* Ein **belegter** Fortschritt ist einer, der aus etwas kommt, das sich unabhängig vom
  Erzähler bewegt: ein Schrittzähler, der zählt; eine Datei, die wächst; eine neue Datei,
  die auftaucht.
* Ein **behaupteter** Fortschritt kommt aus einem Statuswort.

Bei belegtem Fortschritt heisst Stillstand wirklich Stillstand — die Wache meldet
``error`` und der Aufrufer darf abbrechen. Bei bloss behauptetem meldet sie ``warn`` und
sagt ausdrücklich dazu, dass sie langsam und hängend nicht auseinanderhalten kann.
Dieselbe Regel wie in :mod:`aiimaging.belichtung`: **Was nicht belegt ist, darf nicht
verurteilen.**

Und die Wache **bricht nichts ab**. Sie beobachtet und meldet; abgebrochen wird eine
Stufe höher, wo man weiss, was ein Abbruch kostet. Eine Bibliothek, die von sich aus
``raise`` sagt, nimmt dem Aufrufer eine Entscheidung ab, die ihm gehört.

Prüfbarkeit
-----------
Die Uhr ist injizierbar (``_uhr``). Ohne das liesse sich ein Stillstand von fünf Minuten
nur prüfen, indem man fünf Minuten wartet — und ein Test, der so teuer ist, läuft nicht,
und ein Test, der nicht läuft, prüft nichts. Dieselbe Bauform wie ``_starte`` in
``seams.py`` und ``einbetter`` in ``stil_qa.py``.

Abhängigkeiten: reine stdlib. Kein ``bpy``, ohne Oberfläche aufrufbar (Regeln 2 und 4).
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from pathlib import Path

#: Wie ein Fortschrittszeichen zustande kam.
BELEGT = "belegt"          #: aus etwas, das sich unabhängig vom Erzähler bewegt
BEHAUPTET = "behauptet"    #: aus einem Statuswort

#: Schweregrade — dieselben Wörter wie in ``graph.pruefe_bedarf`` und
#: ``belichtung.pruefe``, damit alle Befunde dieses Projekts gleich gelesen werden.
SCHWERE_OK = "ok"
SCHWERE_WARN = "warn"
SCHWERE_FEHLER = "error"

#: Vorgabefrist ohne Fortschritt. Dieselbe Zahl wie im Altbestand — **nicht**, weil sie
#: gemessen wäre, sondern damit ein Vergleich möglich bleibt. Sie ist eine Setzung, und
#: sie steht als Parameter und nicht als Naturkonstante.
FRIST_S = 300.0


class FortschrittsError(ValueError):
    """Die Wache ist falsch aufgesetzt. Erbt von ``ValueError`` wie alle Fehler hier."""


@dataclass
class Wache:
    """Beobachtet Fortschrittszeichen und meldet, wenn keines mehr kommt.

    Sie hält **nichts** an und schläft nicht. Der Aufrufer fragt das Backend, reicht das
    Ergebnis mit :meth:`melde` herein und liest den Befund. So bleibt die Wache
    unabhängig davon, ob jemand pollt, auf ein Ereignis wartet oder eine Datei beobachtet.

    Attribute:
        frist_s: Sekunden ohne Fortschritt, ab denen ein Befund entsteht.
        art: :data:`BELEGT` oder :data:`BEHAUPTET` — entscheidet ``error`` gegen ``warn``.
        name: Klartext für den Befund, etwa ``"Renderlauf"``.
    """

    frist_s: float = FRIST_S
    art: str = BEHAUPTET
    name: str = "Lauf"
    _uhr: object = field(default=None, repr=False)
    _zeichen: object = field(default=None, repr=False)

    _marke: object = field(default=None, init=False, repr=False)
    _hat_marke: bool = field(default=False, init=False, repr=False)
    _seit: float = field(default=0.0, init=False, repr=False)
    _begonnen: float = field(default=0.0, init=False, repr=False)
    _schritte: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if isinstance(self.frist_s, bool) or not isinstance(self.frist_s, (int, float)):
            raise FortschrittsError(f"frist_s ist keine Zahl: {self.frist_s!r}")
        if not math.isfinite(float(self.frist_s)) or self.frist_s <= 0:
            raise FortschrittsError(
                f"frist_s muss positiv und endlich sein, war {self.frist_s!r}. Eine "
                f"Frist von 0 hiesse, jeder Lauf steht schon beim ersten Blick."
            )
        if self.art not in (BELEGT, BEHAUPTET):
            raise FortschrittsError(
                f"art ist {self.art!r}; erlaubt sind {BELEGT!r} und {BEHAUPTET!r}. Die "
                f"Angabe entscheidet, ob ein Stillstand verurteilen darf — sie zu raten "
                f"wäre genau die Bequemlichkeit, gegen die dieses Modul gebaut ist."
            )
        if self._uhr is None:
            self._uhr = time.monotonic
        self._begonnen = self._seit = float(self._uhr())

    # ------------------------------------------------------------------ Beobachten

    def melde(self, marke) -> dict:
        """Ein Fortschrittszeichen hereinreichen und den aktuellen Befund lesen.

        Args:
            marke: Irgendetwas Vergleichbares, das sich ändert, **wenn** etwas
                vorangeht — ein Schrittzähler, eine Dateigrösse, ein ``(status, position)``.
                ``None`` ist erlaubt und heisst „im Moment kein Zeichen"; es zählt
                **nicht** als Fortschritt, sonst hielte ein Backend, das nur noch
                schweigt, die Wache am Leben.

        Returns:
            Dasselbe wie :meth:`befund`.
        """
        jetzt = float(self._uhr())
        neu = (not self._hat_marke) or marke != self._marke
        if neu and marke is not None:
            self._marke = marke
            self._hat_marke = True
            self._seit = jetzt
            self._schritte += 1
        elif not self._hat_marke and marke is None:
            # Noch nie ein Zeichen gesehen. Die Uhr läuft ab Beginn — ein Backend, das
            # nie irgendetwas meldet, ist der klarste Stillstandsfall überhaupt.
            pass
        return self.befund()

    def blick(self) -> dict:
        """Das Zeichen **selbst holen** und melden — wenn die Wache eine Quelle hat.

        :func:`wache_fuer_datei` und :func:`wache_fuer_verzeichnis` binden eine; eine
        Wache auf ein blosses Statuswort hat keine, denn das Statuswort kennt nur der
        Aufrufer. Sie sagt das, statt stillschweigend ``None`` zu melden — ein
        stillschweigendes ``None`` sähe aus wie ein Stillstand und wäre keiner.

        Raises:
            FortschrittsError: Diese Wache hat keine eigene Quelle.
        """
        if self._zeichen is None:
            raise FortschrittsError(
                f"Diese Wache ({self.name!r}) hat keine eigene Zeichenquelle — sie "
                f"beobachtet ein Statuswort, und das kennt nur der Aufrufer. Nimm "
                f"melde(marke) statt blick()."
            )
        return self.melde(self._zeichen())

    # ------------------------------------------------------------------ Urteilen

    @property
    def still_seit_s(self) -> float:
        """Sekunden seit dem letzten Fortschrittszeichen."""
        return float(self._uhr()) - self._seit

    @property
    def laeuft_seit_s(self) -> float:
        """Sekunden seit dem Aufsetzen der Wache."""
        return float(self._uhr()) - self._begonnen

    def befund(self) -> dict:
        """Der aktuelle Stand als Befund.

        Returns:
            ``{befund, schwere, art, unterscheidbar, still_seit_s, laeuft_seit_s,
            schritte, detail}``.

            ``befund`` ist ``None``, solange nichts auffällt — ``"stillstand"``, sobald
            die Frist gerissen ist. ``unterscheidbar`` sagt, ob sich aus den vorliegenden
            Zeichen **langsam** von **hängend** trennen lässt; bei
            :data:`BEHAUPTET` ist es ``False``, und dann bleibt es bei ``warn``.
        """
        still = self.still_seit_s
        belegt = self.art == BELEGT
        grund = {
            "befund": None,
            "schwere": SCHWERE_OK,
            "art": self.art,
            "unterscheidbar": belegt,
            "still_seit_s": still,
            "laeuft_seit_s": self.laeuft_seit_s,
            "schritte": self._schritte,
            "detail": "",
        }
        if still <= self.frist_s:
            grund["detail"] = (
                f"{self.name}: letztes Fortschrittszeichen vor {still:.0f} s "
                f"(Frist {self.frist_s:.0f} s, {self._schritte} Zeichen bisher)."
            )
            return grund

        grund["befund"] = "stillstand"
        if belegt:
            grund["schwere"] = SCHWERE_FEHLER
            grund["detail"] = (
                f"{self.name}: seit {still:.0f} s kein Fortschritt (Frist "
                f"{self.frist_s:.0f} s). Das Zeichen ist BELEGT — es kommt aus etwas, das "
                f"sich unabhängig vom Erzähler bewegt. Stillstand heisst hier wirklich "
                f"Stillstand."
            )
        else:
            grund["schwere"] = SCHWERE_WARN
            grund["detail"] = (
                f"{self.name}: seit {still:.0f} s keine Änderung (Frist "
                f"{self.frist_s:.0f} s). Das Zeichen ist nur BEHAUPTET — es kommt aus "
                f"einem Statuswort. Daraus lässt sich LANGSAM nicht von HÄNGEND "
                f"unterscheiden, und darum bleibt es eine Warnung. Wer hier Gewissheit "
                f"will, braucht ein belegtes Zeichen: einen Schrittzähler, eine "
                f"wachsende Datei, eine neue Datei."
            )
        return grund


# ======================================================================================
# Belegte Zeichen — die Antwort auf „woher soll ich das nehmen"
# ======================================================================================

def datei_marke(pfad) -> tuple[int, int] | None:
    """``(Grösse, Änderungszeit in ganzen Sekunden)`` einer Datei, oder ``None``.

    Ein **belegtes** Zeichen: Eine Datei, die wächst, wächst — unabhängig davon, was ein
    Statuswort behauptet. ``None``, solange es sie nicht gibt; das ist kein Fehler,
    sondern der Normalfall zu Beginn eines Laufs.

    Die Änderungszeit wird auf ganze Sekunden abgeschnitten. Manche Dateisysteme führen
    sie feiner, andere nicht, und eine Marke, die sich je nach Dateisystem verschieden
    oft ändert, machte die Wache auf einer Maschine wachsamer als auf der anderen.
    """
    p = Path(pfad)
    try:
        st = p.stat()
    except OSError:
        return None
    return int(st.st_size), int(st.st_mtime)


def verzeichnis_marke(pfad, *, endung: str | None = None) -> tuple[int, int] | None:
    """``(Anzahl Dateien, Gesamtgrösse)`` eines Verzeichnisses, oder ``None``.

    Ebenfalls belegt: Eine neue Datei im Ausgabeordner ist Fortschritt, auch wenn das
    Backend nichts sagt. ``endung`` schränkt auf einen Dateityp ein (``".png"``).

    Gezählt wird **nicht rekursiv**. Ein rekursiver Lauf über einen Ausgabeordner, in dem
    gerade geschrieben wird, kostet bei jedem Blick Zeit und kann selbst zur Bremse
    werden — die Wache soll billig sein, sonst wird sie seltener befragt.
    """
    p = Path(pfad)
    if not p.is_dir():
        return None
    anzahl = 0
    summe = 0
    for eintrag in p.iterdir():
        if endung is not None and eintrag.suffix != endung:
            continue
        try:
            if eintrag.is_file():
                anzahl += 1
                summe += eintrag.stat().st_size
        except OSError:
            continue
    return anzahl, summe


def wache_fuer_datei(pfad, *, frist_s: float = FRIST_S, name: str | None = None,
                     _uhr=None) -> Wache:
    """Eine Wache auf eine wachsende Datei. Die Art ist zwangsläufig :data:`BELEGT`.

    Der Pfad wird **gebunden**: :meth:`Wache.blick` holt sich die Marke selbst. Ein
    Pfadparameter, den die Wache nicht liest, wäre eine tote Kante — genau die Fehlerart,
    gegen die dieses Projekt seit Phase 0 antritt.
    """
    return Wache(frist_s=frist_s, art=BELEGT, name=name or f"Datei {Path(pfad).name}",
                 _uhr=_uhr, _zeichen=lambda: datei_marke(pfad))


def wache_fuer_verzeichnis(pfad, *, endung: str | None = None, frist_s: float = FRIST_S,
                           name: str | None = None, _uhr=None) -> Wache:
    """Eine Wache auf einen Ausgabeordner, in dem Dateien auftauchen. :data:`BELEGT`."""
    return Wache(frist_s=frist_s, art=BELEGT,
                 name=name or f"Ordner {Path(pfad).name}", _uhr=_uhr,
                 _zeichen=lambda: verzeichnis_marke(pfad, endung=endung))


def wache_fuer_status(*, frist_s: float = FRIST_S, name: str = "Lauf",
                      _uhr=None) -> Wache:
    """Eine Wache auf ein blosses Statuswort. Die Art ist zwangsläufig :data:`BEHAUPTET`.

    Diese Wache kann einen Stillstand **nie** beweisen, und genau das sagt ihr Befund.
    Sie ist trotzdem nützlich: Eine Warnung nach fünf Minuten ist mehr als eine Auskunft
    nach dreissig.
    """
    return Wache(frist_s=frist_s, art=BEHAUPTET, name=name, _uhr=_uhr)
