#!/usr/bin/env python3
"""BEWEIS 04 — Das Node «qa» (kette.ART_QA) misst mit ``geometrie_qa.geometrie_score``
die Geometrietreue einer Ist-Karte gegen die Soll-Karte: Es lässt eine treue und eine
massstäblich verzerrte Karte durch und erkennt eine halluzinierte Kubatur — an drei
synthetischen Fällen, deren Wahrheit VOR der Messung feststeht.

Was bewiesen wird
-----------------
``kette.ART_QA`` ist die letzte Stufe der Standardkette (geometrie → multipass → render
→ qa). Ihr Kern ist ``geometrie_qa.geometrie_gate`` → ``geometrie_score``:

    score = sqrt(max(0, polaritaet · spearman) · geom_iou)

Zwei Anteile, beide im Bild nachprüfbar: die **Tiefenordnung** (Rangkorrelation über
die gemeinsame Silhouette) und die **Silhouetten-Überdeckung** (Intersection over
Union). Das Modul verspricht drei Dinge, und jedes bekommt hier einen Fall mit bekannter
Wahrheit:

    Fall A  treu         Ist = Soll, unverändert. Die Nullprobe — muss 1.000 geben.
    Fall B  massstab     Ist = Soll durch eine streng monotone Umrechnung geschickt
                         (``schwellenstudie.MONOTON``, Stärke 1.0: Potenz 2, Faktor
                         10, Nullpunkt −50 m — die Ist-Werte liegen bei −50…−40 statt
                         16…27). Absolut stimmt kein einziger Wert mehr; die Reihenfolge
                         stimmt überall. Ein rangbasiertes Verfahren MUSS das mit 1.000
                         durchlassen — das ist die Massstabsblindheit, die
                         ``geometrie_qa`` im Modulkopf als Absicht deklariert, und die
                         einzige Kontrolle hier, die die Metrik widerlegen könnte.
    Fall C  halluziniert Ist = ein ERFUNDENES Gebäude (eine zweite, halb so grosse
                         Testszene aus ``schwellenstudie.baue_testszene``) rechts oben
                         ins Bild gesetzt, wo das Soll nur wenig Geometrie hat. Es hat
                         eine in sich stimmige Tiefenstaffelung — genau der Fall, gegen
                         den ``geom_iou`` gebaut ist: Auf dem wenigen, was sich
                         überlappt, ist die Rangkorrelation hoch; die Silhouetten
                         decken sich kaum. Muss unter die Schwelle fallen.

Woran man es im Bild sieht
--------------------------
Je Fall ein Bild ``NN_<fall>_nebeneinander_…png`` mit vier Kacheln gleicher Grösse,
dieselbe Karte (64×64, viermal vergrössert), plus dieselben Kacheln einzeln:

    1  Soll — Tiefe, nah = hell, Hintergrund schwarz (``bildschreiben.KONVENTION``).
    2  Ist  — dieselbe Darstellung, über die eigene Silhouette normalisiert. Fall B
       sieht darum dem Soll ähnlich, obwohl seine Meterwerte negativ sind: Die
       Normalisierung ist selbst eine monotone Umrechnung, und was sie nicht ändert,
       ändert auch die Rangkorrelation nicht. Fall C zeigt ein anderes, kleineres
       Gebäude an anderer Stelle.
    3  Differenz — Ist minus Soll, beide auf 0..1 normalisiert, nur wo BEIDE Karten
       Geometrie tragen. Blau: Ist liegt näher als Soll; Orange: Ist liegt ferner;
       Mittelgrau: gleich; Dunkelgrau: nur eine Karte hat dort Geometrie; Schwarz:
       keine. Fall A ist vollständig Mittelgrau (Differenz exakt 0). Fall B zeigt eine
       weiche Verlaufsfläche — die Potenz 2 verschiebt die Werte, nicht ihre Ordnung.
    4  Überdeckung, das Zweifarbenbild — Orange: nur Soll hat Geometrie, Blau: nur Ist,
       Weiss: beide. ``geom_iou`` ist wörtlich ablesbar: Weiss geteilt durch alles, was
       nicht Schwarz ist. In Fall A und B ist alles Weiss (IoU 1.0); in Fall C bleibt
       ein kleiner weisser Fleck rechts oben, der Rest ist Orange.

Unter den vier Kacheln ein Streifen in der Farbe des Gate-Urteils
(``geometrie_qa.geometrie_gate``): Grün = bestanden, Rot = durchgefallen. Die Zahlen
(``spearman``, ``geom_iou``, ``score``, Urteil) stehen im Dateinamen, nicht im Bild
(Regel 2: keine Bitmap-Schrift).

``NN_balken_…png`` — je Fall eine Dreiergruppe von Balken, von links nach rechts
treu / massstab / halluziniert; in jeder Gruppe Blau = spearman, Orange = geom_iou,
Dunkelgrau = score. Die dünne rote Linie ist ``SCHWELLE_GEOMETRIE`` (0.65) — die einzige
Zahl im Bild, die nicht in diesem Lauf gemessen wurde; sie ist die Konstante des Moduls.
Ein Quadrat unter jeder Gruppe trägt das Gate-Urteil (Grün/Rot). Alle Balkenlängen
stammen aus dem Lauf, der auch die Kacheln geschrieben hat.

Warum die Polarität hier übergeben wird
----------------------------------------
``geometrie_score(polaritaet=POLARITAET_TIEFE)``: Soll und Ist sind hier BEIDE metrische
Tiefe, ohne Schätzer dazwischen — die Polarität ist also nicht geschätzt, sondern
durch die Konstruktion bekannt. Ohne sie fiele die Rechnung auf ``abs(spearman)`` zurück,
und das Modul sagt selbst, dass dieser Modus nicht monoton im Fehler ist. Gewertet wird
darum der gerichtete Weg (``METHODE_GERICHTET``, v2).

Was dieser Beweis NICHT zeigt — und was das Gerät braucht
---------------------------------------------------------
Im Betrieb kommt die Ist-Karte aus ``tiefenschaetzer.qa_gegen_soll`` — einer
monokularen Tiefenschätzung aus dem erzeugten Bild, die Gewichte und in der Praxis eine
GPU braucht. Dieser Teil ist hier NICHT dabei, und zwar nicht aus Verlegenheit: Eine
Ist-Karte aus einem Schätzer hat keine bekannte Wahrheit, und ein Beweis ohne bekannte
Wahrheit beweist nur, dass zwei Zahlen verschieden sind. Der Schätzerfehler ist eine
eigene Messung (``auf-20260818-10``: |ρ| = 0.990 an Blenders eigenem Beauty-Pass). Was
hier steht, ist der Metrikkern des Nodes — er läuft vollständig ohne Gerät, ohne Blender,
ohne numpy, reine stdlib (Regel 4).

Die Szene ist synthetisch (Regel 3): ``schwellenstudie.baue_testszene`` — zwei Baukörper
mit Tiefensprung, in einer Zeile reproduzierbar.

Aufruf:
    python3 tools/beweis/04_knoten_qa.py [ziel_verzeichnis]

Ohne Argument schreibt es nach ``build/beweis/04_knoten_qa/``. Rückgabe 1, wenn die
Nullprobe (Fall A) nicht 1.000 liefert — das wäre kein «nicht gemessen», sondern ein
Befund gegen die Metrik.
"""
from __future__ import annotations

