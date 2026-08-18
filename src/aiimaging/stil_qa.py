"""STIL-QA — das zweite Gate: Sieht der Render aus wie das Haus?

Warum dieses Modul existiert
----------------------------
Ein Render kann geometrisch einwandfrei sein und trotzdem unbrauchbar: falsche
Tageszeit, falsche Materialsprache, Hochglanz-Ästhetik statt der zurückhaltenden
Bildsprache des Büros. Das misst der Stil-Score. Er vergleicht das Bild mit einem
Referenzset — dem belegten Hausstil — und gibt eine Zahl zwischen −1 und 1.

Er ist ausdrücklich **nicht** das einzige Gate. Der belegte Anlass steht in
``gate.py``: Ein reines Stil-Gate meldete einmal ``bestanden`` (0.42) auf eine
halluzinierte Kubatur. Stil misst Aussehen, nicht Wahrheit.

Die Trennung, um die es hier geht
---------------------------------
Das Einbetten eines Bildes braucht ein neuronales Netz (DINOv3), Gewichte und im
Zweifel eine GPU. Das Vergleichen zweier Einbettungen braucht eine Wurzel und eine
Summe. Beides in einer Funktion zu haben hiesse: Die Metrik ist nur dort prüfbar, wo
die Gewichte liegen.

Darum sind sie getrennt:

* :func:`kosinus`, :func:`stil_score`, :func:`stil_gate` sind reine Mathematik über
  Zahlenfolgen — stdlib, deterministisch, überall prüfbar.
* :func:`stil_gate_aus_bildern` nimmt einen **injizierbaren** ``einbetter`` entgegen,
  der Bildpfade zu Vektoren macht. Im Test ist das eine Attrappe, im Betrieb der Aufruf
  des Einbettungsmodells. Dieselbe Test-Naht wie ``_starte`` in ``seams.py``.

Das ist kein Behelf für den fehlenden Rechner, sondern der Grund, warum die Schwelle
überhaupt diskutierbar ist: Eine Metrik, die man nur mit GPU nachrechnen kann, kann
niemand nachprüfen.

Das Einbettungsmodell und seine ungeklärte Lizenz
-------------------------------------------------
Vorgesehen ist DINOv3. Es ist **gated** (Zugang muss beantragt werden) und liegt hier
nicht vor. Seine Lizenz ist im Rahmen dieses Projekts **nicht geprüft** — sie ist keine
der vier permissiven aus Regel 1, und ob sie kommerzielle Nutzung erlaubt, gehört vor
dem produktiven Einsatz am Original geklärt. Das ist ein offener Punkt, kein erledigter.
Genau deshalb ist der Einbetter injizierbar: Ein Wechsel des Einbettungsmodells ist ein
anderes Argument, kein Umbau (dieselbe Absicht wie bei ``backbone.py``).

Abhängigkeiten: keine. Reine stdlib, kein ``torch``, kein ``numpy``, kein ``bpy``.
"""
from __future__ import annotations

import math

#: Ab diesem Stil-Score gilt ein Bild als im Hausstil.
#:
#: Herkunft: KosmoVis-Vorläufer. Getroffene Bilder lagen bei rund 0.5–0.6, verfehlte bei
#: rund 0.06–0.13. Die Schwelle sitzt im Graben dazwischen, näher am unteren Feld — ein
#: knapp verfehltes Bild soll eher durchrutschen als ein passendes fälschlich
#: durchfallen, denn das zweite Gate (Geometrie) fängt die teuren Fehler ohnehin ab.
#:
#: Die Zahl ist an **wenigen Fällen** kalibriert, nicht an einer Studie. Sie gilt für die
#: Aggregation ``max`` (siehe :func:`stil_score`); mit ``mittel`` misst dieselbe Zahl
#: etwas anderes. Die systematische Schwellenstudie steht in ``docs/PLAN.md`` als offener
#: Punkt — bis dahin ist 0.30 eine begründete Setzung, kein Messergebnis.
SCHWELLE_STIL = 0.30

#: Aggregation über das Referenzset: Abstand zur NÄCHSTEN Referenz.
AGG_MAX = "max"

