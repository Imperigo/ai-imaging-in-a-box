"""Kalibrierung der Stil-Schwelle — und die Frage, was hier überhaupt messbar ist.

Warum es dieses Modul gibt
--------------------------
**Stand beim Schreiben dieses Moduls: ``stil_qa.SCHWELLE_STIL = 0,30``. Heute steht sie
auf 0,666** — seit dem 18.08.2026 **abgeleitet statt gesetzt** (Boden plus zwei
Streuungen, gemessen an 4950 Paaren). Der Abschnitt unten beschreibt den **alten** Zustand
und den Weg, der aus ihm herausführte; er bleibt lesenswert, weil er zeigt, woran eine
gesetzte Schwelle scheitert.

Die alte Zahl stammte aus wenigen Fällen des Vorläufers KosmoVis, gemessen mit
**DINOv3**. Der Einbetter dieses Projekts ist seit dem 18.08.2026 **SigLIP 2**
(``einbetter.py``, Regel 1: DINOv3 ist gated und sonderlizenziert). Damit war die
Schwelle nicht nur ungeprüft, sondern an einem anderen Messgerät geeicht als dem,
das sie anwenden sollte.

Der Unterschied zur Geometriestudie — und warum er den Aufbau bestimmt
----------------------------------------------------------------------
``schwellenstudie.py`` konnte eine Soll-Tiefenkarte **gezielt verfälschen**: Rauschen,
Verschiebung, Anbau sind echte Fehlerarten eines Bildmodells, und eine Tiefenkarte ist
physikalisch deutbar — man kann sagen, was „ein Bildpunkt daneben" heisst.

**Ein Einbettungsvektor ist das nicht.** Er hat keine deutbaren Achsen. Einen
SigLIP-Vektor „um 0,3 zu verrauschen" bildet keine reale Abweichung ab: Es gibt kein
Bild, das dieser Störung entspräche. Die Rechnung liefe sauber durch und ergäbe Zahlen
über nichts — genau der Fehler, vor dem die Geometriestudie in ihrem Kapitel 2 warnt
(dort war die *Szene* schief, hier wäre es der *Gegenstand*).

Darum stört diese Studie **nichts**. Sie misst ausschliesslich Eigenschaften, die die
Metrik selbst hat, unabhängig von jedem Modell:

1. **Die Nullverteilung.** Wo liegt die Kosinus-Ähnlichkeit zweier *zusammenhangloser*
   Vektoren? Das ist der Boden, über dem eine Schwelle überhaupt etwas bedeutet. Sie
   hängt allein an der Dimension — und die steht in ``einbetter.EINBETTER``.
2. **Die Längeninvarianz.** ``kosinus(v, 3·v) == 1`` ist die Zusage des ganzen Verfahrens.
   Sie ist die einzige Prüfung hier, die **widerlegen** kann — dieselbe Rolle wie
   ``MONOTON`` in der Geometriestudie.
3. **Die Aggregation.** ``max`` gegen ``mittel`` an einem Referenzsatz mit einem
   Ausreisser. Reine Arithmetik, kein Modell nötig, und die Vorgabe ``max`` steht danach
   anders da als vorher.

Was diese Studie NICHT leisten kann — und das ist wichtiger als was sie leistet
-------------------------------------------------------------------------------
**Sie sagt nicht, ob 0,30 richtige von falschen Bildern trennt.** Das braucht echte
Bilder, echte Einbettungen und ein menschliches Urteil je Bild. Nichts davon liegt hier
vor, und nichts davon lässt sich synthetisch ersetzen: Ein synthetischer Vektor ist kein
Bild, und die Ähnlichkeit zweier synthetischer Vektoren ist keine Stilähnlichkeit.

**Sie misst den Boden isotroper Zufallsvektoren, nicht den Boden von SigLIP 2.** Echte
Einbetter streuen nicht gleichmässig über die Kugel; sie besetzen einen Kegel. Wie eng
der Kegel von SigLIP 2 ist, weiss dieses Modul nicht — es kann nur zeigen, **wie stark
die Bedeutung der Schwelle davon abhängt** (:func:`kegelreihe`). Diese Reihe ist eine
Empfindlichkeitsrechnung unter einer angenommenen Kegelform, **keine Messung an SigLIP 2**.

Der eine Satz, der beides verbindet: Für unabhängige Ziehungen aus *irgendeiner*
Verteilung auf der Einheitskugel ist die mittlere paarweise Ähnlichkeit ``|E[u]|²`` und
damit **niemals negativ**. Der isotrope Boden bei 0,00 ist also der kleinstmögliche
Boden. Jeder echte Einbetter liegt darüber — nur um wieviel, ist hier nicht messbar.

Die Instrumente prüfen sich selbst
----------------------------------
Die Geometriestudie musste zwei Zahlen berichtigen, weil ihre *Messinstrumente* schief
waren (Kapitel 4a dort). Dagegen steht hier eine Vorkehrung: Jeder Zufallsgenerator
dieses Moduls trägt eine **Vorhersage über sich selbst**, die zutreffen oder scheitern
kann.

* Isotrope Vektoren: Streuung der Ähnlichkeit ist ``1/√d``. Trifft das nicht zu, ist der
  Generator kaputt und jede Zeile darunter wertlos.
* Kegelvektoren mit Anteil ``a``: mittlere Ähnlichkeit ist ``a²``.

Beides steht als ``kontrolle`` in jedem Ergebnis, nicht in einer Fussnote.

Abhängigkeiten: reine stdlib. Kein ``numpy``, kein ``torch``, kein ``bpy``. Zufall trägt
einen festen Startwert — eine Studie, die sich nicht wiederholen lässt, ist keine.
"""
from __future__ import annotations

