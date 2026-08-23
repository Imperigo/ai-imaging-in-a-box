"""Waagrechte Kamera und Shift — die einzige verbindliche Regel des Fachs, als Code.

Was hier NICHT geprüft wird: dass die Bilder besser werden. Sie werden es nicht — am
Gerät gemessen (`auf-20260822-29`): Über Eck liegen gekippt (−0,9835) und waagrecht
(−0,9650) innerhalb von 0,019. Der Modus ist eine Normfrage, keine Qualitätsfrage, und
diese Tests behaupten nichts anderes.

Was hier geprüft wird: dass er tut, was er sagt — senkrechte Kanten senkrecht —, dass er
bei ``shift_mm=0`` **Zeile für Zeile** die alte Rechnung ist, und dass er bis in den
Blender-Aufruf durchkommt statt auf halbem Weg zu versickern.
"""
import math

import pytest

from aiimaging import kameras, seams

BBOX = [[0.0, 0.0, 0.0], [40.0, 26.0, 15.0]]


# ======================================================================================
# Was der Shift IST
# ======================================================================================

def test_shift_ist_brennweite_mal_tangens():
    """Der ganze Satz in einer Zusicherung: ``shift = f · tan(Neigung)``."""
    befund = kameras.shift_aus_ziel((0.0, -12.0, 1.7), (0.0, 0.0, 4.7),
                                    brennweite_mm=28.0)
    assert befund["shift_tangens"] == pytest.approx(3.0 / 12.0)
    assert befund["shift_mm"] == pytest.approx(28.0 * 0.25)
    assert befund["neigung_grad"] == pytest.approx(math.degrees(math.atan(0.25)))


def test_das_waagrechte_ziel_behaelt_die_richtung_und_verliert_die_hoehe():
    befund = kameras.shift_aus_ziel((5.0, -12.0, 1.7), (5.0, 3.0, 9.0))
    assert befund["waagrechtes_ziel"] == (5.0, 3.0, 1.7)


def test_ohne_hoehenunterschied_kein_shift():
    """Ein Ziel auf Augenhöhe braucht keinen Shift — beide Modi liefern dasselbe Bild."""
    befund = kameras.shift_aus_ziel((0.0, -12.0, 1.7), (0.0, 0.0, 1.7))
    assert befund["shift_mm"] == pytest.approx(0.0)


def test_ein_ziel_senkrecht_ueber_der_kamera_wird_gemeldet_statt_gerechnet():
    """Kein Shift der Welt bildet das mit waagrechter Achse ab."""
    befund = kameras.shift_aus_ziel((0.0, 0.0, 1.7), (0.0, 0.0, 20.0))
    assert befund["shift_mm"] == 0.0
    assert befund["warnungen"], "eine stille 0 wäre hier eine Unwahrheit"


def test_die_bildkreisgrenze_wird_gemeldet_und_nicht_erzwungen():
    """12 mm ist eine Aussage über Objektive, keine über Geometrie."""
    nah = kameras.shift_aus_ziel((0.0, -6.0, 1.7), (0.0, 0.0, 12.0),
                                 brennweite_mm=28.0)
    assert nah["shift_mm"] > kameras.MAX_SHIFT_MM
    assert nah["ueber_grenze"] is True
    assert any("Bildkreis" in w for w in nah["warnungen"])
    assert nah["shift_mm"] == pytest.approx(28.0 * (12.0 - 1.7) / 6.0), (
        "gerechnet wird der wahre Wert — abgeschnitten wäre er eine stille Lüge"
    )


def test_blender_einheit_ist_der_anteil_der_sensorbreite():
    assert kameras.blender_shift_y(18.0, sensor_breite_mm=36.0) == pytest.approx(0.5)


# ======================================================================================
# Der Rahmen wird unsymmetrisch — das ist die eigentliche Wirkung
# ======================================================================================

