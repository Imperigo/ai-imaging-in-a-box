"""Was eine Datei über sich selbst sagt — und wo dieses Modul aufhört zu raten.

Drei Sorten Tests, bewusst getrennt
-----------------------------------
1. **Ohne alles.** Kopf- und Einheitenlesen an IFC-, glTF- und glb-Dateien, die dieser
   Test selbst schreibt. Der grösste Teil, und er läuft überall: kein ``ifcopenshell``,
   kein numpy, kein Netz. Genau das ist die Zusage von ``herkunft.py`` — der Dateikopf
   wird gebraucht, **bevor** entschieden ist, ob überhaupt konvertiert wird, und darum
   darf sein Leser nicht an der Prozessgrenze hängen.
2. **Die Gegenprobe ohne Konverter.** :func:`pruefe_einheit_gegen_masse` ist reine
   Rechnerei auf einem Kopf und sechs Zahlen; die Fälle „kein Urteil möglich" brauchen
   niemanden.
3. **Mit dem echten Konverter** (``@pytest.mark.skipif``). Nur die drei Lagen aus dem
   Modul-Docstring — Meter, echte ArchiCAD-Art, kaputter Export — laufen wirklich durch
   ``seams.ifc_zu_glb`` im ``.venv-ifc``. Sie sind der Beleg für die Kernaussage des
   Moduls, und der lässt sich nicht nachrechnen, nur messen.

Die eine Verwechslung, gegen die die halbe Datei antritt
---------------------------------------------------------
``meter_je_einheit is None`` heisst *unbekannt*, ``== 1.0`` hiesse *Meter*. Wer das
gleichsetzt, baut den mm-als-m-Fehler ein, den der ``torwaechter`` danach abfangen muss
— und dort ist er nur noch ein Verdacht ohne Ursache. Mehrere Tests prüfen darum nicht
bloss „kein Faktor", sondern ausdrücklich ``is None`` **und** ``!= 1.0``.

Warum die Prüflinge aus ``tools/make_test_ifc.py`` kommen
----------------------------------------------------------
Regel 3: keine echten Projektdaten. Die Fixture erzeugt einen synthetischen Testbau von
8,0 × 5,0 × 3,25 m; alle Spielarten (Millimeter, kaputter Export, fremder Erzeuger)
entstehen daraus durch Textersetzung. Damit ist jeder Prüfling im Repo erzeugbar und
trägt keinen Büro-, Kunden- oder Projektnamen.
"""
from __future__ import annotations

import json
import re
import struct
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import REPO

from aiimaging import herkunft as hk
from aiimaging import seams
from aiimaging.contracts import ContractError
from aiimaging.herkunft import (
    BELEGT,
    HERKUENFTE,
    LESEFENSTER_BYTE,
    UNBEKANNT,
    VERMUTET,
    HerkunftError,
    deute,
    fordere_up_axis,
    lies_gltf_kopf,
    lies_ifc_kopf,
    pruefe_einheit_gegen_masse,
)

#: Die Einheitenzeile, wie ``make_test_ifc.py`` sie schreibt. Angelpunkt aller Varianten.
EINHEIT_METER = "IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.)"

#: Eine Zeile ohne Längeneinheit — der Ersatz für „die Datei sagt nichts dazu". Bewusst
#: eine gültige Einheitenzeile und keine kaputte: Geprüft werden soll das Fehlen der
#: Längenangabe, nicht die Verdauung von Schrott.
EINHEIT_OHNE_LAENGE = "IFCSIUNIT(*,.MASSUNIT.,$,.GRAM.)"

#: Zeilenarten, deren Zahlen eine Länge sind. Beim Umrechnen auf Millimeter werden nur
#: diese mit 1000 multipliziert — ``IFCDIRECTION`` trägt Richtungsvektoren, die sind
#: einheitslos, und ein skalierter Richtungsvektor wäre ein anderer Fehler als der
#: gesuchte.
LAENGENZEILEN = ("IFCCARTESIANPOINT", "IFCRECTANGLEPROFILEDEF", "IFCEXTRUDEDAREASOLID")

#: Grösste Kante des synthetischen Testbaus in Metern (8,0 × 5,0 × 3,25).
KANTE_M = 8.0

#: Blockkennung ``JSON`` im binären glb, wie die Norm sie vorschreibt (little endian).
KENNUNG_JSON = 0x4E4F534A

#: Blockkennung ``BIN\0`` — der zweite Block. Als *erster* ist er normwidrig.
KENNUNG_BIN = 0x004E4942


# ======================================================================================
# Werkzeuge: IFC-Varianten und glb-Dateien selbst herstellen — reine Standardbibliothek
# ======================================================================================

def erzeuge_ifc(ziel: Path) -> Path:
    """Den synthetischen Testbau nach ``ziel`` schreiben.

    Über einen Subprozess und nicht per Import: ``tools/`` ist kein Paket und liegt nicht
    auf ``sys.path``. So wird das Skript genau auf dem Weg benutzt, auf dem es auch sonst
    benutzt wird — ein Importpfad, den niemand sonst geht, prüfte sich selbst.
    """
    ziel.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, str(REPO / "tools" / "make_test_ifc.py"), str(ziel)],
                   check=True, capture_output=True)
    return ziel


def mit_einheit(text: str, ersatz: str) -> str:
    """Die Längeneinheit des Prüflings austauschen."""
    assert EINHEIT_METER in text, "Die Fixture hat ihre Einheitenzeile geändert"
    return text.replace(EINHEIT_METER, ersatz)


def si_einheit(vorsatz: str | None) -> str:
    """Eine ``IFCSIUNIT``-Längenzeile mit dem gewünschten SI-Vorsatz (``None`` = keiner)."""
    return f"IFCSIUNIT(*,.LENGTHUNIT.,{f'.{vorsatz}.' if vorsatz else '$'},.METRE.)"


def mit_file_name(text: str, felder: str) -> str:
    """Die ``FILE_NAME``-Zeile durch eine eigene ersetzen (Reihenfolge nach ISO 10303-21)."""
    neu, treffer = re.subn(r"FILE_NAME\(.*?\);", lambda _: f"FILE_NAME({felder});",
                          text, count=1, flags=re.DOTALL)
    assert treffer == 1, "FILE_NAME nicht gefunden — die Fixture hat sich geändert"
    return neu