import math
import random
import statistics
from collections.abc import Sequence

from aiimaging import einbetter
from aiimaging.stil_qa import (
    AGG_MAX,
    AGG_MITTEL,
    AGGREGATIONEN,
    SCHWELLE_STIL,
    kosinus,
    stil_score,
)


class StilstudieError(ValueError):
    """Die Studie lässt sich mit diesen Angaben nicht durchführen."""


#: Die Dimensionen, die in der Studie vorkommen — **aus der Registry abgeleitet**, nicht
#: abgeschrieben. Kommt ein Einbetter dazu, wandert seine Dimension von selbst mit.
#:
#: DINOv3 ist unter Regel 1 ausgeschlossen und trotzdem enthalten: Seine 1024 Dimensionen
#: sind der Boden, auf dem die überlieferte Schwelle 0,30 entstanden ist. Wer sie deuten
#: will, braucht ihn.
REGISTRY_DIMENSIONEN: tuple[int, ...] = tuple(
    sorted({e.dimension for e in einbetter.EINBETTER.values()})
)

#: Dimension der Vorgabe (SigLIP 2). Alles, was nicht ausdrücklich über Dimensionen
#: geht, wird hier gemessen.
VORGABE_DIMENSION: int = einbetter.hole(einbetter.VORGABE_EINBETTER).dimension

#: Wie viele Ziehungen je Messpunkt. 500 ist ein Kompromiss: Die Streuung einer
#: Streuungsschätzung fällt mit ``1/√(2n)``, bei 500 also auf rund 3 %. Das genügt, um
#: ``1/√d`` zu bestätigen, und läuft in reinem Python noch in Sekunden.
VORGABE_PROBEN = 500

#: Fester Startwert. Ohne ihn ist keine Zeile dieser Studie wiederholbar.
VORGABE_SEED = 20260818

#: Längenfaktoren der Invarianzkontrolle. Sie decken sechs Zehnerpotenzen nach oben und
#: unten ab — mehr als jeder Einbetter je liefert, und genau darum die richtige Probe:
#: Eine Zusage, die nur im gewohnten Bereich gilt, ist eine Beobachtung, keine Zusage.
LAENGENFAKTOREN = (1e-6, 1e-3, 0.5, 1.0, 2.0, 1e3, 1e6)

#: Kegelanteile der Empfindlichkeitsreihe. 0,0 ist der isotrope Fall (der kleinstmögliche
#: Boden), 0,8 ein sehr enger Kegel.
KEGELANTEILE = (0.0, 0.2, 0.3, 0.4, 0.6, 0.8)

#: Referenzsatzgrössen der ``max``-Reihe. Mit jeder weiteren Referenz bekommt ``max``
#: eine weitere Gelegenheit, zufällig hoch auszufallen.
REFERENZZAHLEN = (1, 2, 4, 8, 16, 32, 64)


# ── Zufallsvektoren ──────────────────────────────────────────────────────────────────

def _zufallsvektor(wuerfel: random.Random, dimension: int) -> list[float]:
    """Ein isotroper Zufallsvektor: jede Komponente normalverteilt.

    Normalverteilte Komponenten ergeben eine **exakt gleichmässige Richtung** auf der
    Kugel; das ist der Grund für die Wahl.

    **Eine Annahme dazu war beim Schreiben dieses Moduls falsch, und sie wurde gemessen
    statt geglaubt.** Der erste Entwurf behauptete hier, gleichverteilte Komponenten
    (``uniform(-1, 1)``) würden den Boden sichtbar zu hoch treiben, weil sie einen Würfel
    füllen und dessen Ecken die Diagonalen bevorzugen. Die Nachmessung widerlegt das: Bei
    768 Dimensionen liefert der Würfel eine Streuung von 0,0367 gegen 0,0358 aus der
    Normalverteilung — der Unterschied verschwindet in der Stichprobenstreuung
    (``test_wuerfel_statt_kugel_waere_hier_kein_messbarer_fehler``). Die Wahl bleibt
    richtig, ihre Begründung ist eine andere: Exaktheit, nicht ein abgewendeter Fehler.
    """
    return [wuerfel.gauss(0.0, 1.0) for _ in range(dimension)]


def _normiert(vektor: Sequence[float]) -> list[float]:
    laenge = math.sqrt(sum(x * x for x in vektor))
    if laenge == 0.0:  # pragma: no cover — bei d ≥ 1 und Gauss praktisch unerreichbar
        raise StilstudieError("Zufallsvektor der Länge 0 — der Generator ist kaputt.")
    return [x / laenge for x in vektor]


def _kegelvektor(wuerfel: random.Random, dimension: int, richtung: Sequence[float],
                 anteil: float) -> list[float]:
    """Ein Vektor aus einem Kegel um ``richtung``.

    ``anteil`` 0 heisst isotrop, 1 heisst „exakt die Richtung". Dazwischen wird eine feste
    Richtung mit einem isotropen Anteil gemischt, so dass die Länge 1 bleibt.

    Das bildet **nicht** SigLIP 2 nach. Es bildet nach, dass ein Einbetter einen
    bevorzugten Bereich der Kugel besetzt — die Form dieses Bereichs ist hier eine
    Annahme, und ihr einziger Zweck ist zu zeigen, wie stark die Schwelle davon abhängt.
    """
    rausch = _normiert(_zufallsvektor(wuerfel, dimension))
    rest = math.sqrt(max(0.0, 1.0 - anteil * anteil))
    return _normiert([anteil * r + rest * g for r, g in zip(richtung, rausch)])


