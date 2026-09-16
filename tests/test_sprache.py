"""Was hier geprüft wird, ist nicht „übersetzt sie richtig", sondern „lügt sie nie".

Ein Glossar kann nie vollständig sein. Was es aber können MUSS: sagen, wo es aufhört.
Die Tests unten stehen fast alle auf dieser einen Frage — meldet ``unbekannt``, was
stehengeblieben ist, und schweigt die Warnung, wo nichts zu warnen ist.
"""
from pathlib import Path

import pytest

from aiimaging import prompts, render, sprache

#: Ein PNG-Kopf. Für diese Tests zählt nur, dass die Datei existiert.
_PNG = b"\x89PNG\r\n\x1a\n"


# ======================================================================================
# Spracherkennung
# ======================================================================================

@pytest.mark.parametrize("text", [
    "bedeckter Himmel ohne Sonne",
    "ein Wohnhaus mit Flachdach",
    "Blick von der Straße",
    "keine Menschen und keine Bäume",
])
def test_deutsch_wird_erkannt(text):
    assert sprache.sieht_englisch_aus(text)["englisch"] is False


@pytest.mark.parametrize("text", [
    "overcast sky with no people",
    "seen from the street, the building behind trees",
    "a quiet photograph of the house",
])
def test_englisch_wird_erkannt(text):
    assert sprache.sieht_englisch_aus(text)["englisch"] is True


@pytest.mark.parametrize("text", ["", "   ", "24mm f8", "1600x1000"])
def test_ohne_signal_wird_nichts_behauptet(text):
    """``None`` heisst nicht entscheidbar — und das ist der ehrliche Befund.

    Wer hier ``True`` zurückgäbe, machte die Warnung stumm; wer ``False`` zurückgäbe,
    warnte vor jeder Objektivangabe.
    """
    assert sprache.sieht_englisch_aus(text)["englisch"] is None


def test_gemischt_zaehlt_als_nicht_englisch():
    """Der halbdeutsche Prompt ist der Fall, vor dem gewarnt werden soll."""
    befund = sprache.sieht_englisch_aus("a photograph mit einem Dach und Bäumen")
    assert befund["englisch"] is False
    assert befund["englische_funde"], "die englischen Funde gehören trotzdem in den Befund"
    assert "gemischt" in befund["begruendung"]


def test_die_signalwortlisten_ueberschneiden_sich_nicht():
    """Ein Wort in beiden Listen wäre ein Fehlalarm mit Anlauf — es entschiede nichts."""
    assert not (sprache.DEUTSCHE_SIGNALWOERTER & sprache.ENGLISCHE_SIGNALWOERTER)


def test_ein_umlaut_allein_genuegt():
    """Das stärkste Einzelmerkmal, das ein kurzer Text tragen kann."""
    befund = sprache.sieht_englisch_aus("Bäume")
    assert befund["englisch"] is False
    assert befund["umlaute"] is True
    assert befund["sicher"] is True, "ein Umlaut ist kein Hauch, sondern ein Befund"


def test_ein_einzelnes_signalwort_ist_unsicher():
    """Beide Sprachen, beide Schwellen — ein Hauch ist kein Befund.

    Die deutsche Hälfte fehlte zuerst, und die Mutation ``>= 2`` → ``>= 1`` überlebte
    darum auf der deutschen Seite. Ein Schwellwert ohne Test ist eine Zahl, die jemand
    hingeschrieben hat.
    """
    englisch = sprache.sieht_englisch_aus("photograph")
    assert englisch["englisch"] is True
    assert englisch["sicher"] is False

    deutsch = sprache.sieht_englisch_aus("Haus mit Garten")
    assert deutsch["englisch"] is False
    assert deutsch["deutsche_funde"] == ("mit",), "genau ein Signalwort, kein Umlaut"
    assert deutsch["sicher"] is False

    zwei = sprache.sieht_englisch_aus("Haus mit und ohne Garten")
    assert zwei["sicher"] is True, "zwei Signalwörter sind ein Befund"


# ======================================================================================
# Übersetzen
# ======================================================================================

def test_der_gemessene_fall():
    """Der Satz, der die ganze Übung ausgelöst hat.

    Am Gerät (HomeStation `9a33353`, 8 gepaarte Startwerte) ergab „bedeckter Himmel"
    8 von 8 Mal einen deutlich blaueren Himmel als „overcast sky".
    """
    assert sprache.uebersetze("bedeckter Himmel")["uebersetzt"] == "overcast sky"


def test_englischer_text_wird_nicht_angefasst():
    """Sonst stünde „übersetzt" im Protokoll, wo nichts übersetzt wurde."""
    ergebnis = sprache.uebersetze("overcast sky, no people")
    assert ergebnis["uebersetzt"] == ergebnis["original"]
    assert ergebnis["noetig"] is False
    assert ergebnis["verfahren"] == sprache.VERFAHREN_KEINE


def test_ein_einzelnes_fachwort_wird_erkannt():
    """„Beton" trägt kein Signalwort und keinen Umlaut — und ist trotzdem deutsch.

    Die erste Fassung liess es liegen, weil die Erkennung zu Recht „nicht entscheidbar"
    sagte. Das Glossar ist hier der zweite Zeuge.
    """
    ergebnis = sprache.uebersetze("Beton")
    assert ergebnis["uebersetzt"] == "concrete"
    assert ergebnis["anlass"] == "glossar"
    assert "beton" in ergebnis["evidenz"]


def test_woerter_die_auch_englisch_sind_beweisen_kein_deutsch():
    """`see`, `wind`, `film`, `material` stehen im Glossar — und sind ebenso englisch."""
    for text in ["I can see the wind in the film",
                 "material detail", "modern building", "warm light"]:
        assert sprache.uebersetze(text)["noetig"] is False, text


def test_kollisionen_sind_wirklich_glossarschluessel():
    """Ein Eintrag in ENGLISCH_AUCH, der gar nicht im Glossar steht, wirkt nie.

    Er sähe aus wie Vorsicht und wäre eine tote Kante. Erlaubt sind nur Schlüssel, die
    es auch gibt — der Rest gehört gelöscht.
    """
    fremd = {w for w in sprache.ENGLISCH_AUCH if w not in sprache.GLOSSAR}
    assert not fremd, (
        f"ENGLISCH_AUCH nennt Wörter ohne Glossareintrag: {sorted(fremd)}. Sie schützen "
        f"vor nichts."
    )


def test_laengste_wendung_zuerst():
    """Die Wendung schlägt das Einzelwort — geprüft an der Stelle, wo es zählt.

    Die erste Fassung dieses Tests prüfte „bedeckter Himmel" und „keine Menschen" und
    ÜBERLEBTE die Mutation ``-len(s)`` → ``len(s)``. Der Grund ist lehrreich: Bei beiden
    ergibt die Wort-für-Wort-Übersetzung zufällig dasselbe wie die Wendung
    (``keine`` + ``menschen`` = ``no`` + ``people``). Der Test prüfte also gar nicht die
    Reihenfolge, sondern nur, dass überhaupt übersetzt wird.

    ``hell gestrichen`` ist der Fall, an dem es auseinandergeht: Als Wendung ist es
    „painted in a pale tone", Wort für Wort wäre ``hell`` → ``bright``, und
    ``gestrichen`` bliebe deutsch stehen.
    """
    assert sprache.uebersetze("hell gestrichen")["uebersetzt"] == \
        "painted in a pale tone"


def test_jede_wendung_schlaegt_ihr_eigenes_erstes_wort():
    """Dieselbe Regel als Eigenschaft über das ganze Glossar, nicht an einem Beispiel.

    Für jeden Schlüssel, dessen Anfang selbst ein Schlüssel ist, muss die LANGE Fassung
    greifen. So bleibt die Regel auch dann geprüft, wenn jemand morgen eine Wendung
    hinzufügt, an die dieser Test nie gedacht hat.
    """
    paare = [(kurz, lang) for lang in sprache.GLOSSAR for kurz in sprache.GLOSSAR
             if lang.startswith(kurz + " ")]
    assert paare, "ohne solche Paare prüft dieser Test nichts — dann ist er zu löschen"
    for kurz, lang in paare:
        ersetzt = sprache.glossar_uebersetzung(lang)["ersetzt"]
        assert ersetzt == (lang,), (
            f"{lang!r} wurde als {ersetzt} zerlegt statt als Ganzes genommen; "
            f"das kürzere {kurz!r} hat gewonnen"
        )


def test_kleingeschrieben_auch_am_anfang():
    """Deutsch schreibt Hauptwörter gross; Englisch tut das nicht.

    Und der Freitext steht im fertigen Prompt nie am Anfang, sondern hinter der
    Handschrift des Stils — er ist immer satzmittig.
    """
    assert sprache.uebersetze("Beton")["uebersetzt"] == "concrete"
    assert sprache.uebersetze("Himmel und Bäume")["uebersetzt"] == "sky and trees"


def test_wortgrenzen_werden_geachtet():
    """`Betonung` ist kein Beton, `Wanderung` keine Wand."""
    for text in ["Betonung", "Wanderung", "Dachs"]:
        assert sprache.glossar_uebersetzung(text)["text"] == text, text


# ======================================================================================
# Die Grenze melden — das eigentliche Stück Arbeit
# ======================================================================================

def test_gebeugtes_wird_auf_seinen_stamm_zurueckgefuehrt():
    """Was die erste Fassung nur MELDEN konnte, übersetzt sie jetzt.

    „abendlicht mit langen Schatten" ergab „evening light with langen shadows". Der
    Stamm stand die ganze Zeit im Glossar; es fehlte die Endung. Gemessen an dreizehn
    Prompts, wie sie aus der Oberfläche kommen könnten: vorher war **einer** vollständig
    übersetzt, nachher **dreizehn**.
    """
    ergebnis = sprache.uebersetze("Abendlicht mit langen Schatten")
    assert ergebnis["uebersetzt"] == "evening light with long shadows"
    assert ergebnis["vollstaendig"] is True
    assert [r["art"] for r in ergebnis["regeln"]] == [sprache.ART_BEUGUNG]


