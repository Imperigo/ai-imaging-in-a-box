#!/usr/bin/env python3
"""Erklärkarten für die Tafel: was jeder Knoten der Knotenansicht von Visbox kann.

**Wozu** (Owner, 23.10.2026): *«ergänze in tafel einzelne erklärungen zu den visbox node, pro node
eine tafel zur aufklärung der einzelnen funktionen»*. Je Knotenart eine Karte: wozu er dient, was
man an ihm einstellt (jedes Feld in einem Satz), was hineinfliesst und herauskommt, was er auslöst,
womit er typisch verbunden ist und wo seine ehrliche Grenze liegt — dazu eine Übersichtskarte mit
der typischen Kette. Die ausführliche Fassung mit Quellen steht in ``docs/KNOTEN_ERKLAERT.md``; sie
ersetzt die Karten vom 14.10.2026 (``20261014-knoten-*``).

Regel 100 (Entscheid vom 20.10.2026): Die Karten sind für Leser — sie nennen das Partnerprogramm,
aus dem die Knotenansicht stammt, nicht. Der Stand im Fuss kommt aus ``kosmovis/HERKUNFT.json``,
steht aber nur als «Stand der Knotenansicht».

Die Karten sind **erzeugt, nicht abgelegt**: Die PNG-Dateien gehören nicht ins Repo, sondern auf
die Tafel (Zweig ``zentrale`` im Partner-Repo, ``tafel/kosmovis/``). Wer einen Text ändert, ändert
ihn hier und in ``docs/KNOTEN_ERKLAERT.md`` und erzeugt neu.

So entsteht ein Bild: HTML schreiben (Schrift IBM Plex Sans, OFL, lokal aus
``ipad/Visbox.swiftpm/Schriften``, kein Netz) → Chromium ohne Fenster macht ein Bildschirmbild
(gesucht unter ``/opt/pw-browsers/chromium*/chrome-linux/chrome``, sonst im Pfad, sonst
``--chrome``) → PIL schneidet es auf die Inhaltshöhe zu (sonst bliebe unten ein schwarzer Streifen)
und hält es unter 600 KB und 1600 px Seitenlänge.

**Sprache** (Owner-Regel 15.10.2026, bestätigt als Entscheid 142 am 23.10.2026: «KosmoOrbit-Dinge
deutsch, Visbox-Dinge englisch»): Die Karten sind Visbox-Dinge, darum ist ``--sprache en`` die
Vorgabe (Dateien ``20261024-knoten-*``, Gruppe «Visbox · What the nodes do», Quelle
``docs/KNOTEN_ERKLAERT.en.md``). ``--sprache de`` erzeugt die deutsche Fassung vom 23.10.2026
(``20261023-knoten-*``), die nicht aufgehängt wird. Die Oberfläche von Visbox zeigt deutsche
Beschriftungen: Auf den englischen Karten steht darum zuerst das englische Wort, dahinter in Klammern
die Beschriftung wie am Bildschirm; der gezeichnete Knoten trägt seine Beschriftungen wortgleich.

    python tools/knoten_tafel.py --ausgabe <ordner>
    python tools/knoten_tafel.py --ausgabe <ordner> --sprache de
    python tools/knoten_tafel.py --ausgabe <ordner> --karte render
    python tools/knoten_tafel.py --ausgabe <ordner> --nur-html
"""
from __future__ import annotations

import argparse
import glob
import html
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _kopie_stand() -> str:
    """Der Stand der Knotenansicht (``kosmovis/HERKUNFT.json``), kurz — nicht fest im Text, weil
    die Karten sonst nach jedem Nachzug einen alten Stand zeigen (14.10.2026: stand noch auf
    22988d6ed, obwohl die Kopie auf R29 lag)."""
    try:
        quelle = json.loads((Path(__file__).resolve().parents[1] / "kosmovis" / "HERKUNFT.json")
                            .read_text(encoding="utf-8"))["quelle"]["commit"]
        return str(quelle)[:9]
    except (OSError, ValueError, KeyError, TypeError):
        return "unbekannt"

WURZEL = Path(__file__).resolve().parents[1]
SCHRIFTEN = WURZEL / "ipad" / "Visbox.swiftpm" / "Schriften"
SANS = SCHRIFTEN / "IBMPlexSans" / "IBMPlexSans[wdth,wght].ttf"
MONO = SCHRIFTEN / "IBMPlexMono" / "IBMPlexMono-Regular.ttf"

BREITE = 1600
#: Grenzen der Tafel (``tafel/LIESMICH.md`` auf ``zentrale``).
HOECHSTE_SEITE = 1600
HOECHSTE_BYTES = 600 * 1024
GRUPPE = "Visbox · Was die Knoten tun"
DATUM = "20261023"
GRUPPE_EN = "Visbox · What the nodes do"
DATUM_EN = "20261024"
SPRACHEN = ("en", "de")
#: Wörter, die auf keiner Karte und in keiner Notiz stehen dürfen (Regel 100, Entscheid 100/100a).
VERBOTEN = ("kosmoorbit", "kosmovis", "integrator", "zentrale", "kosmopublish", "homestation")

# ── Farben ──────────────────────────────────────────────────────────────────────────────
# Anschlussfarben: die Werte des dunklen Themas aus `kosmovis/packages/kosmo-ui/src/aura.css`
# (`--k-port-*` im dunklen Block; `kameras` ohne Überschreibung).
PORT = {
    "szene": ("#427ad5", "Szene", "das 3D-Modell"),
    "prompt": ("#278c5d", "Prompt", "Text: wie das Bild aussehen soll"),
    "material": ("#967740", "Material", "Stoffe, Farben, Materialsätze"),
    "zahl": ("#8b70ab", "Zahl", "ein Wert, z. B. 0,8"),
    "kameras": ("#2b8a7a", "Kameras", "Liste von Standpunkten"),
    "bild": ("#c95a33", "Bild", "ein fertiges Bild"),
}
# Gruppenstreifen: `VIS_KATEGORIE_HUE` (visgraph.ts) mit den `--k-mod-*`-Werten aus aura.css.
GRUPPE_FARBE = {
    "quelle": ("#00b4f0", "Quelle"),
    "wandler": ("#96702f", "Wandler"),
    "render": ("#ff4d2e", "Render"),
    "ausgabe": ("#1fd17a", "Ausgabe"),
}
VISBOX_TON = {
    "voll": ("#1fd17a", "In Visbox voll wirksam"),
    "teilweise": ("#ffc21a", "In Visbox mit Einschränkung"),
    "stellvertreter": ("#ff7a5c", "In Visbox nur Stellvertreter"),
}

