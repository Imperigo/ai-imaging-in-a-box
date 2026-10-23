"""Die acht Stimmungen und ihre Himmelsbilder — Heim-PC-Teil des Knotens «Stimmung» (H1).

**Anlass:** Entscheide 107, 110 und 113 (20.10.2026, Blätter 31–33 der Entwurfsfläche). Der
Knoten «Stimmung» bestellt ``render.environment {preset, hdri?, intensitaet?, rotationGrad?}``
(Vertrag mit dem Integrator, nach dem v0.1.9-Schnitt). Bis dahin wies der Heim-PC das Feld ab
(``kosmo_szene.ABGEWIESENE_FELDER``): Es gab keinen Weg, Umgebungsbilder mit zulässiger
Lizenz zu uns zu bringen. Seit Entscheid 107 sind CC0-Bilddaten zugelassen (Regel 1,
Präzisierung Texturen und Himmelsbilder) — die HomeStation hat acht Himmelsbilder von
Poly Haven abgelegt.

**Was hier steht und was nicht:**

* Die **Tabelle** der acht Stimmungen: Vorgabe-Himmelsbild (Namensstamm des Poly-Haven-
  Assets), Satz für den Prompt (deutsch wie ``VIS_STIMMUNGEN`` drüben, englisch wie die
  Bausteine in :mod:`aiimaging.prompts`), und woran man erkennt, dass der Prompt den Satz
  schon trägt.
* Die **Auflösung einer Datei** am Heim-PC: ``$AIIMAGING_HIMMEL_ORDNER/<preset>__<hdri>_<2k|4k>.hdr``.
  **Kein Pfad im Repo** (Regel 3) — der Ordner kommt nur aus der Umgebungsvariable; die
  Bilder selbst liegen nicht im Repo und stehen im ``NOTICE`` als «nicht ausgeliefert, am
  Heim-PC, CC0».
* **Nicht** hier: das Blender-Seitige (Welt mit Environment Texture) — das steht im Runner
  ``runners/blender_depth_stage.py`` (Regel 2), der nur den Pfad bekommt.

Reine Standardbibliothek, ohne Oberfläche aufrufbar (Regel 4).
"""
from __future__ import annotations

import math
import os
import re
from pathlib import Path

__all__ = ["HIMMEL_ORDNER_ENV", "PRESETS", "STIMMUNGEN", "HDRI_MUSTER", "HERKUNFT",
           "VORGABE_INTENSITAET", "VORGABE_DREHUNG_GRAD", "aufloesung_fuer",
           "dateiname", "himmel_ordner", "himmel_datei", "himmelsbilder_stand",
           "prompt_satz", "PRESET_WEISS", "TONWERTE", "NEUTRAL_KELVIN",
           "licht_der_stimmung", "toenung_fuer", "vorgabe_staerke", "hintergrund_aus_himmel",
           "HINTERGRUND_HORIZONT_GRAD", "HINTERGRUND_ZENIT_GRAD",
           # auf-20261020-293: Licht mit Schatten, Hintergrund mit Abstand.
           "LICHT_HERKUNFT", "HINTERGRUND_ABSTAND_EV", "HINTERGRUND_RICHTUNGEN",
           "KONTRAST_SCHWELLE", "GELAENDE_GRAU", "GELAENDE_GRAU_WEISS", "SONNE_FAKTOR",
           "leuchtdichte", "richtung_im_bild", "sonne_aus_himmel", "lampe_aus_himmel",
           "hintergrund_mit_abstand", "haus_leuchtdichte", "euler_fuer_richtung",
           # auf-20261020-294: Sonne seitlich der Kamera, weicher Rueckfall mit grossem Winkel.
           "SONNE_SEITEN", "SONNE_SEITLICH_BEREICH_GRAD", "WEICH_WINKEL_GRAD",
           "kamera_azimut_grad", "drehung_zur_kamera", "winkel_zur_blickachse",
           # auf-20261020-295: die Vorprobe misst das Haus in Blendenstufen.
           "HAUS_MASS", "HAUS_MASSE", "STUFEN_UNTERGRENZE",
           # auf-20261022-333: ein sichtbarer Himmel passt zur Stimmung, nie schwarz.
           "HIMMEL_FAKTOR_MIN", "HELLE_HIMMEL", "himmel_untergrenze", "himmel_begrenzen",
           # auf-20261022-334: unter dem Horizont Boden statt gespiegeltem Himmel.
           "BODEN_DUNST_GRAD", "boden_bis_horizont",
           # auf-20261022-336: der Boden so hell und so gefaerbt wie die Platte.
           "BODEN_FASSUNG", "boden_zum_faktor",
           # auf-20261022-338: abends die ferne Erde auf Plattenhoehe, die nahe daemmrig.
           "BODEN_FERN_GRAD", "boden_fern_zum_faktor"]

#: Die Umgebungsvariable mit dem Ordner der Himmelsbilder — der Wert steht nur am Heim-PC.
HIMMEL_ORDNER_ENV = "AIIMAGING_HIMMEL_ORDNER"

#: Die acht Schlüssel — wörtlich die Aufzählung ``StimmungPreset`` des Vertrags.
PRESETS = ("morgen", "mittag", "abend", "blaue-stunde", "bedeckt", "nebel", "winter",
           "weiss")

#: «Weiss» macht zusätzlich alle Oberflächen weiss wie ein Gipsmodell (Entscheid 113).
PRESET_WEISS = "weiss"

#: Der Namensstamm eines Himmelsbilds im Vertrag — nie ein Pfad (Regel 3).
HDRI_MUSTER = re.compile(r"^[a-z0-9_]{1,64}$")

#: Woher die Himmelsbilder kommen. Als Daten, damit NOTICE und Ergebnis dieselbe Quelle nennen.
HERKUNFT = {"quelle": "Poly Haven", "lizenz": "CC0-1.0",
            "adresse": "https://polyhaven.com/hdris",
            "vermerk": "nicht ausgeliefert, am Heim-PC abgelegt, unverändert"}

#: Vorgaben des Heim-PC, wenn das Feld fehlt (der Vertrag hat keine Defaults — der Heim-PC
#: setzt sie und nennt sie im Ergebnis).
VORGABE_INTENSITAET = 1.0
VORGABE_DREHUNG_GRAD = 0.0

#: Die Tonwertkurve, mit der ein Bild MIT Himmelsbild gerechnet wird — in dieser Reihenfolge
#: versucht, die erste, die das Blender am Heim-PC kennt, gilt (der Bericht nennt sie).
#:
#: **Anlass (auf-20261020-292, B1):** Der Runner setzte immer «Standard» — eine gerade Linie
#: von Renderwert zu Bildwert, für die Messläufe ohne Himmelsbild richtig (eine
#: nachvollziehbare Zuordnung). Ein Himmelsbild bringt aber Werte weit über 1 ins Bild (die
#: Sonne, ein heller Himmel), und «Standard» schneidet sie ab: Das Haus war bei «mittag» eine
#: reine weisse Fläche (11,9 % der Bildpunkte voll weiss). AgX (ab Blender 4.0, Vorgabe dort)
#: rollt die Lichter weich ab, Filmic ist sein Vorgänger. **Ohne Himmelsbild bleibt «Standard»,
#: Wort für Wort** — jede bisherige Messung hängt daran.
TONWERTE = ("AgX", "Filmic")

#: Die Farbtemperatur, die keine Tönung bedeutet.
NEUTRAL_KELVIN = 6500.0

#: Wo der ruhige Hintergrund seine zwei Farben aus dem Himmelsbild nimmt (Grad über dem
#: Horizont): Horizont ein Band knapp darüber, Zenit die obere Kalotte. Median, nicht
#: Mittel — sonst färbt die Sonnenscheibe (Werte über 10'000) den ganzen Grund weiss.
HINTERGRUND_HORIZONT_GRAD = (2.0, 15.0)
HINTERGRUND_ZENIT_GRAD = (45.0, 90.0)

#: Woher die Lichtwerte je Stimmung kommen (auf-20261020-293): gesetzt, nicht gemessen.
LICHT_HERKUNFT = ("gesetzt, nicht gemessen (auf-20261020-293); die HomeStation misst in "
                  "auf-20261020-294")

#: Der feste Abstand des ruhigen Hintergrunds zum Haus, in Blendenstufen (auf-20261020-293,
#: Punkt 1): Eine Stufe heisst halb so hell bzw. doppelt so hell. **In Stufen, nicht in
#: Grauwerten**, weil Stärke und Belichtung Haus und Hintergrund mit demselben Faktor
#: verschieben (293: winter 0,5 / 1,0 / 2,0 gab −0,6 / −0,5 / −0,4 Grauwerte) — ein Verhältnis
#: bleibt unter beiden stehen, ein Grauwertabstand nicht.
HINTERGRUND_ABSTAND_EV = 1.0
HINTERGRUND_RICHTUNGEN = ("dunkler", "heller", "auto")

#: Ab welcher Differenz (Grauwerte 0..255, Haus minus Hintergrund daneben) das Haus als
#: «kaum sichtbar» gilt — gesetzt aus 293: bei −8,6 / −7,5 / −1,3 / −0,5 verschwamm es, bei
#: +20,8 war es lesbar.
KONTRAST_SCHWELLE = 20.0

#: Die Geländeplatte ohne gewähltes Material (auf-20261020-293, Punkt 3): ein ruhiges,
#: leicht dunkleres Neutralgrau (linear), damit Schatten auf ihr sichtbar werden — bei
#: «weiss» ein helleres, damit das Gipsmodell (0,80) darauf steht. Kein Material der
#: Bibliothek: Die Platte ist Grundlage, kein Entwurf.
GELAENDE_GRAU = (0.30, 0.30, 0.30)
GELAENDE_GRAU_WEISS = (0.55, 0.55, 0.55)

#: Ab wievielfacher Himmelshelligkeit (Median über dem Horizont) ein Bildpunkt zur
#: Sonnenscheibe zählt. Auf einer 128 × 64-Kopie verteilt sich die Scheibe (0,5°) auf einen
#: Punkt von 2,8°; ihr Wert sinkt dort von ~10⁴ auf ~10² — weit über diesem Faktor. Ein
#: bedeckter Himmel erreicht ihn nicht.
SONNE_FAKTOR = 20.0
#: Unter dieser Höhe steht eine Lampe nicht — eine harte Sonne knapp darüber gibt
#: Streiflicht; die weiche Lampe (ohne Sonne) kommt mindestens von hier.
SONNE_MIN_HOEHE_GRAD = 2.0
WEICH_MIN_HOEHE_GRAD = 15.0
#: Welcher Anteil der hellsten Punkte die Richtung der weichen Lampe bestimmt.
HELLSTER_ANTEIL = 0.02

