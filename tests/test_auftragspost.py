"""Ein Auftrag als Block — und vor allem, was NICHT hinausgehen darf.

Der Block verlässt das Repo. Alles, was hier durchrutscht, ist draussen — und deshalb
zielt die Hälfte dieser Tests nicht auf die Form, sondern auf Regel 3 und auf die
Vollständigkeit.
"""

import json

import pytest

from aiimaging import auftrag, auftragspost


def _satz(**abweichend):
    satz = {
        "schema": auftrag.SCHEMA_AUFTRAG,
        "worker": "cloud",
        "auftrag_id": "auf-20260827-77",
        "art": "qa",
        "beschreibung": "Eine Frage an den Vertrag.",
        "anweisung": "=== WAS ZU TUN IST ===\n\nSchritt 1. Schritt 2.",
        "erstellt": "2026-08-27T12:00:00Z",
        "geometrie": {"synthetisch": True, "pfad": None,
                      "erzeugen_mit": "python3 tools/make_test_ifc.py build/t.ifc"},
        "params": {},
        "auflagen": ["Nichts am Vertrag im Alleingang aendern"],
        "rueckgabe": ["V1 welcher Weg?"],
    }
    satz.update(abweichend)
    # EIN local-AUFTRAG BRAUCHT SEIT DEM 01.09.2026 SEINE HARDWARE-AUFLAGEN. Die
    # Attrappe trug bis dahin nur Prosa — also genau die Gestalt, an der `darf_starten`
    # abstuerzte, und deshalb sah keine Probe den Fehler.
    if satz.get("worker") == auftrag.WORKER_LOCAL and isinstance(satz["auflagen"], list):
        satz["auflagen"] = {"leistungsgrenze_w": auftrag.LEISTUNGSGRENZE_W,
                            "nur_bei_leerlauf": True,
                            "hinweise": list(satz["auflagen"])}
    return satz


# ======================================================================================
# Der Block trägt alles, was der Empfänger braucht
# ======================================================================================

def test_der_block_traegt_kennung_adressat_anweisung_auflagen_und_rueckgabe():
    """**Selbsttragend.** Wer ihn liest, braucht unser Repo nicht — das ist der Zweck."""
    text = auftragspost.block(_satz())
    for erwartet in ("auf-20260827-77", "an: cloud", "Eine Frage an den Vertrag",
                     "WAS ZU TUN IST", "Nichts am Vertrag im Alleingang aendern",
                     "V1 welcher Weg?"):
        assert erwartet in text, erwartet


def test_der_block_nennt_den_rueckweg_und_er_haengt_am_adressaten():
    """Ein Auftrag ohne Rückweg erzeugt eine Antwort, die niemand findet."""
    an_cloud = auftragspost.block(_satz(worker="cloud"))
    assert "Ihr habt unser Repo nicht" in an_cloud

    an_local = auftragspost.block(_satz(worker="local"))
    assert "auftraege/ergebnisse/auf-20260827-77.json" in an_local
    assert "Ihr habt unser Repo nicht" not in an_local


def test_ein_unvollstaendiger_auftrag_geht_gar_nicht_erst_hinaus():
    with pytest.raises(auftragspost.PostError, match="nicht vollständig"):
        auftragspost.block(_satz(auflagen=[]))


def test_ohne_rueckgabe_geht_kein_block_hinaus():
    """**Strenger als `auftrag.pruefe_auftrag`** — dort ist `rueckgabe` kein Pflichtfeld.

    Die Datei kann man nachbessern, solange sie im Repo liegt. Der Block ist das, was der
    Empfänger liest: Ein Auftrag, der nicht sagt, woran man erkennt, dass er beantwortet
    ist, erzeugt drüben Arbeit und hier keine Antwort.
    """
    with pytest.raises(auftragspost.PostError, match="was zurueckkommen soll"):
        auftragspost.block(_satz(rueckgabe=[]))


def test_ohne_anweisung_UND_ohne_beschreibung_gibt_es_keinen_block():
    with pytest.raises(auftragspost.PostError, match="weder Anweisung noch Beschreibung"):
        auftragspost.block(_satz(anweisung="  ", beschreibung="  "))


def test_ein_alter_auftrag_ohne_anweisungsfeld_ist_trotzdem_zustellbar():
    """**Aufträge vor dem 26.08.2026 haben kein `anweisung`-Feld.**

    Ihre ganze Anweisung steckt in `beschreibung`. Sie deshalb nicht ausgeben zu können,
    machte den ältesten Posten des Rückstands unzustellbar — Buchstabentreue gegen den
    Zweck.
    """
    text = auftragspost.block(_satz(anweisung="", beschreibung="ALLES STEHT HIER DRIN."))
    assert "ALLES STEHT HIER DRIN." in text
    assert text.count("ALLES STEHT HIER DRIN.") == 1, "und nicht zweimal"


