"""Kalibrierung der Geometrie-Schwelle — der Schritt von der Zahl zur Begründung.

Warum es dieses Modul gibt
--------------------------
``geometrie_qa.SCHWELLE_GEOMETRIE`` steht auf **0,65**. Diese Zahl stammt aus wenigen
Einzelfällen und ist bis heute nirgends hergeleitet. ``docs/PLAN.md`` nennt das beim
Namen: *„Eine ordentliche Kalibrierung ist das, was die Arbeit über einen
Werkstattbericht hinaushebt."* Solange die Schwelle geraten ist, ist auch jedes Urteil
darüber geraten.

Kalibrieren heisst hier nicht, eine bessere Zahl zu finden, sondern die Frage überhaupt
messbar zu machen: **Bei welcher Art und Stärke von Abweichung fällt der Score, und tut
er es so, dass eine Grenze zwischen „noch treu" und „nicht mehr treu" existiert?**

Der Aufbau: kontrollierte Störungen statt echter Bilder
-------------------------------------------------------
Eine Kalibrierung an echten Renders bräuchte GPU, Gewichte und ein menschliches Urteil je
Bild. Beides fehlt hier — und beides wäre für die **erste** Hälfte der Frage auch das
falsche Werkzeug. Denn zuerst muss geklärt sein, wie der Score auf eine Abweichung
*bekannter Art und bekannter Stärke* reagiert. Erst wenn das steht, ist ein Score aus
einem echten Bild überhaupt deutbar.

Darum: Eine Soll-Tiefenkarte wird **gezielt verfälscht**, in Störungsarten, die den
tatsächlichen Fehlerarten eines Bildmodells nachgebildet sind, jeweils über eine
Stärkeskala. Jede Störung hat eine **Erwartung**, welchen Anteil des Scores sie treffen
soll — und ob sie eintrifft, ist damit prüfbar und nicht Auslegungssache.

Was diese Studie NICHT leistet — und das ist wichtiger als was sie leistet
--------------------------------------------------------------------------
1. **Sie kalibriert die Metrik, nicht die Kette.** Zwischen Soll und Ist liegt im Betrieb
   ein monokularer Tiefenschätzer. Sein Fehler ist hier nicht enthalten. Eine an dieser
   Studie gewonnene Schwelle ist eine Schwelle **für die Metrik**, keine für den
   Gesamtlauf.
2. **„Treu" ist hier durch die Störungsstärke definiert, nicht durch ein menschliches
   Urteil.** Dass eine Störung der Stärke 0,3 „noch annehmbar" wäre, ist eine Setzung.
   Was die Studie liefert, ist die *Form* des Zusammenhangs — wo der Score steil fällt,
   wo er flach bleibt, und wo er gar nicht reagiert, obwohl er sollte.
3. **Ein synthetischer Baukörper ist kein Haus.** Die Kurven hängen an der Szene. Darum
   nennt jedes Ergebnis die Szene mit, und die Studie ist über beliebige Soll-Karten
   laufbar.

Der eigentliche Ertrag ist der dritte Punkt in dieser Liste
------------------------------------------------------------
Zwei Störungen sind **Kontrollen** statt Prüfungen — sie messen nicht die Schwelle,
sondern die Metrik selbst:

* :data:`MONOTON` transformiert die Tiefe streng monoton (Massstab, Nullpunkt, Potenz).
  Ein rangbasiertes Verfahren **muss** das unverändert überstehen; tut es das nicht, ist
  nicht die Schwelle falsch, sondern die Metrik kaputt. Das ist die einzige Prüfung hier,
  die widerlegen kann statt nur zu beschreiben.
* :data:`TIEFENUMKEHR` dreht nah und fern. Der Score benutzt ``abs(spearman)`` — mit
  Absicht, siehe ``geometrie_qa`` — und **kann diesen Fall darum nicht sehen**. Die
  Studie führt ihn mit, damit die Grenze der Metrik in den Zahlen steht und nicht nur in
  einem Nebensatz der Dokumentation.
"""
from __future__ import annotations

import hashlib
import math
import random
import struct
import warnings
from collections.abc import Sequence
from dataclasses import dataclass

from aiimaging import bildlesen, geometrie_qa

#: Hintergrundmarke der erzeugten Karten. Derselbe Wert, den Cycles schreibt.
HINTERGRUND_M = 1.0e10

#: Woher die Soll-Karte einer Studie stammt. Steht in jedem Ergebnis, weil eine an einer
#: synthetischen Karte gewonnene Kurve etwas anderes behauptet als eine an echter
#: Geometrie gewonnene — und weil man das dem Zahlenblock sonst nicht ansieht.
HERKUNFT_KARTE = "karte"
HERKUNFT_BERICHT = "blender-bericht"

#: Der Vorbehalt, der zu **jedem** Studienergebnis gehört, auch zu einem an echter
#: Geometrie gemessenen. Er steht als Zeichenkette im Ergebnis und nicht nur in der
#: Dokumentation, damit er mitreist, wenn die Zahlen es tun.
VORBEHALT_NICHT_DIE_KETTE = (
    "Diese Studie kalibriert die Metrik, nicht die Kette: Soll-Karte und gestörte Karte "
    "tragen beide eine Hintergrundmarke. Der Fehler des monokularen Schätzers — er legt "
    "den Himmel mitten in die Tiefenspanne des Bauwerks, siehe "
    "docs/DECKELSTUDIE_2026-08-26.md — kommt hier gar nicht vor. Eine hier gewonnene "
    "Schwelle gilt für die Metrik, nicht für den Weg dorthin."
)

# ── Störungsarten ────────────────────────────────────────────────────────────────────

