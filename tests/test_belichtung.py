"""Belichtungsprüfung — und der Befund, der sie überhaupt rechtfertigt.

Der wichtigste Test dieser Datei ist nicht der, der eine Schwelle prüft, sondern
:func:`test_geerbte_schwelle_verurteilt_unseren_eigenen_hausstil`. Er hält die geerbte
Konstante gegen unsere eigene Messung und zeigt in Zahlen, warum eine Belichtungsschwelle
an einen Stil gehört und nicht in eine Konstante.
"""
from __future__ import annotations

import struct
import zlib

import pytest

from aiimaging import belichtung, bildlesen


# ======================================================================================
# Hilfsmittel: farbige PNGs schreiben. Unser Produktivschreiber kann nur Graustufen —
# und soll es auch bleiben, er schreibt Tiefenkarten.
# ======================================================================================

def _png(pfad, pixel, breite, hoehe, *, farbtyp=2, bittiefe=8):
    """Ein PNG aus einer flachen Liste von Kanalwerten (0..255 bzw. 0..65535)."""
    kanaele = {0: 1, 2: 3, 4: 2, 6: 4}[farbtyp]
    roh = bytearray()
    schritt = breite * kanaele
    for y in range(hoehe):
        roh.append(0)  # Filter „None"
        zeile = pixel[y * schritt:(y + 1) * schritt]
        if bittiefe == 8:
            roh.extend(int(w) & 0xFF for w in zeile)
        else:
            for w in zeile:
                roh.extend(struct.pack(">H", int(w) & 0xFFFF))

    def block(art, nutzlast):
        return (struct.pack(">I", len(nutzlast)) + art + nutzlast
                + struct.pack(">I", zlib.crc32(art + nutzlast) & 0xFFFFFFFF))

    daten = (b"\x89PNG\r\n\x1a\n"
             + block(b"IHDR", struct.pack(">IIBBBBB", breite, hoehe, bittiefe,
                                          farbtyp, 0, 0, 0))
             + block(b"IDAT", zlib.compress(bytes(roh)))
             + block(b"IEND", b""))
    pfad.write_bytes(daten)
    return pfad


def _einfarbig(pfad, r, g, b, *, breite=8, hoehe=8):
    return _png(pfad, [r, g, b] * (breite * hoehe), breite, hoehe)


def _messung(*, luminanz=0.5, streuung=0.2, anteil_hell=0.0, anteil_dunkel=0.0,
             hell_grenze=belichtung.HELL_GRENZE,
             dunkel_grenze=belichtung.DUNKEL_GRENZE):
    """Eine Messung von Hand — damit `pruefe` ohne Datei prüfbar ist."""
    return {"pfad": "-", "breite": 1, "hoehe": 1, "pixel": 1, "luminanz": luminanz,
            "streuung": streuung, "anteil_hell": anteil_hell,
            "anteil_dunkel": anteil_dunkel, "hell_grenze": hell_grenze,
            "dunkel_grenze": dunkel_grenze}


# ======================================================================================
# Der Befund
# ======================================================================================

def test_geerbte_schwelle_verurteilt_unseren_eigenen_hausstil():
    """Die geerbte 8-%-Schwelle erklärt unseren gemessenen Hausstil zum Fehler.

    Der Grund, warum es dieses Modul gibt. `auf-20260818-14` hat an 74 Werken gemessen:
    Anteil über 0.95 im Mittel 0.0755, Streuung 0.069, Höchstwert 0.3001.
    """
    mittel, streuung, hoechst = 0.0755, 0.069, 0.3001

    # Der Mittelwert liegt KNAPP darunter — das ist der beunruhigende Teil.
    assert mittel < belichtung.GEERBTER_RAHMEN.hell_anteil_max
    assert mittel > 0.9 * belichtung.GEERBTER_RAHMEN.hell_anteil_max

    # Eine Streuung darüber ist deutlich drüber, der Höchstwert fast das Vierfache.
    assert mittel + streuung > belichtung.GEERBTER_RAHMEN.hell_anteil_max
    assert hoechst > 3.0 * belichtung.GEERBTER_RAHMEN.hell_anteil_max

    # Und dasselbe Werk besteht unseren eigenen, gemessenen Rahmen nicht nur knapp:
    urteil = belichtung.pruefe(_messung(anteil_hell=mittel, luminanz=0.5744),
                               belichtung.HAUSSTIL_RAHMEN)
    assert urteil["bestanden"]
    assert urteil["befunde"] == ()

    # Gegen den geerbten Rahmen wäre derselbe Wert ein Befund.
    geerbt = belichtung.pruefe(
        _messung(anteil_hell=mittel + streuung, luminanz=0.5744,
                 hell_grenze=belichtung.GEERBTER_RAHMEN.hell_grenze,
                 dunkel_grenze=belichtung.GEERBTER_RAHMEN.dunkel_grenze),
        belichtung.GEERBTER_RAHMEN)
    assert any(b["befund"] == "zu-viel-ausgefressen" for b in geerbt["befunde"])


