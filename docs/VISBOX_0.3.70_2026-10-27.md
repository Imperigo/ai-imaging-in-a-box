# Visbox 0.3.70 — Fassungsblatt (27.10.2026)

**Codestand:** Fassung 0.3.70 auf `main` (Demo-Fassung: Wiesenring im Gelände, Skizzenstärke 0,55, Daumen-Marke als Symbol);
Vorgänger 0.3.69 = Tag `v0.3.69`

**Grundlage:** Ergebnisse 370, 371; Owner-Entscheid 154; UI-Stand 112f3b495; Protokoll 74 §294 (Nachtrag), §297 (Nachtrag),
§298; Einbau-Stand C208, C211, C213; Auftrag 372. Abgeglichen gegen alle Änderungen seit `v0.3.69` (`git log v0.3.69..` ohne
Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.70

Messung 370: Am Wiesenring blieb eine Farbkante — der Ring bekam Gips, Materialwahl und Gelände-Grau nicht mit, die die
Platte danach erhält. Messung 371: Aus Strichen macht Z-Image Turbo keine Bauteile; bei 0,55 hält das Haus. Der Owner
entschied 0,55 als Vorgabe; Qwen wird für Skizzen ausdrücklich gewählt.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Der Wiesenring ist Teil des Geländes selbst und bekommt alles, was die Platte bekommt (Stoff, Farbe, Grau) | — | gebaut, mit Probe; Messung 372 offen |
| «Bild aus Skizze» rechnet ohne Wahl mit Z-Image Turbo und Stärke 0,55; der Hinweis sagt ehrlich, dass Striche Linien bleiben — für Bauteile Qwen wählen | 154 | gebaut, mit Probe |
| Fehlt das Schönbild der Unterlage, nimmt der Heim-PC zuerst das fertige Bild, die Vorschau zuletzt | — | gebaut, mit Probe |
| Die Modus-Marke am Varianten-Daumen ist ein Symbol; in der Markenleiste bricht kein Wort mitten durch | 115 | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf, danach Visbox ganz beenden und neu starten, Claude Desktop neu starten. Prüfen: `visbox_status`
  nennt 0.3.70.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 372.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Das Einfügen des Rings ins Gelände ist ohne Blender gebaut; scheitert es, bleibt der Ring ein eigenes Teil (mit Grund),
  und die Farbkante wäre wieder da — Messung 372 zeigt es.
* Aus Strichen macht nur Qwen-Image 2.1 Bauteile (ausdrücklich wählen; ohne Klick nach Entscheid 153).
* Am Render-Knoten steht noch der alte Satz «ob die Striche zu Bauteilen werden, ist ungemessen» (nach der Demo).
* Der Tooltip des Symbols am Daumen ist mit der Maus nicht erreichbar (U14, an den UI-Worker); der Knopf zeigt den vollen
  Wortlaut.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