def _kennzahlen(werte: Sequence[float]) -> dict:
    """Lage und Streuung einer Stichprobe — alles Zahlen, alle Regel-3-tauglich."""
    geordnet = sorted(werte)
    n = len(geordnet)
    if n < 2:
        raise StilstudieError(f"Kennzahlen brauchen mindestens zwei Werte, waren {n}.")

    def quantil(p: float) -> float:
        return geordnet[min(n - 1, max(0, round(p * (n - 1))))]

    return {
        "n": n,
        "mittel": statistics.fmean(geordnet),
        "streuung": statistics.stdev(geordnet),
        "kleinster": geordnet[0],
        "groesster": geordnet[-1],
        "median": statistics.median(geordnet),
        "q05": quantil(0.05),
        "q95": quantil(0.95),
        "q99": quantil(0.99),
    }


# ── Die Nullverteilung ───────────────────────────────────────────────────────────────

def zufallstreffer_schranke(dimension: int, schwelle: float = SCHWELLE_STIL) -> float:
    """Obere **Schranke** für ``P(kosinus ≥ schwelle)`` bei isotroper Richtung.

    ``exp(-d · t² / 2)``, die übliche Konzentrationsschranke für die gleichverteilte
    Richtung auf der Kugel.

    Das ist ausdrücklich **eine Schranke, keine Wahrscheinlichkeit**. Sie ist lose — an
    kleinen Dimensionen, wo der Anteil noch messbar ist, liegt der gemessene Wert um das
    Zwei- bis Zehnfache darunter (siehe ``tests/test_stilstudie.py``). Ihr Zweck ist
    nicht Genauigkeit, sondern eine Aussage, die auch dort gilt, wo keine Stichprobe mehr
    hinreicht: Bei 768 Dimensionen und 0,30 liegt sie in der Grössenordnung 10⁻¹⁵, und
    keine Stichprobe dieser Studie könnte das je bestätigen oder widerlegen.
    """
    if dimension < 1:
        raise StilstudieError(f"Dimension muss positiv sein, war {dimension}.")
    if not (-1.0 <= schwelle <= 1.0):
        raise StilstudieError(f"Schwelle {schwelle!r} liegt ausserhalb [-1, 1].")
    if schwelle <= 0.0:
        return 1.0
    return math.exp(-dimension * schwelle * schwelle / 2.0)


def nullverteilung(dimension: int, *, n_referenzen: int = 1, kegelanteil: float = 0.0,
                   n_proben: int = VORGABE_PROBEN, seed: int = VORGABE_SEED,
                   schwelle: float = SCHWELLE_STIL,
                   aggregation: str = AGG_MAX) -> dict:
    """Wo landet der Stil-Score, wenn zwischen Bild und Referenzen **kein Zusammenhang** ist?

    Das ist die Kernfrage dieser Studie. Eine Schwelle sagt nur dann etwas, wenn bekannt
    ist, was *unter* ihr von selbst passiert. Liegt der Boden bei 0,00 ± 0,04, ist 0,30
    weit draussen; liegt er bei 0,25 ± 0,15, ist 0,30 fast Alltag.

    Args:
        dimension: Länge der Vektoren. Sie allein bestimmt den isotropen Boden.
        n_referenzen: Grösse des Referenzsatzes. Mit ``max`` hebt jede weitere Referenz
            den Boden — sie ist eine weitere Gelegenheit, zufällig hoch auszufallen.
        kegelanteil: 0,0 = isotrop (der kleinstmögliche Boden). Grösser = engerer Kegel,
            **eine Annahme über den Einbetter, keine Messung an ihm**.
        schwelle: Gegen sie wird ``anteil_ueber_schwelle`` gezählt.

    Returns:
        ``{dimension, n_referenzen, kegelanteil, aggregation, n_proben, seed, schwelle,
        kennzahlen, anteil_ueber_schwelle, abstand_in_streuungen, schranke, kontrolle}``.

        ``abstand_in_streuungen`` ist die Zahl, um die es geht: Wie viele Streuungen liegen
        zwischen dem Boden und der Schwelle? Sie ist die einzige Grösse dieser Studie, die
        die Schwelle direkt einordnet — und sie tut es **relativ zum Boden**, nicht absolut.

        ``kontrolle`` prüft den Generator gegen seine eigene Vorhersage (``1/√d`` bzw.
        ``a²``). Schlägt sie fehl, ist nicht die Schwelle falsch, sondern die Messung.

    Raises:
        StilstudieError: unbrauchbare Masse, Anteile ausserhalb ``[0, 1]``, unbekannte
            Aggregation, oder zu wenige Proben für eine Streuung.
    """
    if dimension < 2:
        raise StilstudieError(
            f"Dimension {dimension} ist zu klein. Unter 2 gibt es keine Richtung, die "
            f"sich von einer anderen unterscheiden könnte."
        )
    if n_referenzen < 1:
        raise StilstudieError(f"n_referenzen muss mindestens 1 sein, war {n_referenzen}.")
    if not 0.0 <= kegelanteil <= 1.0:
        raise StilstudieError(f"kegelanteil {kegelanteil!r} liegt ausserhalb [0, 1].")
    if kegelanteil == 1.0:
        raise StilstudieError(
            "kegelanteil 1.0 heisst: alle Vektoren zeigen exakt gleich. Dann ist jeder "
            "Score 1.0 und es gibt keine Verteilung mehr, nur noch eine Konstante."
        )
    if aggregation not in AGGREGATIONEN:
        raise StilstudieError(f"Unbekannte Aggregation {aggregation!r}.")
    if n_proben < 2:
        raise StilstudieError(f"n_proben muss mindestens 2 sein, war {n_proben}.")

    wuerfel = random.Random(seed)
    kegelrichtung = (_normiert(_zufallsvektor(wuerfel, dimension))
                     if kegelanteil > 0.0 else None)

    def ziehe() -> list[float]:
        if kegelrichtung is None:
            return _zufallsvektor(wuerfel, dimension)
        return _kegelvektor(wuerfel, dimension, kegelrichtung, kegelanteil)

    scores: list[float] = []
    for _ in range(n_proben):
        bild = ziehe()
        referenzen = [ziehe() for _ in range(n_referenzen)]
        scores.append(stil_score(bild, referenzen, aggregation=aggregation)["score"])

    kennzahlen = _kennzahlen(scores)
    ueber = sum(1 for s in scores if s >= schwelle) / len(scores)
    abstand = ((schwelle - kennzahlen["mittel"]) / kennzahlen["streuung"]
               if kennzahlen["streuung"] > 0.0 else None)

    return {
        "dimension": dimension,
        "n_referenzen": n_referenzen,
        "kegelanteil": kegelanteil,
        "aggregation": aggregation,
        "n_proben": n_proben,
        "seed": seed,
        "schwelle": schwelle,
        "kennzahlen": kennzahlen,
        "anteil_ueber_schwelle": ueber,
        "abstand_in_streuungen": abstand,
        "schranke": (zufallstreffer_schranke(dimension, schwelle)
                     if n_referenzen == 1 and kegelanteil == 0.0 else None),
        "kontrolle": _generatorkontrolle(dimension, n_referenzen, kegelanteil, kennzahlen),
    }


