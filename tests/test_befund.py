"""Was nicht in einer Datei steht, ist weg — der Satz gilt auch für Messwerte.

`CLAUDE.md` sagt ihn über die Sitzungsprotokolle. Bis zum 23.08.2026 galt er für die
Messwerte dieses Projekts **nicht**: Der Kompositionsbefund je Kamera, die Kameraspanne,
der Maskenbefund, die Einordnung gegen den Nullanker, das Sprachurteil über den Prompt —
alles wurde gerechnet, in ein Wörterbuch gelegt und mit dem Prozess vergessen. Geschrieben
wurden genau zwei Dinge: die drei Vertragsfelder der fremden Oberfläche und die
Seedauswahl.

Der fremde Vertrag ist nicht der Ort dafür, und ihn zu erweitern ist nicht unsere
Entscheidung. Also eine Datei daneben.
"""
import json
from pathlib import Path

import pytest

from aiimaging import abholer
from conftest import MINI_PNG

PNG = MINI_PNG


def _verschiedene_sollkarten():
    """Eine `_soll`-Attrappe, die je Aufruf eine ANDERE Karte liefert.

    Seit dem 26.08.2026 erkennt `verarbeiter` byte-identische Soll-Karten als dieselbe
    Ansicht und rendert sie nur einmal (`_sollkennung`). Eine Attrappe mit fester Karte
    liesse drei bestellte Kameras zu einer werden — und jeder Test darueber pruefte
    stillschweigend den Doppelungsfall statt den, der dasteht.
    """
    zaehler = iter(range(1, 999))

    def soll(*a, **k):
        return [[float(next(zaehler))]], 1, 1

    return soll


@pytest.fixture
def lauf(tmp_path):
    """Ein Auftrag, der bis zum geschriebenen Befund durchläuft."""
    from aiimaging import bruecke

    ordner = tmp_path / "vis-1787123048-098c6e"
    ordner.mkdir()
    (ordner / bruecke.DATEI_LAUFZETTEL).write_text(json.dumps(
        {"job_id": ordner.name, "status": bruecke.STATUS_QUEUED,
         "approval_token": "CONFIRMED_RENDER_a1b2c3d4"}), encoding="utf-8")
    (ordner / bruecke.DATEI_SZENE).write_text(json.dumps(
        {"schema": bruecke.kosmo_szene.SCHEMA_SZENE,
         "geometry": {"path": "model.glb", "format": "glb"},
         "cameras": "auto",
         "style": {"prompt": "bedeckter Himmel, keine Menschen"},
         "render": {"resolution": [64, 64], "samples": 1}}), encoding="utf-8")
    (ordner / bruecke.DATEI_MODELL).write_bytes(b"glTF\x02\x00\x00\x00")

    bild = tmp_path / "bild.png"
    scores = iter([0.81, 0.66, 0.74])

    def multipass(glb, aus, **kw):
        tiefe = Path(aus) / "tiefe_norm.png"
        tiefe.parent.mkdir(parents=True, exist_ok=True)
        tiefe.write_bytes(PNG)
        return {"depth_png": str(tiefe), "kamera": {"weg": "rueckfall"}}

    def rendere(auftrag, **kw):
        bild.write_bytes(PNG)
        return {"status": "ok", "bild_png": str(bild), "hinweise": ()}

    antwort = abholer.hole_einen(
        ordner, fremde_freigabe_gilt=True,
        verarbeite=abholer.verarbeiter(
            out_wurzel=tmp_path / "aus", nullprobe=False,
            _multipass=multipass, _rendere=rendere,
            _qa=lambda *a, **k: {"score": next(scores), "bestanden": True},
            # Je Kamera eine ANDERE Soll-Karte. Drei byte-identische waeren seit dem
            # 26.08.2026 eine erkannte Doppelansicht — dann rendert die Kette einmal und
            # dieser Test pruefte etwas anderes, als er behauptet.
            _soll=_verschiedene_sollkarten()))
    return ordner, antwort