def test_bei_null_shift_ist_es_zeile_fuer_zeile_die_alte_rechnung():
    """Die wichtigste Zusicherung dieses Moduls.

    Der Shift wurde in bestehende Funktionen eingebaut. Wäre die Umstellung auch nur um
    einen Faktor daneben, änderte sich **jede bisher gemessene Aufnahme** — und zwar
    still, weil die Vorgabe ``shift_mm=0`` überall greift.
    """
    auge, ziel = (0.0, -60.0, 1.7), (20.0, 13.0, 4.7)
    ohne = kameras.ecken_im_bild(auge, ziel, BBOX)
    null = kameras.ecken_im_bild(auge, ziel, BBOX, shift_mm=0.0)
    assert ohne == null

    assert kameras.flaechenanteil(auge, ziel, BBOX) == \
        kameras.flaechenanteil(auge, ziel, BBOX, shift_mm=0.0)


def test_der_shift_wirkt_in_BEIDE_richtungen_je_nachdem_was_bindet():
    """Ein Beispiel hätte hier in die Irre geführt — es braucht beide.

    Der Rahmen wird oben grosszügiger und unten enger. Was daraus für den Abstand folgt,
    hängt davon ab, welche Kante überhaupt bindet:

    * **Hoher Turm, Dach bindet** → der Shift schafft oben Platz und die Kamera darf
      NÄHER heran. Das ist der Zweck des Shift-Objektivs.
    * **Flacher Bau aus der Nähe, Fuss bindet** → der Shift nimmt unten Platz und die
      Kamera muss WEITER weg. Das ist der Term, den man übersieht (Recherche §4.3).

    Der erste Anlauf dieses Tests prüfte einen breiten, niedrigen Bau aus 22 m — dort
    bindet die **Breite**, und der Shift änderte gar nichts. Er wäre grün geworden, wenn
    man ihn auf „ändert sich irgendwie" gestellt hätte, und hätte nichts gezeigt.
    """
    turm = [[0.0, 0.0, 0.0], [10.0, 10.0, 40.0]]
    ohne = kameras.ecken_im_bild((5.0, -40.0, 1.7), (5.0, 5.0, 9.7), turm)
    mit = kameras.ecken_im_bild((5.0, -40.0, 1.7), (5.0, 5.0, 9.7), turm, shift_mm=5.0)
    assert ohne["noetiger_rueckschub_m"] > mit["noetiger_rueckschub_m"] > 0.0, (
        "beim hohen Turm bindet das Dach — der Shift schafft dort Platz"
    )

    flach = [[0.0, 0.0, 0.0], [10.0, 10.0, 3.0]]
    ohne = kameras.ecken_im_bild((5.0, -6.0, 1.7), (5.0, 5.0, 1.7), flach)
    mit = kameras.ecken_im_bild((5.0, -6.0, 1.7), (5.0, 5.0, 1.7), flach, shift_mm=5.0)
    assert mit["noetiger_rueckschub_m"] > ohne["noetiger_rueckschub_m"] > 0.0, (
        "beim flachen Bau aus der Nähe bindet der Fuss — der Shift kostet dort Abstand"
    )


def test_zwoelf_millimeter_im_querformat_setzen_den_horizont_auf_die_unterkante():
    """Die Gegenprobe an einer BELEGTEN Zahl, und sie fällt exakt.

    Recherche §4.4: Bei 24 mm Sensorhöhe (Querformat) liegt der Horizont bei 12 mm Shift
    „exakt auf der Unterkante" — der Anteil der Bildhöhe unter dem Horizont ist 0,0 %.
    Der Horizont ist bei waagrechter Kamera nichts anderes als die Blickachse. Unsere
    Rechnung muss also genau dort umschlagen, an dem die Achse den Rahmen verlässt.

    Und sie tut es **unabhängig von der Brennweite**: Sowohl die Rahmengrenze
    ``(s/2)/f`` als auch der Versatz ``v/f`` tragen dasselbe ``f`` im Nenner. Genau das
    sagt die Tabelle der Recherche auch — sie führt die Brennweite gar nicht.
    """
    quer = 36.0 / 24.0                       # Kleinbild quer: 36 × 24 mm
    for brennweite in (17.0, 24.0, 28.0, 90.0):
        knapp = kameras.ecken_im_bild((20.0, -40.0, 1.7), (20.0, 13.0, 1.7), BBOX,
                                      shift_mm=11.9, brennweite_mm=brennweite,
                                      seitenverhaeltnis=quer, bildrand=1.0)
        drueber = kameras.ecken_im_bild((20.0, -40.0, 1.7), (20.0, 13.0, 1.7), BBOX,
                                        shift_mm=12.0, brennweite_mm=brennweite,
                                        seitenverhaeltnis=quer, bildrand=1.0)
        assert knapp["noetiger_rueckschub_m"] is not None, brennweite
        assert "ausserhalb des Rahmens" in drueber["begruendung"], brennweite


