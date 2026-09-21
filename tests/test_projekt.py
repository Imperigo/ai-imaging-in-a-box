"""Das Projekt — **die Mappe, in der die Arbeit einer Person zusammenbleibt.**

Diese Sammlung prüft nicht, ob Daten gespeichert werden. Sie prüft die fünf Stellen, an
denen eine Projektverwaltung still Schaden anrichtet:

1. Sie schluckt das Modell und hat damit eine zweite Wahrheit auf der Platte.
2. Sie repariert beim Öffnen, und niemand kann danach zwei Stände vergleichen.
3. Sie legt ein Bild ohne Urteilsfeld ab — das liest sich später wie «war in Ordnung».
4. Sie schreibt einen Benutzernamen in eine Datei, die ins öffentliche Repo kann.
5. Sie überschreibt ein vorhandenes Projekt, weil danach gefragt wurde.

**Ohne GPU, ohne Blender, ohne Netz.** Jede Datei entsteht hier aus ein paar Bytes.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiimaging import projekt


@pytest.fixture
def ifc(tmp_path):
    """Eine kleine, gültige IFC — mehr sieht der Einlass nicht an (Regel 3: synthetisch)."""
    pfad = tmp_path / "modelle" / "haus.ifc"
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(
        "ISO-10303-21;\n"
        "HEADER;\n"
        "FILE_DESCRIPTION((''),'');\n"
        "FILE_NAME('haus.ifc','2026-09-21T00:00:00',(''),(''),'','Testfixture','');\n"
        "FILE_SCHEMA(('IFC4'));\n"
        "ENDSEC;\n"
        "DATA;\n"
        "#1=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);\n"
        "ENDSEC;\nEND-ISO-10303-21;\n", encoding="utf-8")
    return pfad


# --------------------------------------------------------- 1 · verweisen statt schlucken

def test_das_modell_wird_vermerkt_und_nicht_kopiert(tmp_path, ifc):
    """*Eine Kopie im Projektordner wäre eine zweite Wahrheit auf der Platte.*

    Wer danach die eine ändert, hat zwei Gebäude — und keines der beiden weiss vom
    anderen.
    """
    wurzel = tmp_path / "projekt"
    p = projekt.neu(wurzel, ifc)
    projekt.speichere(p, wurzel)

    dateien = [d.name for d in wurzel.iterdir()]
    assert dateien == [projekt.PROJEKTDATEI], f"nur die Projektdatei, war {dateien}"
    assert p["modell"]["pfad"].endswith("haus.ifc")


def test_der_befund_des_einlasses_wandert_ins_projekt(tmp_path, ifc):
    """Was über Format und Hochachse feststand, als das Projekt entstand.

    Später ist das nicht mehr zu rekonstruieren: Eine Datei, die inzwischen ersetzt wurde,
    sagt nichts mehr darüber, was in ihrer Vorgängerin stand.
    """
    p = projekt.neu(tmp_path / "projekt", ifc)
    e = p["modell"]["einlass"]
    assert e["brauchbar"] is True
    assert "IFC" in (e["format"] or "")
    assert e["hochachse"], "bei IFC folgt sie aus dem Format"


def test_ein_unbrauchbares_modell_ist_ein_befund_und_kein_fehler(tmp_path):
    """*Eine Absage ohne Ausweg ist eine halbe Auskunft* — hier steht der Ausweg im Projekt.

    Wer ein Projekt anlegt, hat eine Absicht. Ihm die Mappe zu verweigern nimmt ihm auch
    die Stelle, an der die Begründung stünde.
    """
    bild = tmp_path / "modell.glb"
    bild.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 64)     # eine umbenannte JPG

    p = projekt.neu(tmp_path / "projekt", bild)

    assert p["modell"]["einlass"]["brauchbar"] is False
    assert p["modell"]["einlass"]["naechster_schritt"], "der Ausweg gehört dazu"


# --------------------------------------------------------------- 2 · nichts reparieren

def test_ein_unveraendertes_modell_wird_als_solches_gemeldet(tmp_path, ifc):
    wurzel = tmp_path / "projekt"
    projekt.speichere(projekt.neu(wurzel, ifc), wurzel)

    auf = projekt.oeffne(wurzel)
    assert auf["modell_stand"] == projekt.MODELL_UNVERAENDERT


def test_ein_geaendertes_modell_haelt_das_projekt_nicht_an_sondern_meldet_es(tmp_path, ifc):
    """**Der Kern dieses Moduls.**

    Ein Projekt, dessen Modell sich geändert hat, öffnet sich normal. Die bisherigen
    Messungen bleiben stehen — sie gehören zum alten Stand und gelten dafür weiter.

        *Wer beim Öffnen still neu rechnet, nimmt dem Benutzer die Möglichkeit, zwei
        Stände zu vergleichen — und das ist der häufigste Grund, überhaupt zwei zu haben.*
    """
    wurzel = tmp_path / "projekt"
    p = projekt.neu(wurzel, ifc)
    projekt.vermerke_bild(p, bild="a.png", schicht="geometrielayer", urteil=True)
    projekt.speichere(p, wurzel)

    ifc.write_text(ifc.read_text(encoding="utf-8") + "\n/* ein Geschoss mehr */\n",
                   encoding="utf-8")

    auf = projekt.oeffne(wurzel)
    assert auf["modell_stand"] == projekt.MODELL_VERAENDERT
    assert "nichts neu gerechnet" in auf["modell_grund"]
    assert len(auf["projekt"]["bilder"]) == 1, "das alte Urteil bleibt stehen"
    assert auf["projekt"]["bilder"][0]["geometrie_bestanden"] is True


def test_ein_verschwundenes_modell_ist_kein_absturz(tmp_path, ifc):
    wurzel = tmp_path / "projekt"
    projekt.speichere(projekt.neu(wurzel, ifc), wurzel)
    ifc.unlink()

    auf = projekt.oeffne(wurzel)
    assert auf["modell_stand"] == projekt.MODELL_FEHLT
    assert "weiterhin gültig" in auf["modell_grund"]


def test_der_fingerabdruck_sagt_selbst_wie_genau_er_ist(tmp_path, ifc):
    """*Eine Prüfsumme ohne Angabe, worüber sie läuft, behauptet mehr, als sie weiss.*

    Bei kleinen Dateien wird alles gelesen, bei grossen nur Anfang und Ende. Der
    Unterschied steht im Abdruck, nicht in einem Kommentar.
    """
    klein = projekt.fingerabdruck(ifc)
    assert klein["art"] == "voll"
    assert klein["summe"] and klein["groesse_byte"] == ifc.stat().st_size

    gross = tmp_path / "gross.bin"
    gross.write_bytes(b"A" * (projekt.VOLLE_PRUEFUNG_BIS_BYTE + 1))
    assert projekt.fingerabdruck(gross)["art"] == "anfang_und_ende"


def test_die_groesse_geht_in_den_abdruck_ein(tmp_path):
    """Sonst sähe eine abgeschnittene Übertragung aus wie die Datei selbst.

    **Diese Probe hat am 21.09.2026 zuerst an der Sache vorbeigeprüft**, und das steht
    hier, weil es lehrreicher ist als die Probe selbst: Sie benutzte zwei *kleine*
    Dateien. Dort wird die ganze Datei gelesen, die Summen unterscheiden sich schon am
    Inhalt — und die Mutationsprobe «die Grösse fliesst nicht ein» ging **grün** durch.

        *Ein Wächter, der nur den Weg bewacht, den man beim Schreiben im Kopf hatte,
        bewacht den anderen nicht.*

    Geprüft wird jetzt der Weg, auf dem es darauf ankommt: **Anfang und Ende gleich,
    Länge verschieden.** Genau so sieht ein abgebrochener Export aus.
    """
    kopf, fuss = b"KKKK", b"FFFF"
    kurz, lang = tmp_path / "a.bin", tmp_path / "b.bin"
    kurz.write_bytes(kopf + b"\x00" * 10 + fuss)
    lang.write_bytes(kopf + b"\x00" * 20 + fuss)

    # BEIDE Grenzen werden heruntergesetzt, und beide sind noetig:
    #   `voll_bis_byte`  damit ueberhaupt der Weg «Anfang und Ende» genommen wird,
    #   `fenster_byte`   damit das Fenster KLEINER ist als die Datei. Mit dem Vorgabewert
    #                    von 64 KiB laese es zweimal die ganze Datei — und dann
    #                    unterscheiden sich die Summen schon am Inhalt, und diese Probe
    #                    saehe gruen aus, ohne etwas zu zeigen.
    klein = dict(voll_bis_byte=8, fenster_byte=4)
    a = projekt.fingerabdruck(kurz, **klein)
    b = projekt.fingerabdruck(lang, **klein)

    assert a["art"] == b["art"] == "anfang_und_ende", "sonst prüft diese Probe den andern Weg"
    assert a["summe"] != b["summe"], (
        "gleicher Anfang, gleiches Ende, andere Länge — ohne die Grösse im Abdruck wäre "
        "ein abgebrochener Export von der ganzen Datei nicht zu unterscheiden")


# ------------------------------------------------------------- 3 · das Urteil ist Pflicht

def test_ein_ungeprueftes_bild_traegt_das_ausdruecklich(tmp_path, ifc):
    """``None`` heisst NICHT GEMESSEN — und nie «war wohl in Ordnung».

    Ein Eintrag **ohne** Urteilsfeld liest sich später wie eine bestandene Prüfung. Darum
    steht immer eines da.
    """
    p = projekt.neu(tmp_path / "projekt", ifc)
    projekt.vermerke_bild(p, bild="a.png", schicht="ai-imaging-layer", urteil=None)

    eintrag = p["bilder"][0]
    assert "geometrie_bestanden" in eintrag
    assert eintrag["geometrie_bestanden"] is None
    assert eintrag["geometrie_gemessen"] is False


def test_das_geerbte_urteil_steht_nie_im_feld_des_eigenen(tmp_path, ifc):
    """Die bindende Auflage aus E20: *Ein geerbtes Urteil ist kein eigenes.*

    Ein Feld, in dem einmal das eigene und einmal das fremde Urteil steht, ist genau der
    Fehler, gegen den dieses Projekt seit Wochen anschreibt.
    """
    p = projekt.neu(tmp_path / "projekt", ifc)
    projekt.vermerke_bild(
        p, bild="variante-3.png", schicht="ai-imaging-layer", urteil=None,
        basis={"bild": "a.png", "geometrie_bestanden": True})

    eintrag = p["bilder"][0]
    assert eintrag["geometrie_bestanden"] is None, "das EIGENE Urteil fehlt"
    assert eintrag["basis"]["geometrie_bestanden"] is True, "das GEERBTE steht daneben"


@pytest.mark.parametrize("unsinn", ["bestanden", 1, 0, 0.9, "nicht gemessen", []])
def test_ein_urteil_das_keines_ist_wird_abgewiesen(tmp_path, ifc, unsinn):
    """Drei Antworten gibt es, eine vierte nicht.

    **Die 1 und die 0 stehen hier nicht zur Vollständigkeit.** In Python gilt ``1 == True``
    und ``0 == False``; eine Prüfung mit ``in (True, False, None)`` lässt beide durch. Sie
    landeten dann als Urteil in der Projektdatei und sähen dort aus wie eine Entscheidung.
    Genau das ist beim ersten Lauf dieser Probe passiert.

        *Eine Zahl, die sich als Urteil ausgibt, ist schlimmer als gar keines: Sie
        beantwortet die Frage, ohne sie gestellt zu haben.*
    """
    p = projekt.neu(tmp_path / "projekt", ifc)
    with pytest.raises(projekt.ProjektError):
        projekt.vermerke_bild(p, bild="a.png", schicht="geometrielayer", urteil=unsinn)


def test_eine_erfundene_schicht_wird_abgewiesen(tmp_path, ifc):
    """Es gibt zwei Stufen (E20), und eine dritte wäre stillschweigend eine neue Regel."""
    p = projekt.neu(tmp_path / "projekt", ifc)
    with pytest.raises(projekt.ProjektError):
        projekt.vermerke_bild(p, bild="a.png", schicht="irgendwas", urteil=True)


# ------------------------------------------------------------------------ 4 · Regel 3

def test_ein_benutzername_kommt_nicht_in_die_projektdatei(tmp_path, ifc):
    """**Regel 3 wird beim Schreiben durchgesetzt, nicht erwähnt.**

    Und die Zahl der Ersetzungen steht in der Datei: *Eine Säuberung, die nicht sagt, dass
    sie stattfand, ist von keiner Säuberung zu unterscheiden.*
    """
    wurzel = tmp_path / "projekt"
    p = projekt.neu(wurzel, ifc)
    p["einstellungen"]["ablage"] = "/home/vorname-nachname/entwuerfe/bilder"
    ziel = projekt.speichere(p, wurzel)

    text = ziel.read_text(encoding="utf-8")
    assert "vorname-nachname" not in text
    assert "<nutzer>" in text
    assert json.loads(text)["regel3_ersetzt"] >= 1, "die Säuberung sagt, dass sie stattfand"


# ------------------------------------------------------- 5 · nichts stillschweigend weg

def test_ein_vorhandenes_projekt_wird_nicht_ueberschrieben(tmp_path, ifc):
    """*Ein Datenverlust ohne Rückfrage ist kein Komfort.*"""
    wurzel = tmp_path / "projekt"
    projekt.speichere(projekt.neu(wurzel, ifc), wurzel)

    with pytest.raises(projekt.ProjektError) as fehler:
        projekt.neu(wurzel, ifc)
    assert "oeffne" in str(fehler.value), "die Absage nennt den richtigen Weg"


def test_ein_fremdes_schema_wird_nicht_versuchsweise_gelesen(tmp_path, ifc):
    """*Was dabei fehlte, fiele niemandem auf.*"""
    wurzel = tmp_path / "projekt"
    projekt.speichere(projekt.neu(wurzel, ifc), wurzel)
    datei = wurzel / projekt.PROJEKTDATEI
    inhalt = json.loads(datei.read_text(encoding="utf-8"))
    inhalt["schema"] = "visbox.projekt/v9"
    datei.write_text(json.dumps(inhalt), encoding="utf-8")

    with pytest.raises(projekt.ProjektError, match="Projektformat"):
        projekt.oeffne(wurzel)


def test_kein_projekt_am_ort_ist_ein_satz_und_kein_traceback(tmp_path):
    with pytest.raises(projekt.ProjektError, match="kein Projekt"):
        projekt.oeffne(tmp_path / "leer")


def test_die_projektdatei_ist_lesbarer_text(tmp_path, ifc):
    """Jemand muss hineinsehen können, ohne dieses Programm zu starten.

    Auch in zehn Jahren, auch ohne Python.
    """
    wurzel = tmp_path / "projekt"
    ziel = projekt.speichere(projekt.neu(wurzel, ifc), wurzel)
    text = ziel.read_text(encoding="utf-8")
    assert text.startswith("{\n"), "eingerückt, nicht in einer Zeile"
    assert '"modell"' in text and '"einstellungen"' in text
    assert text.endswith("\n")


# ------------------------------------------ Die Skizze — die Eingabe des Entwurfsmodus
#
# E23 (Owner-Entscheid 21.09.2026): Das AI-Imaging darf Volumen ERFINDEN, nach einer ins
# Bild gezeichneten Skizze. Die Skizze ist damit die Bestellung, und sie gehoert in die
# Mappe wie das Bild, das daraus wird.

def _mappe(tmp_path):
    modell = tmp_path / "m.glb"
    modell.write_bytes(b"glTF\x02\x00\x00\x00")
    return projekt.neu(tmp_path, modell, name="Probe")


def test_eine_frische_mappe_fuehrt_die_skizzenliste_schon(tmp_path):
    """Sie steht von Anfang an leer da und entsteht nicht erst beim ersten Eintrag.

    *Ein Feld, das mal fehlt und mal nicht, zwingt jeden Leser zu einer
    Fallunterscheidung, die nichts bedeutet.*
    """
    assert _mappe(tmp_path)["skizzen"] == []


def test_eine_skizze_traegt_ihre_unterlage(tmp_path):
    """*Eine Zeichnung ohne ihre Unterlage ist ein Strichbild. Erst zusammen sind sie ein
    Entwurf.*"""
    p = _mappe(tmp_path)
    projekt.vermerke_skizze(p, skizze="s1.png", ueber="ansicht-1.png",
                            bemerkung="Anbau nach Sueden")

    eintrag = p["skizzen"][0]
    assert eintrag["skizze"] == "s1.png"
    assert eintrag["ueber"] == "ansicht-1.png"
    assert eintrag["bemerkung"] == "Anbau nach Sueden"


def test_der_stand_ist_von_anfang_an_offen_und_nicht_leer(tmp_path):
    """*Gezeichnet ist nicht gerechnet.* Eine Skizze ohne Zustand sieht nach zwei Wochen
    aus wie erledigt."""
    p = _mappe(tmp_path)
    projekt.vermerke_skizze(p, skizze="s1.png")

    assert p["skizzen"][0]["stand"] == projekt.SKIZZE_OFFEN
    assert p["skizzen"][0]["ergebnis"] is None


def test_ein_erfundener_stand_wird_abgewiesen(tmp_path):
    """Ein vierter Zustand waere eine Auskunft, die niemand einloesen kann."""
    p = _mappe(tmp_path)
    with pytest.raises(projekt.ProjektError):
        projekt.vermerke_skizze(p, skizze="s1.png", stand="fast_fertig")


def test_ohne_unterlage_ist_erlaubt_und_heisst_wirklich_ohne(tmp_path):
    """`None` heisst hier **ohne Unterlage** und nicht *unbekannt* — wer auf etwas
    zeichnet, weiss, worauf. Das ist die eine Stelle, an der `None` in diesem Projekt
    NICHT «nicht gemessen» bedeutet, und darum steht es im Docstring."""
    p = _mappe(tmp_path)
    projekt.vermerke_skizze(p, skizze="s1.png", ueber=None)

    assert p["skizzen"][0]["ueber"] is None


def test_eine_leere_unterlage_ist_etwas_anderes_als_keine(tmp_path):
    """Eine leere Zeichenkette saehe in der Mappe aus wie `None` und waere es nicht.
    Zwei Sachverhalte, die gleich aussehen, sind genau der Fehler, gegen den E20 steht."""
    p = _mappe(tmp_path)
    for leer in ("", "   "):
        with pytest.raises(projekt.ProjektError):
            projekt.vermerke_skizze(p, skizze="s1.png", ueber=leer)


def test_eine_skizze_ohne_namen_wird_abgewiesen(tmp_path):
    p = _mappe(tmp_path)
    for leer in ("", "  ", None):
        with pytest.raises(projekt.ProjektError):
            projekt.vermerke_skizze(p, skizze=leer)


def test_mehrere_skizzen_behalten_ihre_reihenfolge(tmp_path):
    """Eine Variantenstudie ist eine Reihe. Wer sie umsortiert, nimmt ihr, was sie zeigt."""
    p = _mappe(tmp_path)
    for i in range(3):
        projekt.vermerke_skizze(p, skizze=f"s{i}.png", ueber="a.png")

    assert [s["skizze"] for s in p["skizzen"]] == ["s0.png", "s1.png", "s2.png"]


def test_skizzen_ueberleben_das_speichern_und_oeffnen(tmp_path):
    """Sonst waere der Eintrag eine Angabe, die nur bis zum Schliessen des Fensters gilt."""
    p = _mappe(tmp_path)
    projekt.vermerke_skizze(p, skizze="s1.png", ueber="a.png", bemerkung="mehr Volumen")
    projekt.speichere(p, tmp_path)

    wieder = projekt.oeffne(tmp_path)["projekt"]
    assert wieder["skizzen"][0]["bemerkung"] == "mehr Volumen"


# ------------------------- Pfade in der Mappe — der Fehler, den drei Wochen niemand sah
#
# GEFUNDEN AM 21.09.2026 VON BEWEIS 31, beim ersten Lauf ausserhalb von `/tmp`.
#
# Die Mappe wird beim Speichern von Benutzernamen befreit (Regel 3, dieses Repo ist
# oeffentlich). Aus einem Heimatverzeichnis wurde dabei `/home/<nutzer>/…` — ein Pfad,
# der auf NICHTS mehr zeigt. Jedes Projekt meldete beim naechsten Oeffnen «Modell fehlt»,
# und `rechne` verweigerte die Arbeit mit «keine umgewandelte Geometrie».
#
# Aufgefallen ist es nie, weil JEDE Probe unter `tmp_path` laeuft — und der liegt unter
# `/tmp` und traegt keinen Benutzernamen.
#
#     Zum dritten Mal in diesem Projekt sass der Fehler genau zwischen der Attrappe und
#     der echten Datei.
#
# Diese Proben fahren darum ausdruecklich unter einem Pfad MIT Benutzernamen.

@pytest.fixture
def heimatartig(tmp_path):
    """Ein Ordner, dessen Pfad aussieht wie ein Heimatverzeichnis.

    Er liegt weiterhin unter `tmp_path` — geprueft wird nicht das Dateisystem, sondern
    die Saeuberung, und die schaut auf die **Zeichenkette**.
    """
    ort = tmp_path / "home" / "jemand" / "bauten"
    ort.mkdir(parents=True)
    return ort


def test_der_modellpfad_ueberlebt_das_speichern(heimatartig):
    """**Die Probe, die drei Wochen gefehlt hat.**

    Nach `speichere`/`oeffne` muss das Modell wiedergefunden werden — sonst ist jede
    Mappe beim zweiten Öffnen leer.
    """
    modell = heimatartig / "haus.ifc"
    modell.write_bytes(b"ISO-10303-21;\nENDSEC;\n")
    mappe = heimatartig / "projekt"

    p = projekt.neu(mappe, modell, name="Probe")
    projekt.speichere(p, mappe)

    auf = projekt.oeffne(mappe)
    assert auf["modell_stand"] == projekt.MODELL_UNVERAENDERT, auf["modell_grund"]


def test_kein_benutzername_landet_in_der_mappe(heimatartig):
    """Und die andere Hälfte: Regel 3 gilt weiter. Beides zugleich, nicht eines davon.

    *Ein Pfad, der funktioniert und den Benutzernamen trägt, wäre keine Lösung — er wäre
    der Fehler in die andere Richtung.*
    """
    modell = heimatartig / "haus.ifc"
    modell.write_bytes(b"ISO-10303-21;\n")
    mappe = heimatartig / "projekt"

    p = projekt.neu(mappe, modell)
    pfad = projekt.speichere(p, mappe)
    text = pfad.read_text(encoding="utf-8")

    assert "jemand" not in text, "der Benutzername steht in der Mappe"
    assert "<nutzer>" not in text, (
        "ein ersetzter Benutzername heisst, dass ein absoluter Pfad gespeichert wurde — "
        "und der zeigt danach auf nichts")


def test_der_pfad_steht_relativ_zur_mappe_darin(heimatartig):
    """Was in der Datei steht, ist nachlesbar und kurz: `../haus.ifc`.

    Die Mappe wird dadurch **umziehbar** — wer sie samt Modell kopiert, nimmt eine
    gültige Angabe mit.
    """
    modell = heimatartig / "haus.ifc"
    modell.write_bytes(b"ISO-10303-21;\n")
    mappe = heimatartig / "projekt"

    p = projekt.neu(mappe, modell)
    assert p["modell"]["pfad"] == "../haus.ifc"


def test_die_mappe_laesst_sich_mitsamt_modell_verschieben(heimatartig, tmp_path):
    """**Die Eigenschaft, die als Nebenwirkung entstanden ist — und die zählt.**

    Wer den ganzen Ordner woandershin kopiert, hat weiterhin ein gültiges Projekt. Mit
    absoluten Pfaden wäre es beim ersten Verschieben kaputt gewesen.
    """
    import shutil

    modell = heimatartig / "haus.ifc"
    modell.write_bytes(b"ISO-10303-21;\n")
    mappe = heimatartig / "projekt"
    projekt.speichere(projekt.neu(mappe, modell), mappe)

    anderswo = tmp_path / "stick" / "bauten"
    shutil.copytree(heimatartig, anderswo)

    auf = projekt.oeffne(anderswo / "projekt")
    assert auf["modell_stand"] == projekt.MODELL_UNVERAENDERT, auf["modell_grund"]


def test_ein_geaendertes_modell_faellt_weiterhin_auf(heimatartig):
    """Die Gegenprobe. Ohne sie wäre ein `oeffne`, das IMMER «unverändert» sagt, ebenso
    grün — und der Fingerabdruck umsonst gerechnet."""
    modell = heimatartig / "haus.ifc"
    modell.write_bytes(b"ISO-10303-21;\n")
    mappe = heimatartig / "projekt"
    projekt.speichere(projekt.neu(mappe, modell), mappe)

    modell.write_bytes(b"ISO-10303-21;\nETWAS ANDERES\n")

    assert projekt.oeffne(mappe)["modell_stand"] == projekt.MODELL_VERAENDERT


def test_ein_absoluter_pfad_ohne_gemeinsamen_stamm_bleibt_absolut():
    """Der Fall ohne relativen Pfad — ein anderes Laufwerk unter Windows.

    Dann bleibt es absolut, die Säuberung greift wie bisher, und das Projekt meldet beim
    Öffnen ehrlich, dass es das Modell nicht findet. *Unschön und wahr ist besser als
    schön und falsch.*
    """
    assert projekt.pfad_fuer_die_mappe("/ganz/woanders/haus.ifc", "/mappe").startswith("..")


def test_loese_pfad_macht_aus_leer_nichts(tmp_path):
    """`""` ist keine Datei und wird auch nicht zu einer — sonst zeigte ein leeres Feld
    plötzlich auf den Projektordner selbst."""
    assert str(projekt.loese_pfad("", tmp_path)) == "."
    assert str(projekt.loese_pfad(None, tmp_path)) == "."


def test_der_fingerabdruck_haengt_am_INHALT_und_nicht_an_der_uhr(heimatartig):
    """**Geprueft, weil es auf einem Netzlaufwerk darauf ankommt.**

    Dort ist die Zeitangabe einer Datei grob (oft zwei Sekunden) und kommt von der Uhr des
    Servers. Haengt die Wiedererkennung daran, sieht ein geaendertes Modell unveraendert
    aus — und das Urteil gilt fuer ein anderes Gebaeude.

        *Ein Fingerabdruck, der an einer Uhr haengt, ist ein Zeitstempel mit besserem
        Namen.*

    Hier wird die Datei **angefasst, ohne sie zu aendern**: neue Zeitangabe, gleicher
    Inhalt. Das Projekt muss weiterhin «unveraendert» sagen.
    """
    import os
    import time as zeit

    modell = heimatartig / "haus.ifc"
    modell.write_bytes(b"ISO-10303-21;\n")
    mappe = heimatartig / "projekt"
    projekt.speichere(projekt.neu(mappe, modell), mappe)

    spaeter = zeit.time() + 10_000
    os.utime(modell, (spaeter, spaeter))

    assert projekt.oeffne(mappe)["modell_stand"] == projekt.MODELL_UNVERAENDERT


def test_und_eine_gleich_GROSSE_aenderung_faellt_trotzdem_auf(heimatartig):
    """Die Gegenprobe zur vorigen, und sie ist die schaerfere: Gleiche Groesse, gleiche
    Zeit, **anderer Inhalt**. Wer nur Groesse und Datum vergleicht, sieht hier nichts."""
    import os

    modell = heimatartig / "haus.ifc"
    modell.write_bytes(b"AAAA")
    mappe = heimatartig / "projekt"
    projekt.speichere(projekt.neu(mappe, modell), mappe)
    vorher = modell.stat()

    modell.write_bytes(b"BBBB")
    os.utime(modell, (vorher.st_atime, vorher.st_mtime))

    assert projekt.oeffne(mappe)["modell_stand"] == projekt.MODELL_VERAENDERT
