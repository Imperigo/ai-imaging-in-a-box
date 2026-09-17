"""Der Kontaktbogen wird **gebaut**, und diese Proben halten fest, was das heisst.

Die handgesetzte Fassung stand am 09.09.2026 auf **22 Tafeln**, während dreissig
Beweisskripte gelaufen waren. Acht Tafeln fehlten ganz, zwei zeigten weniger Bilder als
der zugehörige Beweis inzwischen schreibt — und es fiel niemandem auf, *weil eine
unvollständige Galerie vollständig aussieht.*

Geprüft wird darum genau das, was die Handarbeit nicht leisten konnte: dass die Seite
zählt, statt zu behaupten, und dass sie **anhält**, statt eine Tafel ohne Text zu bauen.
"""

from __future__ import annotations

import importlib.util
import struct
import zlib
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]


def _werkzeug():
    pfad = WURZEL / "tools" / "beweisgalerie.py"
    spec = importlib.util.spec_from_file_location("werkzeug_beweisgalerie", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _winziges_png(ziel: Path) -> Path:
    """Ein gültiges 1×1-PNG, von Hand gesetzt — der Bogen soll echte Bytes einbetten."""
    roh = zlib.compress(b"\x00\xff\xff\xff")

    def block(art: bytes, nutz: bytes) -> bytes:
        return (struct.pack(">I", len(nutz)) + art + nutz
                + struct.pack(">I", zlib.crc32(art + nutz) & 0xFFFFFFFF))

    kopf = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ziel.write_bytes(b"\x89PNG\r\n\x1a\n" + block(b"IHDR", kopf)
                     + block(b"IDAT", roh) + block(b"IEND", b""))
    return ziel


@pytest.fixture()
def bogen(tmp_path):
    """Ein Bilderordner mit **einer** bekannten Tafel und zwei Bildern."""
    modul = _werkzeug()
    name = next(iter(modul.TAFELN))
    ordner = tmp_path / name
    ordner.mkdir()
    _winziges_png(ordner / "01_erstes_wert-0.42.png")
    _winziges_png(ordner / "02_zweites_wert-0.99.png")
    return modul, tmp_path, name


def test_die_zahl_im_kopf_wird_gezaehlt_und_nicht_behauptet(bogen):
    """Die handgesetzte Fassung nannte 22 Tafeln, während dreissig gelaufen waren."""
    modul, wurzel, _ = bogen
    html = modul.baue(wurzel)

    # WORTLAUT AM 17.09.2026 GEAENDERT, ABSICHT UNVERAENDERT: Die Kopfzeile nennt jetzt
    # auch, wie viele Tafeln es UEBERHAUPT gibt — sonst sieht ein Bogen aus zwanzig
    # gefahrenen Tafeln so vollstaendig aus wie einer aus dreissig. Genau der Fehler, den
    # diese Probe seit je bewacht, nur eine Ebene hoeher.
    # Gegen die Konstante und nicht gegen eine feste Zahl: Kommt ein Beweis dazu,
    # aendert sich der Nenner, und eine festgeschriebene 30 machte die Probe rot, ohne
    # dass etwas kaputt waere.
    assert f"1 von {len(modul.TAFELN)} Tafeln mit Bildern · 2 Bilder" in html
    assert html.count('<section class="tafel"') == 1
    assert html.count('<figure class="platte') == 2


def test_die_bilder_stehen_wirklich_in_der_seite(bogen):
    """Ein Bogen, der nur Dateinamen nennt, ist ein Verzeichnis und keine Übersicht."""
    modul, wurzel, _ = bogen
    html = modul.baue(wurzel)

    assert html.count("data:image/png;base64,iVBOR") == 2
    assert 'alt="01_erstes_wert-0.42.png"' in html


def test_der_dateiname_wird_zur_bildunterschrift(bogen):
    """*Eine Zahl gehört an die Bedingung, unter der sie gemessen wurde* — hier heisst
    das: unter ihr Bild."""
    modul, _, _ = bogen
    assert modul._felder("03_differenz_mittel-0.05394_schwelle-0.01.png") == [
        "03", "differenz", "mittel 0.05394", "schwelle 0.01"]


def test_ein_ordner_ohne_text_haelt_den_lauf_an(bogen):
    """**Ohne Text keine Tafel.**

    In dem Satz unter der Überschrift steht, was man sieht *und was die Messung nicht
    trägt*. Eine Tafel ohne ihn wäre eine Bildergalerie — und ein Bild ohne den Satz
    daneben ist Dekoration.
    """
    modul, wurzel, _ = bogen
    (wurzel / "99_ein_neuer_beweis").mkdir()

    with pytest.raises(SystemExit) as fehler:
        modul.baue(wurzel)
    assert "99_ein_neuer_beweis" in str(fehler.value)


def test_eine_nicht_gefahrene_tafel_wird_gemeldet_und_uebersprungen(bogen, capsys):
    """Die Gegenrichtung, und sie ist **kein** Fehler.

    Ein Eintrag ohne Ordner heisst: Dieser Beweis ist in diesem Lauf nicht gefahren
    worden. Das gehört gesagt — still weglassen sähe aus wie Vollständigkeit.
    """
    modul, wurzel, name = bogen
    html = modul.baue(wurzel)
    gemeldet = capsys.readouterr().err

    assert "NICHT GEFAHREN" in gemeldet
    assert name not in gemeldet, "die gefahrene Tafel darf nicht als fehlend gelten"
    assert html.count('<section class="tafel"') == 1


def test_der_schalter_bilder_zeigt_wirklich_woanders_hin(bogen, tmp_path):
    """Der Schalter `--bilder`, gedrückt — die Hausregel aus `test_schalterprobe.py`."""
    modul, wurzel, _ = bogen
    ziel = tmp_path / "aus" / "bogen.html"

    assert modul.main([str(ziel), "--bilder", str(wurzel)]) == 0
    assert (f"1 von {len(modul.TAFELN)} Tafeln mit Bildern · 2 Bilder"
            in ziel.read_text(encoding="utf-8"))


def test_ein_fehlender_bilderordner_ist_kein_leerer_bogen(tmp_path, capsys):
    """Fail-closed: Ohne Bilder entsteht **keine** Seite.

    Ein leerer Bogen sähe aus wie «es gibt keine Beweise» — und das ist die gefährlichere
    der beiden Lesarten. Derselbe Grund wie beim leeren Einbau-Blatt.
    """
    modul = _werkzeug()
    assert modul.main([str(tmp_path / "x.html"), "--bilder", str(tmp_path / "gibtsnicht")]) == 1
    assert not (tmp_path / "x.html").exists()


def test_die_seite_bringt_keine_zweite_huelle_mit(bogen):
    """Der Artefaktdienst legt Kopf und Hülle selbst darum — eine zweite bräche die Seite."""
    modul, wurzel, _ = bogen
    html = modul.baue(wurzel)

    assert "<!doctype" not in html.lower()
    assert "</body>" not in html.lower()
    assert html.lstrip().startswith("<title>")


def test_eine_nicht_gefahrene_tafel_verschwindet_nicht_aus_dem_bogen(bogen):
    """**Die dritte Antwort, angewandt auf eine Galerie.**

    Bis zum 17.09.2026 wurden nicht gefahrene Beweise nur auf ``stderr`` gemeldet und
    verschwanden aus der Übersicht. Eine Übersicht, aus der das Fehlende verschwindet,
    **sieht vollständig aus** — wer sie liest, zählt die Tafeln und glaubt, das sei alles.

    *NICHT GEFAHREN ist weder vorhanden noch «gibt es nicht».*
    """
    modul, wurzel, name = bogen
    html = modul.baue(wurzel)

    fehlende = len(modul.TAFELN) - 1
    assert html.count('<section class="tafel ohnebilder"') == fehlende, (
        f"Alle {fehlende} nicht gefahrenen Tafeln gehören in den Bogen.")
    assert html.count("NICHT GEFAHREN") == fehlende
    assert f"1 von {len(modul.TAFELN)} Tafeln mit Bildern" in html, (
        "Der Kopf muss den Nenner nennen, sonst sagt die Zahl nichts.")

    # UND SIE ERFINDET KEINEN GRUND. Wo im Tafeltext kein Vorbehalt steht, sagt die
    # Galerie, dass der Lauf selbst den Grund kennt — nicht sie.
    assert "sie erfindet keinen Grund" in html


def test_die_auswahl_des_vortrags_steht_am_bild_und_nicht_als_zweite_galerie(bogen, tmp_path):
    """`praesentation/bilder/` ist kein zweiter Bestand, sondern eine **Auswahl**.

    Dieselben Bilder ein zweites Mal zu zeigen hiesse, dieselbe Messung zweimal zu
    behaupten — und beim nächsten Lauf hätte man zwei Stände, von denen einer still
    veraltet. *Eine Auswahl ist eine Eigenschaft des Bildes, kein eigenes Bild.*
    """
    import json
    modul, wurzel, name = bogen

    wahl = tmp_path / "wahl.json"
    wahl.write_text(json.dumps({"erstes.png": {"ziel": f"{name}/01_erstes*"}}),
                    encoding="utf-8")
    modul.VORTRAGSWAHL = wahl
    modul.BILDER = wurzel
    html = modul.baue(wurzel)

    assert html.count('class="vortrag"') == 1, "genau das eine gewählte Bild trägt die Marke"
    assert html.count('class="platte beweis') == 2, "beide Bilder stehen weiterhin da"
    assert "1 davon im Vortrag" in html


def test_eine_fehlende_vortragswahl_kostet_nicht_die_galerie(bogen, tmp_path):
    """**GEGENPROBE.** Eine Nebenauskunft darf das Ganze nicht mitreissen.

    Fehlt die Auswahl oder ist sie unlesbar, steht der Bogen ohne Marken da — und das
    heisst «nicht bekannt, welche Bilder im Vortrag sind», nicht «keines ist drin». Ein
    Abbruch kostete die ganze Galerie, weil eine Zusatzangabe fehlt.
    """
    modul, wurzel, _ = bogen

    modul.VORTRAGSWAHL = tmp_path / "gibt-es-nicht.json"
    assert modul._vortragsbilder() == set()
    assert "0 davon im Vortrag" in modul.baue(wurzel)

    kaputt = tmp_path / "kaputt.json"
    kaputt.write_text("{das ist kein json", encoding="utf-8")
    modul.VORTRAGSWAHL = kaputt
    assert modul._vortragsbilder() == set(), "unlesbar heisst nicht «keines»"
    assert modul.baue(wurzel), "und die Galerie steht trotzdem"