def test_ein_shift_nach_unten_kehrt_die_unsymmetrie_um():
    """Negativer Shift ist kein Sonderfall, sondern kommt aus dem eigenen Code.

    ``ZIEL_HOECHSTANTEIL`` hält das Blickziel im Bauwerk. Bei einem 3-m-Bau liegt es
    dadurch bei 1,5 m — **unter** der Augenhöhe von 1,70 m. Der Shift-Modus rechnet dort
    einen Shift nach unten (gemessen: −0,43 mm), und der Rahmen wird andersherum
    unsymmetrisch: oben enger, unten weiter.

    Ohne diesen Test überlebte die Mutation ``hoch / grenze_oben  →  |hoch| / grenze_oben``
    — bei positivem Shift ist sie folgenlos, weil die untere Grenze dort ohnehin
    strenger ist. Bei negativem Shift ist sie es nicht.
    """
    # (a) Oben wird es enger: Ein schmaler 5-m-Bau, der aus 12 m ohne Shift bequem
    #     hineinpasst, braucht mit Shift nach unten 9,4 m Rückschub — das Dach bindet.
    # Brennweite ausdrücklich: Die Zahlen unten sind an 28 mm gerechnet, und ein Test,
    # dessen Aussage an der Vorgabe hängt, misst die Vorgabe statt den Mechanismus.
    schmal = [[0.0, 0.0, 0.0], [3.0, 3.0, 5.0]]
    auge, ziel = (1.5, -12.0, 1.7), (1.5, 1.5, 1.7)
    assert kameras.ecken_im_bild(auge, ziel, schmal,
                                 brennweite_mm=28.0)["noetiger_rueckschub_m"] == 0.0
    assert kameras.ecken_im_bild(auge, ziel, schmal, brennweite_mm=28.0,
                                 shift_mm=-5.0)["noetiger_rueckschub_m"] > 9.0

    # (b) Unten wird es weiter — und GENAU das prüft die Zahl. Bei diesem flachen Bau
    #     bindet die Breite (0,454 m). Wer die obere, engere Grenze fälschlich auch auf
    #     Punkte UNTER der Achse anwendet, macht daraus 3,03 m.
    flach = [[0.0, 0.0, 0.0], [10.0, 10.0, 3.0]]
    runter = kameras.ecken_im_bild((5.0, -8.0, 1.7), (5.0, 5.0, 1.7), flach,
                                   brennweite_mm=28.0, shift_mm=-5.0)
    assert runter["noetiger_rueckschub_m"] == pytest.approx(0.454, abs=0.01)


def test_ein_niedriger_bau_bekommt_wirklich_einen_shift_nach_unten():
    """Die Gegenprobe am echten Weg: nicht erfunden, sondern aus `kamerasatz`."""
    kamera = kameras.kamerasatz([[0, 0, 0], [6, 6, 3]], modus=kameras.MODUS_SHIFT,
                                kuerzel=["n"])["kameras"][0]
    assert kamera["shift_mm"] < 0.0


