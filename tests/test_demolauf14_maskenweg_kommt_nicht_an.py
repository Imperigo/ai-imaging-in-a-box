"""Demolauf 14 (01.09.2026): Der Maskenweg LIEF — und kein Bericht sagt, was er fand.

Vier Läufe in Folge blieb das Geometrie-Urteil ohne Aussage, jedes Mal aus einem anderen
Grund (10: Geländebeleg fehlte · 11: kein Diffusionsbild · 12: Absturz vernichtete das
fertige Urteil). Lauf 14 lief bis zum Bild am Knoten durch, und das Urteil sagte
trotzdem nichts:

    geom_iou 0.0 · spearman null · passed false
    «Geometrie: UNGEMESSEN — keine Kamera lieferte einen Wert.»

**Der Satz ist falsch.** Am Gerät nachgesehen: Alle drei Kameras haben ihr
``urteil.json`` geschrieben, und in jedem steht ein **gemessenes** ``rho_maske`` und ein
``paarurteil`` mit ``gemessen: true``, ``zustaendig: true`` — und ``bestanden: false``.
Der Maskenweg ist gefahren, hat gemessen und NEIN gesagt. Ungemessen blieb allein der
Score über das ganze Bild, und zwar zu Recht: ``n_gemeinsam`` ist 0.

Damit ist es derselbe Fehler wie ``up_axis`` am Tag zuvor — ein Wert, der gemessen wird
und an der Naht verworfen wird —, nur eine Stufe gefährlicher: Verworfen wird hier
ausgerechnet das Mass, das die ABWESENHEIT eines Bauwerks fängt. Der Score über das
ganze Bild fängt sie nicht; ein leeres Grundstück erreichte dort 0.9530 und bestand das
Tor (``auf-20260821-26``).

Die Zahlen sind die **echten** aus ``vis-1788295289-cbed48`` und stehen als Literale
hier, weil die Bilder auf einer Halde ausserhalb des Repos liegen und die Probe sie
überleben soll (REGEL 3: keine Benutzerpfade, keine Projektdaten).
"""
from __future__ import annotations

from aiimaging import abholer, kosmo_szene

# ======================================================================================
# Die Zahlen des Laufs
# ======================================================================================

#: Je Kamera: (Kürzel, rho gerichtet, Kantenanteil, Kante roh, n der Maske).
#: Abgelesen aus den drei ``urteil.json`` des Auftrags.
MASKENWEG_LAUF14 = (
    ("s",   0.7713459339020722, 0.21324992891669037, -0.0002667754348646636, 249437),
    ("sSE", 0.9813041042993375, 0.06326383896477354,  0.00020369516763728493, 302424),
    ("nNW", 0.7215813447528334, 0.008226037195994278, -0.0001335256327988429, 268493),
)

#: Das ganze Bild trägt 1600x992 Punkte; ``n_gemeinsam`` war an jeder Kamera **0**.
N_BILDPUNKTE = 1600 * 992


def _kameraurteil(kuerzel, rho, anteil, kante, n_maske):
    """Ein Kameraurteil in der Form, die der Abholer wirklich ablegt.

    Nur die Felder, auf die die Berichtsschicht zugreift — aber diese mit den echten
    Werten. ``score`` und ``spearman`` sind ``None``: Ohne gemeinsame Silhouette gibt es
    keine Tiefenordnung zu vergleichen, und das ist eine fehlende Messung, kein Nullwert.
    """
    return {
        "kamera": kuerzel,
        "score": None,
        "spearman": None,
        "geom_iou": 0.0,
        "bestanden": False,
        "schwelle": 0.65,
        "n_punkte": N_BILDPUNKTE,
        "n_soll": n_maske,
        "n_ist": n_maske,
        "n_gemeinsam": 0,
        "doppelt_von": None,
        "rho_maske": {
            "rho": -rho,
            "gerichtet": rho,
            "n_maske": n_maske,
            "n_bild": N_BILDPUNKTE,
            "anteil_maske": n_maske / N_BILDPUNKTE,
            "polaritaet": -1,
        },
        "paarurteil": {
            "bestanden": False,
            "gemessen": True,
            "zustaendig": True,
            "rho": rho,
            "kante": kante,
            "anteil": anteil,
            "himmel": 1.0,
            "zweites_bein": "anteil",
            "schwellen": {"rho": 0.8, "kante": 0.05, "anteil": 0.2, "himmel": 0.1},
        },
    }


