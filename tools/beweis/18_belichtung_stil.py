#!/usr/bin/env python3
"""BEWEIS 18 — Der geerbte Rahmen verurteilt den eigenen Hausstil; der Hausstil-Rahmen
tut es nicht, bis wirklich SEINE eigene, gemessene Schwelle reisst.

Der Befund, um den es geht (Modulkopf ``belichtung.py``)
---------------------------------------------------------
Der Altbestand (``archviz_exposure_check.py``) kennt ``HIGHLIGHT_WARN_PCT = 8.0`` als
feste, ungeprüfte Konstante. Unser eigener Stilkorpus (`auf-20260818-14`, 74 Werke)
misst den Anteil ausgefressener Fläche (über 0.95 Helligkeit) im Mittel bei **0.0755**,
Streuung **0.069**, Höchstwert **0.3001** — der Mittelwert liegt KNAPP unter der alten
8-%-Schwelle, eine Streuung darüber liegt fast beim Doppelten. ``belichtung.py`` löst
das nicht durch eine neue Zahl, sondern durch eine Regel: Jede Schwelle hängt an einem
:class:`~aiimaging.belichtung.Rahmen`, und nur wer seine Schwellen wirklich gemessen hat
(``gemessen``-Feld), darf ``error`` melden. ``GEERBTER_RAHMEN`` führt die alte 8-%-Zahl
fort, aber mit ``gemessen=()`` — sie kann darum melden, aber nie verurteilen.

Was dieses Skript zeigt
------------------------
Eine Serie von acht SELBST GESCHRIEBENEN Testbildern (400×250, reine ``bildschreiben``-
Erzeugung, kein ``bpy``, kein Fremdbild) mit steigendem Lichteranteil — dem Anteil
reinweisser Bildpunkte (Luminanz 1.0) vor einem einheitlich grauen Grund (Luminanz
≈0.573, angelehnt an den gemessenen Hausstil-Mittelwert 0.5744). Die acht Anteile:
2 %, 5 %, 7.55 % (= Hausstil-Mittelwert), 8 % (= ``GEERBTER_RAHMEN.hell_anteil_max``,
die alte ``HIGHLIGHT_WARN_PCT``), 10 %, 14.5 % (≈ Mittelwert + eine Streuung), 21.4 %
(= ``HAUSSTIL_RAHMEN.hell_anteil_max``, die eigene, gemessene Grenze) und 30 % (≈ der
gemessene Höchstwert 0.3001). Jeder Anteil ist EXAKT (100 000 Bildpunkte, ganzzahlige
Treffer), keiner geschätzt.

Jedes Testbild wird WIRKLICH über ``belichtung.messe()`` gemessen — einmal ohne Rahmen
(Grenze 0.95, vergleichbar mit ``HAUSSTIL_RAHMEN``) und einmal mit
``rahmen=GEERBTER_RAHMEN`` (Grenze 0.98, seine eigene) — und WIRKLICH über
``belichtung.pruefe()`` beurteilt, gegen ``HAUSSTIL_RAHMEN`` bzw. gegen
``GEERBTER_RAHMEN``. Keine der beiden Urteilszahlen ist geraten; beide entstehen im
selben Lauf, aus derselben Datei. Das Histogramm entsteht direkt aus dem Pixel-Feld, das
dieses Skript selbst geschrieben hat — kein Bild wird zu diesem Zweck wieder eingelesen.

Woran man es im Bild sieht
----------------------------
``01``…``08`` — je eine Tafel pro Lichteranteil, von oben nach unten:

1. Das Testbild selbst (grau mit weissem Streusaat-Muster — die Körnung IST der
   gemessene Lichteranteil, gleichmässig über die Fläche verteilt, kein Zufall).
2. Sein Histogramm (256 Balken, ein Balken je Grauwert 0..255): eine grosse Säule beim
   Grundton, eine zweite bei 255. Zwei senkrechte Linien markieren die Hell-Grenzen:
   Blau bei 0.95 (``HAUSSTIL_RAHMEN``/``HELL_GRENZE``), Magenta bei 0.98
   (``GEERBTER_RAHMEN``) — man sieht, dass beide Grenzen rechts der Grundton-Säule und
   links der 255er-Säule liegen: Jedes Streukorn zählt bei BEIDEN Grenzen als
   „ausgefressen", der gemessene Anteil ist bei beiden Rahmen darum derselbe.
3. Ein Streifen, links/rechts geteilt: LINKS das Urteil von ``HAUSSTIL_RAHMEN``, RECHTS
   das von ``GEERBTER_RAHMEN`` — Grün = bestanden ohne Befund, Gelb = Warnung, Rot =
   Fehler. Der Dateiname trägt beide Wörter ausgeschrieben.

Der Punkt, an dem man es sieht — und er ist genauer, als die erste Messung vermuten
liess: ``pruefe`` prüft mehrere Felder gleichzeitig, und ``GEERBTER_RAHMEN`` bringt ZWEI
ungemessene Schwellen ins Spiel, nicht nur eine. Seine ``streuung_min`` (0.10, geerbt aus
dem alten ``LOW_CONTRAST_THRESHOLD``) reisst bereits bei den zwei DUNKELSTEN Tafeln (01,
02 — 2 % und 5 %): Bei so wenig weissen Punkten ist das Bild zu gleichmässig,
``belichtung.pruefe`` meldet ``flach`` — GELB, aber nicht wegen Ausgefressenheit, sondern
wegen Kontrastarmut. Die Streuung wächst mit dem Lichteranteil; ab Tafel 03 (7.55 %)
liegt sie über 0.10, und da der Lichteranteil selbst noch unter der 8-%-Grenze bleibt,
sind Tafel 03 und 04 die einzigen zwei GRÜNEN Tafeln auf der geerbten Seite — ein kurzer
Rückfall auf Grün, kein monotoner Anstieg. Erst ab Tafel 05 (10 %, real über der alten
``HIGHLIGHT_WARN_PCT``) meldet ``zu-viel-ausgefressen``, und ab Tafel 07 (21.4 %)
zusätzlich ``zu-hell`` (die geerbte ``TARGET_LUMA_MAX`` 0.65 reisst ebenfalls). GELB
bleibt es von da an bis zur letzten Tafel — gleich WELCHER der drei Befunde gerade greift,
denn ``GEERBTER_RAHMEN.gemessen == ()`` zwingt JEDEN seiner Befunde zur Warnung. Das ist
die eigentliche Pointe, breiter als die einzelne Schwelle, um die es im Modulkopf zuerst
geht: Ein Rahmen ohne eine einzige gemessene Zahl kann an KEINER seiner Kanten einen
Fehler melden, gleich an welcher er reisst — nicht nur an der einen, über die dieses
Skript eingangs spricht. Der linke (Hausstil-)Streifen bleibt aus demselben
``gemessen``-Mechanismus, aber mit anderen (tatsächlich gemessenen) Zahlen bis Tafel 07
(exakt 21.4 %, die eigene gemessene Grenze) GRÜN und wird erst bei Tafel 08 (30 %, real
darüber) ROT — die einzige Stelle im ganzen Bilderpaar, an der überhaupt ein Fehler
entsteht, und sie entsteht an der gemessenen, nicht an der geerbten Zahl.

``09_uebersicht_…png`` — dieselben acht Messungen als eine Tafel: der gemessene
Lichteranteil steigt von links nach rechts, zwei waagrechte Linien markieren die beiden
``hell_anteil_max``-Schwellen (Magenta 0.08, Blau 0.214), und unter jeder Gruppe stehen
zwei Punkte in Urteilsfarbe (links Hausstil, rechts Geerbt) auf der Höhe des jeweils
gemessenen Lichteranteils. Die rechten Punkte sind schon bei den ersten BEIDEN Gruppen
gelb — weit UNTER der Magenta-Linie, denn dort schlägt nicht die Fläche an, sondern die
Streuung (``streuung_min``, eine dritte, ebenfalls ungemessene Zahl des geerbten Rahmens):
Die Farbe eines Punktes ist hier also ausdrücklich KEINE reine Funktion des Abstands zur
gezeichneten Linie. Bei Gruppe 3 und 4 sind sie GRÜN (weder Streuung noch Fläche reisst),
erst ab Gruppe 5 — jetzt tatsächlich über der Magenta-Linie — werden sie wieder, und
diesmal bis zum Schluss durchgehend, gelb. Die linken Punkte kreuzen die Blau-Linie
(0.214) erst bei der letzten Gruppe und werden erst dort rot — die einzige rote Stelle im
ganzen Diagramm, und die einzige, die an einer wirklich gemessenen Zahl hängt.

Braucht kein Gerät. Läuft vollständig hier: Nur ``aiimaging.bildschreiben`` (schreibt)
und ``aiimaging.belichtung`` (misst, liest über ``aiimaging.bildlesen`` intern zurück —
das ist die geprüfte Produktionskette selbst, kein Umweg). Kein ``numpy``, kein ``PIL``,
kein ``bpy``. Regel 3: reine Arithmetik dieses Skripts, keine echten Projektdaten.

Aufruf:
    python3 tools/beweis/18_belichtung_stil.py [ziel_verzeichnis]

Ohne Argument schreibt es nach ``build/beweis/18_belichtung_stil/``. Rückgabe 1, wenn
die erwartete Auseinanderentwicklung (Geerbt nie Fehler, Hausstil erst ab 21.4 % Fehler)
in dieser Messung nicht eintritt — das wäre ein Bug in diesem Skript oder eine echte
Verhaltensänderung von ``belichtung.py``, kein Darstellungsproblem.
"""
from __future__ import annotations