#: Aggregation über das Referenzset: mittlerer Abstand zu ALLEN Referenzen.
AGG_MITTEL = "mittel"

#: Alle gültigen Aggregationen. Ein unbekannter Wert ist ein Fehler, kein stiller Default.
AGGREGATIONEN = (AGG_MAX, AGG_MITTEL)


class StilError(ValueError):
    """Eingabe ist keine brauchbare Grundlage für einen Stil-Score.

    Bewusst laut. Ein Score aus einem Nullvektor oder aus zwei verschieden langen
    Vektoren wäre eine Zahl ohne Bedeutung — und eine bedeutungslose Zahl, die ein Gate
    passiert, ist schlimmer als ein Abbruch.
    """


# --------------------------------------------------------------------------------------
# Vektoren lesen — defensiv, weil sie aus einem fremden Modell kommen
# --------------------------------------------------------------------------------------

def _lies_vektor(vektor, bezeichnung: str) -> list[float]:
    """Beliebige Zahlenfolge → Liste endlicher ``float``.

    ``bool`` wird abgewiesen, obwohl es ein ``int`` ist: ``True`` als Vektorkomponente ist
    immer ein Irrtum. Text wird ebenfalls abgewiesen — ``"0.5"`` stillschweigend zu deuten
    wäre dieselbe Art Reparatur, gegen die dieses Projekt durchgehend antritt.

    Raises:
        StilError: leer, keine Folge, oder enthält NaN/inf. NaN darf keinen Vergleich
            erreichen: Jeder Vergleich mit NaN ist falsch, ein Gate liesse dadurch still
            alles durchfallen — oder, je nach Richtung des Vergleichs, alles durch.
    """
    if isinstance(vektor, (str, bytes)) or not hasattr(vektor, "__iter__"):
        raise StilError(f"{bezeichnung} ist keine Zahlenfolge: {type(vektor).__name__}")
    werte: list[float] = []
    for i, wert in enumerate(vektor):
        if isinstance(wert, bool) or not isinstance(wert, (int, float)):
            raise StilError(f"{bezeichnung}[{i}] ist keine Zahl: {wert!r}")
        zahl = float(wert)
        if not math.isfinite(zahl):
            raise StilError(f"{bezeichnung}[{i}] ist nicht endlich: {wert!r}")
        werte.append(zahl)
    if not werte:
        raise StilError(f"{bezeichnung} ist leer — ein Vektor ohne Komponenten.")
    return werte


# --------------------------------------------------------------------------------------
# Die Metrik
# --------------------------------------------------------------------------------------

def kosinus(a, b) -> float:
    """Kosinus-Ähnlichkeit zweier Vektoren, im Bereich −1 … 1.

    Gemessen wird der Winkel, nicht die Länge: ``kosinus(v, 3·v) == 1.0``. Genau das ist
    bei Bild-Embeddings erwünscht — die Länge eines Embeddings trägt kaum Bedeutung, die
    Richtung trägt sie.

    Returns:
        1.0 bei gleicher Richtung, 0.0 bei rechtem Winkel (kein Zusammenhang), −1.0 bei
        entgegengesetzter Richtung. Das Ergebnis wird auf ``[-1, 1]`` geklemmt: Bei
        identischen Vektoren kann die Fliesskommaarithmetik 1.0000000000000002 liefern,
        und ein Score über 1 wäre ein Rätsel ohne Ursache.

    Raises:
        StilError: verschiedene Längen, leere Vektoren, NaN/inf oder ein Nullvektor.
            Ein Nullvektor hat keine Richtung — die Kosinus-Ähnlichkeit ist dort nicht
            definiert, und 0.0 zurückzugeben behauptete „kein Zusammenhang", wo in
            Wahrheit „keine Aussage möglich" gilt. Ein Nullvektor aus einem
            Einbettungsmodell heisst praktisch immer: Das Bild wurde nicht gelesen.
    """
    va = _lies_vektor(a, "a")
    vb = _lies_vektor(b, "b")
    if len(va) != len(vb):
        raise StilError(
            f"Vektoren verschieden lang ({len(va)} und {len(vb)}). Das heisst fast immer: "
            f"zwei verschiedene Einbettungsmodelle. Ihre Räume sind nicht vergleichbar."
        )

    punkt = sum(x * y for x, y in zip(va, vb))
    norm_a = math.sqrt(sum(x * x for x in va))
    norm_b = math.sqrt(sum(y * y for y in vb))
    if norm_a == 0.0 or norm_b == 0.0:
        raise StilError(
            "Nullvektor — keine Richtung, keine Kosinus-Ähnlichkeit. Aus einem "
            "Einbettungsmodell heisst das in aller Regel: Das Bild wurde nicht gelesen."
        )

    return max(-1.0, min(1.0, punkt / (norm_a * norm_b)))


