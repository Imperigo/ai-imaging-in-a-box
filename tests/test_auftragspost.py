"""Ein Auftrag als Block — und vor allem, was NICHT hinausgehen darf.

Der Block verlässt das Repo. Alles, was hier durchrutscht, ist draussen — und deshalb
zielt die Hälfte dieser Tests nicht auf die Form, sondern auf Regel 3 und auf die
Vollständigkeit.
"""

import json

import pathlib

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

    # EIN LEERES ERGEBNIS SCHLIESST SEIT DEM 02.09.2026 NICHTS MEHR.

    # Hier stand `write_text("{}")` — eine Datei ohne Status, und der Auftrag

    # galt als beantwortet. Genau diese Milde hat drei Auftraege geschlossen,

    # von denen einer in seinem eigenen Text sagte, dass die uebrigen Teile

    # noch folgen. Was `baue_ergebnis` nicht kennt, ist keine Antwort.

    (tmp_path / "auftraege" / "ergebnisse" / "auf-20260827-77.json").write_text(

        json.dumps(auftrag.baue_ergebnis(auftrag_id="auf-20260827-77",

                                         status="ok")), encoding="utf-8")
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


def test_auch_der_einzelweg_haengt_den_zustellbeleg_an(tmp_path):
    """**Die Entscheidung lag auf einem Weg, und der andere liess sie still weg.**

    Am Abend des 01.09.2026 verschickte `--auftrag` einen Auftrag an einen Adressaten,
    der noch nie geantwortet hatte — ohne Beleg. Die Regel stand mitten in
    `offene_blocks`; der Einzelweg ging daran vorbei.
    """
    satz = _satz(worker="ui")
    repo = _repo_mit_auftrag(tmp_path, satz)
    ziel = tmp_path / "hinaus"
    assert _cli().main(["--repo", str(repo), "--auftrag", satz["auftrag_id"],
                        "--nach", str(ziel)]) == 0
    text = (ziel / f"{satz['auftrag_id']}.md").read_text(encoding="utf-8")
    assert "ZUSTELLBELEG" in text


def test_der_einzelweg_haengt_ihn_NICHT_an_wenn_der_adressat_geantwortet_hat(tmp_path):
    """Die Gegenprobe — sonst wäre der Beleg eine Dauerwarnung."""
    satz = _satz(worker="ui")
    repo = _repo_mit_auftrag(tmp_path, satz)
    frueher = _satz(worker="ui", auftrag_id="auf-20260827-70")
    auftrag.schreibe_auftrag(frueher, repo)
    auftrag.schreibe_ergebnis(
        auftrag.baue_ergebnis(auftrag_id="auf-20260827-70", status="ok"), repo)
    ziel = tmp_path / "hinaus"
    assert _cli().main(["--repo", str(repo), "--auftrag", satz["auftrag_id"],
                        "--nach", str(ziel)]) == 0
    assert "ZUSTELLBELEG" not in (ziel / f"{satz['auftrag_id']}.md").read_text(
        encoding="utf-8")


# ---------------------------------------------------------------------------------
# ABGELEGT IST NICHT AUSGELIEFERT — der Befund vom 03.09.2026
#
# `auf-20260901-70` und `auf-20260902-72` lagen zwei bzw. einen Tag in
# `auftraege/offen/` und waren nirgends sonst: Der letzte Postlauf war vom 01.09., und
# seither war zwar abgelegt, aber nichts hinausgegeben worden. In jeder Zaehlung standen
# sie als Rueckstand BEIM ADRESSATEN — und nach unserem eigenen Satz war es einer beim
# Absender. Gemerkt hat es niemand, weil abgelegt und ausgeliefert gleich aussahen.
# ---------------------------------------------------------------------------------


def test_ein_abgelegter_auftrag_gilt_nicht_schon_als_ausgeliefert(tmp_path):
    """**Der Befund selbst.** Ohne Postlauf ist der Auftrag nur bei uns."""
    satz = _satz(worker="ui")
    repo = _repo_mit_auftrag(tmp_path, satz)
    offen = auftragspost.unzugestellt(repo)
    assert [e["auftrag_id"] for e in offen] == [satz["auftrag_id"]]
    assert offen[0]["worker"] == "ui"


def test_der_postlauf_traegt_die_zustellung_ein_und_die_liste_wird_leer(tmp_path):
    """Die Gegenprobe — **über die Befehlszeile, nicht über die Hilfsfunktion**.

    *Ein Wächter, der den Aufruf selbst nachbaut, bewacht seine eigene Nachbildung.*
    Hier hängt der Vermerk am Postlauf; wer ihn dort herausnimmt, muss rot werden.
    """
    satz = _satz(worker="ui")
    repo = _repo_mit_auftrag(tmp_path, satz)
    assert _cli().main(["ui", "--repo", str(repo), "--nach", str(tmp_path / "hinaus")]) == 0
    assert auftragspost.unzugestellt(repo) == []


def test_auch_der_einzelweg_vermerkt_die_zustellung(tmp_path):
    """Derselbe Fehler wie beim Zustellbeleg wäre hier wieder möglich: zwei Wege, und
    einer geht an der Regel vorbei. Am 01.09. war das genau so passiert."""
    satz = _satz(worker="cloud")
    repo = _repo_mit_auftrag(tmp_path, satz)
    assert _cli().main(["--repo", str(repo), "--auftrag", satz["auftrag_id"],
                        "--nach", str(tmp_path / "hinaus")]) == 0
    assert auftragspost.unzugestellt(repo) == []


def test_ein_gedruckter_block_gilt_NICHT_als_ausgeliefert(tmp_path):
    """**Drucken ist keine Zustellung.** Ohne `--nach` entsteht keine Datei, die
    jemand lesen könnte — ein Vermerk hier wäre eine Auslieferung, die nur behauptet
    ist. *Der Vermerk soll den Fall finden, nicht ihn zudecken.*"""
    satz = _satz(worker="cloud")
    repo = _repo_mit_auftrag(tmp_path, satz)
    assert _cli().main(["cloud", "--repo", str(repo)]) == 0
    assert [e["auftrag_id"] for e in auftragspost.unzugestellt(repo)] == [
        satz["auftrag_id"]]


def test_local_wird_nicht_vermerkt_denn_local_liest_das_repo_selbst(tmp_path):
    """*Die HomeStation bekommt ihre Aufträge über `git pull`.* Ein Zustellvermerk für
    sie wäre eine Zahl, die nie fällt und darum nichts bedeutet."""
    satz = _satz(worker="local")
    repo = _repo_mit_auftrag(tmp_path, satz)
    assert _cli().main(["local", "--repo", str(repo),
                        "--nach", str(tmp_path / "hinaus")]) == 0
    assert not (repo / auftragspost.ZUSTELLUNG_DATEI).exists(), (
        "Fuer `local` darf gar kein Vermerk entstehen.")
    assert auftragspost.unzugestellt(repo) == []


def test_ein_beantworteter_auftrag_steht_nicht_mehr_als_unzugestellt(tmp_path):
    """Wer geantwortet hat, hat offensichtlich empfangen. Sonst bliebe eine Zeile
    stehen, die einem beantworteten Auftrag nachträgt, nie zugestellt worden zu sein."""
    satz = _satz(worker="cloud")
    repo = _repo_mit_auftrag(tmp_path, satz)
    auftrag.schreibe_ergebnis(
        auftrag.baue_ergebnis(auftrag_id=satz["auftrag_id"], status="ok"), repo)
    assert auftragspost.unzugestellt(repo) == []


def test_ein_kaputter_vermerk_heisst_nichts_zugestellt(tmp_path):
    """**Fail-closed, wie beim Leerlauftor.** Die strengere Auslegung führt hier zu einer
    Auslieferung zu viel; die mildere zu einem Auftrag, der nie ankommt und den niemand
    vermisst."""
    satz = _satz(worker="ui")
    repo = _repo_mit_auftrag(tmp_path, satz)
    ziel = repo / auftragspost.ZUSTELLUNG_DATEI
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text("{kein json", encoding="utf-8")
    assert [e["auftrag_id"] for e in auftragspost.unzugestellt(repo)] == [
        satz["auftrag_id"]]


def test_der_vermerk_traegt_keinen_pfad_des_fremden_repos(tmp_path):
    """**Regel 3 auch hier.** Das Zielverzeichnis zeigt in ein fremdes Repo; unseres ist
    öffentlich. Vermerkt werden Kennung und Zeitpunkt — sonst nichts."""
    satz = _satz(worker="ui")
    repo = _repo_mit_auftrag(tmp_path, satz)
    hinaus = tmp_path / "ein_fremder_ordner"
    assert _cli().main(["ui", "--repo", str(repo), "--nach", str(hinaus)]) == 0
    text = (repo / auftragspost.ZUSTELLUNG_DATEI).read_text(encoding="utf-8")
    assert "ein_fremder_ordner" not in text
    assert str(hinaus) not in text