import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))

from aiimaging import belichtung, bildschreiben  # noqa: E402

ZIEL_VORGABE = WURZEL / "build" / "beweis" / "18_belichtung_stil"

# ── Die Testbild-Serie ──────────────────────────────────────────────────────────────
#
# 400×250 = 100 000 Bildpunkte — gross genug, dass jeder gewünschte Anteil ganzzahlig
# und exakt trifft (kein gerundeter Anteil, ein GEZÄHLTER).
TB_BREITE = 400
TB_HOEHE = 250
N_PIXEL = TB_BREITE * TB_HOEHE

#: Grundton — angelehnt an den gemessenen Hausstil-Mittelwert 0.5744, als 8-Bit-Wert
#: zwangsläufig nicht exakt derselbe (146/255 = 0.5725), aber derselbe Grössenordnung.
BASIS_GRAU = round(0.5744 * 255)

#: Die acht Lichteranteile dieser Serie — siehe Modulkopf für die Herkunft jeder Zahl.
LICHTANTEILE = (0.02, 0.05, 0.0755, 0.08, 0.10, 0.145, 0.214, 0.30)

FARBE_LEINWAND = (245, 245, 245)
FARBE_ACHSE = (120, 120, 120)
FARBE_BALKEN = (90, 90, 90)
FARBE_GRENZE_HAUS = (50, 110, 210)     # Blau — HELL_GRENZE 0.95 / HAUSSTIL_RAHMEN
FARBE_GRENZE_GEERBT = (160, 60, 190)   # Magenta — GEERBTER_RAHMEN.hell_grenze 0.98
FARBE_SCHWERE = {
    belichtung.SCHWERE_OK: (60, 150, 70),      # Grün
    belichtung.SCHWERE_WARN: (225, 175, 40),   # Gelb
    belichtung.SCHWERE_FEHLER: (190, 60, 50),  # Rot
}