def test_der_befund_wird_ueberhaupt_geschrieben(lauf):
    ordner, antwort = lauf
    assert antwort["tat"] == abholer.TAT_VERARBEITET
    assert (ordner / abholer.DATEI_BEFUND).is_file()


def test_er_traegt_die_beurteilungen_die_der_vertrag_streicht(lauf):
    """Der eigentliche Punkt: Genau das, was `nur_vertragsfelder` heraustrennt."""
    ordner, _ = lauf
    befund = json.loads((ordner / abholer.DATEI_BEFUND).read_text(encoding="utf-8"))

    assert befund["schema"] == "aiimaging.befund/v1"
    assert len(befund["kameras"]) == 3
    for kamera in befund["kameras"]:
        assert "komposition" in kamera
        assert "maskenbefund" in kamera
        assert "einordnung" in kamera
    assert befund["geometrie_urteil"]["kameraspanne"]["n_gemessen"] == 3


def test_er_traegt_den_prompt_in_BEIDEN_fassungen(lauf):
    """Was gerendert wurde und was ankam. Ein Protokoll, das nur die Übersetzung führt,
    macht die Übersetzung unüberprüfbar."""
    ordner, _ = lauf
    befund = json.loads((ordner / abholer.DATEI_BEFUND).read_text(encoding="utf-8"))

    assert befund["prompt"] == "overcast sky, no people"
    assert befund["prompt_original"] == "bedeckter Himmel, keine Menschen"
    assert befund["prompt_sprache"]["verfahren"] == "glossar"


def test_er_traegt_die_warnungen_des_auftrags(lauf):
    ordner, _ = lauf
    befund = json.loads((ordner / abholer.DATEI_BEFUND).read_text(encoding="utf-8"))
    assert any("übersetzt" in w for w in befund["warnungen_auftrag"])


# ======================================================================================
# Regel 3 — kein Rechnername, kein Benutzerkonto nach draussen
# ======================================================================================

def test_kein_absoluter_pfad_steht_im_befund(lauf):
    """Der Befund liegt im Auftragsverzeichnis der fremden Oberfläche. Ein absoluter
    Pfad trüge den Rechnernamen und das Benutzerkonto mit hinaus."""
    ordner, _ = lauf
    roh = (ordner / abholer.DATEI_BEFUND).read_text(encoding="utf-8")

    assert '"/' not in roh, "ein Textwert beginnt mit einem Schrägstrich"
    assert "/tmp/" not in roh and "/home/" not in roh


def test_die_kuerzung_greift_rekursiv_und_in_listen():
    tief = {"a": "/x/y/bild.png", "b": [{"c": "/p/q/karte.exr"}, "harmlos"],
            "d": Path("/r/s/datei.json"), "e": 7, "f": None}
    gekuerzt = abholer._ohne_pfade(tief)

    assert gekuerzt["a"] == "bild.png"
    assert gekuerzt["b"][0]["c"] == "karte.exr"
    assert gekuerzt["b"][1] == "harmlos"
    assert gekuerzt["d"] == "datei.json"
    assert gekuerzt["e"] == 7 and gekuerzt["f"] is None


def test_relative_pfade_und_gewoehnlicher_text_bleiben_ganz():
    """Gekürzt wird, was wie ein absoluter Pfad aussieht — nicht jeder Text mit
    Schrägstrich. Sonst verlöre ein Hinweis wie 'nah/fern' seine Hälfte."""
    assert abholer._ohne_pfade("aus/sSE/bild.png") == "aus/sSE/bild.png"
    assert abholer._ohne_pfade("nah = hell, fern = dunkel") == "nah = hell, fern = dunkel"
    assert abholer._ohne_pfade("/") == "/"


# ======================================================================================
# Der Befund darf den Lauf nicht kosten
# ======================================================================================

