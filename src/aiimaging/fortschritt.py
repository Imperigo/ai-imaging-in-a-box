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
import threading
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


# ======================================================================================
# Der Beobachter — die Wache läuft mit, während der Lauf blockiert
# ======================================================================================
#
# Die Wache oben ist passiv: Der Aufrufer reicht Zeichen herein. Das passt, solange er
# selbst pollt. Der Abholer tut das **nicht** — er ruft ``verarbeite(auftrag)`` auf, und
# dieser Aufruf blockiert, bis der Renderlauf fertig ist. Zwischen Aufruf und Rückkehr
# hat der Abholer keinen einzigen Moment, in dem er nachsehen könnte.
#
# Darum beobachtet ein Faden nebenher. Dieselbe Bauform wie der Herzschlag in
# ``runners/blender_depth_stage.py`` und das Abgiessen der Rohre in ``seams.py`` — und
# aus demselben Grund: Wo ein Aufruf die Kontrolle behält, bleibt nur ein zweiter Faden.
#
# Was der Beobachter NICHT tut: abbrechen. Er sammelt und meldet. Wer abbrechen will,
# hängt ``bei_stillstand`` daran und entscheidet dort — an der Stelle, die weiss, was ein
# Abbruch kostet.

#: Wie oft nachgesehen wird. Zwei Sekunden wie ``seams.TAKT_S``: kurz genug, dass ein
#: Stillstand nicht in der Auflösung untergeht, lang genug, dass das Nachsehen selbst
#: nichts kostet. ``verzeichnis_marke`` liest ein Verzeichnis, nicht dessen Bäume.
BEOBACHTUNGS_TAKT_S = 2.0


def _schwerer(a: dict | None, b: dict | None) -> dict | None:
    """Der schlimmere der beiden Befunde. ``None`` verliert immer.

    Rangfolge: ``error`` vor ``warn`` vor ``ok``; bei gleichem Rang der mit dem längeren
    Stillstand. So bleibt am Ende **der schlimmste Moment** des Laufs stehen und nicht
    der letzte — ein Lauf, der zwanzig Minuten stand und sich dann fing, hat gestanden.
    """
    rang = {SCHWERE_FEHLER: 2, SCHWERE_WARN: 1, SCHWERE_OK: 0}
    if a is None:
        return b
    if b is None:
        return a
    schluessel = lambda g: (rang.get(g.get("schwere"), 0), g.get("still_seit_s") or 0.0)
    return b if schluessel(b) > schluessel(a) else a


