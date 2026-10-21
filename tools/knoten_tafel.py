#!/usr/bin/env python3
"""Bildkarten für die Kosmo-Tafel: was jeder Knoten des Vis-Werkzeugs kann.

**Wozu** (Owner, 14.10.2026): *«Ergänze auf der Kosmo-Tafel, was jedes einzelne Node kann, wie
es funktioniert, was es auslöst und wie es mit den anderen Nodes zusammenhängt.»* Die
ausführliche Fassung mit Quellen steht in ``docs/KNOTEN_ERKLAERT.md``; dieses Werkzeug zieht
daraus je Knotenart eine Karte und eine Übersichtskarte (die typische Kette vom Modell zum
geprüften Bild).

Die Karten sind **erzeugt, nicht abgelegt**: Die PNG-Dateien gehören nicht ins Repo, sondern auf
die Tafel (Zweig ``zentrale`` im KosmoOrbit-Repo, ``tafel/kosmovis/``). Wer einen Text ändert,
ändert ihn hier und in ``docs/KNOTEN_ERKLAERT.md`` und erzeugt neu.

So entsteht ein Bild: HTML schreiben (Schrift IBM Plex Sans, OFL, lokal aus
``ipad/Visbox.swiftpm/Schriften``, kein Netz) → Chromium ohne Fenster macht ein Bildschirmbild →
PIL schneidet es auf die Inhaltshöhe zu (sonst bliebe unten ein schwarzer Streifen) und hält es
unter 600 KB.

    python tools/knoten_tafel.py --ausgabe <ordner>
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
    """Der Stand der Visbox-Kopie (``kosmovis/HERKUNFT.json``), kurz — nicht fest im Text, weil
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
GRUPPE = "KosmoVis · Was die Knoten tun"
DATUM = "20261014"

# ── Farben ──────────────────────────────────────────────────────────────────────────────
# Anschlussfarben: die Werte des dunklen Themas aus `kosmovis/packages/kosmo-ui/src/aura.css`
# (`--k-port-*` im `[data-theme='orbit']`-Block; `kameras` ohne Überschreibung).
PORT = {
    "szene": ("#427ad5", "Szene", "das 3D-Modell"),
    "prompt": ("#278c5d", "Prompt", "Text: wie das Bild aussehen soll"),
    "material": ("#967740", "Material", "Materialsätze aus dem Modell"),
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
    "gleich": ("#1fd17a", "In Visbox wie in KosmoOrbit"),
    "teilweise": ("#ffc21a", "In Visbox mit Einschränkung"),
    "stellvertreter": ("#ffc21a", "In Visbox noch Stellvertreter"),
    "fehlt": ("#ff7a5c", "In Visbox ohne Wirkung"),
}

