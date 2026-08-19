# Vorgehensplan

**Angelegt:** 2026-08-14 · **Stand:** Phasen 0–2 erledigt (2026-08-14 / 08-18), Phase 3
bis auf den ersten echten Render erledigt (beauftragt als `auf-20260818-06`)

Dieser Plan ist die verbindliche Reihenfolge. Er wird bei jeder Sitzung fortgeschrieben,
nicht ersetzt. Was erledigt ist, bleibt mit Datum stehen.

---

## Leitgedanke

Jede Phase muss **eine Annahme widerlegen können**. Eine Phase, die nur Funktionalität
hinzufügt, ohne etwas prüfbar zu machen, steht an der falschen Stelle.

Die Reihenfolge ergibt sich aus dem Risiko, nicht aus dem Nutzen: Zuerst das, dessen
Scheitern die Architektur umwerfen würde.

---

## Phase 0 · Feldnamen klären

**Aufwand:** klein · **Blockiert:** Phase 2, faktisch alles mit Schema

Der einzige Punkt, an dem Raten teuer wird. KosmoOrbit verdrahtet Knoten über
**Feldnamen-Gleichheit** — heisst unsere Eingabe anders als die Ausgabe des Vorgängers,
entsteht die Kante nicht, und zwar **ohne Fehlermeldung**.

- [x] `KosmoDraw` lesen: Ausgabefelder von `kosmodraw_export_ifc` — **erledigt 2026-08-14** (`8481ea8`)
- [x] MCP-Registrierungsweg — **erledigt 2026-08-14**, ohne `kosmo-backend`: `register_in_odysseus.sh` dokumentiert ihn vollständig
- [x] Feldnamen-Tabelle nachgetragen — `EINBINDUNG_KOSMOORBIT_2026-08-14.md` §8

**Fertig, wenn** die Namen belegt sind statt vermutet.

---

## Phase 1 · Das Skelett

**Aufwand:** mittel · **Zweck:** die Prozessgrenze beweisen, bevor etwas darauf steht

Der dünnste Pfad, der jede der vier Regeln einmal berührt. Fast ohne Funktionalität —
absichtlich. Bricht hier eine Annahme, ist es bei 500 Zeilen zu erfahren, nicht bei 5 000.

- [x] **Synthetische Testgeometrie** — erledigt: 8×5×3 m, deterministisch, stdlib-only
- [x] **IFC → glb** als Subprozess im eigenen `.venv-ifc` — ausgeführt: 5 Bauteile, 60 Dreiecke.
      *Der CGAL-Befund ist damit praktisch entschärft: GPL-Code läuft jenseits der Grenze.*
- [x] **glb → Blender headless → Tiefenkarte** — ausgeführt: EXR mit echten Meterwerten
      (27,3–39,5 m). *Regel 2 in der Praxis bestätigt.*
- [x] **Vertrag `render-scene.json`** — in `contracts.py`, `up_axis` als Pflichtfeld
- [x] **Tests ab der ersten Zeile** — 82 grün nach den Korrekturen
- [x] **`NOTICE`** — Blender GPL, IfcOpenShell LGPL, CGAL GPL deklariert

**Enthält bewusst nicht:** keine KI, kein Graph-Kern, kein MCP, keine QA.

**Fertig, wenn** aus Python heraus, ohne Oberfläche und ohne `import bpy`, aus einer
synthetischen IFC eine korrekte Tiefenkarte entsteht — und ein Test das festhält.

**Prüffragen der Phase — beantwortet 2026-08-18:**
- Trägt die Prozessgrenze in der Praxis? **Ja**, beide ausgeführt.
- Ist der Tiefen-Pass geometrisch korrekt? **Ja** — Blender meldet 8.0 x 5.0 x 3.25 m,
  exakt die IFC-Masse; die Kette Z-up → Y-up → Z-up ist verlustfrei.
- Bleibt das Produkt-venv frei von `bpy` und `ifcopenshell`? **Ja**, per Test bewacht.

**Offen geblieben, nach Phase 2 verschoben:** Massstabs- und Georeferenz-Torwächter
(mm-als-m, LV95 in float32) — Fehlerklasse bekannt, aber ungeprüft.

---

## Phase 2 · Kern und Naht

**Aufwand:** mittel · **Setzt voraus:** Phase 0 und 1

- [x] **Graph-Kern** — `graph.py`: typisierter DAG, stabile topologische Sortierung,
      Artefakt-Cache mit Content-Hashing, serialisierbar. Klein gehalten.
- [x] **Auftragsverwaltung** — `jobs.py`: Zustandsautomat mit Endzuständen, atomares
      Schreiben, Pfad-Trickserei abgewehrt. Das Token landet **nie** auf der Platte.
- [x] **MCP-Schicht** — drei Werkzeuge (`enqueue_render`, `query_render`,
      `check_geometry`), Verträge als reine Daten, Server als optionaler Zusatz.
- [x] Eingabe-Schemas **nicht** `additionalProperties: false` — per Test bewacht
- [x] **Torwächter** (aus Phase 1 verschoben) — `torwaechter.py`: mm-als-m und LV95

**Fertig, wenn** KosmoOrbit unsere Werkzeuge sieht, verdrahten kann und
`pipelineReadiness` keine toten Kanten meldet.

**Erledigt 2026-08-18.** KosmoOrbits Prüfung ist in `mcp_schemas.pruefe_verdrahtbarkeit`
nachgebaut und läuft in `tests/test_mcp_schemas.py` gegen die **echten** Ausgabeschemas
von `kosmodraw_export_ifc`, `_export_glb` und `_bim_layers`: keine toten Kanten, keine
fehlenden Pflichtfelder. 315 Tests grün.