def test_der_vermerk_entsteht_erst_NACH_dem_schreiben(tmp_path):
    """**Die Reihenfolge ist der ganze Punkt, und ohne diese Probe stünde sie nur im
    Kommentar.** Ein Vermerk vor dem Schreiben behauptet eine Auslieferung, die ein
    Fehler beim Schreiben gerade verhindert hat — und dann steht der Auftrag als
    zugestellt da, mit einer Zeile mehr Beweis dafür, dass alles stimmt.

    Erzwungen wird der Fehler, indem das Zielverzeichnis schon als **Datei** existiert.
    """
    satz = _satz(worker="ui")
    repo = _repo_mit_auftrag(tmp_path, satz)
    versperrt = tmp_path / "kein_ordner"
    versperrt.write_text("ich bin eine Datei", encoding="utf-8")
    with pytest.raises((NotADirectoryError, FileExistsError, OSError)):
        _cli().main(["ui", "--repo", str(repo), "--nach", str(versperrt)])
    assert [e["auftrag_id"] for e in auftragspost.unzugestellt(repo)] == [
        satz["auftrag_id"]], (
        "Nichts ist hinausgegangen — dann darf auch nichts vermerkt sein.")


def test_vermerken_schreibt_nichts_und_vermerkt_doch(tmp_path):
    """``--vermerken`` — der zweite Zustellweg, und er hatte bis zum 10.09.2026 keinen.

    Für ``ui`` und ``cloud`` läuft die Zustellung über **git**: Der Block liegt unter
    ``auftraege/bloecke/``, sie haben unser Repo als Quelle. Auf diesem Weg gab es keine
    Möglichkeit, den Vermerk zu setzen — ``tools/einbau.py`` meldete den Auftrag darum
    dauerhaft als NICHT AUSGELIEFERT, obwohl er hinausgegangen war.

    Der Ausweg war, ``--nach`` in ein Verzeichnis im **eigenen** Repo zu richten. Genau
    das ist am 09.09.2026 geschehen und legte fünf Dateien an, die den Wortlaut aus
    ``offen/*.json`` verdoppeln. *Ein Werkzeug, das man zweckentfremden muss, um eine
    wahre Angabe zu machen, erzeugt dabei eine zweite Wahrheit.*
    """
    satz = _satz(worker="ui")
    repo = _repo_mit_auftrag(tmp_path, satz)
    vorher = sorted(pfad.name for pfad in repo.rglob("*") if pfad.is_file())

    assert _cli().main(["ui", "--repo", str(repo), "--vermerken"]) == 0

    assert auftragspost.unzugestellt(repo) == [], "der Vermerk ist nicht gesetzt worden"
    nachher = sorted(pfad.name for pfad in repo.rglob("*") if pfad.is_file())
    assert set(nachher) - set(vorher) == {pathlib.Path(
        auftragspost.ZUSTELLUNG_DATEI).name}, (
        "ausser dem Vermerk selbst darf keine Datei entstanden sein")


def test_vermerken_gilt_auch_fuer_einen_einzelnen_auftrag(tmp_path):
    """Derselbe Schalter im ``--auftrag``-Zweig.

    Die beiden Zweige sind schon einmal auseinandergelaufen: ``--nach`` galt im
    ``--auftrag``-Zweig zuerst **nicht**, und ein Schalter ohne Wirkung sagt, etwas sei
    geschehen (gefunden am 01.09.2026 beim ersten Gebrauch).
    """
    satz = _satz(worker="ui")
    repo = _repo_mit_auftrag(tmp_path, satz)
    assert _cli().main(
        ["--repo", str(repo), "--auftrag", satz["auftrag_id"], "--vermerken"]) == 0
    assert auftragspost.unzugestellt(repo) == []


def test_der_stichtag_im_zustellbeleg_ist_immer_heute():
    """**Der Fehler, der sich selbst wiederholt hat.** Bis zum 06.09.2026 war der Stichtag
    eine Vorgabe mit einem Kommentar daneben: *«wer die Post neu erzeugt, zieht darum
    dieses Datum mit»*. Am 03.09. wurde er nachgezogen. Am 06.09. ging die Post erneut
    hinaus — und trug wieder den 03.

    *Ein Kommentar, der einen Menschen erinnert, ist kein Wächter.* Die Zahl daneben war
    jedes Mal richtig, weil sie gezählt wurde.
    """
    from datetime import date
    assert auftragspost.zustellbeleg_stand() == date.today().strftime("%d.%m.%Y")
    assert auftragspost.zustellbeleg_stand(date(2026, 1, 2)) == "02.01.2026"


def test_der_block_traegt_das_heutige_datum_im_zustellbeleg(tmp_path):
    """Und zwar **im Block**, nicht nur in der Hilfsfunktion — sonst bewachte die Probe
    ihre eigene Nachbildung."""
    from datetime import date
    satz = _satz(worker="ui")
    text = auftragspost.block(satz, zustellbeleg=3)
    assert date.today().strftime("%d.%m.%Y") in text


# ── Warum eine Antwort fehlt — die vier Lagen (16.09.2026) ────────────────────────────
#
# Am 16.09.2026 standen 18 Aufträge offen, der älteste 25 Tage, und seit acht Tagen hatte
# **keiner** der drei Worker geantwortet. Der Rückstand sagte dazu eine Zahl. Ob drüben
# niemand arbeitete, ob die Aufträge nicht ankamen, oder ob sie ankamen und liegen
# blieben, unterschied dieses Repo nicht — und die drei verlangen verschiedene Handgriffe.

from datetime import date as _date


def _lege_auftrag(tmp_path, kennung, worker, erstellt, rang=1):
    ordner = tmp_path / "auftraege" / "offen"
    ordner.mkdir(parents=True, exist_ok=True)
    (ordner / f"{kennung}.json").write_text(json.dumps({
        "schema": "aiimaging.homeworker-auftrag/v1", "auftrag_id": kennung,
        "art": "frage", "worker": worker, "rang": rang, "params": {},
        "erstellt": erstellt, "beschreibung": "Probe", "anweisung": "Probe",
    }, ensure_ascii=False), encoding="utf-8")


def _lege_antwort(tmp_path, kennung, worker, beendet):
    """Eine BEANTWORTETE Kennung — Auftrag und Ergebnis, sonst zaehlt sie nicht."""
    _lege_auftrag(tmp_path, kennung, worker, beendet, rang=9)
    ordner = tmp_path / "auftraege" / "ergebnisse"
    ordner.mkdir(parents=True, exist_ok=True)
    (ordner / f"{kennung}.json").write_text(json.dumps({
        "schema": "aiimaging.homeworker-ergebnis/v1", "auftrag_id": kennung,
        "status": "ok", "beendet": beendet, "zusammenfassung": "gemessen",
    }, ensure_ascii=False), encoding="utf-8")


def _vermerke(tmp_path, *kennungen):
    (tmp_path / "auftraege").mkdir(parents=True, exist_ok=True)
    (tmp_path / "auftraege" / "zustellung.json").write_text(
        json.dumps({k: {"am": "2026-09-01T00:00:00Z"} for k in kennungen}),
        encoding="utf-8")


def test_ein_nie_zugestellter_auftrag_ist_unser_rueckstand(tmp_path):
    """*Er kann nicht beantworten, was er nicht hat.*"""
    _lege_auftrag(tmp_path, "auf-20260901-01", "cloud", "2026-09-01T00:00:00Z")

    (befund,) = auftragspost.warum_keine_antwort(tmp_path, heute=_date(2026, 9, 16))

    assert befund["lage"] == auftragspost.NICHT_ZUGESTELLT
    assert "bei UNS" in befund["grund"]


def test_ein_frischer_auftrag_sagt_noch_nichts(tmp_path):
    """Die Worker arbeiten in Sitzungen, nicht im Takt."""
    _lege_auftrag(tmp_path, "auf-20260915-01", "cloud", "2026-09-15T00:00:00Z")
    _vermerke(tmp_path, "auf-20260915-01")

    (befund,) = auftragspost.warum_keine_antwort(tmp_path, heute=_date(2026, 9, 16))

    assert befund["lage"] == auftragspost.FRISCH


def test_wer_danach_anderes_beantwortet_hat_diesen_uebergangen(tmp_path):
    """**Die einzige Lage, in der eine Nachfrage angebracht ist.**

    Der Adressat hat nach diesem Auftrag etwas anderes beantwortet — er war also da, und
    dieser eine blieb liegen.
    """
    _lege_auftrag(tmp_path, "auf-20260901-01", "cloud", "2026-09-01T00:00:00Z")
    _lege_antwort(tmp_path, "auf-20260905-02", "cloud", "2026-09-05T00:00:00Z")
    _vermerke(tmp_path, "auf-20260901-01", "auf-20260905-02")

    lagen = {e["auftrag_id"]: e["lage"]
             for e in auftragspost.warum_keine_antwort(tmp_path, heute=_date(2026, 9, 16))}

    assert lagen["auf-20260901-01"] == auftragspost.AKTIV_UEBERGANGEN


def test_ohne_lebenszeichen_wird_ausdruecklich_nicht_gemahnt(tmp_path):
    """**Die dritte Antwort, auf den Rückweg angewandt.**

    Wer seit Wochen nichts schickt, hat eine Mahnung vielleicht ebenso wenig gesehen wie
    den Auftrag. *Es heisst nicht «er übergeht uns» — es heisst, dass wir es nicht wissen.*
    """
    _lege_auftrag(tmp_path, "auf-20260901-01", "cloud", "2026-09-01T00:00:00Z")
    _lege_antwort(tmp_path, "auf-20260820-02", "cloud", "2026-08-20T00:00:00Z")
    _vermerke(tmp_path, "auf-20260901-01", "auf-20260820-02")

    lagen = {e["auftrag_id"]: e for e in
             auftragspost.warum_keine_antwort(tmp_path, heute=_date(2026, 9, 16))}

    assert lagen["auf-20260901-01"]["lage"] == auftragspost.KEIN_LEBENSZEICHEN
    assert "nicht wissen" in lagen["auf-20260901-01"]["grund"]