def urteile_des_laufs():
    return [_kameraurteil(*eintrag) for eintrag in MASKENWEG_LAUF14]


def _geometrie_urteil():
    schlechtestes = abholer._schlechtestes(urteile_des_laufs()) or {}
    return dict(schlechtestes, kameraspanne=abholer._kameraspanne(urteile_des_laufs()))


# ======================================================================================
# Was der Lauf wirklich gemessen hat — die Vorbedingung aller weiteren Proben
# ======================================================================================

def test_der_maskenweg_ist_an_allen_drei_kameras_gefahren():
    """Ohne diese Feststellung ist jede folgende Probe gegenstandslos.

    ``gemessen`` und ``zustaendig`` sind beide ``True``. Das ist der Unterschied zwischen
    «konnte hier nichts sagen» und «hat gemessen und NEIN gesagt» — und genau dieser
    Unterschied geht weiter unten verloren.
    """
    for urteil in urteile_des_laufs():
        paar = urteil["paarurteil"]
        assert paar["gemessen"] is True, urteil["kamera"]
        assert paar["zustaendig"] is True, urteil["kamera"]
        assert paar["bestanden"] is False, urteil["kamera"]
        assert urteil["rho_maske"]["gerichtet"] is not None


def test_der_score_bleibt_zu_recht_ohne_wert():
    """``n_gemeinsam`` 0 heisst: kein Bildpunkt, an dem beide Karten Geometrie sehen.

    Der Score ist dort ``None``, und das ist richtig so — er ist eine fehlende Messung
    und kein Nullwert. Die Probe hält fest, dass hier NICHT der Score kaputt ist.
    """
    for urteil in urteile_des_laufs():
        assert urteil["n_gemeinsam"] == 0
        assert urteil["score"] is None
        assert urteil["spearman"] is None


# ======================================================================================
# POSTEN 1 · Der Kurzbefund verschweigt den einzigen Weg, der gemessen hat
# ======================================================================================

def test_der_kurzbefund_nennt_das_ergebnis_des_maskenwegs():
    """``befund_kurz`` liest nur die Sprache des Scores.

    Heute steht dort genau eine Geometriezeile: «Geometrie: UNGEMESSEN — keine Kamera
    lieferte einen Wert.» Die Zeile über den Widerspruch ist selbstlöschend und feuert
    nur bei ``bestanden is True``; die über die Zuständigkeit nur bei
    ``zustaendig is False``. Beide schweigen hier — und damit schweigt der ganze Bericht
    über drei gemessene, durchgefallene Paarurteile.

    Ein Betreiber, der diesen Kurzbefund liest, hält den Lauf für ungeprüft. Er ist
    geprüft und durchgefallen.
    """
    zeilen = abholer.befund_kurz({"kameras": urteile_des_laufs(),
                                  "geometrie_urteil": _geometrie_urteil()})
    text = "\n".join(zeilen)
    assert "MASKENWEG" in text.upper(), (
        "Kein Wort ueber den Maskenweg, obwohl er an allen drei Kameras gemessen und "
        f"NEIN gesagt hat. Gemeldet wird stattdessen:\n{text}")


def test_wer_ungemessen_sagt_muss_sagen_WAS_ungemessen_ist():
    """«Geometrie: UNGEMESSEN» ist wahr über den Score und falsch über den Lauf.

    Der alte Satz nannte kein Subjekt und wurde darum als Aussage über den ganzen Lauf
    gelesen. Ungemessen ist aber nur der Score über das ganze Bild; der Maskenweg hat
    gemessen. Jede Zeile, die «UNGEMESSEN» behauptet, muss deshalb benennen, WAS
    ungemessen blieb — sonst verdeckt sie das einzige Tor, das in diesem Lauf gesprochen
    hat.
    """
    zeilen = abholer.befund_kurz({"kameras": urteile_des_laufs(),
                                  "geometrie_urteil": _geometrie_urteil()})
    ohne_subjekt = [z for z in zeilen if "UNGEMESSEN" in z and "SCORE" not in z.upper()]
    assert not ohne_subjekt, (
        "Eine Zeile nennt etwas ungemessen, ohne zu sagen was — und wird darum als "
        f"Urteil ueber den ganzen Lauf gelesen: {ohne_subjekt}")