def test_ein_shift_groesser_als_der_halbe_bildwinkel_wird_gemeldet():
    """Dann liegt die Blickachse ausserhalb des Rahmens — kein Rückschub hilft."""
    befund = kameras.ecken_im_bild((20.0, -40.0, 1.7), (20.0, 13.0, 4.7), BBOX,
                                   shift_mm=40.0, brennweite_mm=28.0)
    assert befund["passt"] is False
    assert befund["noetiger_rueckschub_m"] is None
    assert "ausserhalb des Rahmens" in befund["begruendung"]


# ======================================================================================
# Der Kamerasatz
# ======================================================================================

def test_im_shift_modus_bleiben_senkrechte_senkrecht():
    """Der Zweck des ganzen Moduls, und er ist exakt prüfbar: Die Kamera-Hochachse muss
    die Welt-Hochachse sein. Jede Abweichung davon IST die stürzende Linie."""
    kamera = kameras.kamerasatz(BBOX, modus=kameras.MODUS_SHIFT,
                                kuerzel=["sSE"])["kameras"][0]
    _, _, oben = kameras._kamerabasis(kamera["auge"], kamera["blick_auf"])
    assert oben == pytest.approx((0.0, 0.0, 1.0), abs=1e-12)
    assert kamera["neigung_grad"] == 0.0


def test_im_gekippten_modus_kippen_sie_und_die_zahl_steht_dabei():
    """Gegenprobe — und der Grund, warum ``neigung_grad`` auch dort mitgeführt wird:
    Die Normverletzung soll an jedem Bild kleben, nicht in einem Dokument stehen."""
    kamera = kameras.kamerasatz(BBOX, kuerzel=["sSE"],
                                modus=kameras.MODUS_GEKIPPT)["kameras"][0]
    _, _, oben = kameras._kamerabasis(kamera["auge"], kamera["blick_auf"])
    assert oben[2] < 1.0, "die Hochachse ist gekippt"
    assert kamera["neigung_grad"] > 0.5
    assert kamera["shift_mm"] == 0.0


def test_die_ueberlieferten_9_46_grad_gelten_fuer_kamerasatz_nicht():
    """Nachgemessen, weil die Zahl durch vier Dokumente gewandert ist.

    ``atan(0.20/1.2) = 9,4623°`` gilt bei einem Abstand von 1,2 × Gebäudehöhe. Über zwölf
    Richtungen, vier Gebäudehöhen und zwei Formate steht ``kamerasatz`` bei
    2,5–5,5 × Gebäudehöhe, und die Neigung bleibt unter 5°.
    """
    alle = []
    for bbox in ([[0, 0, 0], [12, 10, 8]], [[0, 0, 0], [40, 26, 15]],
                 [[0, 0, 0], [25, 20, 30]], [[0, 0, 0], [30, 30, 60]]):
        for sv in (16 / 9, 1.0):
            alle += [k["neigung_grad"]
                     for k in kameras.kamerasatz(bbox, seitenverhaeltnis=sv)["kameras"]]
    assert max(alle) < 5.0, f"gemessen bis {max(alle):.2f}°"
    assert max(alle) < 9.4623 / 2.0, "die überlieferte Zahl ist mehr als doppelt so gross"


def test_der_noetige_shift_bleibt_weit_unter_dem_machbaren():
    """Die andere Seite desselben Befunds: Wer weit weg steht, muss wenig schieben."""
    alle = []
    for bbox in ([[0, 0, 0], [12, 10, 8]], [[0, 0, 0], [40, 26, 15]],
                 [[0, 0, 0], [30, 30, 60]]):
        for sv in (16 / 9, 1.0):
            alle += [abs(k["shift_mm"]) for k in
                     kameras.kamerasatz(bbox, modus=kameras.MODUS_SHIFT,
                                        seitenverhaeltnis=sv)["kameras"]]
    assert max(alle) < kameras.MAX_SHIFT_MM / 4.0, f"gemessen bis {max(alle):.2f} mm"