import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))

from aiimaging import bildschreiben, geometrie_qa, schwellenstudie  # noqa: E402

ZIEL_VORGABE = WURZEL / "build" / "beweis" / "04_knoten_qa"

#: Kantenlänge der Tiefenkarten. 64 wie in der Schwellenstudie — klein genug, dass die
#: reine Python-Rasterung in Sekunden läuft, gross genug für 1936 Geometriepunkte.
KANTE = 64
#: Jede Karte wird für die Bilder vergrössert (nächster Nachbar, keine Interpolation —
#: eine interpolierte Tiefenkarte zeigte Werte, die nie gemessen wurden).
VERGROESSERUNG = 4
KACHEL = KANTE * VERGROESSERUNG
FUGE = 8

FARBE_HINTERGRUND = (0, 0, 0)
FARBE_NUR_SOLL = (230, 120, 40)          # Orange
FARBE_NUR_IST = (50, 110, 210)           # Blau
FARBE_BEIDE = (235, 235, 235)            # Weiss: die Schnittmenge
FARBE_GLEICH = (128, 128, 128)           # Differenz 0
FARBE_NUR_EINE = (40, 40, 40)            # Differenz nicht definiert (nur eine Karte)
FARBE_BESTANDEN = (60, 150, 70)
FARBE_DURCHGEFALLEN = (190, 60, 50)
FARBE_SCHWELLE = (190, 60, 50)
FARBE_SCORE = (60, 60, 60)
FARBE_LEINWAND = (245, 245, 245)
FARBE_ACHSE = (120, 120, 120)