def test_ein_zusammengesetztes_wort_wird_zerlegt_und_zeigt_seine_teile():
    ergebnis = sprache.uebersetze("Blick auf die Nordfassade")
    assert ergebnis["uebersetzt"] == "view on the north facade"
    regel = ergebnis["regeln"][0]
    assert regel["art"] == sprache.ART_KOMPOSITUM
    assert regel["teile"] == ("nord", "fassade"), (
        "die Teile stehen im Ergebnis, weil eine Regel anders irrt als ein Eintrag — "
        "wer den Prompt prüft, soll sehen, was das Glossar sich gedacht hat"
    )


def test_was_die_regeln_NICHT_koennen_wird_weiterhin_gemeldet():
    """Die Grenze bleibt, sie ist nur weitergerückt.

    ``Fensterbank`` ist ein Kompositum, dessen zweiter Teil nicht im Glossar steht. Es
    bleibt stehen — und wird gemeldet, nicht stillschweigend durchgereicht.
    """
    ergebnis = sprache.uebersetze("eine Fensterbank am Gebäude")
    assert ergebnis["vollstaendig"] is False
    assert "fensterbank" in ergebnis["unbekannt"]
    assert any("halb deutsch" in w for w in ergebnis["warnungen"])


def test_ein_dachs_ist_kein_dach():
    """Der Fund, der die Endung ``s`` gekostet hat.

    ``Dachs`` → Endung ``s`` abgestreift → ``dach`` → ``roof``. In einem Modul, das gegen
    erfundene Dächer gebaut ist, wäre das die denkbar falscheste Sorte Fehler.
    """
    assert sprache.grundform("Dachs") is None
    assert "roof" not in sprache.uebersetze("ein Dachs im Garten")["uebersetzt"]


def test_die_endung_n_musste_zurueck_denn_sie_traegt_die_mehrzahl():
    """``s`` und ``n`` sahen nach derselben Sorte Risiko aus. Nur eines war es.

    Der reguläre Plural der Feminina bildet sich mit ``n``: ``Fassade`` → ``Fassaden``.
    Ohne diese Endung bleibt jede Mehrzahl stehen — und Prompts sprechen von Fassaden,
    Terrassen und Treppen, nicht von einer Fassade.
    """
    assert sprache.grundform("Fassaden") == "fassade"
    assert sprache.grundform("Terrassen") == "terrasse"
    assert sprache.uebersetze("die Fassaden der Stadt")["uebersetzt"] == \
        "the facade the city"


def test_vollstaendig_heisst_wirklich_vollstaendig():
    ergebnis = sprache.uebersetze("Sichtbeton, verwittert, weiches Licht")
    assert ergebnis["vollstaendig"] is True
    assert ergebnis["unbekannt"] == ()
    assert ergebnis["warnungen"] == ()


def test_das_original_geht_nie_verloren():
    """Der Owner-Entscheid: übersetzen UND deklarieren. Ohne Original keine Prüfung."""
    ergebnis = sprache.uebersetze("bedeckter Himmel, keine Menschen")
    assert ergebnis["original"] == "bedeckter Himmel, keine Menschen"
    assert ergebnis["uebersetzt"] != ergebnis["original"]


# ======================================================================================
# Die Naht
# ======================================================================================

def test_ein_eigener_uebersetzer_wird_benutzt():
    def modell(text):
        return {"text": "TRANSLATED", "verfahren": "attrappe", "unbekannt": ()}

    ergebnis = sprache.uebersetze("bedeckter Himmel", uebersetzer=modell)
    assert ergebnis["uebersetzt"] == "TRANSLATED"
    assert ergebnis["verfahren"] == "attrappe"


def test_der_eigene_uebersetzer_bekommt_das_original():
    gesehen = []

    def modell(text):
        gesehen.append(text)
        return {"text": text, "verfahren": "attrappe"}

    sprache.uebersetze("bedeckter Himmel", uebersetzer=modell)
    assert gesehen == ["bedeckter Himmel"], (
        "der Übersetzer muss den unangetasteten Text sehen — sonst übersetzt er "
        "Glossarausgabe statt Eingabe"
    )


@pytest.mark.parametrize("antwort", [
    None, "nur ein String", {"text": "x"}, {"verfahren": "y"}, {"text": 3, "verfahren": "y"},
])
def test_ein_kaputter_uebersetzer_wird_laut(antwort):
    """Still übergehen hiesse: der deutsche Text läuft durch, und alles hier ist umsonst."""
    with pytest.raises(sprache.SprachError):
        sprache.uebersetze("bedeckter Himmel", uebersetzer=lambda t: antwort)


def test_sprach_error_ist_ein_value_error():
    assert issubclass(sprache.SprachError, ValueError)


# ======================================================================================
# Die Warnung
# ======================================================================================

def test_die_warnung_schweigt_beim_unentscheidbaren():
    """Eine Warnung, die bei `24mm f8` anschlägt, wird weggeklickt — und danach auch die
    richtige."""
    assert sprache.sprachwarnung("24mm f8") == ""
    assert sprache.sprachwarnung("overcast sky") == ""
    assert sprache.sprachwarnung("") == ""


def test_die_warnung_greift_beim_deutschen_prompt():
    warnung = sprache.sprachwarnung("bedeckter Himmel ohne Menschen")
    assert warnung
    assert "englisch" in warnung.lower()


# ======================================================================================
# Verdrahtung — ein Test am Baustein ersetzt keinen Test an der Naht
# ======================================================================================

def test_komponiere_uebersetzt_und_deklariert():
    ergebnis = prompts.komponiere(freitext="Sichtbeton, bedeckter Himmel")
    assert "exposed concrete" in ergebnis["prompt"]
    assert "Sichtbeton" not in ergebnis["prompt"]
    assert ergebnis["freitext"]["original"] == "Sichtbeton, bedeckter Himmel"
    assert ergebnis["freitext"]["uebersetzt"] == "exposed concrete, overcast sky"
    assert any("übersetzt" in h for h in ergebnis["hinweise"])


def test_komponiere_laesst_englisch_in_ruhe():
    """Gegenprobe im selben Test, damit das ``not any`` nicht über eine leere Liste läuft.

    Die Vakuumprobe fand genau das: Bei englischem Freitext ist ``hinweise`` leer, und
    „kein Übersetzungshinweis" wäre dann wahr, auch wenn die Übersetzung nie liefe. Der
    deutsche Fall daneben zeigt, dass derselbe Mechanismus sich füllt.
    """
    englisch = prompts.komponiere(freitext="seen from a narrow street")
    deutsch = prompts.komponiere(freitext="von einer engen Strasse aus gesehen")

    assert "seen from a narrow street" in englisch["prompt"]
    assert englisch["freitext"]["noetig"] is False
    assert not any("übersetzt" in h for h in englisch["hinweise"])

    assert deutsch["freitext"]["noetig"] is True
    assert any("übersetzt" in h for h in deutsch["hinweise"]), (
        "dieselbe Sammlung, derselbe Stil — sie füllt sich, wenn es etwas zu melden gibt"
    )


def test_komponiere_ohne_uebersetzung_schweigt_nicht():
    """`uebersetzen=False` ist erlaubt — aber es kostet etwas, und das steht da."""
    ergebnis = prompts.komponiere(freitext="bedeckter Himmel", uebersetzen=False)
    assert "bedeckter Himmel" in ergebnis["prompt"]
    assert any("NICHT übersetzt" in h for h in ergebnis["hinweise"])


def test_der_bauteilwaechter_sieht_beide_fassungen():
    """Ein deutsches „Dach" wird erst als `roof` sicher gefunden — und umgekehrt.

    Ohne diesen Doppelblick rutschten genau die Wörter durch, die die Übersetzung
    erzeugt hat.
    """
    ergebnis = prompts.komponiere(freitext="mit einem Dach")
    hinweis = " ".join(ergebnis["hinweise"])
    assert "dach" in hinweis and "roof" in hinweis


def test_die_naht_reicht_den_uebersetzer_durch():
    """Nicht nur das Schlüsselwort — der WERT muss ankommen.

    Ein Verdrahtungstest, der nur prüft, dass ein Argument existiert, ist selbst eine
    tote Kante (Sitzung 10).
    """
    ergebnis = prompts.komponiere(
        freitext="bedeckter Himmel",
        uebersetzer=lambda t: {"text": "ERKENNBAR", "verfahren": "attrappe"})
    assert "ERKENNBAR" in ergebnis["prompt"]


def _rendere(tmp_path, prompt, **kw):
    """Ein Lauf mit Modell-Attrappe — es geht hier nur um die Hinweise im Ergebnis."""
    karte = tmp_path / "tiefe_norm.png"
    karte.write_bytes(_PNG)
    ziel = tmp_path / "render.png"

    def modell(parameter):
        Path(parameter["ausgabe_png"]).write_bytes(_PNG)
        return parameter["ausgabe_png"]

    auftrag = render.RenderAuftrag(depth_png=str(karte), prompt=prompt,
                                   ausgabe_png=str(ziel), **kw)
    return render.rendere(auftrag, modell=modell)


def test_render_warnt_bei_deutschem_prompt(tmp_path):
    """Der letzte Posten: ein von Hand gebauter Auftrag kommt an keiner Übersetzung vorbei.

    Übersetzt wird weiter vorne. Wer einen ``RenderAuftrag`` aus einem Skript baut, kommt
    dort aber nie hin — und genau der Fall soll wenigstens im Ergebnis stehen.
    """
    ergebnis = _rendere(tmp_path, "ein Wohnhaus mit Flachdach")
    assert any("nicht englisch" in h for h in ergebnis["hinweise"])


def test_render_warnt_auch_beim_einzelnen_fachwort(tmp_path):
    """`Sichtbeton` trägt kein Signalwort. Die Warnung darf ihn trotzdem nicht übersehen —
    sonst hätte sie eine andere Meinung als die Übersetzung, die ihn erkennt."""
    ergebnis = _rendere(tmp_path, "Sichtbeton")
    assert any("nicht englisch" in h for h in ergebnis["hinweise"])


def test_render_schweigt_bei_englischem_prompt(tmp_path):
    ergebnis = _rendere(tmp_path, "a residential building with a flat roof")
    assert not any("nicht englisch" in h for h in ergebnis["hinweise"])