def test_beide_modi_rahmen_praktisch_dasselbe():
    """Wäre der Shift falsch gerechnet, sässe das Bauwerk woanders im Bild.

    Die Flächenanteile dürfen nicht gleich SEIN — Kippen und Schieben sind zwei
    verschiedene Abbildungen —, aber sie müssen nahe beieinander liegen. Ein Faktor zwei
    hiesse: falsch gerechnet.
    """
    for kuerzel in ("n", "sSE", "wWN"):
        gekippt = kameras.kamerasatz(BBOX, kuerzel=[kuerzel])["kameras"][0]
        geshiftet = kameras.kamerasatz(BBOX, modus=kameras.MODUS_SHIFT,
                                       kuerzel=[kuerzel])["kameras"][0]
        assert geshiftet["flaechenanteil"] == pytest.approx(
            gekippt["flaechenanteil"], rel=0.10), kuerzel


def test_unbekannter_modus_ist_ein_fehler_und_kein_rueckfall():
    with pytest.raises(ValueError, match="Kameramodus"):
        kameras.kamerasatz(BBOX, modus="waagerecht-ish")


def test_die_vorgabe_ist_seit_dem_23_08_der_shift_modus():
    """Der Owner hatte den Wechsel an eine Bedingung geknüpft: erst wenn `auf-33` das
    Verhalten am Gerät bestätigt. Es hat — in fünf Fällen, darunter der entscheidende:
    Gekippt weichen die senkrechten Kanten um 0,47°–0,98° ab, geshiftet um 0,004°–0,016°,
    und das ist der Rauschboden der Messung.

    Der gekippte Modus bleibt vollständig erhalten. `auf-33` hat nachgewiesen, dass er
    **bildpunktgleich** dasselbe liefert wie vor dem Umbau — jede vor diesem Tag
    gemessene Aufnahme ist damit weiterhin reproduzierbar.
    """
    assert kameras.kamerasatz(BBOX, kuerzel=["n"])["kameras"][0]["modus"] == \
        kameras.MODUS_SHIFT
    assert kameras.kamerasatz(BBOX, kuerzel=["n"],
                              modus=kameras.MODUS_GEKIPPT)["kameras"][0]["modus"] == \
        kameras.MODUS_GEKIPPT


# ======================================================================================
# Die Naht — ein Test am Baustein ersetzt keinen Test an der Naht
# ======================================================================================

def test_der_modus_erreicht_das_blender_kommando():
    kommando = seams.baue_kommando_multipass("a.glb", "/aus", up_axis="Y",
                                             kamera="sSE",
                                             kamera_modus=kameras.MODUS_SHIFT)
    assert f"--kamera-modus={kameras.MODUS_SHIFT}" in kommando


def test_ein_ausdruecklicher_shift_erreicht_das_blender_kommando():
    kommando = seams.baue_kommando_multipass("a.glb", "/aus", up_axis="Y",
                                             kamera="sSE", shift_y=0.25)
    assert "--shift-y=0.25" in kommando


def test_ohne_angabe_steht_nichts_im_kommando():
    """`None` heisst „nicht angefasst". Stünde hier ein 0-Wert, wäre jede bisher
    gemessene Aufnahme nicht mehr bitgleich reproduzierbar."""
    kommando = seams.baue_kommando_multipass("a.glb", "/aus", up_axis="Y", kamera="sSE")
    assert not [t for t in kommando if "shift" in t or "kamera-modus" in t]


def test_der_abholer_reicht_den_modus_bis_an_die_naht(tmp_path):
    """Der Weg, den ein echter Auftrag nimmt — und der einzige, der zählt.

    Geprüft wird der WERT, nicht das Schlüsselwort: `kamera_modus=None` hätte einen
    Test bestanden, der nur nach dem Vorhandensein des Arguments fragt (Sitzung 10).
    """
    from aiimaging import abholer

    gesehen = {}

    def multipass_attrappe(glb, aus, **kw):
        gesehen.update(kw)
        raise RuntimeError("hier endet der Test — der Modus ist angekommen")

    verarbeite = abholer.verarbeiter(out_wurzel=tmp_path,
                                     kamera_modus=kameras.MODUS_SHIFT,
                                     _multipass=multipass_attrappe)
    auftrag = {"modell": tmp_path / "m.glb", "job_id": "vis-1-aaaaaa",
               "verzeichnis": tmp_path,
               "szene": {"kameras": "auto", "aufloesung": 64, "hoehe": 64,
                         "samples": 1, "prompt": "a house"}}
    with pytest.raises(RuntimeError):
        verarbeite(auftrag)
    assert gesehen.get("kamera_modus") == kameras.MODUS_SHIFT


