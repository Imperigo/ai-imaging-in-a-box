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
#: etwas anderes.
#:
#: Stand nach der Stilstudie vom 18.08.2026 (``aiimaging.stilstudie``,
#: ``docs/STILSTUDIE_2026-08-18.md``) — sie hat die Zahl **nicht** bestätigt und **nicht**
#: widerlegt, sondern gezeigt, wovon ihre Bedeutung abhängt:
#:
#: * Der **Boden** — die Ähnlichkeit zweier zusammenhangloser Vektoren — liegt bei
#:   isotroper Streuung und 768 Dimensionen bei 0,000 ± 0,036. Von dort sind es rund
#:   **acht Streuungen** bis 0,30; keine von 2000 Zufallsproben kam so weit.
#: * Dieser Boden ist aber der **kleinstmögliche**. Besetzt ein Einbetter einen **Kegel**
#:   (und reale Einbetter tun das), steigt er: bei Kegelanteil 0,3 auf 0,09, bei 0,6 auf
#:   0,36 — dort liegt der Boden *über* dieser Schwelle, und jedes beliebige Bildpaar
#:   bestünde. Wo **SigLIP 2** liegt, ist ungemessen und hier nicht messbar.
#: * Der überlieferte Fehlbereich 0,06–0,13 aus den **DINOv3**-Läufen deckt sich mit dem
#:   Boden eines Kegels von rund 0,3. Er kann also der Boden jenes Einbetters gewesen sein
#:   statt eine Messung von Stilunähnlichkeit — und dann ist er auf SigLIP 2 **nicht**
#:   übertragbar. Der Einbetter hat gewechselt (``einbetter.py``), die Zahl nicht.
#:
#: **AM GERÄT GEMESSEN, 18.08.2026** (``auf-20260818-11``, HomeStation, 4950 Paare aus
#: 100 zusammenhanglosen Bildern): Der Boden von SigLIP 2 base liegt bei
#: **0,526 ± 0,070**, Spanne 0,310 bis 0,845.
#:
#: Damit ist die Befürchtung von oben nicht nur eingetreten, sondern übertroffen: Die
#: Schwelle 0,30 lag **3,24 Streuungen UNTER dem Boden**. Sie war kein strenges Gate und
#: kein mildes — **sie war gar keines**: Alle 4950 Paare bestanden, 100 Prozent, und
#: selbst das unähnlichste Paar des ganzen Korpus lag mit 0,3097 noch darüber. Auch ohne
#: die 5 % ähnlichsten Paare bleibt das Maximum der übrigen bei 0,647, immer noch mehr
#: als das Doppelte. Es gibt keinen Zuschnitt dieses Korpus, unter dem 0,30 wieder Sinn
#: ergäbe.
#:
#: Und die Herkunft der alten Zahl ist damit auch geklärt: Der überlieferte Fehlbereich
#: 0,06–0,13 aus den **DINOv3**-Läufen liegt nicht einmal in der Nähe des SigLIP-2-Bodens.
#: Er war der Boden *jenes* Einbetters, nicht eine Messung von Stilunähnlichkeit. Beim
#: Wechsel des Einbetters in Sitzung 06 ist die Zahl stillschweigend mitgewandert.
#:
#: **Ein Gate, das nie zugeht, ist gefährlicher als gar keines** — es sieht aus wie Schutz.
#:
#: Die Schwelle ist darum jetzt **abgeleitet statt gesetzt**: ``Boden + k · Streuung``,
#: mit dem Boden aus :data:`BODEN_MESSUNGEN`. Für SigLIP 2 base mit ``k = 2`` ergibt das
#: 0,666 (der p99 des Bodens liegt bei 0,698 — dieselbe Grössenordnung).
#:
#: **Ehrlich zur Hälfte:** Der Boden ist gemessen, ``k`` ist gesetzt. Diese Messung sagt,
#: wo Unähnlichkeit *aufhört* — nicht, wo Ähnlichkeit *anfängt*. Dafür bräuchte es Paare,
#: die stilistisch ähnlich sein **sollen**, und ein menschliches Urteil darüber. Der Boden
#: ist die eine Hälfte der Kalibrierung, nicht die ganze. Der Unterschied zu vorher ist
#: trotzdem grundsätzlich: Die Zahl liegt jetzt auf der richtigen Seite des Bodens, und
#: sie wandert nicht mehr stillschweigend mit, wenn der Einbetter wechselt — dafür sorgt
#: die Prüfung in :func:`stil_gate`.
SCHWELLE_STIL = 0.666