# ======================================================================================
# Regel 3 — der Block geht nach draussen, die Datei nicht
# ======================================================================================

def test_ein_pfad_aus_dieser_umgebung_wird_ersetzt_und_der_block_sagt_es():
    """Ersetzen statt Ablehnen — wie in `auftrag.ohne_kennungen`, aber **nicht still**."""
    # `jemand` steht in `test_regel3_kennungen.ERLAUBT` und ist ausdruecklich der Name
    # KEINES Menschen. Ein erfundener, namensfoermiger Platzhalter waere hier selbst ein
    # Regel-3-Verstoss — der Waechter ueber das ganze Repo hat genau das gefangen, und er
    # hatte recht: Eine Datei mit einem namensfoermigen Pfad ist eine Datei mit einem
    # namensfoermigen Pfad, auch wenn sie ihn nur pruefen will.
    text = auftragspost.block(_satz(
        anweisung="Der Lauf lag unter /home/jemand/projekt/lauf.json"))
    assert "/home/jemand/" not in text
    assert f"/home/{auftrag.NUTZER_ERSATZ}/projekt/lauf.json" in text, (
        "der Rest des Pfades bleibt — er ist die Auskunft")
    assert "Regel 3" in text
    assert "ungewoehnlich" in text, "eine Ersetzung ist hier selbst ein Befund"


def test_ohne_pfadfund_steht_der_hinweis_nicht_da():
    """Die Gegenprobe — sonst wäre der Hinweis eine Dauerwarnung."""
    assert "Regel 3 — und dieser Text" not in auftragspost.block(_satz())
    assert "ersetzt" not in auftragspost.block(_satz())


# ======================================================================================
# Der Umbruch darf keine Tabelle zerbrechen
# ======================================================================================

def test_eingerueckte_zeilen_und_tabellen_bleiben_unangetastet():
    """Messwerttabellen und Befehlszeilen stehen eingerückt. Ein Umbruch mitten darin
    macht sie unlesbar, und unlesbar heisst hier: wird nicht gelesen."""
    tabelle = "    18:53:40   Takt, eigene Ablage abgegangen: gesehen 0 — und noch mehr Text hintendran"
    text = auftragspost.block(_satz(anweisung=f"Vorher\n{tabelle}\nNachher"))
    assert tabelle in text


def test_lange_rueckgabefragen_werden_mit_haengendem_einzug_gebrochen():
    """Sie sind die längsten Zeilen des Blocks — und beginnen mit Einzug, kämen also
    ungebrochen durch, wenn nur `_umbruch` liefe."""
    frage = "V1 " + "sehr lange Frage " * 12
    text = auftragspost.block(_satz(rueckgabe=[frage.strip()]))
    lang = [z for z in text.splitlines() if len(z) > auftragspost.BREITE]
    assert not lang, lang[:1]


# ======================================================================================
# Ein unzustellbarer Auftrag darf die übrigen nicht verdecken
# ======================================================================================

def test_ein_kaputter_auftrag_wird_gemeldet_statt_uebersprungen(tmp_path):
    """Ein still weggelassener Auftrag sieht hinterher aus wie keiner."""
    ordner = tmp_path / "auftraege" / "offen"
    ordner.mkdir(parents=True)
    (tmp_path / "auftraege" / "ergebnisse").mkdir()
    (ordner / "auf-20260827-77.json").write_text(json.dumps(_satz()), encoding="utf-8")
    (ordner / "auf-20260827-78.json").write_text(
        json.dumps(_satz(auftrag_id="auf-20260827-78", auflagen=[])), encoding="utf-8")

    blocks = dict(auftragspost.offene_blocks(tmp_path, worker="cloud"))
    assert set(blocks) == {"auf-20260827-77", "auf-20260827-78"}
    assert "NICHT ZUSTELLBAR" in blocks["auf-20260827-78"]
    assert "NICHT ZUSTELLBAR" not in blocks["auf-20260827-77"]


def test_der_adressat_filtert(tmp_path):
    ordner = tmp_path / "auftraege" / "offen"
    ordner.mkdir(parents=True)
    (tmp_path / "auftraege" / "ergebnisse").mkdir()
    (ordner / "auf-20260827-77.json").write_text(json.dumps(_satz()), encoding="utf-8")
    (ordner / "auf-20260827-79.json").write_text(
        json.dumps(_satz(auftrag_id="auf-20260827-79", worker="ui")), encoding="utf-8")

    assert [k for k, _ in auftragspost.offene_blocks(tmp_path, worker="ui")] == [
        "auf-20260827-79"]
    assert len(auftragspost.offene_blocks(tmp_path)) == 2