#: Der Winkel der weichen Lampe, wenn eine Stimmung mit Sonne keine Sonnenscheibe im Bild
#: hat und keinen eigenen ``winkel_weich_grad`` nennt (auf-20261020-294, B2): Bis dahin galt
#: auch für den weichen Rückfall der kleine Winkel der Sonne (morgen 1,0°, winter 1,5°) —
#: harte Schattenkanten aus einer Lampe, die der Bericht «weich» nannte.
WEICH_WINKEL_GRAD = 25.0

#: Die Sonne seitlich der Kamera (auf-20261020-294, B1). Wo im Himmelsbild die Sonne steht,
#: wusste niemand: In allen acht Bildern stand sie 0–40° neben der Blickachse der Kamera
#: (abend 5°) — Frontallicht, die Schatten fielen hinter das Haus. Seither wird das
#: Himmelsbild JE KAMERA so gedreht, dass die Sonne ``sonne_seitlich_grad`` neben der Achse
#: Haus–Kamera steht, auf der Seite ``sonne_seite``. 0° hiesse: Sonne im Rücken der Kamera,
#: 90°: genau von der Seite, 180°: Gegenlicht. Der Bereich 60–100° gibt beides — eine
#: beleuchtete Fassade und einen Schatten, der seitlich fällt und im Bild liegt.
SONNE_SEITEN = ("links", "rechts")
SONNE_SEITLICH_BEREICH_GRAD = (60.0, 100.0)

#: Die acht Stimmungen.
#:
#: ``hdri`` ist die Vorgabe je Stimmung (Tabelle der HomeStation, 20.10.2026; am selben Abend
#: getauscht, ``hdri_vorher`` nennt das alte Bild — die alten Dateien bleiben am Heim-PC
#: liegen und sind über ``render.environment.hdri`` weiter bestellbar). Alle Poly Haven, CC0.
#:
#: **Licht je Stimmung (auf-20261020-292, B1/B3) — gesetzt, nicht gemessen:**
#: ``belichtung_ev`` (Blenders Belichtung in Blendenstufen, −1 halbiert das Licht im Bild),
#: ``staerke`` (Vorgabe für ``intensitaet``, wenn die Bestellung keine nennt) und ``kelvin``
#: (Farbtemperatur der Tönung des Himmelslichts, ``None`` = keine). Die Zahlen sind ein erster
#: Stand auf den neuen Bildern; ``auf-20261020-293`` misst je Stimmung den Anteil voll weisser
#: Bildpunkte am Haus und meldet, wo nachzustellen ist.
#:
#: **Licht mit Schatten (auf-20261020-293, Punkte 2–5) — ebenso gesetzt, nicht gemessen**
#: (:data:`LICHT_HERKUNFT`; ``auf-20261020-294`` misst): ``sonne`` (ja: eine harte
#: Sonnenlampe aus der Richtung der Sonne im Himmelsbild; nein: eine weiche Lampe aus dem
#: hellsten Bereich), ``sonnen_staerke`` (Stärke der Lampe als Vielfaches der
#: Himmelshelligkeit auf einer waagrechten Fläche), ``fuell_staerke`` (Anteil des
#: Himmelsbilds als Fülllicht), ``winkel_grad`` (Grösse der Lichtquelle: klein = harte
#: Schattenkante, gross = weiche), ``look`` (die kontrastreichere Fassung der Tonwertkurve,
#: Punkt 4), ``hintergrund_richtung`` (ob der ruhige Hintergrund dunkler oder heller als das
#: Haus gesetzt wird, Punkt 1). Blaue Stunde seit 293 tiefer: −0,7 statt +0,5, 9000 K.
#:
#: **Nach der Messung auf-20261020-294 — wieder gesetzt, nicht gemessen** (``auf-20261020-295``
#: misst): ``sonne_seitlich_grad`` und ``sonne_seite`` (B1: die Sonne je Kamera seitlich der
#: Blickachse statt dort, wo sie im Himmelsbild zufällig steht; abend 80° rechts für
#: Streiflicht und eine andere Seite als der Morgen), ``winkel_weich_grad`` (B2: der Winkel
#: der weichen Lampe, wenn eine Stimmung mit Sonne keine Scheibe im Bild hat — 25° statt
#: des Sonnenwinkels), Blaue Stunde ``belichtung_ev`` −1,5 und ``hintergrund_abstand_ev`` 2
#: (B3: pastell bei −0,7 und einer Stufe), abend ``belichtung_ev`` −0,5 statt 0 (das Haus
#: war mit Mittel 234 fast weiss; die Belichtung senkt Licht und Schatten gleich und lässt
#: das Verhältnis Sonne zu Fülllicht stehen — weniger ``sonnen_staerke`` hätte genau das
#: Verhältnis verkleinert und das Bild noch flacher gemacht) und ein englischer Satz ohne
#: «lit interiors glowing» (das KI-Bild wurde Nacht).
#: ``prompt_de``
#: ist der Satz, den der Knoten drüben in den Prompt legt (``VIS_STIMMUNGEN``; morgen, abend
#: und weiss wörtlich wie dort), ``prompt_en`` der Satz, den der Heim-PC anfügt, wenn der
#: übersetzte Prompt keines der ``merkmale`` trägt — sonst stünde die Stimmung doppelt da.
#: Keine Bauteilwörter (``prompts.BAUTEILWOERTER``) im englischen Satz: Er wird nach dem
#: Bauteilwächter angefügt und soll nichts bestellen, was die Geometrie nicht trägt.
STIMMUNGEN = {
    "morgen": {
        "label": "Morgenlicht", "hdri": "kloppenheim_06_puresky",
        "hdri_vorher": "sunny_vondelpark",
        "belichtung_ev": -0.5, "staerke": 1.0, "kelvin": None,
        "sonne": True, "sonnen_staerke": 3.0, "fuell_staerke": 0.35, "winkel_grad": 1.0,
        "winkel_weich_grad": 25.0, "sonne_seitlich_grad": 70.0, "sonne_seite": "links",
        "look": "Medium High Contrast", "hintergrund_richtung": "dunkler",
        "prompt_de": "Morgenlicht, klare lange Schatten, frische kühle Luft",
        "prompt_en": "early morning light, clear long shadows, fresh cool air",
        "merkmale": ("morning",)},
    "mittag": {
        "label": "Mittag", "hdri": "kloofendal_43d_clear_puresky",
        "hdri_vorher": None,
        "belichtung_ev": -1.0, "staerke": 1.0, "kelvin": None,
        "sonne": True, "sonnen_staerke": 3.0, "fuell_staerke": 0.45, "winkel_grad": 0.8,
        "winkel_weich_grad": 25.0, "sonne_seitlich_grad": 65.0, "sonne_seite": "links",
        "look": "Medium High Contrast", "hintergrund_richtung": "dunkler",
        "prompt_de": "Mittagslicht, hohe Sonne, klarer Himmel",
        "prompt_en": "midday light, high sun, clear sky",
        "merkmale": ("midday", "noon")},
    "abend": {
        "label": "Abendstimmung", "hdri": "belfast_sunset_puresky",
        "hdri_vorher": "fish_eagle_hill",
        "belichtung_ev": -0.5, "staerke": 1.0, "kelvin": 5000.0,
        "sonne": True, "sonnen_staerke": 3.5, "fuell_staerke": 0.3, "winkel_grad": 1.0,
        "winkel_weich_grad": 25.0, "sonne_seitlich_grad": 80.0, "sonne_seite": "rechts",
        "look": "Medium High Contrast", "hintergrund_richtung": "dunkler",
        "prompt_de": "Abendstimmung, warmes Licht, leuchtende Fenster",
        "prompt_en": "evening mood, warm low sunlight, long raking shadows, golden hour",
        "merkmale": ("evening", "sunset", "golden hour")},
    "blaue-stunde": {
        "label": "Blaue Stunde", "hdri": "qwantani_dusk_2_puresky",
        "hdri_vorher": "the_sky_is_on_fire",
        "belichtung_ev": -1.5, "staerke": 1.0, "kelvin": 9000.0,
        "sonne": False, "sonnen_staerke": 0.6, "fuell_staerke": 0.7, "winkel_grad": 30.0,
        "sonne_seitlich_grad": 70.0, "sonne_seite": "links",
        "look": "Medium High Contrast", "hintergrund_richtung": "dunkler",
        "hintergrund_abstand_ev": 2.0,
        "prompt_de": "Blaue Stunde, tiefblauer Himmel, warm leuchtende Innenräume",
        "prompt_en": "blue hour, deep blue sky, warmly lit interiors",
        "merkmale": ("blue hour", "twilight", "dusk")},
    "bedeckt": {
        "label": "Bedeckt", "hdri": "overcast_soil_puresky",
        "hdri_vorher": None,
        "belichtung_ev": -0.5, "staerke": 1.0, "kelvin": None,
        "sonne": False, "sonnen_staerke": 0.8, "fuell_staerke": 0.8, "winkel_grad": 40.0,
        "sonne_seitlich_grad": 70.0, "sonne_seite": "links",
        "look": "Medium High Contrast", "hintergrund_richtung": "heller",
        "prompt_de": "bedeckter Himmel, weiches gleichmässiges Licht",
        "prompt_en": "overcast sky, soft even light",
        "merkmale": ("overcast",)},
    "nebel": {
        "label": "Nebel", "hdri": "kloofendal_misty_morning_puresky",
        "hdri_vorher": "kloppenheim_04",
        "belichtung_ev": 0.0, "staerke": 1.0, "kelvin": None,
        "sonne": False, "sonnen_staerke": 0.6, "fuell_staerke": 0.85, "winkel_grad": 50.0,
        "sonne_seitlich_grad": 70.0, "sonne_seite": "links",
        "look": "Medium High Contrast", "hintergrund_richtung": "heller",
        "prompt_de": "Nebel, gedämpftes Licht, Tiefe im Dunst",
        "prompt_en": "fog, muted light, depth fading into haze",
        "merkmale": ("fog", "mist", "haze")},
    "winter": {
        "label": "Winter", "hdri": "snow_field",
        "hdri_vorher": "snowy_field",
        "belichtung_ev": -0.5, "staerke": 1.0, "kelvin": 7500.0,
        "sonne": True, "sonnen_staerke": 2.5, "fuell_staerke": 0.45, "winkel_grad": 1.5,
        "winkel_weich_grad": 25.0, "sonne_seitlich_grad": 70.0, "sonne_seite": "links",
        "look": "Medium High Contrast", "hintergrund_richtung": "heller",
        "prompt_de": "Winter, Schnee am Boden, kaltes klares Licht",
        "prompt_en": "winter, snow on the ground, cold clear light",
        "merkmale": ("winter", "snow")},
    "weiss": {
        # Getauscht am 21.10.2026 (auf-20261021-306 B5): studio_small_08 hat grosse dunkle Wandflächen und zeigte
        # einen dunklen Raum; white_studio_06 ist eine weisse Hohlkehle mit weichem Oberlicht (HomeStation, Wahl
        # aus 11 Poly-Haven-Studios). Das alte Bild bleibt am Heim-PC als Rückfall.
        "label": "Weissmodell", "hdri": "white_studio_06",
        "hdri_vorher": "studio_small_08",
        "belichtung_ev": 0.0, "staerke": 1.0, "kelvin": None,
        "sonne": False, "sonnen_staerke": 1.2, "fuell_staerke": 0.6, "winkel_grad": 20.0,
        "sonne_seitlich_grad": 70.0, "sonne_seite": "links",
        "look": "Medium High Contrast", "hintergrund_richtung": "dunkler",
        "prompt_de": "Weissmodell, neutrales Studiolicht, keine Materialien",
        "prompt_en": "white plaster study model, neutral studio light, no materials",
        "merkmale": ("white model", "plaster model", "white plaster", "no materials")},
}