def test_der_hoechstwert_des_korpus_reisst_beide_rahmen():
    """0.3001 ist so viel, dass es auch unseren eigenen, gemessenen Rahmen sprengt.

    Der geerbte Rahmen meldet dafür nur `warn` — nicht weil der Wert harmloser wäre,
    sondern weil seine Schwelle ungemessen ist. Genau diese Asymmetrie ist der Punkt.
    """
    geerbt = belichtung.pruefe(
        _messung(anteil_hell=0.3001, luminanz=0.5744,
                 hell_grenze=belichtung.GEERBTER_RAHMEN.hell_grenze,
                 dunkel_grenze=belichtung.GEERBTER_RAHMEN.dunkel_grenze),
        belichtung.GEERBTER_RAHMEN)
    treffer = [b for b in geerbt["befunde"] if b["befund"] == "zu-viel-ausgefressen"]
    assert treffer and treffer[0]["schwere"] == belichtung.SCHWERE_WARN

    eigen = belichtung.pruefe(_messung(anteil_hell=0.3001, luminanz=0.5744),
                              belichtung.HAUSSTIL_RAHMEN)
    treffer = [b for b in eigen["befunde"] if b["befund"] == "zu-viel-ausgefressen"]
    assert treffer and treffer[0]["schwere"] == belichtung.SCHWERE_FEHLER
    assert eigen["bestanden"] is False


def test_der_geerbte_rahmen_gilt_ausdruecklich_als_ungemessen():
    """Er darf darum kein einziges `error` erzeugen — er ist zum Vergleich da."""
    assert belichtung.GEERBTER_RAHMEN.gemessen == ()
    urteil = belichtung.pruefe(
        _messung(anteil_hell=0.99, luminanz=0.99, streuung=0.001,
                 hell_grenze=belichtung.GEERBTER_RAHMEN.hell_grenze,
                 dunkel_grenze=belichtung.GEERBTER_RAHMEN.dunkel_grenze),
        belichtung.GEERBTER_RAHMEN)
    assert urteil["befunde"], "bei diesen Werten muss etwas auffallen"
    assert all(b["schwere"] == belichtung.SCHWERE_WARN for b in urteil["befunde"])
    assert urteil["bestanden"] is True


# ======================================================================================
# Die harte Regel: ungemessen ⇒ nie `error`
# ======================================================================================

def test_ungemessene_schwelle_kann_nur_warnen():
    urteil = belichtung.pruefe(_messung(streuung=0.0), belichtung.HAUSSTIL_RAHMEN)
    flach = [b for b in urteil["befunde"] if b["befund"] == "flach"]
    assert flach and flach[0]["schwere"] == belichtung.SCHWERE_WARN
    assert flach[0]["gemessen"] is False
    assert "NICHT gemessen" in flach[0]["detail"]


def test_gemessene_schwelle_darf_fehler_melden():
    urteil = belichtung.pruefe(_messung(anteil_hell=0.9), belichtung.HAUSSTIL_RAHMEN)
    hell = [b for b in urteil["befunde"] if b["befund"] == "zu-viel-ausgefressen"]
    assert hell and hell[0]["schwere"] == belichtung.SCHWERE_FEHLER
    assert hell[0]["gemessen"] is True
    assert urteil["bestanden"] is False