def test_ein_unschreibbarer_befund_haelt_den_auftrag_nicht_auf(tmp_path, monkeypatch):
    """Die Bilder sind da, das Vertragsergebnis ist geschrieben. Dieselbe Entscheidung
    wie beim Auswahlbericht — aber sie steht im Grund, statt zu schweigen."""
    antwort = {"grund": "3 Bild(er) geschrieben."}

    def kaputt(*a, **k):
        raise OSError("kein Platz")

    monkeypatch.setattr(Path, "write_text", kaputt)
    abholer._befund_ablegen(tmp_path, {"job_id": "x"}, {"bilder": []}, antwort)

    assert "nicht geschrieben" in antwort["grund"]
    assert "3 Bild(er)" in antwort["grund"], "der ursprüngliche Grund bleibt stehen"


def test_etwas_nicht_json_faehiges_wird_gemeldet_statt_zu_werfen(tmp_path):
    antwort = {"grund": ""}
    abholer._befund_ablegen(tmp_path, {"job_id": "x"},
                            {"kameras": [{"seltsam": object()}]}, antwort)
    assert "nicht geschrieben" in antwort["grund"]


def test_der_befund_wird_NACH_dem_vertragsergebnis_geschrieben(lauf):
    """Die Reihenfolge, an der die fremde Oberfläche hängt, darf er nicht stören.

    Sie liest den Laufzettel; steht dort `done`, holt sie das Ergebnis. Der Befund ist
    unsere eigene Buchführung und kommt zuletzt.
    """
    from aiimaging import bruecke

    ordner, _ = lauf
    assert (ordner / bruecke.DATEI_ERGEBNIS).is_file()
    assert (ordner / abholer.DATEI_BEFUND).stat().st_mtime >= \
        (ordner / bruecke.DATEI_ERGEBNIS).stat().st_mtime


# ======================================================================================
# Gelesen, nicht nur geschrieben
# ======================================================================================

def test_der_befund_wird_wirklich_zurueckgelesen(lauf):
    """Eine Datei, die niemand liest, ist die tote Kante in ihrer geduldigsten Form.

    Sie fällt nie auf, und wenn eines Tages jemand hinsieht, steht seit Monaten Unsinn
    darin. Darum liest das Betreiber-Werkzeug sie wirklich.
    """
    ordner, _ = lauf
    befund = abholer.lies_befund(ordner)
    assert befund is not None
    assert befund["schema"] == "aiimaging.befund/v1"


def test_ein_fehlender_befund_ist_eine_auskunft_und_kein_fehler(tmp_path):
    assert abholer.lies_befund(tmp_path) is None
    assert abholer.lies_befund(tmp_path / "gibtsnicht") is None


def test_ein_kaputter_befund_wirft_nicht(tmp_path):
    (tmp_path / abholer.DATEI_BEFUND).write_text("{kein json", encoding="utf-8")
    assert abholer.lies_befund(tmp_path) is None
    (tmp_path / abholer.DATEI_BEFUND).write_text('["Liste statt Woerterbuch"]',
                                                 encoding="utf-8")
    assert abholer.lies_befund(tmp_path) is None


# ======================================================================================
# Die kurze Fassung — was einen Menschen am Terminal erreicht
# ======================================================================================

def test_die_kurzfassung_nennt_die_uebersetzung_und_die_kameraspanne(lauf):
    ordner, _ = lauf
    zeilen = abholer.befund_kurz(abholer.lies_befund(ordner))
    text = "\n".join(zeilen)

    assert "uebersetzt" in text
    assert "bedeckter Himmel" in text, "der ursprüngliche Wortlaut gehört dazu"
    assert "schlechteste von 3 Kameras" in text


def test_eine_halbe_uebersetzung_bekommt_ihre_eigene_zeile():
    """Der Fall, auf den es ankommt: Der Prompt WURDE übersetzt, aber nicht ganz.

    Ohne diese Zeile stünde nur „Prompt uebersetzt" da, und der Betreiber hielte einen
    halbdeutschen Prompt für einen englischen. Ein halb übersetzter Prompt ist für das
    Bildmodell schlechter als ein ganz deutscher — er steht zwischen zwei Sprachen.
    """
    zeilen = abholer.befund_kurz({
        "prompt": "overcast sky, a Fensterbank",
        "prompt_sprache": {"noetig": True, "verfahren": "glossar",
                           "original": "bedeckter Himmel, eine Fensterbank",
                           "vollstaendig": False, "unbekannt": ("fensterbank",)}})
    assert any("NICHT vollstaendig" in z and "fensterbank" in z for z in zeilen)


