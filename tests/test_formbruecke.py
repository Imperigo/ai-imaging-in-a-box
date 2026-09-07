"""Die Brücke Formbefund → Bericht → Maske, und wo sie prüfbar ist.

Warum es diese Datei gibt
-------------------------
Am 08.09.2026 wurde `maske.bauwerksmaske(gelaende_zusatz=…)` gebaut und **nicht
verdrahtet** — der Bericht trug keinen Formbefund. Seit dem 09.09. tut er es:
`blender_depth_stage._bbox_bauwerk` fragt `gelaendeform`, wenn die Namensregel fast nichts
getrennt hat, und legt Wort und Namen in den Bericht.

Was hier prüfbar ist, und was nicht
-----------------------------------
**Die eine Hälfte läuft in Blender und ist von hier aus nicht ausführbar** — ``bpy`` gibt
es im Produkt-venv nicht und darf es nach Regel 2 nicht geben. Deshalb stehen hier zwei
Sorten Proben nebeneinander, und sie sind ausdrücklich verschieden viel wert:

* **Echte Proben** über den Abholer-Durchgriff und die Achsenrechnung.
* **Quelltextproben** über den Runner, nach dem Muster von `test_cpu_ist_gemessen.py`.
  *Sie halten fest, was dasteht, nicht was geschieht.* Was wirklich passiert, sagt nur ein
  Lauf am Gerät — dafür gibt es einen Auftrag.
"""
from __future__ import annotations

import re
from pathlib import Path

from aiimaging import abholer, gelaendeform

RUNNER = (Path(__file__).resolve().parents[1]
          / "src" / "aiimaging" / "runners" / "blender_depth_stage.py")
QUELLE = RUNNER.read_text(encoding="utf-8")


# ----------------------------------------------------------------- der Durchgriff

def test_der_abholer_reicht_den_formbefund_durch():
    """Nur so erreicht die Messung der Boxseite die Bildseite."""
    bericht = {"bbox_bauwerk_entschieden_durch": "form",
               "bbox_bauwerk_gelaende_namen": ["IfcCovering_Sub-Division:1"]}
    assert abholer._formgelaende_aus_bericht(bericht) == ("IfcCovering_Sub-Division:1",)


def test_er_reicht_NICHT_durch_wenn_die_namensregel_entschieden_hat():
    """**Die eigentliche Bedingung.** Hat der Name entschieden, findet die Maske dieselben
    Namen ohnehin selbst — die Übertragung wäre wirkungslos und stünde trotzdem als
    `gelaende_quelle: "name+form"` im Befund.

    *Eine Herkunftsangabe, die eine Absicht meldet statt einer Wirkung, ist keine.*
    """
    for wort in ("name", "keine", "", None):
        bericht = {"bbox_bauwerk_entschieden_durch": wort,
                   "bbox_bauwerk_gelaende_namen": ["Gelaende-Platte"]}
        assert abholer._formgelaende_aus_bericht(bericht) == (), f"bei {wort!r}"


def test_ein_bericht_ohne_die_felder_gibt_leer_und_stuerzt_nicht():
    """Alte Berichte gibt es weiterhin — sie sind kein Fehler, nur älter."""
    assert abholer._formgelaende_aus_bericht({}) == ()


# ----------------------------------------------------------------- die Achse

def test_die_hochachse_ist_in_blender_eine_ANDERE_als_in_gltf():
    """**Die gefährlichste Stelle dieses Baus.**

    `gelaendeform` hat die Vorgabe `hoch=1` — glTF, Y oben, so wie `glbbox.knotenboxen`
    die Boxen liefert. In Blenders Weltkoordinaten ist Z oben.

    *Ein falscher Achsenindex machte Wände flach und Böden aufragend — und keine
    Massprobe sähe es.* Genau die Klasse Fehler, die am 01.09.2026 ein Gebäude auf den
    Kopf gestellt hat: `R_x(180)` lässt jede Kantenlänge gleich, nur die Vorzeichen kippen.
    """
    # Eine Platte und eine Wand, Z oben (Blender-Weltkoordinaten).
    szene = [("Platte", (-50, -50, -1), (50, 50, 0)),
             ("Wand", (-10, -10, 0), (10, 10, 30))]

    richtig = gelaendeform.gelaende_knoten(szene, hoch=2)
    assert richtig["gelaende"] == ("Platte",)
    assert richtig["bauwerk"] == ("Wand",)

    falsch = gelaendeform.gelaende_knoten(szene, hoch=1)
    assert falsch["gelaende"] != ("Platte",), (
        "Mit der falschen Achse muss ein ANDERES Ergebnis herauskommen — sonst haelt "
        "diese Probe nichts, und der Fehler waere unsichtbar.")