def test_der_kurzbefund_sagt_gepruefte_und_nicht_ungeprueft():
    """Der Lauf ist geprüft und durchgefallen. Genau das muss dastehen.

    Von zwei möglichen Fehlern ist «ungeprüft» der weichere und darum der gefährlichere:
    Er lässt einen Lauf harmlos aussehen, in dem das Tor gesperrt hat, das die
    Abwesenheit eines Bauwerks fängt.
    """
    zeilen = abholer.befund_kurz({"kameras": urteile_des_laufs(),
                                  "geometrie_urteil": _geometrie_urteil()})
    text = "\n".join(zeilen)
    assert "DURCHGEFALLEN" in text.upper(), text
    # Und die Zahlen beider Beine, nicht nur das Wort.
    assert "+0.7713" in text and "+0.0082" in text, (
        f"Der Bericht nennt das Ergebnis, aber nicht die Zahlen dahinter:\n{text}")


# ======================================================================================
# POSTEN 2 · Die Kameraspanne erklärt den Lauf für UNGEPRUEFT
# ======================================================================================

def test_die_kameraspanne_nennt_einen_gemessenen_lauf_nicht_ungeprueft():
    """``n_gemessen`` zählt Scores, der Hinweis spricht aber über den ganzen Lauf.

    Heute lautet er wörtlich: «Keine der 3 Kameras ist gemessen. Das gemeldete Urteil ist
    UNGEPRUEFT, nicht durchgefallen.»

    Von zwei möglichen Fehlern ist das der weichere — und darum der gefährlichere: Er
    lässt einen Lauf harmlos aussehen, in dem das Tor, das die Abwesenheit eines
    Bauwerks fängt, dreimal gesperrt hat. «Ungeprüft» und «durchgefallen» sind hier
    vertauscht.
    """
    spanne = abholer._kameraspanne(urteile_des_laufs())
    assert spanne["n_gemessen"] == 0, "Vorbedingung: der Score hat keinen Wert"
    assert "UNGEPRUEFT" not in spanne["hinweis"], (
        "Der Lauf gilt als ungeprueft, obwohl der Maskenweg an allen drei Kameras "
        f"gemessen hat: {spanne['hinweis']!r}")


# ======================================================================================
# POSTEN 3 · Der Vertrag trägt die Zahl nicht, die das Urteil trägt
# ======================================================================================

def test_der_vertrag_sagt_dass_der_maskenweg_gesperrt_hat():
    """``qa.geometry`` führt score, spearman, geom_iou, threshold, passed, method.

    ``rho_maske`` und ``paarurteil`` stehen dort nicht — auch nicht dann, wenn sie die
    **einzigen** gemessenen Werte des Laufs sind. Die Gegenseite liest ``geom_iou 0.0``,
    ``spearman null``, ``passed false`` und kann daraus nicht unterscheiden, ob nichts
    lief oder ob das zweite Tor gemessen und gesperrt hat.

    Der Ort dafür ist ``verdict.reason``: ein Feld IHRES Vertrags. ``hinweise`` wird von
    ``nur_vertragsfelder`` weggestrichen — wer strikt gegen ihr Schema liest, sähe die
    Auskunft nie. Genau dieselbe Lücke wie beim Grund für einen nicht gerenderten Lauf.
    """
    ergebnis = kosmo_szene.als_ergebnis(
        "vis-0000000000-000000", ["s.png"],
        geometrie_urteil=_geometrie_urteil(), stil_urteil=None)
    grund = ergebnis["qa"]["verdict"]["reason"]
    assert "MASKENWEG" in grund.upper(), (
        "Der Vertragsgrund nennt den Maskenweg nicht, obwohl er das einzige Tor ist, "
        f"das in diesem Lauf ueberhaupt gemessen hat: {grund!r}")