# ── Inhalt je Knoten ────────────────────────────────────────────────────────────────────
# Reihenfolge = Nummer auf der Tafel: Quellen, Wandler, Render, Ausgabe. `titel`, `gruppe`, `ein`
# und `aus` stehen wortgleich wie in der Knoten-Registrierung (`tests/test_knoten_tafel.py`).
# `felder`: (Feld, ein Satz). `fluss`: (ein/aus, Anschluss, ein Satz). Texte kurz; die Herleitung
# steht im Dokument.
KNOTEN: list[dict] = [
    {
        "kurz": "01-modell", "typ": "modell", "titel": "Modell", "gruppe": "quelle",
        "hilfe": "Bringt das Gebäude als 3D-Szene in den Graphen — der Startpunkt jedes Bildes.",
        "ein": [], "aus": [("Szene", "szene")],
        "felder": [
            ("Datei laden …", "Wählt eine Modelldatei (glb, gltf oder IFC) und legt sie in die offene Mappe."),
            ("Andere Datei …", "Ersetzt das geladene Modell; die Mappe bleibt dieselbe."),
            ("3D-Fenster", "Zeigt das Modell, das der Render bekommt — ziehen dreht, Doppelklick öffnet gross."),
            ("Anzeige", "«Szene: N Bauteile (aus IFC)» und der Name der Mappe mit ihrer Fassung."),
        ],
        "fluss": [("aus", "Szene", "das Modell, wie es an den Heim-PC geht")],
        "loest": "Das Laden zeigt einen Balken mit echtem Fortschritt; eine IFC-Datei wandelt der Heim-PC "
                 "um und meldet, was fehlt («Kein Dach in der Datei»). Gerechnet wird erst am Render.",
        "verbunden": "Szene → Render, Eingang «Szene» — Pflicht, ohne sie bestellt der Render nichts.",
        "grenze": "Ohne Heim-PC lädt nichts. Was einer IFC-Datei fehlt, meldet Visbox, ergänzt es aber "
                  "nicht. Eine unlesbare Datei lässt das vorige Modell gelten.",
        "visbox": ("voll", "Lädt in die offene Mappe am Mac; der Heim-PC liest die Datei."),
        "quelle": "visgraph.ts · ModellKnoten.tsx · mappe.ts",
    },
    {
        "kurz": "02-kamera", "typ": "kamera", "titel": "Kamera", "gruppe": "quelle",
        "hilfe": "Legt fest, von wo das Haus gesehen wird — eine Liste von Standpunkten.",
        "ein": [], "aus": [("Kamera-Standpunkte", "kameras")],
        "felder": [
            ("Auto", "Der Heim-PC rechnet die Standpunkte aus den Einstellungen darunter (Vorgabe)."),
            ("Richtungen", "Acht Knöpfe N bis NW; Vorgabe Süd, Südost und Nordwest."),
            ("Auge", "Augenhöhe über dem Gelände am Standpunkt, in Metern (Vorgabe 1,7)."),
            ("Brennweite", "24, 35 oder 50 mm (Vorgabe 35); die kleinere Zahl sieht weiter."),
            ("Abstand", "«füllt»: das Haus füllt so viel der Bildbreite (70 %); «fest»: in Metern."),
            ("Perspektive", "Senkrecht hält senkrechte Kanten gerade; Frei kippt auf das Ziel."),
            ("Blick", "Ein gesicherter Blick oder Standpunkt der Mappe als fester Standpunkt."),
            ("Manuell", "Friert die Standpunkte ein; Auge und Ziel in Metern (Ost, Nord, Höhe)."),
            ("3D-Fenster", "Ein Kegel je Kamera, darunter der Blick — Klick zeigt den nächsten."),
        ],
        "fluss": [("aus", "Kameras", "die Standpunkte für den Auftrag")],
        "loest": "Bei «Auto» fragt der Knoten den Heim-PC live nach den Standpunkten; bestellt wird "
                 "«automatisch» mit diesen Einstellungen. «Manuell» und «Blick» schicken eine feste Liste.",
        "verbunden": "Kamera-Standpunkte → Render; die Varianten lesen sie über den Render-Knoten.",
        "grenze": "Ohne Heim-PC keine Kegel. Die festen Richtungen stehen heute ab der Bodenplatte gerechnet "
                  "(rund 1,3 statt 1,7 m über Gelände). Die Kamera «Eingang» aus dem modellierten Haus gibt "
                  "es in Visbox nicht; Innenansichten auch nicht.",
        "visbox": ("teilweise", "Auto, Blick und Manuell wirken; Standpunkte aus Bauteilen leitet Visbox nicht ab."),
        "quelle": "visgraph.ts · KameraKnoten.tsx · heim-standpunkte.ts · blick-quelle.ts",
    },
    {
        "kurz": "03-skizze-vom-ipad", "typ": "skizzeIpad", "titel": "Skizze vom iPad", "gruppe": "quelle",
        "hilfe": "Holt eine Skizze, die am iPad in die Mappe gelegt wurde, in die Knotenansicht.",
        "ein": [], "aus": [("Bild", "bild")],
        "felder": [
            ("Welche Skizze", "«neueste» (Vorgabe: von selbst die zuletzt gelegte) oder eine ältere."),
            ("Daumenbild", "Zeigt die Skizze, die gerade gilt."),
        ],
        "fluss": [("aus", "Bild", "die Skizze mit Bemerkung und dem Standpunkt ihres Bildes")],
        "loest": "Am Eingang «Skizze» des Render-Knotens führt die Skizze das Bild: Der Knopf heisst «Bild aus "
                 "Skizze erzeugen», ihre Bemerkung ist die Anweisung, das Bild entsteht von ihrem Standpunkt.",
        "verbunden": "Bild → Render, Eingang «Skizze»; daneben → Bildvergleich.",
        "grenze": "Die Liste wird beim Öffnen gelesen, nicht laufend. Die Güte «Vorschau» gilt noch nicht für "
                  "Skizzen. Das iPad verbindet sich nur über den Mac.",
        "visbox": ("voll", "Mit den Skizzen der offenen Mappe."),
        "quelle": "visgraph.ts · SkizzeKnoten.tsx · skizze-quelle.ts · skizze-fuehrt.ts",
    },
    {
        "kurz": "04-material", "typ": "materialTextur", "titel": "Material", "gruppe": "quelle",
        "hilfe": "Ein Stoff aus der Bibliothek der elf — Sichtbeton, Fichte, Backstein, Lehm, Putz …",
        "ein": [("Palette", "material")], "aus": [("Material", "material")],
        "felder": [
            ("Stoff", "Die Wahl aus der Bibliothek (Vorgabe Sichtbeton, sandgestrahlt)."),
            ("Vorschau", "Zeigt den Stoff als Kugel, Würfel oder Fläche."),
            ("Massstab", "Wie gross ein Bild der Textur auf dem Bauteil wird, in Metern (Vorgabe 1)."),
            ("Drehung", "Dreht die Textur auf dem Bauteil, in Grad."),
            ("Relief", "Wie plastisch die Oberfläche wirkt, 0 bis 1 (Vorgabe 0,6)."),
        ],
        "fluss": [("ein", "Material", "Palette: tönt den Stoff (nur von der Farbpalette)"),
                  ("aus", "Material", "Stoff mit Massstab, Drehung, Relief und Tönung")],
        "loest": "Nichts von selbst. An der Oberfläche geht er in die Bestellung: Blender legt die Textur auf "
                 "die Bauteil-Art, und der Heim-PC nennt den Stoff im Prompt.",
        "verbunden": "Farbpalette → Palette; Material → Oberfläche, Eingang Fassade, Dach, Fenster, Boden oder Übrige.",
        "grenze": "Die Texturen (frei, CC0) liegen nur am Heim-PC — fehlt eine, weist er den Auftrag mit Satz "
                  "ab. Ohne Oberfläche bewirkt der Knoten nichts.",
        "visbox": ("voll", "Alle elf Stoffe mit echten Vorschaubildern."),
        "quelle": "visgraph.ts (VIS_MATERIAL_BIBLIOTHEK) · OberflaecheKnoten.tsx · materialwahl.py",
    },
    {
        "kurz": "05-farbpalette", "typ": "farbpalette", "titel": "Farbpalette", "gruppe": "quelle",
        "hilfe": "Bis zu vier Farben für den Entwurf; eine davon tönt das Material.",
        "ein": [], "aus": [("Palette", "material")],
        "felder": [
            ("Farben", "Bis vier Farbfelder; das Plus fügt eine hinzu."),
            ("Tönt mit", "Welche Farbe das angehängte Material tönt (die Leitfarbe)."),
            ("Stärke", "Wie stark die Tönung wirkt, 0 bis 1 (Vorgabe 0,4)."),
        ],
        "fluss": [("aus", "Material", "die Farben und ihr Satz, z. B. «Helles Beige, Schiefergrau»")],
        "loest": "Blender mischt die Leitfarbe in die Textur. Aus allen Farben wird ein Satz mit Farbwörtern, "
                 "der über Oberfläche und Kombinierer in den Prompt reist.",
        "verbunden": "Palette → Material, Eingang «Palette».",
        "grenze": "Die Farbwörter sind grob; die KI liest Wörter, keine genauen Farbwerte. Ohne Material "
                  "dazwischen geht die Palette nirgends hin.",
        "visbox": ("voll", "Wie beschrieben."),
        "quelle": "visgraph.ts (paletteAusParams, farbWort) · OberflaecheKnoten.tsx",
    },
    {
        "kurz": "06-bild-referenz", "typ": "referenz", "titel": "Bild-Referenz", "gruppe": "quelle",
        "hilfe": "Ein Vorbild — ein fremdes Bild zum Vergleichen oder als Farbvorbild.",
        "ein": [], "aus": [("Bild", "bild")],
        "felder": [
            ("Bildadresse", "Eine Adresse oder ein eingebettetes Bild; der Knoten zeigt es."),
        ],
        "fluss": [("aus", "Bild", "das Vorbild, unverändert")],
        "loest": "Nichts beim Heim-PC. Im Bildvergleich steht das Vorbild neben den Renders; in der "
                 "Kuratierfläche (Vollbild zum Auswählen) dient es für einen Farbangleich.",
        "verbunden": "Bild → Bildvergleich, Bild 1–3.",
        "grenze": "Aufs Blatt geht es nicht («nur Vorbild») — es ist kein Bild dieses Projekts. Den Stil des "
                  "KI-Bildes steuert es nicht.",
        "visbox": ("voll", "Wie beschrieben."),
        "quelle": "visgraph.ts · NodeCanvas.tsx (bildQuelle) · KuratierFlaeche.tsx",
    },
    {
        "kurz": "07-viewport-aufnahme", "typ": "aufnahme", "titel": "Viewport-Aufnahme", "gruppe": "quelle",
        "hilfe": "Gedacht als Schnappschuss einer 3D-Entwurfsansicht — ein Bild ohne Rendern.",
        "ein": [], "aus": [("Bild", "bild")],
        "felder": [
            ("Welche Aufnahme", "«jüngste Aufnahme» oder ein benannter Standpunkt."),
            ("Aufnehmen", "Sagt nur, wo der echte Knopf sitzt; der Knoten nimmt selbst nichts auf."),
        ],
        "fluss": [("aus", "Bild", "die Aufnahme — in Visbox keine")],
        "loest": "Nichts beim Heim-PC.",
        "verbunden": "Bild → Bildvergleich.",
        "grenze": "Visbox hat keine 3D-Entwurfsansicht, also keine Aufnahme: Der Knoten bleibt bei «Noch keine "
                  "Aufnahme». Er steht in der Liste, damit Graphen gleich bleiben.",
        "visbox": ("stellvertreter", "Steht in der Liste, bewirkt hier nichts und sagt das."),
        "quelle": "visgraph.ts · NodeCanvas.tsx (waehleAufnahme)",
    },
    {
        "kurz": "08-kamera-aus-3d", "typ": "kameraAus3d", "titel": "Kamera aus 3D-Ansicht",
        "gruppe": "quelle",
        "hilfe": "Gedacht, um den Blick einer offenen 3D-Ansicht als Kamera zu übernehmen.",
        "ein": [], "aus": [("Kamera-Standpunkte", "kameras")],
        "felder": [
            ("Kamera übernehmen", "Liest Auge, Ziel und Blickfeld der 3D-Ansicht — einmal, nicht laufend."),
        ],
        "fluss": [("aus", "Kameras", "genau eine Kamera — in Visbox keine")],
        "loest": "Am Render-Knoten ginge nur seine Kamera in den Auftrag; trägt er keine, wird nicht bestellt.",
        "verbunden": "Kamera-Standpunkte → Render.",
        "grenze": "Visbox hat keine 3D-Ansicht; der Knoten sagt «Keine 3D-Ansicht offen». Für einen festen "
                  "Blick dient die Kamera mit dem Reiter «Blick».",
        "visbox": ("stellvertreter", "Steht in der Liste, bewirkt hier nichts und sagt das."),
        "quelle": "visgraph.ts · kamera-aus-3d.ts · KameraAus3dKnoten.tsx",
    },
    {
        "kurz": "09-stimmung", "typ": "stimmung", "titel": "Stimmung", "gruppe": "wandler",
        "hilfe": "Wählt Licht und Stimmung — acht Stimmungen mit eigenem Himmelsbild.",
        "ein": [], "aus": [("Prompt", "prompt")],
        "felder": [
            ("Stimmungen", "Morgen, Mittag, Abend, Blaue Stunde, Bedeckt, Nebel, Winter, Weissmodell; "
                           "mehrere heisst ein Bild je Stimmung."),
            ("Vorschau", "Das Himmelsbild der gewählten Stimmung."),
            ("Drehen", "Aus: der Heim-PC stellt die Sonne je Kamera seitlich; an: fester Winkel."),
            ("Wirkt auf", "«Licht + Satz» (Vorgabe), nur Licht in Blender oder nur Satz für die KI."),
        ],
        "fluss": [("aus", "Prompt", "der Stimmungssatz, z. B. «Abendstimmung, warmes Licht»")],
        "loest": "Das Himmelsbild (frei, CC0) gibt in Blender Licht, Sonne, Schatten und Spiegelungen; Himmel und "
                 "Boden bis zum Horizont passen zur Stimmung. Jede Stimmung bekommt ihr eigenes Grundbild.",
        "verbunden": "Prompt → Prompt-Kombinierer, Eingang «Stimmung».",
        "grenze": "«Satz» allein ändert das Licht nicht. Eine Variante mit anderer Stimmung dauert länger, weil "
                  "Blender neu rechnet.",
        "visbox": ("voll", "Alle acht Stimmungen mit Himmelsbild am Heim-PC."),
        "quelle": "visgraph.ts (VIS_STIMMUNGEN) · StimmungKnoten.tsx · stimmung.py",
    },
    {
        "kurz": "10-prompt", "typ": "prompt", "titel": "Prompt", "gruppe": "wandler",
        "hilfe": "Freier Text, der beschreibt, wie das Bild aussehen soll.",
        "ein": [], "aus": [("Prompt", "prompt")],
        "felder": [
            ("Stil-Text", "Ein Textfeld, z. B. «Sichtbeton, Herbstlaub»; gespeichert beim Verlassen."),
        ],
        "fluss": [("aus", "Prompt", "der Text, wortgleich")],
        "loest": "Nichts von selbst; Kombinierer und Render zeigen ihn sofort. Nennt er einen anderen "
                 "Fassadenstoff, rechnet eine Variante ihr Grundbild mit diesem Stoff neu.",
        "verbunden": "Prompt → Prompt-Kombinierer, Eingang «Stil» (oder direkt an Render).",
        "grenze": "Deutscher Text wird am Heim-PC übersetzt; ungewöhnliche Wörter können verloren gehen. Ein "
                  "leerer Prompt mit KI-Schritt wird abgelehnt — der Knopf sagt es vorher.",
        "visbox": ("voll", "Wie beschrieben."),
        "quelle": "visgraph.ts · NodeCanvas.tsx",
    },
    {
        "kurz": "11-oberflaeche", "typ": "material", "titel": "Oberfläche", "gruppe": "wandler",
        "hilfe": "Ordnet jeder Bauteil-Art einen Stoff zu: Fassade, Dach, Fenster, Boden, Übrige.",
        "ein": [("Fassade", "material"), ("Dach", "material"), ("Fenster", "material"),
                ("Boden", "material"), ("Übrige", "material")],
        "aus": [("Material", "material")],
        "felder": [
            ("Fünf Eingänge", "Je Bauteil-Art ein Material-Knoten; Türen zählen zu «Übrige»."),
            ("Zuordnung", "Eine Zeile sagt, welche Art welchen Stoff hat."),
            ("… mehr", "Klappt die Sätze auf, die zum Kombinierer gehen."),
        ],
        "fluss": [("ein", "Material", "je Art ein Stoff (nur vom Knoten «Material»)"),
                  ("aus", "Material", "die Zuordnung und ihre Sätze")],
        "loest": "Der Render-Knoten bestellt die Stoffe je Bauteil-Art; Blender legt die Texturen an, und das "
                 "Grundbild zeigt sie schon. Was nichts bekommt, behält den Stoff aus dem Modell.",
        "verbunden": "Material → Fassade usw.; Material → Prompt-Kombinierer, Eingang «Material».",
        "grenze": "Welche Bauteile Fassade oder Dach sind, liest der Heim-PC aus der Datei; Bauteile ohne Art "
                  "behalten ihren Stoff.",
        "visbox": ("voll", "Wie beschrieben; Wandschichten als Sätze gibt es in einer Mappe nicht."),
        "quelle": "visgraph.ts (oberflaecheMaterialien) · OberflaecheKnoten.tsx · materialwahl.py",
    },
    {
        "kurz": "12-kombinierer", "typ": "kombinierer", "titel": "Prompt-Kombinierer", "gruppe": "wandler",
        "hilfe": "Fügt Stimmung, Stil und Material zum Text, der wirklich an die KI geht.",
        "ein": [("Stimmung", "prompt"), ("Stil", "prompt"), ("Material", "material")],
        "aus": [("Finaler Prompt", "prompt")],
        "felder": [
            ("Anzeige", "Zeigt den fertigen Prompt live; man stellt nichts ein."),
            ("… mehr", "Klappt den ganzen Text auf."),
        ],
        "fluss": [("ein", "Prompt", "Stimmung und Stil"), ("ein", "Material", "Sätze der Oberfläche"),
                  ("aus", "Prompt", "alles in einem Text")],
        "loest": "Nichts von selbst. Ändert sich der Text, steht ein fertiges Bild am Render-Knoten auf «veraltet».",
        "verbunden": "Stimmung, Prompt und Oberfläche hinein; Ausgang → Render, Eingang «Prompt».",
        "grenze": "Reiht nur aneinander (mit Komma, Leeres fällt weg); Widersprüche zwischen Stimmung und Stil "
                  "löst er nicht.",
        "visbox": ("voll", "Wie beschrieben."),
        "quelle": "visgraph.ts · renderprompt.ts (finalerRenderPrompt)",
    },
    {
        "kurz": "13-zahl", "typ": "zahl", "titel": "Zahl", "gruppe": "wandler",
        "hilfe": "Ein Regler für einen einzelnen Wert.",
        "ein": [], "aus": [("Wert", "zahl")],
        "felder": [
            ("Regler", "Vorgabe 0,8, von 0 bis 1 in Schritten von 0,05; gilt beim Loslassen."),
        ],
        "fluss": [("aus", "Zahl", "der Wert")],
        "loest": "Am Render-Knoten wird er zur Geometrie-Treue (wie eng die KI der Form folgt) oder zu den "
                 "Samples (Rechenschritte je Bildpunkt in Blender).",
        "verbunden": "Wert → Render, Eingang «Geometrie-Treue» oder «Samples».",
        "grenze": "Ist am Render «Qualität gegen Zeit» gewählt, gilt diese statt der Samples-Zahl. Für Samples "
                  "ist der Bereich 0 bis 1 zu klein.",
        "visbox": ("voll", "Wie beschrieben."),
        "quelle": "visgraph.ts · NodeCanvas.tsx · vis-jobs.ts",
    },
    {
        "kurz": "14-render", "typ": "render", "titel": "Render", "gruppe": "render",
        "hilfe": "Bestellt die Bilder beim Heim-PC — nur auf Knopfdruck, nie automatisch.",
        "ein": [("Szene", "szene"), ("Prompt", "prompt"), ("Geometrie-Treue", "zahl"),
                ("Samples", "zahl"), ("Kamera-Standpunkte", "kameras"), ("Skizze", "bild")],
        "aus": [("Bild", "bild")],
        "felder": [
            ("Preset", "Fertiges Paket: Entwurf schnell, Präsentation, Nacht, Innenraum — oder keines."),
            ("Auflösung", "1600 × 1000 (Vorgabe) bis 4000 × 2667 Bildpunkte."),
            ("Qualität gegen Zeit", "Schnell bis voll; hat Vorrang vor der Zahl an «Samples»."),
            ("Himmel / drehen", "Eine Himmelsart von Blender oder keine; Drehung in Grad."),
            ("Bildwerkzeug", "Welches KI-Modell malt (Vorgabe Z-Image Turbo)."),
            ("Grundlage rendern", "Stufe 1: nur Blender — Kamera, Geometrie, Licht, Stoffe, ohne KI."),
            ("Variante erzeugen", "Stufe 2: die KI malt vom Grundbild aus; mit Skizze «Bild aus Skizze erzeugen»."),
            ("Freigeben", "Erst dieser Klick schickt einen wartenden Auftrag zum Heim-PC."),
            ("Abbrechen", "Hält einen laufenden Auftrag an."),
            ("Grundlage", "Kennung und Kameras der Grundlage, oder «veraltet» bzw. «noch keine»."),
            ("Startwert", "Die Zufallszahl, mit der die KI beginnt; «neu würfeln» gibt eine andere."),
            ("Güte", "Voll (Vorgabe): gross, vom Grundbild aus; Vorschau: schnell und klein, Fenster und Form nicht gesichert."),
            ("Strichzeichnung", "Bestellt eine Linienzeichnung, ohne KI."),
            ("… mehr", "Auftragsformular (Fassade, Szene, Jahreszeit, Personen, Freitext) neben dem Knoten."),
            ("Bild am Knoten", "KI-Bild und Grundbild nebeneinander; Klick gross, dort «Exportieren»."),
        ],
        "fluss": [("ein", "Szene", "Szene (Pflicht)"), ("ein", "Prompt", "Prompt"),
                  ("ein", "Zahl", "Geometrie-Treue, Samples"), ("ein", "Kameras", "Standpunkte"),
                  ("ein", "Bild", "Skizze (nur Skizze vom iPad)"), ("aus", "Bild", "das letzte Bild")],
        "loest": "Jeder Auftrag wartet auf «Freigeben». Dann rechnet der Heim-PC je Kamera: Blender für das "
                 "Grundbild, die KI vom Grundbild aus (Stärke 0,5), danach die Prüfung der Form. Bild und "
                 "Urteil kommen an den Knoten; er merkt sich sein letztes Bild.",
        "verbunden": "Modell, Kombinierer, Kamera, Skizze hinein; Bild → Varianten oder Bildvergleich.",
        "grenze": "Ohne Heim-PC rechnet nichts. Die Vorschau geht noch nicht vom Grundbild aus. Modelle mit "
                  "offener Lizenz malen frei und tragen «Lizenz offen». Keine Innenansichten.",
        "visbox": ("voll", "Jeder Auftrag wartet in Visbox auf «Freigeben» — auch Vorschau und Grundlage."),
        "quelle": "visgraph.ts · NodeCanvas.tsx · grundlage.ts · guete.ts · vis-jobs.ts",
    },
    {
        "kurz": "15-varianten", "typ": "varianten", "titel": "Varianten", "gruppe": "render",
        "hilfe": "Bestellt die Einstellung des Render-Knotens in allen Kombinationen — mit einem Klick.",
        "ein": [("Render", "bild")], "aus": [("Bilder", "bild")],
        "felder": [
            ("Zähler", "Sagt vorher, wie viele Bilder es werden: Standpunkte × Stimmungen × Entwürfe."),
            ("Standpunkte", "Die Richtungen der Kamera; mit Skizze deren Standpunkt."),
            ("Stimmungen", "Die acht zum Anhaken (Vorgabe Abend)."),
            ("Entwürfe", "Welches Modell; in Visbox das aktuelle."),
            ("Warnung", "Ab zwölf Bildern, mit ungefährer Dauer; keine Grenze."),
            ("Daumen", "Ein Vorschaubild je Variante; blättern, gross öffnen, eine wählen."),
            ("Bestellen / Alle freigeben", "Zwei Klicks für die ganze Serie."),
        ],
        "fluss": [("ein", "Bild", "der Render-Knoten, dessen Einstellung gilt"),
                  ("aus", "Bild", "alle Bilder der Serie")],
        "loest": "Ein Auftrag je Stimmung und Entwurf, mit allen Standpunkten, in voller Güte. Passt das Grundbild des Render-"
                 "Knotens, wird es genutzt (auch für einen Teil seiner Kameras); eine andere Stimmung oder ein "
                 "anderer Fassadenstoff bekommt ein eigenes Grundbild.",
        "verbunden": "Render → Render; Bilder → Bildvergleich, Bild 1 (dort als Raster).",
        "grenze": "Die Zeitschätzung ist eine Annahme. Zwei Stoff-Varianten mit demselben Stoff rechnen das "
                  "Grundbild doppelt.",
        "visbox": ("teilweise", "Standpunkte sind die Richtungen des Heim-PCs; Entwurf nur das aktuelle Modell."),
        "quelle": "visgraph.ts · varianten.ts · VariantenKnoten.tsx · VariantenDaumen.tsx",
    },
    {
        "kurz": "16-bildvergleich", "typ": "vergleich", "titel": "Bildvergleich", "gruppe": "ausgabe",
        "hilfe": "Stellt Bilder nebeneinander, jedes mit seinem Prüfurteil.",
        "ein": [("Bild 1", "bild"), ("Bild 2", "bild"), ("Bild 3", "bild")], "aus": [],
        "felder": [
            ("Bilder", "Ein Klick öffnet ein Bild gross; die Ansicht bleibt beim Zoomen im Fenster."),
            ("Raster", "Hängen Varianten an: Zeilen Standpunkte, Spalten Stimmungen."),
        ],
        "fluss": [("ein", "Bild", "bis zu drei Bilder oder eine Variantenserie")],
        "loest": "Nichts — er zeigt nur. Jedes Bild trägt «QA ok», «QA ✗», «nicht beurteilbar» oder «QA nicht "
                 "gemessen», dazu den Grund und, wo nötig, «Vorschau» und «Lizenz offen».",
        "verbunden": "Varianten → Bild 1; Render, Skizze oder Bild-Referenz → Bild 1–3.",
        "grenze": "Höchstens drei Einzelbilder, mehr nur als Raster. Ausgewählt und exportiert wird in der "
                  "grossen Ansicht oder der Kuratierfläche.",
        "visbox": ("voll", "Wie beschrieben."),
        "quelle": "visgraph.ts · NodeCanvas.tsx (BildKachel) · VariantenRaster.tsx · varianten-diff.ts",
    },
    {
        "kurz": "17-aufs-blatt", "typ": "blatt", "titel": "Aufs Blatt", "gruppe": "ausgabe",
        "hilfe": "Gedacht, um ein Bild auf ein Plakatblatt zu legen.",
        "ein": [("Bild", "bild")], "aus": [],
        "felder": [
            ("Titel", "Der Name auf dem Blatt (Vorgabe «Visualisierung»)."),
            ("Aufs Blatt", "Nur aktiv mit fertigem Bild; nimmt das neueste fertige."),
        ],
        "fluss": [("ein", "Bild", "ein fertiges Bild eines Render-Knotens")],
        "loest": "In Visbox endet der Klick mit dem Satz, dass es hier keine Blätter gibt.",
        "verbunden": "Render → Bild.",
        "grenze": "Plakatblätter gibt es in Visbox nicht. Ein Bild sichert man mit «Exportieren» in der grossen "
                  "Ansicht, in voller Auflösung. Ein Vorbild geht nie aufs Blatt.",
        "visbox": ("stellvertreter", "Steht in der Liste und sagt beim Klick, dass es hier keine Blätter gibt."),
        "quelle": "visgraph.ts · NodeCanvas.tsx (Fall blatt) · Stellvertreter publish.ts",
    },
]