*Ehrliche Grenze:* Das belegt die Verdrahtbarkeit, nicht die Registrierung. Ob Kosmo den
Server tatsächlich annimmt, lässt sich nur in der laufenden Umgebung prüfen — der Weg ist
aus `register_in_odysseus.sh` bekannt, aber hier nicht ausgeführt.

---

## Phase 3 · Bildkette und QA

**Aufwand:** gross · **Setzt voraus:** Phase 2

- [x] Multipass in Blender vollständig — Beauty, Material-ID (Goldener Winkel),
      Depth als EXR **und** normalisiertes PNG mit Rückrechnungsformel
- [x] **Multipass läuft auch auf Blender 5.2** — erledigt 2026-08-18 (Sitzung 07), auf
      der HomeStation gemessen. Der Weg dahin war kein Flicken: Die Normalisierung ist
      aus dem Runner auf die Produktseite gewandert (`bildschreiben.py`), weil Blender
      5.2 die Multilayer-EXR, die es schreiben **muss**, selbst nicht wieder einlesen
      kann. Zahlen identisch zu 4.2 bis auf 18 von 65 536 Bildpunkten à eine
      Quantisierungsstufe (float32 gegen float64).
- [x] **`art: "render"` im homeworker gebaut** — 2026-08-18. Multipass → Bildmodell →
      Tiefenschätzung → Geometrie-Score, jede Stufe berichtet einzeln. Zwei Test-Nähte
      machen den Pfad ohne GPU prüfbar.
- [x] Backbone-Adapter — `backbone.py`: Registry mit Lizenz je Modell.
      `waehle(kommerziell=True)` gibt FLUX-dev **nie** zurück — Regel 1 ausführbar.
- [x] **Renderstufe gebaut** — `render.py` über `diffusers` (Apache-2.0), Modell
      injizierbar, ohne GPU voll durchlaufbar. Regel 1 im Pfad: FLUX-dev wird abgelehnt.
- [x] **Bildlesen** — `bildlesen.py`: stdlib-EXR-Leser, **bitgleich** mit Blenders eigenen
      Zahlen; PNG-Rückrechnung auf 0,067 mm (= halber Quantisierungsschritt, reine Rundung).
      Blender nur als Rückfall für exotische Kompressionen. Warnt aktiv über den
      Silhouetten-Verlust im PNG — empirisch **genau ein** Punkt, und zwar der entfernteste.
- [x] **Ist-Seite der QA** — `tiefenschaetzer.py`: monokulare Schätzung als injizierbare
      Naht. Nur Depth-Anything-V2-**Small** (Apache-2.0) zulässig; Base/Large/Giant sind
      CC-BY-NC und ausgeschlossen. Fand den `geom_iou`-Deckel, der jeden treuen Render
      hätte durchfallen lassen.
- [x] **Graph-Kern verdrahtet** — `kette.py`: die Bildkette als DAG mit Zwischenspeicher.
      Belegt: Prompt-Änderung ruft die Geometriestufen **gar nicht mehr**, eine
      Geometrieänderung rechnet alles dahinter neu.