def stil_score(bild_vektor, referenz_vektoren, *, aggregation: str = AGG_MAX) -> dict:
    """Stil-Score eines Bildes gegen ein Referenzset.

    Args:
        bild_vektor: Einbettung des zu prüfenden Bildes.
        referenz_vektoren: Einbettungen des Referenzsets. Mindestens eine.
        aggregation: ``"max"`` (Vorgabe) oder ``"mittel"``.

    Returns:
        ``{score, aggregation, n_referenzen, einzelwerte, beste_referenz,
        schlechteste_referenz, streuung}``.

        ``einzelwerte`` ist die Ähnlichkeit zu jeder einzelnen Referenz, in der Reihenfolge
        der Eingabe. Sie wird mitgeliefert, weil der aggregierte Wert allein nicht sagt,
        *warum* er so ausfällt — und weil die spätere Schwellenstudie genau diese
        Einzelwerte braucht.

        ``streuung`` ist der Abstand zwischen bestem und schlechtestem Einzelwert. Ist er
        gross, ist das Referenzset heterogen, und ``max`` und ``mittel`` sagen dann sehr
        Verschiedenes (siehe unten).

    Raises:
        StilError: leeres Referenzset, unbekannte Aggregation, oder ein unbrauchbarer
            Vektor.

    Warum ``max`` die Vorgabe ist
    -----------------------------
    Die beiden Aggregationen messen zwei verschiedene Fragen:

    * ``max`` — Abstand zur **nächsten** Referenz: „Sieht das Bild aus wie *irgendeines*
      der Belegbilder?" Ein Hausstil ist selten homogen; er enthält Innen- und
      Aussenbilder, Tag und Nacht, Holz und Beton. Trifft ein Render eine dieser
      Ausprägungen genau, ist er im Stil — auch wenn er zu den übrigen Referenzen wenig
      Ähnlichkeit hat.
    * ``mittel`` — mittlerer Abstand zu **allen** Referenzen: „Wie nah ist das Bild am
      Schwerpunkt des Sets?" Das misst Konformität mit dem Durchschnitt. Bei einem
      homogenen Referenzset trennt es schärfer als ``max``, weil ein einzelner Ausreisser
      im Set kein Bild mehr durchwinken kann.

    ``max`` ist die Vorgabe aus zwei Gründen. Erstens ist das reale Referenzset
    heterogen; ``mittel`` zieht dort alle Scores in ein mittleres Band, in dem eine
    Schwelle kaum noch trennt. Zweitens — und das wiegt schwerer — ist
    :data:`SCHWELLE_STIL` mit ``max`` kalibriert. Wer die Aggregation wechselt, ohne die
    Schwelle neu zu bestimmen, misst mit einem Massstab, der für etwas anderes geeicht
    wurde. Darum trägt jede Antwort ihre ``aggregation`` mit sich.

    Die Schwäche von ``max`` gehört mitgenannt: Eine einzelne untypische Referenz im Set
    genügt, um beliebig viele falsche Bilder durchzulassen. Das Referenzset ist damit
    selbst ein Prüfgegenstand — ``mittel`` ist das Werkzeug, mit dem man es prüft.
    """
    if aggregation not in AGGREGATIONEN:
        raise StilError(
            f"Unbekannte Aggregation {aggregation!r}. Erlaubt: {', '.join(AGGREGATIONEN)}."
        )
    if isinstance(referenz_vektoren, (str, bytes)) or not hasattr(referenz_vektoren, "__iter__"):
        raise StilError(f"referenz_vektoren ist keine Folge: {type(referenz_vektoren).__name__}")

    referenzen = list(referenz_vektoren)
    if not referenzen:
        raise StilError(
            "Referenzset ist leer. Ohne Belegbilder gibt es keinen Hausstil, gegen den "
            "gemessen werden könnte — und ein Score von 0.0 wäre eine erfundene Messung."
        )

    einzelwerte = tuple(kosinus(bild_vektor, ref) for ref in referenzen)
    score = max(einzelwerte) if aggregation == AGG_MAX else sum(einzelwerte) / len(einzelwerte)

    return {
        "score": score,
        "aggregation": aggregation,
        "n_referenzen": len(einzelwerte),
        "einzelwerte": einzelwerte,
        "beste_referenz": einzelwerte.index(max(einzelwerte)),
        "schlechteste_referenz": einzelwerte.index(min(einzelwerte)),
        "streuung": max(einzelwerte) - min(einzelwerte),
    }