#: Die Notiz neben jedem Bild auf der Tafel — ein bis zwei Sätze für Laien.
NOTIZEN = {
    "00-uebersicht": "Siebzehn Knoten in vier Gruppen, verbunden vom Ausgang zum Eingang. Bilder entstehen in "
                     "zwei Stufen am Render-Knoten — erst das Grundbild aus Blender, dann die KI-Variante — und "
                     "jeder Auftrag wartet auf die Freigabe des Architekten.",
    "01-modell": "Bringt das Gebäude als 3D-Modell in die Knotenansicht; ohne Modell entsteht kein Bild. "
                 "«Datei laden …» nimmt glb oder IFC, ein kleines 3D-Fenster zeigt es.",
    "02-kamera": "Legt fest, von wo das Haus gesehen wird: Auto (der Heim-PC rechnet aus Richtung, Augenhöhe, "
                 "Brennweite und Abstand), ein gesicherter Blick oder von Hand gestellt.",
    "03-skizze-vom-ipad": "Holt eine Skizze vom iPad in die Knotenansicht. Am Render-Knoten führt sie das Bild: "
                          "ihre Bemerkung ist die Anweisung, ihr Standpunkt die Kamera.",
    "04-material": "Ein Stoff aus der Bibliothek der elf mit Massstab, Drehung und Relief. An der Oberfläche "
                   "angehängt, legt Blender ihn als Textur auf die Bauteile.",
    "05-farbpalette": "Bis zu vier Farben; die gewählte tönt das Material, und alle gehen als Farbwörter an die KI.",
    "06-bild-referenz": "Ein Vorbild zum Vergleichen oder als Farbvorbild. Es geht nicht aufs Blatt und steuert "
                        "nicht den Stil.",
    "07-viewport-aufnahme": "In Visbox nur Stellvertreter: Ohne 3D-Entwurfsansicht gibt es keine Aufnahme, und der "
                            "Knoten sagt das.",
    "08-kamera-aus-3d": "In Visbox nur Stellvertreter: Ohne 3D-Ansicht trägt er keine Kamera. Einen festen Blick "
                        "wählt man an der Kamera unter «Blick».",
    "09-stimmung": "Acht Stimmungen mit eigenem Himmelsbild: Licht, Sonne und Schatten in Blender und ein Satz für "
                   "die KI. Jede Stimmung bekommt ihr eigenes Grundbild.",
    "10-prompt": "Freier Text, wie das Bild aussehen soll; er geht wortgleich weiter, meist an den Eingang «Stil» "
                 "des Kombinierers.",
    "11-oberflaeche": "Ordnet Fassade, Dach, Fenster, Boden und Übrigem je einen Stoff zu. Was nichts bekommt, "
                      "behält den Stoff aus dem Modell.",
    "12-kombinierer": "Fügt Stimmung, Stil und Material zum Text, der an die KI geht — live sichtbar. Ändert er "
                      "sich, gilt ein fertiges Bild als veraltet.",
    "13-zahl": "Ein Regler (Vorgabe 0,8) für die Geometrie-Treue oder die Samples am Render-Knoten.",
    "14-render": "Der Knoten, der beim Heim-PC bestellt: erst «Grundlage rendern» (nur Blender), dann «Variante "
                 "erzeugen» (die KI malt vom Grundbild aus). Jeder Auftrag wartet auf «Freigeben».",
    "15-varianten": "Bestellt alle Kombinationen aus Standpunkten, Stimmungen und Entwürfen mit einem Klick; ein "
                    "Zähler sagt vorher, wie viele Bilder es werden.",
    "16-bildvergleich": "Zeigt Bilder nebeneinander, jedes mit Prüfurteil; Varianten erscheinen als Raster aus "
                        "Standpunkten und Stimmungen.",
    "17-aufs-blatt": "In Visbox nur Stellvertreter: Plakatblätter gibt es hier nicht. Ein Bild sichert man mit "
                     "«Exportieren» in der grossen Ansicht.",
}