def test_ein_beantworteter_auftrag_wird_nicht_mehr_ausgegeben(tmp_path):
    ordner = tmp_path / "auftraege" / "offen"
    ordner.mkdir(parents=True)
    (tmp_path / "auftraege" / "ergebnisse").mkdir()
    (ordner / "auf-20260827-77.json").write_text(json.dumps(_satz()), encoding="utf-8")
    assert len(auftragspost.offene_blocks(tmp_path)) == 1

    (tmp_path / "auftraege" / "ergebnisse" / "auf-20260827-77.json").write_text("{}")
    assert auftragspost.offene_blocks(tmp_path) == []


def test_lege_ab_schreibt_je_auftrag_eine_datei(tmp_path):
    """Der Zielpfad ist ein Argument und keine Konstante — er zeigt in ein fremdes Repo."""
    blocks = [("auf-20260827-77", "erster Block"), ("auf-20260827-78", "zweiter Block")]
    ziel = tmp_path / "tief" / "drin"
    pfade = auftragspost.lege_ab(blocks, ziel)

    assert [p.name for p in pfade] == ["auf-20260827-77.md", "auf-20260827-78.md"]
    assert pfade[0].read_text(encoding="utf-8") == "erster Block\n"
    assert ziel.is_dir(), "das Verzeichnis wird angelegt, nicht vorausgesetzt"


def test_lege_ab_ueberschreibt_beim_naechsten_lauf(tmp_path):
    """Deshalb steht in der Erklärung daneben, dass man in diesen Dateien nicht antwortet."""
    auftragspost.lege_ab([("auf-20260827-77", "alt")], tmp_path)
    auftragspost.lege_ab([("auf-20260827-77", "neu")], tmp_path)
    assert (tmp_path / "auf-20260827-77.md").read_text(encoding="utf-8") == "neu\n"


# ======================================================================================
# Der Einstieg — und ein Schalter, der nichts tat
# ======================================================================================