def vorgabe_staerke(preset: str) -> float:
    """Die Stärke des Himmelsbilds, wenn ``intensitaet`` nicht bestellt ist — je Stimmung."""
    eintrag = STIMMUNGEN.get(preset) or {}
    wert = eintrag.get("staerke")
    return float(wert) if wert is not None else VORGABE_INTENSITAET


def toenung_fuer(kelvin) -> tuple[float, float, float] | None:
    """Die Tönung des Himmelslichts zu einer Farbtemperatur — linear, Helligkeit gehalten.

    Relativ zu :data:`NEUTRAL_KELVIN` (``kelvin_zu_farbe(k) / kelvin_zu_farbe(6500)`` je
    Kanal) und danach so geteilt, dass die Rec.-709-Helligkeit 1 bleibt: Die Tönung färbt,
    die Belichtung hellt — zwei Regler, zwei Fragen. ``None`` ohne Farbtemperatur.
    """
    if kelvin is None:
        return None
    from .sonne import kelvin_zu_farbe  # noqa: PLC0415 — reine Rechnung, ohne Blender
    k = kelvin_zu_farbe(float(kelvin))
    n = kelvin_zu_farbe(NEUTRAL_KELVIN)
    roh = [a / b for a, b in zip(k, n)]
    hell = 0.2126 * roh[0] + 0.7152 * roh[1] + 0.0722 * roh[2]
    return tuple(round(c / hell, 6) for c in roh)


def licht_der_stimmung(preset, *, sonne_seite=None) -> dict:
    """``{belichtung_ev, kelvin, toenung_linear, tonwerte}`` — die Lichtdaten einer Stimmung.

    ``tonwerte`` ist die Reihenfolge aus :data:`TONWERTE`; welche gegriffen hat, sagt der
    Bericht des Runners. Unbekannte Stimmung: Belichtung 0, keine Tönung.

    ``sonne_seite`` (``'links'``/``'rechts'``, auf-20261020-294) wählt die Seite der Sonne
    gegen die Vorgabe der Stimmung — aus Python, ohne Oberfläche (Regel 4).
    """
    if sonne_seite is not None and sonne_seite not in SONNE_SEITEN:
        raise ValueError(f"Seite {sonne_seite!r} — erlaubt: {', '.join(SONNE_SEITEN)}.")
    eintrag = STIMMUNGEN.get(preset) or {}
    kelvin = eintrag.get("kelvin")
    aus = {"belichtung_ev": float(eintrag.get("belichtung_ev") or 0.0),
           "kelvin": float(kelvin) if kelvin is not None else None,
           "toenung_linear": (list(toenung_fuer(kelvin)) if kelvin is not None else None),
           "tonwerte": list(TONWERTE)}
    # LICHT MIT SCHATTEN (auf-20261020-293): nur fuer bekannte Stimmungen — eine unbekannte
    # bekommt keine Lampe, kein Grau und keinen Abstand, also das Licht von vor 293.
    if eintrag.get("sonne") is not None:
        aus.update(
            sonne=bool(eintrag["sonne"]),
            sonnen_staerke=float(eintrag["sonnen_staerke"]),
            fuell_staerke=float(eintrag["fuell_staerke"]),
            winkel_grad=float(eintrag["winkel_grad"]),
            look=eintrag.get("look"),
            hintergrund_richtung=eintrag.get("hintergrund_richtung") or "auto",
            # auf-20261020-294 (B1, B2): Sonne seitlich der Kamera, weicher Rueckfall.
            sonne_seitlich_grad=float(eintrag.get("sonne_seitlich_grad") or 0.0) or None,
            sonne_seite=eintrag.get("sonne_seite") or "links",
            # Ohne Sonne IST die Lampe weich: ihr Winkel ist der der Stimmung.
            winkel_weich_grad=(float(eintrag.get("winkel_weich_grad")
                                     or max(float(eintrag["winkel_grad"]), WEICH_WINKEL_GRAD))
                               if eintrag["sonne"] else float(eintrag["winkel_grad"])),
            hintergrund_abstand_ev=float(eintrag.get("hintergrund_abstand_ev")
                                         or HINTERGRUND_ABSTAND_EV),
            kontrast_schwelle=KONTRAST_SCHWELLE,
            # auf-20261020-295 (N1): die Vorprobe misst das Haus in Blendenstufen — als
            # Lichtdatum, damit eine Grundlage von vorher kein Treffer mehr ist.
            haus_mass=HAUS_MASS,
            gelaende_grau=list(GELAENDE_GRAU_WEISS if preset == PRESET_WEISS
                               else GELAENDE_GRAU),
            herkunft_licht=LICHT_HERKUNFT)
        if sonne_seite is not None:
            aus["sonne_seite"] = sonne_seite
    return aus


def _median(werte):
    werte = sorted(werte)
    n = len(werte)
    if n == 0:
        return None
    mitte = n // 2
    return werte[mitte] if n % 2 else 0.5 * (werte[mitte - 1] + werte[mitte])


def hintergrund_aus_himmel(pixel, breite: int, hoehe: int, *, kanaele: int = 4) -> dict:
    """Die zwei Farben des ruhigen Hintergrunds aus einem (verkleinerten) Himmelsbild.

    **Anlass (auf-20261020-292, B2):** Das Himmelsbild war sichtbarer Hintergrund — ein
    Bodenfoto mit Wald und Felsen, das Haus schwebte davor. Seither gibt das Bild nur Licht
    und Spiegelungen; was die Kamera direkt sieht, ist ein Verlauf vom Horizont zum Zenit in
    den Farben dieses Himmels (der Runner baut ihn mit «Is Camera Ray»).

    ``pixel`` ist die flache Liste in Blenders Reihenfolge (Zeile 0 **unten**, je Bildpunkt
    ``kanaele`` Werte), das Bild equirektangulär (oberste Zeile = Zenit, Mitte = Horizont).
    Je Band der Median je Kanal — die Sonnenscheibe zählt dann nicht.

    Returns:
        ``{horizont: [r, g, b], zenit: [r, g, b]}`` (linear) — ``None`` je Band ohne Punkte.
    """
    breite, hoehe = int(breite), int(hoehe)
    if breite <= 0 or hoehe <= 0 or len(pixel) < breite * hoehe * kanaele:
        raise ValueError(f"Himmelsbild {breite} x {hoehe} mit {len(pixel)} Werten passt nicht.")

    def band(grad):
        unten, oben = grad
        zeilen = [z for z in range(hoehe)
                  if unten <= ((z + 0.5) / hoehe * 180.0 - 90.0) <= oben]
        kanal = [[], [], []]
        for z in zeilen:
            basis = z * breite * kanaele
            for x in range(breite):
                i = basis + x * kanaele
                for c in range(3):
                    kanal[c].append(float(pixel[i + c]))
        if not zeilen:
            return None
        return [round(_median(k), 6) for k in kanal]

    return {"horizont": band(HINTERGRUND_HORIZONT_GRAD),
            "zenit": band(HINTERGRUND_ZENIT_GRAD)}


# ======================================================================================
# Licht mit Schatten und ein Hintergrund mit Abstand (auf-20261020-293)
# ======================================================================================

def leuchtdichte(rgb) -> float:
    """Rec.-709-Helligkeit eines linearen Farbwerts — dieselbe Gewichtung wie :func:`toenung_fuer`."""
    return 0.2126 * float(rgb[0]) + 0.7152 * float(rgb[1]) + 0.0722 * float(rgb[2])


def richtung_im_bild(spalte: float, zeile: float, breite: int, hoehe: int) -> tuple:
    """Die Richtung (Z oben) eines Punkts im equirektangulären Bild, Blenders Abbildung.

    Blender liest ein Himmelsbild mit ``u = 0,5 − atan2(y, x) / 2π`` und
    ``v = atan2(z, √(x² + y²)) / π + 0,5`` (Zeile 0 **unten**). Umgekehrt: Höhe
    ``(v − 0,5) · π``, Azimut ``(0,5 − u) · 2π``. ``spalte``/``zeile`` dürfen Bruchteile sein
    (Schwerpunkt).
    """
    u = (float(spalte) + 0.5) / breite
    v = (float(zeile) + 0.5) / hoehe
    hoch = (v - 0.5) * math.pi
    azimut = (0.5 - u) * 2.0 * math.pi
    return (math.cos(hoch) * math.cos(azimut), math.cos(hoch) * math.sin(azimut),
            math.sin(hoch))


def _drehe_z(v, grad: float):
    w = math.radians(grad)
    c, s = math.cos(w), math.sin(w)
    return (c * v[0] - s * v[1], s * v[0] + c * v[1], v[2])


