"""Der Nachweis, dass die Schwellenstudie misst und nicht bloss Zahlen erzeugt.

Eine Kalibrierung ist nur so viel wert wie ihre Messinstrumente. Drei Dinge müssen
darum belegt sein, bevor eine einzige Kurve gedeutet werden darf:

1. **Die Szene trägt die Studie.** ``baue_testszene`` nennt in ihrem Docstring zwei
   Eigenschaften als Voraussetzung, nicht als Zierde — Bindungsfreiheit und einen
   Tiefensprung. Beide wurden nachgerüstet, nachdem ihr Fehlen zwei Störungen wirkungslos
   gemacht hatte. ``test_szene_ist_praktisch_bindungsfrei`` ist der wichtigste Test dieser
   Datei: Bricht er, ist die Rangkorrelation überwiegend eine Rechnung über
   Bindungsgruppen, und jede Zeile der Studie ist fragwürdig.

2. **Jede Störung tut, was ihre Registry-Erwartung sagt.** ``wirkt_auf_spearman`` und
   ``wirkt_auf_iou`` sind Vorhersagen; hier treffen sie einzeln und benannt ein, nicht nur
   gesammelt über ``erwartung_erfuellt``. Eine Störung, die stillschweigend den falschen
   Score-Anteil trifft, wäre ein schiefes Instrument — es lieferte saubere Zahlen über
   nichts.

3. **Die zwei Kontrollen halten.** ``MONOTON`` muss den Score bei 1.0 lassen (ein
   rangbasiertes Verfahren *muss* das), ``TIEFENUMKEHR`` muss unsichtbar bleiben. Der
   zweite Fall ist eine bekannte Grenze der Metrik und wird hier festgehalten, damit sie
   in Zahlen steht und nicht nur in einem Nebensatz.

Was diese Datei zusätzlich festhält, weil es beim Prüfen auffiel und die Deutung der
Studie berührt:

* ``test_glaettung_ist_ein_stumpfes_instrument`` — die Störung ``glaettung`` bewegt den
  Score über ihre ganze Stärkeskala um weniger als 0.01, und der Effekt schrumpft mit
  wachsender Auflösung. Ihre Registry-Erwartung trifft ein, ihre Kurve ist aber praktisch
  flach.
* ``test_staerkeachse_ist_bei_den_raeumlichen_stoerungen_grob_gerastert`` — bei 32×32
  liefern die Stärken 0.2 und 0.3 *punktgleich* dieselbe Störung. Da die Trennschärfe bei
  ``grenzstaerke=0.2`` zwischen „treu" und „untreu" schneidet, stehen dort zwei Zeilen mit
  identischer Messung auf verschiedenen Seiten der Grenze — keine Schwelle der Welt kann
  sie trennen.

Alles ist synthetisch und hier erzeugt (Regel 3): kein Blender, keine GPU, kein Netz,
kein numpy. Zufall trägt einen festen Startwert, damit jeder Lauf dieselben Zahlen
liefert.
"""
from __future__ import annotations

import ast
import json
import math
import sys

import pytest

from aiimaging import geometrie_qa
from aiimaging.geometrie_qa import HINTERGRUND_SCHWELLE_M, geometrie_score
from aiimaging.schwellenstudie import (
    BLEIBT,
    FAELLT,
    GLAETTUNG,
    HERKUNFT_BERICHT,
    HERKUNFT_KARTE,
    HINTERGRUND_M,
    MONOTON,
    RAUSCHEN,
    SILHOUETTE_SCHRUMPFEN,
    SILHOUETTE_WACHSEN,
    STOERUNGEN,
    TIEFENUMKEHR,
    VERSCHIEBUNG,
    VORBEHALT_NICHT_DIE_KETTE,
    VORGABE_STAERKEN,
    ZUSATZKOERPER,
    StudienError,
    baue_testszene,
    stoere,
    studie_aus_bericht,
    studienlauf,
    trennschaerfe,
    trennschaerfe_kurve,
)
from conftest import PAKET

# --------------------------------------------------------------------------------------
# Die Studienszene der Tests
# --------------------------------------------------------------------------------------

#: Arbeitsmass dieser Datei. 32×32 statt 64×64 aus einem einzigen Grund: ``glaettung``
#: bei Stärke 1.0 sind acht Mittelungsdurchgänge in reinem Python. Die Aussagen hängen
#: nicht an der Auflösung — wo doch, steht die Grösse ausdrücklich im Test.
BREITE, HOEHE = 32, 32

#: Die kleinste Szene, die nachweislich **ganz ohne** Bindungen auskommt (siehe
#: ``test_grosse_szene_ist_vollstaendig_bindungsfrei``). Sie trägt die Kontrollen, wo es
#: auf das letzte Bit ankommt.
GROSS = 48

#: Die ungestörte Soll-Karte. Alle Ist-Karten entstehen aus ihr.
SOLL = baue_testszene(BREITE, HOEHE)

#: Dieselbe Szene, bindungsfrei.
SOLL_GROSS = baue_testszene(GROSS, GROSS)

#: Nur die Störungen, die etwas *messen* sollen. Die zwei Kontrollen prüfen die Metrik
#: selbst und dürfen den Score gerade nicht senken.
MESSENDE = tuple(art for art, s in STOERUNGEN.items() if not s.ist_kontrolle)

#: Stärken über der Nullprobe. Die 0.0 wird eigens geprüft, sie ist keine Störung.
GESTOERTE_STAERKEN = tuple(s for s in VORGABE_STAERKEN if s > 0.0)


def geometriepunkte(karte) -> list[int]:
    """Indizes der Bildpunkte, die Geometrie tragen — dieselbe Grenze wie in der Metrik."""
    return [i for i, w in enumerate(karte)
            if math.isfinite(w) and w < HINTERGRUND_SCHWELLE_M]


def geometriewerte(karte) -> list[float]:
    return [karte[i] for i in geometriepunkte(karte)]


def bindungen(werte) -> int:
    """Wie viele Werte einen anderen Wert doppeln.

    Dieselbe Zählweise wie im Docstring von ``baue_testszene`` („1837 Bindungen auf 1936
    Punkte"): Anzahl minus Anzahl verschiedener Werte.
    """
    return len(werte) - len(set(werte))


def masse(breite: int, hoehe: int) -> tuple[int, int, int, int]:
    """Die Rechtecksgrenzen des Baus, aus derselben Rechnung wie in ``baue_testszene``."""
    return breite // 6, breite - breite // 6, hoehe // 6, hoehe - hoehe // 6


def score_von(art: str, staerke: float, *, soll=SOLL, breite=BREITE, hoehe=HOEHE,
              seed: int = 0) -> dict:
    """Eine Studienzeile in ihrer rohen Form: stören, messen, Messwerte zurückgeben."""
    ist = stoere(soll, art, staerke, breite=breite, hoehe=hoehe, seed=seed)
    return geometrie_score(soll, ist)


#: Der volle Studienlauf über die Arbeitsszene. Einmal gerechnet (rund 0.2 s), von vielen
#: Tests gelesen — er ist ein Messergebnis und wird nirgends verändert.
ERGEBNIS = studienlauf(SOLL, breite=BREITE, hoehe=HOEHE, szene="quader-mit-fluegel-32")

#: Eine absichtlich zu kleine Szene: Dort fallen Zeilen unter ``MIN_GEMEINSAME_PUNKTE``
#: und liefern **keinen** Score. Genau die braucht es, um zu prüfen, dass nicht messbare
#: Zeilen nirgends mitgezählt werden.
SOLL_KLEIN = baue_testszene(8, 8)
ERGEBNIS_KLEIN = studienlauf(SOLL_KLEIN, breite=8, hoehe=8, szene="zu-klein-8")


# --------------------------------------------------------------------------------------
# A · Die Testszene — sie trägt die ganze Studie
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("breite, hoehe", [(16, 16), (24, 24), (32, 32), (32, 48),
                                           (48, 48), (64, 64)])
def test_szene_ist_praktisch_bindungsfrei(breite, hoehe):
    """**Der wichtigste Test dieser Datei.** Bricht er, ist jede Zeile der Studie fragwürdig.

    Die erste Fassung der Szene war ein Gefälle aus der Summe zweier gleich gewichteter
    Achsenanteile und hatte damit **1837 Bindungen auf 1936 Punkte** (95 %). Über so einer
    Karte ist die Rangkorrelation grösstenteils eine Rechnung über Bindungsgruppen: Sie
    misst dann, wie ein Verfahren gleiche Werte gruppiert, und nicht mehr die Tiefenordnung.
    Genau daran scheiterte die Kontrolle ``monoton`` scheinbar — nicht die Metrik war
    schuld, sondern die Szene.

    Das inkommensurable Achsenverhältnis (√2) drückt die Quote auf höchstens 5 %; über
    alle geprüften Bildmasse von 8×8 bis 65×65 wird dieser Wert nirgends überschritten.
    """
    werte = geometriewerte(baue_testszene(breite, hoehe))
    anteil = bindungen(werte) / len(werte)
    assert anteil <= 0.05, (
        f"{breite}×{hoehe}: {anteil:.1%} der Geometriepunkte doppeln einen anderen Wert. "
        f"Über einer Karte mit vielen Bindungen misst die Rangkorrelation Gruppierung "
        f"statt Tiefenordnung — die Vorgängerfassung lag bei 95 %."
    )


@pytest.mark.parametrize("kante", [48, 64])
def test_grosse_szene_ist_vollstaendig_bindungsfrei(kante):
    """Ab 48×48 trifft kein Punktpaar mehr denselben Wert — dort ist die Rangkorrelation
    eine reine Ordnungsaussage. Diese Grössen tragen darum die Kontrollen, bei denen es
    auf das letzte Bit ankommt."""
    assert bindungen(geometriewerte(baue_testszene(kante, kante))) == 0