RAUSCHEN = "rauschen"
SILHOUETTE_WACHSEN = "silhouette_wachsen"
SILHOUETTE_SCHRUMPFEN = "silhouette_schrumpfen"
VERSCHIEBUNG = "verschiebung"
GLAETTUNG = "glaettung"
ZUSATZKOERPER = "zusatzkoerper"
TIEFENUMKEHR = "tiefenumkehr"
MONOTON = "monoton"

#: Was ein Score-Anteil unter einer Störung tun soll.
FAELLT = "faellt"
BLEIBT = "bleibt"


class StudienError(ValueError):
    """Die Studie lässt sich mit diesen Angaben nicht durchführen."""


@dataclass(frozen=True)
class Stoerung:
    """Eine Störungsart samt ihrer **Erwartung**.

    `wirkt_auf_spearman` und `wirkt_auf_iou` sind der Grund, warum diese Registry
    existiert. Ohne sie wäre eine Kurve nur eine Kurve; mit ihnen ist jede Störung eine
    **Vorhersage**, die zutreffen oder scheitern kann. Eine Störung, die die Silhouette
    unangetastet lässt und trotzdem den IoU senkt, ist ein Befund über die Metrik — und
    genau das soll auffallen, statt in einer Tabelle unterzugehen.
    """

    name: str
    beschreibung: str
    entspricht: str
    wirkt_auf_spearman: str
    wirkt_auf_iou: str
    ist_kontrolle: bool = False


STOERUNGEN: dict[str, Stoerung] = {
    RAUSCHEN: Stoerung(
        name=RAUSCHEN,
        beschreibung="Normalverteiltes Rauschen auf die Tiefe der Geometriepunkte.",
        entspricht=("Dem Messrauschen des monokularen Tiefenschätzers. Die Silhouette "
                    "bleibt, die Tiefenordnung franst aus."),
        wirkt_auf_spearman=FAELLT, wirkt_auf_iou=BLEIBT,
    ),
    SILHOUETTE_WACHSEN: Stoerung(
        name=SILHOUETTE_WACHSEN,
        beschreibung="Die Silhouette wird um k Bildpunkte verbreitert.",
        entspricht=("Einem Bildmodell, das anbaut — ein Vordach, eine Brüstung, eine "
                    "Wand, die es nicht gibt."),
        wirkt_auf_spearman=BLEIBT, wirkt_auf_iou=FAELLT,
    ),
    SILHOUETTE_SCHRUMPFEN: Stoerung(
        name=SILHOUETTE_SCHRUMPFEN,
        beschreibung="Die Silhouette wird um k Bildpunkte abgetragen.",
        entspricht="Einem Bildmodell, das weglässt — ein Geschoss fehlt, ein Flügel fehlt.",
        wirkt_auf_spearman=BLEIBT, wirkt_auf_iou=FAELLT,
    ),
    VERSCHIEBUNG: Stoerung(
        name=VERSCHIEBUNG,
        beschreibung="Die ganze Karte wird um k Bildpunkte versetzt.",
        entspricht=("Einer verrutschten Kamera oder einem Modell, das den Bau als Ganzes "
                    "verschiebt. Trifft beide Anteile."),
        wirkt_auf_spearman=FAELLT, wirkt_auf_iou=FAELLT,
    ),
    GLAETTUNG: Stoerung(
        name=GLAETTUNG,
        beschreibung="Mittelwertfilter über die Geometriepunkte.",
        entspricht=("Verlorenem Detail — Kanten werden weich, Gliederung verschwindet, "
                    "die grobe Kubatur bleibt."),
        wirkt_auf_spearman=FAELLT, wirkt_auf_iou=BLEIBT,
    ),
    ZUSATZKOERPER: Stoerung(
        name=ZUSATZKOERPER,
        beschreibung="Ein zusätzlicher Quader wird in den Hintergrund gesetzt.",
        entspricht=("Der klassischen Halluzination: ein Baukörper, den die Geometrie "
                    "nicht kennt, an einer Stelle, wo Himmel sein müsste."),
        wirkt_auf_spearman=BLEIBT, wirkt_auf_iou=FAELLT,
    ),
    TIEFENUMKEHR: Stoerung(
        name=TIEFENUMKEHR,
        beschreibung="Nah und fern werden vertauscht (die Tiefenordnung wird gespiegelt).",
        entspricht=("Einem Schätzer mit falscher Polarität. KONTROLLE: Der Score benutzt "
                    "abs(spearman) und kann diesen Fall nicht sehen — er bleibt hoch. "
                    "Die Störung steht hier, damit diese Grenze in Zahlen steht."),
        wirkt_auf_spearman=BLEIBT, wirkt_auf_iou=BLEIBT, ist_kontrolle=True,
    ),
    MONOTON: Stoerung(
        name=MONOTON,
        beschreibung="Streng monotone Umrechnung der Tiefe (Massstab, Nullpunkt, Potenz).",
        entspricht=("KONTROLLE, und die einzige Prüfung hier, die widerlegen kann: Ein "
                    "rangbasiertes Verfahren MUSS das unverändert überstehen. Fällt der "
                    "Score, ist nicht die Schwelle falsch, sondern die Metrik."),
        wirkt_auf_spearman=BLEIBT, wirkt_auf_iou=BLEIBT, ist_kontrolle=True,
    ),
}

#: Vorgabe-Stärken. 0.0 gehört dazu — die ungestörte Karte ist die Nullprobe, und ein
#: Score, der dort nicht 1.0 ist, entwertet jede Zeile darunter.
VORGABE_STAERKEN = (0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0)


# ── Testszene ────────────────────────────────────────────────────────────────────────