def _einheit(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v) if n > 0 else None


def sonne_aus_himmel(pixel, breite: int, hoehe: int, *, kanaele: int = 4) -> dict:
    """Wo im Himmelsbild die Sonne steht, welche Farbe und wieviel Licht sie gibt.

    **Anlass (auf-20261020-293, Punkt 2):** Die Bilder waren flach, ohne Schatten am Haus und
    auf der Platte. Die Puresky-Bilder tragen die Sonne als kleine, sehr helle Scheibe; über
    die Umgebung allein verteilt Cycles sie bei wenigen Samples zu einem weichen Licht. Hier
    wird sie gefunden, damit eine Sonnenlampe aus **genau dieser Richtung** scheint.

    Rechnung auf einer kleinen Kopie (wie :func:`hintergrund_aus_himmel`, dieselbe
    Reihenfolge: Zeile 0 unten), nur über dem Horizont, jeder Punkt mit seinem Raumwinkel
    gewichtet (``cos(Höhe)``):

    * **Schwelle** ``kappung`` = :data:`SONNE_FAKTOR` × Median der Helligkeit über dem
      Horizont. Punkte darüber sind die Sonnenscheibe.
    * **Richtung** = Schwerpunkt der Richtungen, gewichtet mit dem Licht **über** der
      Schwelle; **Farbe** = Mittel der Scheibe, auf Helligkeit 1 gebracht.
    * **Stärke**: ``e_sonne`` (Licht der Scheibe senkrecht zur Sonne), ``e_himmel_h``
      (Himmel ohne Scheibe auf einer waagrechten Fläche), ``relativ`` = Sonne auf derselben
      Fläche geteilt durch Himmel.
    * **Keine Scheibe** (bedeckt, Nebel, Studio): ``gefunden`` False; die Richtung ist dann
      der Schwerpunkt der hellsten :data:`HELLSTER_ANTEIL` — für eine weiche Lampe.

    Returns:
        ``{gefunden, richtung_bild, hoehe_grad, azimut_bild_grad, farbe, e_sonne, e_himmel_h,
        relativ, kappung, median, n_sonne, weg}`` — Richtung im Bild (vor der Drehung).
    """
    breite, hoehe = int(breite), int(hoehe)
    if breite <= 0 or hoehe <= 0 or len(pixel) < breite * hoehe * kanaele:
        raise ValueError(f"Himmelsbild {breite} x {hoehe} mit {len(pixel)} Werten passt nicht.")
    feld = (2.0 * math.pi / breite) * (math.pi / hoehe)
    punkte = []                                  # (L, rgb, richtung, raumwinkel, sin_hoehe)
    for z in range(hoehe):
        hoch = ((z + 0.5) / hoehe - 0.5) * math.pi
        if hoch <= 0.0:
            continue
        dw = math.cos(hoch) * feld
        basis = z * breite * kanaele
        for x in range(breite):
            i = basis + x * kanaele
            rgb = (float(pixel[i]), float(pixel[i + 1]), float(pixel[i + 2]))
            punkte.append((leuchtdichte(rgb), rgb, richtung_im_bild(x, z, breite, hoehe), dw,
                           math.sin(hoch)))
    if not punkte:
        raise ValueError("Himmelsbild ohne Punkte über dem Horizont.")
    median = _median([p[0] for p in punkte]) or 0.0
    kappung = SONNE_FAKTOR * median if median > 0 else max(p[0] for p in punkte)
    sonne = [p for p in punkte if p[0] > kappung] if median > 0 else []
    e_himmel_h = sum(min(p[0], kappung) * p[4] * p[3] for p in punkte)
    if sonne:
        gewicht = [(p[0] - kappung) * p[3] for p in sonne]
        summe = [sum(g * p[2][k] for g, p in zip(gewicht, sonne)) for k in range(3)]
        richtung = _einheit(summe)
        farbe_roh = [sum(p[1][k] * p[3] for p in sonne) for k in range(3)]
        hell = leuchtdichte(farbe_roh)
        farbe = [round(c / hell, 6) for c in farbe_roh] if hell > 0 else [1.0, 1.0, 1.0]
        e_sonne = sum(gewicht)
        weg = "sonnenscheibe"
    else:
        hellste = sorted(punkte, key=lambda p: p[0], reverse=True)
        hellste = hellste[:max(1, int(len(hellste) * HELLSTER_ANTEIL))]
        summe = [sum(p[0] * p[3] * p[2][k] for p in hellste) for k in range(3)]
        richtung = _einheit(summe)
        farbe_roh = [sum(p[1][k] * p[3] for p in hellste) for k in range(3)]
        hell = leuchtdichte(farbe_roh)
        farbe = [round(c / hell, 6) for c in farbe_roh] if hell > 0 else [1.0, 1.0, 1.0]
        e_sonne = 0.0
        weg = "hellster_bereich"
    if richtung is None:
        richtung = (0.0, 0.0, 1.0)
    hoehe_grad = math.degrees(math.asin(max(-1.0, min(1.0, richtung[2]))))
    azimut_grad = math.degrees(math.atan2(richtung[1], richtung[0]))
    relativ = (e_sonne * max(0.0, richtung[2]) / e_himmel_h) if e_himmel_h > 0 else None
    return {"gefunden": bool(sonne), "richtung_bild": [round(c, 6) for c in richtung],
            "hoehe_grad": round(hoehe_grad, 3), "azimut_bild_grad": round(azimut_grad, 3),
            "farbe": farbe, "e_sonne": round(e_sonne, 6), "e_himmel_h": round(e_himmel_h, 6),
            "relativ": None if relativ is None else round(relativ, 4),
            "kappung": round(kappung, 6), "median": round(median, 6),
            "n_sonne": len(sonne), "weg": weg}


def lampe_aus_himmel(analyse: dict, licht: dict, *, drehung_grad: float = 0.0,
                     staerke: float = 1.0, toenung=None) -> dict:
    """Die Lampe einer Stimmung — Richtung in der Welt, Stärke, Winkel, Farbe. Reine Rechnung.

    * ``licht['sonne']`` und eine gefundene Scheibe: **harte Sonne** aus genau ihrer Richtung,
      gedreht wie das Himmelsbild (``drehung_grad``, die Mapping-Drehung um Z: ein Punkt des
      Bilds erscheint in der Welt um ``−drehung`` gedreht). Unter
      :data:`SONNE_MIN_HOEHE_GRAD` wird sie darauf angehoben — tiefe Sonne gibt Streiflicht,
      eine Sonne von unten keines.
    * sonst (ohne Sonne bestellt, oder keine Scheibe gefunden): **weiche Lampe** aus dem
      hellsten Bereich, mindestens :data:`WEICH_MIN_HOEHE_GRAD` hoch, mit dem grossen Winkel
      ``winkel_weich_grad`` (seit auf-20261020-294, B2; bis dahin galt hier der kleine
      Sonnenwinkel, und der «weiche» Rückfall warf harte Schatten). Fehlt die Scheibe bei
      einer Stimmung mit Sonne, sagt ``grund`` es.

    Stärke = ``sonnen_staerke`` × ``e_himmel_h`` × ``staerke`` (Vielfaches der
    Himmelshelligkeit auf einer waagrechten Fläche, wie das Fülllicht mit ``staerke``
    skaliert). Farbe = Farbe der Scheibe × Tönung, auf Helligkeit 1.

    Returns:
        ``{art, richtung_welt, hoehe_grad, azimut_welt_grad, energie, winkel_grad, farbe,
        weg, grund, herkunft}``.
    """
    grund = ""
    hart = bool(licht.get("sonne")) and bool(analyse.get("gefunden"))
    if licht.get("sonne") and not analyse.get("gefunden"):
        grund = ("Keine Sonnenscheibe im Himmelsbild gefunden — weiche Lampe aus dem hellsten "
                 "Bereich statt harter Sonne.")
    richtung = _drehe_z(analyse.get("richtung_bild") or (0.0, 0.0, 1.0), -float(drehung_grad))
    mindest = SONNE_MIN_HOEHE_GRAD if hart else WEICH_MIN_HOEHE_GRAD
    hoch = math.degrees(math.asin(max(-1.0, min(1.0, richtung[2]))))
    azimut = math.degrees(math.atan2(richtung[1], richtung[0]))
    if hoch < mindest:
        hoch = mindest
        r = math.radians(hoch)
        a = math.radians(azimut)
        richtung = (math.cos(r) * math.cos(a), math.cos(r) * math.sin(a), math.sin(r))
    farbe = list(analyse.get("farbe") or (1.0, 1.0, 1.0)) if hart else [1.0, 1.0, 1.0]
    if toenung:
        farbe = [c * float(t) for c, t in zip(farbe, toenung)]
    hell = leuchtdichte(farbe)
    farbe = [round(c / hell, 6) for c in farbe] if hell > 0 else [1.0, 1.0, 1.0]
    e_himmel = float(analyse.get("e_himmel_h") or 0.0) or 1.0
    energie = float(licht.get("sonnen_staerke") or 0.0) * e_himmel * float(staerke)
    if hart:
        winkel = float(licht.get("winkel_grad") or 1.0)
    else:
        winkel = float(licht.get("winkel_weich_grad")
                       or max(float(licht.get("winkel_grad") or 0.0), WEICH_WINKEL_GRAD))
    return {"art": "sonne" if hart else "weich",
            "richtung_welt": [round(c, 6) for c in richtung],
            "hoehe_grad": round(hoch, 3), "azimut_welt_grad": round(azimut, 3),
            "energie": round(energie, 6), "winkel_grad": winkel,
            "farbe": farbe, "weg": analyse.get("weg"), "grund": grund,
            "herkunft": licht.get("herkunft_licht") or LICHT_HERKUNFT}


def euler_fuer_richtung(richtung) -> tuple[float, float, float]:
    """Die Drehung (Euler XYZ, Bogenmass) einer Blender-Sonnenlampe, die AUS ``richtung`` scheint.

    Eine Sonnenlampe strahlt entlang ihrer lokalen −Z-Achse; ihre +Z-Achse muss also zur
    Sonne zeigen. ``Rx(90° − Höhe)`` kippt +Z auf ``(0, −cos h, sin h)``, ``Rz(Azimut + 90°)``
    dreht das auf ``(cos h · cos a, cos h · sin a, sin h)``. Ohne ``mathutils`` — prüfbar ohne
    Blender (Regel 2).
    """
    x, y, z = (float(c) for c in richtung)
    n = math.sqrt(x * x + y * y + z * z)
    if n == 0:
        raise ValueError("Richtung ohne Länge.")
    hoch = math.asin(max(-1.0, min(1.0, z / n)))
    azimut = math.atan2(y, x)
    return (math.pi / 2.0 - hoch, 0.0, azimut + math.pi / 2.0)