# ----------------------------------------------------------------------------------
# Die drei Fälle — jeder mit bekannter Wahrheit, alle aus Repo-Bausteinen
# ----------------------------------------------------------------------------------

def fall_treu(soll: list[float]) -> list[float]:
    return list(soll)


def fall_massstab(soll: list[float]) -> list[float]:
    """Streng monotone Umrechnung — rangerhaltend, absolut völlig anders."""
    return schwellenstudie.stoere(soll, schwellenstudie.MONOTON, 1.0,
                                  breite=KANTE, hoehe=KANTE)


def fall_halluziniert(soll: list[float]) -> list[float]:
    """Ein erfundenes Gebäude an anderer Stelle: eine zweite, halb so grosse Testszene,
    rechts oben eingesetzt. Ihre Tiefen stammen aus ``baue_testszene`` — nichts wird
    gemalt, nur verschoben.

    Position (x = 36, y = 0) ist gewählt, damit die Überlappung mit dem Soll klein,
    aber nicht null ist: Bei null gemeinsamen Punkten gäbe es keinen Score, sondern
    ``None`` — das wäre ein anderer, ebenfalls dokumentierter Fall, aber nicht der,
    um den es hier geht (innen stimmig, aussen daneben).
    """
    klein_kante = KANTE // 2
    klein = schwellenstudie.baue_testszene(klein_kante, klein_kante)
    ist = [schwellenstudie.HINTERGRUND_M] * (KANTE * KANTE)
    ox, oy = KANTE - klein_kante + 4, 0
    for y in range(klein_kante):
        for x in range(klein_kante):
            # x = 36 heisst: die rechten 4 px stehen über die Bildkante hinaus. Sie werden
            # abgeschnitten wie bei jeder Kamera — nicht in die nächste Zeile umgebrochen.
            if ox + x < KANTE and oy + y < KANTE:
                ist[(oy + y) * KANTE + ox + x] = klein[y * klein_kante + x]
    return ist


FAELLE = (
    ("treu", "unveraendert", fall_treu),
    ("massstab", "monoton-potenz2-faktor10-nullpunkt-minus50m", fall_massstab),
    ("halluziniert", "erfundene-kubatur-32px-rechts-oben", fall_halluziniert),
)


# ----------------------------------------------------------------------------------
# Kacheln — aus Zahlen werden Farben, jede Farbe hat genau eine Bedeutung
# ----------------------------------------------------------------------------------

def normalisiere_ueber_silhouette(karte: list[float]) -> tuple[list[float | None], list[bool]]:
    """Nah = 1, fern = 0 über der Silhouette; ``None`` im Hintergrund.

    Nicht ``bildschreiben.normalisiere_tiefe``: Das verlangt ``0 < t`` und schnitte
    die negativen Tiefen aus Fall B stumm weg. Die Silhouette kommt von
    ``geometrie_qa.silhouette`` — derselben Funktion, die auch der Score benutzt.
    """
    sil = geometrie_qa.silhouette(karte)
    werte = [karte[i] for i in range(len(karte)) if sil[i]]
    lo, hi = min(werte), max(werte)
    spanne = (hi - lo) or 1.0
    norm: list[float | None] = [None] * len(karte)
    for i in range(len(karte)):
        if sil[i]:
            norm[i] = 1.0 - (karte[i] - lo) / spanne
    return norm, sil


def kachel_tiefe(norm: list[float | None]) -> list[tuple[int, int, int]]:
    aus = []
    for v in norm:
        g = 0 if v is None else int(round(v * 255))
        aus.append((g, g, g))
    return aus


def _mische(a, b, t: float) -> tuple[int, int, int]:
    return tuple(int(round(a[k] + (b[k] - a[k]) * t)) for k in range(3))


def kachel_differenz(norm_soll, norm_ist) -> tuple[list[tuple[int, int, int]], float]:
    """Ist − Soll auf der gemeinsamen Silhouette. Liefert auch die grösste Abweichung,
    damit sie im Dateinamen steht."""
    aus = []
    groesste = 0.0
    for s, i in zip(norm_soll, norm_ist):
        if s is None and i is None:
            aus.append(FARBE_HINTERGRUND)
        elif s is None or i is None:
            aus.append(FARBE_NUR_EINE)
        else:
            d = i - s                       # > 0: Ist näher (heller) als Soll
            groesste = max(groesste, abs(d))
            ziel = FARBE_NUR_IST if d > 0 else FARBE_NUR_SOLL
            aus.append(_mische(FARBE_GLEICH, ziel, min(1.0, abs(d))))
    return aus, groesste