# ── Inhalt je Knoten ────────────────────────────────────────────────────────────────────
# Reihenfolge = Nummer auf der Tafel. Texte kurz; die Herleitung steht im Dokument.
KNOTEN: list[dict] = [
    {
        "kurz": "01-modell", "typ": "modell", "titel": "Modell", "gruppe": "quelle",
        "hilfe": "Das Gebäude als 3D-Szene — der Startpunkt jedes Renders.",
        "ein": [], "aus": [("Szene", "szene")],
        "kann": "Bringt das Gebäude als 3D-Szene in den Graphen. Am Knoten steht, wie viele "
                "Bauteile die Szene hat.",
        "wie": "Rechnet nichts. Seine Linie sagt dem Render-Knoten: «Diese Szene gehört zu dir.» "
               "Die 3D-Datei (glb) wird erst beim Absenden erzeugt bzw. geholt.",
        "loest": "Nichts von selbst. Ohne Linie vom Modell weigert sich der Render-Knoten; bei "
                 "0 Bauteilen ist «Ausführen» gesperrt.",
        "zusammen": [("aus", "Szene", "Render · Eingang Szene")],
        "visbox": ("teilweise",
                   "Das Modell kommt fertig aus der offenen Mappe und geht unverändert an die "
                   "Rechnung. Im Dokument steht dafür nur ein Bauteil, die gemessene Hüllbox — "
                   "darum zeigt der Knoten «1 Bauteile». Gerendert wird das ganze Modell."),
        "quelle": "visgraph.ts · NodeCanvas.tsx · visbox-knoten/src/mappe.ts",
    },
    {
        "kurz": "02-material", "typ": "material", "titel": "Oberfläche", "gruppe": "wandler",
        "hilfe": "Ordnet Materialien den Bauteil-Arten zu; liest dazu die Wandschichten.",
        "ein": [("Fassade", "material"), ("Dach", "material"), ("Fenster", "material"),
                ("Boden", "material"), ("Übrige", "material")],
        "aus": [("Material", "material")],
        "kann": "Ordnet jeder Bauteil-Art (Fassade, Dach, Fenster, Boden, Übrige) ein Material zu; was "
                "nichts bekommt, behält das Material aus dem Modell. Dazu macht er wie früher aus "
                "dem Modell kurze Sätze für die KI (Wandschicht, Boden, Sonne, Fassadenraster).",
        "wie": "Die Eingänge nehmen nur den Knoten «Material». Der Render-Knoten liest die Zuordnung "
               "über den Kombinierer und bestellt sie als Materialien je Bauteil-Art.",
        "loest": "Am Heim-PC bekommt jede zugeordnete Art in Blender die Textur des Materials; das "
                 "Bild der Grundlage zeigt sie schon. Türen zählen zu «Übrige».",
        "zusammen": [("ein", "Material", "Material · Ausgang Material, je Art"),
                     ("aus", "Material", "Prompt-Kombinierer · Eingang Material")],
        "visbox": ("gleich",
                   "Gleich wie in KosmoOrbit. Die Wandschichten fehlen in einer Visbox-Mappe; die "
                   "Zuordnung der Materialien wirkt voll."),
        "quelle": "visgraph.ts (oberflaecheMaterialien) · OberflaecheKnoten.tsx · materialwahl.py",
    },
    {
        "kurz": "03-auto-kamera", "typ": "kamera", "titel": "Kamera", "gruppe": "quelle",
        "hilfe": "Standpunkte: Auto rechnet der Heim-PC, Manuell von Hand gestellt.",
        "ein": [], "aus": [("Kamera-Standpunkte", "kameras")],
        "kann": "Auto: Richtungen, Augenhöhe, Brennweite, Abstand und Perspektive wählen — der Heim-PC "
                "stellt die Kameras. Manuell: die Auto-Standpunkte einfrieren und Auge und Blickpunkt "
                "in Metern tippen.",
        "wie": "Ein kleines 3D-Fenster zeigt das Modell mit einer Pyramide je Kamera, darunter den Blick "
               "aus einer Kamera; beides aus derselben Rechnung wie beim Rendern, live bei jeder Wahl.",
        "loest": "Auto bestellt «automatisch» mit den Einstellungen, Manuell eine Liste von Kameras mit "
                 "der Perspektive. Ohne Wahl wie früher: Standpunkte aus dem Modell.",
        "zusammen": [("aus", "Kameras", "Render · Eingang Kamera-Standpunkte"),
                     ("hilfe", "Kamera vorschlagen", "setzt ihn und hängt ihn an jeden Render")],
        "visbox": ("gleich",
                   "In Visbox kommen Pyramiden und Blick vom Visbox-Server; in KosmoOrbit rechnet "
                   "der Heim-PC sie erst beim Rendern."),
        "quelle": "visgraph.ts · KameraKnoten.tsx · heim-standpunkte.ts · knotenweg.standpunkte_abfrage",
    },
    {
        "kurz": "04-bild-referenz", "typ": "referenz", "titel": "Bild-Referenz", "gruppe": "quelle",
        "hilfe": "Ein Vorbild-Bild über seine Adresse.",
        "ein": [], "aus": [("Bild", "bild")],
        "kann": "Hält ein Vorbild: Man gibt eine Bildadresse ein, der Knoten zeigt das Bild.",
        "wie": "Speichert nur die Adresse und zeigt das Bild im Knoten.",
        "loest": "In der Kuratierfläche (Vollbild zum Auswählen) ist er Vorbild für einen "
                 "Farbangleich: ein Render bekommt die Farbstimmung der Referenz.",
        "zusammen": [("aus", "Bild", "Bildvergleich, Aufs Blatt — Linie ziehbar, trägt heute "
                                    "aber kein Bild weiter"),
                     ("hilfe", "Kuratierfläche", "Vorbild für den Farbangleich")],
        "visbox": ("teilweise",
                   "Wie in KosmoOrbit. Die Splat-Ansicht als Quelle ist in Visbox nicht "
                   "angeschlossen (keine Splat-Ebene im Dokument)."),
        "quelle": "visgraph.ts · NodeCanvas.tsx (bildQuelle) · KuratierFlaeche.tsx",
    },
    {
        "kurz": "05-viewport-aufnahme", "typ": "aufnahme", "titel": "Viewport-Aufnahme",
        "gruppe": "quelle",
        "hilfe": "Ein Schnappschuss der 3D-Ansicht — Bild ohne Rendern.",
        "ein": [], "aus": [("Bild", "bild")],
        "kann": "Eine echte Bildquelle ohne Rendern und ohne Heim-PC: ein Schnappschuss der "
                "3D-Ansicht im Entwurf.",
        "wie": "Das Bild entsteht im Entwurf über «Für Vis aufnehmen». Der Knoten zeigt die "
               "jüngste Aufnahme; sein Knopf «Aufnehmen» sagt nur, wo der echte Knopf sitzt.",
        "loest": "Nichts beim Heim-PC. Sein Bild geht an Vergleich oder Blatt und erscheint als "
                 "Karte in der Kuratierfläche.",
        "zusammen": [("aus", "Bild", "Bildvergleich · Bild 1–3, Aufs Blatt · Bild")],
        "visbox": ("fehlt",
                   "Visbox hat keine 3D-Entwurfsansicht, also keine Aufnahme. Der Knoten bleibt "
                   "bei «Noch keine Aufnahme»."),
        "quelle": "visgraph.ts · NodeCanvas.tsx · vis-runtime.ts (waehleAufnahme)",
    },
    {
        "kurz": "06-prompt", "typ": "prompt", "titel": "Prompt", "gruppe": "wandler",
        "hilfe": "Freier Stil-Text, z. B. «Sichtbeton, warmes Licht».",
        "ein": [], "aus": [("Prompt", "prompt")],
        "kann": "Ein Feld für freien Text, der beschreibt, wie das Bild aussehen soll.",
        "wie": "Der Text geht wortgleich an den Ausgang; gespeichert wird beim Verlassen des Feldes.",
        "loest": "Nichts von selbst. Kombinierer und Render zeigen den neuen Text sofort.",
        "zusammen": [("aus", "Prompt", "Prompt-Kombinierer · Eingang Stil"),
                     ("aus", "Prompt", "oder direkt Render · Eingang Prompt")],
        "visbox": ("gleich", "Gleich wie in KosmoOrbit."),
        "quelle": "visgraph.ts (evaluiereGraph) · NodeCanvas.tsx",
    },
    {
        "kurz": "07-stimmung", "typ": "stimmung", "titel": "Stimmung", "gruppe": "wandler",
        "hilfe": "Acht Stimmungen mit Himmelsbild: Licht in Blender und Satz für die KI.",
        "ein": [], "aus": [("Prompt", "prompt")],
        "kann": "Wählt Stimmungen: Morgen, Mittag, Abend, Blaue Stunde, Bedeckt, Nebel, Winter, Weiss. "
                "Der Himmel lässt sich fest drehen; die Wirkung geht auf Licht, Satz oder beides.",
        "wie": "Hinter jeder Stimmung liegt am Heim-PC ein Himmelsbild (CC0), das in Blender Licht und "
               "Spiegelungen gibt, und ein Satz für die KI. Der Render-Knoten bestellt die erste.",
        "loest": "Eine eigene Grundlage je Stimmung; zurück zur vorigen holt deren Grundlage wieder.",
        "zusammen": [("aus", "Prompt", "Prompt-Kombinierer · Eingang Stimmung"),
                     ("hilfe", "Drei Stimmungen einfügen", "baut drei Ketten mit je einer Stimmung")],
        "visbox": ("gleich", "Gleich wie in KosmoOrbit."),
        "quelle": "visgraph.ts (VIS_STIMMUNGEN) · StimmungKnoten.tsx · stimmung.py",
    },
    {
        "kurz": "08-kombinierer", "typ": "kombinierer", "titel": "Prompt-Kombinierer",
        "gruppe": "wandler",
        "hilfe": "Fügt Stimmung, Stil und Material zum finalen Prompt.",
        "ein": [("Stimmung", "prompt"), ("Stil", "prompt"), ("Material", "material")],
        "aus": [("Finaler Prompt", "prompt")],
        "kann": "Fügt Stimmung, Stil und Material zum finalen Prompt zusammen — live sichtbar.",
        "wie": "Reiht die drei Texte in dieser Reihenfolge mit Komma aneinander und lässt Leeres "
               "weg.",
        "loest": "Nichts von selbst. Ändert sich der Text, markiert der Render-Knoten ein schon "
                 "fertiges Bild als «veraltet».",
        "zusammen": [("ein", "Prompt", "Stimmung → Eingang Stimmung"),
                     ("ein", "Prompt", "Prompt → Eingang Stil"),
                     ("ein", "Material", "Material-Bausteine → Eingang Material"),
                     ("aus", "Prompt", "Render · Eingang Prompt")],
        "visbox": ("teilweise", "Gleich wie in KosmoOrbit — nur kommt vom Material-Knoten in "
                                "Visbox heute kein Text."),
        "quelle": "visgraph.ts · renderprompt.ts (finalerRenderPrompt)",
    },
    {
        "kurz": "09-zahl", "typ": "zahl", "titel": "Zahl", "gruppe": "wandler",
        "hilfe": "Ein Regler-Wert, Vorgabe 0,8 zwischen 0 und 1.",
        "ein": [], "aus": [("Wert", "zahl")],
        "kann": "Ein Regler für einen einzelnen Wert (Vorgabe 0,8, von 0 bis 1 in Schritten von 0,05).",
        "wie": "Der Wert geht beim Loslassen des Reglers an den Ausgang.",
        "loest": "Am Render-Knoten wird er zur Geometrie-Treue (wie eng die KI der Form folgt; "
                 "am Heim-PC die Stärke der Formführung) oder zu den Samples (Rechenschritte je "
                 "Bildpunkt). Ist am Render «Qualität gegen Zeit» gewählt, gilt diese.",
        "zusammen": [("aus", "Zahl", "Render · Eingang Geometrie-Treue"),
                     ("aus", "Zahl", "Render · Eingang Samples")],
        "visbox": ("gleich", "Gleich wie in KosmoOrbit."),
        "quelle": "visgraph.ts · vis-jobs.ts (sendeGraphRenderAuftrag) · kosmo_szene.py",
    },
    {
        "kurz": "10-render", "typ": "render", "titel": "Render", "gruppe": "render",
        "hilfe": "Bestellt das Bild beim Heim-PC — nur auf «Ausführen», nie automatisch.",
        "ein": [("Szene", "szene"), ("Prompt", "prompt"), ("Geometrie-Treue", "zahl"),
                ("Samples", "zahl"), ("Kamera-Standpunkte", "kameras"), ("Skizze", "bild")],
        "aus": [("Bild", "bild")],
        "kann": "Der einzige Knoten, der etwas bestellt. Eigene Einstellungen: Preset, Auflösung, "
                "Qualität gegen Zeit, Himmel, Umgebung drehen, Bildwerkzeug (KI-Modell, Vorgabe "
                "Z-Image Turbo), «nur Cycles», «Strichzeichnung» und ein Auftragsformular.",
        "wie": "Sammelt alles an seinen Eingängen und seine Einstellungen zu einem Auftrag. Der "
               "Prompt, der wirklich abgeht, steht immer sichtbar am Knoten.",
        "loest": "«Ausführen» → Auftrag an die Brücke → «wartet auf Freigabe» → «Freigeben» → "
                 "Abholer am Heim-PC: Vorlauf in Blender, Bild, Geometrie-Prüfung je Kamera → "
                 "Bild und Urteil zurück. Abbrechen jederzeit; nach 30 min ohne Ergebnis "
                 "«Zeitüberschreitung».",
        "zusammen": [("ein", "Szene", "Modell (Pflicht)"),
                     ("ein", "Prompt", "Kombinierer, Prompt oder Stimmung"),
                     ("ein", "Zahl", "Zahl → Geometrie-Treue / Samples"),
                     ("ein", "Kameras", "Auto-Kamera"),
                     ("aus", "Bild", "Bildvergleich, Aufs Blatt, Kuratierfläche")],
        "visbox": ("teilweise",
                   "Brücke ist der eigene Visbox-Server; jeder Auftrag wartet zuerst auf "
                   "«Freigeben». Gerechnet wird nur, wenn am Heim-PC der Abholer auf die Ablage "
                   "der Mappe schaut. Innenansichten bestellt dieser Weg nicht (braucht IFC)."),
        "quelle": "visgraph.ts · NodeCanvas.tsx · vis-jobs.ts · knotenweg.py · abholer.py",
    },
    {
        "kurz": "11-bildvergleich", "typ": "vergleich", "titel": "Bildvergleich", "gruppe": "ausgabe",
        "hilfe": "Bis zu drei Bilder nebeneinander, je mit Prüfurteil.",
        "ein": [("Bild 1", "bild"), ("Bild 2", "bild"), ("Bild 3", "bild")], "aus": [],
        "kann": "Stellt bis zu drei Bilder nebeneinander, jedes mit Prüfurteil: «QA ok», «QA ✗» "
                "oder «nicht beurteilbar», darunter der Grund und, wo nötig, «Lizenz offen».",
        "wie": "Holt für jeden Eingang das fertige Bild des verbundenen Render- oder "
               "Aufnahme-Knotens.",
        "loest": "Nichts — er zeigt nur. Ausgewählt und nachgearbeitet wird in der Kuratierfläche.",
        "zusammen": [("ein", "Bild", "Render oder Viewport-Aufnahme → Bild 1, 2, 3")],
        "visbox": ("gleich", "Gleich wie in KosmoOrbit."),
        "quelle": "visgraph.ts · NodeCanvas.tsx (BildKachel) · varianten-diff.ts (qaUrteil)",
    },
    {
        "kurz": "12-aufs-blatt", "typ": "blatt", "titel": "Aufs Blatt", "gruppe": "ausgabe",
        "hilfe": "Legt das Bild auf ein Plakatblatt in KosmoPublish.",
        "ein": [("Bild", "bild")], "aus": [],
        "kann": "Legt das verbundene Bild auf ein Plakatblatt in KosmoPublish — ein "
                "Rückgängig-Schritt, Titel einstellbar (Vorgabe «Visualisierung»).",
        "wie": "Der Knopf ist nur aktiv, wenn ein Bild anliegt. Er holt das Bild und setzt es auf "
               "einen freien Platz des Blatts.",
        "loest": "Einen Eintrag im Dokument und die Meldung «Render liegt auf …». Bei offener "
                 "Lizenz sagt die Meldung es mit.",
        "zusammen": [("ein", "Bild", "Render oder Viewport-Aufnahme")],
        "visbox": ("fehlt",
                   "Blätter gibt es in Visbox nicht. Der Klick endet mit dem Satz «Blätter gibt es "
                   "in Visbox nicht — kommt mit der Rückkehr nach KosmoOrbit wieder»."),
        "quelle": "visgraph.ts · vis-jobs.ts (bildAufsBlatt) · Stellvertreter commands/publish.ts",
    },
    # Seit Runde 29 und Entscheiden 95/95a (14.10.2026): zwei Zulieferer-Knoten, hinten angefügt,
    # damit die Nummern der zwölf Karten auf der Tafel bleiben.
    {
        "kurz": "13-kamera-aus-3d", "typ": "kameraAus3d", "titel": "Kamera aus 3D-Ansicht",
        "gruppe": "quelle",
        "hilfe": "Übernimmt den Blick, der in der 3D-Ansicht eingestellt ist.",
        "ein": [], "aus": [("Kamera-Standpunkte", "kameras")],
        "kann": "Trägt genau den Blick der 3D-Ansicht an den Render-Knoten — Position, Ziel und "
                "Blickfeld, ohne Objektiv-Shift.",
        "wie": "Liest die Kamera beim Anlegen und auf «Kamera übernehmen», nicht laufend, und "
               "speichert sie im Knoten. Das Blickfeld wird für das Bestellformat umgerechnet.",
        "loest": "Hängt er am Render-Knoten, geht nur seine Kamera in den Auftrag. Trägt er keine, "
                 "wird nicht bestellt.",
        "zusammen": [("aus", "Kameras", "Render · Eingang Kamera-Standpunkte")],
        "visbox": ("fehlt",
                   "Visbox hat keine 3D-Ansicht. Der Knoten sagt «Keine 3D-Ansicht offen», "
                   "statt eine Kamera vorzutäuschen."),
        "quelle": "visgraph.ts · derive/kamera-aus-3d.ts · KameraAus3dKnoten.tsx",
    },
    {
        "kurz": "14-skizze-vom-ipad", "typ": "skizzeIpad", "titel": "Skizze vom iPad",
        "gruppe": "quelle",
        "hilfe": "Die Skizze, die am iPad in die Mappe gelegt wurde.",
        "ein": [], "aus": [("Bild", "bild")],
        "kann": "Holt die Skizzen der Mappe in die Knotenansicht: von selbst die neueste, eine "
                "ältere ist am Knoten wählbar, mit Vorschaubild.",
        "wie": "Die Liste meldet das Programm, in dem die Knoten laufen. Die Wahl ist ein "
               "Parameter des Knotens und lässt sich rückgängig machen.",
        "loest": "Nichts beim Heim-PC. Der Render-Knoten nimmt heute kein Bild an; die Skizze "
                 "geht in den Bildvergleich (und in KosmoOrbit aufs Blatt).",
        "zusammen": [("aus", "Bild", "Bildvergleich · Bild 1–3, Aufs Blatt · Bild")],
        "visbox": ("gleich",
                   "In Visbox mit den Skizzen der offenen Mappe. In KosmoOrbit steht nur der "
                   "Satz, dass es Skizzen vom iPad in Visbox gibt."),
        "quelle": "visgraph.ts · skizze-quelle.ts · SkizzeKnoten.tsx · visbox-knoten/src/mappe.ts",
    },
    {
        "kurz": "15-varianten", "typ": "varianten", "titel": "Varianten",
        "gruppe": "render",
        "hilfe": "Bestellt die Einstellung des Render-Knotens in allen Kombinationen.",
        "ein": [("Render", "bild")], "aus": [("Bilder", "bild")],
        "kann": "Rechnet Standpunkte × Stimmungen × Entwürfe mit einem Klick, mit Zähler vorher und "
                "einer Freigabe für alle (Entscheide 92/92a/92b).",
        "wie": "Die drei Achsen hakt man am Knoten an; Vorgabe 3 Standpunkte × Abend × aktuelles "
               "Modell. Ab zwölf Bildern warnt er mit der ungefähren Dauer.",
        "loest": "Je Stimmung und Entwurf einen Auftrag beim Heim-PC, mit allen Standpunkten — "
                 "erst auf «Bilder bestellen» und «Alle freigeben».",
        "zusammen": [("ein", "Bild", "Render · Bild"), ("aus", "Bild", "Bildvergleich · Bild 1 (Raster)")],
        "visbox": ("gleich",
                   "In Visbox mit den drei Richtungen des Heim-PCs als Standpunkten und nur dem "
                   "aktuellen Modell als Entwurf; in KosmoOrbit auch Blicke und Ebenenkombinationen."),
        "quelle": "visgraph.ts · derive/varianten.ts · varianten.ts · VariantenKnoten.tsx · VariantenRaster.tsx",
    },
    {
        "kurz": "16-material", "typ": "materialTextur", "titel": "Material", "gruppe": "quelle",
        "hilfe": "Ein Stoff aus der Bibliothek der elf, mit Massstab, Drehung und Relief.",
        "ein": [("Palette", "material")], "aus": [("Material", "material")],
        "kann": "Wählt einen Stoff (Sichtbeton, Fichte, Backstein …) und zeigt ihn als Kugel, Würfel "
                "oder Fläche; Massstab, Drehung und Relief stellt man am Knoten.",
        "wie": "Die Texturen (CC0, ambientCG) liegen am Heim-PC; die App kennt nur die Kennung. Die "
               "Vorschau zeigt den Grundton, bis verkleinerte Bilder ausgeliefert sind.",
        "loest": "Nichts von selbst — an einem Eingang der Oberfläche geht er in die Bestellung.",
        "zusammen": [("ein", "Material", "Farbpalette · Ausgang Palette"),
                     ("aus", "Material", "Oberfläche · Eingang Fassade, Dach, Fenster, Boden oder Übrige")],
        "visbox": ("gleich", "Gleich wie in KosmoOrbit."),
        "quelle": "visgraph.ts (VIS_MATERIAL_BIBLIOTHEK) · OberflaecheKnoten.tsx · materialwahl.py",
    },
    {
        "kurz": "17-farbpalette", "typ": "farbpalette", "titel": "Farbpalette", "gruppe": "quelle",
        "hilfe": "Bis vier Farben; die gewählte tönt das Material.",
        "ein": [], "aus": [("Palette", "material")],
        "kann": "Hält bis zu vier Farben. Die Leitfarbe tönt das angehängte Material so stark wie "
                "eingestellt; alle Farben gehen als Satz an die KI.",
        "wie": "Aus jeder Farbe wird ein Wort («Helles Beige», «Schiefergrau»); der Satz reist über "
               "Oberfläche und Kombinierer in den Prompt.",
        "loest": "Am Heim-PC mischt Blender die Leitfarbe in die Textur des Materials.",
        "zusammen": [("aus", "Material", "Material · Eingang Palette")],
        "visbox": ("gleich", "Gleich wie in KosmoOrbit."),
        "quelle": "visgraph.ts (paletteAusParams, farbWort) · OberflaecheKnoten.tsx",
    },
]