def kamera_azimut_grad(auge, blick_auf) -> float | None:
    """Der Azimut der Richtung Haus → Kamera, waagrecht, in Grad (Blender-Welt, x gegen Uhrzeiger).

    ``auge`` ist der Standort der Kamera, ``blick_auf`` ihr Blickziel (beide wie im Bericht
    ``kamera``). ``None``, wenn beide waagrecht zusammenfallen (Blick senkrecht nach unten) —
    dann gibt es keine Seite, und die Drehung bleibt bei der Vorgabe.
    """
    try:
        dx = float(auge[0]) - float(blick_auf[0])
        dy = float(auge[1]) - float(blick_auf[1])
    except (TypeError, ValueError, IndexError):
        return None
    if math.hypot(dx, dy) < 1e-9:
        return None
    return math.degrees(math.atan2(dy, dx))


def _winkel_normal(grad: float) -> float:
    """Ein Winkel in [-180, 180)."""
    return (float(grad) + 180.0) % 360.0 - 180.0


def drehung_zur_kamera(sonne_azimut_bild_grad: float, kamera_azimut: float, *,
                       seitlich_grad: float, seite: str = "links") -> float:
    """Die Drehung des Himmelsbilds um die Hochachse, die die Sonne seitlich der Kamera stellt.

    **Anlass (auf-20261020-294, B1):** Mit Drehung 0 stand die Sonne in allen acht
    Himmelsbildern 0–40° neben der Blickachse (abend 5°) — Frontallicht, Schatten hinter dem
    Haus. Die Ursache waren die Daten (wo die Sonne im Bild zufällig steht), nicht die Lampe.

    Gelöst **relativ zur Kamera**: Die Sonne soll ``seitlich_grad`` neben der Richtung
    Haus → Kamera stehen (``kamera_azimut``, :func:`kamera_azimut_grad`), auf der ``seite``
    aus Sicht der Kamera. Von der Kamera aus gesehen liegt «links» im Gegenuhrzeigersinn
    vom Blick, also im Uhrzeigersinn von der Richtung Haus → Kamera:
    Ziel-Azimut = ``kamera_azimut ∓ seitlich`` (links −, rechts +).

    Die Mapping-Drehung des Runners stellt einen Punkt des Bilds um ``−drehung`` gedreht in
    die Welt (:func:`lampe_aus_himmel`) — also ``drehung = Bildazimut − Zielazimut``. Dreht
    das ganze Himmelsbild mit: Lampe und Fülllicht passen zusammen.

    Returns:
        Die Drehung in Grad, in [0, 360).
    """
    if seite not in SONNE_SEITEN:
        raise ValueError(f"Seite {seite!r} — erlaubt: {', '.join(SONNE_SEITEN)}.")
    vorzeichen = -1.0 if seite == "links" else 1.0
    ziel = float(kamera_azimut) + vorzeichen * float(seitlich_grad)
    # Erst runden, dann in den Kreis legen: ein Wert knapp unter 360 runde sonst auf genau 360.0.
    return round((float(sonne_azimut_bild_grad) - ziel) % 360.0, 6) % 360.0


def winkel_zur_blickachse(sonne_azimut_welt_grad: float, kamera_azimut: float) -> float:
    """Wie weit die Sonne waagrecht neben der Richtung Haus → Kamera steht, 0–180°.

    0° = Sonne im Rücken der Kamera (Frontallicht), 90° = von der Seite, 180° = Gegenlicht.
    Die Zahl, die 294 nachgezählt hat (dort 0–40°), steht seither im Bericht.
    """
    return round(abs(_winkel_normal(float(sonne_azimut_welt_grad) - float(kamera_azimut))), 3)


def hintergrund_mit_abstand(horizont, zenit, haus: float, *,
                            abstand_ev: float = HINTERGRUND_ABSTAND_EV,
                            richtung: str = "auto") -> dict:
    """Der Faktor, um den der ruhige Hintergrund heller oder dunkler wird — Farbton bleibt.

    **Anlass (auf-20261020-293, Punkt 1):** Das Haus verschwand im Hintergrund (winter −0,5,
    morgen −1,3 Grauwerte), weil der Verlauf in den Medianfarben des Himmels genau so hell
    war wie das diffus beleuchtete Haus. Stärke und Belichtung halfen nicht — sie skalieren
    beide gleich.

    ``horizont``/``zenit`` sind die zwei Farben des Verlaufs, so wie die Kamera sie sieht
    (linear, mit Tönung und Stärke), ``haus`` die mittlere Helligkeit des Hauses im selben
    Mass (die Vorprobe des Runners misst sie). Der Verlauf wird als Ganzes mit einem Faktor
    multipliziert — der Farbton des Himmels bleibt:

    * ``dunkler``: sein **hellstes** Ende höchstens ``haus × 2^−abstand``.
    * ``heller``: sein **dunkelstes** Ende mindestens ``haus × 2^abstand``.
    * ``auto``: die Seite, auf der der Verlauf schon liegt (geometrisches Mittel der Enden).

    **Mindestens, nicht genau:** Liegt der Hintergrund schon weiter weg, bleibt er (Faktor 1)
    — er auf den Abstand zurückgeholt nähme Kontrast weg. Faktor zwischen 1/64 und 64.

    Returns:
        ``{faktor, richtung, abstand_ev, abstand_ev_vorher, abstand_ev_nachher, haus,
        horizont, zenit, grund}``.
    """
    lh, lz = leuchtdichte(horizont), leuchtdichte(zenit)
    haus = float(haus)
    if richtung not in HINTERGRUND_RICHTUNGEN:
        raise ValueError(f"Richtung {richtung!r} — erlaubt: {', '.join(HINTERGRUND_RICHTUNGEN)}.")
    if not (haus > 0.0) or lh <= 0.0 or lz <= 0.0:
        return {"faktor": 1.0, "richtung": richtung, "abstand_ev": float(abstand_ev),
                "abstand_ev_vorher": None, "abstand_ev_nachher": None, "haus": haus,
                "horizont": list(horizont), "zenit": list(zenit),
                "grund": "Haus oder Hintergrund ohne Helligkeit — nichts nachgestellt."}
    mittel = math.sqrt(lh * lz)
    if richtung == "auto":
        richtung = "heller" if mittel >= haus else "dunkler"
    if richtung == "dunkler":
        ziel = haus * 2.0 ** (-float(abstand_ev))
        faktor = min(1.0, ziel / max(lh, lz))
    else:
        ziel = haus * 2.0 ** float(abstand_ev)
        faktor = max(1.0, ziel / min(lh, lz))
    faktor = max(1.0 / 64.0, min(64.0, faktor))
    return {"faktor": round(faktor, 6), "richtung": richtung, "abstand_ev": float(abstand_ev),
            "abstand_ev_vorher": round(math.log2(mittel / haus), 3),
            "abstand_ev_nachher": round(math.log2(mittel * faktor / haus), 3),
            "haus": round(haus, 6),
            "horizont": [round(float(c) * faktor, 6) for c in horizont],
            "zenit": [round(float(c) * faktor, 6) for c in zenit], "grund": ""}


#: **Der sichtbare Himmel passt zur Stimmung (Ergebnis auf-20261022-333, Protokoll 74 §242).**
#:
#: :func:`hintergrund_mit_abstand` ist für den ruhigen **Verlauf** gebaut (Messungen 293/295):
#: Dort ist der Hintergrund eine erfundene Fläche, und nur ihr Abstand zum Haus zählt. Seit
#: Entscheid 126 sieht die Kamera aber das **Himmelsbild** der Stimmung (``himmel_sichtbar``,
#: Vorgabe für Varianten), und dieselbe Regel stellte das echte Himmelsbild bis zu sechs
#: Blenden dunkler. In 331 lag der Faktor bei «abend» bei 0,26 (Stärke 0,30 → 0,079, −1,9 EV
#: gegen den Start), der Himmel war fast schwarz; in 333 war der Mittagshimmel schon im
#: Cycles-Bild dunkles Nachtblau. Ein Himmel, der nicht zur Stimmung passt, widerspricht dem
#: Prompt («clear sky»), und der KI-Schritt hält ihn mit «Umriss halten» fest.
#:
#: **Die Grenze, zwei Fälle:**
#:
#: * **Dämmrige Stimmungen** (morgen, abend, blaue Stunde, weiss, unbekannt): höchstens
#:   :data:`HIMMEL_FAKTOR_MIN` = 0,5, also **eine Blende** dunkler als die Stimmung den Himmel
#:   setzt. Eine Blende ist dieselbe Grösse wie der Abstand der Regel selbst
#:   (:data:`HINTERGRUND_ABSTAND_EV`): Die Regel darf den Himmel so weit verschieben, wie sie
#:   ihn vom Haus wegrücken will, aber nicht weiter. In 309 lag «abend» bei 0,72 (Kontrast
#:   41–64), in 314 bei 0,31 mit Kontrast 62,9 — der Spielraum über der Schwelle 20 ist gross.
#: * **Helle Stimmungen** (:data:`HELLE_HIMMEL`: mittag, bedeckt, nebel, winter): nie unter
#:   die **Stärke der Stimmung** (``intensitaet``, sonst :func:`vorgabe_staerke`). Der Himmel
#:   startet heute bei ``staerke × fuell_staerke`` (mittag 0,45): ``fuell_staerke`` nimmt
#:   Fülllicht vom Haus, weil die Sonnenlampe übernimmt — es war nie gemeint, den Himmel zu
#:   dimmen, den die Kamera sieht; beim Verlauf fiel das nicht auf. Mit der Stärke der
#:   Stimmung steht der Himmel so hell, wie er fotografiert ist, gegenüber einer Sonne, die
#:   als Vielfaches eben dieses Himmels gesetzt ist.
#:
#: Gesetzt, nicht gemessen: ``auf-20261022-334`` misst Himmelshelligkeit und
#: ``qa.kontrast_haus_hintergrund`` je Stimmung; die Prüfung am Bild bleibt, wie sie ist.
HIMMEL_FAKTOR_MIN = 0.5
HELLE_HIMMEL = ("mittag", "bedeckt", "nebel", "winter")