def test_eine_ganze_uebersetzung_bekommt_diese_zeile_nicht():
    """Gegenprobe — sonst stünde die Warnung immer da und bedeutete nichts."""
    zeilen = abholer.befund_kurz({
        "prompt": "overcast sky",
        "prompt_sprache": {"noetig": True, "verfahren": "glossar",
                           "original": "bedeckter Himmel", "vollstaendig": True}})
    assert any("uebersetzt" in z for z in zeilen)
    assert not any("NICHT vollstaendig" in z for z in zeilen)


def test_zeilen_ohne_inhalt_entfallen_ganz():
    """Eine Ausgabe, in der jede Zeile immer dasteht, liest sich nach dem dritten Mal
    wie eine leere."""
    still = abholer.befund_kurz({
        "prompt_sprache": {"noetig": False},
        "geometrie_urteil": {"kameraspanne": {"n_gemessen": 1, "schlechtester": 0.7,
                                              "bester": 0.7}},
        "kameras": [{"kamera": "sSE", "komposition": {"beurteilt": True,
                                                      "warnungen": []}}],
    })
    assert len(still) == 1, still
    assert "Geometrie" in still[0]


def test_was_nur_EINE_kamera_betrifft_wird_einzeln_genannt():
    """Das ist die Zeile, die jemanden hinsehen lässt."""
    zeilen = abholer.befund_kurz({
        "kameras": [
            {"kamera": "s", "komposition": {"beurteilt": True,
                                            "warnungen": ["Neigung 2.0° statt 0°"]}},
            {"kamera": "sSE", "komposition": {"beurteilt": True, "warnungen": []}},
        ]})
    assert any("nur s: Neigung" in z for z in zeilen)
    assert not any("alle" in z for z in zeilen), (
        "nichts betrifft hier alle — sSE ist unbeanstandet"
    )


def test_was_ALLE_kameras_betrifft_steht_einmal_da():
    """Der Anlass, gemessen am eigenen Ausgabetext: Ohne Geländestand meldet die Prüfung
    für JEDE Kamera denselben unzuverlässigen Bezugspunkt und dieselbe Neigung — bei
    zwölf Kameras zwölf von zwölf, immer dieselben zwei.

    Eine Warnung, die bei jedem Lauf und für jede Kamera erscheint, ist kein Signal mehr.
    Beide sind richtig; sie sind nur keine Befunde über DIESEN Auftrag, sondern
    Eigenschaften der Eingabe.
    """
    kameras = [{"kamera": k, "komposition": {
        "beurteilt": True,
        "warnungen": ["Bezugspunkt 'huellbox_unterkante' ist …", f"Neigung 2.{i}° …"]}}
        for i, k in enumerate(("s", "sSE", "nNW"))]
    zeilen = abholer.befund_kurz({"kameras": kameras})

    assert len(zeilen) == 1, zeilen
    assert zeilen[0].startswith("Komposition, alle 3 Kameras: Bezugspunkt, Neigung")


def test_gemeinsames_und_einzelnes_werden_getrennt():
    """Der Fall, um den es geht: Das Dauerrauschen fällt auf eine Zeile zusammen, und
    die eine Kamera mit einem echten Problem steht heraus."""
    kameras = [{"kamera": k, "komposition": {
        "beurteilt": True, "warnungen": ["Bezugspunkt …", "Neigung …"]
        + (["Abstand 9.00 m unterschreitet …"] if k == "nNW" else [])}}
        for k in ("s", "sSE", "nNW")]
    zeilen = abholer.befund_kurz({"kameras": kameras})

    assert len(zeilen) == 2
    assert zeilen[0].startswith("Komposition, alle 3 Kameras: Bezugspunkt, Neigung")
    assert zeilen[1] == "Komposition, nur nNW: Abstand"