# ── English (Owner, 15.10.2026 and Entscheid 142, 23.10.2026: «Visbox-Dinge englisch») ────────────
# Same content as the German cards, sentence for sentence. The Visbox interface shows German labels:
# where a reader must find a button or a node, the English word comes first and the label as it
# appears on screen follows in brackets. Node and port names in the drawn node stay exactly as on
# screen (`ein`/`aus` are checked against the catalogue), so the drawing matches what the reader sees.
PORT_EN = {
    "szene": ("Scene", "the 3D model"),
    "prompt": ("Prompt", "text: how the image should look"),
    "material": ("Material", "surfaces, colours, material phrases"),
    "zahl": ("Number", "one value, e.g. 0.8"),
    "kameras": ("Cameras", "a list of viewpoints"),
    "bild": ("Image", "a finished image"),
}
GRUPPE_FARBE_EN = {"quelle": "Source", "wandler": "Converter", "render": "Render", "ausgabe": "Output"}
VISBOX_TON_EN = {
    "voll": "Fully working in Visbox",
    "teilweise": "Working in Visbox, with limits",
    "stellvertreter": "Only a placeholder in Visbox",
}

#: typ → English texts. `name`: the card title (English, UI label in brackets where it differs).
#: `kurz`: the English short name in the file name. Everything else mirrors the German entry.
KNOTEN_EN_TEXT: dict[str, dict] = {
    "modell": {
        "kurz": "01-model", "name": "Model (Modell)",
        "hilfe": "Brings the building into the graph as a 3D scene — the starting point of every image.",
        "felder": [
            ("Load file … (Datei laden …)", "Picks a model file (glb, gltf or IFC) and puts it into the open project folder."),
            ("Other file … (Andere Datei …)", "Replaces the loaded model; the project folder stays the same."),
            ("3D window", "Shows the model the render will receive — drag to turn it, double-click to enlarge."),
            ("Status line", "“Szene: N Bauteile (aus IFC)” (scene: N building parts) and the folder name with its version."),
        ],
        "fluss": [("aus", "szene", "the model as it goes to the home PC")],
        "loest": "Loading shows a bar with real progress; the home PC converts an IFC file and reports what is "
                 "missing (“Kein Dach in der Datei”, no roof in the file). Nothing is computed until the Render node.",
        "verbunden": "Scene → Render, input “Szene” — required; without it the Render node orders nothing.",
        "grenze": "Without the home PC nothing loads. Visbox reports what an IFC file lacks, but does not add it. "
                  "An unreadable file leaves the previous model in place.",
        "visbox": "Loads into the open project folder on the Mac; the home PC reads the file.",
        "notiz": "Brings the building into the node view as a 3D model; without a model there is no image. "
                 "“Load file” (Datei laden) takes glb or IFC, and a small 3D window shows it.",
    },
    "kamera": {
        "kurz": "02-camera", "name": "Camera (Kamera)",
        "hilfe": "Decides where the house is seen from — a list of viewpoints.",
        "felder": [
            ("Auto", "The home PC computes the viewpoints from the settings below (default)."),
            ("Directions (Richtungen)", "Eight buttons N to NW; default south, south-east and north-west."),
            ("Eye (Auge)", "Eye height above the ground at the viewpoint, in metres (default 1.7)."),
            ("Focal length (Brennweite)", "24, 35 or 50 mm (default 35); the smaller number sees wider."),
            ("Distance (Abstand)", "“füllt” (fills): the house fills this much of the image width (70 %); “fest” (fixed): in metres."),
            ("Perspective (Perspektive)", "Senkrecht (upright) keeps vertical edges straight; Frei (free) tilts towards the target."),
            ("View (Blick)", "A saved view or viewpoint of the project folder, used as one fixed viewpoint."),
            ("Manual (Manuell)", "Freezes the viewpoints; eye and target in metres (east, north, height)."),
            ("3D window", "One cone per camera, below it the view — a click shows the next one."),
        ],
        "fluss": [("aus", "kameras", "the viewpoints for the order")],
        "loest": "With “Auto” the node asks the home PC live for the viewpoints; the order says “automatic” with "
                 "these settings. “Manual” and “View” send a fixed list.",
        "verbunden": "Camera viewpoints (Kamera-Standpunkte) → Render; Variants read them through the Render node.",
        "grenze": "Without the home PC there are no cones. The fixed directions are currently measured from the floor slab "
                  "(about 1.3 instead of 1.7 m above the ground). The “Eingang” (entrance) camera derived from the "
                  "modelled house does not exist in Visbox; nor do interior views.",
        "visbox": "Auto, View and Manual work; Visbox does not derive viewpoints from building parts.",
        "notiz": "Decides where the house is seen from: Auto (the home PC computes from direction, eye height, "
                 "focal length and distance), a saved view, or placed by hand.",
    },
    "skizzeIpad": {
        "kurz": "03-sketch-from-ipad", "name": "Sketch from iPad (Skizze vom iPad)",
        "hilfe": "Brings a sketch that was placed in the project folder on the iPad into the node view.",
        "felder": [
            ("Which sketch", "“neueste” (newest — by default the one placed last, automatically) or an older one."),
            ("Thumbnail", "Shows the sketch that currently applies."),
        ],
        "fluss": [("aus", "bild", "the sketch with its note and the viewpoint of its image")],
        "loest": "At the “Skizze” (sketch) input of the Render node the sketch leads the image: the button reads "
                 "“Bild aus Skizze erzeugen” (make image from sketch), its note becomes the instruction, and the "
                 "image is made from its viewpoint.",
        "verbunden": "Image → Render, input “Skizze”; also → Image comparison.",
        "grenze": "The list is read when the node opens, not continuously. The “Vorschau” (preview) quality does not "
                  "yet work for sketches. The iPad connects only through the Mac.",
        "visbox": "With the sketches of the open project folder.",
        "notiz": "Brings a sketch from the iPad into the node view. At the Render node it leads the image: "
                 "its note is the instruction, its viewpoint the camera.",
    },
    "materialTextur": {
        "kurz": "04-material", "name": "Material",
        "hilfe": "One surface from the library of eleven — fair-faced concrete, spruce, brick, rammed earth, plaster …",
        "felder": [
            ("Surface (Stoff)", "The choice from the library (default sandblasted fair-faced concrete)."),
            ("Preview (Vorschau)", "Shows the surface as a sphere, cube or flat panel."),
            ("Scale (Massstab)", "How large one tile of the texture is on the building part, in metres (default 1)."),
            ("Rotation (Drehung)", "Turns the texture on the building part, in degrees."),
            ("Relief", "How three-dimensional the surface looks, 0 to 1 (default 0.6)."),
        ],
        "fluss": [("ein", "material", "Palette: tints the surface (only from the Colour palette)"),
                  ("aus", "material", "surface with scale, rotation, relief and tint")],
        "loest": "Nothing by itself. At the Surface node it becomes part of the order: Blender puts the texture "
                 "on that kind of building part, and the home PC names the surface in the prompt.",
        "verbunden": "Colour palette → Palette; Material → Surface (Oberfläche), input Fassade, Dach, Fenster, Boden or Übrige.",
        "grenze": "The textures (free, CC0) are stored only on the home PC — if one is missing, it rejects the order "
                  "with a sentence. Without the Surface node this node has no effect.",
        "visbox": "All eleven surfaces with real preview images.",
        "notiz": "One surface from the library of eleven, with scale, rotation and relief. Attached to the Surface "
                 "node, Blender lays it onto the building parts as a texture.",
    },
    "farbpalette": {
        "kurz": "05-colour-palette", "name": "Colour palette (Farbpalette)",
        "hilfe": "Up to four colours for the design; one of them tints the material.",
        "felder": [
            ("Colours", "Up to four colour swatches; the plus adds one."),
            ("Tints with (Tönt mit)", "Which colour tints the attached material (the lead colour)."),
            ("Strength (Stärke)", "How strongly the tint works, 0 to 1 (default 0.4)."),
        ],
        "fluss": [("aus", "material", "the colours and their phrase, e.g. “Helles Beige, Schiefergrau” (light beige, slate grey)")],
        "loest": "Blender mixes the lead colour into the texture. All colours become a phrase of colour words that "
                 "travels through Surface and Combiner into the prompt.",
        "verbunden": "Palette → Material, input “Palette”.",
        "grenze": "The colour words are rough; the AI reads words, not exact colour values. Without a Material node "
                  "in between, the palette goes nowhere.",
        "visbox": "As described.",
        "notiz": "Up to four colours; the chosen one tints the material, and all of them go to the AI as colour words.",
    },
    "referenz": {
        "kurz": "06-image-reference", "name": "Image reference (Bild-Referenz)",
        "hilfe": "A model to look at — an outside image for comparison or as a colour reference.",
        "felder": [
            ("Image address", "A web address or an embedded image; the node shows it."),
        ],
        "fluss": [("aus", "bild", "the reference image, unchanged")],
        "loest": "Nothing on the home PC. In Image comparison the reference stands next to the renders; in the "
                 "curation view (full screen for choosing) it serves for a colour match.",
        "verbunden": "Image → Image comparison, Bild 1–3.",
        "grenze": "It does not go onto a sheet (“nur Vorbild”, reference only) — it is not an image of this project. "
                  "It does not steer the style of the AI image.",
        "visbox": "As described.",
        "notiz": "A reference image for comparison or as a colour model. It does not go onto a sheet and does not "
                 "steer the style.",
    },
    "aufnahme": {
        "kurz": "07-viewport-capture", "name": "Viewport capture (Viewport-Aufnahme)",
        "hilfe": "Meant as a snapshot of a 3D design view — an image without rendering.",
        "felder": [
            ("Which capture", "“jüngste Aufnahme” (latest capture) or a named viewpoint."),
            ("Capture (Aufnehmen)", "Only says where the real button is; the node itself captures nothing."),
        ],
        "fluss": [("aus", "bild", "the capture — in Visbox there is none")],
        "loest": "Nothing on the home PC.",
        "verbunden": "Image → Image comparison.",
        "grenze": "Visbox has no 3D design view, so there is no capture: the node stays at “Noch keine Aufnahme” "
                  "(no capture yet). It is in the list so that graphs stay the same.",
        "visbox": "In the list, has no effect here, and says so.",
        "notiz": "Only a placeholder in Visbox: without a 3D design view there is no capture, and the node says so.",
    },
    "kameraAus3d": {
        "kurz": "08-camera-from-3d", "name": "Camera from 3D view (Kamera aus 3D-Ansicht)",
        "hilfe": "Meant to take over the view of an open 3D view as a camera.",
        "felder": [
            ("Take over camera (Kamera übernehmen)", "Reads eye, target and field of view of the 3D view — once, not continuously."),
        ],
        "fluss": [("aus", "kameras", "exactly one camera — in Visbox none")],
        "loest": "At the Render node only its camera would go into the order; if it carries none, nothing is ordered.",
        "verbunden": "Camera viewpoints (Kamera-Standpunkte) → Render.",
        "grenze": "Visbox has no 3D view; the node says “Keine 3D-Ansicht offen” (no 3D view open). For a fixed "
                  "view, use the Camera node with the “Blick” (view) tab.",
        "visbox": "In the list, has no effect here, and says so.",
        "notiz": "Only a placeholder in Visbox: without a 3D view it carries no camera. A fixed view is chosen "
                 "on the Camera node under “Blick” (view).",
    },
    "stimmung": {
        "kurz": "09-mood", "name": "Mood (Stimmung)",
        "hilfe": "Chooses light and mood — eight moods, each with its own sky image.",
        "felder": [
            ("Moods (Stimmungen)", "Morning, midday, evening, blue hour, overcast, fog, winter, white model; "
                                   "several means one image per mood."),
            ("Preview (Vorschau)", "The sky image of the chosen mood."),
            ("Rotate (Drehen)", "Off: the home PC places the sun to the side for each camera; on: a fixed angle."),
            ("Acts on (Wirkt auf)", "“Licht + Satz” (light and phrase, default), only light in Blender, or only the phrase for the AI."),
        ],
        "fluss": [("aus", "prompt", "the mood phrase, e.g. “Abendstimmung, warmes Licht” (evening mood, warm light)")],
        "loest": "The sky image (free, CC0) gives light, sun, shadows and reflections in Blender; sky and ground "
                 "up to the horizon match the mood. Each mood gets its own base image.",
        "verbunden": "Prompt → Prompt combiner, input “Stimmung”.",
        "grenze": "“Satz” (phrase) alone does not change the light. A variant with another mood takes longer, "
                  "because Blender computes again.",
        "visbox": "All eight moods with a sky image on the home PC.",
        "notiz": "Eight moods, each with its own sky image: light, sun and shadows in Blender, and a phrase for "
                 "the AI. Each mood gets its own base image.",
    },
    "prompt": {
        "kurz": "10-prompt", "name": "Prompt",
        "hilfe": "Free text that describes how the image should look.",
        "felder": [
            ("Style text (Stil-Text)", "A text field, e.g. “Sichtbeton, Herbstlaub” (fair-faced concrete, autumn leaves); saved on leaving it."),
        ],
        "fluss": [("aus", "prompt", "the text, word for word")],
        "loest": "Nothing by itself; Combiner and Render show it at once. If it names a different facade surface, "
                 "a variant computes its base image again with that surface.",
        "verbunden": "Prompt → Prompt combiner, input “Stil” (style), or directly to Render.",
        "grenze": "German text is translated on the home PC; unusual words can get lost. An empty prompt with an "
                  "AI step is rejected — the button says so beforehand.",
        "visbox": "As described.",
        "notiz": "Free text describing how the image should look; it is passed on word for word, usually to the "
                 "“Stil” (style) input of the combiner.",
    },
    "material": {
        "kurz": "11-surface", "name": "Surface (Oberfläche)",
        "hilfe": "Gives each kind of building part a surface: facade, roof, window, floor, others.",
        "felder": [
            ("Five inputs", "One Material node per kind of part (Fassade, Dach, Fenster, Boden, Übrige); doors count as “Übrige” (others)."),
            ("Assignment", "One line says which kind has which surface."),
            ("… mehr (more)", "Opens the phrases that go to the combiner."),
        ],
        "fluss": [("ein", "material", "one surface per kind (only from the Material node)"),
                  ("aus", "material", "the assignment and its phrases")],
        "loest": "The Render node orders the surfaces per kind of building part; Blender applies the textures, and "
                 "the base image already shows them. Whatever gets nothing keeps the surface from the model.",
        "verbunden": "Material → Fassade etc.; Material → Prompt combiner, input “Material”.",
        "grenze": "Which parts count as facade or roof, the home PC reads from the file; parts without a kind "
                  "keep their surface.",
        "visbox": "As described; wall layers as phrases do not exist in a project folder.",
        "notiz": "Gives facade, roof, window, floor and others one surface each. Whatever gets nothing keeps the "
                 "surface from the model.",
    },
    "kombinierer": {
        "kurz": "12-prompt-combiner", "name": "Prompt combiner (Prompt-Kombinierer)",
        "hilfe": "Joins mood, style and material into the text that really goes to the AI.",
        "felder": [
            ("Display", "Shows the finished prompt live; there is nothing to set."),
            ("… mehr (more)", "Opens the full text."),
        ],
        "fluss": [("ein", "prompt", "mood and style"), ("ein", "material", "phrases from the Surface node"),
                  ("aus", "prompt", "everything in one text")],
        "loest": "Nothing by itself. If the text changes, a finished image at the Render node is marked “veraltet” (out of date).",
        "verbunden": "Mood, Prompt and Surface feed in; output → Render, input “Prompt”.",
        "grenze": "It only strings the parts together (with commas, empty parts drop out); it does not resolve "
                  "contradictions between mood and style.",
        "visbox": "As described.",
        "notiz": "Joins mood, style and material into the text that goes to the AI — visible live. If it changes, "
                 "a finished image counts as out of date.",
    },
    "zahl": {
        "kurz": "13-number", "name": "Number (Zahl)",
        "hilfe": "A slider for one single value.",
        "felder": [
            ("Slider", "Default 0.8, from 0 to 1 in steps of 0.05; applies on release."),
        ],
        "fluss": [("aus", "zahl", "the value")],
        "loest": "At the Render node it becomes the geometry fidelity (how closely the AI follows the shape) or the "
                 "samples (computing steps per pixel in Blender).",
        "verbunden": "Wert (value) → Render, input “Geometrie-Treue” (geometry fidelity) or “Samples”.",
        "grenze": "If “Qualität gegen Zeit” (quality versus time) is chosen on the Render node, it applies instead "
                  "of the samples number. For samples the range 0 to 1 is too small.",
        "visbox": "As described.",
        "notiz": "A slider (default 0.8) for the geometry fidelity or the samples at the Render node.",
    },
    "render": {
        "kurz": "14-render", "name": "Render",
        "hilfe": "Orders the images from the home PC — only at the press of a button, never automatically.",
        "felder": [
            ("Preset", "A ready package: quick draft, presentation, night, interior — or none."),
            ("Resolution (Auflösung)", "1600 × 1000 (default) up to 4000 × 2667 pixels."),
            ("Quality vs. time", "“Qualität gegen Zeit”, quick to full; takes priority over the “Samples” number."),
            ("Sky / rotate", "One of Blender’s sky types or none; rotation in degrees."),
            ("Image tool (Bildwerkzeug)", "Which AI model paints (default Z-Image Turbo)."),
            ("Render base (Grundlage rendern)", "Step 1: Blender only — camera, geometry, light, surfaces, no AI."),
            ("Make variant (Variante erzeugen)", "Step 2: the AI paints starting from the base image; with a sketch “Bild aus Skizze erzeugen”."),
            ("Release (Freigeben)", "Only this click sends a waiting order to the home PC."),
            ("Cancel (Abbrechen)", "Stops a running order."),
            ("Base (Grundlage)", "ID and cameras of the base render, or “veraltet” (out of date) or “noch keine” (none yet)."),
            ("Seed (Startwert)", "The random number the AI starts from; “neu würfeln” (reroll) gives another."),
            ("Quality (Güte)", "Voll (full, default): large, starting from the base image; Vorschau (preview): quick and small, windows and shape not secured."),
            ("Line drawing", "“Strichzeichnung” orders a line drawing, without AI."),
            ("… mehr (more)", "Order form (facade, scene, season, people, free text) next to the node."),
            ("Image at the node", "AI image and base image side by side; click to enlarge, there “Exportieren” (export)."),
        ],
        "fluss": [("ein", "szene", "Scene (required)"), ("ein", "prompt", "Prompt"),
                  ("ein", "zahl", "geometry fidelity, samples"), ("ein", "kameras", "viewpoints"),
                  ("ein", "bild", "Sketch (only from Sketch from iPad)"), ("aus", "bild", "the latest image")],
        "loest": "Every order waits for “Freigeben” (release). Then the home PC computes per camera: Blender for "
                 "the base image, the AI starting from the base image (strength 0.5), then the shape check. Image "
                 "and verdict come back to the node; it remembers its latest image.",
        "verbunden": "Model, Combiner, Camera, Sketch feed in; Image → Variants or Image comparison.",
        "grenze": "Without the home PC nothing is computed. The preview does not yet start from the base image. "
                  "Models with an open licence paint freely and carry “Lizenz offen” (licence open). No interior views.",
        "visbox": "Every order waits in Visbox for “Freigeben” (release) — preview and base render too.",
        "notiz": "The node that orders from the home PC: first “Grundlage rendern” (render base, Blender only), then "
                 "“Variante erzeugen” (make variant, the AI paints from the base image). Every order waits for "
                 "“Freigeben” (release).",
    },
    "varianten": {
        "kurz": "15-variants", "name": "Variants (Varianten)",
        "hilfe": "Orders the Render node’s settings in every combination — with one click.",
        "felder": [
            ("Counter", "Says beforehand how many images there will be: viewpoints × moods × designs."),
            ("Viewpoints (Standpunkte)", "The camera’s directions; with a sketch, its viewpoint."),
            ("Moods (Stimmungen)", "The eight to tick (default evening)."),
            ("Designs (Entwürfe)", "Which model; in Visbox the current one."),
            ("Warning", "From twelve images on, with an estimated duration; no limit."),
            ("Thumbnails", "One preview per variant; browse, enlarge, pick one."),
            ("Order / Release all", "“Bestellen” and “Alle freigeben”: two clicks for the whole series."),
        ],
        "fluss": [("ein", "bild", "the Render node whose settings apply"),
                  ("aus", "bild", "all images of the series")],
        "loest": "One order per mood and design, with all viewpoints, in full quality. If the Render node’s base image fits, it is "
                 "used (also for part of its cameras); another mood or another facade surface gets its own base image.",
        "verbunden": "Render → Render; Bilder (images) → Image comparison, Bild 1 (shown there as a grid).",
        "grenze": "The time estimate is an assumption. Two surface variants with the same surface compute the "
                  "base image twice.",
        "visbox": "Viewpoints are the home PC’s directions; design is only the current model.",
        "notiz": "Orders every combination of viewpoints, moods and designs with one click; a counter says "
                 "beforehand how many images there will be.",
    },
    "vergleich": {
        "kurz": "16-image-comparison", "name": "Image comparison (Bildvergleich)",
        "hilfe": "Puts images side by side, each with its check verdict.",
        "felder": [
            ("Images", "A click enlarges an image; the large view stays inside the window when zooming."),
            ("Grid", "If Variants are attached: rows are viewpoints, columns are moods."),
        ],
        "fluss": [("ein", "bild", "up to three images or a variant series")],
        "loest": "Nothing — it only shows. Each image carries “QA ok”, “QA ✗”, “nicht beurteilbar” (cannot be "
                 "judged) or “QA nicht gemessen” (not measured), with the reason and, where needed, “Vorschau” "
                 "(preview) and “Lizenz offen” (licence open).",
        "verbunden": "Variants → Bild 1; Render, Sketch or Image reference → Bild 1–3.",
        "grenze": "At most three single images; more only as a grid. Choosing and exporting happen in the large "
                  "view or the curation view.",
        "visbox": "As described.",
        "notiz": "Shows images side by side, each with its check verdict; variants appear as a grid of "
                 "viewpoints and moods.",
    },
    "blatt": {
        "kurz": "17-onto-the-sheet", "name": "Onto the sheet (Aufs Blatt)",
        "hilfe": "Meant to place an image on a poster sheet.",
        "felder": [
            ("Title (Titel)", "The name on the sheet (default “Visualisierung”)."),
            ("Onto the sheet (Aufs Blatt)", "Active only with a finished image; takes the newest finished one."),
        ],
        "fluss": [("ein", "bild", "a finished image from a Render node")],
        "loest": "In Visbox the click ends with a sentence saying there are no sheets here.",
        "verbunden": "Render → Bild (image).",
        "grenze": "Poster sheets do not exist in Visbox. To keep an image, use “Exportieren” (export) in the large "
                  "view, at full resolution. A reference image never goes onto a sheet.",
        "visbox": "In the list, and says on click that there are no sheets here.",
        "notiz": "Only a placeholder in Visbox: poster sheets do not exist here. To keep an image, use "
                 "“Exportieren” (export) in the large view.",
    },
}