def test_messrahmen_meldet_nie_einen_fehler():
    """Ein Bild, das nur zum Messen entsteht, soll nicht an der Belichtung scheitern."""
    urteil = belichtung.pruefe(_messung(anteil_hell=1.0, anteil_dunkel=1.0,
                                        luminanz=0.99, streuung=0.0),
                               belichtung.MESS_RAHMEN)
    assert all(b["schwere"] == belichtung.SCHWERE_WARN for b in urteil["befunde"])
    assert urteil["bestanden"] is True


def test_gemessen_darf_keine_erfundenen_felder_nennen():
    with pytest.raises(belichtung.BelichtungsError, match="Felder, die es nicht gibt"):
        belichtung.Rahmen(slug="x", name="X", luma_min=0.1, luma_max=0.9,
                          hell_anteil_max=0.1, dunkel_anteil_max=0.1,
                          streuung_min=0.05, gemessen=("luma_maximum",))


# ======================================================================================
# Alle Befunde, nicht nur der erste
# ======================================================================================

def test_mehrere_befunde_werden_alle_gemeldet():
    """Der Altbestand meldet nur `issues[0]` — ein Bild, das zu hell UND flach ist,
    sieht dort aus wie eines, das nur zu hell ist."""
    urteil = belichtung.pruefe(_messung(anteil_hell=0.9, luminanz=0.99, streuung=0.0),
                               belichtung.HAUSSTIL_RAHMEN)
    arten = {b["befund"] for b in urteil["befunde"]}
    assert {"zu-viel-ausgefressen", "zu-hell", "flach"} <= arten


def test_fehler_stehen_vor_warnungen():
    urteil = belichtung.pruefe(_messung(anteil_hell=0.9, streuung=0.0),
                               belichtung.HAUSSTIL_RAHMEN)
    schweren = [b["schwere"] for b in urteil["befunde"]]
    assert schweren == sorted(schweren, key=lambda s: s != belichtung.SCHWERE_FEHLER)


def test_ohne_befund_ist_bestanden_und_die_zusammenfassung_nennt_zahlen():
    urteil = belichtung.pruefe(_messung(luminanz=0.5744, anteil_hell=0.07),
                               belichtung.HAUSSTIL_RAHMEN)
    assert urteil["bestanden"] and urteil["befunde"] == ()
    assert urteil["schwere"] == belichtung.SCHWERE_OK
    assert "0.574" in urteil["zusammenfassung"]


# ======================================================================================
# Abweichende Grenzen: der Vergleich, der keiner ist
# ======================================================================================

def test_abweichende_grenzen_werden_gemeldet_statt_verschluckt():
    """Ein Anteil über 0.98 ist zwangsläufig kleiner als einer über 0.95 — und sieht
    aus wie ein besseres Bild."""
    urteil = belichtung.pruefe(_messung(hell_grenze=0.98, dunkel_grenze=0.02),
                               belichtung.HAUSSTIL_RAHMEN)
    passend = [b for b in urteil["befunde"] if b["befund"] == "grenzen-weichen-ab"]
    assert passend and passend[0]["schwere"] == belichtung.SCHWERE_WARN
    assert "NICHT vergleichbar" in passend[0]["detail"]


def test_messe_mit_rahmen_benutzt_dessen_grenzen(tmp_path):
    """249/255 = 0.9765 liegt ZWISCHEN den beiden Grenzen — genau der Fall, an dem sich
    zeigt, dass die Anteile zweier Rahmen nicht dasselbe messen."""
    pfad = _einfarbig(tmp_path / "hell.png", 249, 249, 249)
    ohne = belichtung.messe(pfad)
    mit = belichtung.messe(pfad, rahmen=belichtung.GEERBTER_RAHMEN)
    assert ohne["hell_grenze"] == belichtung.HELL_GRENZE == 0.95
    assert mit["hell_grenze"] == belichtung.GEERBTER_RAHMEN.hell_grenze == 0.98
    assert ohne["anteil_hell"] == 1.0, "über 0.95 — das ganze Bild"
    assert mit["anteil_hell"] == 0.0, "über 0.98 — kein einziges Pixel"