def test_eine_einzige_kamera_gilt_als_alle():
    """Bei einer Kamera ist „alle" und „nur diese" dasselbe — dann gewinnt die kürzere
    Fassung, statt beide Zeilen zu schreiben."""
    zeilen = abholer.befund_kurz({
        "kameras": [{"kamera": "sSE", "komposition": {"beurteilt": True,
                                                      "warnungen": ["Neigung …"]}}]})
    assert zeilen == ("Komposition, alle 1 Kameras: Neigung",)


def test_die_kurzfassung_trennt_beanstandet_von_nicht_beurteilbar():
    """Zwei verschiedene Aussagen: „geprüft und bemängelt" gegen „gar nicht prüfbar".
    Wer sie zusammenwirft, hält eine Lücke für ein Urteil."""
    zeilen = abholer.befund_kurz({
        "kameras": [{"kamera": "s", "komposition": {"beurteilt": False, "grund": "..."}}]})
    assert zeilen == ("Komposition NICHT beurteilbar: s",)


def test_die_kurzfassung_meldet_einen_unbelegten_seedvorsprung():
    zeilen = abholer.befund_kurz({
        "kameras": [{"kamera": "s",
                     "seedauswahl": {"vorsprung": {"belegt": False}}},
                    {"kamera": "sSE",
                     "seedauswahl": {"vorsprung": {"belegt": True}}}]})
    treffer = [z for z in zeilen if "Seedvorsprung" in z]
    assert len(treffer) == 1
    assert "s" in treffer[0] and "sSE" not in treffer[0]


def test_ohne_seedauswahl_wird_dazu_nichts_behauptet():
    """`vorsprung: None` heisst „nicht geprüft" — und darf nicht als „nicht belegt"
    erscheinen.

    Die Gegenprobe steht im selben Test, weil das ``not any`` sonst über eine **leere**
    Liste liefe und immer wahr wäre. Die Vakuumprobe hat genau das gefunden, als dieser
    Test neu war.
    """
    ungeprueft = abholer.befund_kurz({
        "kameras": [{"kamera": "s", "seedauswahl": {"vorsprung": None}}]})
    assert ungeprueft == (), "aus 'nicht geprüft' folgt gar keine Zeile"

    geprueft = abholer.befund_kurz({
        "kameras": [{"kamera": "s", "seedauswahl": {"vorsprung": {"belegt": False}}}]})
    assert any("Seedvorsprung" in z for z in geprueft), (
        "dieselbe Sammlung, derselbe Aufbau — sie füllt sich, wenn es etwas zu melden gibt"
    )


def test_ohne_beurteilte_kamera_faellt_die_zusammenfassung_ganz_weg():
    """Hier stand ein Wächter (`if not beurteilt: return`). Die Mutationsprobe zeigte,
    dass er nie greift: Ist keine Kamera beurteilt, ergibt die Rechnung darunter ohnehin
    nichts. Entfernt und als Tatsache festgehalten — dieselbe Entscheidung wie bei der
    einspringenden Ecke in `raumkamera` (Sitzung 11).
    """
    assert abholer._kompositionszeilen([]) == []
    assert abholer._kompositionszeilen(
        [{"kamera": "s", "komposition": {"beurteilt": True, "warnungen": []}}]) == []
    assert abholer._kompositionszeilen(
        [{"kamera": "s", "komposition": {"beurteilt": False}}]) == \
        ["Komposition NICHT beurteilbar: s"]


def test_gar_kein_befund_ergibt_gar_keine_zeilen():
    assert abholer.befund_kurz(None) == ()
    assert abholer.befund_kurz("kein Woerterbuch") == ()
    assert abholer.befund_kurz({}) == ()