HIST_BREITE = 512
HIST_HOEHE = 140
STREIFEN_HOEHE = 40
FUGE = 10
TAFEL_BREITE = HIST_BREITE
TAFEL_HOEHE = TB_HOEHE + FUGE + HIST_HOEHE + FUGE + STREIFEN_HOEHE


def _rechteck(px, breite, hoehe, x0, y0, x1, y1, farbe) -> None:
    xa, xb = sorted((max(0, int(round(x0))), min(breite, int(round(x1)))))
    ya, yb = sorted((max(0, int(round(y0))), min(hoehe, int(round(y1)))))
    for y in range(ya, yb):
        px[y * breite + xa:y * breite + xb] = [farbe] * (xb - xa)


def testbild_farben(n_hell: int) -> list[tuple[int, int, int]]:
    """Grauer Grund, ``n_hell`` reinweisse Punkte, GLEICHMÄSSIG über die Fläche
    verteilt — kein Zufall, damit derselbe Anteil bei jedem Lauf dasselbe Bild ergibt."""
    farben = [(BASIS_GRAU, BASIS_GRAU, BASIS_GRAU)] * N_PIXEL
    farben = list(farben)
    if n_hell > 0:
        for i in range(n_hell):
            idx = int((i + 0.5) * N_PIXEL / n_hell)
            farben[min(idx, N_PIXEL - 1)] = (255, 255, 255)
    return farben