NOTIZ_UEBERSICHT_EN = ("Seventeen nodes in four groups, connected from output to input. Images are made in two "
                       "steps at the Render node — first the base image from Blender, then the AI variant — and "
                       "every order waits for the architect’s release.")


def _knoten_en() -> list[dict]:
    """Die englischen Karten: Aufbau (typ, gruppe, Anschlüsse, Quelle) aus :data:`KNOTEN`, Texte aus
    :data:`KNOTEN_EN_TEXT`. So kann eine Sprache keinen Anschluss haben, den die andere nicht hat."""
    aus = []
    for k in KNOTEN:
        en = KNOTEN_EN_TEXT[k["typ"]]
        aus.append({**k, **{f: en[f] for f in ("kurz", "hilfe", "felder", "fluss", "loest", "verbunden",
                                               "grenze")},
                    "name": en["name"], "visbox": (k["visbox"][0], en["visbox"])})
    return aus


KNOTEN_EN = _knoten_en()
NOTIZEN_EN = {"00-overview": NOTIZ_UEBERSICHT_EN,
              **{v["kurz"]: v["notiz"] for v in KNOTEN_EN_TEXT.values()}}

#: Feste Wörter der Karte je Sprache (Köpfe der Blöcke, Fuss, Übersicht).
TEXT = {
    "de": {"lang": "de", "fluss": "Was hinein- und herausfliesst", "verbunden": "Typisch verbunden",
           "felder": "Was man einstellt", "loest": "Was er auslöst", "grenze": "Ehrliche Grenze",
           "rein": "rein", "raus": "raus", "keine": "keine Anschlüsse", "quelle": "Quelle",
           "stand": "Stand der Knotenansicht", "blatt": "docs/KNOTEN_ERKLAERT.md", "wie_ui": ""},
    "en": {"lang": "en", "fluss": "What flows in and out", "verbunden": "Typically connected",
           "felder": "What you set", "loest": "What it triggers", "grenze": "Honest limit",
           "rein": "in", "raus": "out", "keine": "no connections", "quelle": "Source",
           "stand": "Node view version", "blatt": "docs/KNOTEN_ERKLAERT.en.md",
           "wie_ui": "Drawn as on screen — Visbox labels are in German."},
}