- [x] **Erster echter Render** — erledigt 2026-08-18 (`auf-20260818-09`).
      Qwen-Image-Edit-2511 mit echten Gewichten, Score **0,359** — durchgefallen
      (spearman −0,339, geom_iou 0,380). Der Adapter läuft; das Ergebnis ist ein
      Messwert, kein Fehlschlag.
      **Zwei Befunde wiegen schwerer als die Zahl:** (1) Der Vorgabe-Backbone ist über
      `QwenImageEditPlusPipeline` **kein Depth-ControlNet** — `controlnet_staerke` und
      `denoise` sind wirkungslos, die Tiefenkarte ersetzt den Beauty-Pass. Registry
      korrigiert. (2) Mein Prompt verlangte ein Dach („clean flat roof"), das die
      Geometrie nicht hat — *ein Prompt, der Bauteile nennt, die die Geometrie nicht hat,
      ist eine Aufforderung zur Halluzination.*
- [ ] **Ein Render, der besteht** — mit einem Prompt ohne Bauteile und einer Geometrie,
      die ein Gebäude ist statt einer offenen Schachtel. Bis dahin ist die Kette belegt,
      die Aussage „geometrietreu" aber noch nicht.
- [x] **Geometrie-Treue-QA** — `geometrie_qa.py`, an synthetischen Fällen belegt:
      treu 0.995, halluziniert **0.199** bei Spearman +1.000 und `geom_iou` 0.040.
      *Zahl berichtigt 2026-08-18 (Sitzung 07): Hier stand 0.24 bei IoU 0.057 — Werte
      einer früheren Fassung des Testfalls. Gemessen wurde gegen `test_geometrie_qa.py`,
      nicht gegen die Erinnerung.*
      **Und die Aussage „nur die Silhouette fängt ihn" gilt eingeschränkt:** Sie fängt
      eine **ersetzende** Halluzination (Bau steht woanders). Eine **ergänzende** —
      Zusatzkörper neben dem richtigen Bau — besteht mit 0.698, siehe Schwellenstudie.
- [x] Stil-QA als zweites Gate — `stil_qa.py`, Metrik testbar, Einbetter injizierbar
- [x] Doppel-Gate — `gate.py`: bestanden nur, wenn beide bestehen

**Fertig, wenn** ein Render gegen die Eingangsgeometrie messbar bewertet wird und eine
Halluzination nachweislich durchfällt.

**Stand 2026-08-18 (Sitzung 07):** Alles ohne GPU Machbare ist erledigt, jetzt
einschliesslich der Ausführungsstufe auf der HomeStation. Die Halluzination fällt
nachweislich durch — an **synthetischen** Tiefenkarten (Spearman +1.000, IoU 0.057,
Score 0.199). Was aussteht, ist ein **echter** Render durch ein Bildmodell; das braucht
GPU und Gewichte und ist als `auf-20260818-06` beauftragt.

---

## Phase 4 · Wissenschaftlicher Ausbau

- [x] **Schwellenstudie, erste Hälfte: die Metrik** — erledigt 2026-08-18,
      `schwellenstudie.py` + `docs/SCHWELLENSTUDIE_2026-08-18.md`. Acht Störungsarten ×
      sieben Stärken, jede mit einer prüfbaren Erwartung; alle 48 Zeilen erfüllen sie.
      **Drei Befunde:** (1) Die Rangbasiertheit ist *bestätigt* — streng monotone
      Umrechnung lässt den Score bei exakt 1,000; das war die einzige Prüfung, die die
      Metrik hätte umwerfen können. (2) **0,65 ist zu mild:** 18 von 32 auswertbaren
      gestörten Fällen gehen durch; bestes Ergebnis bei 0,90, über drei Auflösungen
      stabil; bis 0,85 wird **kein treuer Fall** gesperrt. (3) Verlorene Gliederung kostet
      **vier Tausendstel** — die Metrik misst Kubatur, nicht Detail.
      *Zwei Zahlen der ersten Auswertung waren falsch (Rasterdubletten, zu kleiner
      Zusatzkörper) — berichtigt, Kapitel 4a der Studie. Beide Fehler sassen in den
      Messinstrumenten, nicht in der Metrik.*
      *Die Schwelle bleibt trotzdem bei 0,65* — Begründung im Konstanten-Kommentar von
      `geometrie_qa`: ohne den Tiefenschätzer in der Messung wäre 0,90 nur schwächer
      unbegründet.
- [x] **Schwellenstudie, zweite Hälfte: die Kette** — erledigt 2026-08-18
      (`auf-20260818-10`, eine Stunde GPU). **Die Kette hat kein Signal mehr:** Nullprobe
      0.033 bei |spearman| 0.005; 22 von 24 gestörten Zeilen schneiden besser ab als die
      ungestörte Geometrie. Drei verschieden gestörte Vorgaben ergeben auf zwölf Stellen
      denselben Score.
      **Der Schätzer ist es nicht** — an Blenders eigenem Beauty-Pass |spearman| 0.990.
      Die Kette verliert an zwei getrennten Stellen: `geom_iou` deckelt schon beim
      perfekten Bild bei 0.261 (Obergrenze 0.509, damit ist 0.65 unerreichbar), und das
      Bildmodell drückt |spearman| von 0.990 auf 0.005.
      **Die Schwelle wurde nicht gesenkt** — eine Schwelle an eine kaputte Kette
      anzupassen hiesse, das Gate an das anzupassen, wogegen es schützen soll.
- [x] **Den `geom_iou`-Deckel beheben** — erledigt 2026-08-18 (`auf-20260818-12`, sechs
      Regeln gegeneinander gemessen). Gewonnen hat `ohne_randberuehrung`: Punkte auf dem
      Bauwerk **40.7 % → 99.2 %**, geom_iou 0.256 → 0.406, Score 0.504 → 0.635 — und der
      **grösste Abstand zum gestörten Fall** von allen sechs.
      **Die Messung war die ganze Arbeit wert.** `groesste_flaeche`, der naheliegendste
      Filter und der, den ich ohne Messung gebaut hätte, trifft **0 %**: Die grösste
      zusammenhängende Fläche der „nächsten n" *ist* der Hintergrundkeil. Und
      `nur_spearman_in_soll` sah mit 0.997 am besten aus, hat aber den **kleinsten**
      Abstand zwischen treu und gestört — die Sorte Verbesserung, die alles nach oben
      schiebt statt zu trennen.
- [ ] **Den Rest des Deckels** — auch der beste Kandidat erreicht am perfekten Bild nur
      0.635 und bleibt knapp unter 0.65. Ungemessen: Trägt eine Kombination
      (`ohne_randberuehrung` **plus** `rand_10`)? Und wie verhält sich die Regel an einer
      Szene mit **echtem Gelände**, wo eine Bodenebene keine Halluzination ist, sondern
      Geometrie?
- [ ] **Schwellenstudie, dritte Hälfte** — dieselben Störungen an einer Kette, die
      überhaupt ein Signal trägt. Sinnlos, bevor Deckel und Backbone stimmen.
- [ ] **(alt) Schwellenstudie, zweite Hälfte: die Kette** — dieselben Störungen, aber die
      Ist-Karte durch den Tiefenschätzer aus einem gerenderten Bild statt durch direkte
      Verfälschung. Erst danach lässt sich die Schwelle mit Grund verschieben.
      *Beauftragt 2026-08-18 als `auf-20260818-10`.* Die wichtigste Einzelzahl darin ist
      die **Nullprobe**: um wieviel senkt der Schätzer den Score bei *ungestörter*
      Geometrie? Sie sagt, wieviel von den 0,90 übrig bleibt.
- [x] **Übersetzung an der Naht** — erledigt 2026-08-18, `kosmo_naht.py` und
      `gate.als_kosmovis_verdikt`. Zwölf Feldabweichungen zum Ökosystem, jede eine tote
      Kante ohne Fehlermeldung. Übersetzt statt umbenannt: Unsere Begriffe bleiben
      deutsch, die Feldnamen an der Naht sind ein **Protokoll**.
      **Owner-Entscheid zum Freigabe-Token (2026-08-18):** Wir bleiben bei unserer Regel —
      das Token landet nie in einer Datei auf unserer Seite. `als_kosmo_auftrag` nimmt es
      als **Argument** und setzt es allein in den übersetzten Satz, im Augenblick des
      Übergangs.
- [x] **Ein Backbone mit echter ControlNet-Naht gesucht** — erledigt 2026-08-18,
      `docs/BACKBONE_CONTROLNET_2026-08-18.md`. Empfehlung: `z-image-turbo` +
      `alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union`, **beide Apache-2.0** — der
      einzige geprüfte Kandidat, bei dem die Regel-1-Spannung offen bleiben kann.
      22,0 GiB (resident), 8 Schritte statt 148 s.
      **Struktureller Befund:** Ein Depth-ControlNet ist immer **zwei** Modelle mit zwei
      Lizenzen; die Registry kannte nur eine und hat damit systematisch die halbe Naht
      geprüft. Bei FLUX sind alle drei verbreiteten Depth-ControlNets *selbst*
      nicht-kommerziell — ein permissives Basismodell hätte „zulässig" ergeben.
      Behoben: `controlnet_id`/`controlnet_lizenz`, dreiwertiges Urteil
      (`None` ≠ `True`). Dazu zwei Adapterfehler behoben — fehlendes `guidance_scale`
      (bei 0.0 wird der negative Prompt still ignoriert) und die SDXL-Falle, die eine
      **tragende** Naht als kaputt gemeldet hätte.
- [x] **Die Empfehlung am Gerät gemessen** — erledigt 2026-08-18 (`auf-20260818-13`).
      **Die Tiefenkonvention WAR invertiert.** Unsere Karte schreibt nah = hell, das
      ControlNet erwartet nah = dunkel; |spearman| springt dadurch von 0.38–0.52 auf
      0.79–0.85, bei jeder Stärke rund das Doppelte. Keine Modellkarte sagt das.
      **Z-Image hält die Geometrie, Qwen nicht:** -0.853 gegen +0.005 unter denselben
      Bedingungen. Rund hundertfach schneller (1.4 s statt 150 s je Bild), 23.4 GiB
      resident, und der Regler wirkt nachweislich — alle sechs Prüfsummen verschieden.
      Nicht monoton allerdings: 0.80 ist besser als 1.00.
      **Der Vorgabe-Backbone ist gewechselt**, und die Polarität ist jetzt ein Feld am
      Backbone statt einer Annahme. Gedreht wird nur bei erklärter Erwartung; bei
      `unbekannt` wird NICHT gedreht, aber gewarnt — raten hiesse, mit halber
      Wahrscheinlichkeit die Geometrie zu spiegeln.
- [ ] **Die Polarität der übrigen Backbones messen** — sechs Einträge stehen auf
      `unbekannt`. Für jeden gilt: Ein schlechter Score kann allein daran liegen.
- [ ] **Z-Image über mehrere Bauwerke prüfen** — ein Lauf, eine Szene, ein Seed. Dass es
      über verschiedene Baukörper trägt, ist nicht gezeigt.
- [ ] **Die auf-12-Auswahlregel gegen Z-Image messen** — der Score bleibt mit 0.265 weit
      unter der Schwelle, und das liegt an `geom_iou` (0.082), nicht am Backbone. Die
      HomeStation hat einen Nachbau der Regel ausdrücklich **verworfen**, weil er die
      Ausgabe des Moduls nicht traf: *„Ein Vergleich zwischen zwei Zahlen, von denen eine
      nicht die ist, für die ich sie halte, ist wertlos."* Die Regel gehört **in**
      `geometrie_qa` gemessen, nicht daneben nachgebaut.
- [x] **Die Stil-Schwelle am Gerät gemessen** — erledigt 2026-08-18 (`auf-20260818-11`).
      **0.30 war gar kein Gate:** Der Boden von SigLIP 2 base liegt bei 0.526 ± 0.070,
      die Schwelle lag 3.24 Streuungen darunter, und **alle 4950 geprüften Paare
      bestanden**. Der überlieferte Fehlbereich 0.06–0.13 war der Boden von DINOv3 und ist
      beim Einbetterwechsel stillschweigend mitgewandert.
      Die Schwelle ist jetzt abgeleitet (`Boden + k · Streuung` = 0.666), der Schlüssel
      ist Einbetter **und** Ausleseort, und `stil_gate` wirft, wenn eine Schwelle unter
      dem gemessenen Boden liegt — damit kann derselbe Fehler nicht wiederkehren.
- [ ] **Die zweite Hälfte der Stil-Kalibrierung** — der Boden ist gemessen, `k = 2` ist
      gesetzt. Es fehlen Paare, die stilistisch **ähnlich sein sollen**, und ein
      menschliches Urteil darüber. Der Boden sagt, wo Unähnlichkeit aufhört, nicht wo
      Ähnlichkeit anfängt.
- [ ] **(alt) Die Stil-Schwelle 0.30** — untersucht 2026-08-18 (`stilstudie.py`,
      `docs/STILSTUDIE_2026-08-18.md`), aber **nicht** entschieden. Die Studie zeigt, wovon
      die Bedeutung der Zahl abhängt: vom **Boden** des Einbetters, und der ist
      ungemessen. Bei Kegelanteil 0,6 läge er bei 0,36 — *über* der Schwelle, jedes
      beliebige Bildpaar bestünde. Und der überlieferte Fehlbereich 0,06–0,13 deckt sich
      mit dem Boden eines Kegels von rund 0,3: Er könnte der Boden von **DINOv3** gewesen
      sein statt eine Messung. Der Einbetter hat gewechselt, die Zahl nicht.
      *Beauftragt als `auf-20260818-11`.* Was die Schwelle braucht, ist kein besserer
      Wert, sondern ein **Verfahren**: Boden messen, Schwelle relativ setzen. Das
      überlebt einen Modellwechsel — genau daran ist 0,30 gescheitert.
- [x] **Connectors, erste Hälfte** — erledigt 2026-08-18, `herkunft.py`. Ein Connector
      ist hier **kein Import-Filter** (IFC und glTF liest das Projekt längst), sondern die
      Antwort auf die zwei Fragen, die zwischen Autorenprogrammen wirklich verschieden
      ausfallen: *in welcher Einheit sind die Zahlen, und wo ist oben?*
      **ArchiCAD über IFC4 braucht keine Umrechnung — gemessen, nicht angenommen.** Eine
      realistische Millimeter-Datei (`.MILLI.` **und** tausendfach grössere Koordinaten)
      läuft durch `ifc_zu_glb` und kommt bei exakt 8,0 × 5,0 × 3,25 m heraus;
      IfcOpenShell wendet den Faktor selbst an. *Die Annahme, die dieses Modul auslöste,
      war falsch, und sie ist im Modul-Docstring als widerlegt stehengelassen.*
      Geblieben ist der Fall, den es wirklich gibt: der **kaputte Export**, der Millimeter
      erklärt und metergrosse Zahlen trägt. Den fing der `torwaechter` schon — aber nur
      als *Verdacht*. `pruefe_einheit_gegen_masse` macht daraus eine **Diagnose**.
      Für glTF bleibt die Up-Achse offen, und das mit Absicht: **Rhino** ist der ehrlichste
      Eintrag der Registry — sein Exporter hat einen Schalter, den die Datei nicht
      mitteilt. `fordere_up_axis` nimmt eine *Vermutung* darum nicht an; sie wäre ein
      Default mit besserer Begründung, und Phase 0 wollte an dieser Stelle keinen.
- [x] **Connectors, zweite Hälfte** — erledigt 2026-08-18 (`auf-20260818-08`), an **40
      echten IFC-Dateien**. 40/40 gedeutet, 40/40 Erzeuger erkannt, **kein einziges
      `herkunft: null`**, kein einziger `HerkunftError`. Drei Erzeuger in freier
      Wildbahn: IfcOpenShell (28), ArchiCAD (10), Revit (2).
      **Zwei echte kaputte Exporte gefunden** — Millimeter erklärt, Meter geliefert.
      Nicht theoretisch: 2 von 40. Genau der Fall, für den
      `pruefe_einheit_gegen_masse` gebaut wurde.
      *Ehrliche Grenze:* Alle 40 stammen aus **einem** Büro. Dass Rhino, Vectorworks oder
      Allplan erkannt werden, ist damit **nicht** belegt.
- [x] **Connector an echten Dateien geprüft** — erledigt 2026-08-18 (`auf-20260818-08`).
      40 IFC aus echten Projekten: 40 von 40 gedeutet, 40 von 40 Erzeuger erkannt, kein
      `herkunft: null`, kein `HerkunftError`. IfcOpenShell 28, ArchiCAD 10, Revit 2.
      IFC4 30-mal, IFC2X3 10-mal. **Zwei echte kaputte Exporte gefunden** — Millimeter
      erklärt, Meter geliefert.
      **Der Befund, der zählt, liegt daneben:** Die Erkennung war Glück. In zwei von drei
      Fällen trägt Feld 5 (`preprocessor_version`) den Namen der *Exportbibliothek*, nicht
      des Programms — `DDS_IFC` für ArchiCAD, `ODA SDAI` für Revit. Hiesse eine
      Bibliothek einmal „Rhino…", ergäbe Feld 5 eine **falsche** Herkunft, und die ist
      schlimmer als keine: Sie schlägt dem Torwächter eine Up-Achse zur Bestätigung vor.
      Erkannt wird jetzt aus Feld 6 (`originating_system`) zuerst.
- [ ] **Connectors: die übrigen Autorenprogramme** — Rhino, Vectorworks, Allplan. Die
      Registry führt sie teils, gesehen hat sie keines: Alle 40 geprüften Dateien stammen
      aus **einem** Büro und damit aus einer eingeschränkten Werkzeuglandschaft. Rhino
      bleibt der Sonderfall: Seine Up-Achse ist an der Datei gar nicht entscheidbar.
- [x] **LoRA-Stiltraining als Subprozess-Naht** — erledigt 2026-08-18, `lora.py`.
      Beide Trainer sind jetzt **am Original geprüft** statt aus Sekundärquelle:
      kohya-ss/sd-scripts Apache-2.0, ostris/ai-toolkit MIT.
      **Das ist die einzige Stelle im Projekt, an der Regel 1 und Regel 3 gleichzeitig
      greifen** — und beide sind hier ausführbar:
      *Regel 1:* Ein LoRA ist eine Differenz zu den Gewichten seiner Grundlage und erbt
      deren Lizenzlage. Ein auf FLUX-dev trainierter Haus-Stil ist nicht verwertbar, und
      daran ändert weder das Eigentum an den Bildern noch die Rechenzeit etwas.
      `pruefe_auftrag` lehnt das **vor der ersten GPU-Sekunde** ab.
      *Regel 3:* Ein Stil-LoRA wird auf echten Bürobildern trainiert — das ist sein
      Zweck und genau das, was nie ins Repo darf. Datensatz **und** Ausgabe innerhalb des
      Repos werden abgewiesen, über `Path.resolve`, damit ein `..`-Umweg nicht daran
      vorbeikommt. Auch späteres Löschen hilft nicht: Die Git-Historie behält die Bilder.
      *Ehrliche Grenze:* Hier wurde **nie ein Training ausgeführt** — keine GPU, kein
      Trainer, keine Gewichte. Die Lizenzen sind gemessen, die Kommandozeilen sind aus
      der Dokumentation übernommen und im Feld `beleg` als solche gekennzeichnet.
      Für `ai-toolkit` verweigert `baue_kommando` die Auskunft, statt eine Kommandozeile
      zu erfinden: Es wird über YAML gesteuert.
- [ ] **LoRA-Training an einem echten Lauf prüfen** — braucht GPU, Trainer und Bilder.
      Erst dort zeigt sich, ob die Flaggennamen stimmen.

---

## Phase 5 · Kameras und die Vis-Stufe

**Aufwand:** mittel · **Setzt voraus:** Phase 3

- [x] **Den alten Add-on-Bestand sichten** — erledigt 2026-08-18,
      `docs/BLENDER_ADDON_BESTAND_2026-08-18.md`. Er existiert, und zwar erheblich:
      **83 Module, rund 37 000 Zeilen.** Beim ersten Nachsehen waren es fünf Dateien —
      der Klon war unvollständig ausgecheckt (5 im Arbeitsbaum, 314 in HEAD).
      *Die Existenz einer Datei ist kein Beleg für ihren Inhalt — und ihr Fehlen ist
      keiner für ihre Abwesenheit.*
      Kein GPL/AGPL im übernehmbaren Material; zwei Module mit „Muster adaptiert" aus
      fremder Quelle ungeprüfter Lizenz sind gemeldet, wir übernehmen davon nichts.
- [x] **Kameraableitung gebaut** — erledigt 2026-08-18, `kameras.py`, 87 Tests, kein
      `bpy`. Zwölf Richtungen mit Bias-Regler, analytischer Abstand aus dem Bildwinkel,
      Eckentest über alle acht Hüllbox-Ecken, Schrittlogik des Heranziehens mit
      hereingereichter Sichtprüfung.
      **Zwei Stellen sind besser als die Vorlage:** die richtungsabhängige sichtbare
      Breite (dort `max(b, t, diagonale)` — die Diagonale gewinnt immer, das `max` ist
      toter Code, und die Frontale steht auf Diagonalabstand), und der **gerechnete**
      statt getasteten Rückschub (ein Durchlauf statt zwanzig).
      **Vertrag entschieden:** `blick_auf` führend, Augenhöhe **absolut 1.70 m**.
- [x] **Die Kameras an Blender angeschlossen** — erledigt 2026-08-18. Zwei Wege über die
      Prozessgrenze (`--kamera` mit Ableitung aus der dort gemessenen Hüllbox, oder
      fertige Koordinaten), und der Bericht sagt, welcher gegriffen hat.
      **Der echte Lauf fand drei Fehler, die 87 grüne Tests nicht gezeigt hatten:** die
      absolute Augenhöhe (bei Fuss auf 400 m ü. M. eine Kamera 400 m unter dem
      Erdgeschoss — jetzt `gelaende_z`), ein Blickziel über dem Dach bei niedrigen Bauten,
      und ein Bauwerk als Fleck in der Bildmitte, das der Eckentest brav durchwinkte
      (jetzt meldet `kamerasatz` den Füllgrad).
- [x] **Die zwölf Bilder angesehen** — erledigt 2026-08-19,
      `docs/KAMERABLICK_2026-08-19.md`. Zwölf echte Blender-Läufe an einem synthetischen
      Wohnhaus. Alle zwölf bestehen den Eckentest, alle melden `vollstaendig`, der
      Füllgrad liegt bei allen zwischen 0.548 und 0.550 — **und die Bilder taugen nicht.**
      Der Füllgrad ist über alle zwölf konstant, die tatsächliche Bildfläche schwankt von
      3.3 % bis 9.6 %. Behoben mit `flaechenanteil`, gegen alle zwölf Messungen geprüft.
- [ ] **Hat die Szene ohne Boden den `geom_iou`-Deckel mitverursacht?** —
      `auf-20260819-15`. Auf jedem der zwölf Bilder **schwebt der Baukörper in Grau**. In
      `auf-10` wurde gemessen, dass der Tiefenschätzer genau dort eine Bodenebene
      hineinlegt. *Wir haben ihm ein Bild ohne Boden gegeben und uns gewundert, dass er
      einen erfindet.* Ob ein echter Boden das ändert, ist ungemessen — und ein Boden
      reicht bis zum Horizont und verschiebt über die Normalisierung jeden Grauwert.
      **Nicht eingebaut, sondern beauftragt** — derselbe Grund wie bei `groesste_flaeche`.
- [ ] **Format oder Vordergrund? — Owner-Entscheid.** Ein 40 m breiter, 15 m hoher Bau
      kann ein Quadrat nicht füllen. Die Referenzbilder des Hausstils sind in ihren
      Quadraten nicht leer, sondern voller Wiese, Bäume und Menschen; unsere Szene hat
      nichts davon. **Der Widerspruch liegt nicht im Stil** — entweder bekommt die Szene
      einen Vordergrund, oder das Format folgt dem Baukörper.
- [ ] **Der Beauty-Pass trennt Bauwerk und Hintergrund kaum** — Gebäudegrau und Weltgrau
      liegen dicht beieinander. Für die Tiefenkarte gleichgültig, für ein Bildmodell nicht:
      Es bekommt ein Ausgangsbild mit sehr wenig Zeichnung. Eine Störgrösse, die niemand
      angemeldet hat.
- [ ] **Verdeckungstest im Runner** — der Strahlenschuss gegen den Depsgraph. Die
      Schrittlogik steht diesseits der Grenze und ist geprüft; die Blender-Seite fehlt.
      Dabei zu klären, ob Frustum- und Verdeckungstest gegeneinander schwingen — der eine
      schiebt weg, der andere holt heran, und im Bestand ist das nie geprüft worden.
- [ ] **Die vier Sockeltypen als Antwort auf die MCP-Frage** — Kameraeinstellung, Bild,
      Render-Ebene, Variante. Das ist die brauchbarste Erbschaft aus dem alten
      Node-Tree: nicht sein Code (er hat gar keine Verdrahtungslogik — `links.clear()`
      beim Aufbau, `links.new` kommt in keinem der 83 Module vor), sondern seine Antwort
      darauf, welche Datenarten zwischen den Stufen fliessen.
- [ ] **`RENDER_SCENE_CONTRACT.md` als Vorbild auswerten** — besonders `faithful` als
      **eine** Zahl von 1.0 (Cycles-treu) bis 0.0 (KI-frei) und `depth_method` in der
      Ausgabe: Die Ausgabe sagt, wie sie entstanden ist.
- [x] **Prompt-Bibliothek und Renderstile gebaut** — erledigt 2026-08-18, `prompts.py`,
      45 Tests. Die **sieben Kategorien des Bestands übernommen** (`vegetation`, `people`,
      `atmosphere`, `light_time`, `sky`, `material_detail`, `composition`) — der Inhalt
      fehlte im Repo, die Form nicht.
      **Der Befund beim Übernehmen:** Keine dieser Kategorien nennt ein Bauteil. Sie
      beschreiben ausnahmslos, was um das Gebäude herum und auf seinen Oberflächen liegt.
      Die Einteilung ist damit genau die Lehre aus `auf-09` — *ein Prompt, der Bauteile
      nennt, die die Geometrie nicht hat, ist eine Aufforderung zur Halluzination* —, in
      Fächer gegossen. Sie wurde nicht erfunden, sondern erkannt.
      Dazu der `bauteilwaechter`: Er prüft freien Text auf Bauteilwörter (deutsch und
      englisch) und **meldet, statt zu verbieten** — manchmal hat die Geometrie das
      Genannte, und das kann ein Textmodul nicht wissen.
      Sechs Stile als erster Entwurf, jeder mit der Angabe, ob er **messtauglich** ist:
      Nebel verdeckt den Fuss, eine Skizze löst die Kanten auf — die Geometrie-QA misst
      dann den Stil und nicht das Bildmodell.
- [x] **Hausstil bestimmt** — 2026-08-18, `kosmo_standard`. Der Owner hat eine Richtung
      anhand von fünf veröffentlichten Wettbewerbsvisualisierungen vorgegeben; daraus ist
      eine Beschreibung **in Eigenschaften** entstanden: bedecktes Licht, heller
      entsättigter Himmel, niedriger Kontrast mit weicher Lichterzeichnung,
      Vordergrundbewuchs, kleine Figuren im Alltag, matte Materialien, filmische Tonwerte.
      **Kein fremder Name im Code, keine fremden Bilder im Repo** — die Eigenschaften sind
      fotografische Konvention und gehören niemandem, die Bilder nicht.
      `HAUS_STIL` und `MESS_STIL` sind bewusst **verschieden**: Gemessen wird auf dem
      Stil, der am wenigsten erfindet, ausgeliefert der, der aussieht wie das Büro.
- [x] **Ein Stil trägt jetzt ein Seitenverhältnis** — der einzige Befund der Stilanalyse,
      der bis in die Kamerarechnung reicht. Keine der fünf Vorlagen ist 16:9; der
      vertikale Bildwinkel folgt aus dem Seitenverhältnis, und mit ihm der Abstand.
- [ ] **Die fünf Behauptungen der Stilanalyse messen** — `auf-20260818-14`. Ich habe sie
      mit blossem Auge aufgestellt („entsättigt", „niedriger Kontrast", „heller Himmel",
      „feines Korn", „nie 16:9"). Das ist angesehen und nicht gemessen, und genau die
      Sorte Behauptung, die dieses Projekt sonst nicht stehen lässt.
- [ ] **Ein Referenzset, das uns gehört** — die andere Hälfte des Hausstils. Der Prompt
      sagt, wie man es macht; `stil_qa` prüft gegen ein Referenzset, ob es gelungen ist.
      Fremde Bilder können das nicht sein: Eine Einbettung ist eine Ableitung des Bildes.
      Es braucht eigene Renders oder eigene Arbeiten des Owners. **Erst danach ist der
      Hausstil prüfbar und nicht nur beschrieben.**
- [ ] **Owner-Entscheid: gelernter Hausstil oder fester Stil?** Der Owner hat beide Wege
      genannt — Referenzen in KosmoData hochladen („so sollen meine Renderings aussehen")
      oder ein festes Preset. **Es ist dieselbe Mechanik:** Ein Preset ist ein
      mitgeliefertes Referenzset. Der gelernte Weg braucht nur einen Ort, an dem die
      Bilder des Nutzers liegen, und die Messung ihres Bodens (`stil_qa.BODEN_MESSUNGEN`)
      — ein hochgeladenes Set hat einen anderen Boden als unser eigenes.
- [ ] **Die Stile am Gerät messen** — ob ein Prompt an einem Backbone wirklich landet,
      ist eine Messung und keine Textarbeit. Erst nach `auf-13`, denn an einem Modell
      ohne ControlNet-Naht sagt eine Prompt-Reihe nichts.

---

## Stehende Regeln für jede Sitzung

1. **Lexikon nachführen** — jeder neue Fachbegriff, in derselben Sitzung (`CLAUDE.md`).
2. **Sitzungsprotokoll schreiben** — `docs/sitzungen/JJJJ-MM-TT_sitzung-NN.md`.
3. **Diesen Plan fortschreiben** — Erledigtes abhaken, nicht löschen.
4. **Lizenz vor Technik** — bei jeder neuen Abhängigkeit zuerst die Lizenz, und zwar
   gegen die LICENSE-Datei, nicht gegen eine Suchmaschine.

---

## Wissensschulden

Bekannt und ausdrücklich nicht erledigt:

- ~~**Binärabhängigkeiten ungeprüft**~~ — `torch`, `opencv` und alles weitere mit grossem
  Binäranteil kann wie `ifcopenshell` fremde Lizenzen statisch mitbringen. Die
  Wheel-Lizenzangabe sagt darüber nichts.
  **Abgetragen 2026-08-18** → `docs/LIZENZPRUEFUNG_BINAER_2026-08-18.md`. 39 Pakete am
  Artefakt geprüft (installierte Datei, sonst Wheel per HTTP-Range geöffnet), 79
  Fremdkomponenten benannt. Die Vermutung hat sich bestätigt, aber anders als erwartet:
  **Kein neuer GPL-Fund im Produktivpfad.** Dafür drei Dinge, die vorher niemand wusste:
  (1) `shapely` deklariert BSD-3 und bringt **GEOS unter LGPL-2.1** mit — in `.venv-ifc`,
  also bereits hinter der Prozessgrenze, aber **nicht im `NOTICE`**; dasselbe gilt für
  **libquadmath (LGPL-2.1+)** aus `numpy`. Das ist die einzige Bringschuld des Berichts.
  (2) `torch` und `numpy` liefern **GNU-Laufzeitbibliotheken** mit (`libgomp`,
  `libgfortran`, GPL-3.0-or-later **mit** GCC-Ausnahme 3.1), ohne sie zu deklarieren —
  die Ausnahme greift, es bleibt zulässig. (3) `pip install torch` zieht auf Linux
  **zwingend** über 1,5 GB NVIDIA-proprietärer Wheels nach; `triton` gibt sich als MIT
  aus und liefert ~90 MB NVIDIA-Werkzeuge ohne jede Lizenzdatei mit.
  **`opencv` liegt in keinem Pfad dieses Projekts** — die Schuld war an dieser Stelle zu
  weit gefasst; die FFmpeg-Frage ist trotzdem vorsorglich beantwortet (LGPL-2.1, nicht
  GPL; Qt-5-LGPL-3 nur in der Nicht-headless-Variante).
  *Eine Architekturänderung folgt daraus nicht* — jeder Fund liegt hinter einer bereits
  gezogenen Grenze oder ist durch eine Ausnahmeklausel entschärft. Was folgt, sind ein
  ergänztes `NOTICE` und gepinnte Versionen; beides ist Owner-Entscheid (§7 des Berichts).
- **Was von den Binärabhängigkeiten offen bleibt** (Rest der obigen Schuld, 2026-08-18):
  Die **Rust-Wheels** (`tokenizers`, `safetensors`, `hf-xet`, `pydantic-core`) linken ihre
  Kisten statisch ein und liefern **keine** Aufstellung mit — `tokenizers` hat nicht
  einmal eine eigene Lizenzdatei im Wheel. Zu prüfen wäre mit `cargo-license` gegen die
  jeweilige `Cargo.lock`, nicht am Wheel. Ebenfalls offen: der Inhalt von
  `libtorch_cpu.so`/`libtorch_cuda.so`/`libtriton.so` (statische Anteile nicht
  verifiziert), **`nvidia-nccl-cu13`** und **`nvidia-nvshmem-cu13`** (keinerlei
  Lizenzangabe in den PyPI-Metadaten), sowie **GMP/MPFR** in `ifcopenshell` (im Binary
  nachgewiesen, Lizenz nicht am Original geprüft — `gmplib.org` und `www.cgal.org` waren
  über den Proxy nicht erreichbar).
- **Rund ein Dutzend Lizenzen nur aus Sekundärquellen** — Liste in
  `LAGEBEURTEILUNG_2026-08-14.md`, Kapitel 9. Vor einer Auslieferung gegen die
  LICENSE-Datei zu prüfen.
- **Ökosystem grösstenteils ungelesen** — `KosmoPublish`, `KosmoDesign`, `KosmoPrepare`,
  `ArchitekturKosmos-Codex`, `architekturkosmos-control-hub`, `Architektur-Cosmos`.
- **`tools/homeworker.py` war bis 2026-08-18 ohne einen einzigen Test** — ausgerechnet
  das Skript, das unbeaufsichtigt an einer 400-W-Hardwareschranke läuft. Seit Sitzung 07
  gibt es `tests/test_homeworker.py` (75 Fälle). Die erste Messung fand **vier
  fail-open-Löcher** in der Schranke, die „Fail-closed" im Docstring zusagte — alle
  behoben. *Erledigt, aber als Warnung stehengelassen:* Ein Docstring ist keine
  Prüfung.
- **Der Graph-Kern lässt fünf Dinge vermissen** (aus der Kettenverdrahtung, 2026-08-18):
  `inhalts_hash` rechnet auch Dateipfade ein, sodass ein verschobener Projektordner den
  ganzen Cache verwirft — die Kette umgeht das mit einer eigenen Hashvorbereitung, sauber
  wäre eine Ausnahmeliste im Kern. Der Cache kennt die Dateien nicht, die er verspricht;
  die Bindung an ein Arbeitsverzeichnis musste die Kette selbst erfinden. Es gibt keine
  selektive Verwerfung einzelner Einträge. Und es fehlt ein Begriff davon, was ein Knoten
  *braucht* — eine Entwurfszeit-Prüfung wie KosmoOrbits `pipelineReadiness` ist im inneren
  Graphen darum nicht möglich.
- **KosmoVis' Reife nicht nachgeprüft** — alle Angaben stammen aus dessen eigener
  Dokumentation, die sich selbst bei ~60–65 % einordnet und einräumt, dass noch kein
  echtes Projekt durchgerendert war.
