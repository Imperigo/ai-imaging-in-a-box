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
           "HAUS_MASS", "HAUS_MASSE", "STUFEN_UNTERGRENZE"]

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
        "label": "Weissmodell", "hdri": "studio_small_08",
        "hdri_vorher": "mud_road_puresky",
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