def test_pruefe_bild_meldet_keine_abweichenden_grenzen(tmp_path):
    """Der bequeme Weg misst gegen den Rahmen — die Warnung darf gar nicht entstehen."""
    pfad = _einfarbig(tmp_path / "mittel.png", 128, 128, 128)
    urteil = belichtung.pruefe_bild(pfad, belichtung.GEERBTER_RAHMEN)
    assert not [b for b in urteil["befunde"] if b["befund"] == "grenzen-weichen-ab"]


# ======================================================================================
# Messung
# ======================================================================================

def test_luminanz_folgt_rec709(tmp_path):
    """Reines Grün ist heller als reines Rot und weit heller als reines Blau."""
    gruen = belichtung.messe(_einfarbig(tmp_path / "g.png", 0, 255, 0))["luminanz"]
    rot = belichtung.messe(_einfarbig(tmp_path / "r.png", 255, 0, 0))["luminanz"]
    blau = belichtung.messe(_einfarbig(tmp_path / "b.png", 0, 0, 255))["luminanz"]
    assert gruen == pytest.approx(bildlesen.LUMA_G, abs=1e-3)
    assert rot == pytest.approx(bildlesen.LUMA_R, abs=1e-3)
    assert blau == pytest.approx(bildlesen.LUMA_B, abs=1e-3)
    assert gruen > rot > blau


def test_einfarbiges_bild_hat_streuung_null(tmp_path):
    m = belichtung.messe(_einfarbig(tmp_path / "flach.png", 100, 100, 100))
    assert m["streuung"] == pytest.approx(0.0, abs=1e-9)


def test_anteile_sind_anteile_und_keine_prozente(tmp_path):
    """Der Altbestand rechnet in Prozent. Zwei Einheiten für dieselbe Grösse sind eine
    Fehlerquelle ohne jeden Gegenwert."""
    m = belichtung.messe(_einfarbig(tmp_path / "weiss.png", 255, 255, 255))
    assert m["anteil_hell"] == 1.0
    m2 = belichtung.messe(_einfarbig(tmp_path / "schwarz.png", 0, 0, 0))
    assert m2["anteil_dunkel"] == 1.0


def test_halb_hell_halb_dunkel(tmp_path):
    pixel = ([255, 255, 255] * 8 + [0, 0, 0] * 8) * 4
    pfad = _png(tmp_path / "haelfte.png", pixel, 16, 4)
    m = belichtung.messe(pfad)
    assert m["anteil_hell"] == pytest.approx(0.5)
    assert m["anteil_dunkel"] == pytest.approx(0.5)
    assert m["luminanz"] == pytest.approx(0.5, abs=0.01)
    assert m["streuung"] == pytest.approx(0.5, abs=0.01)


def test_unlesbares_bild_meldet_die_urspruengliche_ursache(tmp_path):
    kaputt = tmp_path / "kaputt.png"
    kaputt.write_bytes(b"kein PNG")
    with pytest.raises(belichtung.BelichtungsError, match="nicht messbar"):
        belichtung.messe(kaputt)


def test_messung_aus_fremder_quelle_wird_abgewiesen():
    with pytest.raises(belichtung.BelichtungsError, match="stammt nicht aus messe"):
        belichtung.pruefe({"luminanz": 0.5}, belichtung.HAUSSTIL_RAHMEN)


def test_pruefe_verlangt_einen_rahmen_und_kein_woerterbuch():
    with pytest.raises(belichtung.BelichtungsError, match="erwartet einen Rahmen"):
        belichtung.pruefe(_messung(), {"slug": "x", "hell_anteil_max": 0.1})


# ======================================================================================
# Kein stiller Rückfall
# ======================================================================================