def histogramm_bins(farben) -> list[int]:
    """Zählt Grauwerte 0..255 direkt aus dem Pixel-Feld, das geschrieben wurde — kein
    erneutes Einlesen einer Datei nötig, das Feld liegt schon im Speicher."""
    bins = [0] * 256
    for r, _g, _b in farben:
        bins[r] += 1
    return bins


def zeichne_histogramm(bins: list[int]) -> tuple[list, int, int]:
    px = [FARBE_LEINWAND] * (HIST_BREITE * HIST_HOEHE)
    plot_oben, plot_unten = 4, HIST_HOEHE - 4
    hoch = max(bins) or 1
    balken_breite = HIST_BREITE / 256
    for wert in range(256):
        n = bins[wert]
        if n == 0:
            continue
        hoehe_bal = n / hoch * (plot_unten - plot_oben)
        x0 = wert * balken_breite
        _rechteck(px, HIST_BREITE, HIST_HOEHE, x0, plot_unten - hoehe_bal,
                  x0 + balken_breite, plot_unten, FARBE_BALKEN)
    # Grauwert → x-Pixel im Histogramm (balken_breite Pixel je Grauwertstufe):
    x_haus = belichtung.HELL_GRENZE * 255 * balken_breite
    x_geerbt = belichtung.GEERBTER_RAHMEN.hell_grenze * 255 * balken_breite
    _rechteck(px, HIST_BREITE, HIST_HOEHE, x_haus, 0, x_haus + 2, HIST_HOEHE,
              FARBE_GRENZE_HAUS)
    _rechteck(px, HIST_BREITE, HIST_HOEHE, x_geerbt, 0, x_geerbt + 2, HIST_HOEHE,
              FARBE_GRENZE_GEERBT)
    return px, HIST_BREITE, HIST_HOEHE


def baue_tafel(testbild, hist_px, urteil_haus: dict, urteil_geerbt: dict):
    px = [FARBE_LEINWAND] * (TAFEL_BREITE * TAFEL_HOEHE)
    x_off = (TAFEL_BREITE - TB_BREITE) // 2
    for y in range(TB_HOEHE):
        px[y * TAFEL_BREITE + x_off:y * TAFEL_BREITE + x_off + TB_BREITE] = \
            testbild[y * TB_BREITE:(y + 1) * TB_BREITE]

    y_hist = TB_HOEHE + FUGE
    for y in range(HIST_HOEHE):
        px[(y_hist + y) * TAFEL_BREITE:(y_hist + y) * TAFEL_BREITE + HIST_BREITE] = \
            hist_px[y * HIST_BREITE:(y + 1) * HIST_BREITE]

    y_streifen = y_hist + HIST_HOEHE + FUGE
    _rechteck(px, TAFEL_BREITE, TAFEL_HOEHE, 0, y_streifen, TAFEL_BREITE // 2,
              y_streifen + STREIFEN_HOEHE, FARBE_SCHWERE[urteil_haus["schwere"]])
    _rechteck(px, TAFEL_BREITE, TAFEL_HOEHE, TAFEL_BREITE // 2, y_streifen,
              TAFEL_BREITE, y_streifen + STREIFEN_HOEHE,
              FARBE_SCHWERE[urteil_geerbt["schwere"]])
    return px, TAFEL_BREITE, TAFEL_HOEHE


def zeichne_uebersicht(ergebnisse: list[dict], *, breite=512, hoehe=300, rand=50):
    """Alle acht Messungen in einer Tafel — der gemessene Lichteranteil steigt von
    links nach rechts, zwei Punkte je Gruppe (links Hausstil, rechts Geerbt)."""
    px = [FARBE_LEINWAND] * (breite * hoehe)
    plot_oben, plot_unten = rand, hoehe - rand
    y_max = 0.34  # deckt den höchsten gemessenen Anteil (0.30) mit Luft ab

    def y_von(v: float) -> float:
        return plot_unten - (v / y_max) * (plot_unten - plot_oben)

    _rechteck(px, breite, hoehe, rand, plot_unten, breite - rand, plot_unten + 1,
              FARBE_ACHSE)
    y = y_von(belichtung.GEERBTER_RAHMEN.hell_anteil_max)
    _rechteck(px, breite, hoehe, rand, y, breite - rand, y + 2, FARBE_GRENZE_GEERBT)
    y = y_von(belichtung.HAUSSTIL_RAHMEN.hell_anteil_max)
    _rechteck(px, breite, hoehe, rand, y, breite - rand, y + 2, FARBE_GRENZE_HAUS)

    n = len(ergebnisse)
    gruppen_breite = (breite - 2 * rand) / n
    for g, e in enumerate(ergebnisse):
        mitte = rand + (g + 0.5) * gruppen_breite
        y = y_von(e["anteil_hell"])
        _rechteck(px, breite, hoehe, mitte - 16, y - 6, mitte - 3, y + 6,
                  FARBE_SCHWERE[e["schwere_haus"]])
        _rechteck(px, breite, hoehe, mitte + 3, y - 6, mitte + 16, y + 6,
                  FARBE_SCHWERE[e["schwere_geerbt"]])
    return px, breite, hoehe