def test_die_lagen_schliessen_einander_aus(tmp_path):
    """Jeder Auftrag bekommt **genau eine** Lage — sonst wäre die Zählung mehrdeutig."""
    _lege_auftrag(tmp_path, "auf-20260901-01", "cloud", "2026-09-01T00:00:00Z")
    _lege_auftrag(tmp_path, "auf-20260915-02", "cloud", "2026-09-15T00:00:00Z", rang=2)
    _vermerke(tmp_path, "auf-20260915-02")

    befunde = auftragspost.warum_keine_antwort(tmp_path, heute=_date(2026, 9, 16))

    assert len(befunde) == 2
    for e in befunde:
        assert e["lage"] in auftragspost.LAGEN


def test_ein_kern_auftrag_braucht_keine_zustellung(tmp_path):
    """`kern` sind wir selbst — dorthin wird nichts zugestellt, und das Fehlen eines
    Vermerks ist kein Befund."""
    _lege_auftrag(tmp_path, "auf-20260901-01", "kern", "2026-09-01T00:00:00Z")

    (befund,) = auftragspost.warum_keine_antwort(tmp_path, heute=_date(2026, 9, 16))

    assert befund["lage"] != auftragspost.NICHT_ZUGESTELLT


# ── «Gesehen» — der dritte Zustand des Rückwegs (16.09.2026) ──────────────────────────
#
# `warum_keine_antwort` unterschied vier Lagen, und eine Unterscheidung fehlte ihr
# ausdrücklich: Ein ZUGESTELLTER Auftrag, dessen Adressat schweigt, kann gelesen und
# verworfen, ungelesen liegengeblieben oder nie angekommen sein. Von unserer Seite sieht
# das dreierlei gleich aus. `auftraege/gesehen.json` trägt die eine Auskunft, die wir uns
# nicht selbst geben können — und sie kommt vom Adressaten.


def test_ein_gesehener_auftrag_ohne_antwort_bekommt_die_neue_lage(tmp_path):
    """**Die einzige Lage, die nicht geraten ist.** Sie darf sich darum auf einen Vermerk
    berufen statt auf eine Vermutung — genau das steht in ihrem Grundtext."""
    _lege_auftrag(tmp_path, "auf-20260901-01", "cloud", "2026-09-01T00:00:00Z")
    _vermerke(tmp_path, "auf-20260901-01")
    assert auftragspost.vermerke_gesehen(
        tmp_path, ["auf-20260901-01"], von="cloud",
        bemerkung="im Chat bestaetigt", jetzt="2026-09-10T08:00:00Z") == 1

    (befund,) = auftragspost.warum_keine_antwort(tmp_path, heute=_date(2026, 9, 16))

    assert befund["lage"] == auftragspost.GESEHEN_OHNE_ANTWORT
    assert "Nachfrage" in befund["grund"]
    assert "2026-09-10" in befund["grund"], "ohne Datum ist der Vermerk eine Behauptung"
    assert "im Chat bestaetigt" in befund["grund"]


def test_der_vermerk_schlaegt_kein_lebenszeichen(tmp_path):
    """**Derselbe Auftrag, einmal ohne und einmal mit Vermerk.**

    Ohne Vermerk ist `kein lebenszeichen` richtig: Wer seit Wochen nichts schickt, hat die
    Mahnung vielleicht ebenso wenig gesehen wie den Auftrag. Mit Vermerk ist dieselbe
    Zurückhaltung falsch — ein bestätigter Blick ist stärker als jeder Schluss aus dem
    Antwortverhalten.
    """
    _lege_auftrag(tmp_path, "auf-20260901-01", "cloud", "2026-09-01T00:00:00Z")
    _lege_antwort(tmp_path, "auf-20260820-02", "cloud", "2026-08-20T00:00:00Z")
    _vermerke(tmp_path, "auf-20260901-01", "auf-20260820-02")

    vorher = {e["auftrag_id"]: e["lage"] for e in
              auftragspost.warum_keine_antwort(tmp_path, heute=_date(2026, 9, 16))}
    assert vorher["auf-20260901-01"] == auftragspost.KEIN_LEBENSZEICHEN

    auftragspost.vermerke_gesehen(tmp_path, ["auf-20260901-01"], von="cloud",
                                  jetzt="2026-09-12T08:00:00Z")

    nachher = {e["auftrag_id"]: e["lage"] for e in
               auftragspost.warum_keine_antwort(tmp_path, heute=_date(2026, 9, 16))}
    assert nachher["auf-20260901-01"] == auftragspost.GESEHEN_OHNE_ANTWORT


def test_der_vermerk_schlaegt_auch_aktiv_uebergangen(tmp_path):
    """Auch gegen die andere Vermutungslage — sie ist aus dem Antwortverhalten geschlossen,
    der Vermerk ist bestätigt."""
    _lege_auftrag(tmp_path, "auf-20260901-01", "cloud", "2026-09-01T00:00:00Z")
    _lege_antwort(tmp_path, "auf-20260905-02", "cloud", "2026-09-05T00:00:00Z")
    _vermerke(tmp_path, "auf-20260901-01", "auf-20260905-02")
    auftragspost.vermerke_gesehen(tmp_path, ["auf-20260901-01"], von="cloud",
                                  jetzt="2026-09-12T08:00:00Z")

    lagen = {e["auftrag_id"]: e["lage"] for e in
             auftragspost.warum_keine_antwort(tmp_path, heute=_date(2026, 9, 16))}
    assert lagen["auf-20260901-01"] == auftragspost.GESEHEN_OHNE_ANTWORT


def test_ohne_vermerk_bleibt_es_bei_der_vermutung(tmp_path):
    """**Die Gegenprobe.** Sonst bekäme jeder Auftrag die neue Lage, und sie sagte nichts
    mehr — eine Lage, die immer gilt, unterscheidet nichts."""
    _lege_auftrag(tmp_path, "auf-20260901-01", "cloud", "2026-09-01T00:00:00Z")
    _lege_auftrag(tmp_path, "auf-20260902-03", "cloud", "2026-09-02T00:00:00Z", rang=3)
    _vermerke(tmp_path, "auf-20260901-01", "auf-20260902-03")
    auftragspost.vermerke_gesehen(tmp_path, ["auf-20260901-01"], von="cloud",
                                  jetzt="2026-09-12T08:00:00Z")

    lagen = {e["auftrag_id"]: e["lage"] for e in
             auftragspost.warum_keine_antwort(tmp_path, heute=_date(2026, 9, 16))}
    assert lagen["auf-20260901-01"] == auftragspost.GESEHEN_OHNE_ANTWORT
    assert lagen["auf-20260902-03"] == auftragspost.KEIN_LEBENSZEICHEN, (
        "der Vermerk gilt je Kennung und nicht je Adressat")


def test_ein_zweiter_vermerk_ueberschreibt_den_ersten_nicht(tmp_path):
    """**Der erste Blick ist der, der zählt.**

    Ein späterer Eintrag mit neuem Datum wäre eine zweite Wahrheit — und zwar die
    bequemere: Er liesse den Auftrag bei jedem Lauf wieder jung aussehen. Seit wann der
    Adressat ihn kennt, steht dann nirgends mehr.
    """
    _lege_auftrag(tmp_path, "auf-20260901-01", "cloud", "2026-09-01T00:00:00Z")
    assert auftragspost.vermerke_gesehen(
        tmp_path, ["auf-20260901-01"], von="cloud", bemerkung="erster Blick",
        jetzt="2026-09-05T08:00:00Z") == 1
    assert auftragspost.vermerke_gesehen(
        tmp_path, ["auf-20260901-01"], von="cloud", bemerkung="zweiter Blick",
        jetzt="2026-09-14T08:00:00Z") == 0, "nichts NEU eingetragen"

    eintrag = auftragspost.gesehen_vermerke(tmp_path)["auf-20260901-01"]
    assert eintrag["am"] == "2026-09-05T08:00:00Z"
    assert eintrag["bemerkung"] == "erster Blick"
    assert eintrag["von"] == "cloud"


def test_neue_kennungen_kommen_dazu_ohne_die_alten_zu_verlieren(tmp_path):
    """Die Gegenprobe zum Überschreibschutz: Er darf nicht die ganze Ablage einfrieren."""
    auftragspost.vermerke_gesehen(tmp_path, ["auf-20260901-01"], von="ui",
                                  jetzt="2026-09-05T08:00:00Z")
    assert auftragspost.vermerke_gesehen(
        tmp_path, ["auf-20260901-01", "auf-20260902-02"], von="ui",
        jetzt="2026-09-14T08:00:00Z") == 1

    vermerke = auftragspost.gesehen_vermerke(tmp_path)
    assert set(vermerke) == {"auf-20260901-01", "auf-20260902-02"}
    assert vermerke["auf-20260901-01"]["am"] == "2026-09-05T08:00:00Z"
    assert vermerke["auf-20260902-02"]["am"] == "2026-09-14T08:00:00Z"