def himmel_untergrenze(preset) -> dict:
    """Die Untergrenze eines **sichtbaren** Himmelsbilds für diese Stimmung — reine Rechnung.

    ``{"art": "staerke"}`` bei einer hellen Stimmung (:data:`HELLE_HIMMEL`): nie unter die
    Stärke der Stimmung. Sonst ``{"art": "faktor", "faktor": 0.5}``: höchstens eine Blende
    dunkler. Geht in den Lichtdaten an Blender (nur mit ``himmel_sichtbar``).
    """
    if preset in HELLE_HIMMEL:
        return {"art": "staerke"}
    return {"art": "faktor", "faktor": HIMMEL_FAKTOR_MIN}


def himmel_begrenzen(abstand: dict, untergrenze: dict | None, *, staerke_vorher: float,
                     staerke_stimmung: float) -> dict:
    """Den Faktor aus :func:`hintergrund_mit_abstand` für ein sichtbares Himmelsbild begrenzen.

    ``abstand`` ist das Ergebnis der Regel, ``staerke_vorher`` die Stärke, mit der der Himmel
    vor der Regel steht (``staerke × fuell_staerke``), ``staerke_stimmung`` die Stärke der
    Stimmung (bestellte ``intensitaet`` oder die Vorgabe). Der Faktor wird **nie kleiner** als
    die Untergrenze; grösser darf er bleiben (die Regel «heller» bei bedeckt). Ohne
    Untergrenze bleibt alles, wie es ist.

    Returns:
        ``abstand`` mit neuem ``faktor``, ``abstand_ev_nachher``, ``horizont``, ``zenit`` und
        dazu ``faktor_regel`` (was die Regel wollte), ``himmel_grenze`` (``{art, faktor_min,
        begrenzt}``).
    """
    if not untergrenze:
        return dict(abstand)
    faktor_regel = float(abstand.get("faktor") or 1.0)
    if untergrenze.get("art") == "staerke" and float(staerke_vorher) > 0.0:
        faktor_min = max(HIMMEL_FAKTOR_MIN, float(staerke_stimmung) / float(staerke_vorher))
    else:
        faktor_min = float(untergrenze.get("faktor") or HIMMEL_FAKTOR_MIN)
    faktor = max(faktor_regel, faktor_min)
    aus = dict(abstand, faktor=round(faktor, 6), faktor_regel=faktor_regel,
               himmel_grenze={"art": untergrenze.get("art"), "faktor_min": round(faktor_min, 6),
                              "begrenzt": faktor > faktor_regel})
    if faktor != faktor_regel and faktor_regel > 0.0:
        anteil = faktor / faktor_regel
        for ende in ("horizont", "zenit"):
            if abstand.get(ende) is not None:
                aus[ende] = [round(float(c) * anteil, 6) for c in abstand[ende]]
        if abstand.get("abstand_ev_nachher") is not None:
            aus["abstand_ev_nachher"] = round(float(abstand["abstand_ev_nachher"])
                                              + math.log2(anteil), 3)
    return aus


#: **Boden bis zum Horizont (Ergebnis auf-20261022-334, Protokoll 74).**
#:
#: Mit sichtbarem Himmel sieht die Kamera das Himmelsbild in **jede** Richtung — auch unter
#: den Horizont. Die Himmelsbilder der Stimmungen sind «puresky»-Aufnahmen: unten ist keine
#: Erde, sondern die gespiegelte oder graue untere Hälfte. Wo die Geländeplatte endet, stand
#: darum unter dem Horizont blauer bzw. grauer «Himmel» — kein Boden bis zum Horizont.
#:
#: **Die Lösung liegt im Welt-Shader, nur für Kamerastrahlen:** Blickrichtungen unter dem
#: Horizont bekommen eine Bodenfarbe — das Grau der Geländeplatte (``gelaende_grau``, die
#: Albedo), beleuchtet vom mittleren Himmel (``(horizont + zenit) / 2``, getönt wie der
#: Himmel). Eine matte Fläche unter einem gleichmässigen Himmel strahlt Albedo × Himmel ab;
#: die Sonne fehlt dabei bewusst (der ferne Boden steht ruhig, nicht gleissend). Die letzten
#: :data:`BODEN_DUNST_GRAD` Grad unter dem Horizont gehen weich in die Horizontfarbe über —
#: Dunst statt einer harten Kante. **Seit 336 (Ergebnis 335) ist der Boden so hell und so
#: gefärbt wie die Platte unter Sonne und Himmel** — :data:`BODEN_FASSUNG`.
#:
#: **Warum nicht die Platte verlängern:** Eine grössere Platte änderte Szenenbox, Rahmung,
#: Tiefe, ID-Pass, Bauwerksmaske und Schatten. Der Welt-Shader ändert nur, was die Kamera
#: dort sieht, wo kein Objekt steht: Licht und Spiegelungen kommen weiter aus dem Himmelsbild
#: (alle anderen Strahlen), Tiefe und ID-Pass bleiben (der ID-Pass baut seine Welt schwarz).
#: Gesetzt, nicht gemessen — ``auf-20261022-335`` prüft es am Heim-PC.
BODEN_DUNST_GRAD = 6.0


#: **Fassung des Bodens (Ergebnis auf-20261022-335, Protokoll 74).** Reist als Lichtdatum
#: mit (``boden_fassung``), damit ein Bild mit dem Boden von 335 weder Grundlage noch
#: Zwischenspeicher-Treffer ist.
#:
#: **Anlass:** Der Boden von 334 war Albedo × mittlerer Himmel — nur das Fülllicht, mit der
#: Farbe des Himmels, und mit der Stärke des sichtbaren Himmels gestellt. Am Heim-PC war er
#: darum ein ebenes dunkles Blaugrau (mittag RGB 34/48/62), das sich wie Wasser las; die
#: Platte daneben (Grau 113 mittag, 101 abend) stand mit einer Naht von −31,5 bzw. −74,4
#: Grauwerten darauf, und der dunkle Boden neben dem Haus zog den Mittag-Kontrast von −27,7
#: auf −13,9 (Warnung «HAUS KAUM SICHTBAR»).
#:
#: **Seither** ist der Boden die Platte in der Ferne: dieselbe Albedo, dasselbe Licht —
#: Fülllicht (Himmel ohne Sonnenscheibe, ``e_himmel_h``) **und** Sonne (``energie × sin(Höhe)``,
#: Farbe der Lampe). Eine matte Fläche strahlt Albedo × Beleuchtung / π ab; das ist genau, was
#: Cycles auf der Platte rechnet, ohne Schatten. Gestellt wird die Farbe so, dass sie mit der
#: Stärke des Fülllichts (``staerke × fuell_staerke``, die Stärke des Kamerastrahls vor der
#: Vorprobe) die Leuchtdichte der Platte ergibt; was die Vorprobe danach tut, regelt
#: :func:`boden_zum_faktor`.
#:
#: **Seit 338 (Ergebnis 336): ``"platte-338"``** — die Bodenfarbe hat zwei Enden,
#: :data:`BODEN_FERN_GRAD`. Die Fassung reist neu, damit ein Abendbild mit dem Boden von 336
#: weder Grundlage noch Zwischenspeicher-Treffer ist (mittags sind die Pixel gleich, die
#: Grundlage wird trotzdem neu gerechnet — ein Lauf, kein Fehler).
BODEN_FASSUNG = "platte-338"


#: **Der ferne Boden auf Plattenhöhe, der nahe dämmrig (Ergebnis auf-20261022-336,
#: Protokoll 74).** Bis zu so vielen Grad unter dem Horizont geht die Bodenfarbe vom nahen
#: Boden (:func:`boden_zum_faktor`) linear (im Sinus der Blickhöhe) zum fernen Boden
#: (:func:`boden_fern_zum_faktor`) über; darunter steht der nahe Boden, wie in 336.
#:
#: **Anlass:** Abends (Faktor der Vorprobe 0,5) stand der ganze Boden eine Blende unter der
#: Platte. An der Plattenunterkante blieb darum eine Naht von −57,8 Grauwerten (Grenze 45).
#: Die Unterkante liegt bei der sSE-Kamera rund 3,8° unter dem Horizont — mitten im Dunstband:
#: Von 335 auf 336 stieg der Boden dort um 16,6 Grauwerte, das Dunstband im Mittel um 15,5,
#: der tiefe Boden um 28,5.
#:
#: **Warum ein Verlauf und nicht einfach ein hellerer Boden** (gerechnet mit der Tonwertkurve
#: aus 335/336, Probe ``tests/test_boden_naht_abend_auf336.py``): Jeder hellere Weltpunkt im
#: Rahmen um das Haus kostet Abend-Kontrast. Der ganze Boden ½ Blende heller hebt die Kante nur
#: um 11–15 (Naht −47 bis −43, nicht sicher unter 45) und kostet 5–8 Kontrast (27,9 → 20–23).
#: Der Verlauf hebt dort, wo die Kante liegt, und lässt den Vordergrund dämmrig: Kante +18–25
#: (Naht −40 bis −33), Kontrast 27,9 → 23–25 (schlimmster Fall 21,4). Am Horizont selbst bleibt
#: der Dunst (die Horizontfarbe), unverändert. Mittags (Faktor > 1) sind beide Enden gleich —
#: kein Pixel ändert sich.
BODEN_FERN_GRAD = 12.0


def _chroma(rgb):
    """Ein Farbton auf Helligkeit 1 (Rec. 709) — ``None`` bei Schwarz."""
    hell = leuchtdichte(rgb)
    return [float(c) / hell for c in rgb] if hell > 0 else None