def baue_testszene(breite: int = 64, hoehe: int = 64, *,
                   nah_m: float = 18.0, fern_m: float = 27.0) -> list[float]:
    """Eine synthetische Soll-Tiefenkarte: zwei Baukörper mit Sprung dazwischen.

    Warum nicht eine echte Blender-Karte als Vorgabe: Diese hier ist in einer Zeile
    reproduzierbar, hat keine Abhängigkeit und keinen Rauschanteil. Wer gegen echte
    Geometrie kalibrieren will, gibt seine eigene Karte an — die Studie nimmt jede.

    **Zwei Eigenschaften sind hier nicht Zierde, sondern Voraussetzung** — beide wurden
    beim ersten Studienlauf am 18.08.2026 nachgerüstet, weil ihr Fehlen zwei Störungen
    wirkungslos machte:

    1. **Wenige Bindungen.** Die erste Fassung war ein Gefälle aus der Summe zweier
       Achsenanteile. Das erzeugt lauter gleiche Werte: gemessen **1837 Bindungen auf
       1936 Punkte**. Über so einer Karte ist die Rangkorrelation grösstenteils eine
       Rechnung über Bindungsgruppen — und die Kontrolle „streng monotone Umrechnung
       ändert nichts" scheiterte scheinbar, weil die Fliesskomma-Umrechnung
       Bindungsgruppen anders zerlegte. Nicht die Metrik war schuld, sondern die Szene.
       Darum stehen die Achsen jetzt in einem **inkommensurablen Verhältnis** (√2):
       Zwei verschiedene Punkte treffen damit nur noch selten denselben Wert.

    2. **Ein Tiefensprung.** Die erste Fassung war eine reine Rampe — und eine Rampe
       überlebt jede Mittelung, weil der Mittelwert einer linearen Folge wieder dieselbe
       Folge ist. Die Störung ``glaettung`` blieb dadurch **völlig wirkungslos**
       (Score 1,000 bei jeder Stärke): Sie hatte nichts zu zerstören. Der vorspringende
       Flügel liefert jetzt die Kante, an der Glättung überhaupt etwas anrichtet.

    Der Bau füllt bewusst nur die mittleren Zweidrittel: Ohne Hintergrund gäbe es keine
    Silhouette, und ohne Silhouette misst ``geom_iou`` nichts.
    """
    if breite < 8 or hoehe < 8:
        raise StudienError(f"Testszene braucht mindestens 8×8, war {breite}×{hoehe}.")
    x0, x1 = breite // 6, breite - breite // 6
    y0, y1 = hoehe // 6, hoehe - hoehe // 6
    spanne = fern_m - nah_m
    karte = [HINTERGRUND_M] * (breite * hoehe)

    # Der Flügel: die linke Hälfte des Baus springt vor. Der Sprung ist ein Drittel der
    # Bautiefe — gross genug, dass Glättung ihn verschleift, klein genug, dass er nicht
    # die ganze Ordnung dominiert.
    fluegel_bis = x0 + (x1 - x0) // 2
    fluegel_oben, fluegel_unten = y0 + (y1 - y0) // 4, y1 - (y1 - y0) // 4

    wurzel_zwei = 1.41421356237309504880
    for y in range(y0, y1):
        for x in range(x0, x1):
            ax = (x - x0) / max(1, x1 - x0 - 1)
            ay = (y - y0) / max(1, y1 - y0 - 1)
            # Inkommensurables Verhältnis statt gleicher Gewichte: Sonst ergäben (x+1, y-1)
            # und (x, y) denselben Wert, und die Karte bestünde aus Bindungen.
            anteil = (ax + wurzel_zwei * ay) / (1.0 + wurzel_zwei)
            tiefe = nah_m + anteil * spanne
            if x < fluegel_bis and fluegel_oben <= y < fluegel_unten:
                tiefe -= spanne / 3.0                 # der Sprung
            karte[y * breite + x] = tiefe
    return karte


# ── Störungen ────────────────────────────────────────────────────────────────────────

def _geometrie_indizes(karte: Sequence[float]) -> list[int]:
    return [i for i, w in enumerate(karte)
            if math.isfinite(w) and w < geometrie_qa.HINTERGRUND_SCHWELLE_M]


def _spanne(karte: Sequence[float], idx: Sequence[int]) -> float:
    werte = [karte[i] for i in idx]
    return (max(werte) - min(werte)) or 1.0


def _nachbarn(i: int, breite: int, hoehe: int) -> list[int]:
    x, y = i % breite, i // breite
    aus = []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < breite and 0 <= ny < hoehe:
            aus.append(ny * breite + nx)
    return aus