def test_ohne_bemerkung_steht_dort_None_und_nicht_leer(tmp_path):
    """*None heisst NICHT GEMESSEN* — hier: wir wissen nicht, woher die Auskunft kam. Ein
    leerer Text sähe aus wie eine Bemerkung, die jemand geschrieben hat."""
    auftragspost.vermerke_gesehen(tmp_path, ["auf-20260901-01"], von="ui",
                                  jetzt="2026-09-05T08:00:00Z")
    assert auftragspost.gesehen_vermerke(tmp_path)["auf-20260901-01"]["bemerkung"] is None


def test_ein_nie_zugestellter_auftrag_bleibt_nicht_zugestellt_auch_mit_vermerk(tmp_path):
    """**Die Reihenfolge, und warum sie so herum richtig ist.**

    «Gesehen» schliesst die Zustellung logisch ein — stehen beide Angaben gegeneinander,
    ist das ein Fehler in UNSERER Buchführung: Der Zustellvermerk wurde beim Ausliefern
    vergessen. Liesse man ihn hier vom Blickvermerk zudecken, verschwände die einzige
    Stelle, an der dieses Versäumnis noch auffällt — und die Handlungsanweisung wäre die
    falsche: nachfragen, statt die eigene Ablage in Ordnung zu bringen.
    """
    _lege_auftrag(tmp_path, "auf-20260901-01", "ui", "2026-09-01T00:00:00Z")
    auftragspost.vermerke_gesehen(tmp_path, ["auf-20260901-01"], von="ui",
                                  jetzt="2026-09-12T08:00:00Z")

    (befund,) = auftragspost.warum_keine_antwort(tmp_path, heute=_date(2026, 9, 16))

    assert befund["lage"] == auftragspost.NICHT_ZUGESTELLT
    assert "bei UNS" in befund["grund"]


def test_ein_frischer_auftrag_bleibt_frisch_auch_mit_vermerk(tmp_path):
    """Dass er ihn gesehen hat, macht ein Ausbleiben von einem Tag nicht zum Befund. *Erst
    messen, dann mahnen.*"""
    _lege_auftrag(tmp_path, "auf-20260915-01", "cloud", "2026-09-15T00:00:00Z")
    _vermerke(tmp_path, "auf-20260915-01")
    auftragspost.vermerke_gesehen(tmp_path, ["auf-20260915-01"], von="cloud",
                                  jetzt="2026-09-15T08:00:00Z")

    (befund,) = auftragspost.warum_keine_antwort(tmp_path, heute=_date(2026, 9, 16))
    assert befund["lage"] == auftragspost.FRISCH


def test_die_neue_lage_steht_in_LAGEN_und_traegt_den_vereinbarten_wortlaut():
    """Der Wortlaut ist eine Schnittstelle: `tools/` und die Auswertungen vergleichen ihn."""
    assert auftragspost.GESEHEN_OHNE_ANTWORT == "gesehen, ohne antwort"
    assert auftragspost.GESEHEN_OHNE_ANTWORT in auftragspost.LAGEN
    assert len(set(auftragspost.LAGEN)) == 5


def test_eine_unlesbare_gesehen_datei_wird_zum_fehler_und_nicht_zu_leerlauf(tmp_path):
    """**Anders als beim Zustellvermerk, und mit Absicht.**

    Dort ist «kaputt = nichts zugestellt» die sichere Richtung: Sie kostet eine
    Auslieferung zu viel. Hier gibt es keine sichere Richtung — «leer» hiesse «niemand hat
    hingesehen» und verwandelte eine bestätigte Tatsache still in eine Vermutung. *Ein
    unlesbares Buch heisst weder «nichts gesehen» noch «alles gesehen».*
    """
    _lege_auftrag(tmp_path, "auf-20260901-01", "cloud", "2026-09-01T00:00:00Z")
    _vermerke(tmp_path, "auf-20260901-01")
    ziel = tmp_path / auftragspost.GESEHEN_DATEI
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text("{kein json", encoding="utf-8")

    with pytest.raises(auftragspost.PostError, match="nicht lesbar"):
        auftragspost.gesehen_vermerke(tmp_path)

    # UND SIE REISST AUCH DIE AUSWERTUNG AB, statt sie mit Vermutungen weiterlaufen zu
    # lassen. Ohne diese zweite Zeile prüfte die Probe nur die Hilfsfunktion — und
    # `warum_keine_antwort` dürfte den Fehler still schlucken.
    with pytest.raises(auftragspost.PostError):
        auftragspost.warum_keine_antwort(tmp_path, heute=_date(2026, 9, 16))


def test_eine_fehlende_gesehen_datei_ist_kein_fehler(tmp_path):
    """Die Gegenprobe: Keine Datei heisst «noch nie hat jemand einen Blick bestätigt» —
    der Normalzustand dieses Repos, und kein Befund."""
    assert auftragspost.gesehen_vermerke(tmp_path) == {}


def test_ein_unbekannter_adressat_wird_abgewiesen(tmp_path):
    """Ein Tippfehler in `von` erzeugt einen Vermerk, den keine Auswertung je einem Worker
    zuordnet — er stünde da und wirkte nirgends."""
    with pytest.raises(auftragspost.PostError, match="kein bekannter Adressat"):
        auftragspost.vermerke_gesehen(tmp_path, ["auf-20260901-01"], von="cloudd")
    assert not (tmp_path / auftragspost.GESEHEN_DATEI).exists()


def test_der_vermerk_wird_in_einem_zug_ersetzt(tmp_path):
    """**Atomar wie der Zustellvermerk.** Eine halb geschriebene Datei wäre hier schlimmer
    als dort: `gesehen_vermerke` lässt sie hart fehlschlagen, also könnte ein Abbruch
    mitten im Schreiben die Rückstandsfrage ganz unbeantwortbar machen.

    Geprüft wird an der Spur: Nach dem Lauf liegt genau eine Datei da, kein Rest einer
    Zwischendatei.
    """
    auftragspost.vermerke_gesehen(tmp_path, ["auf-20260901-01"], von="ui",
                                  jetzt="2026-09-05T08:00:00Z")
    dateien = sorted(p.name for p in (tmp_path / "auftraege").iterdir())
    assert dateien == ["gesehen.json"], dateien
    assert json.loads((tmp_path / auftragspost.GESEHEN_DATEI).read_text(
        encoding="utf-8"))["auf-20260901-01"]["von"] == "ui"


def test_ein_von_hand_eingetragener_zeitstempel_bringt_die_auswertung_nicht_zu_fall(tmp_path):
    """Die Ablage wird auch von Hand gepflegt. Eine Kennung mit blossem Zeitstempel statt
    des Wörterbuchs ist eine richtige Auskunft in falscher Form — sie deshalb zu verwerfen
    hiesse, den bestätigten Blick wegen seiner Schreibweise zu vergessen."""
    _lege_auftrag(tmp_path, "auf-20260901-01", "cloud", "2026-09-01T00:00:00Z")
    _vermerke(tmp_path, "auf-20260901-01")
    ziel = tmp_path / auftragspost.GESEHEN_DATEI
    ziel.write_text(json.dumps({"auf-20260901-01": "2026-09-11T00:00:00Z"}),
                    encoding="utf-8")

    (befund,) = auftragspost.warum_keine_antwort(tmp_path, heute=_date(2026, 9, 16))
    assert befund["lage"] == auftragspost.GESEHEN_OHNE_ANTWORT
    assert "2026-09-11" in befund["grund"]


def test_ein_leerer_bemerkungstext_wird_zu_None_und_nicht_zu_leerem_text(tmp_path):
    """Ein leerer Text sähe in der Ablage aus wie eine Bemerkung und wäre keine.

    Der Unterschied ist nicht kosmetisch: ``""`` liest sich als «jemand hat hier etwas
    hingeschrieben, und es war nichts», ``None`` als **nicht gemessen**. Der Grund, warum
    wir von dem Blick wissen, ist genau die Auskunft, die diesen Vermerk von einer
    Vermutung unterscheidet — fehlt sie, muss das dastehen.
    """
    _lege_auftrag(tmp_path, "auf-20260901-01", "cloud", "2026-09-01T00:00:00Z")
    _vermerke(tmp_path, "auf-20260901-01")

    for leer in ("", "   ", "\n\t "):
        pfad = tmp_path / auftragspost.GESEHEN_DATEI
        if pfad.is_file():
            pfad.unlink()
        auftragspost.vermerke_gesehen(tmp_path, ["auf-20260901-01"], von="cloud",
                                      bemerkung=leer, jetzt="2026-09-10T08:00:00Z")
        eintrag = auftragspost.gesehen_vermerke(tmp_path)["auf-20260901-01"]
        assert eintrag["bemerkung"] is None, (
            f"{leer!r} muss zu None werden, war {eintrag['bemerkung']!r}")

    # Und der Grund erscheint dann auch nicht als leerer Anhang im Befund.
    befund = auftragspost.warum_keine_antwort(tmp_path, heute=_date(2026, 9, 16))
    eintrag = [b for b in befund if b["auftrag_id"] == "auf-20260901-01"][0]
    assert eintrag["lage"] == auftragspost.GESEHEN_OHNE_ANTWORT
    assert "Vermerk:" not in eintrag["grund"], (
        f"Ohne Bemerkung darf kein leeres «Vermerk:» angehängt werden: {eintrag['grund']!r}")


# ── Nachgezogen bei der Gegenprüfung (16.09.2026) ─────────────────────────────────────
#
# Zwei Wächter standen ohne Probe da: Der `isinstance`-Wächter in `gesehen_vermerke` liess
# sich entschärfen, ohne dass eine Probe fiel, und das atomare Schreiben ebenso. Und zwei
# Eingaben wurden still falsch verarbeitet statt abgewiesen.