def test_der_abholer_faehrt_ohne_angabe_den_shift_modus(tmp_path):
    from aiimaging import abholer

    gesehen = {}

    def multipass_attrappe(glb, aus, **kw):
        gesehen.update(kw)
        raise RuntimeError("hier endet der Test")

    verarbeite = abholer.verarbeiter(out_wurzel=tmp_path,
                                     _multipass=multipass_attrappe)
    auftrag = {"modell": tmp_path / "m.glb", "job_id": "vis-1-aaaaaa",
               "verzeichnis": tmp_path,
               "szene": {"kameras": "auto", "aufloesung": 64, "hoehe": 64,
                         "samples": 1, "prompt": "a house"}}
    with pytest.raises(RuntimeError):
        verarbeite(auftrag)
    assert gesehen.get("kamera_modus") == kameras.MODUS_SHIFT


# ======================================================================================
# Die Vorgabewerte — Entscheidungen des Owners, festgehalten statt vorausgesetzt
# ======================================================================================

def test_die_vorgabe_brennweite_ist_eine_setzung_und_steht_als_solche_da():
    """35 mm ist die Vorliebe des Owners (23.08.2026), nicht die Aussage der Recherche.

    Die sagt 24–25 mm, aus zwei unabhängigen Quellen. Der Widerspruch bleibt sichtbar:
    `komposition.ARBEITSBRENNWEITE_AUSSEN_MM` trägt weiterhin den belegten Wert, und
    dieses Modul führt, was das Fach sagt, nicht was das Projekt entscheidet.
    """
    from aiimaging import komposition

    assert kameras.BRENNWEITE_MM == 35.0
    assert komposition.ARBEITSBRENNWEITE_AUSSEN_MM == 24.0
    assert kameras.BRENNWEITE_MM != komposition.ARBEITSBRENNWEITE_AUSSEN_MM, (
        "die Abweichung ist gewollt — wer sie glättet, verliert den Beleg"
    )


def test_der_vertragsumsetzer_erbt_die_vorgabe_statt_sie_abzuschreiben():
    """Der stille Fall, gegen den das gebaut ist.

    Hier stand eine fest verdrahtete 28. Als die Vorgabe auf 35 ging, wäre eine Kamera
    ohne eigene Brennweite mit 28 mm in den fremden Vertrag gegangen, während mit 35
    gerendert wird — zwei Zahlen für dieselbe Optik, und kein Test hätte angeschlagen.
    """
    from aiimaging import kosmo_szene

    ohne = kosmo_szene.kamera_zu_spec(
        {"auge": (0.0, -30.0, 1.7), "blick_auf": (0.0, 0.0, 5.0)})
    assert ohne["fov"] == pytest.approx(
        kosmo_szene.brennweite_zu_fov(kameras.BRENNWEITE_MM), abs=0.01)


def test_die_brennweite_ist_je_lauf_einstellbar(tmp_path):
    """„soll ja dann einstellbar sein" — und zwar bis an die Naht, nicht nur im Modul.

    Geprüft wird der WERT, nicht das Schlüsselwort: `brennweite_mm=None` hätte einen
    Test bestanden, der nur nach dem Vorhandensein des Arguments fragt.
    """
    from aiimaging import abholer

    gesehen = {}

    def multipass_attrappe(glb, aus, **kw):
        gesehen.update(kw)
        raise RuntimeError("hier endet der Test")

    verarbeite = abholer.verarbeiter(out_wurzel=tmp_path, brennweite_mm=24.0,
                                     auto_richtungen=("sSE",),
                                     _multipass=multipass_attrappe)
    auftrag = {"modell": tmp_path / "m.glb", "job_id": "vis-1-aaaaaa",
               "verzeichnis": tmp_path,
               "szene": {"kameras": "auto", "aufloesung": 64, "hoehe": 64,
                         "samples": 1, "prompt": "a house"}}
    with pytest.raises(RuntimeError):
        verarbeite(auftrag)
    assert gesehen.get("brennweite") == 24.0