def stil_gate(bild_vektor, referenz_vektoren, *, schwelle: float = SCHWELLE_STIL,
              **kw) -> dict:
    """Stil-Score plus Urteil gegen die Schwelle.

    Args:
        bild_vektor: Einbettung des Renders.
        referenz_vektoren: Einbettungen des Referenzsets.
        schwelle: Ab hier gilt der Stil als getroffen. Vorgabe :data:`SCHWELLE_STIL`.
        **kw: an :func:`stil_score` durchgereicht (``aggregation``).

    Returns:
        ``{bestanden, score, schwelle, aggregation, n_referenzen, einzelwerte,
        beste_referenz, schlechteste_referenz, streuung, begruendung}``.

    Raises:
        StilError: unbrauchbare Eingabe oder eine Schwelle ausserhalb ``[-1, 1]`` — dort
            wäre das Gate immer offen oder immer zu, also gar kein Gate.

    Der Vergleich ist ``>=``: Ein Score genau auf der Schwelle besteht. Die Schwelle ist
    eine gesetzte Zahl, kein Naturgesetz; sie soll nicht ausgerechnet an ihrem eigenen
    Rand zusätzlich streng sein.

    Die Antwort trägt ``schwelle`` und ``aggregation`` mit sich. Wer später ein Urteil
    nachvollzieht, muss wissen, gegen welchen Massstab gemessen wurde — sonst ist ein
    protokolliertes ``bestanden: False`` nicht mehr deutbar, sobald jemand die Vorgabe
    ändert.

    Dieses Gate allein genügt nicht. Siehe ``gate.py``.
    """
    if isinstance(schwelle, bool) or not isinstance(schwelle, (int, float)):
        raise StilError(f"schwelle ist keine Zahl: {schwelle!r}")
    schwelle = float(schwelle)
    if not math.isfinite(schwelle) or not (-1.0 <= schwelle <= 1.0):
        raise StilError(
            f"schwelle {schwelle!r} liegt ausserhalb des Wertebereichs der "
            f"Kosinus-Ähnlichkeit [-1, 1]. Ein solches Gate wäre immer offen oder immer zu."
        )

    ergebnis = stil_score(bild_vektor, referenz_vektoren, **kw)
    bestanden = ergebnis["score"] >= schwelle

    if bestanden:
        begruendung = (
            f"Stil-Score {ergebnis['score']:.3f} >= Schwelle {schwelle:.2f} "
            f"(Aggregation '{ergebnis['aggregation']}' über {ergebnis['n_referenzen']} "
            f"Referenzen). Der Render liegt im Hausstil. Das sagt nichts darüber, ob er "
            f"der Geometrie folgt — dafür ist das zweite Gate zuständig."
        )
    else:
        begruendung = (
            f"Stil-Score {ergebnis['score']:.3f} < Schwelle {schwelle:.2f} "
            f"(Aggregation '{ergebnis['aggregation']}' über {ergebnis['n_referenzen']} "
            f"Referenzen). Nächste Referenz ist Nr. {ergebnis['beste_referenz']} mit "
            f"{max(ergebnis['einzelwerte']):.3f}. Der Render trifft den Hausstil nicht."
        )

    return {**ergebnis, "bestanden": bestanden, "schwelle": schwelle,
            "begruendung": begruendung}