def _generatorkontrolle(dimension: int, n_referenzen: int, kegelanteil: float,
                        kennzahlen: dict) -> dict:
    """Die Vorhersage des Generators über sich selbst — prüfbar, nicht behauptet.

    Zwei Aussagen sind geschlossen bekannt und werden hier gegen die Stichprobe gehalten:

    * **isotrop, eine Referenz:** Streuung ``1/√d``. Weicht die Messung stark ab, zieht der
      Generator keine gleichmässigen Richtungen — und jede Zeile darunter ist wertlos.
    * **Kegel mit Anteil ``a``:** mittlere Ähnlichkeit ``a²``. Denn für unabhängige
      Ziehungen ``u, v`` gilt ``E[⟨u, v⟩] = |E[u]|²``, und der Mittelvektor des Kegels ist
      ``a`` mal seine Achse.

    Bei mehreren Referenzen mit ``max`` gibt es keine solche geschlossene Vorhersage. Dann
    ist ``pruefbar`` ``False`` — kein Urteil aus Mangel an Vorhersage, dieselbe Haltung
    wie ``erwartung_erfuellt`` in der Geometriestudie.
    """
    if n_referenzen != 1:
        return {"pruefbar": False,
                "grund": ("Für max über mehrere Referenzen gibt es keine geschlossene "
                          "Vorhersage — die Zeile beschreibt, sie prüft nicht.")}
    if kegelanteil == 0.0:
        erwartet = 1.0 / math.sqrt(dimension)
        gemessen = kennzahlen["streuung"]
        # 15 % Toleranz: Die Streuung einer Streuungsschätzung liegt bei ~1/√(2n), also
        # rund 3 % bei 500 Proben. 15 % ist reichlich Luft und schlägt trotzdem an, wenn
        # der Generator die Richtung nicht gleichmässig zieht (Würfel statt Kugel liefe
        # deutlich daneben).
        return {"pruefbar": True, "groesse": "streuung",
                "erwartet": erwartet, "gemessen": gemessen,
                "erfuellt": abs(gemessen - erwartet) <= 0.15 * erwartet,
                "bedeutung_bei_fehlschlag": (
                    "Die Streuung des Bodens folgt nicht 1/√d. Dann rechnet der Generator "
                    "nicht über die Dimension, die er angibt — der gemessene Boden wäre "
                    "ein Artefakt und keine Eigenschaft der Metrik.")}
    erwartet = kegelanteil * kegelanteil
    gemessen = kennzahlen["mittel"]
    return {"pruefbar": True, "groesse": "mittel",
            "erwartet": erwartet, "gemessen": gemessen,
            "erfuellt": abs(gemessen - erwartet) <= 0.02 + 0.05 * erwartet,
            "bedeutung_bei_fehlschlag": (
                "Der Kegelgenerator baut nicht den Kegel, den sein Parameter behauptet. "
                "Die Empfindlichkeitsreihe wäre dann falsch beschriftet — derselbe Fehler "
                "wie der zu kleine Zusatzkörper der Geometriestudie.")}


def nullverteilung_je_dimension(dimensionen: Sequence[int] = REGISTRY_DIMENSIONEN,
                                **kw) -> dict:
    """Die Nullverteilung über die Dimensionen der Einbetter-Registry.

    Returns:
        ``{dimensionen, zeilen, alle_kontrollen_erfuellt}``. Jede Zeile ist ein volles
        Ergebnis von :func:`nullverteilung`.
    """
    zeilen = [nullverteilung(d, **kw) for d in dimensionen]
    return {
        "dimensionen": tuple(dimensionen),
        "zeilen": zeilen,
        "alle_kontrollen_erfuellt": all(z["kontrolle"].get("erfuellt", True) for z in zeilen),
    }


def kegelreihe(dimension: int = VORGABE_DIMENSION,
               kegelanteile: Sequence[float] = KEGELANTEILE, **kw) -> dict:
    """Wie verschiebt sich der Boden, wenn der Einbetter einen Kegel besetzt?

    **Das ist die wichtigste Reihe dieser Studie und zugleich die, die am wenigsten
    behauptet.** Sie misst nicht SigLIP 2. Sie misst, wie stark die Aussage „Score 0,30"
    von einer Eigenschaft abhängt, die niemand hier gemessen hat.

    Returns:
        ``{dimension, zeilen, kippanteil}``. ``kippanteil`` ist der kleinste geprüfte
        Kegelanteil, bei dem der Boden selbst die Schwelle erreicht — ab dort besteht
        **jedes** Bildpaar, auch ein völlig zusammenhangloses.
    """
    zeilen = [nullverteilung(dimension, kegelanteil=a, **kw) for a in kegelanteile]
    schwelle = zeilen[0]["schwelle"]
    kippend = [z["kegelanteil"] for z in zeilen if z["kennzahlen"]["mittel"] >= schwelle]
    return {"dimension": dimension, "zeilen": zeilen,
            "kippanteil": min(kippend) if kippend else None}