def test_eine_einzelne_kennung_statt_einer_folge_wird_abgewiesen(tmp_path):
    """**Gemessen, nicht vermutet.** Vor dieser Prüfung trug
    ``vermerke_gesehen(wurzel, "auf-1", von="ui")`` fünf Vermerke ein — «a», «u», «f»,
    «-», «1» — und meldete ``5`` zurück. Eine Zeichenkette ist auch eine Folge, und zwar
    eine von Buchstaben. Kein Aufruf wäre gescheitert, kein Auftrag je gefunden worden,
    und der Rückstand hätte ab da eine Zahl getragen, die nichts zählt.
    """
    with pytest.raises(auftragspost.PostError, match="einzelne Kennung"):
        auftragspost.vermerke_gesehen(tmp_path, "auf-20260901-01", von="ui")
    assert not (tmp_path / auftragspost.GESEHEN_DATEI).exists()


def test_eine_liste_mit_einer_kennung_geht_weiterhin(tmp_path):
    """Die Gegenprobe: Der Wächter darf nur die Zeichenkette treffen, nicht den
    Einzelfall."""
    assert auftragspost.vermerke_gesehen(
        tmp_path, ["auf-20260901-01"], von="ui", jetzt="2026-09-05T08:00:00Z") == 1
    assert list(auftragspost.gesehen_vermerke(tmp_path)) == ["auf-20260901-01"]


def test_eine_gesehen_datei_mit_einer_liste_wird_zum_fehler(tmp_path):
    """Lesbares JSON in der falschen Gestalt — und damit **keine** Auskunft über
    irgendeinen Blick.

    Dieser Fall stand bis zum 16.09.2026 ohne Probe da: Der Wächter liess sich durch
    ``return {}`` ersetzen, ohne dass eine einzige Probe fiel. Still als «niemand hat
    hingesehen» gelesen, wäre er genau die Verwandlung einer Tatsache in eine Vermutung,
    gegen die diese Ablage gebaut ist.
    """
    ziel = tmp_path / auftragspost.GESEHEN_DATEI
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text('["auf-20260901-01"]', encoding="utf-8")

    with pytest.raises(auftragspost.PostError, match="kein Wörterbuch"):
        auftragspost.gesehen_vermerke(tmp_path)


def test_ein_abbruch_mitten_im_schreiben_laesst_die_alte_ablage_stehen(tmp_path,
                                                                      monkeypatch):
    """**Die Probe, die das atomare Schreiben wirklich hält.**

    Die vorhandene Probe prüft nur die Spur danach — sie bleibt grün, wenn man das
    Ersetzen durch ein schlichtes Überschreiben tauscht. Hier bricht der letzte Schritt
    ab: Danach muss die alte Ablage **unverändert** dastehen und kein Rest der
    Zwischendatei herumliegen. Ein Überschreiben hätte die alte Datei da schon
    abgeschnitten — und `gesehen_vermerke` liesse den Rückstand ab dann hart scheitern.
    """
    auftragspost.vermerke_gesehen(tmp_path, ["auf-20260901-01"], von="ui",
                                  jetzt="2026-09-05T08:00:00Z")
    vorher = (tmp_path / auftragspost.GESEHEN_DATEI).read_text(encoding="utf-8")

    def _abbruch(*args, **kwargs):
        raise OSError("Abbruch mitten im Schreiben")

    monkeypatch.setattr(auftragspost.os, "replace", _abbruch)
    with pytest.raises(OSError):
        auftragspost.vermerke_gesehen(tmp_path, ["auf-20260902-02"], von="ui",
                                      jetzt="2026-09-14T08:00:00Z")

    assert (tmp_path / auftragspost.GESEHEN_DATEI).read_text(encoding="utf-8") == vorher
    assert sorted(p.name for p in (tmp_path / "auftraege").iterdir()) == ["gesehen.json"]


def test_eine_zeichenkette_als_zustellung_wird_abgewiesen_und_nicht_zerlegt(tmp_path):
    """**Dieselbe Falle wie beim Blickvermerk, nur älter — und hier wiegt sie schwerer.**

    ``vermerke_zustellung(wurzel, "auf-1")`` legte bis zum 16.09.2026 fünf Zustellvermerke
    an: ``a``, ``u``, ``f``, ``-``, ``1``. Kein Aufruf scheiterte, keine Datei fehlte.

    Der Schaden ist nicht der Unsinn im Buch, sondern was danebensteht: Der **echte**
    Auftrag bleibt `nicht zugestellt` — in genau der Lage, die nach unserer eigenen Lesart
    *unser* Fehler ist — während das Buch aussieht, als sei fleissig ausgeliefert worden.
    *Ein Fehlschlag, der wie ein Erfolg aussieht, wird nicht gefunden; er wird geglaubt.*
    """
    with pytest.raises(auftragspost.PostError, match="einzelne Kennung"):
        auftragspost.vermerke_zustellung(tmp_path, "auf-20260901-01")

    assert not (tmp_path / auftragspost.ZUSTELLUNG_DATEI).exists(), (
        "Ein abgewiesener Aufruf darf keine halbe Ablage hinterlassen.")

    # GEGENPROBE: Die Liste mit einer einzigen Kennung geht weiter — der Wächter darf
    # nicht den Normalfall treffen.
    auftragspost.vermerke_zustellung(tmp_path, ["auf-20260901-01"], wann="2026-09-05T08:00:00Z")
    vermerk = json.loads((tmp_path / auftragspost.ZUSTELLUNG_DATEI).read_text(encoding="utf-8"))
    assert vermerk == {"auf-20260901-01": "2026-09-05T08:00:00Z"}


# ── Der Einstieg zum Blickvermerk (16.09.2026) ────────────────────────────────────────
#
# `vermerke_gesehen` stand seit demselben Tag, und es gab keinen Weg, sie zu benutzen,
# ohne Python von Hand zu schreiben. Damit existierte sie praktisch nicht: Die Auskunft
# «drueben hat jemand hingesehen» kommt muendlich, per Zustellbeleg oder als Nebensatz in
# einem Ergebnis — also immer dann, wenn gerade niemand ein Schnipsel tippt. Ohne Vermerk
# raet `warum_keine_antwort` weiter, und ihr Raten heisst `kein lebenszeichen` — genau die
# Lage, in der wir ausdruecklich NICHT mahnen.


def _repo_mit_offenen(tmp_path):
    """Zwei offene Auftraege, beide zugestellt, beide alt genug fuer eine Aussage."""
    _lege_auftrag(tmp_path, "auf-20260901-01", "cloud", "2026-09-01T00:00:00Z")
    _lege_auftrag(tmp_path, "auf-20260902-02", "ui", "2026-09-02T00:00:00Z", rang=2)
    _vermerke(tmp_path, "auf-20260901-01", "auf-20260902-02")
    return tmp_path


def test_der_einstieg_traegt_den_vermerk_wirklich_ein_und_die_lage_springt_um(tmp_path):
    """**Der ganze Zweck dieses Einstiegs, in einer Probe.**

    Nicht «der Aufruf lief durch», sondern: Der Vermerk liegt in der Ablage, und die
    Auswertung sagt daraufhin etwas anderes als vorher. Ein Einstieg, der schreibt, ohne
    dass die Auswertung es merkt, waere ein Fehlschlag, der wie ein Erfolg aussieht.
    """
    repo = _repo_mit_offenen(tmp_path)
    vorher = {e["auftrag_id"]: e["lage"] for e in
              auftragspost.warum_keine_antwort(repo, heute=_date(2026, 9, 16))}
    assert vorher["auf-20260901-01"] == auftragspost.KEIN_LEBENSZEICHEN

    assert _cli().main(["--repo", str(repo), "--gesehen", "auf-20260901-01",
                        "--von", "cloud"]) == 0

    assert auftragspost.gesehen_vermerke(repo)["auf-20260901-01"]["von"] == "cloud"
    nachher = {e["auftrag_id"]: e["lage"] for e in
               auftragspost.warum_keine_antwort(repo, heute=_date(2026, 9, 16))}
    assert nachher["auf-20260901-01"] == auftragspost.GESEHEN_OHNE_ANTWORT
    assert nachher["auf-20260902-02"] == auftragspost.KEIN_LEBENSZEICHEN, (
        "der Vermerk gilt je Kennung und nicht je Adressat")


def test_die_bemerkung_erreicht_die_ablage(tmp_path):
    """*Woher wir es wissen* ist die Angabe, die den Vermerk von einer Vermutung trennt."""
    repo = _repo_mit_offenen(tmp_path)
    assert _cli().main(["--repo", str(repo), "--gesehen", "auf-20260901-01",
                        "--von", "cloud", "--bemerkung", "im Chat bestaetigt"]) == 0
    eintrag = auftragspost.gesehen_vermerke(repo)["auf-20260901-01"]
    assert eintrag["bemerkung"] == "im Chat bestaetigt"