def boden_bis_horizont(horizont, zenit, albedo=None, toenung=None, *, lampe=None,
                       e_himmel_h=None, staerke=None, fuell_staerke=None) -> dict:
    """Die Bodenfarbe unter dem Horizont eines sichtbaren Himmels — reine Rechnung, linear.

    **Mit Licht** (``lampe`` aus :func:`lampe_aus_himmel`, ``e_himmel_h`` aus
    :func:`sonne_aus_himmel`, ``staerke`` und ``fuell_staerke`` der Stimmung; seit
    :data:`BODEN_FASSUNG`): der Boden ist die Platte in der Ferne —

    ``boden = albedo / π × (E_füll + E_sonne) / (staerke × fuell_staerke)``

    mit ``E_füll = e_himmel_h × staerke × fuell_staerke × Farbton(Himmelsmittel) × Tönung``
    (so färbt die Welt das Fülllicht) und ``E_sonne = energie × sin(Höhe) × Farbe der Lampe``.
    Mit der Stärke des Kamerastrahls vor der Vorprobe (``staerke × fuell_staerke``)
    multipliziert, ist das die Leuchtdichte der unbeschatteten Platte. Mittags überwiegt die
    Sonne (Boden fast neutral, wie die Platte, Grau 113), abends das warme Fülllicht.

    **Ohne Licht** (Rückfall, und Wort für Wort wie 334): Albedo × mittlerer Himmel × Tönung.

    Args:
        horizont, zenit: die Himmelsfarben (``hintergrund_aus_himmel``), ungetönt.
        albedo: das Grau der Platte (``gelaende_grau``), sonst :data:`GELAENDE_GRAU`.
        toenung: die Tönung der Stimmung (wie beim Himmel), sonst keine.

    Returns:
        ``{boden, dunst, albedo, dunst_grad, weg, fassung?, anteil_sonne?, fern_grad?}`` —
        ``fern_grad`` (nur ``weg="platte"``, seit 338) der Verlauf zum fernen Boden; ``boden`` die
        Farbe tief unten, ``dunst`` die Farbe direkt unter dem Horizont (die getönte
        Horizontfarbe), beide RGB linear, vor der Stärke des Hintergrunds; ``weg``
        ``"platte"`` (mit Licht) oder ``"himmel"`` (Rückfall).
    """
    tf = [float(t) for t in (toenung or (1.0, 1.0, 1.0))]
    al = [float(a) for a in (albedo or GELAENDE_GRAU)]
    himmel = [0.5 * (float(h) + float(z)) for h, z in zip(horizont, zenit)]
    dunst = [round(float(h) * t, 6) for h, t in zip(horizont, tf)]
    aus = {"dunst": dunst, "albedo": al, "dunst_grad": BODEN_DUNST_GRAD}
    try:
        k_fuell = float(staerke) * float(fuell_staerke)
        e_h = float(e_himmel_h)
        ton = _chroma(himmel)
        energie = float(lampe["energie"])
        sin_h = max(0.0, math.sin(math.radians(float(lampe["hoehe_grad"]))))
        farbe = [float(c) for c in lampe["farbe"]]
    except (TypeError, KeyError, ValueError):
        k_fuell, e_h, ton = 0.0, 0.0, None
    if k_fuell > 0.0 and e_h > 0.0 and ton is not None:
        fuell = [e_h * c * t for c, t in zip(ton, tf)]
        sonne = [energie * sin_h / k_fuell * c for c in farbe]
        boden = [round(a / math.pi * (f + s), 6) for a, f, s in zip(al, fuell, sonne)]
        anteil = leuchtdichte(sonne) / max(leuchtdichte(sonne) + leuchtdichte(fuell), 1e-12)
        return dict(aus, boden=boden, weg="platte", fassung=BODEN_FASSUNG,
                    anteil_sonne=round(anteil, 4), fern_grad=BODEN_FERN_GRAD)
    boden = [round(a * h * t, 6) for a, h, t in zip(al, himmel, tf)]
    return dict(aus, boden=boden, weg="himmel")


def boden_zum_faktor(boden, faktor) -> list:
    """Die Bodenfarbe nach der Vorprobe — reine Rechnung (Ergebnis auf-20261022-335).

    Die Vorprobe stellt die Stärke des Kamerastrahls mit ``faktor`` — Himmel und Boden
    zugleich, denn beide hängen am selben Knoten. Für den Boden gilt: **höchstens so hell wie
    die Platte.**

    * ``faktor > 1`` (mittag 2,22: die Untergrenze hält den sichtbaren Himmel so hell wie die
      Stimmung) — das betrifft das Aussehen des Himmels, nicht das Licht auf dem Boden. Der
      Boden wird durch ``faktor`` geteilt und bleibt bei der Platte; ohne das stünde er
      +1,2 Blenden über ihr, eine neue Naht.
    * ``faktor ≤ 1`` (abend 0,5: die Vorprobe dunkelt den Hintergrund ab, damit sich das Haus
      abhebt) — der ferne Boden ist Hintergrund und dunkelt mit: abends bleibt er dämmrig,
      eine Blende unter der Platte. Mit dem Boden auf Plattenhöhe fiele der Abend-Kontrast
      nach den Messwerten aus 335 von 35,7 auf rund 14 (Protokoll 74).
      Seit 338 gilt das für den **nahen** Boden; zum Horizont hin geht er in den fernen
      über (:func:`boden_fern_zum_faktor`, :data:`BODEN_FERN_GRAD`).

    Returns:
        die neue Farbe (RGB linear), die mit der neuen Stärke multipliziert wird.
    """
    f = float(faktor or 1.0)
    teiler = f if f > 1.0 else 1.0
    return [round(float(c) / teiler, 6) for c in boden]


def boden_fern_zum_faktor(boden, faktor) -> list:
    """Die Farbe des **fernen** Bodens nach der Vorprobe — reine Rechnung (Ergebnis 336).

    Immer auf Plattenhöhe: ``boden / faktor``, mit der neuen Stärke multipliziert also genau
    die Leuchtdichte der Platte. Bei ``faktor > 1`` (mittag) ist das dieselbe Farbe wie
    :func:`boden_zum_faktor` — der Verlauf (:data:`BODEN_FERN_GRAD`) mischt dann zweimal
    dieselbe Farbe, kein Pixel ändert sich. Bei ``faktor < 1`` (abend 0,5) ist der ferne Boden
    heller als der nahe: zum Horizont hin so hell wie die Platte, an deren Kante, im
    Vordergrund dämmrig. Ohne oder mit unbrauchbarem Faktor: die Farbe unverändert.

    Returns:
        die neue Farbe (RGB linear), die mit der neuen Stärke multipliziert wird.
    """
    try:
        f = float(faktor or 1.0)
    except (TypeError, ValueError):
        f = 1.0
    if not f > 0.0 or math.isinf(f):
        f = 1.0
    return [round(float(c) / f, 6) for c in boden]


#: Wie die Vorprobe das Haus misst (auf-20261020-295, N1): ``"stufen"`` — das Mittel in
#: Blendenstufen (geometrisches Mittel der Helligkeit), ``"linear"`` — das Mittel der
#: Helligkeit selbst (293 bis 295).
#:
#: **Anlass:** Bei «abend» mass die Vorprobe den Hintergrund 1,9 Stufen unter dem Haus und
#: liess ihn stehen; im Bild hob sich das Haus aber nur um +18 Grauwerte ab (Schwelle 20).
#: Die Kamera sah zu drei Vierteln die Schattenseite (Grauwert 98) und zu einem Viertel die
#: Sonnenseite (230). **Das lineare Mittel gehört der Sonnenseite** — sie ist dort rund
#: zwanzigmal heller und zieht den Wert hoch —, das Mittel der Grauwerte, das
#: ``qa.kontrast_haus_hintergrund`` bildet, gehört der Schattenseite. Grauwerte nach der
#: Tonwertkurve (AgX) wachsen ungefähr mit den Blendenstufen, nicht mit dem Licht: Das
#: Mittel in Stufen ist darum, was die Messung am Bild sieht. Seither misst die Vorprobe
#: dieselbe Grösse wie die Prüfung — sonst stimmen Steuerung und Messung nie überein.
#: Bei einem gleichmässig hellen Haus sind beide Mittel gleich.
HAUS_MASS = "stufen"
HAUS_MASSE = ("stufen", "linear")
#: Untergrenze der Helligkeit eines Hauspunkts im Mittel in Stufen — ein schwarzer Punkt
#: (Helligkeit 0) hätte sonst unendlich viele Stufen Abstand.
STUFEN_UNTERGRENZE = 1.0e-6


def haus_leuchtdichte(pixel, *, kanaele: int = 4, deckend_ab: float = 0.99,
                      mass: str = HAUS_MASS) -> dict:
    """Die mittlere Helligkeit des Hauses in der Vorprobe des Runners — reine Rechnung.

    Die Vorprobe rechnet ein kleines Bild mit durchsichtigem Hintergrund und ohne Gelände
    vor der Kamera: Deckend (Alpha ab ``deckend_ab``) ist dort nur das Haus. Gemittelt wird
    die Rec.-709-Helligkeit über diese Punkte, linear (vor Tonwertkurve und Belichtung — die
    verschieben Haus und Hintergrund gleich) — **seit auf-20261020-295 in Blendenstufen**
    (``mass`` ``"stufen"``, :data:`HAUS_MASS`), damit die Vorprobe dieselbe Grösse misst wie
    ``qa.kontrast_haus_hintergrund`` am fertigen Bild.

    Returns:
        ``{leuchtdichte, linear, stufen, mass, n, n_bild}`` — ``leuchtdichte`` ist der Wert
        nach ``mass``; ``linear`` und ``stufen`` stehen beide daneben, damit der Bericht
        zeigt, wie weit sie auseinanderliegen. ``None`` ohne deckenden Punkt.
    """
    if kanaele < 4:
        raise ValueError("Die Vorprobe braucht einen Alphakanal (RGBA).")
    if mass not in HAUS_MASSE:
        raise ValueError(f"Mass {mass!r} — erlaubt: {', '.join(HAUS_MASSE)}.")
    n_bild = len(pixel) // kanaele
    summe, summe_log, n = 0.0, 0.0, 0
    for i in range(n_bild):
        j = i * kanaele
        if float(pixel[j + 3]) >= deckend_ab:
            hell = leuchtdichte((pixel[j], pixel[j + 1], pixel[j + 2]))
            summe += hell
            summe_log += math.log2(max(hell, STUFEN_UNTERGRENZE))
            n += 1
    linear = (summe / n) if n else None
    stufen = (2.0 ** (summe_log / n)) if n else None
    return {"leuchtdichte": stufen if mass == "stufen" else linear,
            "linear": linear, "stufen": stufen, "mass": mass, "n": n, "n_bild": n_bild}


