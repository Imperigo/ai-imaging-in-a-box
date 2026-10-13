# Tiefenfilter der Splat-Brücke — Probe am synthetischen Strassenraum mit Person

**Codestand:** `05e58b4`

**Grundlage:** `auf-20261013-276` (echter Splat: gesprenkelte Tiefe, Person als Wolke vor den
Kameras, 497 497 Netzstücke, 69 % Inseln, Deckung 10 %); Auskunft der HomeStation zu den Masken
(13.10.2026); CPU-Ersatzrenderer im Scratch-venv (torch 2.14.1+cpu, gsplat 1.5.3 ohne CUDA,
open3d 0.20.0, numpy 2.4.6).

**Nur Probe.** Der Ersatzrenderer ist nicht gsplat, und der synthetische Splat ist nicht trainiert.
Die Zahlen sagen, ob die Filter das tun, wofür sie gebaut sind — nicht, wie das Netz am echten
Splat wird. Das misst die HomeStation.

## Aufbau

* Splat: `tools/make_test_splat.py --punkte 12000 --form strasse` (12 × 75 m), mit Person
  `--person 30`: je Augenblick 30 Gaussians (Körper und Arm), Deckkraft 0,6, an jedem Augenblick
  an anderer Stelle 0,7–1,0 m vom Rig; alle 80 Wolken zugleich im Splat. Die Person sind 18 % der
  dichten Punkte.
* Aufnahme: `tools/make_test_colmap.py --form strasse --person 30 --masken <lauf>/masks
  --ansichtsordner` — 80 Augenblicke × 4 Kameras; Masken je Bild schneiden **nur die Person
  dieses Augenblicks** aus (wie eine Personenmaske am Foto), `maske.json` dazu.
* Brücke: Blickwinkel aus der Aufnahme (240), Renderbreite 160, **Voxel 7 cm** (wie am echten
  Splat; bei 15 cm ist die Person dünner als zwei Voxel und entsteht gar nicht erst).
* Ersatzrenderer seit diesem Stand mit **erwarteter Tiefe** und akkumulierter Deckkraft wie gsplat
  (vorher: nächste Scheibe — damit lag die Person sauber auf sich selbst, und die Probe sah den
  Fehler aus 276 nicht).
* «Deckung Strasse»: Anteil der dichten Strassen-Gaussians (ohne Person) höchstens 3 Voxel vom
  Netz, nachgerechnet (`deckung.anteil` im Bericht zählt die Person mit).

## Ergebnis

| Lauf | Stücke | Inseln (Dreiecke) | Deckung Bericht | Deckung Strasse | verworfen |
|---|---:|---:|---:|---:|---:|
| ohne Person, kein Filter | 2 399 | 1,9 % | 95,4 % | 95,4 % | — |
| ohne Person, alle ausser Maske | 723 | 0,7 % | 92,1 % | 92,1 % | 15 % |
| **Person, kein Filter** | **8 989** | **6,1 %** | 77,8 % | 93,8 % | — |
| Person, nah | 8 827 | 6,0 % | 77,8 % | 93,8 % | 4 % |
| Person, maske | 7 411 | 4,9 % | 77,3 % | 93,1 % | 15 % |
| Person, nah + maske | 7 255 | 4,8 % | 77,3 % | 93,1 % | 18 % |
| Person, deckkraft | 9 056 | 6,7 % | 77,2 % | 92,9 % | 9 % |
| Person, sprenkel | 8 464 | 5,2 % | 77,2 % | 93,0 % | 3 % |
| **Person, streuung** | **762** | **0,9 %** | 75,6 % | 91,1 % | 19 % |
| Person, streuung + nah + weg | 761 | 0,9 % | 75,6 % | 91,1 % | 20 % |
| Person, alle ausser Maske | 789 | 1,0 % | 74,1 % | 89,2 % | 28 % |
| **Person, alle (Vorgabe)** | **860** | **1,1 %** | 73,2 % | 88,1 % | 38 % |

## Befunde

1. **Die Person zerlegt das Netz:** 2 399 → 8 989 Stücke, Inselanteil 1,9 % → 6,1 %. Die Fläche
   der Strasse selbst bleibt fast (95,4 % → 93,8 %): Die Fetzen sind zusätzlich, nicht anstelle.
2. **Nahbereich und Masken helfen hier kaum** (8 827 bzw. 7 255 Stücke). Grund: Eine halb
   durchsichtige Wolke 1 m vor der Kamera und eine Wand dahinter ergeben als **erwartete** Tiefe
   einen Wert in der Luft dazwischen — weit jenseits von 1,5 m, und von der eigenen Maske nur für
   die Person dieses Augenblicks erfasst. Das widerspricht der Erwartung im Auftrag («mit
   Nahbereich und/oder Masken gute Deckung») und wird hier so festgehalten.
3. **Die Streuung entlang des Strahls trägt:** 8 989 → 762 Stücke, Inseln 6,1 % → 0,9 % — unter
   den Stand ohne Person. Sie kostet 2,7 Punkte Deckung der Strasse (93,8 % → 91,1 %).
4. **Die Deckkraft-Schwelle schadet am synthetischen Splat:** mehr Stücke (9 056), weniger Fläche.
   Bei der zuerst gesetzten 0,9 verwarf sie 33 % der Bildpunkte, darum 0,7. Der synthetische Splat
   hat Lücken zwischen seinen Wölkchen; ob ein trainierter Splat ebenso leidet, sagt erst der
   Heim-PC.
5. **Alle sechs zusammen (die Vorgabe)** liegen bei 860 Stücken, kosten aber 5,7 Punkte Deckung
   der Strasse — mehr als die Streuung allein. Die Vorgabe bleibt «alle», weil der Auftrag sie so
   will und die Kosten am trainierten Splat anders sein können; der Vergleichslauf
   `tiefenfilter="streuung,nah,weg"` steht im Messauftrag.
6. **Ohne Person** halbiert die Vorgabe die Fetzen ebenfalls (2 399 → 723): Bei 7 cm ist der
   synthetische Splat zu dünn besetzt, und die Streuung nimmt die Ränder zwischen den Wölkchen weg.

## Was nur am Heim-PC prüfbar ist

* Ob der zweite gsplat-Durchgang für die Streuung (Merkmale `z`, `z²` je Kamera) auf der Karte
  läuft — `tiefenfilter.streuung_bilder`, `streuung_fehler`.
* Die Anteile je Filter am echten Splat (ohne Masken, er hat keine), Stücke, Inseln, Deckung und
  die Fläche neben dem Bauwerk im Bild — je mit `keine`, `streuung,nah,weg` und allen.
* Masken am Lauf, zu dem sie gehören (eigener Splat, eigenes `sparse/0`).
* Ob das Netz mit gsplat bei gleichem Schlüssel bitgleich bleibt.