def maxreihe(dimension: int = VORGABE_DIMENSION,
             referenzzahlen: Sequence[int] = REFERENZZAHLEN, **kw) -> dict:
    """Wie stark hebt ein wachsender Referenzsatz den Boden unter ``max``?

    ``max`` nimmt die **beste** Übereinstimmung. Jede zusätzliche Referenz ist damit ein
    weiterer Versuch — und der Boden steigt, ohne dass sich am Bild etwas geändert hätte.
    Wer sein Referenzset verdoppelt, verschiebt die Bedeutung der Schwelle, ohne die
    Schwelle anzufassen.
    """
    zeilen = [nullverteilung(dimension, n_referenzen=n, **kw) for n in referenzzahlen]
    return {"dimension": dimension, "referenzzahlen": tuple(referenzzahlen),
            "zeilen": zeilen}


# ── Die Kontrolle, die widerlegen kann ───────────────────────────────────────────────

def laengeninvarianz(*, dimension: int = VORGABE_DIMENSION,
                     faktoren: Sequence[float] = LAENGENFAKTOREN,
                     n_paare: int = 40, seed: int = VORGABE_SEED) -> dict:
    """**Kontrolle.** Ändert eine Längenänderung den Score? Sie darf es nicht.

    Der Kosinus misst den Winkel, nicht die Länge. Das ist keine Nebeneigenschaft, sondern
    die Zusage, auf der das ganze Stil-Gate ruht: Ein Einbettungsmodell darf seine
    Vektoren beliebig skalieren, ohne dass sich ein Urteil ändert. Diese Kontrolle ist die
    einzige Messung dieser Studie, die die Metrik **widerlegen** könnte — dieselbe Rolle
    wie ``MONOTON`` in der Geometriestudie.

    Geprüft wird über zufällige Vektorpaare, beide mit **verschiedenen** Faktoren
    gestreckt: Zwei gleich gestreckte Vektoren wären der leichtere Fall.

    Returns:
        ``{dimension, faktoren, n_paare, groesste_abweichung, bestanden,
        bedeutung_bei_fehlschlag}``.
    """
    if not faktoren:
        raise StilstudieError("Ohne Faktoren prüft die Invarianzkontrolle nichts.")
    if any(f <= 0.0 for f in faktoren):
        raise StilstudieError(
            "Ein Faktor ≤ 0 ist keine Längenänderung: 0 löscht die Richtung, ein negativer "
            "Faktor dreht sie um. Beides wäre eine andere Prüfung."
        )
    wuerfel = random.Random(seed)
    groesste = 0.0
    schlimmster: tuple[float, float] | None = None
    for _ in range(n_paare):
        a = _zufallsvektor(wuerfel, dimension)
        b = _zufallsvektor(wuerfel, dimension)
        soll = kosinus(a, b)
        for fa in faktoren:
            for fb in faktoren:
                ist = kosinus([x * fa for x in a], [y * fb for y in b])
                abweichung = abs(ist - soll)
                if abweichung > groesste:
                    groesste, schlimmster = abweichung, (fa, fb)
    return {
        "dimension": dimension,
        "faktoren": tuple(faktoren),
        "n_paare": n_paare,
        "n_vergleiche": n_paare * len(faktoren) ** 2,
        "groesste_abweichung": groesste,
        "schlimmstes_faktorpaar": schlimmster,
        # 1e-12 statt 0.0: Die Skalierung selbst rechnet in Fliesskomma, und der Kosinus
        # summiert d Produkte. Exakte Gleichheit zu fordern hiesse, die Arithmetik zu
        # prüfen statt die Invarianz.
        "bestanden": groesste <= 1e-12,
        "bedeutung_bei_fehlschlag": (
            "Nicht die Schwelle wäre falsch, sondern die Metrik. Sie hinge dann an der "
            "Länge der Einbettung — und die trägt keine Bedeutung."
        ),
    }