# ── HTML ────────────────────────────────────────────────────────────────────────────────

def _e(text: str) -> str:
    return html.escape(text, quote=True)


def _kopf_css() -> str:
    return f"""
@font-face {{ font-family: 'Plex'; src: url('{SANS.as_uri()}') format('truetype');
  font-weight: 100 700; font-stretch: 85% 100%; }}
@font-face {{ font-family: 'PlexMono'; src: url('{MONO.as_uri()}') format('truetype'); }}
:root {{ --grund: #12151c; --flaeche: #191d26; --flaeche2: #20252f; --linie: #2c3240;
  --tinte: #ece9e2; --leise: #a3abb9; --sehrleise: #6f7889; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ background: #000; }}
body {{ width: {BREITE}px; font-family: 'Plex', sans-serif; color: var(--tinte); }}
.karte {{ background: var(--grund); padding: 52px 60px 40px; }}
.oben {{ display: flex; align-items: baseline; gap: 18px; margin-bottom: 6px; }}
.nummer {{ font-family: 'PlexMono', monospace; color: var(--sehrleise); font-size: 22px; }}
.gruppe {{ font-size: 17px; letter-spacing: .14em; text-transform: uppercase; font-weight: 600; }}
h1 {{ font-size: 58px; font-weight: 600; letter-spacing: -.01em; line-height: 1.05; }}
.hilfe {{ font-size: 25px; color: var(--leise); margin-top: 10px; }}
.leib {{ display: grid; grid-template-columns: 440px 1fr; gap: 40px; margin-top: 34px; }}
.block {{ background: var(--flaeche); border-radius: 14px; padding: 20px 24px; }}
.block + .block {{ margin-top: 18px; }}
.block h2 {{ font-size: 15px; letter-spacing: .12em; text-transform: uppercase; color: var(--leise);
  font-weight: 600; margin-bottom: 8px; }}
.block p {{ font-size: 20px; line-height: 1.4; }}
.zwei {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-top: 18px; }}
.zwei .block {{ margin-top: 0; }}
.feld {{ display: grid; grid-template-columns: 210px 1fr; gap: 14px; font-size: 19px; line-height: 1.35;
  padding: 6px 0; border-top: 1px solid var(--linie); }}
.feld:first-of-type {{ border-top: none; }}
.feld b {{ font-weight: 600; }}
.felder-viele .feld {{ font-size: 17.5px; padding: 4px 0; grid-template-columns: 200px 1fr; }}
.zeile {{ display: flex; align-items: center; gap: 12px; font-size: 19px; line-height: 1.35;
  padding: 6px 0; border-top: 1px solid var(--linie); }}
.zeile:first-of-type {{ border-top: none; }}
.punkt {{ width: 15px; height: 15px; border-radius: 50%; flex: none; }}
.richtung {{ font-family: 'PlexMono', monospace; font-size: 15px; color: var(--sehrleise);
  width: 44px; flex: none; }}
.visbox {{ margin-top: 18px; border-radius: 14px; padding: 18px 22px; background: var(--flaeche2);
  border-left: 6px solid; }}
.visbox h2 {{ font-size: 15px; letter-spacing: .12em; text-transform: uppercase; font-weight: 600;
  margin-bottom: 6px; }}
.visbox p {{ font-size: 19px; line-height: 1.4; }}
.grenze {{ border-left: 6px solid #ffc21a; }}
.fuss {{ margin-top: 24px; display: flex; justify-content: space-between; gap: 24px; color: var(--sehrleise);
  font-size: 15px; font-family: 'PlexMono', monospace; }}
svg text {{ font-family: 'Plex', sans-serif; }}
"""


