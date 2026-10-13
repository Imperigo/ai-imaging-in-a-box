# Visbox 0.2.0 — Fassungsblatt (13.10.2026)

**Codestand:** Fassung 0.2.0 auf `main` (dieser Commit); Vorgänger 0.1.0 = `c358b6d` (03.10.2026)

**Grundlage:** Owner-Entscheid 82 (13.10.2026, per Auswahl: «0.2.0 jetzt»); Messungen `auf-20261008-259` bis `auf-20261013-277`

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Das KosmoVis-Werkzeug in KosmoOrbit hat keine eigene Nummer; es gehört zur
KosmoOrbit-Fassung.

## Warum 0.2.0 und nicht 0.1.1

Seit 0.1.0 sind neue Fähigkeiten dazugekommen, nicht nur Behebungen: die Umgebung aus dem Splat im Bild, der
Messboden, die nähere Kamera für lange Bauten, Bestand ohne Schrift, die Brücke zu RealityScan.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| «Nicht beurteilbar», wenn das Haus unter 20 % des Bildes füllt — auch auf Fläche, iPad und Mac | 70 | am Gerät bestätigt (268), iPad/Mac: Mac-Prüfung grün |
| Standpunkt-Satz am Bild («Kein Standpunkt bestellt — von Süden gerechnet») | 73 | Fläche und iPad gebaut |
| Lange, flache Bauten als Ausschnitt — auch ohne Gelände | 75 | am Gerät bestätigt (272: alle 9 Kameras) |
| Rahmung nach dem Bauwerk bei glb über die Brücke (vorher nie angekommen) | — | am Gerät bestätigt (272: 62 % statt 5 %) |
| Bestand ohne Schrift (Zusatz am Bildauftrag) | — | gebaut; Wirkung ungemessen (0 gegen 1 Schriftzug bei 9 Bildern) |
| Umgebung (Splat) im Bild: ausgeblendet in der Prüfung, Tiefe nach dem Modell | 76, 77 | am Gerät bestätigt (272) |
| Splat → echtes Netz (gsplat + Open3D, eigene Umgebung `.venv-splat`), aus den Kamerastandorten der Aufnahme | 79 | am Gerät: Konfetti weg (275/276), Prüfung **3 von 3 bestanden** (276); **Deckung der Umgebung nur ~10 %** |
| Messboden (Modelle ohne Boden werden messbar; nur zum Trennen) | 78, 78a | am Gerät bestätigt (274, 276) |
| Brücke zu RealityScan (Umgebung aus den Fotos; nur vom Nutzer selbst installiert) | 79, 81 | gebaut; **wartet auf die Installation durch den Owner** (`auf-20261013-278`) |
| IFC-Oberflächenstile in die glb (F6) | — | am Gerät bestätigt (264/265) |

## Passende KosmoOrbit-Fassung

* **Mit KosmoOrbit 0.1.7** (veröffentlicht): Bilder, Prüfung, «nicht beurteilbar» als `passed: false` plus Satz.
  **Ohne** Verlauf am Render-Knoten und ohne Umgebung (Splat) in der Bestellung.
* **Mit KosmoOrbit 0.1.8** (offen): dazu der Verlauf (Zweig `claude/kosmovis-v018-verlauf-feinschliff`,
  `4e488412a`) und der Splat-Vertrag (`claude/kosmovis-v018-splat-context`, `ea2b2295e`) — beide an Int 1
  gemeldet und **eingespielt** in Runde 23 (Int 1, \`e40051731\`, ROADMAP 1760, 13.10.2026; Kern 4020, App 7219,
  Contracts 202, gezielte E2E 50/50, Wächter 71/71 grün). Am Gerät in der installierten 0.1.8 noch zu sehen.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Die Umgebung trägt im Bild wenig bei: Das Netz aus dem Splat deckt ~10 %, den Rest erfindet das Bildmodell.
  Tiefenfilter halfen am echten Splat nicht (277); Weg nach vorn: RealityScan (Entscheid 81).
* Die Mac-App ist übersetzt und in der Prüfstrecke grün, von einem Menschen gestartet wurde sie nicht
  (`auf-20261001-234`).
* Der lichtaktive Splat an Bauteilen ist eine Forschungsfrage, nicht gebaut.

## Prüfung

Volle Suite ohne GPU: **9650 Proben**, grün. iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml` (läuft mit diesem
Commit, weil die Nummer in `ipad/` steht).