def test_unbekannter_stil_bekommt_keinen_ersatzrahmen():
    """Ein untergeschobener Rahmen wäre ein Urteil über einen Stil anhand der Zahlen
    eines anderen — und es stünde nirgends, dass es so war."""
    assert belichtung.rahmen_fuer("morgennebel") is None
    assert belichtung.rahmen_fuer("kosmo_standard") is belichtung.HAUSSTIL_RAHMEN


def test_rahmen_ist_eingefroren():
    with pytest.raises(Exception):
        belichtung.HAUSSTIL_RAHMEN.hell_anteil_max = 0.9


@pytest.mark.parametrize("kwargs, muster", [
    ({"luma_min": 0.9, "luma_max": 0.1}, "keine Spanne"),
    ({"hell_grenze": 0.1, "dunkel_grenze": 0.5}, "nicht unter"),
    ({"luma_min": float("nan")}, "nicht endlich"),
    ({"hell_anteil_max": "viel"}, "keine Zahl"),
])
def test_unbrauchbare_rahmen_werden_beim_bauen_abgewiesen(kwargs, muster):
    grund = dict(slug="x", name="X", luma_min=0.1, luma_max=0.9, hell_anteil_max=0.1,
                 dunkel_anteil_max=0.1, streuung_min=0.05)
    grund.update(kwargs)
    with pytest.raises(belichtung.BelichtungsError, match=muster):
        belichtung.Rahmen(**grund)


# ======================================================================================
# Der Leser, auf dem alles steht
# ======================================================================================

def test_luminanzleser_nimmt_farbe_an_wo_der_tiefenleser_sie_ablehnt(tmp_path):
    pfad = _einfarbig(tmp_path / "farbe.png", 10, 200, 30)
    werte, breite, hoehe = bildlesen.lies_png_luminanz(pfad)
    assert (breite, hoehe) == (8, 8) and len(werte) == 64
    with pytest.raises(bildlesen.BildError, match="Farbtyp 2"):
        bildlesen.lies_png_graustufen(pfad)


def test_luminanzleser_liest_graustufen_unveraendert(tmp_path):
    pixel = [0, 64, 128, 255]
    pfad = _png(tmp_path / "grau.png", pixel, 4, 1, farbtyp=0)
    luma, _, _ = bildlesen.lies_png_luminanz(pfad)
    grau, _, _ = bildlesen.lies_png_graustufen(pfad)
    assert luma == pytest.approx(grau)


def test_luminanzleser_kann_16_bit(tmp_path):
    pfad = _png(tmp_path / "tief.png", [65535, 0, 0] * 4, 4, 1, farbtyp=2, bittiefe=16)
    werte, _, _ = bildlesen.lies_png_luminanz(pfad)
    assert all(w == pytest.approx(bildlesen.LUMA_R, abs=1e-6) for w in werte)


def test_luminanzleser_ignoriert_alpha(tmp_path):
    """Ein halbdurchsichtiges Pixel hat trotzdem eine Helligkeit — was dahinter liegt,
    weiss dieser Leser nicht."""
    deckend = _png(tmp_path / "deckend.png", [200, 200, 200, 255], 1, 1, farbtyp=6)
    durchsichtig = _png(tmp_path / "durch.png", [200, 200, 200, 0], 1, 1, farbtyp=6)
    a, _, _ = bildlesen.lies_png_luminanz(deckend)
    b, _, _ = bildlesen.lies_png_luminanz(durchsichtig)
    assert a == b


def test_palette_wird_abgelehnt_weil_ihre_zahlen_indizes_sind(tmp_path):
    daten = bytearray(b"\x89PNG\r\n\x1a\n")

    def block(art, nutz):
        return (struct.pack(">I", len(nutz)) + art + nutz
                + struct.pack(">I", zlib.crc32(art + nutz) & 0xFFFFFFFF))

    daten += block(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 3, 0, 0, 0))
    daten += block(b"PLTE", b"\xff\x00\x00")
    daten += block(b"IDAT", zlib.compress(b"\x00\x00"))
    daten += block(b"IEND", b"")
    pfad = tmp_path / "palette.png"
    pfad.write_bytes(bytes(daten))
    with pytest.raises(bildlesen.BildError, match="Palette"):
        bildlesen.lies_png_luminanz(pfad)