def test_eine_unbekannte_kennung_wird_abgewiesen_und_hinterlaesst_keine_halbe_ablage(
        tmp_path, capsys):
    """**Die fuenfte Regel am Einstieg.**

    Ein Tippfehler legte sonst einen Vermerk fuer einen Auftrag an, den es nicht gibt. Der
    wirkt nie — `warum_keine_antwort` schlaegt seine Kennungen in `auftraege/offen/` nach
    und findet diese nicht —, waehrend der ECHTE Auftrag in seiner Vermutungslage
    stehenbleibt und die Ablage ordentlich aussieht. *Ein Fehlschlag, der wie ein Erfolg
    aussieht, wird nicht gefunden; er wird geglaubt.*

    Und die zweite Haelfte ist die wichtigere: Auch die Kennung daneben, die es gibt, wird
    NICHT vermerkt. Erst pruefen, dann schreiben — eine halbe Ablage sieht ordentlich aus.
    """
    repo = _repo_mit_offenen(tmp_path)

    assert _cli().main(["--repo", str(repo), "--gesehen", "auf-20260901-01",
                        "auf-20260901-99", "--von", "cloud"]) == 2

    assert not (repo / auftragspost.GESEHEN_DATEI).exists(), (
        "Ein abgewiesener Aufruf darf keine halbe Ablage hinterlassen.")
    fehler = capsys.readouterr().err
    assert "auf-20260901-99" in fehler, "die falsche Kennung muss dastehen"
    assert "auf-20260901-01" not in fehler.split("gibt es hier nicht:")[1].split("\n")[0]


def test_ein_unbekannter_adressat_wird_auch_am_einstieg_abgewiesen(tmp_path, capsys):
    """Der Waechter steht in der Bibliothek; diese Probe haelt fest, dass der Einstieg ihn
    nicht verschluckt — und dass ein Missgriff eine Meldung ist und kein Stapelauszug."""
    repo = _repo_mit_offenen(tmp_path)

    assert _cli().main(["--repo", str(repo), "--gesehen", "auf-20260901-01",
                        "--von", "cloudd"]) == 2

    assert not (repo / auftragspost.GESEHEN_DATEI).exists()
    assert "kein bekannter Adressat" in capsys.readouterr().err


def test_ohne_von_wird_nichts_vermerkt(tmp_path, capsys):
    """«Jemand hat es gesehen» beantwortet keine der Fragen, fuer die es den Vermerk gibt —
    und stuende trotzdem in der Ablage, von keiner Auswertung einem Worker zuzuordnen."""
    repo = _repo_mit_offenen(tmp_path)

    assert _cli().main(["--repo", str(repo), "--gesehen", "auf-20260901-01"]) == 2

    assert not (repo / auftragspost.GESEHEN_DATEI).exists()
    assert "--von" in capsys.readouterr().err


def test_ein_zweiter_vermerk_meldet_schon_vermerkt_statt_still_nichts_zu_tun(
        tmp_path, capsys):
    """**Das gehoert dem Benutzer gesagt, sonst haelt er es fuer einen Fehlschlag.**

    Der erste Blick ist der, der zaehlt; ein zweiter ueberschreibt nicht. Ohne Meldung
    saehe «0 neu» aus, als haette das Werkzeug versagt — und der naechste Griff waere, von
    Hand in die Datei zu schreiben.
    """
    repo = _repo_mit_offenen(tmp_path)
    # BEIDE KENNUNGEN GEHOEREN `cloud`. Die erste Fassung dieser Probe nahm die zweite
    # Kennung von `ui` und trug sie unter `--von cloud` ein — genau der Widerspruch, den
    # der Waechter seit dem 16.09.2026 abweist: Die Ablage haette «von cloud» gesagt und
    # die Ansicht «ui hat ihn gesehen».
    _lege_auftrag(repo, "auf-20260903-03", "cloud", "2026-09-03T00:00:00Z", rang=3)
    assert _cli().main(["--repo", str(repo), "--gesehen", "auf-20260901-01",
                        "--von", "cloud"]) == 0
    erster = auftragspost.gesehen_vermerke(repo)["auf-20260901-01"]["am"]
    capsys.readouterr()

    # Rueckgabe 1 = «nichts NEU» — wie `1` beim Postlauf «nichts offen» heisst. Kein
    # Fehler, aber ohne den Text zu lesen von «eingetragen» unterscheidbar.
    assert _cli().main(["--repo", str(repo), "--gesehen", "auf-20260901-01",
                        "auf-20260903-03", "--von", "cloud"]) == 0
    ausgabe = capsys.readouterr().out
    assert "schon vermerkt" in ausgabe, (
        "Ein stiller Nicht-Eintrag sieht aus wie ein Fehlschlag.")
    assert "auf-20260901-01" in ausgabe
    assert auftragspost.gesehen_vermerke(repo)["auf-20260901-01"]["am"] == erster, (
        "der erste Blick wurde ueberschrieben")


def test_alles_schon_vermerkt_meldet_null_neu_und_unterscheidet_sich(tmp_path, capsys):
    """Die Gegenprobe zur Rueckgabe: Nichts Neu ist kein Fehler (**2**) und kein
    Eintrag (**0**), sondern **1**."""
    repo = _repo_mit_offenen(tmp_path)
    assert _cli().main(["--repo", str(repo), "--gesehen", "auf-20260901-01",
                        "--von", "cloud"]) == 0
    assert _cli().main(["--repo", str(repo), "--gesehen", "auf-20260901-01",
                        "--von", "cloud"]) == 1
    assert "0 von 1" in capsys.readouterr().out


def test_von_ohne_gesehen_wirkt_nicht_still(tmp_path, capsys):
    """*Ein Bedienelement ohne Wirkung ist schlimmer als keines: Es sagt, etwas sei
    geschehen.* Dieselbe Regel, an der am 01.09.2026 `--nach` aufgefallen ist."""
    repo = _repo_mit_offenen(tmp_path)
    assert _cli().main(["cloud", "--repo", str(repo), "--von", "cloud"]) == 2
    assert "NICHTS vermerkt" in capsys.readouterr().err
    assert not (repo / auftragspost.GESEHEN_DATEI).exists()


def test_die_ansicht_zeigt_jeden_offenen_mit_adressat_alter_und_lage(tmp_path, capsys):
    """**Ohne diese Ansicht muesste man die JSON-Ablage lesen**, um zu sehen, ob ein
    Vermerk gewirkt hat — und wer die Ablage liest, liest sie irgendwann statt der
    Auswertung."""
    repo = _repo_mit_offenen(tmp_path)

    assert _cli().main(["--repo", str(repo), "--warum"]) == 0

    ausgabe = capsys.readouterr().out
    # GEPRUEFT WIRD DIE ZEILE, NICHT DIE GESAMTAUSGABE — und das ist der Unterschied
    # zwischen einer Probe und einer Beruhigung. Die erste Fassung suchte die Lage
    # irgendwo im Text; sie blieb gruen, als ich die Lage aus der Zeile entfernte, weil
    # die Zusammenfassung unten sie ebenfalls nennt. *Ein Waechter, der nicht faellt,
    # bewacht nichts* — gemessen am 16.09.2026 als Mutation M6.
    zeilen = {z.split()[0]: z for z in ausgabe.splitlines() if z.startswith("auf-")}
    assert set(zeilen) == {"auf-20260901-01", "auf-20260902-02"}
    assert "cloud" in zeilen["auf-20260901-01"], "ohne Adressat weiss man nicht, wer liegt"
    assert "ui" in zeilen["auf-20260902-02"]
    for zeile in zeilen.values():
        assert auftragspost.KEIN_LEBENSZEICHEN in zeile, (
            f"ohne Lage ist es eine blosse Liste: {zeile!r}")
        assert "Tage" in zeile, (
            f"ohne Alter fehlt die Angabe, ob das Ausbleiben etwas heisst: {zeile!r}")
    # AELTESTE ZUERST — sonst steht der dringendste Posten irgendwo mittendrin.
    assert ausgabe.index("auf-20260901-01") < ausgabe.index("auf-20260902-02")


def test_die_ansicht_zeigt_dass_der_vermerk_gewirkt_hat(tmp_path, capsys):
    """Die beiden neuen Wege zusammen: eintragen, dann nachsehen. Das ist der Handgriff,
    fuer den es sie gibt."""
    repo = _repo_mit_offenen(tmp_path)
    _cli().main(["--repo", str(repo), "--warum"])
    assert auftragspost.GESEHEN_OHNE_ANTWORT not in capsys.readouterr().out

    _cli().main(["--repo", str(repo), "--gesehen", "auf-20260901-01", "--von", "cloud",
                 "--bemerkung", "im Chat bestaetigt"])
    capsys.readouterr()

    assert _cli().main(["--repo", str(repo), "--warum"]) == 0
    ausgabe = capsys.readouterr().out
    assert auftragspost.GESEHEN_OHNE_ANTWORT in ausgabe
    assert "im Chat bestaetigt" in ausgabe, "der Grund des Vermerks gehoert in die Ansicht"


def test_die_ansicht_filtert_auf_einen_adressaten(tmp_path, capsys):
    repo = _repo_mit_offenen(tmp_path)
    assert _cli().main(["ui", "--repo", str(repo), "--warum"]) == 0
    ausgabe = capsys.readouterr().out
    assert "auf-20260902-02" in ausgabe
    assert "auf-20260901-01" not in ausgabe


def test_die_ansicht_ohne_offene_meldet_es_und_unterscheidet_sich(tmp_path, capsys):
    """Rueckgabe **1** wie beim Postlauf: kein Fehler, aber ohne Textlesen erkennbar."""
    repo = _repo_mit_offenen(tmp_path)
    assert _cli().main(["local", "--repo", str(repo), "--warum"]) == 1
    assert "Nichts offen" in capsys.readouterr().out