def test_render_schweigt_beim_unentscheidbaren(tmp_path):
    """Gegenprobe zur Warnung: Eine Objektivangabe ist kein Anlass."""
    ergebnis = _rendere(tmp_path, "24mm f8")
    assert not any("nicht englisch" in h for h in ergebnis["hinweise"])


def test_auch_der_negativ_prompt_wird_geprueft(tmp_path):
    ergebnis = _rendere(tmp_path, "a quiet photograph of the house",
                        negativ_prompt="keine Menschen, kein Nebel")
    assert any("Negativ-Prompt" in h and "englisch" in h
               for h in ergebnis["hinweise"])


# ======================================================================================
# Die beiden Regeln einzeln — und ihre Grenzen
# ======================================================================================

@pytest.mark.parametrize("gebeugt, stamm", [
    ("langen", "lang"), ("feiner", "fein"), ("ruhiges", "ruhig"),
    ("weichem", "weich"), ("bewölkter", "bewölkt"), ("verwitterte", "verwittert"),
    ("nasse", "nass"), ("graue", "grau"), ("grüne", "grün"),
    ("hohe", "hoh"), ("hohen", "hoh"), ("dunkle", "dunkl"),
])
def test_die_endungsregel_findet_den_stamm(gebeugt, stamm):
    assert sprache.grundform(gebeugt) == stamm


def test_umlaute_werden_erst_nachrangig_aufgeloest():
    """``Bäumen`` → ``bäum`` (kein Eintrag) → ``baum`` (Eintrag).

    Die Reihenfolge ist wichtig: Weil zuerst der Stamm wie er ist geprüft wird und die
    Regel überhaupt nur bei Unbekanntem greift, wird aus ``grün`` nie ``grun``.
    """
    assert sprache.grundform("Bäumen") == "baum"
    assert sprache.grundform("Häuser") == "haus"
    assert sprache.grundform("grün") == "grün"


def test_die_endungsregel_kann_nichts_erfinden():
    """Abgestreift wird nur, was danach im Glossar steht — sonst nichts.

    Das ist der ganze Sicherheitsgurt: Die Regel kann finden, nicht erfinden.
    """
    for wort in ("Fensterbank", "Türgriff", "knallig", "Sperrholzplatte"):
        assert sprache.grundform(wort) is None, wort


def test_die_zerlegung_verlangt_BEIDE_teile_im_glossar():
    assert sprache.zerlege_kompositum("Holzfassade") == ("holz", "fassade")
    assert sprache.zerlege_kompositum("Regenbogen") is None, (
        "'bogen' steht nicht im Glossar — also wird nicht zerlegt"
    )


def test_der_zweite_teil_darf_gebeugt_sein():
    assert sprache.zerlege_kompositum("Nordfassaden") == ("nord", "fassade")


def test_ein_bestehender_eintrag_schlaegt_die_zerlegung():
    """Ein Eintrag ist genauer als eine Regel, und darum kommt er zuerst.

    ``Modellfoto`` ist der Fall, an dem es auseinandergeht: Der Eintrag sagt „photograph
    of an architectural model", die Zerlegung ergäbe ``modell`` + ``foto`` = „model
    photograph". Beides ist verständlich, aber nur eines ist die getroffene Entscheidung.
    """
    assert sprache.zerlege_kompositum("Modellfoto") is None
    ergebnis = sprache.uebersetze("Modellfoto")
    assert ergebnis["uebersetzt"] == "photograph of an architectural model"
    assert ergebnis["regeln"] == ()


def test_die_himmelsrichtungen_sind_der_grund_fuer_die_mindestlaenge_drei():
    """``süd``, ``ost``, ``west`` haben drei Zeichen. Mit vier bliebe ``Südseite`` stehen."""
    assert sprache.MIN_TEILLAENGE == 3
    for wort, teile in (("Südseite", ("süd", "seite")), ("Ostfassade", ("ost", "fassade")),
                        ("Westfassade", ("west", "fassade"))):
        assert sprache.zerlege_kompositum(wort) == teile, wort


def test_was_eine_regel_tat_ist_von_einem_eintrag_unterscheidbar():
    """Eine Regel irrt anders als ein Nachschlagewerk. Wer das Ergebnis prüft, soll die
    beiden Sorten trennen können, ohne den Code zu lesen."""
    ergebnis = sprache.uebersetze("Sichtbeton, Nordfassade, langen Schatten")
    arten = {r["art"] for r in ergebnis["regeln"]}
    assert arten == {sprache.ART_KOMPOSITUM, sprache.ART_BEUGUNG}
    assert "sichtbeton" in ergebnis["ersetzt"], "der Eintrag steht getrennt davon"
    assert "sichtbeton" not in {r["wort"] for r in ergebnis["regeln"]}


def test_die_regeln_fassen_nichts_englisches_an():
    """Der Wächter, der im gemischten Prompt wirklich greift.

    Über alle englischen Wörter geprüft, die in unseren Übersetzungen vorkommen, gibt es
    **genau einen** zerstörerischen Fall: ``under`` verliert seine Endung ``er`` und
    landet auf dem deutschen Schlüssel ``und`` — aus „under the sky" würde „and the sky".
    Weil ``under`` im englischen Wortschatz steht, fasst die Regel es nicht an.

    Und gemischte Prompts sind kein Sonderfall: :func:`sieht_englisch_aus` zählt sie
    ausdrücklich als nicht englisch und schickt sie durch die Übersetzung.
    """
    assert sprache.uebersetze("eine Fassade under dem Himmel")["uebersetzt"] == \
        "a facade under the sky"

    ergebnis = sprache.uebersetze("Sichtbeton und Holzfassade")
    assert ergebnis["uebersetzt"] == "exposed concrete and wood facade"


def test_ein_zwei_zeichen_langer_schluessel_verschluckt_kein_wort():
    """Die Mindestlänge des Stamms, und wogegen sie wirklich schützt.

    Das Glossar führt drei Schlüssel mit zwei Zeichen: ``im``, ``in``, ``am``. Ohne die
    Mindestlänge zerfiele jedes Wort der Form ``am`` + Endung — ``Amen`` würde zu ``at
    the``. Kein Wort der Architektursprache gerät dorthin; der Wächter schützt nicht vor
    einer Eingabe, sondern vor den kurzen Schlüsseln des eigenen Glossars, und die gibt
    es wirklich.
    """
    assert sprache.grundform("Amen") is None
    assert sprache.grundform("Ines") is None


# ======================================================================================
# Zusammengesetzte Woerter — die Luecke, die ein echter Lauf gefunden hat
# ======================================================================================
#
# HomeStation, auf-vis-20260826-16 (26.08.2026): Die Uebersetzung liess 3 von 7 Begriffen
# deutsch — «aussenperspektive», «nachmittagslicht», «fotografisch» — und rechnete
# trotzdem weiter.
#
# Das Glossar hatte in allen drei Faellen die BAUSTEINE und nicht das WORT: "aussen" und
# "perspektive", "nachmittag" und "licht", "foto" und "realistisch". Eine zusammengesetzte
# Form faellt zwischen sie — und im Deutschen ist die zusammengesetzte Form der Normalfall.
#
# Warum das mehr ist als Kosmetik: Am Geraet ist gemessen, dass Deutsch das Bild
# veraendert (8 von 8 gepaarten Startwerten, deutlich blauerer Himmel). Ein halb deutscher
# Prompt kommt also bis ins Bild.

DER_PROMPT_AUS_DEM_LAUF = (
    "Aussenperspektive eines Wohnhauses, Nachmittagslicht, fotografisch, "
    "bedeckter Himmel")


def test_der_prompt_aus_dem_lauf_kommt_jetzt_ganz_durch():
    """Die drei Begriffe wörtlich aus dem gemeldeten Lauf."""
    ergebnis = sprache.uebersetze(DER_PROMPT_AUS_DEM_LAUF)

    assert ergebnis["unbekannt"] == ()
    assert ergebnis["vollstaendig"] is True
    for deutsch in ("Aussenperspektive", "Nachmittagslicht", "fotografisch"):
        assert deutsch not in ergebnis["uebersetzt"], deutsch


@pytest.mark.parametrize("deutsch, englisch", [
    ("aussenperspektive", "exterior view"),
    ("außenperspektive", "exterior view"),
    ("innenperspektive", "interior view"),
    ("nachmittagslicht", "afternoon light"),
    ("vormittagslicht", "morning light"),
    ("mittagslicht", "midday light"),
    ("fotografisch", "photographic"),
    ("photographisch", "photographic"),
])
def test_die_zusammengesetzten_formen_stehen_im_glossar(deutsch, englisch):
    assert sprache.GLOSSAR[deutsch] == englisch


def test_die_bausteine_bleiben_ebenfalls_stehen():
    """Die Gegenprobe: Ein zusammengesetztes Wort ergänzt seine Teile, es ersetzt sie
    nicht. Wer «aussen» allein schreibt, meint es auch."""
    for baustein in ("aussen", "nachmittag", "licht", "foto"):
        assert baustein in sprache.GLOSSAR, baustein


def test_ein_wirklich_unbekanntes_wort_wird_weiterhin_gemeldet():
    """**Die wichtigere Gegenprobe.** Ein Glossar, nach dem nie mehr etwas unbekannt ist,
    hätte die Meldung abgeschafft statt die Lücke geschlossen — und der nächste fehlende
    Begriff fiele nirgends mehr auf."""
    ergebnis = sprache.uebersetze("ein Wohnhaus mit Wurstelprader und Zwetschgenkrampus")

    assert ergebnis["unbekannt"], "die Meldung muss weiter greifen"
    assert ergebnis["vollstaendig"] is False


# ── Ersatzschreibung der Umlaute (12.09.2026) ────────────────────────────────────────
#
# Der Anlass ist ein Ausfall an der Naht, gemeldet von der HomeStation nach dem ersten
# Lauf von der Szene bis zum fertigen Bild: Im Prompt stand «vier, betonwaende», und
# beides blieb deutsch stehen. Nachgemessen:
#
#     betonwände  -> concrete walls    (das Glossar kann es)
#     betonwaende -> betonwaende       (dasselbe Wort, unberührt)
#
# Das Glossar ist auf echte Umlaute geschlüsselt. Wer ohne deutsche Tastatur tippt,
# erreicht es nicht — und dieses Repo selbst schreibt in jedem zweiten Kommentar
# «waende».