def test_der_runner_uebergibt_die_blender_achse_ausdruecklich():
    """Quelltextprobe: Der Wert wird **übergeben**, nicht geerbt.

    Eine geerbte Vorgabe wäre hier die stille Hälfte einer doppelten Vorgabe — sie stünde
    in `gelaendeform` und meinte glTF, und niemand sähe, dass hier etwas anderes gilt.
    """
    assert "HOCHACHSE_BLENDER = 2" in QUELLE
    assert re.search(r"gelaende_knoten\([^)]*hoch=HOCHACHSE_BLENDER", QUELLE), (
        "Der Runner muss die Achse ausdruecklich uebergeben.")
    # NUR AUFRUFE, NICHT PROSA. Der Kommentar an `HOCHACHSE_BLENDER` nennt `hoch=1`
    # ausdruecklich, um den Unterschied zu erklaeren — das ist die Dokumentation, die
    # hier gewollt ist, und keine Fundstelle.
    for aufruf in re.findall(r"\b(?:gelaende_knoten|merkmale|urteil)\([^)]*\)", QUELLE):
        assert "hoch=1" not in aufruf, f"Aufruf mit glTF-Achse im Runner: {aufruf}"


# ----------------------------------------------------------------- der Runner

def test_der_runner_holt_die_schwelle_und_schreibt_sie_nicht_hin():
    """*Zwei Wege zur selben Zahl sollen bei derselben Lage dieselbe Auskunft geben* —
    und dann darf die Schwelle nicht zweimal dastehen."""
    assert "glbbox.GERINGE_SCHRUMPFUNG" in QUELLE
    assert not re.search(r"GERINGE_SCHRUMPFUNG\s*=", QUELLE), (
        "Die Schwelle gehoert nach `glbbox`, nicht in den Runner.")


def test_der_runner_fragt_die_form_erst_unterhalb_der_schwelle():
    """Sonst trüge jeder Bericht einen Formbefund, auch der, dessen Namensregel sauber
    getrennt hat — und eine Auskunft, die immer dasteht, wird nicht gelesen."""
    stelle = QUELLE.index("form = _form_zweitmeinung(")
    davor = QUELLE[:stelle]
    assert "if schrumpfung < glbbox.GERINGE_SCHRUMPFUNG:" in davor[-1200:], (
        "Der Aufruf muss im Zweig unterhalb der Schrumpfungsschwelle stehen.")


def test_beide_berichtsfelder_stehen_immer_da():
    """*Ein Feld, das mal da ist und mal nicht, zwingt jeden Leser zu einer
    Fallunterscheidung, die er vergessen wird* — und dann liest er `None` als «kein
    Gelände» statt als «nicht gefragt».
    """
    assert '"bbox_bauwerk_entschieden_durch": bau_form["entschieden_durch"],' in QUELLE
    assert '"bbox_bauwerk_gelaende_namen": list(bau_form["gelaende_namen"]),' in QUELLE
    # JEDER RUECKGABEWEG VON `_bbox_bauwerk` TRAEGT EINEN FORMBEFUND — geprueft ueber den
    # Syntaxbaum und nicht ueber Zeilen.
    #
    # *Ein `return`, das ueber vier Zeilen laeuft, ist zeilenweise nicht zu pruefen* —
    # der erste Anlauf dieser Probe scheiterte genau daran und haette bei einem
    # mehrzeiligen Rueckgabeweg still nichts geprueft.
    import ast

    baum = ast.parse(QUELLE)
    fn = next(k for k in ast.walk(baum)
              if isinstance(k, ast.FunctionDef) and k.name == "_bbox_bauwerk")
    rueckgaben = [k for k in ast.walk(fn) if isinstance(k, ast.Return)]
    assert rueckgaben, "keine Rueckgabe gefunden — dann prueft diese Probe nichts"
    for r in rueckgaben:
        assert isinstance(r.value, ast.Tuple) and len(r.value.elts) == 5, (
            f"Rueckgabe in Zeile {r.lineno} hat "
            f"{len(r.value.elts) if isinstance(r.value, ast.Tuple) else '?'} Werte "
            f"statt fuenf — der Formbefund fehlt.")


def test_der_runner_faellt_nicht_still_zurueck_wenn_das_modul_fehlt():
    """*Ein stiller Rückfall sähe aus wie «die Form hat nichts gefunden», und richtig wäre
    «die Form wurde nie gefragt».*"""
    assert "die Form wurde nie gefragt" in QUELLE