def test_die_ansicht_meldet_ein_unbestimmbares_alter_als_solches(tmp_path, capsys):
    """**Die dritte Antwort in der Anzeige.** Ein unlesbares Erstelldatum heisst NICHT
    GEMESSEN — niemals `0 Tage`. Eine Null waere die bequemste Luege der ganzen Ansicht:
    Sie liesse den aeltesten Posten von heute sein.
    """
    _lege_auftrag(tmp_path, "auf-20260901-01", "cloud", "keindatum")
    _vermerke(tmp_path, "auf-20260901-01")

    assert _cli().main(["--repo", str(tmp_path), "--warum"]) == 0

    zeile = [z for z in capsys.readouterr().out.splitlines()
             if z.startswith("auf-20260901-01")][0]
    assert "?" in zeile, f"ein unbestimmbares Alter muss als solches dastehen: {zeile!r}"
    assert "0 Tage" not in zeile, f"nicht gemessen ist nicht null: {zeile!r}"


def test_eine_unlesbare_ablage_wird_in_der_ansicht_gemeldet_und_nicht_geworfen(
        tmp_path, capsys):
    """Die Auswertung reisst bei unlesbarer `gesehen.json` mit Absicht ab. Am Einstieg
    wird daraus eine Meldung — ein Stapelauszug ist keine Auskunft."""
    repo = _repo_mit_offenen(tmp_path)
    (repo / auftragspost.GESEHEN_DATEI).write_text("{kein json", encoding="utf-8")

    assert _cli().main(["--repo", str(repo), "--warum"]) == 2
    assert "nicht lesbar" in capsys.readouterr().err


def test_von_wirkt_auch_neben_der_ansicht_nicht_still(tmp_path, capsys):
    """Die Gegenprobe zur Stellung des Waechters: Er stand zuerst NACH dem Ansichtszweig,
    und dort waere `--von` stumm durchgelaufen — ein Schalter ohne Wirkung, an derselben
    Stelle wie die Meldung, dass alles in Ordnung sei."""
    repo = _repo_mit_offenen(tmp_path)
    assert _cli().main(["--repo", str(repo), "--warum", "--von", "cloud"]) == 2
    assert "NICHTS vermerkt" in capsys.readouterr().err


# ── Nachgezogen bei der Gegenpruefung am 16.09.2026 ───────────────────────────────────
#
# Drei Luecken, alle von derselben Art: Etwas geschieht (oder geschieht gerade NICHT),
# und keine Probe faellt, wenn man es abschaltet.


def test_ein_von_das_nicht_dem_adressaten_gehoert_wird_abgewiesen(tmp_path, capsys):
    """**Der Vermerk wuerde eine Unwahrheit anzeigen, und sie waere nicht zu loeschen.**

    `warum_keine_antwort` liest den Adressaten des AUFTRAGS und nicht das ``von`` des
    Vermerks. Ein Blickvermerk `von: cloud` auf einem ui-Auftrag laesst die Ansicht «ui
    hat ihn gesehen» melden — waehrend in der Ablage cloud steht. Gemessen am 16.09.2026
    von Hand, bevor der Waechter da war.

    Und die zweite Haelfte: Der erste Blick zaehlt, ein zweiter ueberschreibt ihn nie —
    ein falsches ``--von`` ist durch das Werkzeug **nicht mehr zurueckzunehmen**.
    """
    repo = _repo_mit_offenen(tmp_path)

    assert _cli().main(["--repo", str(repo), "--gesehen", "auf-20260902-02",
                        "--von", "cloud"]) == 2

    assert not (repo / auftragspost.GESEHEN_DATEI).exists(), (
        "ein Widerspruch darf keine Ablage hinterlassen — sie waere nicht zu loeschen")
    fehler = capsys.readouterr().err
    assert "gehoert ui" in fehler, f"wem er gehoert, ist die Auskunft: {fehler!r}"


def test_ein_tippfehler_im_von_meldet_den_tippfehler_und_nicht_die_kennung(
        tmp_path, capsys):
    """Die Gegenprobe zur Reihenfolge der beiden Waechter.

    Ein unbekanntes ``--von`` passt zu KEINEM Adressaten — der Widerspruchswaechter wuerde
    also zuerst anschlagen und «auf-… gehoert cloud» melden. Das ist wahr und zeigt auf
    die falsche Stelle: Der Fehler steckt in ``--von``, nicht in der Kennung.
    """
    repo = _repo_mit_offenen(tmp_path)

    assert _cli().main(["--repo", str(repo), "--gesehen", "auf-20260901-01",
                        "--von", "cloudd"]) == 2

    fehler = capsys.readouterr().err
    assert "kein bekannter Adressat" in fehler, fehler
    assert "gehoert" not in fehler, (
        f"der Widerspruchswaechter zeigt hier auf die falsche Stelle: {fehler!r}")


def test_ein_unlesbarer_auftrag_ist_kein_widerspruch(tmp_path, capsys):
    """**Die dritte Antwort im Waechter selbst.** Wessen Auftrag es ist, steht in der
    Datei; ist sie unlesbar, wissen wir es NICHT — und «wir wissen es nicht» ist kein
    Widerspruch. Ein Waechter, der aus Unkenntnis abweist, verhindert den richtigen
    Vermerk genauso wie den falschen.
    """
    repo = _repo_mit_offenen(tmp_path)
    (repo / "auftraege" / "offen" / "auf-20260901-01.json").write_text(
        "{kaputt", encoding="utf-8")

    assert _cli().main(["--repo", str(repo), "--gesehen", "auf-20260901-01",
                        "--von", "ui"]) == 0
    assert auftragspost.gesehen_vermerke(repo)["auf-20260901-01"]["von"] == "ui"


def test_ein_schalter_neben_gesehen_wirkt_nicht_still(tmp_path, capsys):
    """**Dieselbe Regel wie bei `--von`, nur in der anderen Richtung.**

    Gemessen am 16.09.2026: `--gesehen … --von cloud --nach raus/ --vermerken` trug den
    Blick ein, legte **keine** Datei an, zog **keinen** Zustellvermerk nach — und meldete
    «gesehen vermerkt», Rueckgabe 0. Drei Handgriffe verlangt, einer geschehen, kein Wort
    darueber. *Ein Fehlschlag, der wie ein Erfolg aussieht, wird nicht gefunden; er wird
    geglaubt.*
    """
    repo = _repo_mit_offenen(tmp_path)
    ziel = tmp_path / "raus"

    assert _cli().main(["--repo", str(repo), "--gesehen", "auf-20260901-01",
                        "--von", "cloud", "--nach", str(ziel), "--vermerken"]) == 2

    assert not (repo / auftragspost.GESEHEN_DATEI).exists(), "auch der Vermerk unterbleibt"
    assert not ziel.exists()
    fehler = capsys.readouterr().err
    assert "--nach" in fehler and "--vermerken" in fehler, fehler


def test_die_ansicht_neben_gesehen_wird_nicht_verschluckt(tmp_path, capsys):
    """«Eintragen und gleich nachsehen» ist der naheliegendste Handgriff ueberhaupt — und
    er lief still nur halb durch: Der Vermerk wurde geschrieben, die Lage nie gezeigt."""
    repo = _repo_mit_offenen(tmp_path)

    assert _cli().main(["--repo", str(repo), "--gesehen", "auf-20260901-01",
                        "--von", "cloud", "--warum"]) == 2

    assert not (repo / auftragspost.GESEHEN_DATEI).exists()
    assert "--warum" in capsys.readouterr().err


def test_ein_schalter_neben_der_ansicht_wirkt_nicht_still(tmp_path, capsys):
    """Die Ansicht liest nur. `--nach` daneben schrieb nichts und sagte nichts."""
    repo = _repo_mit_offenen(tmp_path)
    ziel = tmp_path / "raus"

    assert _cli().main(["--repo", str(repo), "--warum", "--nach", str(ziel)]) == 2

    assert not ziel.exists()
    assert "--nach" in capsys.readouterr().err


def test_der_positionsadressat_filtert_die_ansicht_und_wird_nicht_abgewiesen(
        tmp_path, capsys):
    """Die Gegenprobe zum Waechter darueber: `ui --warum` **wirkt** (es filtert), also
    darf es nicht als wirkungslos gelten. Ein Waechter, der das Richtige abweist, ist
    schlimmer als keiner."""
    repo = _repo_mit_offenen(tmp_path)
    assert _cli().main(["ui", "--repo", str(repo), "--warum"]) == 0
    assert "auf-20260902-02" in capsys.readouterr().out