def mal_tausend(text: str) -> str:
    """Alle Längenzahlen mit 1000 multiplizieren — aus Metern werden Millimeter.

    Das ist die *echte* ArchiCAD-Art: Die Einheitenzuweisung sagt ``.MILLI.`` **und** die
    Koordinaten sind tausendfach grösser. Wer nur eines von beidem ändert, baut den
    kaputten Export nach — auch ein Prüfling, aber ein anderer.
    """
    zeilen = []
    for zeile in text.splitlines(True):
        if any(art in zeile for art in LAENGENZEILEN):
            zeile = re.sub(r"-?\d+\.\d*",
                           lambda m: f"{float(m.group(0)) * 1000.0:.6f}", zeile)
        zeilen.append(zeile)
    return "".join(zeilen)


def schreibe(ordner: Path, name: str, text: str) -> Path:
    """Einen IFC-Prüfling ablegen und seinen Pfad zurückgeben."""
    ziel = ordner / name
    ziel.write_text(text, encoding="utf-8")
    return ziel


def fuellung(mindestens: int) -> str:
    """STEP-Kommentarzeilen, bis die geforderte Bytezahl überschritten ist."""
    zeile = "/* Fuellzeile, damit die Datei ueber das Lesefenster hinauswaechst. */\n"
    return zeile * (mindestens // len(zeile) + 1)


def gltf_daten(generator: str | None = None, *, version: str = "2.0") -> dict:
    """Ein minimales, aber gültiges glTF-Dokument."""
    asset: dict = {"version": version}
    if generator is not None:
        asset["generator"] = generator
    return {"asset": asset, "scene": 0, "scenes": [{"nodes": []}], "nodes": []}


def schreibe_gltf(ziel: Path, daten: dict) -> Path:
    """Das JSON-glTF — die lesbare Spielart."""
    ziel.write_text(json.dumps(daten), encoding="utf-8")
    return ziel


def schreibe_glb(ziel: Path, daten: dict | None = None, *, fassung: int = 2,
                 kennung: int = KENNUNG_JSON, block: bytes | None = None) -> Path:
    """Das binäre glb von Hand: 12-Byte-Kopf, dann Blocklänge, Kennung, Inhalt.

    Von Hand, weil eine Bibliothek dafür eine Lizenzentscheidung wäre (Regel 1) — und
    weil die Fehlerfälle (Fassung 1, erster Block nicht JSON) sich nur so herstellen
    lassen: Ein normkonformer Schreiber weigert sich, sie zu erzeugen.
    """
    inhalt = block if block is not None else json.dumps(daten or {}).encode("utf-8")
    inhalt += b" " * (-len(inhalt) % 4)          # Norm: Blöcke liegen auf 4 Byte
    gesamt = 12 + 8 + len(inhalt)
    ziel.write_bytes(b"glTF" + struct.pack("<II", fassung, gesamt)
                     + struct.pack("<II", len(inhalt), kennung) + inhalt)
    return ziel


def konverter_fehlt() -> bool:
    """Steht das ``.venv-ifc`` mit ifcopenshell bereit?"""
    try:
        return not Path(seams.finde_ifc_python()).exists()
    except seams.SeamError:
        return True


ohne_konverter = pytest.mark.skipif(
    konverter_fehlt(),
    reason=".venv-ifc fehlt — die gemessenen Lagen über die Prozessgrenze entfallen",
)


@pytest.fixture(scope="module")
def basis_ifc(tmp_path_factory) -> str:
    """Der synthetische Testbau als Text — Ausgangspunkt jeder Variante.

    Modulweit: Das Skript läuft einmal statt vierzigmal, und der Text ist deterministisch
    (die GUIDs sind aus laufenden Nummern abgeleitet). Der Dateiname ist bewusst
    unverfänglich. Er landete bis zum 18.08.2026 über ``FILE_NAME`` in der
    Erzeugererkennung — siehe ``test_der_dateiname_bestimmt_die_herkunft_nicht``.
    """
    ordner = tmp_path_factory.mktemp("herkunft-basis")
    return erzeuge_ifc(ordner / "testbau.ifc").read_text(encoding="utf-8")


# ======================================================================================
# A · lies_ifc_kopf — die Einheit, und was None von 1.0 unterscheidet
# ======================================================================================

def test_meter_ohne_vorsatz_ergibt_faktor_eins(tmp_path, basis_ifc):
    """Der Normalfall: METRE ohne Vorsatz heisst Meter, Faktor 1.0 — und das ist gemessen."""
    kopf = lies_ifc_kopf(schreibe(tmp_path, "bau.ifc", basis_ifc))

    assert kopf["format"] == "IFC"
    assert kopf["laengeneinheit"] == "METRE"
    assert kopf["vorsatz"] is None
    assert kopf["meter_je_einheit"] == 1.0


@pytest.mark.parametrize("vorsatz, faktor", [
    ("MILLI", 0.001),
    ("CENTI", 0.01),
    ("KILO", 1000.0),
])
def test_si_vorsatz_wird_zum_faktor(tmp_path, basis_ifc, vorsatz, faktor):
    """Der Vorsatz ist der ganze Unterschied zwischen 8 Metern und 8 Millimetern."""
    text = mit_einheit(basis_ifc, si_einheit(vorsatz))
    kopf = lies_ifc_kopf(schreibe(tmp_path, "bau.ifc", text))

    assert kopf["vorsatz"] == vorsatz
    assert kopf["meter_je_einheit"] == pytest.approx(faktor)
    assert kopf["laengeneinheit"] == "METRE"


def test_unbekannter_vorsatz_ergibt_none_und_nicht_eins(tmp_path, basis_ifc):
    """Der wichtigste Test der Gruppe: Unbekannt heisst ``None``, nicht „vermutlich Meter".

    ``1.0`` wäre eine Behauptung über die Datei, die niemand geprüft hat — und genau die
    Behauptung, aus der der mm-als-m-Fehler entsteht. Ein ``None`` zwingt den Aufrufer,
    sich zu entscheiden; eine 1.0 entscheidet still für ihn.
    """
    text = mit_einheit(basis_ifc, si_einheit("QUATSCHO"))
    kopf = lies_ifc_kopf(schreibe(tmp_path, "bau.ifc", text))

    assert kopf["meter_je_einheit"] is None
    assert kopf["meter_je_einheit"] != 1.0
    assert kopf["vorsatz"] == "QUATSCHO"
    assert any("QUATSCHO" in w for w in kopf["warnungen"]), kopf["warnungen"]


def test_fehlende_einheitenzeile_ergibt_none_und_nicht_eins(tmp_path, basis_ifc):
    """Dieselbe Unterscheidung ohne jede Angabe — schweigen ist nicht dasselbe wie Meter."""
    text = mit_einheit(basis_ifc, EINHEIT_OHNE_LAENGE)
    kopf = lies_ifc_kopf(schreibe(tmp_path, "bau.ifc", text))

    assert kopf["laengeneinheit"] is None
    assert kopf["vorsatz"] is None
    assert kopf["meter_je_einheit"] is None
    assert kopf["meter_je_einheit"] != 1.0
    assert any("1.0" in w for w in kopf["warnungen"]), \
        "Die Warnung soll benennen, warum hier nicht 1.0 eingesetzt wird"


def test_umrechnungseinheit_bleibt_ohne_faktor_mit_begruendung(tmp_path, basis_ifc):
    """Zoll und Fuss: Der Faktor steht in einem verwiesenen Objekt — und wird nicht geraten.

    Ihn aufzulösen hiesse, einen STEP-Parser zu bauen. Das Modul sagt stattdessen, warum
    es nichts sagt; das ist die brauchbarere Auskunft als eine hingeschriebene 1.0.
    """
    text = mit_einheit(basis_ifc, "IFCCONVERSIONBASEDUNIT($,.LENGTHUNIT.,'INCH',#9999)")
    kopf = lies_ifc_kopf(schreibe(tmp_path, "bau.ifc", text))

    assert kopf["meter_je_einheit"] is None
    assert kopf["laengeneinheit"] == "INCH"
    grund = " ".join(kopf["warnungen"])
    assert "INCH" in grund and "STEP-Parser" in grund, kopf["warnungen"]


@pytest.mark.parametrize("schema", ["IFC4", "IFC2X3"])
def test_file_schema_wird_gelesen(tmp_path, basis_ifc, schema):
    """Die Schemafassung entscheidet, was ein Leser erwarten darf — sie wird nicht geraten."""
    text = basis_ifc.replace("FILE_SCHEMA(('IFC4'))", f"FILE_SCHEMA(('{schema}'))")
    kopf = lies_ifc_kopf(schreibe(tmp_path, "bau.ifc", text))

    assert kopf["schema"] == schema
    assert not any("FILE_SCHEMA" in w for w in kopf["warnungen"])


def test_fehlendes_file_schema_steht_in_den_warnungen(tmp_path, basis_ifc):
    """Fehlt die Fassung, bleibt sie offen — und das steht da, statt still zu verschwinden."""
    text = basis_ifc.replace("FILE_SCHEMA(('IFC4'));\n", "")
    kopf = lies_ifc_kopf(schreibe(tmp_path, "bau.ifc", text))

    assert kopf["schema"] is None
    assert any("FILE_SCHEMA" in w for w in kopf["warnungen"]), kopf["warnungen"]


def test_archicad_wird_aus_file_name_erkannt(tmp_path, basis_ifc):
    """Eine ArchiCAD-Zeile im Kopf ergibt ``herkunft == "ArchiCAD"``.

    Die Felderfolge ist die der Norm: name, time_stamp, author, organization,
    preprocessor_version, originating_system, authorization. Der Programmname steht im
    vorletzten Feld.
    """
    text = mit_file_name(basis_ifc, (
        "'testbau.ifc','2026-01-01T00:00:00',('Verfasserin'),('Planungsstelle'),"
        "'IFC4 Add-On 27.0','ARCHICAD-64 27.0.0 GER FULL',''"))
    kopf = lies_ifc_kopf(schreibe(tmp_path, "bau.ifc", text))

    assert kopf["herkunft"] == "ArchiCAD"
    assert "ARCHICAD-64" in kopf["erzeuger"]


def test_unbekannter_erzeuger_ist_kein_fehler(tmp_path, basis_ifc):
    """Ein fremdes Programm ergibt ``herkunft is None`` — gelesen wird die Datei trotzdem.

    Die Herkunft ist eine Zusatzauskunft, keine Voraussetzung: Einheit, Schema und
    Up-Achse stehen unabhängig davon fest, wer die Datei geschrieben hat.
    """
    text = mit_file_name(basis_ifc, (
        "'testbau.ifc','2026-01-01T00:00:00',(''),(''),'',"
        "'Unbekanntes CAD 1.0',''"))
    kopf = lies_ifc_kopf(schreibe(tmp_path, "bau.ifc", text))

    assert kopf["herkunft"] is None
    assert "Unbekanntes CAD 1.0" in kopf["erzeuger"]
    assert kopf["meter_je_einheit"] == 1.0
    assert kopf["schema"] == "IFC4"


def test_up_achse_ist_bei_ifc_belegt_und_zwar_aus_der_norm(tmp_path, basis_ifc):
    """IFC ist Z-up nach ISO 16739 — das folgt aus dem Format, nicht aus dem Erzeuger.

    Der einzige Fall im Projekt, in dem ``up_axis`` aus der Datei folgt statt aus einer
    Zusage. Darum ``BELEGT`` und nicht ``VERMUTET``, und darum gilt es auch für die
    Datei mit unerkanntem Erzeuger.
    """
    kopf = lies_ifc_kopf(schreibe(tmp_path, "bau.ifc", basis_ifc))

    assert kopf["up_axis"] == "Z_UP"
    assert kopf["sicherheit"] == BELEGT
    assert kopf["herkunft"] is None, "Der Prüfling nennt kein bekanntes Programm"
    assert "16739" in kopf["begruendung"]


@pytest.mark.parametrize("inhalt", [
    "Das ist ein Brief und keine IFC.\n",
    '{"asset": {"version": "2.0"}}',
    "",
])
def test_datei_ohne_iso_kennung_wird_abgelehnt(tmp_path, inhalt):
    """Keine STEP-Kennung, keine Deutung — und die Meldung zeigt, was stattdessen dastand.

    Ein blosses „unlesbar" zwänge den Aufrufer, die Datei selbst zu öffnen. Die ersten
    Zeichen im Klartext sagen ihm meist sofort, dass er den falschen Pfad übergeben hat.
    """
    pfad = tmp_path / "bau.ifc"
    pfad.write_text(inhalt, encoding="utf-8")

    with pytest.raises(HerkunftError) as fehler:
        lies_ifc_kopf(pfad)

    assert "ISO-10303-21" in str(fehler.value)
    assert "bau.ifc" in str(fehler.value)


def test_kleine_datei_gilt_als_vollstaendig_gelesen(tmp_path, basis_ifc):
    """Gegenprobe zum Lesefenster: Wer ganz gelesen wurde, trägt keine Fensterwarnung."""
    kopf = lies_ifc_kopf(schreibe(tmp_path, "bau.ifc", basis_ifc))

    assert kopf["vollstaendig_gelesen"] is True
    assert not any("gelesenen Anfang" in w for w in kopf["warnungen"])


def test_grosse_datei_meldet_das_lesefenster(tmp_path, basis_ifc):
    """Über dem Fenster wird nur der Anfang gelesen — und das steht in der Rückgabe.

    Hier ist alles Gesuchte noch im Fenster; gemeldet wird trotzdem, dass nicht die ganze
    Datei angesehen wurde. Eine Auskunft über den Anfang einer Datei ist etwas anderes
    als eine Auskunft über die Datei.
    """
    text = basis_ifc + fuellung(LESEFENSTER_BYTE)
    pfad = schreibe(tmp_path, "bau.ifc", text)
    assert pfad.stat().st_size > LESEFENSTER_BYTE

    kopf = lies_ifc_kopf(pfad)

    assert kopf["vollstaendig_gelesen"] is False
    assert kopf["meter_je_einheit"] == 1.0, "die Einheit stand noch im Fenster"


def test_lesefenster_unterscheidet_nicht_gefunden_von_nicht_vorhanden(tmp_path, basis_ifc):
    """Der Kern der Fensterwarnung: „im gelesenen Anfang nicht gefunden" ≠ „nicht vorhanden".

    Der Prüfling schiebt die Einheitenzeile hinter das Fenster. Heraus kommt kein
    Faktor — aber der Grund ist ein anderer als bei einer Datei ohne Einheit, und
    genau diesen Unterschied muss die Warnung tragen. Sonst suchte ein Mensch den
    Exportfehler in einer Datei, die in Ordnung ist.
    """
    text = basis_ifc.replace("DATA;\n", "DATA;\n" + fuellung(LESEFENSTER_BYTE), 1)
    kopf = lies_ifc_kopf(schreibe(tmp_path, "bau.ifc", text))

    assert kopf["vollstaendig_gelesen"] is False
    assert kopf["meter_je_einheit"] is None, "die Einheitenzeile lag hinter dem Fenster"

    fenster = [w for w in kopf["warnungen"] if "gelesenen Anfang nicht gefunden" in w]
    assert fenster, kopf["warnungen"]
    assert "nicht vorhanden" in fenster[0], \
        "Die Warnung muss beide Lesarten nennen, sonst unterscheidet sie sie nicht"


def test_der_dateiname_bestimmt_die_herkunft_nicht(tmp_path):
    """**Der Fehler, den die Testabnahme dieses Moduls fand — behoben am 18.08.2026.**

    Die erste Fassung sammelte alle nichtleeren Zeichenketten aus ``FILE_NAME`` und nahm
    die letzten drei. In der Testgeometrie sind nur drei Felder gefüllt — Dateiname,
    Zeitstempel, Beschreibung —, also landete der **Dateiname** in der Erkennung: Eine
    Datei namens ``rhino-haus.ifc`` galt als von Rhino erzeugt, obwohl das Erzeugerfeld
    Rhino nirgends nennt.

    **Wer eine Datei umbenannte, änderte ihre Herkunft.** Das war keine ungenaue
    Erkennung, sondern eine falsche. Gelesen wird jetzt nach Position
    (``preprocessor_version`` und ``originating_system``, Index 4 und 5 nach ISO
    10303-21), und der Dateiname bleibt draussen.
    """
    pfad = erzeuge_ifc(tmp_path / "rhino-haus.ifc")

    kopf = lies_ifc_kopf(pfad)

    assert kopf["herkunft"] is None, "Der Dateiname darf die Herkunft nicht bestimmen"
    assert "rhino" not in (kopf["erzeuger"] or "").lower()


def test_autor_und_organisation_bestimmen_die_herkunft_nicht(tmp_path, basis_ifc):
    """Dieselbe Schwäche von der anderen Seite, ebenfalls behoben.

    ``Blenderweg 12`` ist eine Strasse, kein Programm — aber ``blender`` steckt als
    Teilzeichenkette darin. Solange Autor und Organisation in die Erkennung eingingen,
    genügte eine Adresse. Sie gehen nicht mehr ein.

    Der Test prüft **beides**: dass das Freitextfeld ignoriert wird, *und* dass das
    richtige Feld trotzdem gelesen wird. Ohne die zweite Hälfte wäre er auch dann grün,
    wenn die Erkennung gar nichts mehr fände.
    """
    text = mit_file_name(basis_ifc, (
        "'testbau.ifc','2026-01-01T00:00:00',('Muster, Anna','Blenderweg 12'),"
        "('Blenderweg 12'),'IFC add-on 27.0','ARCHICAD-64 27.0.0 GRAPHISOFT',''"))
    kopf = lies_ifc_kopf(schreibe(tmp_path, "bau.ifc", text))

    assert kopf["herkunft"] == "ArchiCAD", "das richtige Feld wird gelesen"
    assert "Blenderweg" not in (kopf["erzeuger"] or ""), \
        "Autor und Organisation gehören nicht in die Erkennung"


def test_ein_komma_im_autorennamen_verschiebt_die_felder_nicht(tmp_path, basis_ifc):
    """Warum die Felder klammertreu zerlegt werden und nicht per ``split(',')``.

    Autor und Organisation sind in ``FILE_NAME`` selbst **Listen**, und ein Autorenname
    der Form „Muster, Anna" trägt ein Komma. Ein naives Trennen verschöbe jedes Feld
    danach — und die Erkennung läse dann Feld 4 und 5 von etwas ganz anderem. Genau
    deshalb liest ``_step_felder`` klammer- und zeichenkettentreu.
    """
    text = mit_file_name(basis_ifc, (
        "'testbau.ifc','2026-01-01T00:00:00',"
        "('Muster, Anna','Zweiter, Bert','Dritter, Cora'),('Buero, AG'),"
        "'IFC add-on 27.0','ARCHICAD-64 27.0.0 GRAPHISOFT',''"))
    kopf = lies_ifc_kopf(schreibe(tmp_path, "bau.ifc", text))

    assert kopf["herkunft"] == "ArchiCAD"
    # Reihenfolge seit dem 18.08.2026: Feld 6 (originating_system) zuerst, dann Feld 5.
    # An 40 echten Dateien trug Feld 5 in zwei von drei Fällen die Exportbibliothek statt
    # des Programms — `DDS_IFC` bei ArchiCAD, `ODA SDAI` bei Revit.
    assert kopf["erzeuger"] == "ARCHICAD-64 27.0.0 GRAPHISOFT | IFC add-on 27.0"


# ======================================================================================
# B · lies_gltf_kopf — und die Ehrlichkeit über die Up-Achse
# ======================================================================================

def test_gltf_und_glb_liefern_bis_auf_das_format_dasselbe(tmp_path):
    """JSON oder binär ist eine Verpackungsfrage — die Auskunft darf nicht daran hängen."""
    daten = gltf_daten("Blender 4.2.1 glTF-Exporter")
    aus_json = lies_gltf_kopf(schreibe_gltf(tmp_path / "bau.gltf", daten))
    aus_binaer = lies_gltf_kopf(schreibe_glb(tmp_path / "bau.glb", daten))

    assert aus_json.pop("format") == "gltf"
    assert aus_binaer.pop("format") == "glb"
    assert aus_json == aus_binaer
    assert aus_json["version"] == "2.0"
    assert aus_json["generator"] == "Blender 4.2.1 glTF-Exporter"


def test_blender_ergibt_eine_vermutung_und_nennt_sie_so(tmp_path):
    """Blender rechnet nach Norm auf Y-up um — aber die Datei sagt es nicht, also: vermutet.

    ``Y_UP`` **mit** ``VERMUTET`` ist eine andere Aussage als ``Y_UP`` allein. Erst der
    zweite Wert hindert ``fordere_up_axis`` daran, sie zu verwenden.
    """
    kopf = lies_gltf_kopf(schreibe_gltf(tmp_path / "bau.gltf",
                                        gltf_daten("Blender 4.2.1 glTF-Exporter")))

    assert kopf["herkunft"] == "Blender"
    assert kopf["up_axis"] == "Y_UP"
    assert kopf["sicherheit"] == VERMUTET


def test_rhino_wird_bewusst_nicht_geraten(tmp_path):
    """Der ehrlichste Eintrag der Registry: Bei Rhino ist die Vermutung nicht schwach,
    sondern unmöglich.

    Rhinos Modellraum ist Z-up, die glTF-Norm schreibt Y-up vor, und der Exporter hat
    dafür einen **Schalter** — was in der Datei steht, hängt an einer Einstellung, die
    die Datei nicht mitteilt. Hier ``Z_UP`` einzutragen wäre kein Wissen, sondern eine
    Münze; darum steht ``None``/``unbekannt``, und die Begründung sagt warum.
    """
    kopf = lies_gltf_kopf(schreibe_gltf(tmp_path / "bau.gltf",
                                        gltf_daten("Rhino 8 glTF exporter")))

    assert kopf["herkunft"] == "Rhino"
    assert kopf["up_axis"] is None
    assert kopf["sicherheit"] == UNBEKANNT
    assert "Schalter" in kopf["begruendung"], \
        "Die Begründung muss den Grund der Unmöglichkeit nennen, nicht nur das Ergebnis"


def test_unbekannter_generator_bleibt_unbekannt(tmp_path):
    """Ohne bekannten Erzeuger und ohne Feld in der Datei bleibt ``up_axis`` Pflichtfeld."""
    kopf = lies_gltf_kopf(schreibe_gltf(tmp_path / "bau.gltf",
                                        gltf_daten("Eigenbau-Exporter 0.1")))

    assert kopf["herkunft"] is None
    assert kopf["up_axis"] is None
    assert kopf["sicherheit"] == UNBEKANNT
    assert "Eigenbau-Exporter 0.1" in kopf["begruendung"]


@pytest.mark.parametrize("generator", [
    "Blender 4.2.1 glTF-Exporter",
    "Rhino 8 glTF exporter",
    "KosmoDraw glb_export_runner",
    "Eigenbau-Exporter 0.1",
    None,
])
def test_jede_rueckgabe_traegt_die_warnung_zum_fehlenden_up_feld(tmp_path, generator):
    """glTF 2.0 kennt kein Up-Achsen-Feld — das gehört in **jede** Antwort, auch die sichere.

    Auch dort, wo eine Vermutung herauskommt: Wer nur ``up_axis`` liest und die Warnung
    nicht, soll sie beim nächsten Blick wieder vorfinden. Eine Auskunft, die ihre eigene
    Herkunft nur manchmal mitliefert, wird als sicher gelesen.
    """
    kopf = lies_gltf_kopf(schreibe_gltf(tmp_path / "bau.gltf", gltf_daten(generator)))

    assert any("kein Up-Achsen-Feld" in w for w in kopf["warnungen"]), kopf["warnungen"]


def test_glb_fassung_eins_wird_nicht_geraten(tmp_path):
    """glb 1 hat einen anderen Aufbau. Ihn zu deuten hiesse, Bytes zu raten."""
    pfad = schreibe_glb(tmp_path / "bau.glb", gltf_daten("Blender"), fassung=1)

    with pytest.raises(HerkunftError, match="Fassung 1"):
        lies_gltf_kopf(pfad)


def test_glb_mit_falschem_erstem_block_wird_abgelehnt(tmp_path):
    """Die Norm verlangt JSON als ersten Block — steht dort BIN, ist die Datei kaputt."""
    pfad = schreibe_glb(tmp_path / "bau.glb", block=b"\x00\x01\x02\x03",
                        kennung=KENNUNG_BIN)

    with pytest.raises(HerkunftError, match="nicht JSON"):
        lies_gltf_kopf(pfad)


def test_zu_kurze_glb_wird_abgelehnt(tmp_path):
    """Ein abgebrochener Übertrag hat die Kennung, aber keinen Block — das ist kein glb."""
    pfad = tmp_path / "bau.glb"
    pfad.write_bytes(b"glTF" + struct.pack("<II", 2, 12))

    with pytest.raises(HerkunftError, match="zu kurz"):
        lies_gltf_kopf(pfad)


def test_glb_mit_kaputtem_json_block_wird_abgelehnt(tmp_path):
    """Kennung und Blockkopf stimmen, der Inhalt nicht — auch das wird gemeldet, nicht gedeutet."""
    pfad = schreibe_glb(tmp_path / "bau.glb", block=b'{"asset": ')

    with pytest.raises(HerkunftError, match="JSON-Block"):
        lies_gltf_kopf(pfad)


def test_gltf_mit_kaputtem_json_wird_abgelehnt(tmp_path):
    """Dieselbe Härte auf dem Textweg: kein JSON, keine Deutung."""
    pfad = tmp_path / "bau.gltf"
    pfad.write_text('{"asset": {"version": ', encoding="utf-8")

    with pytest.raises(HerkunftError):
        lies_gltf_kopf(pfad)


@pytest.mark.parametrize("inhalt", ["[]", "5", '"text"', "null"])
def test_gltf_das_kein_objekt_ist_wird_als_herkunftfehler_gemeldet(tmp_path, inhalt):
    """Gültiges JSON ist noch kein glTF — und ein AttributeError ist keine Auskunft.

    Ein Aufrufer, der ``HerkunftError`` fängt (so steht es im Docstring), bekommt hier
    einen ``AttributeError`` durchgereicht und stürzt an einer Stelle ab, die mit seiner
    Datei nichts zu tun hat.
    """
    pfad = tmp_path / "bau.gltf"
    pfad.write_text(inhalt, encoding="utf-8")

    with pytest.raises(HerkunftError):
        lies_gltf_kopf(pfad)


def test_datei_die_weder_glb_noch_json_ist_wird_abgelehnt(tmp_path):
    """Binärschrott ohne glb-Kennung: als Nichtdeutbares gemeldet, nicht durchgereicht."""
    pfad = tmp_path / "bau.gltf"
    pfad.write_bytes(b"\x00\xff\xfe\x01 kein Text und kein glTF")

    with pytest.raises(HerkunftError):
        lies_gltf_kopf(pfad)


# ======================================================================================
# C · fordere_up_axis — hier wird aus Deutung ein Entscheid
# ======================================================================================

def test_ausdrueckliche_angabe_schlaegt_den_belegten_wert(tmp_path, basis_ifc):
    """Wer die Datei besser kennt als ihr Kopf, darf das sagen — auch gegen ``BELEGT``.

    Die Angabe ist eine Zusage eines Menschen; sie ist die einzige Quelle, die mehr weiss
    als das Format. Sie stillschweigend zu überstimmen wäre dieselbe Bevormundung, gegen
    die das Modul sonst antritt.
    """
    kopf = lies_ifc_kopf(schreibe(tmp_path, "bau.ifc", basis_ifc))
    assert kopf["sicherheit"] == BELEGT and kopf["up_axis"] == "Z_UP"

    assert fordere_up_axis(kopf, angabe="Y") == "Y"


def test_belegter_wert_wird_genommen(tmp_path, basis_ifc):
    """Ohne Angabe zählt der belegte Wert: Er ist eine Messung, keine Gewohnheit."""
    kopf = lies_ifc_kopf(schreibe(tmp_path, "bau.ifc", basis_ifc))

    assert fordere_up_axis(kopf) == "Z"


def test_vermutung_genuegt_nicht_und_steht_in_der_meldung(tmp_path):
    """Die Phase-0-Regel: Eine Vermutung, die sich selbst durchwinkt, ist ein Default.

    Sie wird darum abgelehnt — aber genannt, damit ein Mensch sie bestätigen kann, statt
    selbst nachzuschlagen, was Blender exportiert. Ablehnen ohne Auskunft wäre nur die
    andere Sorte Unfreundlichkeit.
    """
    kopf = lies_gltf_kopf(schreibe_gltf(tmp_path / "bau.gltf",
                                        gltf_daten("Blender 4.2.1 glTF-Exporter")))
    assert kopf["sicherheit"] == VERMUTET

    with pytest.raises(HerkunftError) as fehler:
        fordere_up_axis(kopf)

    meldung = str(fehler.value)
    assert "Y_UP" in meldung, "Die Vermutung muss bestätigbar sein, also genannt werden"
    assert "Default" in meldung
    assert "Blender" in meldung


def test_unbekannte_up_achse_wird_abgelehnt(tmp_path):
    """Bei Rhino gibt es nicht einmal etwas zu bestätigen — der Aufrufer muss angeben."""
    kopf = lies_gltf_kopf(schreibe_gltf(tmp_path / "bau.gltf",
                                        gltf_daten("Rhino 8 glTF exporter")))

    with pytest.raises(HerkunftError) as fehler:
        fordere_up_axis(kopf)

    meldung = str(fehler.value)
    assert "angegeben werden" in meldung
    assert "Vermutet wird" not in meldung, "Es gibt hier nichts zu vermuten"


def test_undeutbare_angabe_wird_nicht_still_geschluckt(tmp_path):
    """Eine Angabe, die weder Y noch Z ist, ist ein Irrtum des Aufrufers — kein Rückfall."""
    kopf = lies_gltf_kopf(schreibe_gltf(tmp_path / "bau.gltf", gltf_daten("Rhino 8")))

    with pytest.raises(ContractError):
        fordere_up_axis(kopf, angabe="oben")


# ======================================================================================
# D · pruefe_einheit_gegen_masse — aus dem Verdacht wird eine Diagnose
# ======================================================================================

@pytest.fixture(scope="module")
def gemessene_lagen(tmp_path_factory) -> dict:
    """Die drei Lagen des Modul-Docstrings, wirklich durch ``seams.ifc_zu_glb`` geschickt.

    Modulweit und in einem Rutsch: Drei Läufe über die Prozessgrenze sind das Teuerste,
    was diese Datei tut, und was danach geprüft wird, sind Zahlen — die ändern sich nicht
    mehr. Nachgerechnet werden kann hier nichts: Ob IfcOpenShell den Einheitenfaktor
    selbst anwendet, ist eine Tatsachenfrage über ein fremdes Programm.
    """
    if konverter_fehlt():
        pytest.skip(".venv-ifc fehlt")

    ordner = tmp_path_factory.mktemp("herkunft-gemessen")
    basis = erzeuge_ifc(ordner / "testbau.ifc").read_text(encoding="utf-8")
    millimeter = mit_einheit(basis, si_einheit("MILLI"))

    varianten = {
        "meter": basis,
        # Echte ArchiCAD-Art: Einheit UND Zahlen sind Millimeter.
        "archicad": mal_tausend(millimeter),
        # Kaputter Export: Einheit sagt Millimeter, die Zahlen sind metergross geblieben.
        "kaputt": millimeter,
    }

    lagen = {}
    for name, text in varianten.items():
        ifc = schreibe(ordner, f"{name}.ifc", text)
        bericht = seams.ifc_zu_glb(ifc, ordner / f"{name}.glb")
        lagen[name] = (lies_ifc_kopf(ifc), bericht["bbox"])
    return lagen


@ohne_konverter
def test_meterdatei_ist_stimmig(gemessene_lagen):
    """Der unauffällige Fall, und er muss unauffällig bleiben: Meter erklärt, Meter gemessen."""
    kopf, bbox = gemessene_lagen["meter"]
    ergebnis = pruefe_einheit_gegen_masse(kopf, bbox)

    assert kopf["meter_je_einheit"] == 1.0
    assert ergebnis["stimmig"] is True
    assert ergebnis["groesste_kante_m"] == pytest.approx(KANTE_M)
    assert ergebnis["erklaerte_einheit"] == "metre"


@ohne_konverter
def test_echte_archicad_art_braucht_keine_umrechnung(gemessene_lagen):
    """Der Befund, der das Modul auf seine heutige Grösse gestutzt hat (gemessen 18.08.2026).

    Eine realistische ArchiCAD-Datei — ``.MILLI.`` **und** tausendfach grössere
    Koordinaten — kommt aus ``seams.ifc_zu_glb`` mit 8,0 m heraus, nicht mit 8000 m.
    IfcOpenShell wendet den Einheitenfaktor selbst an. Die ursprüngliche Annahme des
    Moduls war also falsch, und dieser Test ist der Grund, warum hier **keine**
    Umrechnung eingebaut wurde: Ein Connector, der ein gelöstes Problem noch einmal löst,
    verdoppelt es — und zwar um Faktor 1000.
    """
    kopf, bbox = gemessene_lagen["archicad"]
    ergebnis = pruefe_einheit_gegen_masse(kopf, bbox)

    assert kopf["meter_je_einheit"] == pytest.approx(0.001)
    assert ergebnis["groesste_kante_m"] == pytest.approx(KANTE_M, rel=1e-6), \
        "Aus Millimeter-Koordinaten kam kein Bauwerk von 8000 m — der Konverter rechnet selbst"
    assert ergebnis["stimmig"] is True


@ohne_konverter
def test_kaputter_export_wird_benannt_statt_nur_verdaechtigt(gemessene_lagen):
    """Der Fall, den es wirklich gibt — und die Stelle, an der der Verdacht zur Diagnose wird.

    Der ``torwaechter`` sieht nur 0,008 m und sagt „Verdacht auf Einheitenfehler um
    Faktor 0,001". Mit dem Dateikopf daneben lässt sich sagen, **was** nicht
    zusammenpasst: Die Einheitenzuweisung behauptet Millimeter, die Zahlen standen in
    Metern. Der Unterschied kostet einen Menschen, der nachsieht — oder eben nicht.
    """
    kopf, bbox = gemessene_lagen["kaputt"]
    ergebnis = pruefe_einheit_gegen_masse(kopf, bbox)

    assert ergebnis["stimmig"] is False
    assert ergebnis["groesste_kante_m"] == pytest.approx(KANTE_M * 0.001, rel=1e-6)

    befund = ergebnis["befund"]
    assert "millimetre" in befund, "Die erklärte Einheit gehört in den Befund"
    assert "8 m" in befund, "Der herausgerechnete Wert macht den Befund nachprüfbar"
    assert "in Metern" in befund
    assert "Export" in befund, "Schuld ist der Export, nicht der Konverter — das gehört dazu"


@pytest.mark.parametrize("bbox", [
    None,
    "8x5x3",
    [[0.0, 0.0, 0.0]],
    [[0.0, 0.0, 0.0], [8.0, 5.0]],
    [[0.0, 0.0, 0.0], [8.0, 5.0, "hoch"]],
])
def test_undeutbare_bbox_faellt_kein_urteil(tmp_path, basis_ifc, bbox):
    """``None`` ist kein „nein", sondern „kein Urteil" — dieselbe Haltung wie in ``geometrie_qa``.

    Ein ``False`` hier hiesse: die Einheit passt nicht zu den Massen. Das wäre eine
    Aussage über die Datei, die aus einer unlesbaren bbox gar nicht folgt — und der
    Aufrufer suchte den Fehler am falschen Ort.
    """
    kopf = lies_ifc_kopf(schreibe(tmp_path, "bau.ifc", basis_ifc))
    ergebnis = pruefe_einheit_gegen_masse(kopf, bbox)

    assert ergebnis["stimmig"] is None
    assert ergebnis["stimmig"] is not False
    assert ergebnis["groesste_kante_m"] is None


def test_ohne_lesbare_einheit_faellt_kein_urteil(tmp_path, basis_ifc):
    """Ohne Einheit fehlt die eine Hälfte des Vergleichs — die Masse allein genügen nicht.

    Der Torwächter bleibt dann die einzige Instanz, und er kann nur den Verdacht äussern.
    Genau das soll der Befund auch sagen, statt Stillschweigen zu üben.
    """
    text = mit_einheit(basis_ifc, EINHEIT_OHNE_LAENGE)
    kopf = lies_ifc_kopf(schreibe(tmp_path, "bau.ifc", text))

    ergebnis = pruefe_einheit_gegen_masse(kopf, [[0.0, 0.0, 0.0], [8.0, 5.0, 3.25]])

    assert ergebnis["stimmig"] is None
    assert ergebnis["groesste_kante_m"] == pytest.approx(KANTE_M)
    assert "Torwächter" in ergebnis["befund"]


# ======================================================================================
# E · Die Registry — jeder Eintrag muss sich rechtfertigen
# ======================================================================================

@pytest.mark.parametrize("eintrag", HERKUENFTE, ids=lambda h: h.name)
def test_jeder_eintrag_traegt_eine_begruendung(eintrag):
    """``beleg`` ist Pflicht, nicht Schmuck: Ohne ihn wäre die Registry eine Meinungsliste.

    Wer später eine echte Datei misst, muss sehen können, worauf der bisherige Eintrag
    beruhte — sonst weiss er nicht, ob er etwas widerlegt oder etwas bestätigt.
    """
    assert eintrag.beleg.strip(), f"{eintrag.name} behauptet etwas ohne Begründung"
    assert len(eintrag.beleg.strip()) > 20, f"{eintrag.name}: {eintrag.beleg!r} ist keine Begründung"


@pytest.mark.parametrize("eintrag", [h for h in HERKUENFTE if h.sicherheit == BELEGT],
                         ids=lambda h: h.name)
def test_belegte_eintraege_berufen_sich_auf_die_norm(eintrag):
    """``BELEGT`` darf nur aus dem Format folgen, nie aus einer Herstellergewohnheit.

    Der Unterschied ist der ganze Sinn des Feldes: Ein belegter Wert wird von
    ``fordere_up_axis`` ohne Rückfrage verwendet. Käme er aus einer Gewohnheit, wäre das
    ein Default mit besserer Begründung — genau das, was Phase 0 verhindern wollte.
    """
    assert "16739" in eintrag.beleg, \
        f"{eintrag.name} gilt als belegt, nennt aber keine Norm: {eintrag.beleg!r}"
    assert eintrag.up_axis == "Z_UP", "Die IFC-Norm kennt nur Z-up"


@pytest.mark.parametrize("eintrag", HERKUENFTE, ids=lambda h: h.name)
def test_kennungen_sind_kleingeschrieben(eintrag):
    """Verglichen wird gegen ``text.lower()`` — eine Grossbuchstabe machte den Eintrag tot.

    Und zwar lautlos: Der Erzeuger würde einfach nie erkannt, und bei glTF hiesse das
    ``unbekannt`` statt einer Vermutung. Ein Fehler, den niemand als Fehler sieht.
    """
    for kennung in eintrag.kennungen:
        assert kennung == kennung.lower(), f"{eintrag.name}: {kennung!r} wird nie treffen"
        assert kennung.strip() == kennung and kennung, f"{eintrag.name}: {kennung!r}"


def test_keine_kennung_passt_auf_zwei_eintraege():
    """Kennungen dürfen sich nicht so überschneiden, dass die Reihenfolge entscheidet.

    ``_erkenne`` nimmt den ersten Treffer in der Aufzählungsreihenfolge. Wäre eine
    Kennung in zwei Einträgen enthalten, hinge die Herkunft — und über sie die Up-Achse —
    daran, wer in der Tabelle weiter oben steht. Das ist keine Eigenschaft der Datei.
    """
    for eintrag in HERKUENFTE:
        for kennung in eintrag.kennungen:
            treffer = [h.name for h in HERKUENFTE
                       if any(k in kennung for k in h.kennungen)]
            assert treffer == [eintrag.name], \
                f"{kennung!r} passt auf mehrere Einträge: {treffer}"


def test_unbekannte_sicherheit_kommt_in_der_registry_nicht_vor():
    """Nur die drei benannten Stufen — eine vierte wäre eine Aussage, die niemand auswertet."""
    for eintrag in HERKUENFTE:
        assert eintrag.sicherheit in (BELEGT, VERMUTET, UNBEKANNT), eintrag


def test_unbekannte_eintraege_tragen_keine_up_achse():
    """Wer ``UNBEKANNT`` meldet, darf keine Achse mitliefern — sonst wird sie doch gelesen.

    Der Rhino-Eintrag ist der Prüfstein: Ein ``Z_UP`` daneben, und irgendein Aufrufer
    nähme es irgendwann, weil es dasteht.
    """
    for eintrag in HERKUENFTE:
        if eintrag.sicherheit == UNBEKANNT:
            assert eintrag.up_axis is None, f"{eintrag.name} weiss es angeblich doch"


# ======================================================================================
# F · deute — entschieden wird am Inhalt, nicht an der Endung
# ======================================================================================

def test_deute_erkennt_ifc_trotz_falscher_endung(tmp_path, basis_ifc):
    """Eine Endung ist eine Behauptung des Benennenden, der Dateianfang eine des Erzeugers."""
    pfad = schreibe(tmp_path, "bau.glb", basis_ifc)

    kopf = deute(pfad)

    assert kopf["format"] == "IFC"
    assert kopf["meter_je_einheit"] == 1.0


def test_deute_erkennt_glb_trotz_falscher_endung(tmp_path):
    """Gegenprobe: Eine binäre glb, die ``.ifc`` heisst, wird trotzdem als glb gelesen."""
    pfad = schreibe_glb(tmp_path / "bau.ifc", gltf_daten("Blender 4.2.1 glTF-Exporter"))

    kopf = deute(pfad)

    assert kopf["format"] == "glb"
    assert kopf["herkunft"] == "Blender"


def test_deute_meldet_eine_fehlende_datei(tmp_path):
    """Kein Pfad, keine Auskunft — und der Fehler trägt den Namen dieses Moduls."""
    with pytest.raises(HerkunftError):
        deute(tmp_path / "gibtsnicht.ifc")


def test_modul_kommt_ohne_ifcopenshell_und_ohne_numpy_aus():
    """Regel 1 und 2 im Quelltext nachgesehen: Der Kopfleser lebt diesseits der Prozessgrenze.

    Er wird gebraucht, **bevor** entschieden ist, ob konvertiert wird. Ein Import von
    ``ifcopenshell`` machte ihn von einem fremden venv abhängig — und holte GPL-CGAL in
    den Produktprozess.
    """
    quelle = Path(hk.__file__).read_text(encoding="utf-8")

    for verboten in ("import ifcopenshell", "import numpy", "import bpy", "import trimesh"):
        assert verboten not in quelle, f"{verboten} steht in herkunft.py"