def test_der_gemeldete_fall_wird_jetzt_uebersetzt():
    """Wörtlich der Prompt aus dem Befund — und was am 12.09.2026 davon zu holen war.

    Diese Probe hielt zuerst ``"vier, concrete walls"`` fest, weil die Umlautregel nur
    das zweite Wort erreichte. Seit dem 16.09.2026 stehen die Zahlwörter im Glossar, und
    ``vier`` fällt mit; die Erwartung ist darum auf den ganzen Satz nachgezogen. Sie
    bleibt hier trotzdem stehen: Sie prüft die **Umlautstelle** — ``betonwaende`` ist
    kein Eintrag und wird es nie —, und ein Test, der mit dem Befund gealtert ist, wird
    gelöscht, nicht verstümmelt.
    """
    assert sprache.uebersetze("vier, betonwaende")["uebersetzt"] == "four, concrete walls"


def test_ersatzschreibung_und_umlaut_ergeben_dasselbe():
    mit = sprache.glossar_uebersetzung("betonwände")["text"]
    ohne = sprache.glossar_uebersetzung("betonwaende")["text"]

    assert mit == ohne == "concrete walls"


def test_die_regel_kann_nichts_erfinden():
    """Dieselbe Zusage wie bei `grundform`: gefunden wird nur, was im Glossar steht.

    `blue` würde zu `blü`, `value` zu `valü`, `true` zu `trü` — keines davon ist ein
    Eintrag, also bleibt alles stehen. Ein englischer Prompt darf hier nicht kippen.
    """
    for englisch in ("blue", "value", "true", "queue", "guest"):
        assert sprache.glossar_uebersetzung(englisch)["text"] == englisch


def test_ein_englischer_prompt_gilt_weiterhin_nicht_als_deutsch():
    """Die Gegenprobe zum zweiten Zeugen — ohne sie hätte er alles Deutsche gefunden."""
    for englisch in ("a modern concrete building with glass facade, four storeys",
                     "exterior view, afternoon light, soft shadows",
                     "photorealistic render of a house"):
        assert sprache.ist_deutsch(englisch) is False, englisch
        assert sprache.uebersetze(englisch)["uebersetzt"] == englisch


def test_der_zweite_zeuge_kennt_jetzt_die_regeln():
    """**Der eigentliche Fehler war nicht das Glossar, sondern der Zeuge.**

    `betonwaende` ist kein Eintrag; erst die Regeln machen daraus `concrete walls`.
    `glossar_evidenz` sah nur Einträge, `ist_deutsch` sagte darum nein — und die
    Übersetzung lief gar nicht erst an. *Ein Zeuge, der weniger kennt als der, für den er
    aussagt, spricht regelmässig frei.*
    """
    assert "betonwaende" in sprache.glossar_evidenz("vier, betonwaende")
    assert sprache.ist_deutsch("vier, betonwaende") is True


def test_einzelne_stellen_werden_auch_geprueft():
    """Ein echtes «ue» anderswo im Wort darf die Umlautstelle nicht blockieren."""
    kandidaten = sprache._umlaut_kandidaten("neuewaende")

    assert "neuewände" in kandidaten


# ======================================================================================
# Zahlwörter (Posten «Zahlwörter stehen in keinem Glossar», 12.09.2026)
# ======================================================================================
#
# Der Befund ist die zweite Hälfte desselben gemeldeten Prompts: Im Feld der HomeStation
# stand «vier, betonwaende». Seit dem 12.09.2026 wird das zweite Wort übersetzt; «vier»
# blieb deutsch stehen. Ein deutsches Wort im englischen Prompt kostet messbar
# Bildqualität — am 21.08.2026 über 8 gepaarte Startwerte gemessen, fiel der deutsche
# Prompt 8 von 8 Mal schlechter aus.
#
# Was dabei NICHT ins Glossar durfte, steht unten in zwei Gegenproben. Sie sind der
# eigentliche Inhalt dieses Blocks: Ein Glossar wächst leicht, und jedes Wort, das zu
# viel darin steht, übersetzt englischen Text, den niemand übersetzt haben wollte.


def test_der_gemeldete_fall_wird_jetzt_ganz_uebersetzt():
    """Wörtlich der Prompt aus dem Befund — und diesmal ohne deutschen Rest.

    Nicht nur der Text zählt: ``vollstaendig`` muss ``True`` sein und ``unbekannt`` leer.
    Ein Prompt, der richtig übersetzt ist und sich selbst als lückenhaft meldet, wäre
    derselbe Fehler nochmal, nur andersherum.
    """
    ergebnis = sprache.uebersetze("vier, betonwaende")

    assert ergebnis["uebersetzt"] == "four, concrete walls"
    assert ergebnis["unbekannt"] == ()
    assert ergebnis["vollstaendig"] is True


@pytest.mark.parametrize("deutsch, englisch", [
    ("eins", "one"),
    ("zwei", "two"),
    ("drei", "three"),
    ("vier", "four"),
    ("fünf", "five"),
    ("sechs", "six"),
    ("sieben", "seven"),
    ("neun", "nine"),
    ("zehn", "ten"),
    ("zwölf", "twelve"),
])
def test_jedes_aufgenommene_zahlwort_kommt_englisch_heraus(deutsch, englisch):
    assert sprache.glossar_uebersetzung(deutsch)["text"] == englisch


def test_neun_wurde_vorher_zu_new():
    """Der stillste der Funde, und der Grund, warum ein Eintrag mehr ist als ein Komfort.

    Ohne Eintrag griff bei ``neun`` die Beugungsregel: Endung ``n`` abgestreift ergibt
    ``neu``, und ``neu`` steht im Glossar als ``new``. «neun Fenster» wurde damit zu
    «new window» — nicht unübersetzt, sondern **falsch**, und ohne jede Meldung. Der
    direkte Eintrag schlägt die Regel, weil das Nachschlagewerk zuerst läuft.
    """
    # Das ``windows`` kam am Nachmittag des 16.09.2026 dazu (Mehrzahlregel). Geprüft
    # wird hier weiterhin das ``nine``: dass der Eintrag die Beugungsregel schlägt.
    assert sprache.glossar_uebersetzung("neun fenster")["text"] == "nine windows"
    assert sprache.GLOSSAR["neu"] == "new", "Die Falle steht noch; der Eintrag hält sie zu."


@pytest.mark.parametrize("ersatz, umlaut, englisch", [
    ("fuenf", "fünf", "five"),
    ("zwoelf", "zwölf", "twelve"),
])
def test_ersatzschreibung_und_umlaut_ergeben_dasselbe_zahlwort(ersatz, umlaut, englisch):
    """Wer ohne deutsche Tastatur tippt, erreicht dasselbe Wort.

    Und zwar **ohne zweiten Glossareintrag**: ``_umlaut_kandidaten`` leistet das schon,
    ``grundform`` schlägt die Umlautform nach. Nachgemessen am 16.09.2026 — darum steht
    ``fuenf`` bewusst NICHT im Glossar. Diese Probe hält genau das fest: Verschwände die
    Umlautauflösung, fiele sie, und nicht erst ein Bild.
    """
    assert sprache.glossar_uebersetzung(ersatz)["text"] == englisch
    assert sprache.glossar_uebersetzung(umlaut)["text"] == englisch
    assert ersatz not in sprache.GLOSSAR


def test_ersatzschreibung_im_satz_mit_zahlwort():
    """Beides zusammen, wie es aus der Oberfläche käme."""
    assert sprache.uebersetze("fuenf betonwaende")["uebersetzt"] == "five concrete walls"


# --- GEGENPROBEN ----------------------------------------------------------------------

@pytest.mark.parametrize("englisch", [
    "a modern concrete building with four storeys, six windows",
    "seven trees in front of the house, ten metres tall",
    "nine people seen at eye level, twelve columns behind them",
])
def test_englische_zahlwoerter_bleiben_unberuehrt(englisch):
    """Die Gegenprobe, die auslösen dürfte und nicht darf.

    Drei englische Prompts, jeder voller Zahlwörter. Sie müssen **Wort für Wort**
    stehenbleiben und dürfen auch nicht als deutsch gelten — sonst warnte die QA bei
    jedem englischen Prompt, und eine Warnung, die immer kommt, wird weggeklickt.
    """
    assert sprache.ist_deutsch(englisch) is False, englisch
    assert sprache.uebersetze(englisch)["uebersetzt"] == englisch
    assert sprache.sprachwarnung(englisch) == ""


@pytest.mark.parametrize("wort, grund", [
    ("elf", "Im Englischen ein Fabelwesen — der einzige echte falsche Freund der zwölf. "
            "Gemessen am 16.09.2026: Mit Eintrag wurde «elf statue» zu «eleven statue» "
            "und galt zugleich als deutsch."),
    ("acht", "Im Englischen sauber, aber die eigene Beugungsregel streift «achte» und "
             "«achten» auf «acht» ab. Der Eintrag übersetzte damit durch die Hintertür "
             "die Ordnungszahl (eighth, nicht eight) und den Stamm des Verbs «achten». "
             "Es ist das einzige Zahlwort, dem das passiert."),
])
def test_weggelassene_zahlwoerter_bleiben_stehen(wort, grund):
    """Was nicht aufgenommen wurde, bleibt deutsch — und wird **gemeldet**.

    Das ist die dritte Antwort, angewandt aufs Glossar: nicht übersetzt ist weder
    richtig noch falsch, sondern unbearbeitet. Ein stehengebliebenes Wort kostet einen
    Blick, ein falsch übersetztes ein Bild.
    """
    assert wort not in sprache.GLOSSAR, grund
    assert sprache.glossar_uebersetzung(wort)["text"] == wort
    assert wort in sprache.glossar_uebersetzung(wort)["unbekannt"], (
        f"«{wort}» wird nicht übersetzt und muss deshalb als unbekannt gemeldet werden. "
        f"Grund für die Auslassung: {grund}")