def test_die_dauerwarnung_nennt_den_handgriff():
    """Eine Warnung, die immer erscheint und gegen die man nichts tun kann, ist keine
    Warnung mehr, sondern Möblierung.

    Der unbekannte Geländestand erscheint bei jedem Auftrag — aus einer glb ist er nicht
    zu erfahren. Seit `verarbeiter(gelaende_z=…)` gibt es aber den Handgriff, und damit
    wird aus der Klage ein Angebot.
    """
    zeilen = abholer.befund_kurz({
        "kameras": [{"kamera": k, "komposition": {
            "beurteilt": True, "warnungen": ["Bezugspunkt 'huellbox_unterkante' …"]}}
            for k in ("s", "sSE", "nNW")]})

    assert len(zeilen) == 1
    assert "--gelaende-z" in zeilen[0]


def test_andere_dauerwarnungen_bekommen_keinen_falschen_handgriff():
    """Gegenprobe: Der Hinweis hängt an DIESER Warnung, nicht an jeder gemeinsamen.

    Stünde er überall, wäre er in dem Moment falsch, in dem eine andere Warnung alle
    Kameras betrifft — und ein falscher Rat ist schlimmer als keiner.
    """
    zeilen = abholer.befund_kurz({
        "kameras": [{"kamera": k, "komposition": {
            "beurteilt": True, "warnungen": ["Abstand 9.00 m unterschreitet …"]}}
            for k in ("s", "sSE")]})

    assert len(zeilen) == 1
    assert "Abstand" in zeilen[0]
    assert "gelaende" not in zeilen[0]


# ======================================================================================
# Der Maskenweg gehört auf die eine Bildschirmseite — nachgetragen 26.08.2026
# ======================================================================================

def test_ein_ausgefallener_maskenweg_steht_im_kurzbefund():
    """**Die Zeile, die drei Tage lang gefehlt hat.**

    Die HomeStation hat am 26.08.2026 gemeldet, dass in allen vier Läufen jenes Tages
    `rho_maske`, `kante` und `paarurteil` auf `None` standen — *und niemandem fiel es
    auf*. Der Grund stand im Maskenbefund je Kamera, also in einer Datei, die man
    aufschlagen muss, während oben auf dem Schirm ein Score steht.

    Die Folge ist keine Kleinigkeit: Ohne Maskenweg wird die gemessene Polarität nie
    angewandt, der Score fällt auf `abs(spearman)` zurück — **und in dem Modus besteht ein
    Bild mit vertauschter Tiefe das Tor.**
    """
    befund = {"kameras": [
        {"kamera": "s", "bild_png": "/x.png",
         "maskenbefund": {"maske": None, "grund": "Die Geländeregel passte auf nichts."}},
    ]}

    zeilen = "\n".join(abholer.befund_kurz(befund))

    assert "MASKENWEG NICHT GEFAHREN" in zeilen
    assert "abs(spearman)" in zeilen, "Die Folge gehört in denselben Satz."
    assert "vertauschter Tiefe" in zeilen, (
        "Und wozu sie führt — sonst liest sich die Zeile wie eine Formalie.")


def test_mit_maske_schweigt_der_kurzbefund():
    """Die Gegenprobe. **Eine Zeile, die immer dasteht, wird nicht gelesen.**

    Genau das ist an diesem Tag drei Dauerwarnungen passiert: Sie füllten alle drei Plätze
    und verdeckten jede echte.
    """
    befund = {"kameras": [
        {"kamera": "s", "bild_png": "/x.png", "maskenbefund": {"maske": [True, False]}},
    ]}

    assert not any("MASKENWEG" in z for z in abholer.befund_kurz(befund))


def test_eine_uebersprungene_kamera_meldet_keinen_maskenausfall():
    """Wo gar nicht gerendert wurde, ist der Maskenweg **nicht zuständig**.

    Sonst stünde bei jedem vom Rahmungsriegel abgelehnten Auftrag zusätzlich eine Zeile
    über einen Weg, den niemand fahren wollte — und die echte Meldung ginge darin unter.
    """
    befund = {"kameras": [
        {"kamera": "s", "bild_png": None, "rahmung": {"abbruch": True},
         "maskenbefund": {"maske": None, "grund": "irgendwas"}},
    ]}

    assert not any("MASKENWEG" in z for z in abholer.befund_kurz(befund))