def invarianzgrenze(*, dimension: int = 64, seed: int = VORGABE_SEED,
                    von: int = -200, bis: int = 200) -> dict:
    """Bis zu welcher Grösse hält die Längeninvarianz — und **wie** bricht sie?

    Die Invarianz ist mathematisch unbedingt, die Rechnung ist es nicht: ``kosinus``
    bildet ``sum(x*x)``. Jenseits von etwa ``1e153`` läuft diese Summe über, darunter
    unter — und beides geschieht **ohne Fehlermeldung**.

    Der Befund gehört in diese Studie, obwohl er im Betrieb nicht vorkommt (SigLIP-2-
    Komponenten liegen in der Grössenordnung 1). Denn die Art des Versagens ist genau die,
    gegen die ``StilError`` angetreten ist: nicht ein Abbruch, sondern **eine
    bedeutungslose Zahl, die ein Gate passiert**.

    Returns:
        ``{sicher_von, sicher_bis, stille_faelschungen, art_der_faelschung}``.
        ``stille_faelschungen`` zählt die Exponenten, bei denen ein *falscher* Wert ohne
        Fehler zurückkam.
    """
    wuerfel = random.Random(seed)
    a = _zufallsvektor(wuerfel, dimension)
    b = _zufallsvektor(wuerfel, dimension)
    soll = kosinus(a, b)

    sicher: list[int] = []
    still: list[dict] = []
    laut: list[int] = []
    for exponent in range(von, bis + 1):
        faktor = 10.0 ** exponent
        gestreckt_a = [x * faktor for x in a]
        gestreckt_b = [y * faktor for y in b]
        if not all(math.isfinite(x) for x in gestreckt_a + gestreckt_b):
            continue  # schon die Streckung selbst ist keine Zahl mehr — nicht die Metrik
        try:
            ist = kosinus(gestreckt_a, gestreckt_b)
        except ValueError:
            # ``StilError`` erbt von ``ValueError``. Der laute Abbruch ist hier kein
            # Fehlschlag der Messung, sondern ihr Ergebnis: Er ist der *bessere* der
            # beiden Ausgänge und wird als solcher gezählt.
            laut.append(exponent)
            continue
        if abs(ist - soll) <= 1e-9:
            sicher.append(exponent)
        else:
            still.append({"exponent": exponent, "geliefert": ist, "richtig": soll})

    return {
        "dimension": dimension,
        "richtiger_wert": soll,
        "sicher_von": min(sicher) if sicher else None,
        "sicher_bis": max(sicher) if sicher else None,
        "n_sicher": len(sicher),
        "stille_faelschungen": still,
        "laute_abbrueche": laut,
        "art_der_faelschung": (
            "Überlauf in sum(x*x) liefert einen Score ohne Bedeutung — teils 1.0, also "
            "'bestanden'. Unterlauf liefert einen Nullvektor und damit einen StilError, "
            "dessen Text 'Das Bild wurde nicht gelesen' behauptet, obwohl der Vektor in "
            "Ordnung war. Der laute Fall ist der bessere; der stille ist der gefährliche."
        ),
    }


# ── Wertebereich und Winkel ──────────────────────────────────────────────────────────

def winkel_grad(kosinuswert: float) -> float:
    """Kosinus → Winkel in Grad. Die Übersetzung, die zur falschen Anschauung verführt."""
    if not -1.0 <= kosinuswert <= 1.0:
        raise StilstudieError(f"Kosinus {kosinuswert!r} liegt ausserhalb [-1, 1].")
    return math.degrees(math.acos(kosinuswert))


def grenzfaelle(dimension: int = VORGABE_DIMENSION, *, seed: int = VORGABE_SEED) -> dict:
    """Die vier Ecken des Wertebereichs, an gebauten Vektoren nachgerechnet.

    Gleich, fast gleich, rechtwinklig, entgegengesetzt — und dazu der **Winkel**, den die
    Schwelle bedeutet.

    Der Winkel ist hier die eigentliche Aussage, und er ist eine Warnung: 0,30 entspricht
    rund **72,5 Grad**. In zwei Dimensionen ist das ein weiter Kegel — ein Fünftel aller
    Richtungen liegt darin. In 768 Dimensionen liegt darin fast nichts. Wer die Schwelle
    am Winkel beurteilt, beurteilt sie mit einer Anschauung aus der Ebene.
    """
    wuerfel = random.Random(seed)
    v = _normiert(_zufallsvektor(wuerfel, dimension))
    stoerung = _normiert(_zufallsvektor(wuerfel, dimension))
    fast = _normiert([x + 0.01 * s for x, s in zip(v, stoerung)])
    gegen = [-x for x in v]
    # Ein exakt rechtwinkliger Partner, aus v herausprojiziert — nicht gewürfelt: Ein
    # zufälliger Vektor ist nur *ungefähr* rechtwinklig, und „ungefähr 0" belegt nicht,
    # dass die Metrik bei genau 0 landet.
    anteil = sum(x * s for x, s in zip(v, stoerung))
    recht = _normiert([s - anteil * x for x, s in zip(v, stoerung)])

    return {
        "dimension": dimension,
        "gleich": kosinus(v, v),
        "fast_gleich": kosinus(v, fast),
        "rechtwinklig": kosinus(v, recht),
        "entgegengesetzt": kosinus(v, gegen),
        "doppelte_laenge": kosinus(v, [2.0 * x for x in v]),
        "schwelle": SCHWELLE_STIL,
        "schwelle_als_winkel_grad": winkel_grad(SCHWELLE_STIL),
        "warnung": (
            "Der Winkel verführt zur falschen Anschauung. 72,5 Grad klingt nach viel "
            "Spielraum; in 768 Dimensionen liegt in diesem Kegel fast keine Richtung."
        ),
    }


# ── Referenzsatz und Aggregation ─────────────────────────────────────────────────────

def kohaerenz(vektoren: Sequence[Sequence[float]]) -> dict:
    """Wie einig ist ein Referenzsatz mit sich selbst?

    Der Mittelwert aller paarweisen Ähnlichkeiten. Er ist **ohne jedes Modell** aus einem
    vorhandenen Referenzsatz berechenbar und beantwortet die Frage, die ``stil_qa``
    aufwirft, ohne sie zu beantworten: *Ist dieses Referenzset homogen genug, dass ``max``
    und ``mittel`` dasselbe messen?*

    Returns:
        ``{n, mittlere_aehnlichkeit, kleinste, groesste, spreizung, homogen}``.
        ``homogen`` ist wahr, wenn die kleinste paarweise Ähnlichkeit noch über der
        Schwelle liegt — dann liegen alle Referenzen im Sinne des Gates beieinander.
    """
    satz = [list(v) for v in vektoren]
    if len(satz) < 2:
        raise StilstudieError(
            f"Kohärenz braucht mindestens zwei Referenzen, waren {len(satz)}. Bei einer "
            f"einzigen Referenz sind max und mittel ohnehin dasselbe."
        )
    paare = [kosinus(satz[i], satz[j])
             for i in range(len(satz)) for j in range(i + 1, len(satz))]
    return {
        "n": len(satz),
        "n_paare": len(paare),
        "mittlere_aehnlichkeit": statistics.fmean(paare),
        "kleinste": min(paare),
        "groesste": max(paare),
        "spreizung": max(paare) - min(paare),
        "homogen": min(paare) >= SCHWELLE_STIL,
    }