@pytest.mark.parametrize("ordnungszahl", [
    "erste", "zweite", "dritte", "vierte", "fünfte", "sechste", "siebte", "achte",
    "neunte", "zehnte", "elfte", "zwölfte",
])
def test_ordnungszahlen_bleiben_draussen(ordnungszahl):
    """Bewusste Grenze (16.09.2026): Ordnungszahlen sind gebeugt, Grundzahlen nicht.

    «zweites Geschoss» und «the second floor» stellen anders; für eine Aufzählung durch
    Kommata trägt eine Grundzahl, eine gebeugte Ordnungszahl trüge nicht. Sie bleiben
    also stehen und werden gemeldet — und diese Probe hält fest, dass kein neu
    aufgenommenes Grundzahlwort seine Ordnungszahl durch die Beugungsregel nachzieht.
    """
    assert sprache.glossar_uebersetzung(ordnungszahl)["text"] == ordnungszahl


def test_achten_wird_nicht_zu_eight():
    """Der Einzelfall, an dem «acht» gescheitert ist — namentlich festgehalten.

    «achten» ist im Deutschen ein Verb («auf etwas achten») und zugleich eine gebeugte
    Ordnungszahl. Beides ist nicht die Zahl acht. Nähme jemand «acht» ins Glossar auf,
    fiele diese Probe — und genau dafür steht sie hier.
    """
    assert sprache.glossar_uebersetzung("achten")["text"] == "achten"
    assert sprache.grundform("achte") is None


# --- MUTATIONSPROBE -------------------------------------------------------------------

def test_mutationsprobe_ohne_den_eintrag_faellt_der_gemeldete_fall_wieder():
    """Wächter entschärfen, Probe muss fallen.

    Ohne diese Probe könnte der Eintrag ``vier`` aus dem Glossar verschwinden, und die
    Tests darüber sagten nur, dass irgendetwas übersetzt wurde. Hier wird er
    herausgenommen — und der gemeldete Prompt muss wieder genau den Zustand zeigen, der
    am 12.09.2026 gemeldet wurde: «vier» deutsch stehengeblieben und als unbekannt
    gemeldet.
    """
    gesichert = dict(sprache.GLOSSAR)
    muster = sprache._GLOSSAR_MUSTER
    wortschatz = sprache._ENGLISCHER_WORTSCHATZ
    try:
        del sprache.GLOSSAR["vier"]
        sprache._GLOSSAR_MUSTER = sprache._glossar_muster()
        sprache._ENGLISCHER_WORTSCHATZ = sprache._englischer_wortschatz()

        entschaerft = sprache.uebersetze("vier, betonwaende")
        assert entschaerft["uebersetzt"] == "vier, concrete walls"
        assert "vier" in entschaerft["unbekannt"]
        assert entschaerft["vollstaendig"] is False
    finally:
        sprache.GLOSSAR.clear()
        sprache.GLOSSAR.update(gesichert)
        sprache._GLOSSAR_MUSTER = muster
        sprache._ENGLISCHER_WORTSCHATZ = wortschatz

    # Und danach steht wieder alles, wie es stehen soll — sonst vergiftete diese Probe
    # jede Probe, die nach ihr läuft.
    assert sprache.uebersetze("vier, betonwaende")["uebersetzt"] == "four, concrete walls"


# ======================================================================================
# Die Sperre der Kompositumsregel gegen Zahlwörter (Nachmessung 16.09.2026)
# ======================================================================================
#
# Der Fund entstand bei der Prüfung der Zahlwort-Aufnahme, nicht beim Bau: Über den
# Wortschatz dieses Repos gemessen (69'273 verschiedene Wörter) zerlegte
# `zerlege_kompositum` mit den neuen Einträgen **sechs** Wörter falsch — `dreizehn` zu
# «three ten», `dreiecke` zu «three corner», `obendrein` zu «above three». Alle sechs
# **still**: `unbekannt` war leer, `vollstaendig` war `True`.
#
# Das ist der teuerste Fehler dieses Moduls, nicht der billigste: Ein stehengebliebenes
# Wort kostet einen Blick, eine erfundene Zahl im Prompt kostet ein Bild — und niemand
# sieht ihr an, dass sie erfunden ist.


@pytest.mark.parametrize("wort, falsch_gewesen", [
    ("dreizehn", "three ten"),
    ("vierzehn", "four ten"),
    ("fünfzehn", "five ten"),
    ("neunzehn", "nine ten"),
    ("dreiecke", "three corner"),
    ("obendrein", "above three"),
])
def test_zusammengesetzte_zahlwoerter_werden_nicht_zerlegt(wort, falsch_gewesen):
    """Deutsch zählt zusammengesetzt, wo Englisch ein eigenes Wort hat.

    ``dreizehn`` ist *thirteen*, nicht *three ten*; ``Dreieck`` ist *triangle*, nicht
    *three corner*. Die Kompositumsregel kann das nicht wissen — sie prüft nur, ob beide
    Teile im Glossar stehen, und bei einer Zahl stehen sie immer.

    Geprüft wird beides: dass das Wort stehenbleibt **und** dass es als ``unbekannt``
    gemeldet wird. Nur stehenbleiben genügte nicht — dann wäre der Prompt still halb
    deutsch, und das ist der Zustand, gegen den dieses Modul gebaut ist.
    """
    ergebnis = sprache.glossar_uebersetzung(wort)

    assert ergebnis["text"] == wort, (
        f"Zerlegt zu «{ergebnis['text']}» — {falsch_gewesen!r} war der Stand vor der "
        f"Sperre, und er war still.")
    assert wort in ergebnis["unbekannt"]
    assert ergebnis["regeln"] == ()


def test_ein_ganzer_prompt_mit_zusammengesetzter_zahl_meldet_sich_unvollstaendig():
    """Die dritte Antwort am ganzen Prompt: nicht übersetzt ist nicht «in Ordnung».

    Vor der Sperre kam hier «three ten window» heraus, mit ``vollstaendig is True``. Eine
    erfundene Zahl, die sich selbst für vollständig erklärt.
    """
    ergebnis = sprache.uebersetze("dreizehn fenster")

    assert ergebnis["uebersetzt"] == "dreizehn window"
    assert "dreizehn" in ergebnis["unbekannt"]
    assert ergebnis["vollstaendig"] is False


# --- GEGENPROBE -----------------------------------------------------------------------

@pytest.mark.parametrize("wort, englisch", [
    ("nordfassade", "north facade"),
    ("nordfassaden", "north facade"),
    ("holzfassade", "wood facade"),
    ("südseite", "south side"),
    ("betonwaende", "concrete walls"),
])
def test_echte_komposita_werden_weiterhin_zerlegt(wort, englisch):
    """Die Sperre darf genau die Zahlwörter treffen und sonst nichts.

    Über denselben Wortschatz gemessen (16.09.2026) blockiert sie **sieben** Wortformen,
    und alle sieben waren falsch zerlegt. Eine Sperre, die nebenbei ``Nordfassade``
    mitnähme, wäre teurer als der Fehler, den sie behebt.
    """
    assert sprache.glossar_uebersetzung(wort)["text"] == englisch


def test_das_zahlwort_allein_bleibt_uebersetzt():
    """Die Sperre gilt der **Regel**, nicht dem Eintrag.

    ``vier`` steht im Glossar und wird nachgeschlagen; gesperrt ist nur, ``vier`` als
    Baustein eines zusammengesetzten Wortes zu verwenden. Ohne diese Unterscheidung hätte
    die Sperre den gemeldeten Fall vom 12.09.2026 wieder aufgemacht.
    """
    assert sprache.uebersetze("vier, betonwaende")["uebersetzt"] == "four, concrete walls"
    assert sprache.glossar_uebersetzung("neun fenster")["text"] == "nine windows"


# --- MUTATIONSPROBE -------------------------------------------------------------------

def test_mutationsprobe_ohne_die_sperre_erfindet_die_regel_wieder_zahlen():
    """Wächter entschärfen, Probe muss fallen.

    ``ZAHLWOERTER`` wird geleert — damit greift wieder die blosse Bedingung «beide Teile
    stehen im Glossar», und genau die sechs Wörter kippen zurück in den Zustand vom
    Vormittag des 16.09.2026.
    """
    gesichert = sprache.ZAHLWOERTER
    try:
        sprache.ZAHLWOERTER = frozenset()

        assert sprache.glossar_uebersetzung("dreizehn")["text"] == "three ten"
        # ``corners`` und ``windows``: Die Mehrzahlregel vom Nachmittag des 16.09.2026
        # läuft auch über den entschärften Stand. Der Fund bleibt derselbe — aus einer
        # Dreizehn werden eine Drei und eine Zehn.
        assert sprache.glossar_uebersetzung("dreiecke")["text"] == "three corners"
        entschaerft = sprache.uebersetze("dreizehn fenster")
        assert entschaerft["uebersetzt"] == "three ten windows"
        # Und das ist der eigentliche Schaden: Der Prompt hält sich für fertig.
        assert entschaerft["vollstaendig"] is True
    finally:
        sprache.ZAHLWOERTER = gesichert

    assert sprache.glossar_uebersetzung("dreizehn")["text"] == "dreizehn"


# ======================================================================================
# Die Mehrzahl: eine Zahl vor einem Hauptwort
# ======================================================================================
#
# **Der gemeldete Fall** (16.09.2026): «zwoelf fenster» ergab ``twelve window``. Die Zahl
# stimmte, das Hauptwort stand in der Einzahl — ein englischer Prompt mit einem
# Grammatikfehler, aus einem Modul, das es genau dagegen gibt.
#
# Die Proben unten stehen auf zwei Fragen, und die zweite ist die wichtigere:
# **beugt die Regel, wo sie soll** — und **lässt sie in Ruhe, wo sie es nicht weiss.**

def test_der_gemeldete_fall_zieht_jetzt_die_mehrzahl():
    """Der Befund vom 16.09.2026, wörtlich.

    ``fenster`` → ``window`` stand schon vorher im Glossar; die Zahlwörter desselben
    Vormittags haben den Fall nur sichtbar gemacht. Was fehlte, war die Übereinstimmung
    zwischen zwei Wörtern — und die konnte ein Nachschlagewerk nie leisten, das je ein
    Wort sieht.
    """
    assert sprache.glossar_uebersetzung("zwoelf fenster")["text"] == "twelve windows"
    assert sprache.uebersetze("zwölf Fenster")["uebersetzt"] == "twelve windows"


