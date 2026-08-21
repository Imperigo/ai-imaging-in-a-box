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

def test_stehengebliebenes_wird_gemeldet():
    """Der Fehler der ersten Fassung, als Test festgehalten.

    „abendlicht mit langen Schatten" wurde zu „evening light with langen shadows" — und
    meldete ``unbekannt = ()``. Ein halb übersetzter Prompt, der sich selbst für
    vollständig hält, ist schlimmer als gar keine Übersetzung: Er nimmt dem Leser den
    Anlass hinzusehen.
    """
    ergebnis = sprache.uebersetze("abendlicht mit langen Schatten")
    assert "langen" in ergebnis["unbekannt"]
    assert ergebnis["vollstaendig"] is False
    assert any("halb deutsch" in w for w in ergebnis["warnungen"])


def test_ein_zusammengesetztes_wort_bleibt_stehen_und_sagt_es():
    ergebnis = sprache.uebersetze("Blick auf die Nordfassade")
    assert "nordfassade" in ergebnis["unbekannt"]
    assert ergebnis["vollstaendig"] is False


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