def mittel_bei_teiltreffer(n_referenzen: int, n_treffer: int,
                           kosinus_treffer: float = 1.0) -> float:
    """Exakt, ohne Zufall: der ``mittel``-Score eines Bildes, das nur einen Teil trifft.

    Trifft ein Bild ``n_treffer`` Referenzen mit ``kosinus_treffer`` und steht zu allen
    übrigen rechtwinklig, ist der Mittelwert ``n_treffer · kosinus_treffer / n_referenzen``.

    Diese eine Zeile Arithmetik ist das schärfste Ergebnis der Aggregationsfrage, und sie
    braucht keinen einzigen Zufallsvektor: **Ein Bild, das eine Referenz perfekt trifft
    (Kosinus 1,0), fällt mit ``mittel`` ab vier Referenzen unter 0,30.** Nicht weil es
    schlecht wäre, sondern weil der Referenzsatz gewachsen ist.
    """
    if n_referenzen < 1 or n_treffer < 0 or n_treffer > n_referenzen:
        raise StilstudieError(
            f"Unmögliche Angaben: {n_treffer} Treffer bei {n_referenzen} Referenzen."
        )
    return n_treffer * kosinus_treffer / n_referenzen


def baue_referenzsatz(*, dimension: int = VORGABE_DIMENSION, n_auspraegungen: int = 4,
                      je_auspraegung: int = 2, naehe: float = 0.85,
                      seed: int = VORGABE_SEED) -> dict:
    """Ein synthetischer Referenzsatz mit der Struktur, die ``stil_qa`` beschreibt.

    Der Docstring von :func:`aiimaging.stil_qa.stil_score` sagt über das reale
    Referenzset: *„Ein Hausstil ist selten homogen; er enthält Innen- und Aussenbilder,
    Tag und Nacht, Holz und Beton."* Genau das wird hier gebaut: mehrere **Ausprägungen**
    (Richtungen), je mehrere Referenzen um jede Ausprägung herum.

    Was hier **nicht** behauptet wird: dass echte Belegbilder so liegen. Die Ausprägungen
    stehen zufällig und damit in hoher Dimension nahezu rechtwinklig zueinander — ob der
    Abstand zwischen „Innenraum" und „Nachtaufnahme" im SigLIP-Raum wirklich so gross ist,
    ist ungemessen. Der Satz zeigt die **Wirkung von Struktur**, nicht die reale Struktur.

    Returns:
        ``{satz, ausprägungen, ausreisser, bilder, kohaerenz, …}`` — ``bilder`` enthält
        drei Prüfbilder: eines im Stil, eines nur am Ausreisser, eines ohne Zusammenhang.
    """
    if n_auspraegungen < 1 or je_auspraegung < 1:
        raise StilstudieError("Ein Referenzsatz braucht mindestens eine Referenz.")
    if not 0.0 <= naehe < 1.0:
        raise StilstudieError(f"naehe {naehe!r} muss in [0, 1) liegen.")

    wuerfel = random.Random(seed)
    auspraegungen = [_normiert(_zufallsvektor(wuerfel, dimension))
                     for _ in range(n_auspraegungen)]
    satz = [_kegelvektor(wuerfel, dimension, richtung, naehe)
            for richtung in auspraegungen for _ in range(je_auspraegung)]
    ausreisser = _normiert(_zufallsvektor(wuerfel, dimension))

    bilder = {
        "im_stil": _kegelvektor(wuerfel, dimension, auspraegungen[0], naehe),
        "am_ausreisser": _kegelvektor(wuerfel, dimension, ausreisser, naehe),
        "ohne_zusammenhang": _normiert(_zufallsvektor(wuerfel, dimension)),
    }
    return {
        "dimension": dimension,
        "n_auspraegungen": n_auspraegungen,
        "je_auspraegung": je_auspraegung,
        "naehe": naehe,
        "seed": seed,
        "satz": satz,
        "auspraegungen": auspraegungen,
        "ausreisser": ausreisser,
        "bilder": bilder,
        "kohaerenz": kohaerenz(satz),
    }