#: Der k-Faktor: wie viele Streuungen über dem Boden die Schwelle liegt.
#:
#: **Gesetzt, nicht gemessen** — siehe :data:`SCHWELLE_STIL`. 2 ist die zurückhaltende
#: Wahl: Sie liegt sicher jenseits des Rauschens (der p99 des gemessenen Bodens liegt bei
#: k ≈ 2,46), ohne so hoch zu greifen, dass nur noch nahezu identische Bilder bestehen.
K_STREUUNGEN = 2.0

#: Gemessene Böden je Einbetter **und Ausleseort**.
#:
#: Der Ausleseort gehört zwingend zum Schlüssel: ``pooler_output`` und gemittelte
#: Kachel-Vektoren aus ``last_hidden_state`` sind zwei verschiedene Räume mit zwei
#: verschiedenen Böden, auch beim selben Modell. Wer die Schwelle übernimmt, ohne den
#: Ausleseort zu übernehmen, wiederholt genau den Fehler, der 0,30 hierher gebracht hat.
BODEN_MESSUNGEN = {
    ("siglip2-base", "pooler_output"): {
        "mittel": 0.526,
        "streuung": 0.070,
        "median": 0.523,
        "kleinster": 0.310,
        "groesster": 0.845,
        "p99": 0.698,
        "n_paare": 4950,
        "n_bilder": 100,
        "dimensionen": 768,
        "quelle": "auf-20260818-11 (HomeStation, 18.08.2026)",
    },
}


def boden_fuer(einbetter: str, ausleseort: str = "pooler_output"):
    """Der gemessene Boden dieses Einbetters — oder ``None``, wenn keiner vorliegt.

    ``None`` heisst **nicht** „Boden bei null". Es heisst: Für diese Kombination aus
    Modell und Ausleseort hat niemand gemessen, wie ähnlich sich zwei zusammenhanglose
    Bilder darin sind — und ohne diese Zahl ist jede Schwelle geraten.
    """
    return BODEN_MESSUNGEN.get((einbetter, ausleseort))