def test_die_ansicht_zaehlt_je_lage_und_die_summe_stimmt(tmp_path, capsys):
    """**Die Zaehlung unten trug keine Probe.**

    Sie ist die einzige Zeile, die man liest, wenn zwanzig Auftraege offen sind — und sie
    ordnet nach :data:`aiimaging.auftragspost.LAGEN`, also von «unser Fehler» zu «wir
    wissen es nicht». In derselben Reihenfolge ist zu handeln; eine andere Reihenfolge
    waere eine andere Empfehlung.
    """
    _lege_auftrag(tmp_path, "auf-20260901-01", "cloud", "2026-09-01T00:00:00Z")
    _lege_auftrag(tmp_path, "auf-20260902-02", "ui", "2026-09-02T00:00:00Z", rang=2)
    # NUR DER ZWEITE IST ZUGESTELLT — der erste steht damit bei UNS, der zweite bei ihm.
    _vermerke(tmp_path, "auf-20260902-02")

    assert _cli().main(["--repo", str(tmp_path), "--warum"]) == 0

    zeile = [z for z in capsys.readouterr().out.splitlines() if z.startswith("2 offen:")]
    assert zeile, "ohne Zaehlung muss man zwanzig Zeilen selbst addieren"
    assert f"1x {auftragspost.NICHT_ZUGESTELLT}" in zeile[0]
    assert f"1x {auftragspost.KEIN_LEBENSZEICHEN}" in zeile[0]
    # DIE REIHENFOLGE IST DIE HANDLUNGSANWEISUNG, nicht Schmuck.
    assert (zeile[0].index(auftragspost.NICHT_ZUGESTELLT)
            < zeile[0].index(auftragspost.KEIN_LEBENSZEICHEN))
    # UND KEINE LAGE OHNE FALL — sonst stuende dauerhaft «0x» da und verdeckte die echten.
    assert "0x" not in zeile[0]


def test_ein_von_hand_eingetragener_zeitstempel_wird_vertragen(tmp_path, capsys):
    """Die Ablage wird von Hand gepflegt — die Auskunft kommt muendlich oder als Nebensatz
    in einem Ergebnis. Steht dort ein blosser Zeitstempel statt des Woerterbuchs, ist das
    eine richtige Auskunft in ungewohnter Form; daran abzustuerzen hiesse, sie wegen ihrer
    Form zu verwerfen (dieselbe Milde wie in `warum_keine_antwort`).

    **Und wessen Blick es war, wird NICHT erfunden:** Der blosse Zeitstempel sagt es
    nicht, also steht dort `unbekannt` und nicht der Adressat des Auftrags.
    """
    repo = _repo_mit_offenen(tmp_path)
    (repo / auftragspost.GESEHEN_DATEI).write_text(
        json.dumps({"auf-20260901-01": "2026-09-05T10:00:00Z"}), encoding="utf-8")

    assert _cli().main(["--repo", str(repo), "--gesehen", "auf-20260901-01",
                        "--von", "cloud"]) == 1

    ausgabe = capsys.readouterr().out
    assert "gesehen am 2026-09-05" in ausgabe, ausgabe
    assert "von unbekannt" in ausgabe, (
        f"wessen Blick es war, sagt der blosse Zeitstempel nicht: {ausgabe!r}")


def test_ein_blickvermerk_von_uns_selbst_wird_abgewiesen(tmp_path):
    """**Der teuerste Fehler, den diese Ablage machen kann.**

    Alle anderen Lagen von :func:`warum_keine_antwort` lesen unsere eigene Buchführung.
    ``gesehen, ohne antwort`` liest das eine, was wir uns **nicht selbst geben können**:
    dass drüben jemand hingesehen hat. Genau darum schlägt diese Lage die beiden
    Vermutungslagen.

    Ein Eintrag mit ``von="kern"`` hiesse *«wir haben gesehen, dass wir es geschrieben
    haben»* — und er würde die Vermutungslagen trotzdem schlagen, obwohl er selbst nichts
    als eine dritte Vermutung ist. *Eine Zahl, die aussieht wie eine Tatsache von drüben
    und von uns kommt, ist schlimmer als gar keine.*
    """
    _lege_auftrag(tmp_path, "auf-20260901-01", "cloud", "2026-09-01T00:00:00Z")

    with pytest.raises(auftragspost.PostError, match="sind wir selbst"):
        auftragspost.vermerke_gesehen(tmp_path, ["auf-20260901-01"],
                                      von=auftragspost.SELBST)

    assert not (tmp_path / auftragspost.GESEHEN_DATEI).exists(), (
        "Ein abgewiesener Aufruf darf keine halbe Ablage hinterlassen.")

    # GEGENPROBE: Die echten Adressaten gehen weiter durch — der Riegel darf nicht
    # einfach alles abweisen.
    for adressat in ("cloud", "ui", "local"):
        pfad = tmp_path / auftragspost.GESEHEN_DATEI
        if pfad.is_file():
            pfad.unlink()
        assert auftragspost.vermerke_gesehen(
            tmp_path, ["auf-20260901-01"], von=adressat,
            jetzt="2026-09-05T08:00:00Z") == 1, f"{adressat} muss durchgehen"


def test_MUTATION_ohne_den_selbst_riegel_schlaegt_ein_eigener_vermerk_die_vermutung(tmp_path):
    """**MUTATIONSPROBE.** Der Riegel weg — und wir belegen uns selbst.

    Ohne ihn trägt `warum_keine_antwort` die Lage ``gesehen, ohne antwort`` für einen
    Auftrag, den **niemand ausser uns** je angesehen hat.

    **Und die Probe hat gezeigt, dass es schlimmer ist als gedacht.** Die Auswertung nennt
    den Adressaten des *Auftrags*, nicht das ``von`` des Vermerks — das ist so gewollt und
    anderswo begründet. Ein Eintrag von uns erscheint darum nicht als *«kern hat
    hingesehen»*, sondern als **«cloud hat ihn gesehen»**: eine Aussage über einen Dritten,
    die wir selbst erzeugt haben und die er nie gemacht hat. Wer den Befund liest, sieht
    uns darin nirgends.

    *Genau deshalb wird der Eintrag vorne abgewiesen und nicht hinten gekennzeichnet.*
    """
    _lege_auftrag(tmp_path, "auf-20260901-01", "cloud", "2026-09-01T00:00:00Z")
    _vermerke(tmp_path, "auf-20260901-01")

    echt = auftragspost.warum_keine_antwort(tmp_path, heute=_date(2026, 9, 16))
    assert echt[0]["lage"] == auftragspost.KEIN_LEBENSZEICHEN, "ohne Vermerk: Vermutung"

    urspruenglich = auftragspost.SELBST
    try:
        auftragspost.SELBST = "niemand-mit-diesem-namen"   # der Riegel greift nicht mehr
        auftragspost.vermerke_gesehen(tmp_path, ["auf-20260901-01"], von="kern",
                                      jetzt="2026-09-05T08:00:00Z")
    finally:
        auftragspost.SELBST = urspruenglich

    ohne = auftragspost.warum_keine_antwort(tmp_path, heute=_date(2026, 9, 16))
    assert ohne[0]["lage"] == auftragspost.GESEHEN_OHNE_ANTWORT, (
        "Ohne Riegel muss der eigene Vermerk die Vermutungslage schlagen — sonst prüft "
        "der Riegel etwas anderes, als seine Begründung behauptet.")

    # UND HIER IST ES SCHLIMMER, ALS DER RIEGEL BEHAUPTET. Die Auswertung nennt den
    # Adressaten des AUFTRAGS und nicht das `von` des Vermerks (so gewollt, siehe
    # `tools/auftragspost.py`). Ein Eintrag von uns erscheint damit nicht als «kern hat
    # hingesehen», sondern als «CLOUD hat ihn gesehen» — eine Aussage über einen Dritten,
    # die wir selbst erzeugt haben und die er nie gemacht hat.
    assert "cloud hat ihn gesehen" in ohne[0]["grund"], (
        f"Der Grund schreibt den eigenen Vermerk dem Adressaten zu: {ohne[0]['grund']!r}")
    assert "kern" not in ohne[0]["grund"], (
        "…und nennt uns dabei nirgends. Wer den Befund liest, sieht nicht, dass er von "
        "uns stammt — genau darum wird der Eintrag vorne abgewiesen und nicht hinten "
        "gekennzeichnet.")


def test_die_vertauschte_argumentreihenfolge_bekommt_einen_wegweiser(tmp_path):
    """Seit dem 17.09.2026 steht die Repo-Wurzel zuerst — wie überall sonst im Modul.

    Ein vertauschter Aufruf bräche ohnehin, aber mit ``TypeError: expected str, bytes or
    os.PathLike object, not list`` aus dem Inneren von ``pathlib``. Daran sieht niemand,
    was er falsch gemacht hat. *Ein Wegweiser kostet drei Zeilen; ein falsch gelesener
    Traceback kostet eine halbe Stunde.*
    """
    with pytest.raises(auftragspost.PostError, match="vertauscht"):
        auftragspost.vermerke_zustellung(["auf-20260901-01"], tmp_path)   # alte Ordnung

    assert not (tmp_path / auftragspost.ZUSTELLUNG_DATEI).exists()

    # GEGENPROBE: die neue Ordnung geht durch.
    auftragspost.vermerke_zustellung(tmp_path, ["auf-20260901-01"],
                                     wann="2026-09-05T08:00:00Z")
    vermerk = json.loads((tmp_path / auftragspost.ZUSTELLUNG_DATEI).read_text(encoding="utf-8"))
    assert vermerk == {"auf-20260901-01": "2026-09-05T08:00:00Z"}

    # Und die beiden Funktionen sind jetzt gleich gebaut — das war der ganze Punkt.
    import inspect
    erste = list(inspect.signature(auftragspost.vermerke_zustellung).parameters)[:2]
    zweite = list(inspect.signature(auftragspost.vermerke_gesehen).parameters)[:2]
    assert erste == zweite == ["repo_wurzel", "kennungen"], (
        f"Dieselbe Datei, zwei Reihenfolgen — genau das war der Befund: {erste} / {zweite}")