def test_der_gebeugte_prompt_meldet_sich_weiterhin_vollstaendig():
    """Die stillste Stelle des Einbaus, und sie wäre fast danebengegangen.

    ``unbekannt`` prüft gegen den englischen Wortschatz dieses Moduls, und der kennt nur
    die Formen, die im Glossar stehen — ``windows`` steht dort nicht. Erst gemessen,
    meldete der Prompt darum ausgerechnet das Wort als «nicht übersetzt», das die neue
    Regel gerade richtig gestellt hatte. Gemessen wird ``unbekannt`` deshalb VOR der
    Beugung; die Regel fasst ohnehin nur an, was schon englisch ist.
    """
    ergebnis = sprache.uebersetze("zwölf Fenster")

    assert ergebnis["unbekannt"] == ()
    assert ergebnis["vollstaendig"] is True


@pytest.mark.parametrize("deutsch, englisch", [
    ("zwei fenster", "two windows"),
    ("drei baum", "three trees"),
    ("vier fassade", "four facades"),
    ("fünf treppe", "five stairs"),
    ("sechs kamin", "six chimneys"),
    ("sieben stütze", "seven columns"),
    ("neun gaube", "nine dormers"),
    ("zehn tür", "ten doors"),
    ("zwölf balkon", "twelve balconies"),
])
def test_jedes_zahlwort_ab_zwei_zieht_die_mehrzahl(deutsch, englisch):
    assert sprache.glossar_uebersetzung(deutsch)["text"] == englisch


@pytest.mark.parametrize("deutsch, englisch", [
    ("12 fenster", "12 windows"),
    ("2 bäume", "2 trees"),
    ("144 fenster", "144 windows"),
])
def test_eine_ziffer_loest_die_mehrzahl_ebenso_aus(deutsch, englisch):
    """Ziffern werden **gerechnet**, nicht nachgeschlagen.

    Das Glossar reicht bis ``zwölf``, aus guten Gründen (Zahlwörter oben). Eine Liste
    englischer Zahlwörter bis zwölf wäre hier aber genau die Sorte Grenze, die beim
    dreizehnten Fenster still kippt: ``144 fenster`` ist derselbe Satz wie
    ``zwölf fenster``, nur grösser.
    """
    assert sprache.glossar_uebersetzung(deutsch)["text"] == englisch


@pytest.mark.parametrize("deutsch, englisch", [
    ("ein fenster", "a window"),
    ("eine fassade", "a facade"),
    ("eins fenster", "one window"),
    ("1 fenster", "1 window"),
    ("0 fenster", "0 window"),
])
def test_eins_loest_keine_mehrzahl_aus(deutsch, englisch):
    """Eins ist keine Mehrzahl — und ``ein`` ist nicht einmal eine Zahl.

    «ein Wohnhaus» ist *a residential building*, nicht *one residential building*; der
    Artikel steht im Glossar als ``a`` und bleibt es. Die Null steht mit in dieser Probe,
    weil sie der Fall ist, den man beim Schreiben einer Regel «grösser als eins» am
    ehesten übersieht: ``zero windows`` wäre zwar richtiges Englisch, aber ``0`` kommt aus
    einer Ziffernrechnung und nicht aus dem Glossar — die Verneinung hat hier ihren
    eigenen Weg (``kein`` → ``no``), und zwei Wege zu einer Aussage sind einer zu viel.
    """
    assert sprache.glossar_uebersetzung(deutsch)["text"] == englisch


# --- DIE GRENZEN: WO DIE REGEL BEWUSST NICHTS TUT -------------------------------------

@pytest.mark.parametrize("deutsch, englisch", [
    ("vier geschosse", "four storeys"),
    ("zwei balkone", "two balconies"),
    ("sechs stützen", "six columns"),
    ("drei räume", "three rooms"),
    ("zwei dächer", "two roofs"),
    ("vier betonwaende", "four concrete walls"),
    ("zwei hohe wolken", "two high thin clouds"),
    ("drei lange schatten", "three long shadows"),
])
def test_ein_schon_mehrzahliger_eintrag_bleibt_unveraendert(deutsch, englisch):
    """Keine doppelte Bildung.

    Das Glossar führt zu vielen Hauptwörtern **beide** Formen (``wand`` → ``wall``,
    ``wände`` → ``walls``), und mehrere mehrwortige Einträge enden auf einer Mehrzahl.
    Eine Regel, die stur ein ``s`` anhängt, macht daraus ``wallses`` — und das liest sich
    nicht wie ein Tippfehler, sondern wie eine Sprache.
    """
    assert sprache.glossar_uebersetzung(deutsch)["text"] == englisch


@pytest.mark.parametrize("deutsch, englisch", [
    ("zwei beton", "two concrete"),
    ("drei glas", "three glass"),
    ("zwei licht", "two light"),
    ("vier holz", "four wood"),
    ("zwei schnee", "two snow"),
    ("drei sichtbeton", "three exposed concrete"),
])
def test_nicht_zaehlbares_bleibt_unveraendert(deutsch, englisch):
    """``two concretes`` wäre schlimmer als der Fehler, den diese Regel behebt.

    Ein stehengebliebenes ``two concrete`` ist ein sichtbarer Schönheitsfehler: Wer den
    Prompt liest, sieht sofort, dass da etwas nicht stimmt. Ein ``two concretes`` sieht
    dagegen aus wie richtiges Englisch und wird nie wieder als Fehler erkannt.
    """
    assert sprache.glossar_uebersetzung(deutsch)["text"] == englisch


@pytest.mark.parametrize("deutsch, englisch", [
    ("drei wohnhaus", "three residential buildings"),
    ("zwei neubau", "two new buildings"),
    ("vier flachdach", "four flat roofs"),
    ("zwei fensterband", "two ribbon windows"),
    ("drei erdgeschoss", "three ground floors"),
    ("zwei modellfoto", "two photographs of an architectural model"),
])
def test_ein_mehrwortiger_eintrag_beugt_nur_das_letzte_wort(deutsch, englisch):
    """Deutsch wie Englisch stellen das Hauptwort ans Ende der Wortgruppe.

    ``residential building`` → ``residential buildings``, nicht ``residentials
    building``. Und ``photograph of an architectural model`` zeigt, warum die Wortgruppe
    am ersten Funktionswort endet: Gebeugt wird ``photograph``, nicht ``model`` —
    obwohl ``model`` das letzte Wort des Eintrags ist.
    """
    assert sprache.glossar_uebersetzung(deutsch)["text"] == englisch


def test_die_einzige_unregelmaessige_form():
    """``person`` → ``people``, und es ist die einzige in diesem Glossar.

    Nachgezählt am 16.09.2026 über alle Glossarwerte. ``roof`` → ``roofs`` sieht nach
    einem zweiten Fall aus und ist keiner — das Glossar führt ``dächer`` → ``roofs`` und
    bestätigt die regelmässige Form.
    """
    assert sprache.mehrzahl("person") == "people"
    assert sprache.glossar_uebersetzung("zwei person")["text"] == "two people"
    assert set(sprache.MEHRZAHL_UNREGELMAESSIG) == {"person"}


@pytest.mark.parametrize("deutsch, englisch", [
    # Das Komma macht aus zwei Gliedern einer Aufzählung keine Wortgruppe.
    ("vier, betonwaende", "four, concrete walls"),
    ("zwei, fenster", "two, window"),
    # Ein Verhältnis- oder Bindewort beendet die Gruppe: Die Zwei zählt nicht den Garten.
    ("zwei mit garten", "two with garden"),
    ("drei ohne fenster", "three without window"),
    ("zwei tagsüber", "two during the day"),
])
def test_die_zahl_muss_unmittelbar_davorstehen(deutsch, englisch):
    """«Unmittelbar» heisst wörtlich: nur ein Abstand, kein Zeichen, kein Zwischenwort.

    Der erste Fall steht seit dem 12.09.2026 als gemeldeter Prompt in diesen Tests. Er
    ist der Grund, dass die Einschränkung überhaupt auffiel — «vier, betonwaende» ist
    eine Aufzählung aus zwei Gliedern, und das Komma sagt es. Was danach käme, wäre
    geraten, nicht gelesen.
    """
    assert sprache.glossar_uebersetzung(deutsch)["text"] == englisch


def test_ein_unbekannter_kopf_wird_nicht_gebeugt_sondern_gemeldet():
    """Die dritte Antwort, auf Grammatik angewandt.

    ``twelve window frames``: ``frames`` kennt das Glossar nicht, aber es ist
    offensichtlich der Kopf der Wortgruppe. Endete die Gruppe vor ihm, entstünde
    ``twelve windows frames`` — falscher als vorher. Sie läuft darum bis zum Kopf, und
    weil der in keinem Verzeichnis steht, geschieht nichts. Der Befund sagt aber, dass
    nichts geschah und **warum**: ``nicht entschieden`` ist nicht ``in Ordnung``.
    """
    text, befunde = sprache._mehrzahl_anwenden("twelve window frames")

    assert text == "twelve window frames"
    assert befunde == ({"zahl": "twelve", "einzahl": "frames", "mehrzahl": None,
                        "grund": sprache.MEHRZAHL_OFFEN},)


def test_die_beiden_none_sind_auseinanderzuhalten():
    """``None`` heisst hier zweierlei, und das Ergebnis sagt welches.

    Bei ``concrete`` ist entschieden, dass nicht gebeugt wird — jemand hat hingesehen.
    Bei ``cantilevered`` hat niemand hingesehen. Beide Male bleibt der Text gleich; nur
    der zweite Fall ist eine offene Stelle, und nur wenn man sie unterscheiden kann,
    findet sie jemand.
    """
    assert sprache.mehrzahl("concrete") is None
    assert sprache.mehrzahl("cantilevered") is None

    assert sprache.mehrzahl_befund("concrete")["grund"] == sprache.MEHRZAHL_UNZAEHLBAR
    assert sprache.mehrzahl_befund("walls")["grund"] == sprache.MEHRZAHL_SCHON
    assert sprache.mehrzahl_befund("cantilevered")["grund"] == sprache.MEHRZAHL_OFFEN
    assert sprache.mehrzahl_befund("window")["grund"] == sprache.MEHRZAHL_GEBEUGT