def aggregationsvergleich(*, schwelle: float = SCHWELLE_STIL, **kw) -> dict:
    """``max`` gegen ``mittel`` — mit und ohne einen einzelnen Ausreisser im Referenzsatz.

    Die Vorgabe ist ``max``, und ``stil_qa`` nennt ihre Schwäche selbst: *„Eine einzelne
    untypische Referenz im Set genügt, um beliebig viele falsche Bilder durchzulassen."*
    Hier steht dazu eine Zahl statt eines Nebensatzes.

    Gemessen wird an drei Prüfbildern über zwei Referenzsätze, die sich um **genau eine**
    Referenz unterscheiden.

    Returns:
        ``{schwelle, kohaerenz_ohne, kohaerenz_mit, zeilen, befunde}``. Jede Zeile trägt
        ``bild``, ``satz``, ``max``, ``mittel`` und die beiden Urteile.
    """
    aufbau = baue_referenzsatz(**kw)
    ohne = aufbau["satz"]
    mit = [*aufbau["satz"], aufbau["ausreisser"]]

    zeilen = []
    for satzname, satz in (("ohne_ausreisser", ohne), ("mit_ausreisser", mit)):
        for bildname, bild in aufbau["bilder"].items():
            s_max = stil_score(bild, satz, aggregation=AGG_MAX)["score"]
            s_mittel = stil_score(bild, satz, aggregation=AGG_MITTEL)["score"]
            zeilen.append({
                "bild": bildname, "satz": satzname, "n_referenzen": len(satz),
                "max": s_max, "mittel": s_mittel,
                "bestanden_max": s_max >= schwelle,
                "bestanden_mittel": s_mittel >= schwelle,
            })

    def hole(bild: str, satz: str) -> dict:
        return next(z for z in zeilen if z["bild"] == bild and z["satz"] == satz)

    ausreisser_vorher = hole("am_ausreisser", "ohne_ausreisser")
    ausreisser_nachher = hole("am_ausreisser", "mit_ausreisser")
    im_stil = hole("im_stil", "mit_ausreisser")

    return {
        "schwelle": schwelle,
        "dimension": aufbau["dimension"],
        "seed": aufbau["seed"],
        "kohaerenz_ohne": aufbau["kohaerenz"],
        "kohaerenz_mit": kohaerenz(mit),
        "zeilen": zeilen,
        "befunde": {
            "eine_referenz_oeffnet_das_gate": {
                "frage": ("Genügt eine einzelne untypische Referenz, um ein Bild "
                          "durchzulassen, das sonst durchgefallen wäre?"),
                "vorher": ausreisser_vorher["max"],
                "nachher": ausreisser_nachher["max"],
                "kippt": (not ausreisser_vorher["bestanden_max"]
                          and ausreisser_nachher["bestanden_max"]),
            },
            "mittel_bestraft_das_stiltreue_bild": {
                "frage": ("Fällt ein Bild, das eine Ausprägung des Hausstils genau "
                          "trifft, mit 'mittel' durch dieselbe Schwelle?"),
                "max": im_stil["max"],
                "mittel": im_stil["mittel"],
                "faellt_durch": (im_stil["bestanden_max"]
                                 and not im_stil["bestanden_mittel"]),
                "was_das_heisst": (
                    "0,30 mit 'mittel' ist nicht dieselbe Schwelle, nur strenger — sie "
                    "misst etwas anderes und ist auf einem heterogenen Satz für ein "
                    "stiltreues Bild kaum erreichbar. Die Vorgabe 'max' ist damit nicht "
                    "bloss Konvention, sondern Voraussetzung der Zahl."),
            },
        },
    }


# ── Der Studienlauf ──────────────────────────────────────────────────────────────────

def studienlauf(*, dimension: int = VORGABE_DIMENSION,
                dimensionen: Sequence[int] = REGISTRY_DIMENSIONEN,
                n_proben: int = VORGABE_PROBEN, seed: int = VORGABE_SEED,
                schwelle: float = SCHWELLE_STIL) -> dict:
    """Alle Messungen dieser Studie in einem Durchgang.

    Returns:
        ``{schwelle, dimension, seed, boden, kegel, max_reihe, invarianz, grenzfaelle,
        aggregation, kontrollen_bestanden, was_nicht_gemessen_wurde}``.

    Das letzte Feld ist kein Schmuck. Es reist mit dem Ergebnis mit, damit eine Tabelle
    aus dieser Studie nicht ohne die Sätze zitiert werden kann, die ihre Reichweite
    begrenzen — die Geometriestudie musste dieselbe Lehre nachträglich ziehen.
    """
    boden = nullverteilung_je_dimension(dimensionen, n_proben=n_proben, seed=seed,
                                        schwelle=schwelle)
    kegel = kegelreihe(dimension, n_proben=n_proben, seed=seed, schwelle=schwelle)
    max_reihe = maxreihe(dimension, n_proben=max(50, n_proben // 4), seed=seed,
                         schwelle=schwelle)
    invarianz = laengeninvarianz(dimension=dimension, seed=seed)

    kontrollen = [invarianz["bestanden"], boden["alle_kontrollen_erfuellt"]]
    kontrollen += [z["kontrolle"].get("erfuellt", True) for z in kegel["zeilen"]]

    return {
        "schwelle": schwelle,
        "dimension": dimension,
        "seed": seed,
        "einbetter_vorgabe": einbetter.VORGABE_EINBETTER,
        "boden": boden,
        "kegel": kegel,
        "max_reihe": max_reihe,
        "invarianz": invarianz,
        "grenzfaelle": grenzfaelle(dimension, seed=seed),
        "aggregation": aggregationsvergleich(dimension=dimension, seed=seed,
                                             schwelle=schwelle),
        "kontrollen_bestanden": all(kontrollen),
        "was_nicht_gemessen_wurde": (
            "Ob 0,30 stiltreue von stilfremden Bildern trennt. Das braucht echte Bilder, "
            "echte Einbettungen und ein menschliches Urteil je Bild — keines davon liegt "
            "hier vor, und keines lässt sich durch Zufallsvektoren ersetzen. Gemessen "
            "sind Eigenschaften der Metrik, nicht ihre Tauglichkeit."
        ),
    }


__all__ = [
    "KEGELANTEILE", "LAENGENFAKTOREN", "REFERENZZAHLEN", "REGISTRY_DIMENSIONEN",
    "VORGABE_DIMENSION", "VORGABE_PROBEN", "VORGABE_SEED", "StilstudieError",
    "aggregationsvergleich", "baue_referenzsatz", "grenzfaelle", "invarianzgrenze",
    "kegelreihe", "kohaerenz", "laengeninvarianz", "maxreihe",
    "mittel_bei_teiltreffer", "nullverteilung", "nullverteilung_je_dimension",
    "studienlauf", "winkel_grad", "zufallstreffer_schranke",
]
