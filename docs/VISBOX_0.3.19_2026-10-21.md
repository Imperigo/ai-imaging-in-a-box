# Visbox 0.3.19 — Fassungsblatt (21.10.2026)

**Codestand:** Fassung 0.3.19 auf `main` (Vorschaubilder im Varianten-Knoten, Stilprobe am Bau, Probename im Gerätebuch); Vorgänger 0.3.18 = Tag `v0.3.18`

**Grundlage:** Blatt 36 der Entwurfsfläche; Befund 308 B1; Protokoll 74 §186–§192; Einbau-Stand C112–C115. Abgeglichen
gegen alle Änderungen seit `v0.3.18` (`git log v0.3.18..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.19

Der Varianten-Knoten zeigte keine Bilder, und eine verlorene Klammer in einer Gestaltungsdatei war durch alle Proben
gerutscht. Diese Fassung bringt die Bilder und eine Probe, die genau diesen Fehler künftig am fertigen Bau findet.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Der Varianten-Knoten zeigt ein Vorschaubild je Variante mit Stimmung und Standpunkt, blättert, öffnet gross und lässt eine Variante wählen; die Stimmungs-Achse rollt, damit alle acht Stimmungen erreichbar sind | — (Owner-Wunsch, Blatt 36) | gebaut, mit Probe; am Gerät unbestätigt |
| Die grosse Ansicht im Bildvergleich bleibt beim Zoomen im Fenster | — | gebaut, mit Probe |
| Stilprobe: jeder Bau der Knotenansicht wird auf offene Klammern und darauf geprüft, dass Inseln, Claude-Marke, Karten und Gesprächsfeld sichtbar gestaltet sind | 115 | gebaut, mit Probe; Pflicht in der Prüfstrecke |
| Proben der HomeStation laufen unter eigenem Gerätenamen und überschreiben das echte iPad nicht mehr | — (308) | gebaut, mit Probe; Messung 311 offen |

## Stand am Gerät

* **Mac:** Update-Knopf. Dann: im Varianten-Knoten mehrere Bilder bestellen — je Variante ein Vorschaubild, blättern,
  gross öffnen, «Diese Variante wählen».
* **Heim-PC:** `git pull`; am Rechnen ändert sich nichts. Proben bitte künftig mit `X-Geraet: ipad-probe`.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Einzelne Bedienteile im Kamera- und im Stimmungs-Knoten sehen wie in KosmoOrbit noch unruhig aus (grosse Formen,
  überlappende Beschriftungen); die Gestaltung liegt beim UI-Worker und kommt in beide Programme.
* Wohin eine gewählte Variante weitergeht (aufs Blatt, in den Bildvergleich), ist noch nicht entschieden.
* Kugel, Gespräch, Karten, Mappe am Mac und iPad über den Mac sind am Gerät weiter unbestätigt.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
