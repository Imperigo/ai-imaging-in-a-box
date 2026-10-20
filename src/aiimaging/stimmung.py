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

import os
import re
from pathlib import Path

__all__ = ["HIMMEL_ORDNER_ENV", "PRESETS", "STIMMUNGEN", "HDRI_MUSTER", "HERKUNFT",
           "VORGABE_INTENSITAET", "VORGABE_DREHUNG_GRAD", "aufloesung_fuer",
           "dateiname", "himmel_ordner", "himmel_datei", "himmelsbilder_stand",
           "prompt_satz", "PRESET_WEISS"]

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

#: Die acht Stimmungen.
#:
#: ``hdri`` ist die Vorgabe je Stimmung (Tabelle der HomeStation, 20.10.2026). ``prompt_de``
#: ist der Satz, den der Knoten drüben in den Prompt legt (``VIS_STIMMUNGEN``; morgen, abend
#: und weiss wörtlich wie dort), ``prompt_en`` der Satz, den der Heim-PC anfügt, wenn der
#: übersetzte Prompt keines der ``merkmale`` trägt — sonst stünde die Stimmung doppelt da.
#: Keine Bauteilwörter (``prompts.BAUTEILWOERTER``) im englischen Satz: Er wird nach dem
#: Bauteilwächter angefügt und soll nichts bestellen, was die Geometrie nicht trägt.
STIMMUNGEN = {
    "morgen": {
        "label": "Morgenlicht", "hdri": "sunny_vondelpark",
        "prompt_de": "Morgenlicht, klare lange Schatten, frische kühle Luft",
        "prompt_en": "early morning light, clear long shadows, fresh cool air",
        "merkmale": ("morning",)},
    "mittag": {
        "label": "Mittag", "hdri": "kloofendal_43d_clear_puresky",
        "prompt_de": "Mittagslicht, hohe Sonne, klarer Himmel",
        "prompt_en": "midday light, high sun, clear sky",
        "merkmale": ("midday", "noon")},
    "abend": {
        "label": "Abendstimmung", "hdri": "fish_eagle_hill",
        "prompt_de": "Abendstimmung, warmes Licht, leuchtende Fenster",
        "prompt_en": "evening mood, warm low light, lit interiors glowing",
        "merkmale": ("evening", "sunset", "golden hour")},
    "blaue-stunde": {
        "label": "Blaue Stunde", "hdri": "the_sky_is_on_fire",
        "prompt_de": "Blaue Stunde, tiefblauer Himmel, warm leuchtende Innenräume",
        "prompt_en": "blue hour, deep blue sky, warmly lit interiors",
        "merkmale": ("blue hour", "twilight", "dusk")},
    "bedeckt": {
        "label": "Bedeckt", "hdri": "overcast_soil_puresky",
        "prompt_de": "bedeckter Himmel, weiches gleichmässiges Licht",
        "prompt_en": "overcast sky, soft even light",
        "merkmale": ("overcast",)},
    "nebel": {
        "label": "Nebel", "hdri": "kloppenheim_04",
        "prompt_de": "Nebel, gedämpftes Licht, Tiefe im Dunst",
        "prompt_en": "fog, muted light, depth fading into haze",
        "merkmale": ("fog", "mist", "haze")},
    "winter": {
        "label": "Winter", "hdri": "snowy_field",
        "prompt_de": "Winter, Schnee am Boden, kaltes klares Licht",
        "prompt_en": "winter, snow on the ground, cold clear light",
        "merkmale": ("winter", "snow")},
    "weiss": {
        "label": "Weissmodell", "hdri": "mud_road_puresky",
        "prompt_de": "Weissmodell, neutrales Studiolicht, keine Materialien",
        "prompt_en": "white plaster study model, neutral studio light, no materials",
        "merkmale": ("white model", "plaster model", "white plaster", "no materials")},
}


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