def test_zwei_zahlen_vor_einem_kopf_beugen_ihn_nur_einmal():
    """Ein gemessener Fehler, gefunden von einer fremden Mutationsprobe.

    ``three ten window`` entsteht, wenn man die Zahlwortsperre der Kompositumsregel
    entschärft und «dreizehn fenster» durchlässt. Beide Zahlen sind Auslöser, beide
    fanden denselben Kopf, und die erste Fassung dieser Regel beugte ihn zweimal:
    ``three ten windowss``. Es gewinnt jetzt die **nähere** Zahl, und sie gewinnt genau
    einmal.
    """
    text, befunde = sprache._mehrzahl_anwenden("three ten window")

    assert text == "three ten windows"
    assert [b["zahl"] for b in befunde] == ["ten"]


# --- ENGLISCHE EINGABEN ---------------------------------------------------------------

@pytest.mark.parametrize("text", [
    "twelve windows and two doors",
    "a photograph of the house with two balconies",
    "seen from the street, four storeys above the trees",
])
def test_englische_eingaben_bleiben_vollstaendig_unberuehrt(text):
    """Was englisch aussieht, wird nicht angefasst — auch nicht von dieser Regel.

    Die Mehrzahl läuft im Glossarübersetzer, und der läuft nur bei erkanntem Deutsch.
    Ein englischer Prompt geht unverändert durch, mitsamt seiner schon richtigen
    Mehrzahl; eine Regel, die ihn «verbessert», könnte ihn nur verschlechtern.
    """
    ergebnis = sprache.uebersetze(text)

    assert ergebnis["noetig"] is False
    assert ergebnis["uebersetzt"] == text
    assert ergebnis["mehrzahl"] == ()


def test_der_befund_nennt_zahl_wort_und_grund():
    """Sichtbarkeit statt Vermeidung — dieselbe Zusage wie bei der Kompositumsregel.

    Wer den Prompt prüft, soll sehen, was die Regel getan hat und was sie liegen liess,
    ohne den Code zu lesen. Darum steht der Befund auch da, wo nichts geändert wurde.
    """
    ergebnis = sprache.uebersetze("zwölf Fenster und zwei Balkone")

    assert ergebnis["uebersetzt"] == "twelve windows and two balconies"
    assert ergebnis["mehrzahl"] == (
        {"zahl": "twelve", "einzahl": "window", "mehrzahl": "windows",
         "grund": sprache.MEHRZAHL_GEBEUGT},
        {"zahl": "two", "einzahl": "balconies", "mehrzahl": None,
         "grund": sprache.MEHRZAHL_SCHON},
    )


# --- DIE VERZEICHNISSE ----------------------------------------------------------------

def test_die_endungsregel_trifft_die_mehrzahlen_des_glossars():
    """Die Gegenprobe steckt im Glossar selbst — sie ist gemessen, nicht geschätzt.

    Zu fünfzehn zählbaren Hauptwörtern führt das Glossar die Mehrzahl **unabhängig** als
    eigenen deutschen Eintrag: ``wände`` → ``walls``, ``dächer`` → ``roofs``, ``balkone``
    → ``balconies``, ``geschosse`` → ``storeys``, ``personen`` → ``people`` und zehn
    weitere. Sie sind Jahre vor dieser Regel entstanden und wissen nichts von ihr. Wenn
    die Regel für alle fünfzehn dieselbe Form liefert, ist das ein Abgleich gegen fremde
    Daten und nicht gegen die eigene Erwartung.

    Die Zahl steht mit in der Probe: Fällt sie unter fünfzehn, hat jemand einen Eintrag
    entfernt — und dann ist dieser Abgleich schwächer, ohne dass es auffiele.
    """
    letzte_woerter = {
        sprache._WORT.findall(englisch)[-1]
        for englisch in sprache.GLOSSAR.values() if sprache._WORT.findall(englisch)
    }
    treffer = {
        wort: sprache.mehrzahl(wort) for wort in sprache.ZAEHLBAR
        if sprache.mehrzahl(wort) in letzte_woerter
    }

    assert len(treffer) == 15, treffer
    assert treffer["wall"] == "walls"
    assert treffer["roof"] == "roofs"
    assert treffer["balcony"] == "balconies"
    assert treffer["storey"] == "storeys"
    assert treffer["person"] == "people"


@pytest.mark.parametrize("wort, mehrzahl", [
    ("lens", "lenses"),      # auf -s
    ("bush", "bushes"),      # auf -sh
    ("sketch", "sketches"),  # auf -ch
    ("city", "cities"),      # Mitlaut + y
    ("balcony", "balconies"),
    ("storey", "storeys"),   # Selbstlaut + y — NICHT storeies
    ("chimney", "chimneys"),
    ("terrace", "terraces"), # auf -ce, nicht auf -c+e-Sonderweg
    ("roof", "roofs"),       # NICHT rooves
])
def test_die_endungsregel_kennt_ihre_faelle(wort, mehrzahl):
    assert sprache.mehrzahl(wort) == mehrzahl


def test_die_verzeichnisse_ueberschneiden_sich_nicht():
    """Der Stolperdraht für den nächsten, der ein Wort aufnimmt.

    ``ZAEHLBAR`` sagt «beugen», ``OHNE_MEHRZAHL`` und ``SCHON_MEHRZAHL`` sagen «nicht
    beugen». Ein Wort in zwei Listen wäre eine Frage mit zwei Antworten, und welche
    gewinnt, entschiede die Reihenfolge der ``if`` in :func:`mehrzahl_befund` — also der
    Zufall.
    """
    assert not sprache.ZAEHLBAR & sprache.OHNE_MEHRZAHL
    assert not sprache.ZAEHLBAR & sprache.SCHON_MEHRZAHL
    assert not sprache.OHNE_MEHRZAHL & sprache.SCHON_MEHRZAHL
    assert not set(sprache.MEHRZAHL_UNREGELMAESSIG) & sprache.OHNE_MEHRZAHL
    assert not set(sprache.MEHRZAHL_UNREGELMAESSIG) & sprache.SCHON_MEHRZAHL


@pytest.mark.parametrize("name", ["ZAEHLBAR", "OHNE_MEHRZAHL", "SCHON_MEHRZAHL"])
def test_kein_verzeichnis_fuehrt_ein_wort_das_im_glossar_nicht_vorkommt(name):
    """Jedes Wort in den drei Listen muss im Glossar auch wirklich auftauchen.

    Sonst sammelt sich hier über die Jahre Wortschatz an, den niemand mehr prüft — und
    eine Liste, die mehr behauptet, als das Glossar hergibt, sieht gepflegt aus und ist
    es nicht. Geprüft wird gegen das **letzte** Wort jedes Glossarwerts, denn nur dieses
    kann je ein Kopf sein.
    """
    letzte_woerter = {
        sprache._WORT.findall(englisch)[-1]
        for englisch in sprache.GLOSSAR.values() if sprache._WORT.findall(englisch)
    }

    assert not getattr(sprache, name) - letzte_woerter


# --- MUTATIONSPROBEN ------------------------------------------------------------------
#
# Fünf Wächter, fünf Proben. Jede entschärft genau einen und muss dabei rot werden — ein
# Wächter, der nicht fällt, bewacht nichts. Alle fünf sind am 16.09.2026 wirklich
# gefahren worden, und alle fünf sind rot geworden; was dabei herauskam, steht jeweils
# als erwarteter Text in der Probe.

def test_mutationsprobe_ohne_die_endungsregel_entstehen_falsche_formen(monkeypatch):
    """Wächter: die Endungsregel. Entschärft zu «immer +s».

    Das ist die Regel, die jeder zuerst schreibt, und sie trifft drei der neun Formen
    dieses Glossars nicht.
    """
    monkeypatch.setattr(sprache, "_endungsregel", lambda wort: wort + "s")

    assert sprache.glossar_uebersetzung("drei skizze")["text"] == "three sketchs"
    assert sprache.glossar_uebersetzung("zwei balkon")["text"] == "two balconys"
    assert sprache.glossar_uebersetzung("zwei objektiv")["text"] == "two lenss"


def test_mutationsprobe_ohne_die_unzaehlbaren_entsteht_two_concretes(monkeypatch):
    """Wächter: :data:`OHNE_MEHRZAHL`, hinter der Sperre von :data:`ZAEHLBAR`.

    Entschärft werden **beide** — erst die Sperre (``concrete`` wird für zählbar erklärt),
    dann die Ausnahme. Genau so entsteht der Fehler in echt: Jemand nimmt ein Wort in die
    zählbaren auf und sieht die Ausnahmeliste nicht.
    """
    monkeypatch.setattr(sprache, "ZAEHLBAR", sprache.ZAEHLBAR | {"concrete"})
    monkeypatch.setattr(sprache, "OHNE_MEHRZAHL", frozenset())

    assert sprache.glossar_uebersetzung("zwei beton")["text"] == "two concretes"


def test_mutationsprobe_ohne_die_mehrzahlformen_entsteht_wallses(monkeypatch):
    """Wächter: :data:`SCHON_MEHRZAHL`. Die doppelte Bildung.

    ``walls`` endet auf ``s``, die Endungsregel hängt darum ``es`` an — ``wallses``. Das
    ist die Sorte Wort, die niemand als Tippfehler erkennt.
    """
    monkeypatch.setattr(sprache, "ZAEHLBAR", sprache.ZAEHLBAR | {"walls"})
    monkeypatch.setattr(sprache, "SCHON_MEHRZAHL", frozenset())

    assert sprache.glossar_uebersetzung("vier betonwaende")["text"] == "four concrete wallses"


def test_mutationsprobe_mit_eins_als_ausloeser_entsteht_one_windows(monkeypatch):
    """Wächter: :data:`MEHRZAHL_AUSLOESER`. Die Grenze bei zwei.

    Sie ist der Grund, warum «ein Fenster» ein Fenster bleibt. Ohne sie steht im Prompt
    ``a windows``, und das ist kein halbrichtiges Englisch mehr, sondern falsches.
    """
    monkeypatch.setattr(sprache, "MEHRZAHL_AUSLOESER",
                        sprache.MEHRZAHL_AUSLOESER | {"one", "a"})

    assert sprache.glossar_uebersetzung("eins fenster")["text"] == "one windows"
    assert sprache.glossar_uebersetzung("ein fenster")["text"] == "a windows"