def kachel_ueberdeckung(sil_soll, sil_ist) -> list[tuple[int, int, int]]:
    aus = []
    for s, i in zip(sil_soll, sil_ist):
        if s and i:
            aus.append(FARBE_BEIDE)
        elif s:
            aus.append(FARBE_NUR_SOLL)
        elif i:
            aus.append(FARBE_NUR_IST)
        else:
            aus.append(FARBE_HINTERGRUND)
    return aus


def vergroessere(kachel, kante: int, faktor: int) -> list[tuple[int, int, int]]:
    aus = []
    for y in range(kante * faktor):
        zeile = kachel[(y // faktor) * kante:(y // faktor + 1) * kante]
        for x in range(kante * faktor):
            aus.append(zeile[x // faktor])
    return aus


def nebeneinander(kacheln, bestanden: bool, *, streifen: int = 12):
    """Vier Kacheln mit Fuge, darunter der Urteilsstreifen."""
    n = len(kacheln)
    breite = n * KACHEL + (n - 1) * FUGE
    hoehe = KACHEL + FUGE + streifen
    urteil = FARBE_BESTANDEN if bestanden else FARBE_DURCHGEFALLEN
    px = [FARBE_LEINWAND] * (breite * hoehe)
    for k, kachel in enumerate(kacheln):
        x0 = k * (KACHEL + FUGE)
        for y in range(KACHEL):
            zeile = kachel[y * KACHEL:(y + 1) * KACHEL]
            px[y * breite + x0:y * breite + x0 + KACHEL] = zeile
    for y in range(KACHEL + FUGE, hoehe):
        px[y * breite:(y + 1) * breite] = [urteil] * breite
    return px, breite, hoehe


# ----------------------------------------------------------------------------------
# Balkenbild — gemessene Zahlen des Laufs, eine Achse, feste Farben je Grösse
# ----------------------------------------------------------------------------------

def _rechteck(px, breite, hoehe, x0, y0, x1, y1, farbe) -> None:
    xa, xb = sorted((max(0, int(round(x0))), min(breite, int(round(x1)))))
    ya, yb = sorted((max(0, int(round(y0))), min(hoehe, int(round(y1)))))
    for y in range(ya, yb):
        for x in range(xa, xb):
            px[y * breite + x] = farbe


def zeichne_balken(ergebnisse: list[dict], *, breite: int = 720, hoehe: int = 360,
                   rand: int = 40, schwelle: float = geometrie_qa.SCHWELLE_GEOMETRIE):
    """Gruppen von links nach rechts in Reihenfolge der Fälle; je Gruppe
    spearman (Blau), geom_iou (Orange), score (Dunkelgrau).

    Die Achse reicht von 0 bis 1; ein negatives spearman würde nach unten unter die
    Grundlinie gezeichnet — die Grundlinie liegt darum nicht am Bildrand.
    """
    px = [FARBE_LEINWAND] * (breite * hoehe)
    masse = (("spearman", FARBE_NUR_IST), ("geom_iou", FARBE_NUR_SOLL), ("score", FARBE_SCORE))
    werte = [e[k] for e in ergebnisse for k, _ in masse if e[k] is not None]
    unten = min(0.0, min(werte)) if werte else 0.0
    oben = 1.0
    plot_oben, plot_unten = rand, hoehe - rand - 24        # 24 px für die Urteilsquadrate

    def y_von(v: float) -> float:
        return plot_unten - (v - unten) / (oben - unten) * (plot_unten - plot_oben)

    gruppen = len(ergebnisse)
    gruppen_breite = (breite - 2 * rand) / gruppen
    balken_breite = gruppen_breite / (len(masse) + 1.5)

    # Grundlinie (0), Deckenlinie (1) und die Schwelle des Moduls.
    _rechteck(px, breite, hoehe, rand, y_von(0.0), breite - rand, y_von(0.0) + 1, FARBE_ACHSE)
    _rechteck(px, breite, hoehe, rand, y_von(1.0), breite - rand, y_von(1.0) + 1, FARBE_ACHSE)
    _rechteck(px, breite, hoehe, rand, y_von(schwelle), breite - rand, y_von(schwelle) + 1,
              FARBE_SCHWELLE)

    for g, e in enumerate(ergebnisse):
        x_start = rand + g * gruppen_breite + balken_breite * 0.75
        for m, (name, farbe) in enumerate(masse):
            v = e[name]
            if v is None:
                continue
            x0 = x_start + m * balken_breite
            _rechteck(px, breite, hoehe, x0 + 2, y_von(v), x0 + balken_breite - 2,
                      y_von(0.0), farbe)
        urteil = FARBE_BESTANDEN if e["bestanden"] else FARBE_DURCHGEFALLEN
        mitte = rand + (g + 0.5) * gruppen_breite
        _rechteck(px, breite, hoehe, mitte - 8, plot_unten + 8, mitte + 8, plot_unten + 24,
                  urteil)
    return px, breite, hoehe


def _z(x: float | None) -> str:
    return "None" if x is None else f"{x:.3f}"


def main() -> int:
    ziel = Path(sys.argv[1]) if len(sys.argv) > 1 else ZIEL_VORGABE
    ziel.mkdir(parents=True, exist_ok=True)
    geschrieben: list[Path] = []
    nr = 0

    def schreibe(stamm: str, px, breite, hoehe) -> None:
        nonlocal nr
        nr += 1
        pfad = ziel / f"{nr:02d}_{stamm}.png"
        bildschreiben.schreibe_farb_png(pfad, px, breite, hoehe)
        geschrieben.append(pfad)

    soll = schwellenstudie.baue_testszene(KANTE, KANTE)
    norm_soll, sil_soll = normalisiere_ueber_silhouette(soll)
    kachel_soll = vergroessere(kachel_tiefe(norm_soll), KANTE, VERGROESSERUNG)
    schreibe("soll_nah-hell", kachel_soll, KACHEL, KACHEL)

    ergebnisse: list[dict] = []
    for name, beschreibung, baue in FAELLE:
        ist = baue(soll)
        # Das Urteil des Nodes — dieselbe Funktion, die kette.ART_QA über
        # tiefenschaetzer.qa_gegen_soll aufruft.
        e = geometrie_qa.geometrie_gate(soll, ist, polaritaet=geometrie_qa.POLARITAET_TIEFE)
        ergebnisse.append(e)

        norm_ist, sil_ist = normalisiere_ueber_silhouette(ist)
        k_ist = vergroessere(kachel_tiefe(norm_ist), KANTE, VERGROESSERUNG)
        diff, groesste = kachel_differenz(norm_soll, norm_ist)
        k_diff = vergroessere(diff, KANTE, VERGROESSERUNG)
        k_ueber = vergroessere(kachel_ueberdeckung(sil_soll, sil_ist), KANTE, VERGROESSERUNG)

        schreibe(f"{name}_ist_{beschreibung}", k_ist, KACHEL, KACHEL)
        schreibe(f"{name}_differenz_max-{groesste:.3f}", k_diff, KACHEL, KACHEL)
        schreibe(f"{name}_ueberdeckung_iou-{_z(e['geom_iou'])}"
                 f"_gemeinsam-{e['n_gemeinsam']}", k_ueber, KACHEL, KACHEL)
        px, b, h = nebeneinander([kachel_soll, k_ist, k_diff, k_ueber], e["bestanden"])
        urteil = "bestanden" if e["bestanden"] else "durchgefallen"
        schreibe(f"{name}_nebeneinander_rho-{_z(e['spearman'])}_iou-{_z(e['geom_iou'])}"
                 f"_score-{_z(e['score'])}_{urteil}", px, b, h)

    px, b, h = zeichne_balken(ergebnisse)
    stamm = "balken_spearman-iou-score_" + "_".join(
        f"{name}-{_z(e['score'])}" for (name, _, _), e in zip(FAELLE, ergebnisse)
    ) + f"_schwelle-{geometrie_qa.SCHWELLE_GEOMETRIE:.2f}"
    schreibe(stamm, px, b, h)

    for p in geschrieben:
        print(p)

    nullprobe = ergebnisse[0]["score"]
    if nullprobe is None or abs(nullprobe - 1.0) > 1e-9:
        print(f"NULLPROBE VERFEHLT: treu gibt {nullprobe!r} statt 1.000 — Befund gegen "
              f"die Metrik, nicht gegen die Szene.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
