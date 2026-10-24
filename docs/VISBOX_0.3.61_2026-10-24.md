# Visbox 0.3.61 — Fassungsblatt (24.10.2026)

**Codestand:** Fassung 0.3.61 auf `main` (Stärke je Bildart, «Freies Bild»); Vorgänger 0.3.60 = Tag `v0.3.60`

**Grundlage:** Ergebnisse 351, 353, 356; Owner-Entscheid 149 (mit Ergänzung am Abend); Protokoll 74 §290; Einbau-Stand
C207; Auftrag 357. Abgeglichen gegen alle Änderungen seit `v0.3.60` (`git log v0.3.60..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.61

Messung 353: Bei Stärke 0,5 war die Variante fast das Grundbild; bis 0,7 halten Fenster und Form. Am Wettbewerbsmodell
löste sich der Hauptbau bei 0,7 aber auf. Licht in den Fenstern, Wiese und Hügel bringt nur ein Bild ohne Grundbild.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Varianten ohne eigene Stärke rechnen mit 0,7 beim einzelnen Haus und mit 0,5 bei einer grossen Anlage (dieselbe Regel wie die Vogelschau) | 149 | gebaut, mit Probe; Messung 357 offen |
| «Freies Bild (ohne Grundbild)» am Varianten-Knoten und «Frei» am Render-Knoten — für ein Stimmungsbild; überall als «freies Bild» markiert | 149 | gebaut, mit Probe; am Mac offen |
| Nach «Freigeben» an der Stundengrenze steht kein veralteter Grenz-Vermerk mehr; «wieder frei ab» nennt die nächste volle Minute | 146 | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf, danach die Claude-Sitzung neu starten. Prüfen: Variante ohne eigene Stärke — Verlauf nennt 0,7;
  Haken «Freies Bild» — das Bild trägt die Marke «freies Bild».
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 357.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Ein freies Bild hält Form und Fenster nicht — die Sätze FORM und FENSTER stehen dann zu Recht da.
* Die Prüfung erkennt Formverlust nicht, wenn das Haus nur einen kleinen Teil des Bildes füllt.
* Als «Variante» gilt eine Bestellung mit Grundlage; ohne passende Grundlage rechnet sie wie ein erstes Bild mit 0,5.
* Im Umfeld-Knoten sind Zeilen noch abgeschnitten, und auf dem Wettbewerbsmodell stellt er noch nichts — Fixe folgen.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