# --------------------------------------------------------------------------------------
# Die Naht zum Einbettungsmodell
# --------------------------------------------------------------------------------------

def _kein_einbetter(pfad):
    """Vorgabe-Einbetter: er bettet nichts ein, er erklärt, was fehlt.

    Kein stiller Rückfall auf einen Behelfs-Einbetter (Histogramme, Bildgrösse, Zufall).
    Ein solcher Rückfall lieferte Zahlen, die aussehen wie ein Stil-Score, es aber nicht
    sind — und ein Gate, das auf erfundenen Zahlen ``bestanden`` meldet, ist schlimmer
    als gar kein Gate. Dasselbe Prinzip wie ``finde_ifc_python`` in ``seams.py``, das
    lieber abbricht als auf das falsche Python zurückzufallen.
    """
    raise StilError(
        "Kein Einbetter übergeben. Das Einbettungsmodell (DINOv3) ist gated und liegt "
        "hier nicht vor; seine Lizenz ist zudem nicht geprüft (Regel 1). Übergib "
        "'einbetter=<funktion>', die einen Bildpfad auf einen Vektor abbildet — im Test "
        "eine Attrappe, im Betrieb der Aufruf des Modells jenseits der Prozessgrenze. "
        f"Nicht eingebettet: {pfad!r}"
    )


def stil_gate_aus_bildern(bild_pfad, referenz_pfade, *, einbetter=None,
                          schwelle: float = SCHWELLE_STIL, **kw) -> dict:
    """Wie :func:`stil_gate`, aber ab Bildpfaden — über einen injizierbaren Einbetter.

    Args:
        bild_pfad: Pfad des zu prüfenden Renders.
        referenz_pfade: Pfade des Referenzsets. Mindestens einer.
        einbetter: Funktion ``pfad -> Vektor``. **Pflicht.** Ohne sie bricht der Aufruf
            mit einer Erklärung ab, statt sich etwas auszudenken.
        schwelle: siehe :func:`stil_gate`.
        **kw: an :func:`stil_score` durchgereicht.

    Returns:
        Dasselbe Wörterbuch wie :func:`stil_gate`, zusätzlich ``bild_pfad`` und
        ``referenz_pfade`` — damit ein protokolliertes Urteil sagt, worüber es urteilte.

    Raises:
        StilError: kein Einbetter, leeres Referenzset, oder der Einbetter liefert etwas,
            das kein brauchbarer Vektor ist.

    Diese Funktion ist die einzige Stelle des Moduls, die überhaupt von Bildern weiss.
    Alles darunter rechnet auf Zahlen. Deshalb ist der Kern dieses Moduls auf einem
    Rechner ohne GPU und ohne Gewichte vollständig prüfbar — die Naht wird im Test durch
    eine Attrappe ersetzt, genau wie ``_starte`` in ``seams.py``.
    """
    einbetten = einbetter or _kein_einbetter

    if isinstance(referenz_pfade, (str, bytes)):
        # Ein einzelner Pfad als String liesse sich in seine Zeichen zerlegen, und das
        # Modell bekäme "/" als Bildpfad. Der Fehlgriff ist häufig und still — darum hier
        # abgefangen, statt ihn erst im Einbetter auflaufen zu lassen.
        raise StilError(
            f"referenz_pfade ist ein einzelner Pfad, keine Folge: {referenz_pfade!r}. "
            f"Als Liste übergeben: [{referenz_pfade!r}]."
        )
    referenzen = list(referenz_pfade)
    if not referenzen:
        raise StilError("Referenzset ist leer — keine Belegbilder, kein Hausstil.")

    bild_vektor = einbetten(bild_pfad)
    referenz_vektoren = [einbetten(pfad) for pfad in referenzen]

    urteil = stil_gate(bild_vektor, referenz_vektoren, schwelle=schwelle, **kw)
    return {**urteil, "bild_pfad": str(bild_pfad),
            "referenz_pfade": tuple(str(p) for p in referenzen)}