def schwelle_aus_boden(boden: dict, k: float = K_STREUUNGEN) -> float:
    """``Boden + k · Streuung`` — die Schwelle als Verfahren statt als Zahl.

    Warum überhaupt so
    ------------------
    Eine feste Zahl ist an den Einbetter gebunden, der sie hervorgebracht hat, und stirbt
    mit ihm. Genau das ist hier passiert: 0,30 stammte aus DINOv3-Läufen und wanderte beim
    Wechsel auf SigLIP 2 stillschweigend mit — in einen Raum, in dem sie unter dem Boden
    lag und damit jedes Bildpaar durchliess.

    Eine abgeleitete Schwelle wandert nicht mit; sie wird beim Wechsel des Einbetters neu
    gerechnet oder es gibt sie nicht.

    Raises:
        StilError: ``boden`` unbrauchbar oder ``k`` negativ. Ein negatives ``k`` ergäbe
            eine Schwelle **unter** dem Boden — also wieder kein Gate.
    """
    if not isinstance(boden, dict) or "mittel" not in boden or "streuung" not in boden:
        raise StilError(f"boden unbrauchbar, erwartet 'mittel' und 'streuung': {boden!r}")
    if isinstance(k, bool) or not isinstance(k, (int, float)) or not math.isfinite(float(k)):
        raise StilError(f"k ist keine endliche Zahl: {k!r}")
    if float(k) < 0.0:
        raise StilError(
            f"k={k} ist negativ. Die Schwelle läge damit UNTER dem Boden — jedes "
            f"beliebige Bildpaar bestünde, und das Gate wäre wieder keines."
        )
    return float(boden["mittel"]) + float(k) * float(boden["streuung"])

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

    # Vor dem Quadrieren auf die grösste Komponente normieren.
    #
    # BEFUND 18.08.2026 (Stilstudie, Abnahme): Ohne diesen Schritt lief `sum(x*x)` ab
    # Komponenten von etwa 1e155 in `inf`, und `inf/inf` ergab `nan`, das die Klammerung
    # anschliessend auf **1.0** zog. Zwei rechtwinklige Vektoren bekamen so den Score
    # 1.0 — ein **bestandenes Gate aus einem Überlauf**, ohne Fehlermeldung. Aus 0.8
    # wurde ebenfalls 1.0.
    #
    # Betrieblich kommen solche Zahlen aus keinem Einbetter. Aber das ist genau die
    # Gestalt, gegen die `StilError` angetreten ist: ein still falsches Urteil in die
    # freisprechende Richtung. Ein Gate, das bei Unsinn „bestanden" sagt, ist schlimmer
    # als eines, das abstürzt.
    #
    # Die Normierung ist mathematisch folgenlos — der Kosinus ist längeninvariant, das
    # ist seine definierende Eigenschaft — und macht die Rechnung für jede endliche
    # Eingabe überlauffrei.
    groesste = max(max(abs(x) for x in va), max(abs(y) for y in vb))
    if groesste == 0.0:
        raise StilError(
            "Nullvektor — keine Richtung, keine Kosinus-Ähnlichkeit. Aus einem "
            "Einbettungsmodell heisst das in aller Regel: Das Bild wurde nicht gelesen."
        )
    va = [x / groesste for x in va]
    vb = [y / groesste for y in vb]

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
              einbetter_name: str = "siglip2-base",
              ausleseort: str = "pooler_output",
              **kw) -> dict:
    """Stil-Score plus Urteil gegen die Schwelle.

    Args:
        bild_vektor: Einbettung des Renders.
        referenz_vektoren: Einbettungen des Referenzsets.
        schwelle: Ab hier gilt der Stil als getroffen. Vorgabe :data:`SCHWELLE_STIL`.
        einbetter_name: Welcher Einbetter die Vektoren erzeugt hat — der **Name** aus
            ``einbetter.EINBETTER``, nicht die Funktion (die heisst in
            :func:`stil_gate_aus_bildern` ``einbetter``). Wird gegen
            :data:`BODEN_MESSUNGEN` geprüft — siehe unten. ``None`` schaltet die Prüfung
            ab und ist als Notausgang gedacht, nicht als Normalfall.
        ausleseort: Wo im Modell die Vektoren abgegriffen wurden. Gehört zwingend dazu:
            Derselbe Einbetter hat an zwei Ausleseorten zwei verschiedene Böden.
        **kw: an :func:`stil_score` durchgereicht (``aggregation``).

    Returns:
        ``{bestanden, score, schwelle, aggregation, n_referenzen, einzelwerte,
        beste_referenz, schlechteste_referenz, streuung, begruendung}``.

    Raises:
        StilError: unbrauchbare Eingabe, eine Schwelle ausserhalb ``[-1, 1]`` — dort wäre
            das Gate immer offen oder immer zu, also gar kein Gate —, **oder eine
            Schwelle unterhalb des gemessenen Bodens des benannten Einbetters**.

    Die Bodenprüfung ist die Lehre aus ``auf-20260818-11``
    ------------------------------------------------------
    Bis zum 18.08.2026 stand hier 0,30. Gemessen liegt der Boden von SigLIP 2 base bei
    0,526 — die Schwelle lag also **unter** der Ähnlichkeit zweier zusammenhangloser
    Bilder, und **alle 4950 geprüften Paare bestanden**. Ein Gate, das nie zugeht, ist
    gefährlicher als gar keines: Es sieht aus wie Schutz, und niemand sucht dahinter.

    Der Fehler war nicht die Zahl, sondern dass sie einen Modellwechsel überlebt hat. Die
    Prüfung hier macht genau das unmöglich: Wer den Einbetter wechselt und die Schwelle
    stehen lässt, bekommt eine Ausnahme statt eines stillschweigend offenen Gates. Und
    wer einen Einbetter benutzt, für den **kein** Boden gemessen ist, bekommt das als
    Mangel in die Antwort — nicht als Fehler, denn ein ungemessener Boden ist keine
    falsche Schwelle, sondern eine unbekannte.

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

    boden = boden_fuer(einbetter_name, ausleseort) if einbetter_name else None
    boden_maengel: list[str] = []
    if einbetter_name and boden is None:
        boden_maengel.append(
            f"Für den Einbetter '{einbetter_name}' am Ausleseort '{ausleseort}' ist kein "
            f"Boden "
            f"gemessen. Die Schwelle {schwelle:.3f} ist damit nicht überprüfbar — sie "
            f"könnte wie 0.30 bei SigLIP 2 unter dem Boden liegen und jedes beliebige "
            f"Bildpaar durchlassen. Boden messen, bevor dieses Urteil zählt."
        )
    elif boden is not None and schwelle <= boden["mittel"]:
        raise StilError(
            f"Schwelle {schwelle:.3f} liegt auf oder unter dem gemessenen Boden von "
            f"'{einbetter_name}' ({boden['mittel']:.3f} ± {boden['streuung']:.3f}, "
            f"{boden['quelle']}). Der Boden ist die Ähnlichkeit ZUSAMMENHANGLOSER Bilder "
            f"— eine Schwelle darunter lässt jedes Bildpaar durch und ist kein Gate, "
            f"sondern nur die Behauptung eines Gates. Genau das war 0.30 hier: 4950 von "
            f"4950 Paaren bestanden. Schwelle aus dem Boden ableiten "
            f"(schwelle_aus_boden), nicht aus einem anderen Modell übernehmen."
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
            "einbetter_name": einbetter_name, "ausleseort": ausleseort, "boden": boden,
            "boden_maengel": tuple(boden_maengel),
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