class Beobachter:
    """Fragt eine :class:`Wache` in Abständen und merkt sich den schlimmsten Befund.

    Die Arbeit steckt in :meth:`tick`, und die ist **fadenfrei**: ein Aufruf, ein Blick,
    ein Befund. :meth:`start` hängt nur eine Schleife davor. Das ist Absicht — ein
    Ablauf, der sich nur mit laufendem Faden prüfen liesse, wäre auf Zeitfenster geprüft
    statt auf Verhalten, und solche Tests flackern.

    Args:
        wache: eine Wache **mit eigener Quelle** (:func:`wache_fuer_datei`,
            :func:`wache_fuer_verzeichnis`). Eine Wache auf ein Statuswort hat keine —
            das Statuswort kennt nur der Aufrufer, und ein Faden könnte es nicht holen.
        takt_s: Sekunden zwischen zwei Blicken.
        bei_stillstand: ``(befund) -> None``, gerufen **einmal je Stillstandsereignis**
            und nicht bei jedem Blick. Bei einem Stillstand von einer halben Stunde wären
            das sonst neunhundert Rufe für eine einzige Nachricht. Fängt sich der Lauf
            wieder, ist das nächste Stillstehen ein neues Ereignis.
    """

    def __init__(self, wache: Wache, *, takt_s: float = BEOBACHTUNGS_TAKT_S,
                 bei_stillstand=None) -> None:
        if not isinstance(wache, Wache):
            raise FortschrittsError(f"wache ist keine Wache, sondern {type(wache).__name__}.")
        if getattr(wache, "_zeichen", None) is None:
            raise FortschrittsError(
                f"Die Wache {wache.name!r} hat keine eigene Zeichenquelle. Ein Faden kann "
                f"nur holen, was sich holen lässt — ein Statuswort kennt allein der "
                f"Aufrufer. Nimm wache_fuer_datei oder wache_fuer_verzeichnis, oder "
                f"reiche die Zeichen selbst mit Wache.melde(...) herein."
            )
        if isinstance(takt_s, bool) or not isinstance(takt_s, (int, float)):
            raise FortschrittsError(f"takt_s ist keine Zahl: {takt_s!r}")
        if not math.isfinite(float(takt_s)) or takt_s <= 0:
            raise FortschrittsError(
                f"takt_s muss positiv und endlich sein, war {takt_s!r}. Ein Takt von 0 "
                f"wäre eine Schleife ohne Pause und beschäftigte einen Kern damit, "
                f"nichts zu tun."
            )
        if bei_stillstand is not None and not callable(bei_stillstand):
            raise FortschrittsError("bei_stillstand muss aufrufbar sein oder None.")
        self.wache = wache
        self.takt_s = float(takt_s)
        self.bei_stillstand = bei_stillstand
        self.blicke = 0
        self.meldungen = 0
        self.quellenfehler = 0
        self.rueckruffehler: list[str] = []
        self._schlimmster: dict | None = None
        self._im_stillstand = False
        self._halt = threading.Event()
        self._faden: threading.Thread | None = None

    # ------------------------------------------------------------------ Beobachten

    def tick(self) -> dict | None:
        """Einmal nachsehen. Gibt den Befund dieses Blicks zurück, oder ``None``.

        Wirft nie. Eine Quelle, die stolpert — eine Datei, die gerade ersetzt wird, ein
        Verzeichnis, das kurz nicht lesbar ist —, darf den Beobachter nicht mitreissen.
        Solche Fehlschläge werden gezählt (:attr:`quellenfehler`), nicht verschwiegen.
        """
        self.blicke += 1
        try:
            befund = self.wache.blick()
        except Exception:                  # noqa: BLE001 — siehe Docstring
            self.quellenfehler += 1
            return None
        self._schlimmster = _schwerer(self._schlimmster, befund)
        steht = befund.get("befund") == "stillstand"
        if steht and not self._im_stillstand:
            self._im_stillstand = True
            self.meldungen += 1
            if self.bei_stillstand is not None:
                try:
                    self.bei_stillstand(befund)
                except Exception as fehler:   # noqa: BLE001
                    self.rueckruffehler.append(f"{type(fehler).__name__}: {fehler}")
        elif not steht:
            self._im_stillstand = False
        return befund

    def befund(self) -> dict | None:
        """Der schlimmste Befund dieses Laufs, oder ``None``, wenn nie einer entstand."""
        return self._schlimmster

    def bericht(self) -> dict:
        """Was der Beobachter gesehen hat — auch wenn er nichts gesehen hat.

        ``gestanden`` ist ``False``, wenn kein Stillstand auftrat, **und** es hat
        mindestens einen Blick gebraucht, um das zu wissen: ``blicke == 0`` heisst
        *nicht gemessen*, nicht *in Ordnung*. Dieselbe Dreiteilung wie überall hier.
        """
        schlimmster = self._schlimmster
        return {
            "gemessen": self.blicke > 0,
            "gestanden": bool(schlimmster and schlimmster.get("befund") == "stillstand"),
            "schwere": (schlimmster or {}).get("schwere", SCHWERE_OK) if self.blicke
                       else SCHWERE_OK,
            "laengster_stillstand_s": float((schlimmster or {}).get("still_seit_s") or 0.0)
                                      if self.blicke else None,
            "blicke": self.blicke,
            "meldungen": self.meldungen,
            "quellenfehler": self.quellenfehler,
            "rueckruffehler": list(self.rueckruffehler),
            "detail": (schlimmster or {}).get("detail", "") if self.blicke else (
                "Nicht beobachtet — kein einziger Blick. Das heisst NICHT, dass der Lauf "
                "durchlief; es heisst, dass niemand hingesehen hat."),
        }

    # ------------------------------------------------------------------ Der Faden

    def start(self) -> "Beobachter":
        """Die Schleife in einem Hintergrundfaden starten."""
        if self._faden is not None:
            raise FortschrittsError("Dieser Beobachter läuft bereits.")
        self._halt.clear()

        def schleife() -> None:
            while not self._halt.is_set():
                self.tick()
                self._halt.wait(self.takt_s)

        # Daemon: Bricht der Hauptfaden ab, soll kein Beobachter den Prozess offenhalten.
        # Er hält keinen Zustand, den jemand vermissen würde.
        self._faden = threading.Thread(target=schleife, name="fortschrittswache",
                                       daemon=True)
        self._faden.start()
        return self

    def stop(self, *, warten_s: float = 5.0) -> dict:
        """Den Faden anhalten und den Bericht abholen.

        Auf das Ende wird **gewartet**, aber nicht ewig: Der Faden hängt am selben
        ``Event`` wie die Pause, das Anhalten greift also sofort. Bleibt er trotzdem, ist
        das ein eigener Befund und kein Grund, den Aufrufer festzuhalten.
        """
        self._halt.set()
        faden, self._faden = self._faden, None
        if faden is not None:
            faden.join(timeout=warten_s)
            if faden.is_alive():
                self.rueckruffehler.append(
                    f"Der Beobachtungsfaden lief nach {warten_s:.0f} s noch. Der Bericht "
                    f"kann unvollständig sein.")
        return self.bericht()

    def __enter__(self) -> "Beobachter":
        return self.start()

    def __exit__(self, *_ausnahme) -> bool:
        self.stop()
        return False


def beobachte(wache: Wache, *, takt_s: float = BEOBACHTUNGS_TAKT_S,
              bei_stillstand=None) -> Beobachter:
    """Kurzform: ``with beobachte(wache_fuer_verzeichnis(ordner)) as b: ...``"""
    return Beobachter(wache, takt_s=takt_s, bei_stillstand=bei_stillstand)