#: Die Notiz neben jedem Bild auf der Tafel — zwei bis vier Sätze.
NOTIZEN = {
    "00-uebersicht": "Siebzehn Knoten in vier Gruppen. Linien führen vom Ausgang zum Eingang, nur "
                     "gleiche Sorte passt, nichts fliesst im Kreis. Nur der Render-Knoten bestellt "
                     "etwas beim Heim-PC, und erst auf «Ausführen» und «Freigeben».",
    "01-modell": "Bringt das Gebäude als Szene in den Graphen; ohne ihn rendert nichts. In Visbox "
                 "kommt das Modell fertig aus der Mappe, im Dokument steht nur seine Hüllbox.",
    "02-material": "Die Oberfläche ordnet Materialien den Bauteil-Arten zu; was nichts bekommt, behält "
                   "das Material aus dem Modell. Der Heim-PC legt die Texturen in Blender an.",
    "03-auto-kamera": "Auto: der Heim-PC stellt die Kameras nach Richtungen, Augenhöhe, Brennweite, "
                      "Abstand und Perspektive. Manuell: eingefroren und von Hand gestellt; Pyramiden "
                      "und Blick zeigen live, was bestellt wird.",
    "04-bild-referenz": "Hält ein Vorbild-Bild; in der Kuratierfläche dient es für den Farbangleich. "
                        "Eine Linie zu Vergleich oder Blatt trägt heute kein Bild weiter.",
    "05-viewport-aufnahme": "Schnappschuss der 3D-Ansicht als Bildquelle, ohne Heim-PC. In Visbox "
                            "gibt es keine 3D-Entwurfsansicht, der Knoten bleibt leer.",
    "06-prompt": "Freier Text, der wortgleich als Prompt weitergeht. Meist an den Eingang «Stil» "
                 "des Kombinierers.",
    "07-stimmung": "Acht Stimmungen mit Himmelsbild: Licht in Blender und ein Satz für die KI. Jede "
                   "Stimmung rechnet ihre eigene Grundlage.",
    "08-kombinierer": "Reiht Stimmung, Stil und Material zum finalen Prompt. Ändert er sich, wird ein "
                      "fertiges Bild am Render-Knoten als «veraltet» markiert.",
    "09-zahl": "Ein Regler (Vorgabe 0,8) für Geometrie-Treue oder Samples am Render-Knoten. Eine "
               "Wahl bei «Qualität gegen Zeit» schlägt die Zahl von der Linie.",
    "10-render": "Der einzige Knoten, der beim Heim-PC bestellt, nur auf «Ausführen». Danach: "
                 "Freigeben, der Abholer rechnet je Kamera Bild und Geometrie-Prüfung, Bild und "
                 "Urteil kommen zurück. In Visbox wartet jeder Auftrag auf «Freigeben».",
    "11-bildvergleich": "Bis zu drei Bilder nebeneinander, je mit Prüfurteil und Vorbehalt. Zeigt "
                        "nur, löst nichts aus.",
    "12-aufs-blatt": "Legt das Bild auf ein Plakatblatt in KosmoPublish. In Visbox gibt es keine "
                     "Blätter; der Klick sagt das.",
    "13-kamera-aus-3d": "Trägt den Blick der 3D-Ansicht als Kamera an den Render-Knoten, gelesen "
                        "beim Anlegen und auf Knopfdruck. In Visbox gibt es keine 3D-Ansicht, der "
                        "Knoten sagt das.",
    "14-skizze-vom-ipad": "Holt die neueste Skizze der Mappe in die Knotenansicht, eine ältere ist "
                          "wählbar. Der Render-Knoten nimmt noch kein Bild an — die Skizze geht in "
                          "den Bildvergleich.",
    "15-varianten": "Bestellt die Einstellung des Render-Knotens für alle Kombinationen aus "
                    "Standpunkten, Stimmungen und Entwürfen. Ein Zähler sagt vorher, wie viele Bilder "
                    "es werden, ein Klick gibt alle frei. Der Bildvergleich zeigt sie als Raster.",
    "16-material": "Ein Stoff aus der Bibliothek der elf mit Massstab, Drehung und Relief, als Kugel, "
                   "Würfel oder Fläche. Die Texturen liegen am Heim-PC.",
    "17-farbpalette": "Bis vier Farben; die Leitfarbe tönt das Material. Alle gehen als Satz an die KI.",
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
.karte {{ background: var(--grund); padding: 56px 64px 44px; }}
.oben {{ display: flex; align-items: baseline; gap: 18px; margin-bottom: 6px; }}
.nummer {{ font-family: 'PlexMono', monospace; color: var(--sehrleise); font-size: 22px; }}
.gruppe {{ font-size: 17px; letter-spacing: .14em; text-transform: uppercase; font-weight: 600; }}
h1 {{ font-size: 60px; font-weight: 600; letter-spacing: -.01em; line-height: 1.05; }}
.hilfe {{ font-size: 25px; color: var(--leise); margin-top: 10px; }}
.leib {{ display: grid; grid-template-columns: 470px 1fr; gap: 48px; margin-top: 40px; }}
.bloecke {{ display: grid; grid-template-columns: 1fr 1fr; gap: 22px; }}
.block {{ background: var(--flaeche); border-radius: 14px; padding: 24px 26px; }}
.block h2 {{ font-size: 16px; letter-spacing: .12em; text-transform: uppercase; color: var(--leise);
  font-weight: 600; margin-bottom: 10px; }}
.block p {{ font-size: 21px; line-height: 1.42; }}
.zusammen {{ grid-column: 1 / -1; }}
.zeile {{ display: flex; align-items: center; gap: 14px; font-size: 20px; line-height: 1.35;
  padding: 7px 0; border-top: 1px solid var(--linie); }}
.zeile:first-of-type {{ border-top: none; }}
.punkt {{ width: 16px; height: 16px; border-radius: 50%; flex: none; }}
.richtung {{ font-family: 'PlexMono', monospace; font-size: 15px; color: var(--sehrleise);
  width: 64px; flex: none; }}
.sorte {{ font-weight: 600; width: 190px; flex: none; }}
.visbox {{ margin-top: 22px; border-radius: 14px; padding: 20px 26px; background: var(--flaeche2);
  border-left: 6px solid; }}
.visbox h2 {{ font-size: 16px; letter-spacing: .12em; text-transform: uppercase; font-weight: 600;
  margin-bottom: 6px; }}
.visbox p {{ font-size: 20px; line-height: 1.42; }}
.fuss {{ margin-top: 26px; display: flex; justify-content: space-between; color: var(--sehrleise);
  font-size: 15px; font-family: 'PlexMono', monospace; }}
svg text {{ font-family: 'Plex', sans-serif; }}
"""


def _knoten_svg(k: dict, breite: int = 470) -> str:
    """Der Knoten so gezeichnet, wie er in der Knotenansicht steht: Kopf mit Gruppenstreifen,
    Eingänge links, Ausgänge rechts, je in der Farbe ihrer Sorte."""
    farbe = GRUPPE_FARBE[k["gruppe"]][0]
    zeilen = max(len(k["ein"]), len(k["aus"]), 1)
    rand = 26
    kx, ky, kb = rand, 20, breite - 2 * rand
    kopf_h, abstand = 64, 52
    kh = kopf_h + 28 + zeilen * abstand
    h = ky + kh + 24
    teile = [f'<svg width="{breite}" height="{h}" viewBox="0 0 {breite} {h}" '
             'xmlns="http://www.w3.org/2000/svg">',
             f'<rect x="{kx}" y="{ky}" width="{kb}" height="{kh}" rx="14" fill="#1d222c" '
             'stroke="#353c4b" stroke-width="2"/>',
             f'<rect x="{kx}" y="{ky + kopf_h - 4}" width="{kb}" height="4" fill="{farbe}"/>',
             f'<text x="{kx + 22}" y="{ky + 41}" font-size="26" font-weight="600" '
             f'fill="#ece9e2">{_e(k["titel"])}</text>']
    for i, (name, sorte) in enumerate(k["ein"]):
        y = ky + kopf_h + 40 + i * abstand
        teile.append(f'<circle cx="{kx}" cy="{y}" r="10" fill="{PORT[sorte][0]}" '
                     'stroke="#12151c" stroke-width="3"/>')
        teile.append(f'<text x="{kx + 22}" y="{y + 7}" font-size="20" fill="#cfd4dd">'
                     f'{_e(name)}</text>')
    for i, (name, sorte) in enumerate(k["aus"]):
        y = ky + kopf_h + 40 + i * abstand
        teile.append(f'<circle cx="{kx + kb}" cy="{y}" r="10" fill="{PORT[sorte][0]}" '
                     'stroke="#12151c" stroke-width="3"/>')
        teile.append(f'<text x="{kx + kb - 22}" y="{y + 7}" font-size="20" fill="#cfd4dd" '
                     f'text-anchor="end">{_e(name)}</text>')
    if not k["ein"] and not k["aus"]:
        teile.append(f'<text x="{kx + 22}" y="{ky + kopf_h + 46}" font-size="18" '
                     'fill="#6f7889">keine Anschlüsse</text>')
    teile.append("</svg>")
    return "".join(teile)


def _legende_html(k: dict) -> str:
    sorten = []
    for _, s in k["ein"] + k["aus"]:
        if s not in sorten:
            sorten.append(s)
    zeilen = "".join(
        f'<div class="zeile"><span class="punkt" style="background:{PORT[s][0]}"></span>'
        f'<span class="sorte">{_e(PORT[s][1])}</span><span style="color:var(--leise)">'
        f'{_e(PORT[s][2])}</span></div>' for s in sorten)
    return (f'<div class="block" style="margin-top:22px"><h2>Sorten an diesem Knoten</h2>'
            f'{zeilen or "<p>—</p>"}</div>')


def karte_html(k: dict, nummer: int) -> str:
    farbe, gruppenname = GRUPPE_FARBE[k["gruppe"]]
    ton, tontitel = VISBOX_TON[k["visbox"][0]]
    zus = []
    for art, sorte, text in k["zusammen"]:
        if art == "hilfe":
            zus.append(f'<div class="zeile"><span class="richtung">Knopf</span>'
                       f'<span class="sorte">{_e(sorte)}</span><span>{_e(text)}</span></div>')
            continue
        portfarbe = PORT[sorte.lower()][0] if sorte.lower() in PORT else "#888"
        pfeil = "← von" if art == "ein" else "→ an"
        zus.append(f'<div class="zeile"><span class="richtung">{pfeil}</span>'
                   f'<span class="punkt" style="background:{portfarbe}"></span>'
                   f'<span class="sorte">{_e(PORT[sorte.lower()][1])}</span>'
                   f'<span>{_e(text)}</span></div>')
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<style>{_kopf_css()}</style></head><body><div class="karte">
<div class="oben"><span class="nummer">{nummer:02d} / {len(KNOTEN)}</span>
<span class="gruppe" style="color:{farbe}">{_e(gruppenname)}</span></div>
<h1>{_e(k["titel"])}</h1><div class="hilfe">{_e(k["hilfe"])}</div>
<div class="leib"><div>{_knoten_svg(k)}{_legende_html(k)}</div>
<div><div class="bloecke">
<div class="block"><h2>Was er kann</h2><p>{_e(k["kann"])}</p></div>
<div class="block"><h2>Wie er funktioniert</h2><p>{_e(k["wie"])}</p></div>
<div class="block zusammen"><h2>Was er auslöst</h2><p>{_e(k["loest"])}</p></div>
<div class="block zusammen"><h2>Zusammenhang mit anderen Knoten</h2>{"".join(zus)}</div>
</div>
<div class="visbox" style="border-color:{ton}"><h2 style="color:{ton}">{_e(tontitel)}</h2>
<p>{_e(k["visbox"][1])}</p></div></div></div>
<div class="fuss"><span>Quelle: {_e(k["quelle"])}</span>
<span>KosmoVis {_kopie_stand()} · docs/KNOTEN_ERKLAERT.md</span></div>
</div></body></html>"""


def _uebersicht_svg() -> str:
    """Die typische Kette: Quellen links, Wandler in der Mitte, Render, Ausgabe rechts."""
    w, h = 1472, 600
    nb, nh = 262, 60
    pos = {  # (x, y) linke obere Ecke
        "Stimmung": (20, 20, "wandler"), "Prompt": (20, 112, "wandler"),
        "Material-Bausteine": (20, 204, "quelle"), "Modell": (20, 340, "quelle"),
        "Zahl": (20, 432, "wandler"), "Auto-Kamera": (20, 524, "quelle"),
        "Prompt-Kombinierer": (420, 112, "wandler"), "Render": (830, 250, "render"),
        "Bildvergleich": (1190, 150, "ausgabe"), "Aufs Blatt": (1190, 380, "ausgabe"),
    }
    linien = [  # (von, nach, sorte, Eingangs-Versatz in y)
        ("Stimmung", "Prompt-Kombinierer", "prompt", -14), ("Prompt", "Prompt-Kombinierer", "prompt", 0),
        ("Material-Bausteine", "Prompt-Kombinierer", "material", 14),
        ("Prompt-Kombinierer", "Render", "prompt", -20), ("Modell", "Render", "szene", -34),
        ("Zahl", "Render", "zahl", 6), ("Auto-Kamera", "Render", "kameras", 20),
        ("Render", "Bildvergleich", "bild", 0), ("Render", "Aufs Blatt", "bild", 0),
    ]
    teile = [f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">']
    for von, nach, sorte, dy in linien:
        x0, y0, _ = pos[von]
        x1, y1, _ = pos[nach]
        a = (x0 + nb, y0 + nh / 2)
        b = (x1, y1 + (nh + (50 if nach == "Render" else 0)) / 2 + dy)
        m = (a[0] + b[0]) / 2
        teile.append(f'<path d="M{a[0]},{a[1]} C{m},{a[1]} {m},{b[1]} {b[0]},{b[1]}" fill="none" '
                     f'stroke="{PORT[sorte][0]}" stroke-width="4"/>')
        teile.append(f'<circle cx="{b[0]}" cy="{b[1]}" r="7" fill="{PORT[sorte][0]}"/>')
        teile.append(f'<circle cx="{a[0]}" cy="{a[1]}" r="7" fill="{PORT[sorte][0]}"/>')
    for name, (x, y, gruppe) in pos.items():
        farbe = GRUPPE_FARBE[gruppe][0]
        hoehe = nh + (50 if name == "Render" else 0)
        teile.append(f'<rect x="{x}" y="{y}" width="{nb}" height="{hoehe}" rx="12" fill="#1d222c" '
                     'stroke="#353c4b" stroke-width="2"/>')
        teile.append(f'<rect x="{x}" y="{y}" width="6" height="{hoehe}" rx="3" fill="{farbe}"/>')
        teile.append(f'<text x="{x + 22}" y="{y + 39}" font-size="22" font-weight="600" '
                     f'fill="#ece9e2">{_e(name)}</text>')
        if name == "Render":
            teile.append(f'<text x="{x + 22}" y="{y + 76}" font-size="17" fill="#ff8a70">'
                         'nur auf «Ausführen»</text>')
    # Zwei Quellen ohne Platz in der Kette — als Randnotiz.
    teile.append('<text x="1190" y="500" font-size="18" fill="#a3abb9">Auch Bild-Quellen:</text>')
    teile.append('<text x="1190" y="528" font-size="18" fill="#a3abb9">Viewport-Aufnahme,</text>')
    teile.append('<text x="1190" y="556" font-size="18" fill="#a3abb9">Bild-Referenz</text>')
    teile.append("</svg>")
    return "".join(teile)


def uebersicht_html() -> str:
    sorten = "".join(
        f'<div class="zeile"><span class="punkt" style="background:{f}"></span>'
        f'<span class="sorte">{_e(n)}</span><span style="color:var(--leise)">{_e(t)}</span></div>'
        for f, n, t in PORT.values())
    gruppen = "".join(
        f'<div class="zeile"><span class="punkt" style="background:{f};border-radius:3px"></span>'
        f'<span class="sorte">{_e(n)}</span><span style="color:var(--leise)">{_e(t)}</span></div>'
        for (f, n), t in zip(GRUPPE_FARBE.values(),
                             ["Modell, Material, Auto-Kamera, Referenz, Aufnahme",
                              "Prompt, Stimmung, Kombinierer, Zahl", "Render",
                              "Bildvergleich, Aufs Blatt"]))
    schritte = [
        ("1", "Ausführen", "am Render-Knoten: Szene, Prompt, Zahlen, Kameras gehen als Auftrag ab"),
        ("2", "Brücke", "nimmt den Auftrag an — in Visbox der eigene Server, Ablage in der Mappe"),
        ("3", "Freigeben", "erst dieser Klick schickt ihn in die Reihe (Visbox: immer nötig)"),
        ("4", "Abholer am Heim-PC", "je Kamera: Vorlauf in Blender → Bild → Geometrie-Prüfung"),
        ("5", "Bild + Urteil", "zurück am Knoten: bestanden, durchgefallen oder nicht beurteilbar"),
    ]
    weg = "".join(
        f'<div class="schritt"><div class="nr">{n}</div><div class="st">{_e(t)}</div>'
        f'<div class="sx">{_e(x)}</div></div>' for n, t, x in schritte)
    regeln = ("Linien führen vom <b>Ausgang</b> (rechts) zum <b>Eingang</b> (links). Nur "
              "<b>gleiche Sorte</b> passt. Ein Eingang hat <b>eine</b> Linie — eine neue ersetzt "
              "die alte. Nichts fliesst <b>im Kreis</b>. Einfache Knoten rechnen sofort und "
              "live; der Graph liegt im Projekt und ist rückgängig machbar, Bilder nicht.")
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<style>{_kopf_css()}
.schritte {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; }}
.schritt {{ background: var(--flaeche); border-radius: 14px; padding: 20px 20px 22px; }}
.nr {{ font-family: 'PlexMono', monospace; color: #ff8a70; font-size: 18px; }}
.st {{ font-size: 23px; font-weight: 600; margin: 4px 0 6px; }}
.sx {{ font-size: 18px; line-height: 1.38; color: var(--leise); }}
.drei {{ display: grid; grid-template-columns: 1fr 1fr 1.2fr; gap: 22px; margin-top: 22px; }}
.block p b {{ color: var(--tinte); }}
</style></head><body><div class="karte">
<div class="oben"><span class="nummer">00 / {len(KNOTEN)}</span>
<span class="gruppe" style="color:#ffc21a">Übersicht</span></div>
<h1>Wie die Knoten zusammenhängen</h1>
<div class="hilfe">Die typische Kette im Vis-Werkzeug — vom Modell bis zum geprüften Bild.</div>
<div style="margin-top:24px">{_uebersicht_svg()}</div>
<div class="drei">
<div class="block"><h2>Die Regeln</h2><p>{regeln}</p></div>
<div class="block"><h2>Was durch die Linien fliesst</h2>{sorten}</div>
<div class="block"><h2>Vier Gruppen</h2>{gruppen}</div></div>
<div class="block" style="margin-top:22px;background:transparent;padding:22px 0 0">
<h2>Der Weg eines Render-Auftrags</h2><div class="schritte">{weg}</div></div>
<div class="fuss"><span>Quelle: visgraph.ts · vis.ts (vis.verbinden) · vis-jobs.ts · knotenweg.py · abholer.py</span>
<span>KosmoVis {_kopie_stand()} · docs/KNOTEN_ERKLAERT.md</span></div>
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


def karten() -> list[tuple[str, str, str, str]]:
    """(kurzname, titel, notiz, html) für die Übersicht und alle Knoten (`KNOTEN`)."""
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
    a = ap.parse_args(argv)

    ziel = Path(a.ausgabe)
    ziel.mkdir(parents=True, exist_ok=True)
    auswahl = [c for c in karten() if a.karte is None or a.karte in c[0]]
    if not auswahl:
        print(f"Keine Karte passt zu «{a.karte}».", file=sys.stderr)
        return 2
    chrome = None if a.nur_html else finde_chrome(a.chrome)
    if not a.nur_html and chrome is None:
        print("Kein Chromium gefunden — mit --chrome angeben oder --nur-html.", file=sys.stderr)
        return 3
    for kurz, titel, notiz, inhalt in auswahl:
        name = f"{DATUM}-knoten-{kurz}"
        (ziel / f"{name}.html").write_text(inhalt, encoding="utf-8")
        (ziel / f"{name}.json").write_text(
            json.dumps({"titel": titel, "gruppe": GRUPPE, "notiz": notiz}, ensure_ascii=False),
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