@pytest.mark.parametrize("breite, hoehe", [(16, 16), (32, 32), (48, 48)])
def test_szene_hat_genau_einen_tiefensprung(breite, hoehe):
    """Ohne Sprung ist die Karte eine reine Rampe — und eine Rampe überlebt jede Mittelung.

    Der Mittelwert einer linearen Folge ist wieder dieselbe Folge; die Störung
    ``glaettung`` hatte auf der ersten Szenenfassung darum **nichts zu zerstören** und
    lieferte Score 1.000 bei jeder Stärke. Der vorspringende Flügel liefert die Kante.

    Geprüft wird an einer waagrechten Schnittlinie mitten durch den Flügel: **genau ein**
    Schritt ist gross (mindestens ein Viertel der Wertespanne), alle anderen sind
    Rampenschritte unter 5 %. Ein einzelner scharfer Absatz — nicht viel Rauschen, das
    zufällig einmal gross ausfällt.
    """
    karte = baue_testszene(breite, hoehe)
    x0, x1, y0, y1 = masse(breite, hoehe)
    zeile_y = (y0 + (y1 - y0) // 4 + y1 - (y1 - y0) // 4) // 2
    spanne = max(geometriewerte(karte)) - min(geometriewerte(karte))
    schritte = [karte[zeile_y * breite + x + 1] - karte[zeile_y * breite + x]
                for x in range(x0, x1 - 1)]

    gross = [d for d in schritte if abs(d) >= 0.25 * spanne]
    klein = [d for d in schritte if abs(d) < 0.25 * spanne]
    assert len(gross) == 1, f"erwartet genau ein Sprung, gemessen {len(gross)}"
    assert all(abs(d) < 0.05 * spanne for d in klein), "die Rampe ist keine Rampe mehr"


def test_der_sprung_ist_ein_drittel_der_bautiefe():
    """Die Sprunghöhe ist gesetzt, nicht zufällig: ein Drittel von ``fern_m - nah_m``.

    Gross genug, dass Glättung ihn verschleift; klein genug, dass er nicht die ganze
    Tiefenordnung dominiert. Der gemessene Absatz ist der Sprung **plus** ein
    Rampenschritt, weil die Rampe unter ihm weiterläuft.
    """
    nah, fern = 18.0, 27.0
    karte = baue_testszene(BREITE, HOEHE, nah_m=nah, fern_m=fern)
    x0, x1, y0, y1 = masse(BREITE, HOEHE)
    zeile_y = (y0 + (y1 - y0) // 4 + y1 - (y1 - y0) // 4) // 2
    schritte = [karte[zeile_y * BREITE + x + 1] - karte[zeile_y * BREITE + x]
                for x in range(x0, x1 - 1)]
    rampenschritt = min(schritte)
    assert max(schritte) == pytest.approx((fern - nah) / 3.0 + rampenschritt)


def test_szene_hat_hintergrund():
    """Ohne Hintergrund gibt es keine Silhouette — und ``geom_iou`` misst nichts.

    Der Bau füllt bewusst nur die mittleren Zweidrittel. Wäre das Bild randvoll, wäre der
    IoU strukturell 1.0, und die Hälfte des Scores stünde als Konstante in jeder Zeile.
    """
    karte = baue_testszene(BREITE, HOEHE)
    hintergrund = [w for w in karte if w >= HINTERGRUND_SCHWELLE_M]
    assert hintergrund, "kein einziger Hintergrundpunkt"
    assert all(w == HINTERGRUND_M for w in hintergrund)
    assert len(hintergrund) / len(karte) > 0.3


@pytest.mark.parametrize("breite, hoehe", [(8, 8), (16, 24), (32, 32), (48, 40)])
def test_szene_hat_die_zugesagten_masse(breite, hoehe):
    """Länge und Silhouettengrösse folgen der Rechnung, nicht dem Zufall.

    Die Länge ist Voraussetzung für ``stoere`` (das die Masse gegen sie prüft), die
    Silhouettengrösse für die Deutung jedes ``geom_iou``.
    """
    karte = baue_testszene(breite, hoehe)
    x0, x1, y0, y1 = masse(breite, hoehe)
    assert len(karte) == breite * hoehe
    assert len(geometriepunkte(karte)) == (x1 - x0) * (y1 - y0)


def test_szene_bleibt_im_zugesagten_tiefenbereich():
    """``nah_m`` und ``fern_m`` spannen die Rampe; der Flügel springt um ein Drittel davor.

    Der tiefste Punkt liegt also nicht bei ``nah_m``, sondern bis zu einer Drittelspanne
    davor — wer das nicht weiss, hält den Flügel für einen Fehler.
    """
    nah, fern = 5.0, 8.0
    werte = geometriewerte(baue_testszene(BREITE, HOEHE, nah_m=nah, fern_m=fern))
    assert max(werte) == pytest.approx(fern)
    assert min(werte) >= nah - (fern - nah) / 3.0
    assert min(werte) < nah, "ohne Flügel wäre nah_m der vorderste Wert"


@pytest.mark.parametrize("breite, hoehe", [(7, 8), (8, 7), (0, 0), (4, 40)])
def test_zu_kleine_szene_ist_ein_fehler(breite, hoehe):
    """Unter 8×8 bliebe von der Silhouette nach einer Störung nichts übrig. Ein Fehler
    statt einer stillen Ersatzgrösse: Eine Studie über zwölf Punkte wäre keine."""
    with pytest.raises(StudienError, match="mindestens 8"):
        baue_testszene(breite, hoehe)


# --------------------------------------------------------------------------------------
# B · Jede Störung tut, was ihre Registry-Erwartung sagt
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("art", sorted(STOERUNGEN))
def test_staerke_null_gibt_die_karte_punktgleich_zurueck(art):
    """Die Nullprobe. Ein Score, der hier nicht 1.0 ist, entwertet jede Zeile darunter.

    Geprüft wird Punkt für Punkt und nicht über den Score: Ein Score von 1.0 liesse noch
    offen, ob die Karte gleich ist oder nur gleich *geordnet*.
    """
    unveraendert = stoere(SOLL, art, 0.0, breite=BREITE, hoehe=HOEHE)
    assert unveraendert == SOLL
    assert unveraendert is not SOLL, "die Soll-Karte darf nie durchgereicht werden"


@pytest.mark.parametrize("art", sorted(STOERUNGEN))
def test_stoerung_laesst_die_soll_karte_unberuehrt(art):
    """Die Soll-Karte wird über den ganzen Lauf hinweg wiederverwendet. Würde eine Störung
    sie verändern, trüge jede folgende Zeile die Spuren der vorigen — und niemand sähe es
    den Zahlen an."""
    vorher = list(SOLL)
    stoere(SOLL, art, 1.0, breite=BREITE, hoehe=HOEHE)
    assert SOLL == vorher


def test_rauschen_senkt_die_rangkorrelation_und_laesst_die_silhouette_in_ruhe():
    """Erwartung der Registry: ``spearman`` fällt, ``geom_iou`` bleibt.

    Rauschen liegt auf der Tiefe der Geometriepunkte, nicht auf ihrer Lage — die
    Silhouette ist danach dieselbe Punktmenge. Das ist das Bild des Messrauschens eines
    monokularen Schätzers: Die Kubatur stimmt, die Tiefenordnung franst aus.
    """
    assert STOERUNGEN[RAUSCHEN].wirkt_auf_spearman == FAELLT
    assert STOERUNGEN[RAUSCHEN].wirkt_auf_iou == BLEIBT

    messung = score_von(RAUSCHEN, 0.5)
    assert messung["geom_iou"] == 1.0
    assert messung["n_soll"] == messung["n_ist"]
    assert abs(messung["spearman"]) < 1.0
    assert messung["score"] < 0.95


def test_silhouette_wachsen_senkt_den_iou_und_laesst_die_rangkorrelation_in_ruhe():
    """Erwartung der Registry: ``geom_iou`` fällt, ``spearman`` bleibt.

    Ein Anbau, den es nicht gibt — Vordach, Brüstung, erfundene Wand. Die neuen Punkte
    liegen ausserhalb der Soll-Silhouette und gehen darum gar nicht in die Rangkorrelation
    ein: Die wird nur über die **gemeinsame** Silhouette gerechnet, und die ist unverändert
    die alte. Deshalb muss ``spearman`` exakt 1.0 bleiben, nicht bloss ungefähr.
    """
    assert STOERUNGEN[SILHOUETTE_WACHSEN].wirkt_auf_spearman == BLEIBT
    assert STOERUNGEN[SILHOUETTE_WACHSEN].wirkt_auf_iou == FAELLT

    messung = score_von(SILHOUETTE_WACHSEN, 0.5)
    assert messung["spearman"] == 1.0
    assert messung["geom_iou"] < 1.0
    assert messung["n_ist"] > messung["n_soll"], "gewachsen heisst: mehr Punkte"
    assert messung["n_gemeinsam"] == messung["n_soll"], "der Bau selbst bleibt erhalten"


def test_silhouette_schrumpfen_senkt_den_iou_und_laesst_die_rangkorrelation_in_ruhe():
    """Erwartung der Registry: ``geom_iou`` fällt, ``spearman`` bleibt.

    Das Gegenstück: ein Bildmodell, das weglässt. Der abgetragene Rand verschwindet aus
    der gemeinsamen Silhouette; was übrig bleibt, trägt seine Tiefen unverändert — die
    Ordnung auf einer Teilmenge einer geordneten Menge ist dieselbe Ordnung.
    """
    assert STOERUNGEN[SILHOUETTE_SCHRUMPFEN].wirkt_auf_spearman == BLEIBT
    assert STOERUNGEN[SILHOUETTE_SCHRUMPFEN].wirkt_auf_iou == FAELLT

    messung = score_von(SILHOUETTE_SCHRUMPFEN, 0.5)
    assert messung["spearman"] == 1.0
    assert messung["geom_iou"] < 1.0
    assert messung["n_ist"] < messung["n_soll"]


def test_verschiebung_trifft_beide_anteile():
    """Erwartung der Registry: beides fällt — die einzige Störung, die das tut.

    Eine verrutschte Kamera verschiebt die Silhouette (``geom_iou`` fällt) **und** stellt
    im überlappenden Rest andere Tiefen übereinander (``spearman`` fällt). Genau darum
    steht sie in der Registry mit zwei ``faellt`` und ist der Prüfstein dafür, dass die
    Erwartungen nicht bloss zwei Schablonen sind.
    """
    assert STOERUNGEN[VERSCHIEBUNG].wirkt_auf_spearman == FAELLT
    assert STOERUNGEN[VERSCHIEBUNG].wirkt_auf_iou == FAELLT

    messung = score_von(VERSCHIEBUNG, 0.5)
    assert abs(messung["spearman"]) < 1.0
    assert messung["geom_iou"] < 1.0


def test_glaettung_senkt_die_rangkorrelation_und_laesst_die_silhouette_in_ruhe():
    """Erwartung der Registry: ``spearman`` fällt, ``geom_iou`` bleibt.

    Der Mittelwertfilter läuft nur über die Geometriepunkte; der Hintergrund geht nicht
    ein, sonst zöge er die Ränder ins Unendliche und verschöbe die Silhouette. Also bleibt
    die Punktmenge exakt dieselbe und nur die Tiefenordnung leidet.
    """
    assert STOERUNGEN[GLAETTUNG].wirkt_auf_spearman == FAELLT
    assert STOERUNGEN[GLAETTUNG].wirkt_auf_iou == BLEIBT

    messung = score_von(GLAETTUNG, 1.0)
    assert messung["geom_iou"] == 1.0
    assert messung["n_soll"] == messung["n_ist"]
    assert abs(messung["spearman"]) < 1.0


@pytest.mark.parametrize("kante", [32, 48])
def test_glaettung_ist_ein_stumpfes_instrument(kante):
    """**Befund, nicht Zusage.** Die Erwartung trifft ein — die Wirkung ist winzig.

    Über die ganze Stärkeskala von 0.0 bis 1.0 (acht Mittelungsdurchgänge) bewegt sich der
    Score um weniger als 0.01, und der Effekt **schrumpft mit wachsender Auflösung**: Die
    Glättung wirkt lokal an der Flügelkante, die Rangordnung aber wird global über alle
    Geometriepunkte gebildet, und die Rampe darunter bleibt unberührt.

    Der Docstring von ``baue_testszene`` sagt, der Flügel liefere „die Kante, an der
    Glättung überhaupt etwas anrichtet". Das stimmt — sie richtet nur fast nichts an. Für
    die Trennschärfe heisst das: Die Zeilen dieser Störung stehen bei jeder Schwelle unter
    0.99 auf der Seite „durchgelassen", und vier von ihnen zählen dabei als
    ``falsch_frei``. Sie sind damit die Obergrenze jeder erreichbaren Trefferquote — wer
    die Kurve deutet, muss das wissen.
    """
    soll = baue_testszene(kante, kante)
    ganz = score_von(GLAETTUNG, 1.0, soll=soll, breite=kante, hoehe=kante)["score"]
    assert ganz < 1.0, "wirkungslos wäre schlimmer als schwach"
    assert ganz > 0.99, (
        f"{kante}×{kante}: Glättung bei voller Stärke lässt den Score bei {ganz:.4f}. "
        f"Sollte diese Störung je wirklich beissen, ist dieser Test die Stelle, an der "
        f"der Befund aus der Auswertung verschwindet."
    )


def test_zusatzkoerper_senkt_den_iou_und_laesst_die_rangkorrelation_in_ruhe():
    """Erwartung der Registry: ``geom_iou`` fällt, ``spearman`` bleibt.

    Die klassische Halluzination: ein Baukörper an einer Stelle, wo Himmel sein müsste.
    Er sitzt ausserhalb der Soll-Silhouette, also unberührt von der Rangkorrelation — der
    Anteil, der ihn fängt, ist allein die Silhouettendeckung. Genau dafür steht ``geom_iou``
    überhaupt im Score.
    """
    assert STOERUNGEN[ZUSATZKOERPER].wirkt_auf_spearman == BLEIBT
    assert STOERUNGEN[ZUSATZKOERPER].wirkt_auf_iou == FAELLT

    messung = score_von(ZUSATZKOERPER, 0.5)
    assert messung["spearman"] == 1.0
    assert messung["geom_iou"] < 1.0
    assert messung["n_ist"] > messung["n_soll"]
    assert messung["n_gemeinsam"] == messung["n_soll"], "der Bau selbst bleibt unberührt"


def test_der_zusatzkoerper_haelt_jetzt_ein_was_seine_staerke_verspricht():
    """**Die Beschriftung der Stärkeachse muss stimmen, sonst deutet die Kurve daneben.**

    Vorgeschichte, 18.08.2026: Der Quelltext sagte „staerke 1.0 = ein Zusatzkörper von der
    Fläche des Baus selbst" und baute ein Quadrat dieser Fläche in die obere linke Ecke —
    aber gesetzt wurde nur, wo Hintergrund ist, und das Quadrat überlappte den Bau.
    Tatsächlich entstanden **40 %** der angekündigten Fläche. Die Rechnung war harmlos, die
    Achse falsch beschriftet, und die Auswertung hat der Beschriftung geglaubt.

    Seither wächst das Quadrat, bis die **tatsächlich gesetzte** Punktzahl das Ziel
    erreicht. Die Toleranz nach oben ist nötig, weil in ganzen Bildpunkten gerastert wird:
    Der letzte Ring, der die Zahl über das Ziel bringt, wird ganz gesetzt.
    """
    bau = len(geometriepunkte(SOLL))
    voll = stoere(SOLL, ZUSATZKOERPER, 1.0, breite=BREITE, hoehe=HOEHE)
    gesetzt = len(geometriepunkte(voll)) - bau
    assert 0.95 * bau <= gesetzt <= 1.3 * bau, (
        f"angekündigt waren {bau} Punkte, gesetzt wurden {gesetzt}"
    )
    halb = stoere(SOLL, ZUSATZKOERPER, 0.5, breite=BREITE, hoehe=HOEHE)
    halb_gesetzt = len(geometriepunkte(halb)) - bau
    assert 0.45 * bau <= halb_gesetzt <= 0.8 * bau, (
        f"halbe Stärke sollte rund die halbe Fläche setzen, waren {halb_gesetzt}"
    )
    assert halb_gesetzt < gesetzt, "wenigstens wächst er mit der Stärke"


def test_zusatzkoerper_braucht_hintergrund_und_sagt_es_sonst():
    """Auf einer randvollen Karte gibt es keinen Himmel, in den ein Körper halluziniert
    werden könnte. Der Fall wird benannt statt still übergangen — eine Störung, die
    nichts stört, sähe in der Tabelle aus wie eine robuste Metrik."""
    randvoll = [10.0 + 0.001 * i for i in range(BREITE * HOEHE)]
    with pytest.raises(StudienError, match="Hintergrund"):
        stoere(randvoll, ZUSATZKOERPER, 1.0, breite=BREITE, hoehe=HOEHE)


@pytest.mark.parametrize("art", sorted(MESSENDE))
@pytest.mark.parametrize("staerke", GESTOERTE_STAERKEN)
def test_jede_messende_stoerung_haelt_ihre_registry_erwartung(art, staerke):
    """Dasselbe noch einmal über das ganze Gitter — direkt gerechnet, nicht aus dem
    Studienergebnis abgelesen.

    ``erwartung_erfuellt`` prüft dieselbe Frage; würde nur das geprüft, prüfte der Test
    die Studie gegen sich selbst. Hier stehen die Messwerte gegen die Registry.
    """
    stoerung = STOERUNGEN[art]
    messung = score_von(art, staerke)
    if messung["score"] is None:            # nicht messbar ist kein Gegenbeweis
        pytest.skip("keine Messung, kein Urteil")

    if stoerung.wirkt_auf_spearman == FAELLT:
        assert abs(messung["spearman"]) < 1.0
    else:
        assert abs(messung["spearman"]) == pytest.approx(1.0, abs=1e-6)

    if stoerung.wirkt_auf_iou == FAELLT:
        assert messung["geom_iou"] < 1.0
    else:
        assert messung["geom_iou"] == pytest.approx(1.0, abs=1e-6)


@pytest.mark.parametrize("art", sorted(MESSENDE))
def test_groessere_staerke_erhoeht_den_score_nicht(art):
    """Monotonie in der Stärke — die Voraussetzung dafür, dass eine Kurve eine Kurve ist.

    Geprüft wird „nicht grösser", nicht „echt kleiner": Die Stärkeachse der räumlichen
    Störungen ist grob gerastert (``round(staerke * k)``), 0.2 und 0.3 ergeben dort
    denselben Bildpunktversatz und damit denselben Score. Auf „echt kleiner" zu bestehen
    hiesse, ein Raster für einen Fehler zu halten.

    Die Kontrollen sind ausgenommen: Sie sollen den Score gerade **nicht** senken.
    """
    scores = [score_von(art, s)["score"] for s in VORGABE_STAERKEN]
    for vorher, nachher, s_vor, s_nach in zip(scores, scores[1:],
                                              VORGABE_STAERKEN, VORGABE_STAERKEN[1:]):
        if vorher is None or nachher is None:
            continue
        assert nachher <= vorher + 1e-12, (
            f"{art}: Stärke {s_nach} liefert {nachher:.6f}, mehr als Stärke {s_vor} "
            f"({vorher:.6f}) — die Störung wird bei mehr Stärke milder."
        )


@pytest.mark.parametrize("art", [SILHOUETTE_WACHSEN, SILHOUETTE_SCHRUMPFEN, VERSCHIEBUNG])
def test_staerkeachse_ist_bei_den_raeumlichen_stoerungen_grob_gerastert(art):
    """**Befund über die Studie, keine Zusage des Moduls.**

    Die räumlichen Störungen rechnen ihre Stärke in ganze Bildpunkte um
    (``round(staerke * min(breite, hoehe) // 8)``). Bei 32×32 ist dieser Faktor 4, und
    0.2 wie 0.3 runden beide auf **einen** Bildpunkt: Die beiden Studienzeilen sind
    punktgleich dieselbe Störung.

    Das ist mehr als Kosmetik. ``trennschaerfe_kurve`` schneidet bei ``grenzstaerke=0.2``
    zwischen „treu" und „untreu" — genau mitten durch dieses Plateau. Zwei Zeilen mit
    **identischer Messung** stehen damit auf verschiedenen Seiten der Grenze, und keine
    Schwelle der Welt kann sie trennen. Ein Teil der ``falsch_frei``-Zählungen ist deshalb
    kein Befund über die Metrik, sondern ein Artefakt des Stärkerasters.

    Wird die Stärkeachse je feiner aufgelöst, muss dieser Test fallen — und dann gehört
    die Trennschärfe neu gedeutet.
    """
    assert (stoere(SOLL, art, 0.2, breite=BREITE, hoehe=HOEHE)
            == stoere(SOLL, art, 0.3, breite=BREITE, hoehe=HOEHE))


# --------------------------------------------------------------------------------------
# C · Die zwei Kontrollen — der wissenschaftliche Kern
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("kante", [16, 32, 48, 64])
@pytest.mark.parametrize("staerke", [0.1, 0.3, 0.5, 1.0, 5.0])
def test_kontrolle_monoton_laesst_den_score_bei_eins(kante, staerke):
    """**Die einzige Prüfung der Studie, die widerlegen kann statt nur zu beschreiben.**

    Massstab, Nullpunkt und Potenz sind streng monoton wachsend, also rangerhaltend. Ein
    rangbasiertes Verfahren **muss** das unverändert überstehen; fällt der Score, ist nicht
    die Schwelle falsch, sondern die Metrik — sie hinge dann am Zahlenwert statt an der
    Reihenfolge.

    Die Toleranz ist die des Moduls selbst (``_kontrollen`` prüft ``> 1.0 - 1e-6``) und
    nicht Bequemlichkeit: Bei 32×32 fallen zwei benachbarte Tiefenwerte nach der Potenz
    auf dieselbe Fliesskommazahl zusammen, was die Rangkorrelation um 5e-8 drückt. Der
    eigene Test dazu steht direkt darunter.
    """
    soll = baue_testszene(kante, kante)
    messung = score_von(MONOTON, staerke, soll=soll, breite=kante, hoehe=kante)
    assert messung["geom_iou"] == 1.0
    assert messung["spearman"] == pytest.approx(1.0, abs=1e-6)
    assert messung["score"] == pytest.approx(1.0, abs=1e-6)


@pytest.mark.parametrize("kante", [16, 48, 64])
@pytest.mark.parametrize("staerke", [0.1, 1.0, 5.0])
def test_monoton_ist_auf_bindungsfreien_szenen_exakt_eins(kante, staerke):
    """Wo die Szene keine zwei gleichen Werte trägt, ist der Score **bitgenau** 1.0.

    Das trennt die Ursache sauber: Die 5e-8 bei 32×32 kommen aus der
    Fliesskomma-Auflösung der Szene, nicht aus der Metrik. Auf einer bindungsfreien Karte
    bleibt kein Rest.
    """
    soll = baue_testszene(kante, kante)
    assert score_von(MONOTON, staerke, soll=soll, breite=kante, hoehe=kante)["score"] == 1.0


def test_die_monotone_umrechnung_ist_wirklich_streng_monoton_wachsend():
    """Ohne diesen Test prüfte die Kontrolle nur, dass zwei kaputte Dinge zusammenpassen.

    Nach Soll-Tiefe sortiert müssen die Ist-Tiefen aufsteigen — sonst wäre die
    „Umrechnung" gar nicht rangerhaltend, und ein Score von 1.0 bewiese nicht die
    Rangtreue der Metrik, sondern nur, dass beide Seiten denselben Fehler machen.

    Geprüft auf der bindungsfreien Szene, wo „aufsteigend" ohne Einschränkung gilt.
    """
    ist = stoere(SOLL_GROSS, MONOTON, 1.0, breite=GROSS, hoehe=GROSS)
    nach_soll = sorted(geometriepunkte(SOLL_GROSS), key=lambda i: SOLL_GROSS[i])
    folge = [ist[i] for i in nach_soll]
    assert all(a < b for a, b in zip(folge, folge[1:])), (
        "die Umrechnung ist nicht streng monoton wachsend — die Kontrolle prüfte dann "
        "nichts."
    )
    # Und sie ist wirklich eine Umrechnung, keine Kopie: andere Werte, andere Grössenordnung.
    assert min(folge) < 0.0 < abs(min(geometriewerte(SOLL_GROSS)))


def test_monotone_umrechnung_kann_werte_nur_zusammenlegen_nie_aufspalten():
    """Der Rest bei 32×32, benannt statt weggerundet.

    Eine deterministische Funktion kann gleiche Werte nie verschieden machen — sie kann
    aber verschiedene Werte auf dieselbe Fliesskommazahl legen. Genau das passiert bei
    32×32 an zwei Stellen und drückt die Rangkorrelation um 5e-8 unter 1.0. Der Befund ist
    eine Eigenschaft der Zahlendarstellung, keine der Metrik; er bleibt weit unter jeder
    Schwelle, die die Studie deutet.
    """
    ist = stoere(SOLL, MONOTON, 1.0, breite=BREITE, hoehe=HOEHE)
    punkte = geometriepunkte(SOLL)
    assert len({ist[i] for i in punkte}) <= len({SOLL[i] for i in punkte})

    nach_soll = sorted(punkte, key=lambda i: SOLL[i])
    folge = [ist[i] for i in nach_soll]
    assert all(a <= b for a, b in zip(folge, folge[1:])), "aufsteigend bleibt es trotzdem"


@pytest.mark.parametrize("staerke", GESTOERTE_STAERKEN)
def test_kontrolle_tiefenumkehr_bleibt_fuer_den_score_unsichtbar(staerke):
    """Die bekannte Grenze der Metrik, in Zahlen statt in einem Nebensatz.

    Nah und fern werden vertauscht: Die Rangkorrelation ist danach **exakt −1.0** — eine
    perfekte Umkehrung, keine Verschlechterung. Der Score wertet ``abs(spearman)``, weil
    invertierte Tiefe (Disparität) eine verbreitete Konvention ist, und bleibt darum bei
    1.0. Er **kann** diesen Fall nicht sehen.

    Das ist kein Fehler, sondern eine Arbeitsteilung: Die Polarität muss ausserhalb der
    Metrik festgestellt werden. Festgehalten wird beides — der Score *und* das Vorzeichen,
    an dem der Fall überhaupt erkennbar ist.
    """
    messung = score_von(TIEFENUMKEHR, staerke)
    assert messung["spearman"] == -1.0
    assert messung["geom_iou"] == 1.0
    assert messung["score"] == pytest.approx(1.0)
    assert any("negativ" in w for w in messung["warnungen"]), (
        "das Vorzeichen ist der einzige Hinweis, den es gibt — er muss im Klartext stehen"
    )


def test_studienlauf_meldet_beide_kontrollen_getrennt_von_den_kurven():
    """Die Kontrollen beantworten eine andere Frage als die Kurven: nicht „wo liegt die
    Grenze", sondern „taugt das Verfahren". Darum stehen sie im Ergebnis an eigener
    Stelle — und darum trägt jede von ihnen ihre Frage und ihre Deutung im Klartext mit."""
    kontrollen = ERGEBNIS["kontrollen"]
    assert set(kontrollen) == {"rangerhaltung", "polaritaet_unsichtbar"}

    rang = kontrollen["rangerhaltung"]
    assert rang["bestanden"] is True
    assert rang["kleinster_score"] > 1.0 - 1e-6
    assert rang["frage"] and rang["bedeutung_bei_fehlschlag"]

    polaritaet = kontrollen["polaritaet_unsichtbar"]
    assert polaritaet["wie_erwartet_blind"] is True
    assert polaritaet["kleinster_score"] == pytest.approx(1.0)
    assert polaritaet["frage"] and polaritaet["was_das_heisst"]


# --------------------------------------------------------------------------------------
# D · Determinismus — eine Studie, die sich nicht wiederholen lässt, ist keine
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("art", sorted(STOERUNGEN))
def test_gleicher_seed_liefert_punktgleich_dasselbe(art):
    """Punktgleich, nicht „gleicher Score": Zwei Karten mit gleicher Tiefenordnung und
    verschiedenen Werten hätten denselben Score und wären trotzdem nicht dasselbe
    Ergebnis."""
    erste = stoere(SOLL, art, 0.7, breite=BREITE, hoehe=HOEHE, seed=20260818)
    zweite = stoere(SOLL, art, 0.7, breite=BREITE, hoehe=HOEHE, seed=20260818)
    assert erste == zweite


def test_verschiedener_seed_aendert_das_rauschen():
    """Die Gegenprobe: Ohne sie wäre auch eine Störung „reproduzierbar", die den Startwert
    schlicht ignoriert. ``rauschen`` ist die einzige Art, die überhaupt würfelt."""
    assert (stoere(SOLL, RAUSCHEN, 0.5, breite=BREITE, hoehe=HOEHE, seed=1)
            != stoere(SOLL, RAUSCHEN, 0.5, breite=BREITE, hoehe=HOEHE, seed=2))


def test_der_ganze_studienlauf_ist_wiederholbar():
    """Zweimal derselbe Aufruf, zweimal dasselbe Ergebnis — bis auf die letzte Stelle.

    Der Seed steht im Rückgabewert, damit ein Ergebnis in der Arbeit nachgerechnet werden
    kann, ohne dass jemand den Aufruf rekonstruieren muss.
    """
    wiederholt = studienlauf(SOLL, breite=BREITE, hoehe=HOEHE,
                             szene="quader-mit-fluegel-32")
    assert wiederholt == ERGEBNIS
    assert ERGEBNIS["seed"] == 0


# --------------------------------------------------------------------------------------
# E · studienlauf und trennschaerfe_kurve
# --------------------------------------------------------------------------------------

def test_studienlauf_traegt_die_zugesagten_schluessel():
    """Der Rückgabewert ist eine Zusage des Docstrings, kein Zufallsprodukt — er wandert
    unverändert in ``auftrag.baue_ergebnis(messwerte=…)``."""
    assert set(ERGEBNIS) == {"szene", "breite", "hoehe", "schwelle", "seed", "methode",
                             "herkunft", "geometrieanteil", "n_geometrie", "n_punkte",
                             "vorbehalte", "zeilen", "kontrollen", "warnungen"}
    assert ERGEBNIS["szene"] == "quader-mit-fluegel-32"
    assert (ERGEBNIS["breite"], ERGEBNIS["hoehe"]) == (BREITE, HOEHE)
    assert ERGEBNIS["schwelle"] == geometrie_qa.SCHWELLE_GEOMETRIE
    assert ERGEBNIS["methode"] == geometrie_qa.METHODE, (
        "die Szene nennt jedes Ergebnis mit — und den Rechenweg, an dem es hängt"
    )


def test_ohne_gerechnete_zeile_steht_kein_rechenweg_da():
    """Der Rechenweg wird vom Urteil **abgelesen**, nicht danebengeschrieben.

    Bis zum 26.08.2026 stand hier fest ``geometrie_qa.METHODE``. Das war richtig, solange
    die Studie ungerichtet rechnet — aber richtig aus Zufall, und dieselbe Stelle war am
    selben Tag in ``kosmo_szene`` gefunden worden, wo sie falsch war.

    **Dieser Test ist die Probe darauf, und er war zuerst nicht da:** Eine Mutationsprobe
    (M5, 26.08.2026) hat die feste Angabe wieder eingesetzt, und nichts wurde rot — beide
    Fassungen liefern dieselbe Zeichenkette, solange gerechnet wird. Nur der leere Lauf
    trennt sie: Ohne eine einzige Zeile gibt es keinen Rechenweg, und eine Angabe darüber
    wäre eine Auskunft über etwas, das niemand getan hat.
    """
    leer = studienlauf(SOLL, breite=BREITE, hoehe=HOEHE, arten=[], staerken=[])

    assert leer["zeilen"] == []
    assert leer["methode"] is None
    assert studienlauf(SOLL, breite=BREITE, hoehe=HOEHE, arten=[RAUSCHEN],
                       staerken=[0.0])["methode"] == geometrie_qa.METHODE, (
        "die Gegenprobe: sobald gerechnet wird, steht der Weg da — und zwar der, den "
        "`geometrie_gate` wirklich gegangen ist"
    )


def test_jede_zeile_traegt_die_zugesagten_schluessel():
    """Eine Zeile ohne ``erwartung_erfuellt`` wäre eine Tabelle ohne Vorhersage — und
    damit genau die Sorte Kurve, gegen die diese Studie gebaut ist."""
    zugesagt = {"art", "staerke", "score", "spearman", "geom_iou", "bestanden",
                "erwartung_erfuellt"}
    for zeile in ERGEBNIS["zeilen"]:
        assert zugesagt <= set(zeile)
        assert set(zeile) == zugesagt | {"n_gemeinsam", "ist_kontrolle", "ist_abdruck"}
        assert isinstance(zeile["art"], str) and zeile["art"] in STOERUNGEN
        assert isinstance(zeile["staerke"], float)
        assert isinstance(zeile["bestanden"], bool)
        assert zeile["ist_kontrolle"] is STOERUNGEN[zeile["art"]].ist_kontrolle


def test_der_lauf_deckt_das_ganze_gitter_ab():
    """Störungsart × Stärke, vollständig und ohne Doppelung. Eine fehlende Zelle fiele in
    der Kurve nicht auf — sie sähe aus wie eine Stelle, an der nichts passiert."""
    gitter = [(z["art"], z["staerke"]) for z in ERGEBNIS["zeilen"]]
    erwartet = [(art, float(s)) for art in STOERUNGEN for s in VORGABE_STAERKEN]
    assert sorted(gitter) == sorted(erwartet)
    assert len(gitter) == len(set(gitter))


def test_das_ergebnis_traegt_nur_zahlen_wahrheitswerte_und_text():
    """**Regel 3, rekursiv geprüft.** Kein Bild, keine Tiefenkarte, keine echten Daten.

    Das Ergebnis ist dafür gebaut, im Repo zu landen und in der Arbeit zitiert zu werden.
    Ein später hinzugefügtes Feld, das eine Karte mitschleppt, brächte hunderttausend
    Zahlen mit — und im Betrieb wäre das eine Tiefenkarte aus einem echten Projekt. Die
    Prüfung läuft darum über den ganzen Baum und nicht nur über die oberste Ebene.
    """
    def pruefe(wert, pfad: str) -> None:
        if wert is None or isinstance(wert, (bool, int, float, str)):
            return
        if isinstance(wert, dict):
            for schluessel, unterwert in wert.items():
                assert isinstance(schluessel, str), f"{pfad}: Schlüssel {schluessel!r}"
                pruefe(unterwert, f"{pfad}.{schluessel}")
            return
        if isinstance(wert, list):
            assert len(wert) < len(SOLL), (
                f"{pfad}: {len(wert)} Einträge — so lang wie eine Tiefenkarte. Karten "
                f"gehören nicht ins Ergebnis (Regel 3)."
            )
            for i, unterwert in enumerate(wert):
                pruefe(unterwert, f"{pfad}[{i}]")
            return
        pytest.fail(f"{pfad}: {type(wert).__name__} — nur Zahlen, Wahrheitswerte und Text")

    pruefe(ERGEBNIS, "ergebnis")


def test_das_ergebnis_laesst_sich_als_json_schreiben():
    """Die praktische Probe aufs Exempel: Was sich nicht serialisieren lässt, kann auch
    nicht in eine Ergebnisdatei — und wäre damit nach der Sitzung weg."""
    wieder_gelesen = json.loads(json.dumps(ERGEBNIS))
    assert wieder_gelesen["zeilen"][0]["art"] == ERGEBNIS["zeilen"][0]["art"]
    assert len(wieder_gelesen["zeilen"]) == len(ERGEBNIS["zeilen"])


def test_die_nullprobe_traegt_keine_erwartung():
    """Bei Stärke 0 gibt es nichts zu erwarten. ``None`` statt ``True`` — sonst zählte die
    Studie ihre eigenen Nullproben als bestandene Vorhersagen und sähe besser aus, als sie
    ist."""
    nullproben = [z for z in ERGEBNIS["zeilen"] if z["staerke"] == 0.0]
    assert len(nullproben) == len(STOERUNGEN)
    for zeile in nullproben:
        assert zeile["erwartung_erfuellt"] is None
        assert zeile["score"] == pytest.approx(1.0)


def test_alle_erwartungen_der_registry_treffen_ein():
    """Die Sammelaussage — nachdem die Einzelfälle oben benannt geprüft sind.

    Ein ``False`` hier wäre ein Befund über die Metrik und keine Panne: eine Störung, die
    einen Score-Anteil trifft, den sie laut Registry nicht treffen kann.
    """
    verfehlt = [(z["art"], z["staerke"]) for z in ERGEBNIS["zeilen"]
                if z["erwartung_erfuellt"] is False]
    assert verfehlt == []
    assert any(z["erwartung_erfuellt"] is True for z in ERGEBNIS["zeilen"])


def test_ohne_nullprobe_ist_keine_erwartung_entscheidbar():
    """Ohne Vergleichspunkt kein Urteil — dieselbe Haltung wie beim nicht messbaren Score.

    Wer ``staerken`` ohne die 0.0 übergibt, bekommt Messwerte, aber keine Vorhersage. Ein
    stilles ``True`` wäre hier die gefährlichere Antwort.
    """
    ohne = studienlauf(SOLL, breite=BREITE, hoehe=HOEHE, arten=[RAUSCHEN],
                       staerken=(0.5, 1.0))
    assert all(z["erwartung_erfuellt"] is None for z in ohne["zeilen"])
    assert all(z["score"] is not None for z in ohne["zeilen"])


def test_nicht_messbare_zeilen_stehen_in_den_warnungen():
    """Ein ``score`` von ``None`` ist kein schlechter Wert, sondern **kein Wert**.

    Auf der 8×8-Szene fällt die gemeinsame Silhouette nach dem Abtragen bzw. Verschieben
    unter ``MIN_GEMEINSAME_PUNKTE``. Die Zeilen bleiben in der Tabelle stehen — sichtbar,
    mit Begründung — und zählen nirgends mit.
    """
    unmessbar = [z for z in ERGEBNIS_KLEIN["zeilen"] if z["score"] is None]
    assert unmessbar, "die kleine Szene sollte nicht messbare Zeilen erzeugen"
    assert len(ERGEBNIS_KLEIN["warnungen"]) == len(unmessbar)
    assert all(z["bestanden"] is False for z in unmessbar)
    assert all(z["erwartung_erfuellt"] is None for z in unmessbar)
    assert ERGEBNIS["warnungen"] == [], "auf 32×32 ist jede Zeile messbar"


def test_die_kurve_laesst_kontrollen_und_nicht_messbare_zeilen_weg():
    """Beide Sorten würden die Trennschärfe verfälschen, jede auf ihre Art.

    Die Kontrollen sollen den Score **nicht** senken — sie stünden bei jeder Schwelle als
    „durchgelassen" da und schönten die Quote. Nicht messbare Zeilen wiederum wären ein
    Urteil aus Mangel an Messung. Und die Nullproben sind keine Störung.
    """
    auswertbar = [z for z in ERGEBNIS_KLEIN["zeilen"]
                  if not z["ist_kontrolle"] and z["score"] is not None and z["staerke"] > 0]
    kurve = trennschaerfe_kurve(ERGEBNIS_KLEIN)
    assert kurve["n_roh"] == len(auswertbar)
    assert kurve["punkte"][0]["n"] < len(ERGEBNIS_KLEIN["zeilen"])

    voll = trennschaerfe_kurve(ERGEBNIS)
    assert voll["n_roh"] == len(MESSENDE) * len(GESTOERTE_STAERKEN)


def test_punktgleiche_wiederholungen_werden_entdoppelt_statt_gezaehlt():
    """**Der Befund, der die erste Auswertung dieser Studie verfälscht hat.**

    Die räumlichen Störungen rechnen in ganzen Bildpunkten. Auf 64² ergeben Stärke 0,2
    und 0,3 beide zwei Bildpunkte — die Ist-Karten sind dann nicht ähnlich, sondern
    **punktgleich**, mit demselben Score.

    Verheerend wird das erst dadurch, dass `grenzstaerke` genau dazwischen liegt: Zwei
    Zeilen mit derselben Messung stehen auf verschiedenen Seiten der Grenze. Keine
    Schwelle kann sie trennen; jede zählt zwangsläufig einen Fehler, und der landete in
    der ersten Auswertung als `falsch_frei` — also als Aussage über die Metrik, wo eine
    Aussage über das Stärkeraster stand.

    Der Test hält beides fest: dass entdoppelt wird, **und** dass gesagt wird, wie oft.
    Eine stillschweigende Bereinigung wäre nur die zweite Art, dieselbe Zahl zu erfinden.
    """
    kurve = trennschaerfe_kurve(ERGEBNIS)
    assert kurve["n_ausgewertet"] + len(kurve["entdoppelt"]) == kurve["n_roh"]
    assert kurve["punkte"][0]["n"] == kurve["n_ausgewertet"]

    for verworfen in kurve["entdoppelt"]:
        gleich = [z for z in ERGEBNIS["zeilen"]
                  if z["art"] == verworfen["art"]
                  and z["staerke"] == verworfen["gleich_wie_staerke"]]
        assert len(gleich) == 1
        assert gleich[0]["score"] == verworfen["score"], (
            "entdoppelt wurde etwas, das gar nicht gleich war"
        )


def test_ohne_auswertbare_zeile_gibt_es_keine_kurve():
    """Ein Lauf über nur eine Kontrolle hat nichts zu trennen. Ein Fehler statt einer
    leeren Kurve: Eine Trefferquote über null Zeilen wäre eine Zahl ohne Gegenstand."""
    nur_kontrolle = studienlauf(SOLL, breite=BREITE, hoehe=HOEHE, arten=[MONOTON])
    with pytest.raises(StudienError, match="Keine auswertbare Zeile"):
        trennschaerfe_kurve(nur_kontrolle)


def test_die_kurve_zaehlt_jede_zeile_genau_einmal():
    """Die vier Fälle sind eine Aufteilung, keine Auswahl: richtig frei, falsch frei,
    richtig gesperrt, falsch gesperrt ergeben zusammen ``n``. Ginge eine Zeile verloren,
    wäre die Trefferquote stillschweigend zu gut."""
    for punkt in trennschaerfe_kurve(ERGEBNIS)["punkte"]:
        summe = (punkt["richtig_frei"] + punkt["falsch_frei"]
                 + punkt["richtig_gesperrt"] + punkt["falsch_gesperrt"])
        assert summe == punkt["n"]
        assert punkt["treffer"] == pytest.approx(
            (punkt["richtig_frei"] + punkt["richtig_gesperrt"]) / punkt["n"])
        assert 0.0 <= punkt["treffer"] <= 1.0


def test_hoehere_schwelle_sperrt_mehr():
    """Die Kurve muss in eine Richtung laufen, sonst ist sie keine: Wer die Latte höher
    legt, lässt nicht mehr durch."""
    punkte = trennschaerfe_kurve(ERGEBNIS)["punkte"]
    frei = [p["richtig_frei"] + p["falsch_frei"] for p in punkte]
    assert punkte == sorted(punkte, key=lambda p: p["schwelle"])
    assert all(b <= a for a, b in zip(frei, frei[1:]))


def test_trennschaerfe_ist_genau_ein_punkt_der_kurve():
    """Eine Schwelle einzeln zu prüfen darf nichts anderes heissen als sie in der Kurve
    nachzuschlagen — sonst existierten zwei Rechenwege für dieselbe Zahl."""
    einzeln = trennschaerfe(ERGEBNIS, 0.65)
    aus_kurve = trennschaerfe_kurve(ERGEBNIS, (0.65,))["punkte"][0]
    assert einzeln == aus_kurve
    assert einzeln["schwelle"] == 0.65


def test_die_grenzstaerke_steht_im_ergebnis_und_verschiebt_das_urteil():
    """``grenzstaerke`` ist eine **Setzung, keine Messung** — was „noch treu" heisst, ist
    hier durch die Störungsstärke definiert und nicht durch ein menschliches Urteil.

    Genau darum steht sie im Rückgabewert: Wer sie verschiebt, verschiebt das Ergebnis,
    und das soll man dem Ergebnis ansehen.
    """
    mild = trennschaerfe_kurve(ERGEBNIS, (0.65,), grenzstaerke=0.7)
    streng = trennschaerfe_kurve(ERGEBNIS, (0.65,), grenzstaerke=0.1)
    assert mild["grenzstaerke"] == 0.7 and streng["grenzstaerke"] == 0.1
    assert mild["punkte"][0]["richtig_frei"] > streng["punkte"][0]["richtig_frei"]


def zeile(art: str, staerke: float, score, *, kontrolle: bool = False) -> dict:
    """Eine Studienzeile von Hand — für Fälle, die sich mit der echten Szene nicht
    herstellen lassen, ohne die Aussage im Rauschen zu verlieren."""
    return {"art": art, "staerke": staerke, "score": score, "spearman": 1.0,
            "geom_iou": 1.0, "n_gemeinsam": 100, "bestanden": True,
            "ist_kontrolle": kontrolle, "erwartung_erfuellt": None}


def test_beste_nimmt_bei_gleichstand_die_kleinste_schwelle():
    """Bei gleicher Güte ist die mildere Wahl die richtige: Eine niedrigere Schwelle
    sperrt weniger, und jede Sperre kostet einen weiteren Render.

    Der Fall ist von Hand gebaut, weil er auf einen exakten Gleichstand angewiesen ist:
    Ein treuer Fall bei 1.0, ein untreuer bei 0.5 — jede Schwelle zwischen den beiden
    trennt perfekt. Gewählt werden muss die kleinste davon.
    """
    gebaut = {"zeilen": [zeile(RAUSCHEN, 0.1, 1.0), zeile(RAUSCHEN, 1.0, 0.5)]}
    kurve = trennschaerfe_kurve(gebaut, (0.6, 0.7, 0.8), grenzstaerke=0.2)
    assert [p["treffer"] for p in kurve["punkte"]] == [1.0, 1.0, 1.0], "kein Gleichstand"
    assert kurve["beste"]["schwelle"] == 0.6


def test_beste_nimmt_die_hoechste_trefferquote_vor_der_milde():
    """Die Milde ist der Stichentscheid, nicht das Kriterium. Sonst gewönne immer die
    kleinste Schwelle — und die lässt alles durch."""
    gebaut = {"zeilen": [zeile(RAUSCHEN, 0.1, 1.0), zeile(RAUSCHEN, 1.0, 0.5)]}
    kurve = trennschaerfe_kurve(gebaut, (0.3, 0.7), grenzstaerke=0.2)
    assert kurve["beste"]["schwelle"] == 0.7
    assert kurve["beste"]["treffer"] == 1.0


def test_kontrollzeilen_zaehlen_auch_von_hand_nicht_mit():
    """Dieselbe Aussage wie oben, aber ohne Umweg über die Szene: ``ist_kontrolle`` ist
    das Merkmal, an dem die Auswertung sie aussortiert."""
    gebaut = {"zeilen": [zeile(RAUSCHEN, 1.0, 0.2), zeile(MONOTON, 1.0, 1.0, kontrolle=True)]}
    assert trennschaerfe_kurve(gebaut, (0.5,))["punkte"][0]["n"] == 1


# --------------------------------------------------------------------------------------
# Fehlerfälle — sprechend statt still
# --------------------------------------------------------------------------------------

def test_unbekannte_stoerungsart_ist_ein_fehler():
    """Die Meldung nennt die bekannten Arten. Ein Tippfehler in einer Studienzeile wäre
    sonst eine Zeile, die es nie gab, und niemand vermisste sie."""
    with pytest.raises(StudienError, match="Unbekannte Störung"):
        stoere(SOLL, "silhouette_waschen", 0.5, breite=BREITE, hoehe=HOEHE)


def test_studienlauf_weist_unbekannte_arten_vorab_zurueck():
    """Vorab, nicht nach der halben Rechnung — ein Lauf, der nach zwanzig Zeilen abbricht,
    hinterlässt Zahlen, die niemand deuten kann."""
    with pytest.raises(StudienError, match="Unbekannte Störungsarten"):
        studienlauf(SOLL, breite=BREITE, hoehe=HOEHE, arten=[RAUSCHEN, "nebel"])


@pytest.mark.parametrize("staerke", [-0.1, -1, True, "viel", None])
def test_unbrauchbare_staerke_ist_ein_fehler(staerke):
    """``True`` ist in Python eine 1 — als Störungsstärke ist es immer ein Irrtum, und
    stillschweigend als 1.0 gedeutet ergäbe es die stärkste Störung überhaupt."""
    with pytest.raises(StudienError, match="staerke"):
        stoere(SOLL, RAUSCHEN, staerke, breite=BREITE, hoehe=HOEHE)


@pytest.mark.parametrize("breite, hoehe", [(31, 32), (32, 31), (16, 16), (64, 64)])
def test_falsche_masse_sind_ein_fehler(breite, hoehe):
    """Die räumlichen Störungen brauchen die echten Masse.

    Eine falsche Breite verschöbe jede Zeile gegen die vorige — das Ergebnis sähe aus wie
    eine Störung, wäre aber ein Aufruffehler.
    """
    with pytest.raises(StudienError, match="passt nicht"):
        stoere(SOLL, VERSCHIEBUNG, 0.5, breite=breite, hoehe=hoehe)


def test_falsche_masse_mit_richtigem_produkt_werden_nicht_erkannt():
    """**Befund: Die Massprüfung ist eine Längenprüfung.** Grenze, nicht Fehler.

    Geprüft wird ``breite * hoehe == len(soll)``. Ein vertauschtes oder ganz anderes
    Seitenverhältnis mit demselben Produkt kommt durch — hier ``1024×1`` statt ``32×32``.
    Die Störung läuft dann auf einer Karte, die es nicht gibt: Die Verschiebung schiebt in
    einer einzeiligen Karte alles über den Rand, übrig bleibt eine leere Ist-Karte.

    Immerhin fällt es auf, weil die Zeile danach **nicht messbar** ist und mit Begründung
    in den Warnungen steht — aber es fällt erst dort auf, und nicht am Aufruf. Wer die
    Masse aus einer anderen Quelle bezieht als die Karte, prüft sie besser selbst.
    """
    verrutscht = stoere(SOLL, VERSCHIEBUNG, 0.5, breite=1024, hoehe=1)
    assert geometriepunkte(verrutscht) == []
    assert geometrie_score(SOLL, verrutscht)["score"] is None


def test_soll_karte_ohne_geometrie_ist_ein_fehler():
    """Eine leere Szene ist kein Studienfall. Ohne Geometriepunkt gäbe es nichts zu stören
    — und jede Zeile darüber wäre eine Messung an einem leeren Bild."""
    with pytest.raises(StudienError, match="keinen einzigen Geometriepunkt"):
        stoere([HINTERGRUND_M] * (BREITE * HOEHE), RAUSCHEN, 0.5,
               breite=BREITE, hoehe=HOEHE)


def test_leere_soll_karte_wird_an_den_massen_gefangen():
    """Auch der Extremfall bekommt eine sprechende Meldung statt eines IndexError."""
    with pytest.raises(StudienError):
        stoere([], RAUSCHEN, 0.5, breite=BREITE, hoehe=HOEHE)


# --------------------------------------------------------------------------------------
# Hygiene
# --------------------------------------------------------------------------------------

def test_modul_importiert_nur_stdlib():
    """Regel 4: Die Studie muss überall laufen, auch ohne GPU und ohne schwere Pakete.

    Ein ``import numpy`` wäre hier besonders verführerisch — Mittelwertfilter und
    Rauschen sind genau die Stellen, an denen man danach greift. Der Test ist billig und
    fängt den bequemen Moment ab.
    """
    quelle = (PAKET / "schwellenstudie.py").read_text(encoding="utf-8")
    module: set[str] = set()
    for knoten in ast.walk(ast.parse(quelle)):
        if isinstance(knoten, ast.Import):
            module.update(a.name.split(".")[0] for a in knoten.names)
        elif isinstance(knoten, ast.ImportFrom) and knoten.level == 0 and knoten.module:
            module.add(knoten.module.split(".")[0])
    fremd = sorted(m for m in module if m not in sys.stdlib_module_names and m != "aiimaging")
    assert not fremd, f"schwellenstudie.py importiert {fremd}"


def test_die_registry_ist_vollstaendig_und_widerspruchsfrei():
    """Jede Störungsart hat einen Eintrag, jeder Eintrag eine Vorhersage.

    Eine Störung ohne Erwartung wäre wieder nur eine Kurve — und eine Kontrolle, von der
    beide Anteile fallen dürfen, wäre keine Kontrolle mehr.
    """
    for art, stoerung in STOERUNGEN.items():
        assert stoerung.name == art
        assert stoerung.wirkt_auf_spearman in (FAELLT, BLEIBT)
        assert stoerung.wirkt_auf_iou in (FAELLT, BLEIBT)
        assert stoerung.beschreibung and stoerung.entspricht
        if stoerung.ist_kontrolle:
            assert stoerung.wirkt_auf_spearman == BLEIBT
            assert stoerung.wirkt_auf_iou == BLEIBT
    assert {art for art, s in STOERUNGEN.items() if s.ist_kontrolle} == {MONOTON,
                                                                        TIEFENUMKEHR}
    assert 0.0 in VORGABE_STAERKEN, "ohne Nullprobe ist keine Zeile darunter zu deuten"


# --------------------------------------------------------------------------------------
# H · studie_aus_bericht — die Studie auf echter Geometrie
# --------------------------------------------------------------------------------------
#
# Warum dieser Abschnitt eigene Dateien schreibt statt eine Attrappe zu setzen: Der
# ganze Zweck des Läufers ist der Weg vom Blender-Bericht zur Karte. Eine gefälschte
# `tiefen_aus_report` prüfte genau den Schritt nicht, für den es die Funktion gibt —
# und die Hintergrundmarke `1e10`, um die es hier geht, käme dann aus dem Test statt
# aus der Datei. Die EXR wird darum wirklich geschrieben, mit reiner Standardbibliothek
# (Regel 3: synthetisch und hier erzeugt).

#: Nicht quadratisch, und das ist Absicht: Nur an einer ungleichseitigen Karte fällt
#: auf, wenn Breite und Höhe vertauscht durchgereicht werden.
BERICHT_BREITE, BERICHT_HOEHE = 24, 16

#: Bauwerk im Bericht: sieben Zeilen zu zehn Punkten — 70, also über
#: ``geometrie_qa.MIN_GEMEINSAME_PUNKTE`` (32). Bewusst **nicht** die mittleren
#: Zweidrittel wie in `baue_testszene`: Der Geometrieanteil ist die Grösse, an der
#: `geom_iou` hängt, und ein Läufer, der die Karte des Berichts durch die synthetische
#: ersetzt, muss daran auffallen (0.18 gegen 0.44).
BERICHT_X = range(4, 14)
BERICHT_Y = range(3, 10)


def bericht_karte() -> list[float]:
    """Die Soll-Karte, die in der EXR landen soll — bindungsfrei und mit Hintergrund."""
    karte = [1.0e10] * (BERICHT_BREITE * BERICHT_HOEHE)
    lauf = 0
    for y in BERICHT_Y:
        for x in BERICHT_X:
            # Ungleiche Schrittweite: gleiche Werte machten die Rangkorrelation zu einer
            # Rechnung über Bindungsgruppen, siehe `test_szene_ist_praktisch_bindungsfrei`.
            karte[y * BERICHT_BREITE + x] = 20.0 + lauf * 0.37
            lauf += 1
    return karte


@pytest.fixture
def bericht(tmp_path):
    """Ein Bericht, wie ``seams.glb_zu_multipass`` ihn zurückgibt — mit echter EXR."""
    from test_bildlesen import schreibe_exr

    werte = bericht_karte()
    exr = schreibe_exr(tmp_path / "tiefe_0001.exr", BERICHT_BREITE, BERICHT_HOEHE,
                       {"V": werte})
    return {"status": "ok", "depth_exr": str(exr), "depth_png": None}


@pytest.fixture
def studie(bericht):
    return studie_aus_bericht(bericht, szene="prüfkörper-24x16")


def test_die_studie_steht_auf_der_karte_des_berichts(studie):
    """Der Kern von A3: Masse und Geometrieanteil stammen aus der Datei, nicht aus einer
    Vorgabe.

    Der Geometrieanteil ist hier kein Beiwerk. ``geom_iou`` hängt an ihm — an der
    synthetischen Szene liegt er bei rund 0.44, an unseren echten Szenen zwischen 0.08
    und 0.17. Eine Schwelle, die bei 0.44 kalibriert und bei 0.08 angewandt wird, ist
    nicht dieselbe Schwelle. Der Test rechnet den Anteil **aus der geschriebenen Karte**
    nach statt die Zahl der Studie zu glauben.
    """
    erwartet = len(BERICHT_X) * len(BERICHT_Y)

    assert (studie["breite"], studie["hoehe"]) == (BERICHT_BREITE, BERICHT_HOEHE)
    assert studie["n_punkte"] == BERICHT_BREITE * BERICHT_HOEHE
    assert studie["n_geometrie"] == erwartet
    assert studie["geometrieanteil"] == pytest.approx(
        erwartet / (BERICHT_BREITE * BERICHT_HOEHE))
    assert studie["szene"] == "prüfkörper-24x16"


def test_die_karte_der_synthetischen_szene_haette_einen_anderen_anteil(studie):
    """Gegenprobe zum vorigen Test — sonst wäre er ohne Aussagekraft.

    Er behauptet, der Anteil komme aus dem Bericht. Das ist nur dann eine Behauptung,
    wenn die synthetische Karte einen **anderen** Anteil hätte. Sie hat einen: rund 0.44
    gegen rund 0.17. Ein Läufer, der die Karte des Berichts stillschweigend durch
    ``baue_testszene`` ersetzte, fiele hier auf.
    """
    synthetisch = studienlauf(SOLL, breite=BREITE, hoehe=HOEHE, arten=[RAUSCHEN],
                              staerken=[0.0], szene="synthetisch")

    assert synthetisch["geometrieanteil"] > 0.4
    assert studie["geometrieanteil"] < 0.2


def test_der_echte_hintergrundwert_geht_unveraendert_durch(bericht):
    """Die Vorbedingung von A3, und sie stimmt ohne einen Handgriff.

    ``HINTERGRUND_M`` der Studie ist genau der Wert, den Cycles in die EXR schreibt.
    Wäre er es nicht, hielte die Studie den Himmel für Bauwerk, der Geometrieanteil
    spränge auf 1.0 und jede Zeile darunter wäre wertlos — ein Fehler, der ohne diesen
    Test als plausible Zahl durchginge.
    """
    from aiimaging import bildlesen

    assert HINTERGRUND_M == 1.0e10
    soll, _, _ = bildlesen.tiefen_aus_report(bericht)
    assert max(soll) == pytest.approx(HINTERGRUND_M, rel=1e-6)

    studie = studie_aus_bericht(bericht, szene="hintergrund", arten=[RAUSCHEN],
                                staerken=[0.0])
    assert studie["n_geometrie"] == len(BERICHT_X) * len(BERICHT_Y)
    assert studie["n_geometrie"] < studie["n_punkte"], (
        "ohne Hintergrund gäbe es keine Silhouette, und `geom_iou` misst nichts"
    )


def test_die_nullprobe_ergibt_auf_echter_geometrie_genau_eins(studie):
    """Stärke 0.0 muss den Score 1.000 ergeben — auf jeder Szene.

    Tut sie es nicht, misst der Läufer etwas anderes als gedacht, und alles Weitere ist
    wertlos. Das ist die erste Prüfung jedes Studienlaufs und nicht verhandelbar.
    """
    nullen = [z for z in studie["zeilen"] if z["staerke"] == 0.0]

    assert len(nullen) == len(STOERUNGEN)
    for z in nullen:
        assert z["score"] == pytest.approx(1.0, abs=1e-9), f"{z['art']} bei Stärke 0"


def test_die_beiden_kontrollen_halten_auch_auf_echter_geometrie(studie):
    """Rangerhaltung muss halten, Polaritätsblindheit muss bleiben.

    Beide sind Eigenschaften der **Metrik**, nicht der Szene — sie dürfen sich beim
    Wechsel von der synthetischen zur echten Karte nicht ändern. Fällt die erste, ist
    nicht die Schwelle falsch, sondern das Verfahren.
    """
    kontrollen = studie["kontrollen"]

    assert kontrollen["rangerhaltung"]["bestanden"] is True
    assert kontrollen["polaritaet_unsichtbar"]["wie_erwartet_blind"] is True


def test_der_vorbehalt_reist_in_jedem_ergebnis_mit(studie):
    """Was die Studie **nicht** abdeckt, steht in den Zahlen und nicht nur im Dokument.

    In der Studie tragen beide Karten eine Hintergrundmarke — der Fehler des monokularen
    Schätzers aus ``docs/DECKELSTUDIE_2026-08-26.md`` kommt hier gar nicht vor. Das ist
    richtig so; eine Schwelle lässt sich nur unabhängig vom Schätzerfehler kalibrieren.
    Aber es muss dastehen, sonst liest die Studie später jemand, als decke sie die ganze
    Kette ab.
    """
    synthetisch = studienlauf(SOLL, breite=BREITE, hoehe=HOEHE, arten=[RAUSCHEN],
                              staerken=[0.0])

    assert VORBEHALT_NICHT_DIE_KETTE in studie["vorbehalte"]
    assert VORBEHALT_NICHT_DIE_KETTE in synthetisch["vorbehalte"]
    assert "Metrik, nicht die Kette" in VORBEHALT_NICHT_DIE_KETTE


def test_die_herkunft_unterscheidet_echte_von_synthetischer_grundlage(studie):
    """Einem Zahlenblock sieht man nicht an, worauf er steht — hier steht es dabei."""
    synthetisch = studienlauf(SOLL, breite=BREITE, hoehe=HOEHE, arten=[RAUSCHEN],
                              staerken=[0.0])

    assert studie["herkunft"] == HERKUNFT_BERICHT
    assert synthetisch["herkunft"] == HERKUNFT_KARTE
    assert HERKUNFT_BERICHT != HERKUNFT_KARTE


def test_die_masse_des_berichts_werden_nicht_vertauscht(bericht):
    """Mutationsprobe: Breite und Höhe getauscht — die Nachbarschaftsstörungen kippen.

    Die Prüfung in ``stoere`` ist eine **Längen**prüfung, keine Massprüfung: 24×16 und 16×24
    kommen beide durch, weil das Produkt stimmt. Was dann herauskommt, ist keine Störung,
    sondern Unsinn — und er sieht wie eine Messung aus. Also wird hier belegt, dass der
    Läufer die Masse so weitergibt, wie sie in der Datei stehen.
    """
    from aiimaging import bildlesen

    soll, _, _ = bildlesen.tiefen_aus_report(bericht)
    arten, staerken = [VERSCHIEBUNG, SILHOUETTE_WACHSEN], [1.0]
    scores = lambda e: [z["score"] for z in e["zeilen"]]   # noqa: E731

    echt = studie_aus_bericht(bericht, szene="masse", arten=arten, staerken=staerken)
    richtig = studienlauf(soll, breite=BERICHT_BREITE, hoehe=BERICHT_HOEHE,
                          arten=arten, staerken=staerken)
    vertauscht = studienlauf(soll, breite=BERICHT_HOEHE, hoehe=BERICHT_BREITE,
                             arten=arten, staerken=staerken)

    assert scores(echt) == scores(richtig)
    assert scores(echt) != scores(vertauscht), (
        "wären beide gleich, prüfte dieser Test nichts — dann wäre die Szene zu "
        "symmetrisch für die Aussage"
    )


def test_ohne_szenennamen_gibt_es_keine_studie(bericht):
    """Eine Kurve gehört an die Szene, an der sie gemessen wurde.

    Der Name liesse sich aus ``glb_path`` ableiten — das wäre ein absoluter Pfad und
    nach Regel 3 nichts, was in ein Ergebnis gehört, das über das Repo reist. Also nennt
    ihn, wer die Studie fährt.
    """
    for leer in ("", "   "):
        with pytest.raises(StudienError, match="szene"):
            studie_aus_bericht(bericht, szene=leer)


def test_eine_karte_ganz_ohne_bauwerk_ist_keine_studie(tmp_path):
    """Ein Lauf, der nur Himmel gerendert hat, wird gemeldet statt gerechnet.

    Der Test greift auf die **Masse** in der Meldung, und das ist kein Zierrat: ``stoere``
    hat einen eigenen Wächter für denselben Fall, und der wirft dieselbe Ausnahme mit
    demselben Wort „Geometriepunkt". Eine Probe darauf hätte auch dann gehalten, wenn der
    Wächter hier ersatzlos entfiele — genau das war beim Prüfen der Fall (Mutationsprobe
    P8, 26.08.2026). Die Masse nennt nur dieser Wächter; er ist der einzige, der zu
    diesem Zeitpunkt schon weiss, wie gross die Karte war.
    """
    from test_bildlesen import schreibe_exr

    exr = schreibe_exr(tmp_path / "leer.exr", 4, 4, {"V": [1.0e10] * 16})

    with pytest.raises(StudienError, match=r"4×4.*nur Himmel"):
        studie_aus_bericht({"depth_exr": str(exr)}, szene="nur-himmel")


def test_der_png_rueckfall_traegt_seinen_verlust_als_vorbehalt(tmp_path):
    """Liegt nur das normalisierte PNG vor, misst ``geom_iou`` gegen eine bereits
    beschädigte Silhouette — und die Studie sagt das, statt es zu verschweigen.

    Das PNG kann den hintersten Geometriepunkt nicht vom Himmel trennen (beide landen
    auf Grauwert 0). Eine Studie auf so einer Karte ist nicht falsch, aber sie steht auf
    einer anderen Grundlage als eine aus der EXR — und der Unterschied gehört zu den
    Zahlen, nicht in eine Fussnote.
    """
    from aiimaging import bildlesen
    from test_bildlesen import schreibe_png

    karte = bericht_karte()
    geo = [w for w in karte if w < 1e7]
    nah, fern = min(geo), max(geo)
    grau = [round((1.0 - (w - nah) / (fern - nah)) * 65535) if w < 1e7 else 0
            for w in karte]
    png = schreibe_png(tmp_path / "tiefe_norm.png", BERICHT_BREITE, BERICHT_HOEHE, grau,
                       filterarten=[0] * BERICHT_HOEHE)
    bericht = {"depth_exr": None, "depth_png": str(png),
               "depth_normalisierung": {"min_m": nah, "max_m": fern}}

    with pytest.warns(bildlesen.SilhouettenVerlust):
        studie = studie_aus_bericht(bericht, szene="nur-png", arten=[RAUSCHEN],
                                    staerken=[0.0])

    assert VORBEHALT_NICHT_DIE_KETTE in studie["vorbehalte"]
    assert any("normalisierten PNG" in v for v in studie["vorbehalte"])
    assert studie["n_geometrie"] < len(BERICHT_X) * len(BERICHT_Y), (
        "genau der dokumentierte Verlust: der hinterste Punkt fällt in den Himmel"
    )


def test_ein_gitter_ohne_auswertbare_zeile_hat_keine_kurve_und_sagt_das(bericht):
    """Die dritte Antwort, auch hier: keine Kurve ist kein Fehler des Läufers.

    Ein Gitter nur aus Kontrollen hat nichts, woran sich eine Schwelle messen liesse —
    Kontrollen prüfen die Metrik, nicht die Grenze. Das ist kein Grund abzubrechen: Wer
    die Zeilen wollte, bekommt sie; wer die Kurve braucht, findet ``None`` und den Grund
    daneben. Ein geworfener Fehler hätte hier eine Messung verhindert, die es gibt.
    """
    studie = studie_aus_bericht(bericht, szene="nur-kontrollen",
                                arten=[MONOTON, TIEFENUMKEHR])

    assert studie["kurve"] is None
    assert any("Keine Trennschärfekurve" in w for w in studie["warnungen"])
    assert len(studie["zeilen"]) == 2 * len(VORGABE_STAERKEN), (
        "die Zeilen sind gemessen und da — nur auswerten lassen sie sich nicht"
    )


def test_die_kurve_haengt_am_ergebnis_und_ist_die_gewohnte(studie):
    """``kurve`` ist kein zweiter Rechenweg, sondern dieselbe Auswertung wie bisher."""
    assert studie["kurve"] == trennschaerfe_kurve(studie, grenzstaerke=0.2)
    assert 0.0 <= studie["kurve"]["beste"]["schwelle"] <= 1.0
    assert studie["kurve"]["grenzstaerke"] == 0.2