def aufloesung_fuer(guete) -> str:
    """``'2k'`` bei ``guete: 'vorschau'`` (Entscheid 104), sonst ``'4k'``."""
    return "2k" if guete == "vorschau" else "4k"


def dateiname(preset: str, hdri: str, aufloesung: str) -> str:
    """``<preset>__<hdri>_<2k|4k>.hdr`` — die Ablageform der HomeStation."""
    return f"{preset}__{hdri}_{aufloesung}.hdr"


def himmel_ordner(umgebung=None) -> Path | None:
    """Der Ordner aus :data:`HIMMEL_ORDNER_ENV` — ``None``, wenn nicht eingestellt."""
    wert = (umgebung if umgebung is not None else os.environ).get(HIMMEL_ORDNER_ENV)
    return Path(wert) if wert else None


def himmel_datei(preset: str, hdri: str, *, guete=None, ordner=None) -> dict:
    """Das Himmelsbild am Rechner — ``{pfad, datei, aufloesung, satz}``.

    ``pfad`` ist ``None``, wenn es fehlt; ``satz`` sagt dann mit dem Namen, was fehlt
    (Entscheid 113: abweisen mit Satz, und derselbe Satz steht im Ergebnis unter
    ``lieferstatus_grund``). Der Satz nennt **keinen Pfad** — er geht bis in die Oberfläche.
    """
    aufl = aufloesung_fuer(guete)
    name = dateiname(preset, hdri, aufl)
    wurzel = Path(ordner) if ordner is not None else himmel_ordner()
    if wurzel is None:
        return {"pfad": None, "datei": name, "aufloesung": aufl,
                "satz": (f"Himmelsbild '{hdri}' ({aufl}) fehlt am Rechner: Der Ordner der "
                         f"Himmelsbilder ist nicht eingestellt ({HIMMEL_ORDNER_ENV}).")}
    pfad = wurzel / name
    if not pfad.is_file():
        return {"pfad": None, "datei": name, "aufloesung": aufl,
                "satz": f"Himmelsbild '{hdri}' ({aufl}) fehlt am Rechner."}
    return {"pfad": pfad, "datei": name, "aufloesung": aufl, "satz": None}


def himmelsbilder_stand(ordner=None) -> dict:
    """Wie viele der acht Vorgabe-Himmelsbilder liegen da — ``{da, von, fehlend, satz}``.

    Gezählt wird je Stimmung ihr Vorgabebild in beiden Grössen (2k für die Vorschau, 4k für
    das volle Bild); eine Stimmung zählt, wenn beide da sind. Für die Zeile «Himmelsbilder
    n/8» im Einrichten (``heimstand``). Ohne Pfad im Satz (Regel 3).
    """
    wurzel = Path(ordner) if ordner is not None else himmel_ordner()
    fehlend = []
    for preset, eintrag in STIMMUNGEN.items():
        ok = wurzel is not None and all(
            (wurzel / dateiname(preset, eintrag["hdri"], a)).is_file() for a in ("2k", "4k"))
        if not ok:
            fehlend.append(preset)
    da = len(PRESETS) - len(fehlend)
    if wurzel is None:
        satz = f"Himmelsbilder 0/{len(PRESETS)} — {HIMMEL_ORDNER_ENV} ist nicht eingestellt."
    elif fehlend:
        satz = f"Himmelsbilder {da}/{len(PRESETS)} — es fehlen: {', '.join(fehlend)}."
    else:
        satz = f"Himmelsbilder {da}/{len(PRESETS)}."
    return {"da": da, "von": len(PRESETS), "fehlend": fehlend, "satz": satz}


def ohne_stimmungssaetze(prompt_en: str) -> tuple[str, tuple[str, ...]]:
    """``(rest, presets)`` — der Prompt ohne die englischen Sätze der Stimmungen.

    **Anlass (auf-20261021-306, B2):** Der Stimmungs-Knoten legt seinen Satz selbst in den
    Prompt. Kam er halb übersetzt an, galt die Stimmung über ein ``merkmal`` als «schon im
    Prompt», und der Satz des Heim-PC fehlte — «abend» zeigte einen Innenraum. Ist eine Stimmung
    bestellt, ist der Satz des Heim-PC massgebend: Die Sätze der Tabelle (wie das Glossar sie
    aus dem deutschen Satz des Knotens macht) werden herausgenommen, und
    :func:`kosmo_szene.lies_szene` fügt den der bestellten Stimmung einmal an. Was der Besteller
    sonst schreibt, bleibt Wort für Wort.
    """
    rest, raus = prompt_en or "", []
    for preset, eintrag in STIMMUNGEN.items():
        satz = eintrag.get("prompt_en")
        if not satz:
            continue
        muster = re.compile(r"(?:^|,)\s*" + r"\s+".join(re.escape(t) for t in satz.split())
                            + r"\s*(?=,|$)", re.IGNORECASE)
        neu = muster.sub("", rest)
        if neu != rest:
            raus.append(preset)
            rest = neu
    rest = re.sub(r"^\s*,\s*", "", rest).strip()
    return rest, tuple(raus)


def ohne_teile_des_satzes(prompt_en: str, satz: str) -> tuple[str, tuple[str, ...]]:
    """``(rest, doppelt)`` — der Prompt ohne die Teile, die wörtlich Teile von ``satz`` sind.

    **Anlass (Ergebnis auf-20261022-342, g):** Der Mac schickt «Abendstimmung», das Glossar
    macht daraus «evening mood», und :func:`kosmo_szene.lies_szene` fügt den Satz der Stimmung
    an, der selbst mit «evening mood» beginnt — im gerechneten Prompt stand es zweimal.
    :func:`ohne_stimmungssaetze` nimmt nur GANZE Sätze heraus. Hier fällt jeder durch Komma
    getrennte Teil des Prompts weg, der (ohne Gross/Klein) genau ein Teil des Satzes ist —
    «evening mood», nicht aber «warm light» (der Satz sagt «warm low sunlight»).
    """
    teile_satz = {t.strip().lower() for t in (satz or "").split(",") if t.strip()}
    bleiben, doppelt = [], []
    for teil in (prompt_en or "").split(","):
        if teil.strip() and teil.strip().lower() in teile_satz:
            doppelt.append(teil.strip())
        else:
            bleiben.append(teil)
    if not doppelt:
        return prompt_en or "", ()
    rest = ",".join(bleiben)
    rest = re.sub(r"^\s*,\s*", "", rest).strip().strip(",").strip()
    rest = re.sub(r"\s*,\s*,\s*", ", ", rest)
    return rest, tuple(doppelt)


#: Die STIMMUNGSWÖRTER je Stimmung (Befund auf-20261022-340, 22.10.2026) — woran eine
#: Variante ihre Stimmung zeigt, wenn der Prompt nicht den ganzen Satz der Tabelle trägt
#: («Abendstimmung» allein, «evening mood»). Englisch, wie das Glossar
#: (:mod:`aiimaging.sprache`) den deutschen Prompt übersetzt; deutsch als Rückhalt für Wörter,
#: die das Glossar nicht kennt («abends», «verschneit»). Gesucht wird nach ganzen Wörtern
#: (``\b``): «afternoon» ist nicht «noon», «Nachmittag» nicht «Mittag». Das Gipsmodell
#: («weiss») fehlt mit Absicht: Es ist keine Lichtstimmung und wird nie aus einem Wort erraten.
#: Getrennt von ``merkmale``: Die entscheiden, ob der Satz des Heim-PC angefügt wird, und
#: bleiben, wie sie sind.
STIMMUNGSWOERTER = {
    "morgen": {"en": ("morning", "sunrise", "dawn"),
               "de": (r"morgen\w*", r"sonnenaufgang\w*")},
    "mittag": {"en": ("midday", "noon", "noonday"),
               "de": (r"mittag\w*",)},
    "abend": {"en": ("evening", "sunset", "golden hour"),
              "de": (r"abend\w*", r"sonnenuntergang\w*", r"goldene\s+stunde")},
    "blaue-stunde": {"en": ("blue hour", "twilight", "dusk"),
                     "de": (r"blaue\w*\s+stunde", r"d(?:ä|ae)mmerung\w*")},
    "bedeckt": {"en": ("overcast", "cloudy"),
                "de": (r"bedeckt\w*", r"bew(?:ö|oe)lkt\w*")},
    "nebel": {"en": ("fog", "foggy", "mist", "misty", "haze", "hazy"),
              "de": (r"nebel\w*", r"neblig\w*", r"dunst\w*")},
    "winter": {"en": ("winter", "wintry", "snow", "snowy"),
               "de": (r"winter\w*", r"schnee\w*", r"verschneit\w*")},
}


def stimmungen_im_text(prompt_en: str, prompt_original: str | None = None) -> tuple[str, ...]:
    """Die Stimmungen, deren WORT im Prompt steht — in der Reihenfolge der Tabelle.

    Gelesen werden der übersetzte Prompt (englische Wörter) und, wenn gegeben, das Original
    (deutsche Wörter). Leer, wenn kein Stimmungswort vorkommt. Mehr als eine Stimmung heisst:
    nicht eindeutig — :func:`aiimaging.kosmo_szene.stimmung_der_variante` rät dann nicht.
    """
    en = (prompt_en or "").lower()
    de = (prompt_original or "").lower()
    gefunden = []
    for preset, woerter in STIMMUNGSWOERTER.items():
        treffer = any(re.search(r"\b" + r"\s+".join(map(re.escape, w.split())) + r"\b", en)
                      for w in woerter["en"])
        if not treffer and de:
            treffer = any(re.search(r"\b" + m + r"\b", de) for m in woerter["de"])
        if treffer:
            gefunden.append(preset)
    return tuple(gefunden)


def prompt_satz(preset: str, prompt_en: str) -> tuple[str | None, bool]:
    """``(satz, schon_da)`` — der englische Satz der Stimmung, wenn ihn der Prompt nicht trägt.

    Der Knoten drüben legt den Satz der Stimmung selbst in den Prompt; ein zweites Mal
    angefügt stünde er doppelt da. Angefügt wird darum nur, wenn keines der ``merkmale`` im
    (übersetzten) Prompt vorkommt — etwa bei einer Bestellung über ``vis_render`` ohne Knoten.
    """
    eintrag = STIMMUNGEN[preset]
    text = (prompt_en or "").lower()
    if any(m in text for m in eintrag["merkmale"]):
        return None, True
    return eintrag["prompt_en"], False