def stoere(soll: Sequence[float], art: str, staerke: float, *,
           breite: int, hoehe: int, seed: int = 0) -> list[float]:
    """Eine Soll-Karte gezielt verfälschen → die Ist-Karte einer Studienzeile.

    Args:
        staerke: 0.0 heisst **unverändert** (die Nullprobe), 1.0 die stärkste Form der
            jeweiligen Störung. Was „1,0" bedeutet, ist je Art verschieden und im
            Quelltext der Art dokumentiert — eine gemeinsame Einheit gibt es nicht, weil
            ein verschobener Bildpunkt und ein Rauschanteil nichts miteinander zu tun
            haben. Vergleichbar sind darum die **Kurven**, nicht die Stärken.
        seed: Fester Startwert. Eine Studie, die sich nicht wiederholen lässt, ist keine.

    Raises:
        StudienError: unbekannte Art, negative Stärke, oder Masse passen nicht zur Karte.
    """
    if art not in STOERUNGEN:
        raise StudienError(f"Unbekannte Störung {art!r}. Bekannt: {', '.join(sorted(STOERUNGEN))}")
    if not isinstance(staerke, (int, float)) or isinstance(staerke, bool) or staerke < 0:
        raise StudienError(f"staerke: nicht-negative Zahl erwartet, war {staerke!r}.")
    if breite < 1 or hoehe < 1:
        raise StudienError(f"Masse müssen positiv sein, waren {breite}×{hoehe}.")
    if breite * hoehe != len(soll):
        raise StudienError(
            f"{breite}×{hoehe} = {breite * hoehe} passt nicht zu {len(soll)} Werten. "
            f"Die räumlichen Störungen brauchen die echten Masse — eine falsche Breite "
            f"verschöbe jede Zeile und sähe wie eine Störung aus, die keine ist."
        )
    # Ehrliche Grenze, bei der Testabnahme am 18.08.2026 gefunden: Diese Prüfung ist
    # eine **Längen**prüfung, keine Massprüfung. `breite=1024, hoehe=1` kommt auf einer
    # 32×32-Karte durch, weil das Produkt stimmt — aus einer flachen Werteliste lässt
    # sich die wahre Zeilenbreite nicht ablesen. Was danach herauskommt, ist keine
    # Störung, sondern Unsinn; er fällt erst als „nicht messbar" in der Zeile auf.
    # Wer hier eine echte Prüfung will, muss die Masse zur Karte mitführen — das wäre
    # ein anderer Datentyp und nicht die Sache dieses Moduls.
    karte = list(soll)
    idx = _geometrie_indizes(karte)
    if not idx:
        raise StudienError("Soll-Karte enthält keinen einzigen Geometriepunkt.")
    if staerke == 0.0:
        return karte

    wuerfel = random.Random(seed)

    if art == RAUSCHEN:
        # staerke 1.0 = Standardabweichung von einer halben Bautiefe. Darüber hinaus
        # wäre die Ordnung nicht mehr gestört, sondern ersetzt.
        sigma = 0.5 * staerke * _spanne(karte, idx)
        for i in idx:
            karte[i] += wuerfel.gauss(0.0, sigma)
        return karte

    if art == GLAETTUNG:
        # staerke 1.0 = so viele Mittelungsdurchgänge, dass von der Gliederung nichts
        # bleibt. Der Hintergrund geht NICHT ein — sonst zöge er die Ränder ins Unendliche.
        durchgaenge = max(1, round(staerke * 8))
        geo = set(idx)
        for _ in range(durchgaenge):
            neu = list(karte)
            for i in idx:
                nachbarn = [karte[n] for n in _nachbarn(i, breite, hoehe) if n in geo]
                neu[i] = (karte[i] + sum(nachbarn)) / (1 + len(nachbarn))
            karte = neu
        return karte

    if art == TIEFENUMKEHR:
        # Spiegelung an der Mitte der Bautiefe: nah wird fern, fern wird nah, die
        # Silhouette bleibt Punkt für Punkt dieselbe.
        werte = [karte[i] for i in idx]
        lo, hi = min(werte), max(werte)
        for i in idx:
            karte[i] = lo + hi - karte[i]
        return karte

    if art == MONOTON:
        # Massstab, Nullpunkt und eine Potenz — alle drei streng monoton wachsend, also
        # rangerhaltend. staerke steuert nur, wie stark die Umrechnung ausfällt; am
        # Ergebnis darf sie nichts ändern.
        werte = [karte[i] for i in idx]
        lo = min(werte)
        spanne = _spanne(karte, idx)
        potenz = 1.0 + staerke                       # >= 1, streng monoton auf [0, ∞)
        faktor = 1.0 + 9.0 * staerke
        versatz = -50.0 * staerke                    # auch negative Tiefen sind erlaubt
        for i in idx:
            normiert = (karte[i] - lo) / spanne
            karte[i] = versatz + faktor * (normiert ** potenz)
        return karte

    if art in (SILHOUETTE_WACHSEN, SILHOUETTE_SCHRUMPFEN):
        # staerke 1.0 = ein Achtel der kürzeren Bildkante. Mehr wäre kein Anbau mehr,
        # sondern ein anderes Gebäude.
        schritte = max(1, round(staerke * max(1, min(breite, hoehe) // 8)))
        geo = set(idx)
        for _ in range(schritte):
            if art == SILHOUETTE_WACHSEN:
                rand = {n for i in geo for n in _nachbarn(i, breite, hoehe) if n not in geo}
                for n in rand:
                    # Der neue Punkt bekommt die Tiefe seines nächsten Nachbarn im Bau —
                    # ein Anbau steht in derselben Ebene, nicht im Nichts.
                    quellen = [karte[m] for m in _nachbarn(n, breite, hoehe) if m in geo]
                    karte[n] = sum(quellen) / len(quellen)
                geo |= rand
            else:
                rand = {i for i in geo
                        if any(n not in geo for n in _nachbarn(i, breite, hoehe))}
                for i in rand:
                    karte[i] = HINTERGRUND_M
                geo -= rand
                if not geo:
                    break
        return karte

    if art == VERSCHIEBUNG:
        # staerke 1.0 = ein Achtel der kürzeren Bildkante, diagonal.
        d = max(1, round(staerke * max(1, min(breite, hoehe) // 8)))
        neu = [HINTERGRUND_M] * len(karte)
        for i, wert in enumerate(karte):
            x, y = i % breite, i // breite
            nx, ny = x + d, y + d
            if 0 <= nx < breite and 0 <= ny < hoehe:
                neu[ny * breite + nx] = wert
        return neu

    if art == ZUSATZKOERPER:
        # staerke 1.0 = ein Zusatzkörper von der Fläche des Baus selbst.
        #
        # BEFUND 18.08.2026, bei der Testabnahme gemessen: Die erste Fassung legte ein
        # Quadrat der Kantenlänge √(staerke · Baufläche) in die obere linke Ecke — und
        # der Bau selbst schnitt davon so viel weg, dass bei Stärke 1,0 nur **40 %** der
        # angekündigten Fläche stehenblieb (780 statt 1936 Punkte auf 64²). Die Rechnung
        # war harmlos, die Beschriftung der Achse falsch: „Fläche des Baus selbst" war
        # schlicht nicht wahr, und die Auswertung hat es geglaubt.
        #
        # Jetzt wird das Quadrat gewachsen, bis die **tatsächlich gesetzte** Punktzahl
        # das Ziel erreicht. Was die Achse verspricht, steht danach auch im Bild.
        ziel = max(1, round(staerke * len(idx)))
        werte = [karte[i] for i in idx]
        tiefe = min(werte)                            # davor, also gut sichtbar
        frei = [i for i in range(len(karte))
                if not (math.isfinite(karte[i])
                        and karte[i] < geometrie_qa.HINTERGRUND_SCHWELLE_M)]
        if not frei:
            raise StudienError(
                "Der Zusatzkörper fand keinen freien Platz — diese Szene hat keinen "
                "Hintergrund. Die Störung braucht welchen."
            )
        gesetzt = 0
        for kante in range(1, max(breite, hoehe) + 1):
            for y in range(min(kante, hoehe)):
                for x in range(min(kante, breite)):
                    i = y * breite + x
                    if karte[i] == HINTERGRUND_M or not (
                            math.isfinite(karte[i])
                            and karte[i] < geometrie_qa.HINTERGRUND_SCHWELLE_M):
                        if karte[i] != tiefe:
                            karte[i] = tiefe
                            gesetzt += 1
            if gesetzt >= ziel or kante >= max(breite, hoehe):
                break
        if gesetzt == 0:
            raise StudienError(
                "Der Zusatzkörper konnte keinen einzigen Punkt setzen — die obere linke "
                "Ecke dieser Szene ist vollständig bebaut."
            )
        return karte

    raise StudienError(f"Störung {art!r} ist bekannt, aber nicht gebaut.")   # pragma: no cover


# ── Der Studienlauf ──────────────────────────────────────────────────────────────────

def studienlauf(soll: Sequence[float], *, breite: int, hoehe: int,
                arten: Sequence[str] | None = None,
                staerken: Sequence[float] = VORGABE_STAERKEN,
                schwelle: float = geometrie_qa.SCHWELLE_GEOMETRIE,
                seed: int = 0, szene: str = "unbenannt") -> dict:
    """Das Gitter aus Störungsart × Stärke messen.

    Returns:
        ``{szene, breite, hoehe, schwelle, seed, methode, herkunft, geometrieanteil,
        n_geometrie, n_punkte, vorbehalte, zeilen, kontrollen, warnungen}``

        Jede Zeile trägt ``art``, ``staerke``, ``score``, ``spearman``, ``geom_iou``,
        ``bestanden`` und ``erwartung_erfuellt``. Alles Zahlen und Text — das Ergebnis
        darf nach Regel 3 über das Repo reisen und passt unverändert in
        ``auftrag.baue_ergebnis(messwerte=…)``.

    Ein ``score`` von ``None`` ist **kein schlechter Wert, sondern kein Wert** — dieselbe
    Haltung wie in ``geometrie_qa``. Solche Zeilen zählen nirgends mit; sie stehen in
    ``warnungen``.
    """
    arten = list(arten) if arten is not None else list(STOERUNGEN)
    unbekannt = [a for a in arten if a not in STOERUNGEN]
    if unbekannt:
        raise StudienError(f"Unbekannte Störungsarten: {sorted(unbekannt)}")

    geo_idx = _geometrie_indizes(soll)

    zeilen: list[dict] = []
    warnungen: list[str] = []
    for art in arten:
        for staerke in staerken:
            ist = stoere(soll, art, staerke, breite=breite, hoehe=hoehe, seed=seed)
            urteil = geometrie_qa.geometrie_gate(soll, ist, schwelle=schwelle)
            zeile = {
                "art": art,
                "staerke": float(staerke),
                # Fingerabdruck der Ist-Karte. Er ist eine Zahl und reist damit nach
                # Regel 3 mit; wozu er da ist, steht bei `trennschaerfe_kurve`.
                "ist_abdruck": _abdruck(ist),
                "score": urteil["score"],
                "spearman": urteil["spearman"],
                "geom_iou": urteil["geom_iou"],
                "n_gemeinsam": urteil["n_gemeinsam"],
                "bestanden": bool(urteil["bestanden"]),
                "ist_kontrolle": STOERUNGEN[art].ist_kontrolle,
            }
            zeilen.append(zeile)
            if urteil["score"] is None:
                warnungen.append(
                    f"{art} bei Stärke {staerke}: nicht messbar — {urteil.get('begruendung')}")
    for zeile in zeilen:
        zeile["erwartung_erfuellt"] = _erwartung_erfuellt(zeile, zeilen)

    return {
        "szene": szene, "breite": breite, "hoehe": hoehe,
        "schwelle": schwelle, "seed": seed,
        "methode": geometrie_qa.METHODE,
        # Woher die Karte kam und wie viel von ihr Bauwerk ist. Der Anteil steht hier,
        # weil `geom_iou` an ihm hängt: Eine Schwelle, die an 44 % Geometrie kalibriert
        # wurde und bei 8 % angewandt wird, ist nicht dieselbe Schwelle.
        "herkunft": HERKUNFT_KARTE,
        "geometrieanteil": len(geo_idx) / max(1, len(soll)),
        "n_geometrie": len(geo_idx),
        "n_punkte": len(soll),
        "vorbehalte": [VORBEHALT_NICHT_DIE_KETTE],
        "zeilen": zeilen,
        "kontrollen": _kontrollen(zeilen),
        "warnungen": warnungen,
    }


def _abdruck(karte: Sequence[float]) -> str:
    """Ein kurzer, stabiler Fingerabdruck einer Tiefenkarte.

    Nur zum **Vergleichen zweier Zeilen**, nicht als Prüfsumme gegen Verfälschung —
    darum genügt eine kurze Kennung. Sie ist eine Zeichenkette aus Ziffern und reist
    unter Regel 3 mit, weil sich aus ihr keine Karte zurückgewinnen lässt.
    """
    h = hashlib.blake2b(digest_size=8)
    for wert in karte:
        h.update(struct.pack("<d", wert))
    return h.hexdigest()


def _nullprobe(zeilen: list[dict], art: str) -> dict | None:
    for z in zeilen:
        if z["art"] == art and z["staerke"] == 0.0:
            return z
    return None


def _erwartung_erfuellt(zeile: dict, zeilen: list[dict]) -> bool | None:
    """Trifft ein, was die Registry für diese Störung vorhersagt?

    ``None`` heisst „nicht entscheidbar" — bei Stärke 0 gibt es nichts zu erwarten, und
    ein nicht messbarer Score ist kein Gegenbeweis. Auch hier gilt: kein Urteil aus
    Mangel an Messung.
    """
    if zeile["staerke"] == 0.0 or zeile["score"] is None:
        return None
    null = _nullprobe(zeilen, zeile["art"])
    if null is None or null["score"] is None:
        return None
    s = STOERUNGEN[zeile["art"]]
    toleranz = 1e-9
    def passt(erwartet: str, jetzt, vorher) -> bool:
        if jetzt is None or vorher is None:
            return True
        if erwartet == FAELLT:
            return jetzt < vorher - toleranz
        return abs(jetzt - vorher) <= 1e-6
    return (passt(s.wirkt_auf_spearman, abs(zeile["spearman"]) if zeile["spearman"] is not None else None,
                  abs(null["spearman"]) if null["spearman"] is not None else None)
            and passt(s.wirkt_auf_iou, zeile["geom_iou"], null["geom_iou"]))


def _kontrollen(zeilen: list[dict]) -> dict:
    """Die zwei Aussagen, die eine Widerlegung sein können.

    Sie stehen getrennt von den Kurven, weil sie eine andere Frage beantworten: nicht
    „wo liegt die Grenze", sondern „taugt das Verfahren".
    """
    monoton = [z for z in zeilen if z["art"] == MONOTON and z["score"] is not None]
    umkehr = [z for z in zeilen if z["art"] == TIEFENUMKEHR and z["score"] is not None]
    return {
        "rangerhaltung": {
            "frage": ("Überstehen Massstab, Nullpunkt und Potenz den Score unverändert? "
                      "Ein rangbasiertes Verfahren muss das."),
            "kleinster_score": min((z["score"] for z in monoton), default=None),
            "bestanden": all(z["score"] > 1.0 - 1e-6 for z in monoton) if monoton else None,
            "bedeutung_bei_fehlschlag": (
                "Nicht die Schwelle wäre falsch, sondern die Metrik — sie wäre dann nicht "
                "rangbasiert, sondern hinge am Zahlenwert."),
        },
        "polaritaet_unsichtbar": {
            "frage": ("Sieht der Score eine vertauschte Tiefenordnung? Er benutzt "
                      "abs(spearman) und sollte sie NICHT sehen."),
            "kleinster_score": min((z["score"] for z in umkehr), default=None),
            "wie_erwartet_blind": all(z["score"] > 1.0 - 1e-6 for z in umkehr) if umkehr else None,
            "was_das_heisst": (
                "Eine bestätigte Blindheit ist kein Fehler, sondern eine bekannte Grenze: "
                "Die Polarität muss ausserhalb der Metrik festgestellt werden — in der "
                "Kette tut das `tiefenschaetzer`, indem er sie nie aus den Daten rät."),
        },
    }


def trennschaerfe(ergebnis: dict, schwelle: float) -> dict:
    """Wie gut trennt **diese** Schwelle? Ohne Kontrollen, ohne nicht messbare Zeilen.

    Der Massstab ist bewusst schlicht: Eine Zeile gilt als *treu*, solange ihre Störung
    schwach ist, und als *untreu* darüber. Die Grenze dazwischen ist eine **Setzung**
    (`grenzstaerke`) und keine Messung — sie steht im Ergebnis, damit niemand sie für
    ein Naturgesetz hält.

    Returns:
        ``{schwelle, richtig_frei, falsch_frei, richtig_gesperrt, falsch_gesperrt,
        treffer, n}``. ``falsch_frei`` ist der teure Fehler: ein untreues Bild, das
        durchgeht. ``falsch_gesperrt`` kostet nur einen weiteren Render.
    """
    return trennschaerfe_kurve(ergebnis, (schwelle,))["punkte"][0]


def trennschaerfe_kurve(ergebnis: dict, schwellen: Sequence[float] = tuple(
        round(0.05 * k, 2) for k in range(1, 20)), *, grenzstaerke: float = 0.2) -> dict:
    """Dieselbe Rechnung über eine ganze Reihe von Schwellen → die Kurve.

    Das ist der Kern der Studie: Nicht *eine* Schwelle zu verteidigen, sondern zu zeigen,
    wie sich das Verhältnis der beiden Fehlerarten verschiebt, wenn man sie bewegt.

    Args:
        grenzstaerke: Bis zu dieser Störungsstärke gilt eine Zeile als *treu*. **Eine
            Setzung, keine Messung** — wer sie ändert, ändert das Ergebnis, und genau
            darum steht sie im Rückgabewert.

    Returns:
        ``{grenzstaerke, punkte, beste, entdoppelt, n_roh, n_ausgewertet}``.
        ``entdoppelt`` nennt jede Zeile, die als punktgleiche Wiederholung verworfen
        wurde — siehe die Begründung im Rumpf. ``beste`` ist die Schwelle mit der höchsten
        Trefferquote; bei Gleichstand die **kleinste** von ihnen, denn eine niedrigere
        Schwelle sperrt weniger und ist bei gleicher Güte die mildere Wahl.
    """
    roh = [z for z in ergebnis["zeilen"]
           if not z["ist_kontrolle"] and z["score"] is not None and z["staerke"] > 0.0]

    # ENTDOPPLUNG — der Befund, der die erste Auswertung dieser Studie verfälscht hat.
    #
    # Die räumlichen Störungen rechnen in **ganzen Bildpunkten**: `round(staerke · k)`.
    # Auf 64² ergeben Stärke 0,2 und 0,3 beide zwei Bildpunkte — die beiden Ist-Karten
    # sind dann nicht ähnlich, sondern **punktgleich identisch**, mit demselben Score.
    #
    # Das ist für sich harmlos. Verheerend wird es, weil `grenzstaerke` genau dazwischen
    # liegt: Zwei Zeilen mit **derselben Messung** stehen auf verschiedenen Seiten der
    # Grenze, die eine gilt als treu, die andere als untreu. **Keine Schwelle der Welt
    # kann sie trennen** — jede zählt zwangsläufig einen Fehler, und der landete in der
    # ersten Auswertung als `falsch_frei`, also als Aussage über die Metrik.
    #
    # Er war eine Aussage über das Stärkeraster. Solche Zeilen werden hier verworfen
    # statt gezählt, und wie viele es waren, steht im Ergebnis: Eine stillschweigende
    # Bereinigung wäre nur die zweite Art, dieselbe Zahl zu erfinden.
    zeilen: list[dict] = []
    verworfen: list[dict] = []
    gesehen: dict[tuple[str, str], float] = {}
    for z in roh:
        schluessel = (z["art"], z.get("ist_abdruck") or f"ohne-abdruck-{z['staerke']}")
        if schluessel in gesehen:
            verworfen.append({"art": z["art"], "staerke": z["staerke"],
                              "gleich_wie_staerke": gesehen[schluessel],
                              "score": z["score"]})
            continue
        gesehen[schluessel] = z["staerke"]
        zeilen.append(z)

    if not zeilen:
        raise StudienError(
            "Keine auswertbare Zeile: Kontrollen und nicht messbare Fälle zählen nicht "
            "mit, Stärke 0 ist die Nullprobe, und punktgleiche Wiederholungen sind "
            "entdoppelt."
        )
    punkte = []
    for schwelle in schwellen:
        rf = ff = rg = fg = 0
        for z in zeilen:
            treu = z["staerke"] <= grenzstaerke
            frei = z["score"] >= schwelle
            if treu and frei:
                rf += 1
            elif not treu and frei:
                ff += 1
            elif not treu and not frei:
                rg += 1
            else:
                fg += 1
        n = len(zeilen)
        punkte.append({
            "schwelle": float(schwelle),
            "richtig_frei": rf, "falsch_frei": ff,
            "richtig_gesperrt": rg, "falsch_gesperrt": fg,
            "treffer": (rf + rg) / n, "n": n,
        })
    beste = max(punkte, key=lambda p: (p["treffer"], -p["schwelle"]))
    return {"grenzstaerke": grenzstaerke, "punkte": punkte, "beste": beste,
            "entdoppelt": verworfen, "n_roh": len(roh), "n_ausgewertet": len(zeilen)}


# ── Die Studie an einer echten Szene ─────────────────────────────────────────────────

def studie_aus_bericht(bericht: dict, *, szene: str,
                       quelle: str = bildlesen.QUELLE_AUTO,
                       arten: Sequence[str] | None = None,
                       staerken: Sequence[float] = VORGABE_STAERKEN,
                       schwelle: float = geometrie_qa.SCHWELLE_GEOMETRIE,
                       seed: int = 0, grenzstaerke: float = 0.2,
                       timeout: int = 300, _starte=None) -> dict:
    """Einen Blender-Bericht zur Grundlage einer Studie machen — echte Geometrie statt Szene.

    Der Docstring von :func:`baue_testszene` sagt seit dem 18.08.2026, was fehlt: *„Wer
    gegen echte Geometrie kalibrieren will, gibt seine eigene Karte an — die Studie nimmt
    jede."* Diese Funktion ist genau dieser Handgriff und **kein neuer Messcode**: Sie
    liest die Soll-Karte mit ``bildlesen.tiefen_aus_report``, gibt sie an
    :func:`studienlauf` und hängt :func:`trennschaerfe_kurve` daran. Wer den Weg von Hand
    gehen will, kann das weiterhin; hier ist er nur einmal aufgeschrieben statt in jeder
    Auswertung neu.

    **Warum das nicht bloss „nochmal laufen lassen" ist.** Die synthetische Szene füllt
    die mittleren Zweidrittel — Geometrieanteil rund 44 %. Unsere echten Szenen liegen
    zwischen 8 % und 17 %. ``geom_iou`` hängt am Geometrieanteil (gemessen, siehe
    ``docs/DECKELSTUDIE_2026-08-26.md``), und eine bei 44 % kalibrierte Schwelle ist bei
    8 % nicht dieselbe Schwelle. Darum steht der Anteil im Ergebnis, neben jeder Zahl,
    die von ihm abhängt.

    Args:
        bericht: Rückgabe von ``seams.glb_zu_multipass`` bzw. Inhalt eines
            ``blender-report.json``.
        szene: **Pflicht, und mit Absicht ohne Vorgabe.** Der Name liesse sich aus
            ``glb_path`` ableiten — das wäre ein absoluter Pfad und damit nach Regel 3
            nichts, was in ein Ergebnis gehört, das über das Repo reist. Also nennt ihn,
            wer die Studie fährt. Eine Kurve ohne ihre Szene ist keine Aussage.
        quelle, timeout, _starte: werden an ``bildlesen.tiefen_aus_report``
            durchgereicht.
        grenzstaerke: an :func:`trennschaerfe_kurve`. Eine Setzung, keine Messung.

    Returns:
        Was :func:`studienlauf` liefert, dazu ``herkunft`` (``HERKUNFT_BERICHT``) und
        ``kurve``. ``geometrieanteil``, ``n_geometrie`` und ``n_punkte`` stammen aus dem
        Studienlauf und gelten damit für die **wirklich gemessene** Karte. ``kurve`` ist
        ``None``, wenn das Gitter keine auswertbare Zeile enthält — der Grund steht dann
        in ``warnungen``.

    Raises:
        StudienError: leerer Szenenname, oder die Karte enthält keinen Geometriepunkt.
        bildlesen.BildError: der Bericht nennt keine lesbare Tiefenkarte.

    **Der Vorbehalt reist mit.** ``vorbehalte`` trägt :data:`VORBEHALT_NICHT_DIE_KETTE`,
    und beim PNG-Rückfall zusätzlich den gemeldeten Silhouettenverlust: Das PNG kann den
    hintersten Geometriepunkt nicht vom Himmel trennen, und dann misst ``geom_iou`` gegen
    eine Silhouette, die vor der ersten Störung schon beschädigt war.
    """
    if not isinstance(szene, str) or not szene.strip():
        raise StudienError(
            "szene: ein nicht-leerer Name ist Pflicht. Eine Kurve gehört an die Szene, "
            "an der sie gemessen wurde; ohne sie ist sie eine Zahl ohne Bedingung."
        )

    # Die Warnung wird gefangen, um sie in das Ergebnis zu schreiben — und danach
    # weitergereicht, damit sie am Bildschirm nicht verschwindet. Eine Meldung, die eine
    # Auswertung stillschweigend schluckt, ist schlimmer als keine.
    with warnings.catch_warnings(record=True) as gefangen:
        warnings.simplefilter("always")
        soll, breite, hoehe = bildlesen.tiefen_aus_report(
            bericht, quelle=quelle, timeout=timeout, _starte=_starte)
    for w in gefangen:
        warnings.warn(w.message, w.category, stacklevel=2)
    verluste = [str(w.message) for w in gefangen
                if issubclass(w.category, bildlesen.SilhouettenVerlust)]

    if not _geometrie_indizes(soll):
        raise StudienError(
            f"Die Tiefenkarte aus diesem Bericht ({breite}×{hoehe}) enthält keinen "
            f"einzigen Geometriepunkt — der Lauf hat nur Himmel gerendert. Ohne "
            f"Silhouette misst `geom_iou` nichts."
        )

    ergebnis = studienlauf(soll, breite=breite, hoehe=hoehe, arten=arten,
                           staerken=staerken, schwelle=schwelle, seed=seed, szene=szene)
    ergebnis["herkunft"] = HERKUNFT_BERICHT
    if verluste:
        ergebnis["vorbehalte"] = list(ergebnis["vorbehalte"]) + [
            "Die Soll-Karte stammt aus dem normalisierten PNG, nicht aus der EXR: "
            + " ".join(verluste)
        ]
    # Die dritte Antwort, auch hier: Ein Gitter ohne auswertbare Zeile — nur Kontrollen,
    # nur die Nullprobe, oder lauter punktgleiche Wiederholungen — ist kein Fehler des
    # Läufers. Es ist eine Studie ohne Kurve, und das gehört gesagt statt geworfen. Wer
    # die Kurve braucht, findet `None` und den Grund daneben; wer nur die Zeilen wollte,
    # bekommt sie.
    try:
        ergebnis["kurve"] = trennschaerfe_kurve(ergebnis, grenzstaerke=grenzstaerke)
    except StudienError as ohne:
        ergebnis["kurve"] = None
        ergebnis["warnungen"] = list(ergebnis["warnungen"]) + [
            f"Keine Trennschärfekurve: {ohne}"]
    return ergebnis


__all__ = [
    "GLAETTUNG", "HINTERGRUND_M", "MONOTON", "RAUSCHEN", "SILHOUETTE_SCHRUMPFEN",
    "SILHOUETTE_WACHSEN", "STOERUNGEN", "TIEFENUMKEHR", "VERSCHIEBUNG", "VORGABE_STAERKEN",
    "ZUSATZKOERPER", "Stoerung", "StudienError",
    "HERKUNFT_BERICHT", "HERKUNFT_KARTE", "VORBEHALT_NICHT_DIE_KETTE",
    "baue_testszene", "stoere", "studie_aus_bericht", "studienlauf", "trennschaerfe",
    "trennschaerfe_kurve",
]