def _knoten_svg(k: dict, breite: int = 440, sprache: str = "de") -> str:
    """Der Knoten so gezeichnet, wie er in der Knotenansicht steht: Kopf mit Gruppenstreifen,
    Eingänge links, Ausgänge rechts, je in der Farbe ihrer Sorte."""
    farbe = GRUPPE_FARBE[k["gruppe"]][0]
    zeilen = max(len(k["ein"]), len(k["aus"]), 1)
    rand = 24
    kx, ky, kb = rand, 16, breite - 2 * rand
    kopf_h, abstand = 60, 46
    kh = kopf_h + 24 + zeilen * abstand
    h = ky + kh + 20
    teile = [f'<svg width="{breite}" height="{h}" viewBox="0 0 {breite} {h}" '
             'xmlns="http://www.w3.org/2000/svg">',
             f'<rect x="{kx}" y="{ky}" width="{kb}" height="{kh}" rx="14" fill="#1d222c" '
             'stroke="#353c4b" stroke-width="2"/>',
             f'<rect x="{kx}" y="{ky + kopf_h - 4}" width="{kb}" height="4" fill="{farbe}"/>',
             f'<text x="{kx + 22}" y="{ky + 39}" font-size="25" font-weight="600" '
             f'fill="#ece9e2">{_e(k["titel"])}</text>']
    for i, (name, sorte) in enumerate(k["ein"]):
        y = ky + kopf_h + 36 + i * abstand
        teile.append(f'<circle cx="{kx}" cy="{y}" r="10" fill="{PORT[sorte][0]}" '
                     'stroke="#12151c" stroke-width="3"/>')
        teile.append(f'<text x="{kx + 22}" y="{y + 7}" font-size="19" fill="#cfd4dd">'
                     f'{_e(name)}</text>')
    for i, (name, sorte) in enumerate(k["aus"]):
        y = ky + kopf_h + 36 + i * abstand
        teile.append(f'<circle cx="{kx + kb}" cy="{y}" r="10" fill="{PORT[sorte][0]}" '
                     'stroke="#12151c" stroke-width="3"/>')
        teile.append(f'<text x="{kx + kb - 22}" y="{y + 7}" font-size="19" fill="#cfd4dd" '
                     f'text-anchor="end">{_e(name)}</text>')
    if not k["ein"] and not k["aus"]:
        teile.append(f'<text x="{kx + 22}" y="{ky + kopf_h + 42}" font-size="18" '
                     f'fill="#6f7889">{_e(TEXT[sprache]["keine"])}</text>')
    teile.append("</svg>")
    return "".join(teile)


def _fluss_html(k: dict, sprache: str = "de") -> str:
    zeilen = []
    for art, sorte, text in k["fluss"]:
        farbe = PORT[sorte.lower()][0]
        pfeil = TEXT[sprache]["rein" if art == "ein" else "raus"]
        zeilen.append(f'<div class="zeile"><span class="richtung">{pfeil}</span>'
                      f'<span class="punkt" style="background:{farbe}"></span>'
                      f'<span>{_e(text)}</span></div>')
    return "".join(zeilen)


def karte_html(k: dict, nummer: int, sprache: str = "de") -> str:
    tx = TEXT[sprache]
    farbe, gruppenname = GRUPPE_FARBE[k["gruppe"]]
    ton, tontitel = VISBOX_TON[k["visbox"][0]]
    if sprache == "en":
        gruppenname = GRUPPE_FARBE_EN[k["gruppe"]]
        tontitel = VISBOX_TON_EN[k["visbox"][0]]
    titel = k.get("name", k["titel"]) if sprache == "en" else k["titel"]
    felder = "".join(f'<div class="feld"><b>{_e(n)}</b><span>{_e(t)}</span></div>'
                     for n, t in k["felder"])
    viele = " felder-viele" if len(k["felder"]) > 8 else ""
    wie_ui = (f'<div style="color:var(--sehrleise);font-size:15px;margin:-6px 0 0 24px">{_e(tx["wie_ui"])}</div>'
              if tx["wie_ui"] else "")
    return f"""<!doctype html><html lang="{tx['lang']}"><head><meta charset="utf-8">
<style>{_kopf_css()}{_kopf_css_sprache(sprache)}</style></head><body><div class="karte">
<div class="oben"><span class="nummer">{nummer:02d} / {len(KNOTEN)}</span>
<span class="gruppe" style="color:{farbe}">{_e(gruppenname)}</span></div>
<h1>{_e(titel)}</h1><div class="hilfe">{_e(k["hilfe"])}</div>
<div class="leib"><div>{_knoten_svg(k, sprache=sprache)}{wie_ui}
<div class="block" style="margin-top:14px"><h2>{_e(tx["fluss"])}</h2>{_fluss_html(k, sprache)}</div>
<div class="block"><h2>{_e(tx["verbunden"])}</h2><p>{_e(k["verbunden"])}</p></div>
<div class="visbox" style="border-color:{ton}"><h2 style="color:{ton}">{_e(tontitel)}</h2>
<p>{_e(k["visbox"][1])}</p></div></div>
<div><div class="block{viele}"><h2>{_e(tx["felder"])}</h2>{felder}</div>
<div class="zwei">
<div class="block"><h2>{_e(tx["loest"])}</h2><p>{_e(k["loest"])}</p></div>
<div class="block grenze"><h2>{_e(tx["grenze"])}</h2><p>{_e(k["grenze"])}</p></div>
</div></div></div>
<div class="fuss"><span>{_e(tx["quelle"])}: {_e(k["quelle"])}</span>
<span>{_e(tx["stand"])} {_kopie_stand()} · {_e(tx["blatt"])}</span></div>
</div></body></html>"""


def _kopf_css_sprache(sprache: str) -> str:
    """Englische Feldnamen tragen die Beschriftung in Klammern und sind länger: breitere Spalte."""
    if sprache != "en":
        return ""
    return """
.feld { grid-template-columns: 280px 1fr; }
.felder-viele .feld { grid-template-columns: 280px 1fr; }
"""