def test_mutationsprobe_ohne_die_trennwoerter_zaehlt_die_zahl_ueber_das_komma_hinaus(
        monkeypatch):
    """Wächter: :data:`_MEHRZAHL_TRENNER`. Wo die Wortgruppe endet.

    ``two with garden`` — die Zwei zählt nicht den Garten, sie steht vor dem ``mit``.
    Ohne die Trennwörter greift die Regel über das Verhältniswort hinweg und behauptet
    etwas, das im Prompt nicht steht.
    """
    monkeypatch.setattr(sprache, "_MEHRZAHL_TRENNER", frozenset())

    assert sprache.glossar_uebersetzung("zwei mit garten")["text"] == "two with gardens"
    assert sprache.glossar_uebersetzung("drei ohne fenster")["text"] == "three without windows"


# ======================================================================================
# Die Mehrzahl — was die Prüfung vom 16.09.2026 nachgetragen hat
# ======================================================================================
#
# Drei Befunde aus dem Nachfahren der Mehrzahlregel:
#
# 1. **Ein Fehler.** ``f2.8 objektiv`` ergab ``f2.8 lenses``. Die Blendenzahl zerfiel im
#    Muster in ``2`` und ``8``, und die ``8`` stand unmittelbar vor ``lens``.
# 2. **Ein Wächter ohne Probe.** :data:`MEHRZAHL_MAX_GRUPPE` von 3 auf 99 gesetzt — kein
#    einziger Test wurde rot.
# 3. **Ein zweiter Wächter ohne Probe.** Die leere Lücke («24mm») aus der Bedingung
#    entfernt — ebenfalls kein einziger Test rot.
#
# Zu jedem der drei steht unten eine Probe und eine Mutationsprobe.


@pytest.mark.parametrize("deutsch, englisch", [
    # Die Blende — der gemessene Fall. `objektiv` → `lens` steht im Glossar.
    ("f2.8 objektiv", "f2.8 lens"),
    ("f5.6 objektiv", "f5.6 lens"),
    ("f1.4 objektiv", "f1.4 lens"),
    # Deutsche Schreibung mit Komma, derselbe Fall.
    ("2,8 objektiv", "2,8 lens"),
    # Ein Datum ist auch keine Stückzahl.
    ("16.09.2026 fenster", "16.09.2026 window"),
    # Die Gegenprobe: eine ganze Zahl zählt weiterhin.
    ("12 fenster", "12 windows"),
])
def test_eine_nachkommastelle_ist_keine_anzahl(deutsch, englisch):
    """Die Blendenzahl zählt nichts — gemessener Fehler vom 16.09.2026.

    ``f2.8`` sind für das Zahlenmuster zwei Funde, ``2`` und ``8``. Die ``8`` steht
    unmittelbar vor ``objektiv`` → ``lens``, ist grösser als eins, und die erste Fassung
    machte daraus ``lenses``. Das ist die fünfte Regel dieses Repos in Reinform: Ein
    Prompt mit ``f2.8 lenses`` sieht heil aus, liest sich wie Englisch, und niemand
    sucht dort je einen Fehler.

    ``24mm f8`` führt dieses Modul an zwei Stellen als Musterfall eines Prompts, der
    weder deutsch noch englisch ist — die Blendenzahl ist hier also kein erfundener Fall,
    sondern der Normalfall der Oberfläche.
    """
    assert sprache.glossar_uebersetzung(deutsch)["text"] == englisch


def test_die_nachkommastelle_taucht_nicht_als_gebeugt_im_befund_auf():
    """Und sie behauptet auch im Protokoll nichts.

    Der Befund der ersten Fassung lautete ``{zahl: '8', einzahl: 'lens', mehrzahl:
    'lenses', grund: 'gebeugt'}`` — er zeigte den Unsinn sogar an, nur las ihn keiner.
    Jetzt steht dort keine Beugung mehr.
    """
    befunde = sprache.glossar_uebersetzung("f2.8 objektiv")["mehrzahl"]

    assert all(b["mehrzahl"] is None for b in befunde)
    assert all(b["grund"] != sprache.MEHRZAHL_GEBEUGT for b in befunde)


def test_mutationsprobe_ohne_die_nachkommasperre_entsteht_f2_8_lenses(monkeypatch):
    """Wächter: :func:`sprache._ist_nachkommastelle`. Entschärft zu «gibt es nicht».

    Das ist wörtlich der Zustand vor dem 16.09.2026, und er ist hier festgehalten, damit
    niemand die Sperre für überflüssige Vorsicht hält.
    """
    monkeypatch.setattr(sprache, "_ist_nachkommastelle", lambda text, stuecke, i: False)

    assert sprache.glossar_uebersetzung("f2.8 objektiv")["text"] == "f2.8 lenses"
    assert sprache.glossar_uebersetzung("16.09.2026 fenster")["text"] == \
        "16.09.2026 windows"


def test_eine_zu_lange_wortgruppe_bleibt_in_ruhe():
    """Wächter: :data:`MEHRZAHL_MAX_GRUPPE`. Er hatte bis zum 16.09.2026 keine Probe.

    Vier Wörter zwischen Zahl und Kopf sind kein Wortgruppe mehr, sondern ein halber
    Satz — und in einem halben Satz weiss diese Regel nicht mehr, welches Wort zur Zahl
    gehört. Sie lässt ihn dann in Ruhe, und der Befund sagt, dass sie es tat.
    """
    ergebnis = sprache.glossar_uebersetzung("drei grosse alte hohe fenster")

    assert ergebnis["text"] == "three large old tall window"
    assert ergebnis["mehrzahl"] == (
        {"zahl": "three", "einzahl": None, "mehrzahl": None,
         "grund": sprache.MEHRZAHL_OFFEN},
    )
    # Drei Wörter sind noch eine Wortgruppe — die Grenze liegt genau dazwischen.
    assert sprache.glossar_uebersetzung("drei grosse alte fenster")["text"] == \
        "three large old windows"


def test_mutationsprobe_ohne_die_gruppengrenze_zaehlt_die_zahl_ueber_den_halben_satz(
        monkeypatch):
    """Wächter: :data:`MEHRZAHL_MAX_GRUPPE`, entschärft von 3 auf 99.

    Am 16.09.2026 gemessen: Mit dieser Entschärfung wurde **kein einziger** der 208
    Tests dieses Moduls rot. Ein Wächter, der nicht fällt, bewacht nichts — darum diese
    Probe.
    """
    monkeypatch.setattr(sprache, "MEHRZAHL_MAX_GRUPPE", 99)

    assert sprache.glossar_uebersetzung("drei grosse alte hohe fenster")["text"] == \
        "three large old tall windows"


def test_eine_zahl_ohne_abstand_zaehlt_nichts():
    """Wächter: die **leere** Lücke in :func:`sprache._schliesst_an`. Auch ohne Probe.

    ``24mm`` ist eine Brennweite. Klebt die Zahl am nächsten Wort, ist sie keine Anzahl
    — und ``24mm f8`` ist ausgerechnet der Prompt, den dieses Modul an zwei Stellen als
    Musterfall führt.
    """
    assert sprache.glossar_uebersetzung("24mm wand")["text"] == "24mm wall"
    assert sprache.glossar_uebersetzung("50mm objektiv")["text"] == "50mm lens"


def test_mutationsprobe_ohne_die_leere_luecke_wird_die_brennweite_zur_anzahl(monkeypatch):
    """Wächter: :func:`sprache._schliesst_an`, entschärft auf «nur Satzzeichen trennen».

    Am 16.09.2026 gemessen: Auch diese Entschärfung liess alle 208 Tests grün. Danach
    zählt die Brennweite die Wände.
    """
    monkeypatch.setattr(sprache, "_schliesst_an", lambda luecke: not luecke.strip())

    assert sprache.glossar_uebersetzung("24mm wand")["text"] == "24mm walls"
    # Das Komma bleibt dabei ein Trenner — die beiden Hälften sind auseinanderzuhalten.
    assert sprache.glossar_uebersetzung("zwei, fenster")["text"] == "two, window"


def test_eine_zahl_ohne_lesbare_wortgruppe_meldet_sich_als_offen():
    """Die dritte Antwort, an der Stelle, an der die Regel aufgibt.

    Vorher stand hier ein blosses ``continue``: Der Text blieb richtigerweise stehen,
    aber im Befund stand danach **gar nichts** — und gar nichts liest sich wie «nichts
    zu tun». Eine Zahl, deren Wortgruppe die Regel nicht lesen konnte, ist aber genau
    der NICHT-GEMESSEN-Fall: «zwei, fenster» wäre mit einem Tippfehler weniger eine
    Mehrzahl, und niemand sähe es je.
    """
    for deutsch in ("zwei, fenster", "zwei mit garten", "drei grosse alte hohe fenster"):
        befunde = sprache.glossar_uebersetzung(deutsch)["mehrzahl"]
        assert len(befunde) == 1, (deutsch, befunde)
        assert befunde[0]["grund"] == sprache.MEHRZAHL_OFFEN, deutsch
        assert befunde[0]["einzahl"] is None, deutsch
        assert befunde[0]["mehrzahl"] is None, deutsch


def test_mutationsprobe_ohne_den_offenen_befund_schweigt_die_regel(monkeypatch):
    """Wächter: der Befund am Abbruch. Entschärft, indem die Liste nichts mehr aufnimmt.

    Entschärft wird hier nicht der Text — der bleibt richtig —, sondern die **Auskunft**
    darüber. Genau das ist der Fehlschlag, der wie ein Erfolg aussieht.
    """
    echt = sprache._mehrzahl_anwenden

    def ohne_offene(text):
        neu, befunde = echt(text)
        return neu, tuple(b for b in befunde if b["grund"] != sprache.MEHRZAHL_OFFEN
                          or b["einzahl"] is not None)

    monkeypatch.setattr(sprache, "_mehrzahl_anwenden", ohne_offene)

    assert sprache.glossar_uebersetzung("zwei, fenster")["mehrzahl"] == ()