def main() -> int:
    ziel = Path(sys.argv[1]) if len(sys.argv) > 1 else ZIEL_VORGABE
    ziel.mkdir(parents=True, exist_ok=True)
    geschrieben: list[Path] = []
    eingabebilder: list[Path] = []
    nr = 0

    def schreibe(stamm: str, px, breite, hoehe) -> None:
        nonlocal nr
        nr += 1
        pfad = ziel / f"{nr:02d}_{stamm}.png"
        bildschreiben.schreibe_farb_png(pfad, px, breite, hoehe)
        geschrieben.append(pfad)

    ergebnisse: list[dict] = []
    print(f"Testbild {TB_BREITE}x{TB_HOEHE} = {N_PIXEL} Punkte, Grundton {BASIS_GRAU} "
          f"(Luminanz {BASIS_GRAU / 255:.4f}), {len(LICHTANTEILE)} Lichteranteile.")

    for p in LICHTANTEILE:
        n_hell = round(p * N_PIXEL)
        farben = testbild_farben(n_hell)

        eingabe = ziel / f"_testbild_lichteranteil-{p:.4f}.png"
        bildschreiben.schreibe_farb_png(eingabe, farben, TB_BREITE, TB_HOEHE)
        eingabebilder.append(eingabe)

        # Die eigentliche, geprüfte Produktivkette: messe() liest die Datei WIRKLICH
        # über bildlesen zurück, pruefe() urteilt gegen den jeweiligen Rahmen.
        messung_haus = belichtung.messe(eingabe)
        urteil_haus = belichtung.pruefe(messung_haus, belichtung.HAUSSTIL_RAHMEN)
        messung_geerbt = belichtung.messe(eingabe, rahmen=belichtung.GEERBTER_RAHMEN)
        urteil_geerbt = belichtung.pruefe(messung_geerbt, belichtung.GEERBTER_RAHMEN)

        bins = histogramm_bins(farben)
        hist_px, hist_b, hist_h = zeichne_histogramm(bins)
        tafel_px, tafel_b, tafel_h = baue_tafel(farben, hist_px, urteil_haus,
                                                urteil_geerbt)

        # Welches Feld genau den Befund auslöst — nicht nur die Schwere. GEERBTER_RAHMEN
        # prüft mehrere Felder gleichzeitig (hell_anteil_max, luma_max, streuung_min),
        # und WELCHES davon greift, ändert sich über die Serie (siehe Modulkopf); ohne
        # diese Liste liesse sich die Docstring-Erzählung nicht gegen die Messung prüfen.
        befunde_haus = tuple(b["feld"] for b in urteil_haus["befunde"])
        befunde_geerbt = tuple(b["feld"] for b in urteil_geerbt["befunde"])

        eintrag = {
            "lichteranteil_soll": p,
            "n_hell": n_hell,
            "anteil_hell": messung_haus["anteil_hell"],
            "anteil_hell_geerbt": messung_geerbt["anteil_hell"],
            "schwere_haus": urteil_haus["schwere"],
            "schwere_geerbt": urteil_geerbt["schwere"],
            "bestanden_haus": urteil_haus["bestanden"],
            "bestanden_geerbt": urteil_geerbt["bestanden"],
            "befunde_haus": befunde_haus,
            "befunde_geerbt": befunde_geerbt,
        }
        ergebnisse.append(eintrag)

        schreibe(
            f"lichteranteil-{p:.4f}_haus-{urteil_haus['schwere']}_"
            f"geerbt-{urteil_geerbt['schwere']}",
            tafel_px, tafel_b, tafel_h,
        )

        print(f"  p={p:.4f} (n_hell={n_hell:6d})  "
              f"gemessen anteil_hell={messung_haus['anteil_hell']:.4f}  "
              f"Haus={urteil_haus['schwere']:5s} (bestanden={urteil_haus['bestanden']}, "
              f"befunde={befunde_haus or '-'})  "
              f"Geerbt={urteil_geerbt['schwere']:5s} "
              f"(bestanden={urteil_geerbt['bestanden']}, befunde={befunde_geerbt or '-'})")

    px, b, h = zeichne_uebersicht(ergebnisse)
    stamm = "uebersicht_" + "-".join(
        f"{e['schwere_haus'][0]}{e['schwere_geerbt'][0]}" for e in ergebnisse
    )
    schreibe(stamm, px, b, h)

    for p in geschrieben:
        print(p)
    for p in eingabebilder:
        print(p)

    # Die Aussage dieses Beweises als harte Prüfung, nicht nur als Bild: der geerbte
    # Rahmen darf NIE einen Fehler melden (gemessen == ()), der Hausstil-Rahmen erst ab
    # seiner eigenen, gemessenen Grenze (0.214, hier bei p=0.30 und p=0.214 sicher
    # gerissen, bei p<=0.145 sicher nicht).
    fehlgeschlagen = []
    if any(e["schwere_geerbt"] == belichtung.SCHWERE_FEHLER for e in ergebnisse):
        fehlgeschlagen.append("GEERBTER_RAHMEN hat einen Fehler gemeldet — das darf "
                              "bei gemessen=() nie passieren.")
    if ergebnisse[-1]["schwere_haus"] != belichtung.SCHWERE_FEHLER:
        fehlgeschlagen.append("Bei p=0.30 (über der gemessenen Grenze 0.214) meldet "
                              "HAUSSTIL_RAHMEN keinen Fehler.")
    if any(e["schwere_haus"] == belichtung.SCHWERE_FEHLER
           for e in ergebnisse if e["lichteranteil_soll"] <= 0.145):
        fehlgeschlagen.append("HAUSSTIL_RAHMEN meldet unterhalb seiner gemessenen "
                              "Grenze bereits einen Fehler.")

    # Die Docstring-Erzählung behauptet mehr als nur "irgendwann gelb": Sie behauptet,
    # WELCHES Feld bei welchem Anteil greift (erst streuung_min, dann eine grüne Lücke,
    # dann hell_anteil_max). Das ist keine Illustration, wenn es hier gegen die echten
    # Befund-Namen aus pruefe() geprüft wird — sonst wäre es nur eine Geschichte, die zum
    # Bild passt, ohne dass irgendetwas sie hätte widerlegen können.
    by_p = {e["lichteranteil_soll"]: e for e in ergebnisse}
    if by_p[0.02]["befunde_geerbt"] != ("streuung_min",) or \
            by_p[0.05]["befunde_geerbt"] != ("streuung_min",):
        fehlgeschlagen.append("Bei 2%/5% meldet GEERBTER_RAHMEN nicht mehr ausschliesslich "
                              "'streuung_min' (Kontrastarmut) — die Docstring-Erklärung "
                              "des frühen Gelb passt nicht mehr zur Messung.")
    if by_p[0.0755]["befunde_geerbt"] or by_p[0.08]["befunde_geerbt"]:
        fehlgeschlagen.append("Bei 7.55%/8% meldet GEERBTER_RAHMEN einen Befund — die "
                              "behauptete grüne Lücke zwischen den beiden Gelb-Phasen "
                              "gibt es in dieser Messung nicht (mehr).")
    if not all("hell_anteil_max" in by_p[p]["befunde_geerbt"]
               for p in (0.10, 0.145, 0.214, 0.30)):
        fehlgeschlagen.append("Ab 10% meldet GEERBTER_RAHMEN nicht durchgehend "
                              "'hell_anteil_max' — die Kernbehauptung dieses Beweises "
                              "(die alte HIGHLIGHT_WARN_PCT reisst) trägt nicht mehr.")

    if fehlgeschlagen:
        print("AUSEINANDERENTWICKLUNG NICHT WIE ERWARTET:", file=sys.stderr)
        for zeile in fehlgeschlagen:
            print(f"  - {zeile}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