def _cli():
    import importlib.util
    from pathlib import Path
    pfad = Path(__file__).resolve().parents[1] / "tools" / "auftragspost.py"
    spec = importlib.util.spec_from_file_location("werkzeug_auftragspost", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _repo_mit_auftrag(tmp_path, satz):
    ordner = tmp_path / "auftraege" / "offen"
    ordner.mkdir(parents=True)
    (ordner / f"{satz['auftrag_id']}.json").write_text(
        json.dumps(satz, ensure_ascii=False), encoding="utf-8")
    return tmp_path


def test_nach_wirkt_auch_zusammen_mit_auftrag(tmp_path):
    """*Der Fehler, den der erste Gebrauch gefunden hat.* `--auftrag` kehrte vor der
    Ablage um und **druckte** den Block, obwohl ein Zielverzeichnis dastand. Die Datei,
    die der Adressat lesen sollte, entstand nie — und es gab keine Fehlermeldung.

    **Ein Bedienelement ohne Wirkung ist schlimmer als keines:** Es sagt, etwas sei
    geschehen. Genau der Befund, den wir sonst an die Oberfläche weitergeben.
    """
    satz = _satz()
    repo = _repo_mit_auftrag(tmp_path, satz)
    ziel = tmp_path / "hinaus"
    assert _cli().main(["--repo", str(repo), "--auftrag", satz["auftrag_id"],
                        "--nach", str(ziel)]) == 0
    datei = ziel / f"{satz['auftrag_id']}.md"
    assert datei.exists(), "--nach wurde übergangen, der Block ging nur auf den Bildschirm"
    assert satz["auftrag_id"] in datei.read_text(encoding="utf-8")


def test_ohne_nach_druckt_auftrag_weiterhin(tmp_path, capsys):
    """Die Gegenprobe: Der alte Weg bleibt. Ohne Ziel wird gedruckt."""
    satz = _satz()
    repo = _repo_mit_auftrag(tmp_path, satz)
    assert _cli().main(["--repo", str(repo), "--auftrag", satz["auftrag_id"]]) == 0
    assert satz["auftrag_id"] in capsys.readouterr().out


def test_eine_unbekannte_kennung_wird_gemeldet_und_nicht_still_uebergangen(tmp_path):
    repo = _repo_mit_auftrag(tmp_path, _satz())
    assert _cli().main(["--repo", str(repo), "--auftrag", "auf-gibt-es-nicht"]) == 2


# ======================================================================================
# Der Zustellbeleg — für Adressaten, von denen noch nie eine Antwort kam
# ======================================================================================
#
# Gemessen am 01.09.2026: `ui` hatte vier Aufträge in sieben Tagen und **nie** geantwortet,
# `cloud` sieben in zehn Tagen ebenfalls nie. Aus dem Schweigen allein ist nicht zu
# unterscheiden, ob die Frage querliegt oder ob niemand in das Verzeichnis sieht — und die
# beiden verlangen das Gegenteil voneinander.

def test_ein_block_ohne_zustellbeleg_traegt_ihn_nicht():
    """Die Vorgabe ist null. Ein Beleg in jedem Block wäre eine Dauerwarnung."""
    assert "ZUSTELLBELEG" not in auftragspost.block(_satz())


def test_der_zustellbeleg_nennt_die_zahl_der_offenen():
    text = auftragspost.block(_satz(), zustellbeleg=7)
    assert "ZUSTELLBELEG" in text
    assert "7 Auftraege" in text, (
        "Ohne die Zahl ist es eine Höflichkeitsfloskel — mit ihr eine Tatsache.")


def test_der_zustellbeleg_verlangt_ausdruecklich_keine_inhaltliche_antwort():
    """*Wer die Frage nicht beantworten kann, kann trotzdem bestätigen, dass er sie
    gelesen hat.* Ein Beleg, der wie eine Mahnung klingt, wird wie eine behandelt."""
    # Auf die WORTE wird an der Konstante geprüft und nicht am Block: Der Block ist
    # umbrochen, und ein Umbruch mitten in «kein Termin» hätte diesen Test rot gemacht,
    # ohne dass am Beleg etwas fehlte. *Ein Test, der an der Zeilenbreite hängt, prüft
    # die Zeilenbreite.*
    assert "keine Messung" in auftragspost.ZUSTELLBELEG
    assert "kein Termin" in auftragspost.ZUSTELLBELEG
    assert "VOR DER INHALTLICHEN ANTWORT" in auftragspost.block(_satz(), zustellbeleg=3)


def test_der_zustellbeleg_steht_nach_dem_rueckweg():
    """Er ist die Vorstufe, nicht der Ersatz. Wer nur den Anfang liest, liest den Auftrag."""
    text = auftragspost.block(_satz(), zustellbeleg=2)
    assert text.index("RUECKWEG") < text.index("ZUSTELLBELEG")


def test_der_zustellbeleg_sagt_dass_der_fehler_bei_uns_liegen_koennte():
    """*Ein Auftrag, den sein Adressat nicht erreichen kann, ist kein Rückstand bei ihm —
    er ist einer beim Absender.* Der Satz gehört in den Beleg, sonst liest er sich als
    Vorwurf."""
    assert "Fehler bei UNS" in auftragspost.ZUSTELLBELEG
    assert "ZUSTELLBELEG" in auftragspost.block(_satz(), zustellbeleg=1)


def test_der_block_zeigt_die_WERTE_der_woerterbuchauflagen_und_nicht_ihre_namen():
    """**Die zweite Probe, die ihre Mutation zuerst überlebt hat.** Sie prüfte
    `auflagen_text` von Hand — also die Hilfsfunktion, nicht den Block, der sie benutzt.

    Über ein Wörterbuch gezählt ergab `AUFLAGEN` die Schlüsselnamen:
    `leistungsgrenze_w`, `nur_bei_leerlauf`, `hinweis`. Die Zahl, an der der Rechner
    hängt, stand in keinem einzigen Block, der je hinausging.
    """
    satz = _satz(worker="local", auflagen={
        "leistungsgrenze_w": 400, "nur_bei_leerlauf": True,
        "hinweis": "RTX 5090 loest ohne Grenze die Netzteil-Schutzschaltung aus."})
    text = auftragspost.block(satz)
    assert "400" in text, "die Zahl fehlte, nur ihr Schluesselname stand da"
    assert "Netzteil" in text, "der Hinweis stand nur als Schluesselname da"


def test_der_block_sagt_es_wenn_ein_auftrag_keine_rueckgabepunkte_nennt():
    """Nicht abweisen — sichtbar machen. *Buchstabentreue, die den ältesten Posten des
    Rückstands unzustellbar macht, ist derselbe Fehler in die andere Richtung.*"""
    text = auftragspost.block(_satz(rueckgabe={
        "verzeichnis": "auftraege/ergebnisse", "nur_zahlen": True, "hinweis": "Nur Zahlen"}))
    assert "keine EINZELNEN Rueckgabepunkte" in text
    assert "Mangel bei uns" in text, (
        "Der Empfaenger darf nicht denken, er habe etwas uebersehen.")


def test_echte_rueckgabepunkte_verdraengen_den_hinweis():
    """Die Gegenprobe: Sonst stünde der Satz unter jedem Block — eine Dauerwarnung."""
    assert "keine EINZELNEN Rueckgabepunkte" not in auftragspost.block(_satz())