def test_ohne_angabe_bleibt_die_brennweite_offen_und_der_runner_entscheidet(tmp_path):
    """`None` heisst „nicht angefasst", nicht „null".

    Der Runner setzt dann `kameras.BRENNWEITE_MM` — an genau einer Stelle, statt dass
    zwei Module dieselbe Zahl führen.
    """
    from aiimaging import abholer

    gesehen = {}

    def multipass_attrappe(glb, aus, **kw):
        gesehen.update(kw)
        raise RuntimeError("hier endet der Test")

    verarbeite = abholer.verarbeiter(out_wurzel=tmp_path, auto_richtungen=("sSE",),
                                     _multipass=multipass_attrappe)
    auftrag = {"modell": tmp_path / "m.glb", "job_id": "vis-1-aaaaaa",
               "verzeichnis": tmp_path,
               "szene": {"kameras": "auto", "aufloesung": 64, "hoehe": 64,
                         "samples": 1, "prompt": "a house"}}
    with pytest.raises(RuntimeError):
        verarbeite(auftrag)
    assert gesehen.get("brennweite") is None


def test_der_gelaendestand_erreicht_die_naht(tmp_path):
    """Bis an den Multipass, nicht nur bis zum `verarbeiter`.

    Die Mutationsprobe fand genau diese Lücke: Ein Test am Werkzeug zeigte, dass der Wert
    entgegengenommen wird — dass er auch weitergereicht wird, prüfte niemand. Ein
    Parameter, der ankommt und dann liegenbleibt, sieht an einem Werkzeugtest richtig aus.
    """
    from aiimaging import abholer

    gesehen = {}

    def multipass_attrappe(glb, aus, **kw):
        gesehen.update(kw)
        raise RuntimeError("hier endet der Test")

    verarbeite = abholer.verarbeiter(out_wurzel=tmp_path, gelaende_z=412.5,
                                     auto_richtungen=("sSE",),
                                     _multipass=multipass_attrappe)
    auftrag = {"modell": tmp_path / "m.glb", "job_id": "vis-1-aaaaaa",
               "verzeichnis": tmp_path,
               "szene": {"kameras": "auto", "aufloesung": 64, "hoehe": 64,
                         "samples": 1, "prompt": "a house"}}
    with pytest.raises(RuntimeError):
        verarbeite(auftrag)
    assert gesehen.get("gelaende_z") == 412.5


def test_ohne_angabe_bleibt_der_gelaendestand_bis_zur_naht_offen(tmp_path):
    """`None` heisst „nicht gesagt". Erst der Runner setzt dann die Hüllbox-Unterkante —
    an genau einer Stelle, und mit der Warnung, die dazugehört."""
    from aiimaging import abholer

    gesehen = {}

    def multipass_attrappe(glb, aus, **kw):
        gesehen.update(kw)
        raise RuntimeError("hier endet der Test")

    verarbeite = abholer.verarbeiter(out_wurzel=tmp_path, auto_richtungen=("sSE",),
                                     _multipass=multipass_attrappe)
    auftrag = {"modell": tmp_path / "m.glb", "job_id": "vis-1-aaaaaa",
               "verzeichnis": tmp_path,
               "szene": {"kameras": "auto", "aufloesung": 64, "hoehe": 64,
                         "samples": 1, "prompt": "a house"}}
    with pytest.raises(RuntimeError):
        verarbeite(auftrag)
    assert gesehen.get("gelaende_z") is None