def _uebersicht_svg(sprache: str = "de") -> str:
    """Die typische Kette (der fertige Anfang, `start-graph.ts`): Quellen links, Wandler in der
    Mitte, Render und Varianten, Ausgabe rechts."""
    w, h = 1480, 560
    nb, nh = 236, 56
    pos = {  # (x, y, Gruppe) linke obere Ecke
        "Farbpalette": (10, 20, "quelle"), "Material": (10, 100, "quelle"),
        "Stimmung": (10, 180, "wandler"), "Prompt": (10, 260, "wandler"),
        "Modell": (10, 340, "quelle"), "Kamera": (10, 420, "quelle"),
        "Skizze vom iPad": (10, 500, "quelle"),
        "Oberfläche": (310, 100, "quelle"), "Prompt-Kombinierer": (580, 200, "wandler"),
        "Render": (880, 330, "render"), "Varianten": (1180, 250, "render"),
        "Bildvergleich": (1180, 440, "ausgabe"),
    }
    gruppe_von = {"Oberfläche": "wandler"}
    linien = [  # (von, nach, sorte, Eingangs-Versatz in y)
        ("Farbpalette", "Material", "material", 0, "unten"),
        ("Material", "Oberfläche", "material", 0, None),
        ("Oberfläche", "Prompt-Kombinierer", "material", 14, None),
        ("Stimmung", "Prompt-Kombinierer", "prompt", -14, None),
        ("Prompt", "Prompt-Kombinierer", "prompt", 0, None),
        ("Prompt-Kombinierer", "Render", "prompt", -30, None),
        ("Modell", "Render", "szene", -44, None),
        ("Kamera", "Render", "kameras", 10, None),
        ("Skizze vom iPad", "Render", "bild", 34, None),
        ("Render", "Varianten", "bild", 0, None),
        ("Varianten", "Bildvergleich", "bild", 0, "unten"),
    ]
    hoehe_von = {"Render": nh + 60}
    en = sprache == "en"
    teile = [f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">']
    for von, nach, sorte, dy, art in linien:
        x0, y0, _ = pos[von]
        x1, y1, _ = pos[nach]
        f = PORT[sorte][0]
        if art == "unten":  # senkrecht: unten aus, oben hinein
            a = (x0 + nb / 2, y0 + nh)
            b = (x1 + nb / 2, y1)
            teile.append(f'<path d="M{a[0]},{a[1]} L{b[0]},{b[1]}" stroke="{f}" stroke-width="4" '
                         'stroke-dasharray="2 0"/>')
        else:
            a = (x0 + nb, y0 + hoehe_von.get(von, nh) / 2)
            b = (x1, y1 + hoehe_von.get(nach, nh) / 2 + dy)
            m = (a[0] + b[0]) / 2
            teile.append(f'<path d="M{a[0]},{a[1]} C{m},{a[1]} {m},{b[1]} {b[0]},{b[1]}" fill="none" '
                         f'stroke="{f}" stroke-width="4"/>')
        teile.append(f'<circle cx="{b[0]}" cy="{b[1]}" r="7" fill="{f}"/>')
        teile.append(f'<circle cx="{a[0]}" cy="{a[1]}" r="7" fill="{f}"/>')
    for name, (x, y, gruppe) in pos.items():
        farbe = GRUPPE_FARBE[gruppe_von.get(name, gruppe)][0]
        hoehe = hoehe_von.get(name, nh)
        teile.append(f'<rect x="{x}" y="{y}" width="{nb}" height="{hoehe}" rx="12" fill="#1d222c" '
                     'stroke="#353c4b" stroke-width="2"/>')
        teile.append(f'<rect x="{x}" y="{y}" width="6" height="{hoehe}" rx="3" fill="{farbe}"/>')
        englisch = UEBERSICHT_EN.get(name, name) if en else name
        if en and englisch != name:  # englisch gross, darunter die Beschriftung wie am Bildschirm
            teile.append(f'<text x="{x + 20}" y="{y + 27}" font-size="20" font-weight="600" '
                         f'fill="#ece9e2">{_e(englisch)}</text>')
            teile.append(f'<text x="{x + 20}" y="{y + 47}" font-size="14" fill="#8f98a8">'
                         f'({_e(name)})</text>')
        else:
            teile.append(f'<text x="{x + 20}" y="{y + 36}" font-size="21" font-weight="600" '
                         f'fill="#ece9e2">{_e(englisch)}</text>')
        if name == "Render":
            z1, z2 = (("1 base · 2 variant", "each only after “Freigeben”") if en
                      else ("1 Grundlage · 2 Variante", "je erst nach «Freigeben»"))
            teile.append(f'<text x="{x + 20}" y="{y + 68}" font-size="16" fill="#ff8a70">{_e(z1)}</text>')
            teile.append(f'<text x="{x + 20}" y="{y + 92}" font-size="16" fill="#ff8a70">{_e(z2)}</text>')
        if name == "Skizze vom iPad":
            z = "optional: the sketch leads the image" if en else "wahlweise: die Skizze führt das Bild"
            teile.append(f'<text x="{x + nb + 14}" y="{y + 50}" font-size="16" fill="#a3abb9">{_e(z)}</text>')
    extra = (["Also as needed:", "Number → geometry fidelity,", "Image reference → comparison"] if en
             else ["Dazu nach Bedarf:", "Zahl → Geometrie-Treue,", "Bild-Referenz → Bildvergleich"])
    for i, z in enumerate(extra):
        teile.append(f'<text x="1180" y="{40 + 26 * i}" font-size="17" fill="#a3abb9">{_e(z)}</text>')
    teile.append("</svg>")
    return "".join(teile)


#: Namen der Übersicht: englisch, die Beschriftung wie am Bildschirm steht darunter.
UEBERSICHT_EN = {"Farbpalette": "Colour palette", "Modell": "Model", "Kamera": "Camera",
                 "Stimmung": "Mood", "Skizze vom iPad": "Sketch from iPad", "Oberfläche": "Surface",
                 "Prompt-Kombinierer": "Prompt combiner", "Varianten": "Variants",
                 "Bildvergleich": "Image comparison"}

UEBERSICHT_TEXT = {
    "de": {
        "gruppen": ["Modell, Kamera, Skizze, Material, Farbpalette, Referenz (+ 2 Stellvertreter)",
                    "Stimmung, Prompt, Oberfläche, Kombinierer, Zahl", "Render, Varianten",
                    "Bildvergleich (+ Aufs Blatt, Stellvertreter)"],
        "schritte": [
            ("1", "Grundlage rendern", "der Heim-PC rechnet mit Blender das Grundbild: Kamera, Form, Licht, Stoffe — ohne KI"),
            ("2", "Freigeben", "in Visbox wartet jeder Auftrag, bis der Architekt freigibt"),
            ("3", "Variante erzeugen", "die KI malt vom Grundbild aus (Stärke 0,5): Form, Fenster, Stoff bleiben"),
            ("4", "Freigeben", "wieder der Klick des Architekten — auch für eine ganze Variantenserie nur einer"),
            ("5", "Bild + Urteil", "zurück am Knoten und in der Mappe: Prüfurteil und «deckungsgleich» oder «Form weicht ab»"),
        ],
        "regeln": ("Linien führen vom <b>Ausgang</b> (rechts) zum <b>Eingang</b> (links). Nur <b>gleiche Sorte</b> "
                   "passt, manche Eingänge nehmen nur einen bestimmten Knoten. Ein Eingang hat <b>eine</b> Linie. "
                   "Nichts fliesst <b>im Kreis</b>. Einfache Knoten rechnen sofort; Render und Varianten erst auf "
                   "Knopfdruck. Unten rechts das <b>Lot</b>: der Assistent schlägt nur vor — anwenden und "
                   "freigeben kann allein der Architekt."),
        "kopf": "Übersicht", "h1": "Wie die Knoten von Visbox zusammenhängen",
        "hilfe": "Die typische Kette in der Knotenansicht — vom Modell bis zum geprüften Bild.",
        "h_regeln": "Die Regeln", "h_sorten": "Was durch die Linien fliesst", "h_gruppen": "Vier Gruppen",
        "h_weg": "Der Weg eines Bildes", "sorte_breite": 120,
    },
    "en": {
        "gruppen": ["Model, Camera, Sketch, Material, Colour palette, Reference (+ 2 placeholders)",
                    "Mood, Prompt, Surface, Combiner, Number", "Render, Variants",
                    "Image comparison (+ Onto the sheet, placeholder)"],
        "schritte": [
            ("1", "Render base", "“Grundlage rendern”: the home PC computes the base image with Blender — camera, shape, light, surfaces, no AI"),
            ("2", "Release", "“Freigeben”: in Visbox every order waits until the architect releases it"),
            ("3", "Make variant", "“Variante erzeugen”: the AI paints from the base image (strength 0.5); shape, windows, surface stay"),
            ("4", "Release", "the architect’s click again — only one, even for a whole series of variants"),
            ("5", "Image + verdict", "back at the node and in the project folder: check verdict and “deckungsgleich” (identical shape) or “Form weicht ab” (shape differs)"),
        ],
        "regeln": ("Lines run from an <b>output</b> (right) to an <b>input</b> (left). Only the <b>same kind</b> "
                   "fits, and some inputs accept only one particular node. An input has <b>one</b> line. Nothing "
                   "flows <b>in a circle</b>. Simple nodes compute at once; Render and Variants only at the press "
                   "of a button. Bottom right is the <b>Lot</b> (plumb line), the assistant’s sign: it only "
                   "suggests — only the architect can apply and release."),
        "kopf": "Overview", "h1": "How the nodes of Visbox fit together",
        "hilfe": "The typical chain in the node view — from the model to the checked image.",
        "h_regeln": "The rules", "h_sorten": "What flows through the lines", "h_gruppen": "Four groups",
        "h_weg": "The path of an image", "sorte_breite": 120,
    },
}


def uebersicht_html(sprache: str = "de") -> str:
    tx, ut = TEXT[sprache], UEBERSICHT_TEXT[sprache]
    en = sprache == "en"
    sorten = "".join(
        f'<div class="zeile"><span class="punkt" style="background:{f}"></span>'
        f'<span style="font-weight:600;width:{ut["sorte_breite"]}px;flex:none">{_e(PORT_EN[s][0] if en else n)}</span>'
        f'<span style="color:var(--leise)">{_e(PORT_EN[s][1] if en else t)}</span></div>'
        for s, (f, n, t) in PORT.items())
    gruppen = "".join(
        f'<div class="zeile"><span class="punkt" style="background:{f};border-radius:3px"></span>'
        f'<span style="font-weight:600;width:110px;flex:none">{_e(GRUPPE_FARBE_EN[g] if en else n)}</span>'
        f'<span style="color:var(--leise)">{_e(t)}</span></div>'
        for (g, (f, n)), t in zip(GRUPPE_FARBE.items(), ut["gruppen"]))
    weg = "".join(
        f'<div class="schritt"><div class="nr">{n}</div><div class="st">{_e(t)}</div>'
        f'<div class="sx">{_e(x)}</div></div>' for n, t, x in ut["schritte"])
    return f"""<!doctype html><html lang="{tx['lang']}"><head><meta charset="utf-8">
<style>{_kopf_css()}
.schritte {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; }}
.schritt {{ background: var(--flaeche); border-radius: 14px; padding: 18px 18px 20px; }}
.nr {{ font-family: 'PlexMono', monospace; color: #ff8a70; font-size: 18px; }}
.st {{ font-size: 22px; font-weight: 600; margin: 4px 0 6px; }}
.sx {{ font-size: 17px; line-height: 1.38; color: var(--leise); }}
.drei {{ display: grid; grid-template-columns: 1.15fr 0.95fr 1.1fr; gap: 18px; margin-top: 18px; }}
.drei .block {{ margin-top: 0; }}
.drei .zeile {{ font-size: 17px; }}
.block p b {{ color: var(--tinte); }}
.block p {{ font-size: 18.5px; }}
</style></head><body><div class="karte">
<div class="oben"><span class="nummer">00 / {len(KNOTEN)}</span>
<span class="gruppe" style="color:#ffc21a">{_e(ut["kopf"])}</span></div>
<h1>{_e(ut["h1"])}</h1>
<div class="hilfe">{_e(ut["hilfe"])}</div>
<div style="margin-top:20px">{_uebersicht_svg(sprache)}</div>
<div class="drei">
<div class="block"><h2>{_e(ut["h_regeln"])}</h2><p>{ut["regeln"]}</p></div>
<div class="block"><h2>{_e(ut["h_sorten"])}</h2>{sorten}</div>
<div class="block"><h2>{_e(ut["h_gruppen"])}</h2>{gruppen}</div></div>
<div class="block" style="margin-top:18px;background:transparent;padding:18px 0 0">
<h2>{_e(ut["h_weg"])}</h2><div class="schritte">{weg}</div></div>
<div class="fuss"><span>{_e(tx["quelle"])}: visgraph.ts · start-graph.ts · vis.ts (vis.verbinden) · grundlage.ts · vis-jobs.ts</span>
<span>{_e(tx["stand"])} {_kopie_stand()} · {_e(tx["blatt"])}</span></div>
</div></body></html>"""


# ── Bild ────────────────────────────────────────────────────────────────────────────────

def finde_chrome(vorgabe: str | None = None) -> str | None:
    if vorgabe:
        return vorgabe if Path(vorgabe).is_file() else None
    treffer = sorted(glob.glob("/opt/pw-browsers/chromium*/chrome-linux/chrome"))
    if treffer:
        return treffer[-1]
    for name in ("chromium", "chromium-browser", "google-chrome"):
        pfad = shutil.which(name)
        if pfad:
            return pfad
    return None


def zuschneiden(png: Path) -> tuple[int, int]:
    """Schneidet unten den schwarzen Rand weg (die Seite ist schwarz, die Karte nicht) und hält
    die Datei unter :data:`HOECHSTE_BYTES`. Gibt (Breite, Höhe) zurück."""
    from PIL import Image

    bild = Image.open(png).convert("RGB")
    b, h = bild.size
    grau = bild.convert("L")
    unten = h
    pixel = grau.load()
    for y in range(h - 1, -1, -1):
        if any(pixel[x, y] > 4 for x in range(0, b, 8)):
            unten = y + 1
            break
    bild = bild.crop((0, 0, b, unten))
    if max(bild.size) > HOECHSTE_SEITE:
        faktor = HOECHSTE_SEITE / max(bild.size)
        bild = bild.resize((round(bild.size[0] * faktor), round(bild.size[1] * faktor)),
                           Image.LANCZOS)
    bild.save(png, optimize=True)
    if png.stat().st_size > HOECHSTE_BYTES:
        bild.quantize(colors=256, method=Image.Quantize.MEDIANCUT).save(png, optimize=True)
    return bild.size


def rendere(html_pfad: Path, png: Path, chrome: str, hoehe: int = 1900) -> tuple[int, int]:
    subprocess.run(
        [chrome, "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
         "--force-device-scale-factor=1", f"--screenshot={png}",
         f"--window-size={BREITE},{hoehe + 300}", html_pfad.as_uri()],
        check=True, capture_output=True, timeout=120)
    return zuschneiden(png)


def karten(sprache: str = "de") -> list[tuple[str, str, str, str]]:
    """(kurzname, titel, notiz, html) für die Übersicht und alle Knoten (`KNOTEN` bzw. `KNOTEN_EN`)."""
    if sprache == "en":
        aus = [("00-overview", "Overview: How the nodes fit together", NOTIZEN_EN["00-overview"],
                uebersicht_html("en"))]
        for i, k in enumerate(KNOTEN_EN, start=1):
            aus.append((k["kurz"], f'Node {i:02d}: {k["name"]}', NOTIZEN_EN[k["kurz"]], karte_html(k, i, "en")))
        return aus
    aus = [("00-uebersicht", "Übersicht: Wie die Knoten zusammenhängen",
            NOTIZEN["00-uebersicht"], uebersicht_html())]
    for i, k in enumerate(KNOTEN, start=1):
        aus.append((k["kurz"], f'Knoten {i:02d}: {k["titel"]}', NOTIZEN[k["kurz"]],
                    karte_html(k, i)))
    return aus


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--ausgabe", default=str(Path(tempfile.gettempdir()) / "knoten-tafel"),
                    help="Ordner für HTML, PNG und JSON der Tafel (nicht im Repo).")
    ap.add_argument("--karte", default=None,
                    help="Nur diese Karte, z. B. render oder 00-uebersicht (Teil des Kurznamens).")
    ap.add_argument("--nur-html", action="store_true",
                    help="Nur HTML und JSON schreiben, kein Bild (ohne Chromium).")
    ap.add_argument("--chrome", default=None, help="Pfad zum Chromium, sonst gesucht.")
    ap.add_argument("--sprache", choices=SPRACHEN, default="en",
                    help="en (Vorgabe, Visbox-Dinge englisch, Entscheid 142) oder de (Fassung vom 23.10.2026).")
    a = ap.parse_args(argv)

    ziel = Path(a.ausgabe).resolve()
    ziel.mkdir(parents=True, exist_ok=True)
    datum, gruppe = (DATUM_EN, GRUPPE_EN) if a.sprache == "en" else (DATUM, GRUPPE)
    auswahl = [c for c in karten(a.sprache) if a.karte is None or a.karte in c[0]]
    if not auswahl:
        print(f"Keine Karte passt zu «{a.karte}».", file=sys.stderr)
        return 2
    chrome = None if a.nur_html else finde_chrome(a.chrome)
    if not a.nur_html and chrome is None:
        print("Kein Chromium gefunden — mit --chrome angeben oder --nur-html.", file=sys.stderr)
        return 3
    for kurz, titel, notiz, inhalt in auswahl:
        name = f"{datum}-knoten-{kurz}"
        (ziel / f"{name}.html").write_text(inhalt, encoding="utf-8")
        (ziel / f"{name}.json").write_text(
            json.dumps({"titel": titel, "gruppe": gruppe, "notiz": notiz}, ensure_ascii=False),
            encoding="utf-8")
        if chrome:
            groesse = rendere(ziel / f"{name}.html", ziel / f"{name}.png", chrome)
            kb = (ziel / f"{name}.png").stat().st_size // 1024
            print(f"{name}.png  {groesse[0]}×{groesse[1]}  {kb} KB")
        else:
            print(f"{name}.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
