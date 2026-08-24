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
- [x] **Weg B, Schritt 1–4: die Naht zur Designzentrale** — 2026-08-19,
      `kosmo_szene.py` (48 Tests) und `bruecke.py` (28 Tests). Die Verträge sind
      **wörtlich aus ihren Schemadateien gelesen**, nicht aus einem Bericht abgeschrieben.
      Drei Stellen, an denen wir ihnen bewusst NICHT folgen: ihre Stil-Schwelle 0.30 und
      „dinov3" (gemessen wirkungslos), ihre Backbone-Liste (kennt unseren Vorgabewert
      nicht), und `faithful` als eine Zahl (bildet drei Regler nicht ab, und die Wirkung
      ist nicht monoton).
- [ ] **DER BEFUND, DER EINEN OWNER-ENTSCHEID BRAUCHT: Die Brücke erteilt sich die
      Freigabe selbst.** Ihr `create_job` erzeugt den `approval_token` mit
      `secrets.token_hex` — **jeder Auftrag kommt mit einer Freigabe an, die kein Mensch
      erteilt hat.** Unser `enqueue_render` lässt einen Auftrag ohne menschliche Freigabe
      ausdrücklich liegen und rührt die Grafikkarte nicht an; das ist der Freeze-Schutz
      und der Grund, warum die Leistungsgrenze eingehalten wird.
      `bruecke.lies_auftrag` verlangt darum `fremde_freigabe_gilt=True` als ausdrückliche
      Entscheidung des Betreibers. **Diese Entscheidung gehört dem Owner**, nicht dem
      Programm — und sie gehört getroffen, bevor die Naht in Betrieb geht.
- [x] **Welche App wird vorgeführt? — Das eigene Repo des Owners, Stand von heute.**
      `auf-20260819-16` beantwortet: `apps/kosmo-orbit`, `@kosmo/orbit-app` **0.9.36**,
      Remote `Imperigo/Architektur-Cosmos`, **letzter Commit am selben Vormittag**, null
      uncommittete Änderungen.
      **Meine Prämisse trug nicht.** Der Anlass war „`KosmoSpez` kommt in keinem
      Quelltext vor, den wir haben". Dort steht es in **31 Dateien** — *unser Klon ist
      schlicht älter als der Arbeitsstand.* Es war nie ein unbekannter Bestand, sondern
      unser eigener veralteter Blick darauf.
      **Der Merksatz ist damit um einen Halbsatz zu erweitern:** Das Fehlen einer Datei
      in einem Klon ist nicht einmal ein Beleg für ihr Fehlen im Bestand. Dreimal an einem
      Tag derselbe Fehler in drei Verkleidungen — das geschlossene Menü, das fehlende
      `KosmoSpez`, das nirgends auffindbare `Design/Vis`.
      Die Kehrtwende zum Übergabeblatt wird davon **bestätigt statt widerlegt**: Ein
      Bestand, dessen letzter Commit vom selben Vormittag ist, war schon beim Beginn der
      Bestandsaufnahme nicht mehr der, den sie beschrieb.
- [ ] **Lügt „bereit"? — UNGEMESSEN, und die frühere Antwort war ein Fehlschluss.**
      Wir hatten notiert, ein Druck im unverdrahteten Zustand bleibe wirkungslos. Die
      HomeStation hat den Klick nachgemessen (`document.elementFromPoint`): Der
      Vergrössern-Knopf (44 × 44 bei 895,741) überdeckt die obere linke Ecke des
      Ausführen-Knopfs (84 × 32 bei 911,759) — **der Klick hat den Knopf nie erreicht.**
      Unabhängig bestätigt durch ihren eigenen Insel-Überdeckungs-Wächter.
      **Was steht:** Das Panel *zeigt* `bereit` bei unverdrahteten Knoten — eine Ablesung,
      kein Klick. **Was nicht mehr gilt:** dass ein Druck dort wirkungslos bleibt.
      *Aus einem ausbleibenden Effekt auf eine Ursache geschlossen, ohne zu prüfen, ob die
      Handlung überhaupt ankam* — derselbe Fehler wie dreimal zuvor an diesem Tag, nur
      diesmal unserer.
- [x] **Die Verdrahtung ändert alles — das steht unabhängig davon.**
      `auf-20260819-16`: Unverdrahtet bleibt der Zustand dreimal auf `bereit`. Verdrahtet
      wechselt er auf `fehler` **mit präziser Begründung**, nach dem Nachtragen des
      Bridge-Tokens auf „auf GPU-Leerlauf" — und in der Warteschlange liegt ein
      vollständiger Auftrag.
      **Was bleibt, ist der Befund in schärferer Form:** Der Zustand meldet `bereit` auch
      bei unverdrahteten Knoten. Das ist wörtlich der Befund, mit dem dieses Projekt
      angefangen hat, und genau dagegen sind `kette.pruefe_kette` und `graph.pruefe_bedarf`
      gebaut. Steht als Kapitel 3 im Übergabeblatt.
- [x] **„Ein bestandener Test ist kein Beleg dafür, dass er etwas geprüft hat."**
      Die HomeStation hat einen eigenen Fehler gemeldet: einen als *grün* geführten
      Wächter, dessen Fundartefakt `{"geprueft": 0}` trug — er hatte **nichts** gemessen.
      **Dieselbe Frage an unsere eigene Suite gestellt und gemessen**, 2026-08-20,
      `tools/vakuumprobe.py`, 13 Tests. Gesucht wird die vakuum-wahre Gestalt: `all(...)`
      und `not any(...)` über eine Sammlung, die leer sein kann. Nicht statisch geraten,
      sondern **umgeschrieben und ausgeführt** — auf einer Kopie, das Repo bleibt
      unangetastet.
      **Ergebnis: 40 Stellen umgeschrieben, 6 Treffer, kein einziger falsch-grüner Test.**
      Für jeden der sechs lag eine Gegenprobe in derselben Datei — teils drei Zeilen
      darüber. Das Ergebnis ist damit unspektakulär und genau darum berichtenswert: Die
      Frage war offen und ist jetzt beantwortet statt vermutet.
      Das Werkzeug bleibt, weil die nächste schwache Stelle sonst wieder unentdeckt bliebe.
- [ ] **Weg B, Schritt 5–7** — QA je Kamera statt je Bild, die Verzeichniskonvention
      `<out>/<kamera>/…`, Varianten, und der Treue-Regler des Panels bis in die Kette.
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
- [x] **Die zwei grössten KI-Module geöffnet** — erledigt 2026-08-19,
      `docs/KI_MODULE_BESTAND_2026-08-19.md`. Beide sind Regel-1-**sauber**: Sie bauen
      ComfyUI-Workflows als JSON (Daten) und sprechen einen laufenden Server über HTTP an
      (Prozessgrenze). **Aber nebenan liegt ein GPL-Fund ersten Ranges:**
      `kosmovis_render.py` macht `import nodes` und `import execution` — ComfyUI-Interna,
      GPL-3.0, in-process ausgeführt. Für uns in jeder Form gesperrt. Die Bestandsaufnahme
      vom 18.08. führte das nicht; sie ist berichtigt.
- [x] **`archviz_variant_scorer.py` und `archviz_exposure_check.py` geöffnet** —
      2026-08-20. Beide **ohne jede Lizenzdatei** in jenem Bestand (Regel 1: ohne
      Lizenzangabe gilt „alle Rechte vorbehalten" — nicht übernehmbar, was ohnehin nie
      der Plan war), und beide laden ihr Bild zuerst über `bpy`, also für uns unter
      Regel 2 und 4 verschlossen. Übernommen wurde **nichts ausser den Fragen**.
      **Der Befund, der mehr wert ist als die fehlende Prüfung:** Beide Module kodieren
      *einen* Stil in einer Konstante und geben das Ergebnis als objektives Qualitätsmass
      aus. `HIGHLIGHT_WARN_PCT = 8.0` erklärt mehr als 8 % geclippte Lichter zum Fehler
      „Überbelichtet" — unser am Vortag gemessener Hausstil liegt bei **7,55 % ± 6,9 mit
      einem Höchstwert von 30,0 %**. Und der Variantenbewerter gewichtet *Schärfe* mit
      **0,50**, was jeden Nebel- und Skizzenstil systematisch als schlechtestes Bild
      ausweist.
- [x] **Belichtungsprüfung gebaut** — 2026-08-20, `belichtung.py`, 31 Tests, reine
      stdlib. Die Schwellen hängen an einem `Rahmen` je Stil, und **jeder Rahmen sagt,
      welche seiner Zahlen gemessen sind**. Daraus die einzige harte Regel des Moduls:
      *Eine ungemessene Schwelle darf nie `error` melden, höchstens `warn`* — dieselbe
      Dreiteilung wie überall sonst, denn *nicht gemessen* ist nicht *in Ordnung*.
      Der geerbte Rahmen ist als `GEERBTER_RAHMEN` mitgeführt, **zum Vergleich und nicht
      zum Gebrauch**: Ein gemessener Widerspruch ist mehr wert als eine Behauptung.
      Dazu `bildlesen.lies_png_luminanz` — der erste farbfähige Leser des Projekts,
      sauber getrennt vom Tiefenleser, der Farbe weiterhin **ablehnen muss**.
- [x] **Variantenreihen gebaut — und ausdrücklich KEIN neuer Bewerter.** 2026-08-20,
      `varianten.py`, 32 Tests.
      Der geerbte Bewerter normalisiert **min-max innerhalb der Charge** (die beste
      Variante bekommt ~100, auch wenn alle fünf unbrauchbar sind; eine einzelne bekommt
      pauschal 50) und gewichtet **Schärfe mit 0.50**, was jeden Nebel- und Skizzenstil
      systematisch als schlechtestes Bild ausweist. Beides sind Massstäbe, die einen Stil
      für die Wahrheit halten.
      **Wir bewerten darum gar nicht neu:** `geometrie_qa` und `belichtung` sind bereits
      absolut und ihre Schwellen gemessen. Was fehlte, war die Reihe — und die Frage,
      **ab wann ein Unterschied überhaupt einer ist**.
      Zwei Reihenarten, und ihre Verwechslung macht beide wertlos: Eine **Saatreihe**
      ändert nur den Seed und misst den **Rauschboden** der Kette; eine **kontrollierte
      Reihe** ändert genau eine Grösse bei **festem Seed** und misst deren Wirkung.
      `kontrollierte_reihe` weigert sich, den Seed mitzufahren.
      Daraus die eigentliche Leistung: *Ein Unterschied ist erst dann einer, wenn er den
      Rauschboden übersteigt* — dieselbe Denkweise, mit der `stil_qa` zu seiner Schwelle
      kam, und mit derselben Zahl (`K_STREUUNGEN = 2.0`, an beiden Stellen).
      Und `waehle` kann sagen: **keine besteht.** Der geerbte liefert immer eine beste —
      die Sorte Antwort, die eine Frage beendet, ohne sie zu beantworten.
- [x] **Die erste Saatreihe ist gefahren — und die Streuung ist gross.**
      `auf-20260820-20`, fünf Seeds, sonst identisch, `docs/RAUSCHBODEN_2026-08-20.md`.
      Standardabweichung **0.0331** bei einem Mittel von 0.0493 — **67 %
      Variationskoeffizient**. Und: **zwei von fünf Läufen sind gar nicht messbar**,
      `n_gemeinsam` schwankt von **0 bis 1925**. Bei Seed 1002 gibt es keinen einzigen
      gemeinsamen Bildpunkt.
      *Ein Einzellauf als Vergleichsgrundlage ist damit wertlos.*
- [ ] **Der Rauschboden gilt noch nicht für den Fall, der zählt — meine Schuld.**
      Die Messung lief auf dem Testbau **ohne Boden**, und ich hatte am selben Tag die
      Vorgabe auf `wie_soll` zurückgenommen. Das ist genau die Szenenart, in der die
      *zurückgenommene* Regel gewinnt: `geom_iou` fiel von 0.082 (`auf-13`) auf ≈ 0.006 —
      ein Dreizehntel. Beide Messungen stehen damit an **zwei Betriebspunkten**.
      Die HomeStation konnte das nicht wissen; der Auftrag sagte „mit der Vorgabe messen".
      **Zum dritten Mal an einem Tag: Eine Messung gilt so weit, wie gemessen wurde.**
      `auf-20260820-21` wiederholt sie auf einer Szene **mit** Boden und wertet **beide
      Strategien auf denselben Bildern** aus — das kostet keinen zweiten Renderlauf und
      beendet die Vermutung.
- [ ] **„0.80 schlägt 1.00" gilt bis dahin als UNBELEGT** — nicht als widerlegt. Der
      Unterschied von 0.0228 liegt unter der gemessenen Streuung von 0.0331, aber die
      beiden Zahlen stammen von verschiedenen Betriebspunkten. Der Unterschied zwischen
      *unbelegt* und *widerlegt* ist wichtig genug, um ihn stehen zu lassen.
- [x] **Warum nie ein erzeugtes Bild das Gate bestanden hat — zur Hälfte Arithmetik.**
      2026-08-20, `geometrie_qa.erreichbarkeit()`, 10 Tests. Der Score ist
      `sqrt(|spearman| × geom_iou)`; für 0.65 braucht es bei perfekter Ordnung ein
      `geom_iou` von **0.4225**. Gemessene Deckel:

      | Szene · Strategie | Deckel | höchstmöglich | 0.65? |
      |---|---|---|---|
      | ohne Boden · `wie_soll` | 0.256 | 0.505 | **nein** |
      | ohne Boden · `ohne_randberuehrung` | 0.406 | 0.636 | **nein** |
      | Platte endlich · `wie_soll` | 0.967 | 0.982 | ja |

      **Alle unsere Renderläufe liefen auf der Szene ohne Boden. Dort war die Schwelle
      arithmetisch unerreichbar** — ein durchgefallenes Bild belegte nichts über seine
      Geometrietreue, der Lauf mass nicht das Bild, sondern die Szene.
      `erreichbarkeit()` beantwortet das jetzt **vor** dem Rechnen, kostet nichts, und
      hätte den Unterschied gemerkt, bevor er drei Aufträge gekostet hat. Eine ungemessene
      Kombination bekommt **`None`** und keine Schätzung.
- [x] **Der Deckel lässt sich aus der Soll-Karte ABLESEN** — kein Szenenname nötig.
      Derselbe Tag, und es macht die Tabelle oben fast überflüssig: Der **Geometrieanteil**
      (wieviel Prozent der Bildpunkte überhaupt Geometrie tragen) sagt fast alles.

      | Szene | Anteil | Deckel |
      |---|---|---|
      | ohne Boden | 17,0 % | 0,256 |
      | Platte endlich | 59,8 % | 0,967 |
      | Ebene bis Rand | 93,9 % | 0,974 |
      | Ebene mit Horizont | 100 % | 1,000 |

      Der Grund ist bekannt: Ein monokularer Schätzer legt in eine leere Fläche eine
      Bodenebene hinein (`auf-10`) — je mehr leere Fläche, desto mehr erfundene Geometrie
      in der Ist-Silhouette. `geometrie_score` meldet den Anteil jetzt in jedem Ergebnis
      und **warnt** unter 20 %, mit der Messung in der Meldung.
      **Vier Punkte sind keine Kurve:** Es stehen die untere und die obere Marke da, und
      dass es zwischen 20 % und 60 % ungemessen ist, steht in der Warnung selbst.
      *Nebenbei aufgefallen:* Unsere eigene Test-Sollkarte liegt bei **18,8 %** — also
      selbst im unerreichbaren Bereich.
- [x] **Die Testgeometrie kann jetzt Gelände tragen** — 2026-08-20,
      `make_test_ifc.py --gelaende`, Platte in 2,5-facher Gebäudespanne wie
      `platte_endlich`. **Vorgabe bleibt aus:** Alle bestehenden Tests hängen an der
      Hüllbox 8,0 × 5,0 × 3,25 m, und eine stillschweigend geänderte Testgeometrie macht
      eine Messreihe unbrauchbar, ohne dass es auffällt.
- [x] **Gelände allein macht es SCHLECHTER — die Kamera war das Problem.** Beim
      Nachmessen: Mit Gelände sinkt der Geometrieanteil von 6,9 % auf **0,9 %**. Die
      Geländeplatte bläht die Hüllbox von 8 × 5 auf 20 × 20 m, die Kamera zieht sich
      zurück, und das Gebäude wird *kleiner*. Eine flache Platte, von 1,70 m Augenhöhe
      gesehen, füllt fast keine Bildfläche.
      **Behoben mit `--kamera-huellbox`:** Die Kamera bezieht sich auf die Hüllbox des
      **Bauwerks**, der Bericht weiter auf alles, was dasteht. Zwei Fragen, zwei
      Hüllboxen. Gemessen an drei Läufen derselben Geometrie: **6,9 % → 0,9 % → 24,7 %.**
      *Dabei wäre mir fast derselbe Fehler unterlaufen, gegen den ich am selben Tag
      `kontrollierte_reihe` gebaut habe:* Die erste Messung änderte Gelände **und** Kamera
      zugleich. Mit fester Kamera stieg der Anteil von 21,9 % auf 51,8 % — das Gelände
      wirkt, nur die Kamera rahmte es mit.
- [ ] **24,7 % liegen im ungemessenen Mittelfeld.** Unter 20 % war der Deckel
      unerreichbar, ab 60 % hoch — dazwischen weiss niemand etwas. Entweder eine kleinere
      Geländeplatte oder ein höherer Standpunkt; beides ungemessen.
- [x] **Rauschboden mit Boden gemessen — und weisses Rauschen besteht das Gate.**
      `auf-20260820-21`, `docs/RAUSCHBODEN_2026-08-20.md` Teil 2. Streuung relativ viel
      kleiner (14,2 % statt 67 %), **null Ausfälle**. Und `ohne_randberuehrung` liefert
      fünfmal `n_ist = 0` — die Rücknahme der Vorgabe war richtig, jetzt auch am
      *erzeugten* Bild belegt.
      **Die Nullprobe, die niemand verlangt hatte, ist der eigentliche Ertrag:**

      | Kontrollbild | Score | Gate 0.65 |
      |---|---|---|
      | Beauty (perfekt) | 0.9839 | ✓ |
      | **weisses Rauschen** | **0.7217** | **✓** |
      | leeres Graubild | 0.5188 | ✗ |
      | unsere fünf Läufe | 0.471 – 0.657 | einmal knapp |

      Der eine Lauf über der Schwelle liegt **24,8 % unter dem Rauschanker**. Grund: Ein
      monokularer Schätzer legt in *jedes* Bild eine Bodenrampe, und eine Szene mit 60 %
      Boden **ist** so eine Rampe. *Auf einer Szene mit viel Boden misst die Kette nicht
      mehr das Bauwerk, sondern die Bodenrampe.*
- [x] **`NULLANKER` und `einordnung()` gebaut** — ein Score wird nicht mehr nur gegen die
      Schwelle gehalten, sondern gegen das, was **nichts** auf derselben Soll-Karte
      erreicht. Dieselbe Medizin wie bei `stil_qa` seit dem 18.08. Ohne Nullprobe gibt es
      **keine** Einordnung, sondern die Feststellung, dass keine vorliegt.
- [ ] **Die Zange — und das Mittelfeld ist ungemessen.** Bei 17 % Geometrieanteil ist das
      Gate *unerreichbar* (Deckel 0.64); bei 60 % *trennt es nicht* (Rauschen 0.72).
      Beides gemessen. Dazwischen weiss niemand etwas — und ausgerechnet dort liegt die
      Geometrie vom selben Tag: Testbau mit Gelände, Kamera aufs Bauwerk, **24,7 %**.
      **Das ist die nächste Messung**, und sie entscheidet, ob die Geometrie-QA überhaupt
      einen brauchbaren Arbeitsbereich hat.
- [x] **Die eigene Schwelle steht als unkalibriert in den DATEN, nicht nur im Blatt.**
      2026-08-20. Wir werfen dem fremden Vertrag vor, seine Stil-Schwelle 0.30 sei kein
      Gate — es wäre unredlich, dabei zu verschweigen, was wir über die eigene gemessen
      haben. Kapitel 2 des Übergabeblatts trägt jetzt die Tabelle der Kontrollanker.
      **Und weil ein Übergabeblatt niemand aufschlägt, während er auf ein Häkchen sieht**,
      meldet `verdict.reason` *„Geometrie-Schwelle NICHT kalibriert"*, solange keine
      Nullprobe vorliegt. `verdict.reason` ist ein **Vertragsfeld** und überlebt damit
      auch `nur_vertragsfelder` — die Warnung erreicht auch den, der strikt sendet.
- [x] **Die Nullprobe ist angeschlossen — und der Anker wird GEMESSEN, nicht
      nachgeschlagen.** 2026-08-20, `abholer.verarbeiter(nullprobe=True)`, voreingestellt.
      Je Kamera drei Kontrollbilder (`bildschreiben.schreibe_kontrollbild`): weisses
      Rauschen, graue Fläche, Querverlauf. **Kostet keinen Renderlauf** — nur je einen
      Durchgang des Tiefenschätzers.
      **Warum gemessen statt nachgeschlagen:** Eine Tabelle nach Szenennamen hätte zwei
      Fehler — der Aufrufer kennt den Namen nicht, und zwei Szenen desselben Namens sind
      nicht dieselbe Szene. Der Anker gehört zur **Soll-Karte**, und die liegt vor.
      Das Rauschen hat einen **festen Startwert**: Eine Nullprobe, die bei jedem Aufruf
      anders ausfällt, ist keine. Und der Querverlauf läuft ausdrücklich *quer* — eine
      Tiefenrampe läuft von unten nach oben, und ein Kontrollbild, das genau den
      Gradienten liefert, den der Schätzer ohnehin erfindet, prüfte nichts.
      Ein einzelner gescheiterter Anker macht die Probe nicht wertlos: Gemeldet wird, was
      gemessen wurde.
- [x] **Trägt die ControlNet-Naht? — JA, und meine Hypothese ist widerlegt.**
      `auf-20260820-22`. Kein Hinweis nennt `control_image` oder
      `controlnet_conditioning_scale`: Beide werden angenommen. **A (Stärke 0.0) ≠ B
      (0.8):** `geom_iou` steigt von 0.76 auf 0.95.
      *Die Naht transportiert die Silhouette — nicht die Tiefenordnung.*
      **Widerlegt:** Ich hatte vermutet, die niedrige Rangkorrelation komme entweder von
      einer toten Naht oder von verdrehter Polarität, und hielt beides für erschöpfend.
      `|rho|` bleibt über alle vier Läufe bei 0.45–0.49 — **auch beim unkonditionierten
      Lauf A.** Der Rückstand gegenüber dem Graubild ist ein Artefakt der Metrik auf einer
      Bodenszene, keine Eigenschaft der Naht. Es gab eine dritte Erklärung.
- [x] **Die Polarität ist nicht messbar** — C liegt 0.0418 über B, die Seed-Streuung
      derselben Szene beträgt 0.0758. Der Unterschied liegt **unter dem Rauschen**.
      *Hier greift `varianten.ist_unterschied_belegt` zum ersten Mal:* Ohne den am Vortag
      gemessenen Rauschboden hätte man C für besser gehalten und die Polarität „korrigiert"
      — auf Rauschen hin.
- [x] **Es gibt einen Arbeitsbereich — aber nicht den erwarteten.** Bei 29,1 %
      Geometrieanteil besteht weisses Rauschen das Gate **nicht** mehr (0.2546). Das
      perfekte Bild aber auch nicht (0.4149).
      **Und der Zusammenhang ist nicht monoton:** 17 % → 0.504, **29,1 % → 0.415**,
      59,8 % → 0.984. Die Mitte hat die *niedrigste Decke von dreien* und die *beste
      Trennung* (1.63 gegen 1.36). Mein Bild „zwischen den Fehlerbereichen liegt der gute
      Bereich" war zu einfach — es gibt keinen Anteil, bei dem beides zugleich stimmt.
- [x] **WIDERLEGT am 20.08. (`auf-20260820-23`): Die Normierung trägt nicht.** Dieselbe
      Verschiebung von 1 m ergibt bei 29 % Geometrieanteil rund 0.40 der Spanne, bei
      59.8 % rund 0.92 — Faktor 2,3. Und härter noch: Der Score ist **nicht monoton**
      (2 m → 0.1191, 4 m → 0.2301). Eine nicht-monotone Grösse lässt sich durch keine
      Normierung in ein Mass für Abstand vom Richtigen verwandeln; der Anteil der Spanne
      erbt die Nicht-Monotonie unverändert. Damit ist das Gebäude vom 20.08. weg.
- [x] **Die Richtung ist eingebaut (21.08.), und sie repariert einen von drei Knicken.**
      `geometrie_score(..., polaritaet=...)` wertet das vorzeichenbehaftete ρ, sobald die
      Polarität gemessen ist (`polaritaet_aus_messungen`, `GEMESSENE_POLARITAET`); ohne
      Messung bleibt es beim Betrag, und das Ergebnis **sagt dann selbst**, dass sein
      Score nicht monoton ist. Nachgerechnet in `docs/POLARITAET_2026-08-21.md`.

      **Der Gewinn, den niemand gesucht hat:** Eine vollständig invertierte Tiefenkarte
      erreichte mit `abs()` den Score 1.0 und bestand das Tor — vorne und hinten
      vertauscht, der grösstmögliche Geometriefehler, bewertet wie ein perfektes Bild.
      Jetzt fällt sie auf 0.0. Das war kein Genauigkeits-, sondern ein Sicherheitsloch.

      **Was es NICHT löst, damit es niemand für mehr hält:** die Stumpfheit gar nicht
      (kein Lauf der Szene B fällt unter den Rauschanker, vorher wie nachher), und zwei
      der drei Knicke nicht — die sitzen in `geom_iou`, nicht in ρ.
- [x] **Die Widerlegung ist im Code angekommen, nicht nur in den Dokumenten (21.08.).**
      `einordnung` rechnet `anteil_der_spanne` weiter — sie ist eine nachvollziehbare
      Ableitung aus zwei gemessenen Ankern und steht in älteren Ergebnissen —, **deutet
      sie aber nicht mehr**. Neues Feld `anteil_gilt`, immer `False`, damit die Warnung
      den Aufrufer erreicht und nicht bloss den Docstring. Was überlebt, ist
      `ueber_rauschen`: ein **Vergleich innerhalb einer Szene**, kein Abstand — und
      darum weder auf Monotonie noch auf Szenenunabhängigkeit angewiesen.
- [x] **Ein grüner Test hat eine Unwahrheit dokumentiert, und das ist die eigentliche
      Lehre des Abends.** `test_der_anteil_der_spanne_ist_die_szenenunabhaengige_groesse`
      setzte in beide Szenen die Mitte zwischen Rauschanker und perfekt ein und stellte
      fest, dass beide Male 0.5 herauskommt. Grün seit dem 20.08. — und **tautologisch**:
      Der Anteil ist als lineare Abbildung von `[rauschen, beauty]` auf `[0, 1]`
      definiert, also trifft ihre Mitte per Konstruktion 0.5. In jeder Szene. Auch in
      einer, in der die Normierung völlig falsch wäre. Geprüft wurde die Umkehrfunktion
      der eigenen Definition, nicht die Behauptung im Namen.

      Ersetzt durch eine Prüfung an **demselben geometrischen Fehler** in beiden Szenen
      (1 m Versatz, Messwerte aus `auf-23`): 0.40 gegen 0.92.
- [ ] **Blinder Fleck der Vakuumprobe — benannt, nicht behoben.** Sie findet
      Zusicherungen, die über einer leeren Sammlung *immer* wahr sind. Sie findet
      **nicht** den Fall oben: eine Zusicherung, die etwas prüft, nur nicht das, was ihr
      Name behauptet. Ob sich das überhaupt maschinell fassen lässt, ist offen — der
      Verdacht ist, dass es auf „stimmt der Name mit der Zusicherung überein" hinausläuft
      und damit auf eine Frage, die kein Werkzeug beantwortet. Bis dahin bleibt es eine
      Lesepflicht: **Wer einen Test schreibt, dessen Name eine Behauptung trägt, muss
      prüfen, ob die Zusicherung diese Behauptung wirklich falsifizieren KÖNNTE.**
- [x] **BESTÄTIGT (`auf-20260821-24`): Es liegt am Boden — und die Heilung ist eine
      andere, als ich vorgeschlagen habe.** Meine Vorgabe war `geom_iou` über der
      Bauwerksmaske. Das geht nicht: Innerhalb der Maske trägt die Soll-Karte **überall**
      Geometrie, `geom_iou` ist dort konstruktionsbedingt 1 und misst nichts. Und mit der
      Maske als Soll-Karte durch die übliche Kette bricht es zusammen — das perfekte Bild
      erreicht in Szene B **zwei** gemeinsame Punkte, weil `wie_soll` die 44 604 nächsten
      Punkte *irgendwo im Bild* wählt und die auf dem Boden liegen. Derselbe Fehler wie
      bei `ohne_randberuehrung`, und ich bin ihm ein zweites Mal aufgesessen.

      **Was trägt: ρ über der Bauwerksmaske, ohne `geom_iou`, ohne Normierung.**

      | Versatz | 0 m | 0.25 | 0.5 | 1 m | 2 m | 4 m | Rauschen |
      |---|---|---|---|---|---|---|---|
      | 29 % | −0.9908 | −0.9627 | −0.9239 | −0.8449 | −0.7814 | −0.7386 | −0.5207 |
      | 59.8 % | −0.9874 | −0.9594 | −0.9211 | −0.8437 | −0.7843 | −0.7435 | −0.5207 |

      **Streng monoton** in beiden Szenen, deutlicher Abstand zum Rauschen — und die
      beiden Kurven liegen mit höchstens **0.005** aufeinander. **Was die Normierung
      nicht leistete, leistet die Maske ohne jede Normierung: Die Szenenabhängigkeit war
      nie eine Eigenschaft der Metrik, sie war der Boden.**
- [x] **Die Maske kostet keinen zweiten Renderdurchgang.** Der Material-ID-Pass des
      Multipass liefert exakt dieselbe: 44 604 Punkte aus beiden Quellen, Differenz in
      beide Richtungen null. Bedingung, die die HomeStation ausdrücklich nennt: Es geht,
      weil das Gelände ein eigenes Objekt mit eigenem Eintrag ist. Für eine Automatik
      braucht es eine Regel, **woran das Gelände zu erkennen ist** (Objektname, `IfcSite`,
      vereinbartes Material) — solange die Zuordnung am Namen hängt, ist der Weg für
      einen Messstand gut und für den Betrieb noch nicht fertig.
- [x] **Die Polarität der Nullproben ist gemessen — und meine Hoffnung war falsch.** Alle
      Nullproben haben ein **negatives** ρ (Rauschen −0.9165 bei 59.8 %, −0.9486 bei
      29 %). Der Rauschanker fällt mit der gerichteten Rechnung also **nicht** auf 0. Der
      Grund ist derselbe wie beim Graubild: Ein monokularer Schätzer legt in eine
      strukturlose Fläche eine glatte Rampe, und die Soll-Karte einer Bodenszene **ist**
      im Wesentlichen eine Rampe. Zwei Rampen korrelieren.

## Kamerasetzung — die Recherche ist da, und sie trifft härter als erwartet

*Drei Recherchen unter `docs/recherche/`, Synthese in `docs/KAMERAREGELN_2026-08-21.md`.*

- [ ] **UNSERE KAMERA KIPPT, UND DIE ARCHITEKTURFOTOGRAFIE KIPPT NICHT.** `ZIEL_ANTEIL_HOEHE
      = 0.20` erzeugt bei 1,2 × Gebäudehöhe Abstand **9,46° Neigung, unabhängig von der
      Gebäudehöhe** — die Vertikalen laufen um rund 9 bis 12 % aufeinander zu (bei
      waagrechter Kamera: exakt null). **Die zuerst hier genannten 11,8-21,8 % waren falsch
      gerechnet** - die Formel enthielt die Neigung gar nicht und lieferte dieselben Werte
      auch bei null Grad. Der Befund steht, die Spanne war zu gross. Der Kommentar im Code nennt das „der übliche Griff der
      Architekturfotografie"; **das ist die Umkehrung der Wahrheit.** Parallele Vertikalen
      entstehen dadurch, dass die Sensorebene lotrecht steht, und HABS/NPS schreibt die
      Korrektur **bei der Aufnahme** zwingend vor. Der übliche Griff ist waagrecht halten
      und **shiften**.

      Das ist die einzige institutionell verbindliche Regel des Fachs, und wir verletzen
      sie in jedem Bild, das dieses Projekt je erzeugt hat. Zu bauen: waagrechte Kamera
      plus Shift statt Blickziel über Augenhöhe. `komposition.py` rechnet es bereits;
      `kameras.py` umzustellen ist der nächste Schritt und ändert **jede bisher gemessene
      Aufnahme**, also nicht nebenbei.
- [ ] **Der Bodenanteil von 59,8 % kann gar nicht entstehen — und das verbindet zwei
      Befunde, die ich für unabhängig hielt.** Eine waagrechte Kamera ohne Shift legt den
      Horizont exakt in die Bildmitte: 50 % Boden. **Korrektur, nachts:** Shift regelt in
      **beide** Richtungen; ueber 50 % zu kommen ist geometrisch moeglich - die 59,8 %
      verlangen -2,35 mm, ein Zwoelftel des Wegs. Der Satz "nur durch Kippen" war falsch.
      Richtig bleibt: **kein gesichteter Text beschreibt einen Shift nach unten.** Nicht
      unmoeglich, sondern unbeschrieben. Unsere Versuchsszene hatte 59,8 % — und ist
      genau die, an der die Geometrie-QA zusammenbrach (Rauschen 0,72; leeres Grundstück
      schlägt Rauschen).

      **Die Szenen, an denen die Metrik versagte, waren fotografisch nicht gültig.** Das
      entlastet die Metrik nicht — der Betrieb wird schlechte Bilder liefern —, aber es
      sagt, wo zuerst zu reparieren ist: **an der Kamera, nicht an der Metrik.**
- [ ] **„Vordergrund füllen" ist bei uns behauptet, nicht umgesetzt.** Vordergrund mit
      **Inhalt** ist belegt (bis in die HABS-Pflichtansicht); **leerer Boden** wird in
      keiner Quelle als Mittel genannt, sondern durchgehend als Fehler. Unsere
      synthetischen Szenen haben nichts, was als Vordergrund taugte — kein Belag, keine
      Bepflanzung, nichts. Solange das so bleibt, erzeugt der Entscheid des Owners genau
      den Fehlerfall, den er vermeiden soll.
- [ ] **Ich habe dem Owner eine falsche Alternative vorgelegt.** Format anpassen *oder*
      Vordergrund füllen — die Praxis kennt einen dritten und üblicheren Weg: **den
      Standort.** HABS verlangt zwei Über-Eck-Ansichten gegen eine frontale; ein 8:3-Bau
      projiziert sich schräg nicht mehr als 8:3. Der Entscheid bleibt gültig, aber er fiel
      auf unvollständiger Auswahl, und das steht hier statt stillschweigend korrigiert zu
      werden.
- [ ] **Innen gibt es eine beweisbare Regel, und sie widerlegt unsere Zahl.** Boden und
      Decke bekommen **exakt** gleich viel Bildfläche, wenn die Kamera auf halber Raumhöhe
      steht — unabhängig von Brennweite und Abstand (nachgerechnet über 24/35/50 mm und
      3/5/8 m, Differenz jedes Mal 0,000000). Bei 2,55 m Raumhöhe: 1,275 m. Unsere 1,70 m
      erzeugen dort 28 Prozentpunkte Ungleichgewicht und liegen ausserhalb dessen, was die
      Innenraumfotografie überhaupt nennt (0,91–1,52 m).
- [ ] **1,70 m ist keine Mitte, sondern eine Setzung.** DIN 33402-2: Augenhöhe Erwachsener
      1,43–1,74 m — **1,70 m liegt nahe dem 95. Perzentil der Männer.** Wichtiger als die
      Zahl ist aber der Nullpunkt: 1,60 gegen 1,70 m verschiebt den Horizont am Baukörper
      um 0,6–1,2 Prozentpunkte (unsichtbar), ein falscher **Bezugspunkt** um 2,3–17,5
      (sichtbar). **Die 100 mm sind gleichgültig, der Nullpunkt nicht.**
- [ ] **Bildpositionsregeln gibt es nicht — und das ist das Ergebnis, nicht die Lücke.**
      Regeln der Form „Bauteil X gehört an Bildstelle Y" stehen in der Fachliteratur
      praktisch nirgends. Zur **Stütze** (dem Beispiel des Owners) findet sich keine
      einzige Positionsaussage, nur Aussagen über ihre Funktion. Belegt sind genau zwei
      Konventionen: mittiger Fluchtpunkt innen, und die Horizontlinie aussen — die aber
      nicht gewählt wird, sondern aus der waagrechten Kamera folgt.

      **Die 2/3-Regel des Owners für die Stütze ist damit eine Projektsetzung.** Mit der
      Drittelregel verträglich, keiner Fachaussage widersprechend — aber sie als „so machen
      es Architekturfotografen" auszugeben wäre falsch. Sie kommt gekennzeichnet in den
      Code, mit Datum und Urheber.
- [ ] **Die Drittelregel ist als Beschreibung der Praxis widerlegt**, nicht bloss
      zweifelhaft: Amirshahi et al., *Art & Perception* 2 (2014), ρ = 0,17 über grosse
      Bildkorpora; hochbewertete Fotos zeigen dieselben Werte wie Kontrollbilder.
- [ ] **Die grösste Lücke der Recherche, und sie trifft die Vertiefungsarbeit:** Die
      Fachbücher (Schulz, McGrath, Heinrich) waren nicht im Volltext erreichbar. Alles
      Belegte stützt sich auf Normen, Behördenvorschriften, begutachtete Studien und
      Geometrie — **nicht auf die Lehrbücher des Fachs.** Für die schriftliche Arbeit wird
      das nachzuholen sein, notfalls in einer Bibliothek.
- [x] **Räume aus IFC lesen — erledigt 22.08. (Sitzung 11), die Voraussetzung für alles
      Innere.** `runners/ifc_raeume_runner.py` im `.venv-ifc`, Naht `seams.ifc_raeume`,
      Testgeometrie `make_test_ifc.py --raeume` (zwei Räume, standardmässig aus).
      Gemessen an allen vier Kombinationen IFC4/IFC2X3 × Meter/Millimeter: dieselben zwei
      Räume, 26,62 m² und 5,94 m², Höhen 2,70 m und 2,40 m. Vierzehn Mutationen einzeln
      gekappt, alle vierzehn rot.

      **Die Höhe trägt ihren Bezugspunkt mit:** `z_unten_m` ist die Unterkante des
      Raumkörpers in IFC-Weltkoordinaten — nicht über Meer, nicht über Gelände —, und
      `hoehe_m` die Länge nach oben ab dort. Ob das die lichte Raumhöhe oder die
      Geschosshöhe meint, sagt die Datei nicht, und der Report behauptet es auch nicht.

      **Kein Raum wird stillschweigend weggelassen:** `len(raeume) == n_raeume` ist die
      Zahl der `IfcSpace`; was nicht lesbar war, steht mit `None` und einem benannten
      Befund da. Zwei Urteile je Raum (Grundriss / Höhe), weil eine schiefe Extrusion den
      Bezugspunkt kostet, aber nicht den Fussbodenumriss.

      Ausdrücklich **nicht** mitgebaut: Kamerasetzung im Raum. Die braucht eigene
      Entscheidungen und wäre hier ungeprüft mitgeliefert.
      Offen geblieben: `IfcIndexedPolyCurve` als Profilkurve (moderne Revit-IFC4-Exporte),
      das Auspacken von `IfcBooleanClippingResult`, Aussparungen im Grundriss.
- [x] **Der Innenraum-Standpunkt steht (22.08.), `raumkamera.py`, 24 Tests.** Aus einem
      Raum des Raumlesers werden **beide** Blickarten gerechnet — frontal und über Eck —
      und **gewählt wird anderswo** (Owner-Entscheid 22.08.). Der Grund: Ob frontal oder
      über Eck richtig ist, hängt daran, ob die Stirnwand ein *Motiv* trägt, und das steht
      in keiner IFC-Datei. Ein Programm, das hier entscheidet, tut so, als wüsste es
      etwas, das es nicht wissen kann.

      **Kamerahöhe = halbe Raumhöhe**, ab `z_unten_m` gerechnet — dann bekommen Boden und
      Decke exakt gleich viel Bildfläche. **Keine Ersatzhöhe**, wenn die Raumhöhe fehlt:
      `kameras.AUGENHOEHE_M` (1,70 m) erzeugt in einem 2,55-m-Raum 28 Prozentpunkte
      Ungleichgewicht. **Kamera waagrecht**, Blickziel auf Kamerahöhe — anders als
      `kameras.py`, das kippt. (**Nachgemessen:** um −0,51° bis +5,98°, nicht um die
      vielzitierten 9,46° — die gelten bei 1,2 × Gebäudehöhe Abstand, und dort steht
      `kamerasatz` nie. Siehe unten.)

      Geprüft an den **echten** Räumen des Runners (L-förmig 26,62 m², rechteckig
      5,94 m²), nicht an erfundenen. Mutationsprobe: sechs Kappungen, fünf gefangen — und
      die sechste war der eigentliche Ertrag (siehe unten).
- [x] **Ein Wächter, der nie greift, ist eine tote Kante — auch wenn er richtig gedacht
      ist.** Im Eck-Standpunkt stand eine Abfrage, die einspringende Ecken übergeht. Die
      Mutationsprobe überlebte sie. Die Nachprüfung zeigte warum: An einer einspringenden
      Ecke zeigt die Winkelhalbierende nach **aussen**, und der Lauf nach innen findet von
      dort keinen gültigen Punkt — die Ecke schliesst sich **selbst** aus. Am L-Raum
      nachgemessen: fünf vorspringende Ecken mit Lauf, die einspringende ohne. Der Wächter
      ist entfernt, die Tatsache steht als Test.
- [ ] **Der frontale Standpunkt fasst seine Zielwand nicht immer — und sagt es jetzt.**
      Am L-Raum: 4,10 m vor einer 7,40 m breiten Wand, bei 24 mm davon 6,15 m im Bild.
      Nötig wären 20 mm. Das Sichtfeld wird darum mitgerechnet und mit der **belegten**
      Grenze verglichen (Airbnb: *„never capture wider than 16mm"*). Unterhalb davon macht
      das Objektiv den Raum grösser, als er ist — für ein Projekt, das Geometrietreue
      prüft, wäre das der Fehler, den es finden soll, selbst eingebaut.

      **Was daraus folgt und noch offen ist:** Ein Raum, dessen Wand nicht ins Bild passt,
      braucht die fotografische Kaskade — Türöffnung, Nachbarraum, Teilausschnitt. Davon
      kann dieses Modul nichts.
- [x] **Die Räume hängen an der Kette (22.08.).** `_raeume_lesen` läuft auf dem
      **IFC-Weg** von `baue_kette` — und nur dort. Aus einer glb sind Wände und Böden
      Dreiecke ohne Raumbegriff; wer über `glb_path` einsteigt, bekommt `raeume: None`,
      und das heisst *nicht gemessen*, nicht „dieses Gebäude hat keine Räume". Der einzige
      Moment, in dem die Frage beantwortbar ist, liegt **vor** der Umwandlung.

      Ein Fehlschlag hält die Kette nicht an: Innenaufnahmen sind eine Zugabe, und eine
      Kette, die daran stürbe, lieferte **kein einziges** Bild statt eines ohne
      Innenansichten.

      **Zum zweiten Mal an einem Tag dieselbe Lehre.** Die Mutationsprobe fand, dass sich
      *beide* Verdrahtungszeilen des IFC-Zweigs herausschneiden liessen, ohne dass ein
      Test rot wurde — ich hatte `_raeume_lesen` direkt geprüft und den glb-Zweig, nie den
      IFC-Zweig. **Ein Test am Baustein ersetzt keinen Test an der Naht.**
- [ ] **Was die Standpunkte noch nicht erreichen: den Renderer.** Sie stehen in der
      Ausgabe des Geometrie-Knotens, aber kein Multipass fährt sie. Der nächste Schritt
      wäre, sie als Kameraliste weiterzureichen — und dabei fällt die Entscheidung, wie
      viele Räume eines Gebäudes überhaupt gerendert werden. Das ist eine Betriebs- und
      keine Programmfrage, so wie `AUTO_RICHTUNGEN` aussen.
- [x] **Der Verdeckungstest ist gebaut (22.08.) — die Regel geprüft, der Schuss nicht.**
      `_sicht_frei` im Blender-Runner, als Gegenstück zu `kameras.ziehe_bis_frei`, das die
      Schrittlogik seit Wochen rechnet und die Funktion hereingereicht bekommt.

      **Die Semantik ist die Stelle, an der man sich vertut.** Naiv gefragt — *„trifft der
      Strahl etwas?"* — lautet die Antwort praktisch immer ja, denn das Blickziel liegt
      auf einer Oberfläche. Gefragt ist: *Trifft er etwas, das NÄHER liegt als das Ziel?*
      Ein Test mit der naiven Frage meldete bei **jeder** Kamera eine Verdeckung. Die
      Entscheidungsregel ist diesseits der Prozessgrenze geprüft (sechs Tests, ohne
      Blender); der Strahlenschuss selbst läuft nur am Gerät — `auf-20260822-32`.

      **Ein Fall ohne Vorhersage** steht ausdrücklich im Auftrag: Kamera *in* der Wand.
      Ein Strahl, der in einem Bauteil startet, trifft womöglich sofort dessen Rückseite —
      oder gar nichts, weil Blender Rückseiten je nach Einstellung überspringt. Meldet er
      „frei", während die Kamera steckt, ist das eine Lücke.
- [x] **Der Prompt wird übersetzt — und die Übersetzung wird deklariert (22.08.).**
      `src/aiimaging/sprache.py`, 48 Tests. Anlass ist eine Messung der HomeStation
      (`9a33353`): gepaart über acht Startwerte, gemessen am Blauüberschuss des oberen
      Bildfünftels, ergab der deutsche Prompt **+40,1** gegen **+13,9** englisch — und
      war bei **8 von 8** gleichen Startwerten blauer. Isoliert nachgestellt:
      `overcast sky` +0,3 gegen `bedeckter Himmel` +17,8. Die Vis-Oberfläche sammelt
      deutschen Text und legt ihn wörtlich in `style.prompt`.

      **Owner-Entscheid 21.08.:** übersetzen **und deklarieren** — im Ergebnis stehen
      beide Fassungen nebeneinander (`prompt` und `prompt_original`, dazu der ganze
      Befund unter `prompt_sprache`). Dazu, ebenfalls entschieden: **die QA warnt**, wenn
      ein Prompt nicht englisch aussieht.

      **Glossar als Vorgabe, Modell als Naht.** Das Glossar ist bestimmt (dieselbe
      Eingabe, derselbe Prompt — sonst wäre keine Vergleichsreihe mehr lesbar),
      lizenzfrei und netzlos. Ein Übersetzungsmodell hängt an `uebersetzer` ein, ohne dass
      ein Aufrufer sich ändert. Die Frage, *welches*, ist damit bewusst offen und nicht
      vertagt.

      Verdrahtet an drei Stellen, weil ein Prompt auf drei Wegen ankommt:
      `kosmo_szene.lies_szene` (Oberfläche), `prompts.komponiere` (Bibliothek),
      `render` (von Hand gebauter Auftrag — dort nur noch die Warnung).
- [x] **Vier Fehler beim Bauen, die alle dieselbe Form hatten: eine Meldung, die schweigt.**
      (1) `unbekannt` meldete `()` für „evening light with **langen** shadows" — es suchte
      nur nach Umlauten und Signalwörtern, und `langen` hat weder. Ein halb übersetzter
      Prompt, der sich selbst für vollständig hält, ist schlimmer als gar keiner.
      (2) `sprachwarnung` schwieg zu `Sichtbeton`, das die Übersetzung unmittelbar davor
      erkannt hätte — **zwei Antworten auf dieselbe Frage im selben Programm**; jetzt
      beantwortet sie `ist_deutsch` an einer Stelle.
      (3) Der Abholer reichte `auftrag["warnungen"]` **gar nicht weiter**: eine tote Kante
      auf dem Weg der Warnung selbst.
      (4) `ENGLISCH_AUCH` nannte acht Wörter, die im Glossar gar nicht vorkommen — Vorsicht,
      die vor nichts schützt. Ein Test hält die Liste jetzt an ihre Schlüssel.
- [x] **Ein Test, der aus dem falschen Grund grün war.** `test_laengste_wendung_zuerst`
      prüfte „bedeckter Himmel" und „keine Menschen" — und überlebte die Mutation
      `-len(s)` → `len(s)`. Grund: Bei beiden ergibt die Wort-für-Wort-Übersetzung
      zufällig dasselbe wie die Wendung (`keine`+`menschen` = `no`+`people`). Der Test
      prüfte also nie die Reihenfolge. Ersetzt durch `hell gestrichen` (wo es
      auseinandergeht) **und** durch eine Eigenschaft über das ganze Glossar, damit die
      Regel auch für morgen hinzugefügte Wendungen geprüft bleibt.
- [x] **Das Glossar kann jetzt Grammatik — zwei Regeln, und der Ertrag ist gemessen.**
      Erst gemessen, dann gebaut: An dreizehn Prompts, wie sie aus der Oberfläche kommen
      könnten, war mit dem blossen Nachschlagewerk **einer von dreizehn** vollständig
      übersetzt. Das war deutlich schlechter, als meine zwei Beispiele hatten ahnen
      lassen. Die Lücken lagen in drei Klassen: gebeugte Wörter (12 von 23), Komposita
      (5), schlicht fehlende Wörter (5).

      `grundform` streift Endungen ab und schlägt nach — sie kann finden, nicht erfinden.
      `zerlege_kompositum` teilt in zwei Glossarteile. Dazu rund 30 neue Einträge
      (Himmelsrichtungen, Jahreszeiten, `seite`, `struktur`). Danach: **dreizehn von
      dreizehn.**

      Nicht behauptet wird gutes Englisch: „die Fassaden der Stadt" wird zu „the facade
      the city". Für eine Aufzählung durch Kommata trägt das, für einen Satz nicht.
- [x] **Die Wahl der Endungen ist keine Kleinigkeit — zwei Befunde in beide Richtungen.**
      `s` musste weichen: Ein Test fing `Dachs` → `dach` → `roof`, und in einem Modul,
      das gegen erfundene Dächer gebaut ist, ist das die denkbar falscheste Sorte Fehler.
      `n` flog im selben Zug mit heraus und **musste zurück**: Der reguläre Plural der
      Feminina bildet sich damit (`Fassade` → `Fassaden`), und ohne die Endung bleibt
      jede Mehrzahl stehen. Zwei Endungen, die gleich aussahen, und nur eine war das
      Risiko.
- [x] **Ein Wächter, der wirklich greift — nachgewiesen statt behauptet.** Die Regeln
      laufen im zweiten Durchgang über bereits übersetzten Text und dürfen dort nichts
      anfassen. Ob dieser Schutz je nötig ist, war offen; über alle englischen Wörter
      unserer Übersetzungen geprüft, gibt es **genau einen** zerstörerischen Fall:
      `under` → `und` → „and". Ihn fängt der Wächter. Der Fall ist nicht theoretisch —
      gemischte Prompts zählen ausdrücklich als nicht englisch und gehen durch die
      Übersetzung.
- [ ] **Was die Regeln weiterhin nicht können.** Ein Kompositum, dessen Teil fehlt
      (`Fensterbank`), eine unregelmässige Form ohne Stammeintrag, und die Mehrzahl
      (`Fassaden` wird zu `facade`, nicht `facades`). Alles davon wird **gemeldet**, nicht
      stillschweigend durchgereicht. Ob das genügt oder ob ein Übersetzungsmodell an die
      Naht gehört, entscheidet sich an echten Eingaben der Oberfläche.
- [ ] **Die Zielwand wird nach LÄNGE gewählt, und das ist eine schwache Setzung.** Die
      Praxis wählt die Wand mit dem Motiv. Ein Kamin oder eine Küchenzeile ist ein Motiv
      und hat keine Öffnung; die längste Wand ist oft, aber nicht immer, die richtige. Der
      Hinweis steht bei jedem Standpunkt.
- [x] **Die waagrechte Kamera steht (22.08.), `kameras.MODUS_SHIFT`, 24 Tests.**
      Additiv: `MODUS_GEKIPPT` bleibt Vorgabe, jede bisher gemessene Aufnahme bleibt
      reproduzierbar. Der Grund für den Umbau ist die Norm und **nicht** die Bildqualität
      — `auf-29` hat gemessen, dass die Kippung dem Tiefenschätzer nichts nimmt (über Eck
      −0,9835 gekippt gegen −0,9650 waagrecht, alle drei innerhalb von 0,019). Wer den
      Modus wählt, wählt die Norm, nicht eine bessere Zahl.

      **Der Kern in einem Satz:** `shift_mm = brennweite · tan(Neigung)`. In
      Tangenseinheiten *ist* der Shift der Winkel, um den sonst gekippt würde. Verdrahtet
      bis ans Gerät: `kamerasatz` → `seams` → `--kamera-modus` / `--shift-y` →
      `kam_daten.shift_y`, und der Abholer reicht ihn durch.
- [x] **Nachgemessen — zweimal, und beide Male anders als behauptet: `kameras.py` kippt
      um −0,51° bis +5,98°.** Die Zahl 9,46° steht in vier Dokumenten dieses Projekts.
      Sie ist `atan(0.20 / 1.2)` und gilt bei einem Abstand von **1,2 × Gebäudehöhe** —
      den `kamerasatz` nie einnimmt: `DECKUNGSGRAD = 0.55` stellt die Kamera auf
      2,5–5,5 × Gebäudehöhe.

      **Meine erste Richtigstellung (1,92°–4,70°) war ebenfalls zu eng.** Sie stammte aus
      vier Gebäudehöhen und **zwei** Formaten — quer und quadratisch. Die HomeStation
      fuhr am selben Tag ein Hochformat (`auf-33`) und mass 5,985°; nachgerechnet stimmt
      das auf 0,01° mit unserer Rechnung überein. Negative Werte kommen von flachen
      Bauten, wo `ZIEL_HOECHSTANTEIL` das Blickziel unter die Augenhöhe holt — die hatte
      ich sogar gesehen und nicht in die Spanne aufgenommen.

      **Die Lehre ist nicht die Zahl, sondern der Weg:** Eine Spanne, die aus einer
      Stichprobe stammt, ist eine Aussage über die Stichprobe.

      Das ändert das Urteil nicht (2° Konvergenz sind auch Konvergenz), aber die
      Grössenordnung — und die andere Seite derselben Rechnung ist eine gute Nachricht:
      Der nötige Shift beträgt **0,94–2,30 mm** gegen die 12 mm, die ein wirkliches
      Objektiv leistet. Der normgerechte Modus ist nicht an der Grenze des Machbaren,
      sondern weit innerhalb.
- [x] **Der Rahmen wird durch den Shift unsymmetrisch — und das ist die ganze Wirkung.**
      Oben `grenze_v + s`, unten `grenze_v − s`. Ob ein Shift Abstand *kostet* oder
      *spart*, hängt daran, welche Kante bindet: Beim hohen Turm bindet das Dach, und die
      Kamera darf näher heran; beim flachen Bau aus der Nähe bindet der Fuss, und sie
      muss weiter weg (der Term aus Recherche §4.3, den man übersieht). Der erste Anlauf
      des Tests prüfte einen breiten, niedrigen Bau — dort bindet die **Breite**, und der
      Shift änderte gar nichts. Er wäre grün geworden und hätte nichts gezeigt.

      Gegenprobe an einer belegten Zahl: Bei 24 mm Sensorhöhe verlässt die Achse den
      Rahmen bei genau 12 mm Shift — der Horizont sitzt dann auf der Bildunterkante
      (Recherche §4.4), **unabhängig von der Brennweite**, weil Rahmengrenze und Versatz
      dasselbe `f` im Nenner tragen.
- [x] **Ein Gleitkomma-ULP zwischen „unmöglich" und „1,5 · 10^16 Meter".** Genau am
      Grenzfall oben ist `grenze_v` rechnerisch gleich dem Versatz, im Gleitkomma aber um
      ein ULP daneben. Auf der falschen Seite lieferte die Umstellung keinen Fehler,
      sondern einen Rückschub mit sechzehn Stellen. Der Vergleich ist jetzt relativ
      (`DEGENERIERT_ANTEIL`). Gefunden nicht durch Nachdenken, sondern weil ein Test an
      der belegten 12-mm-Zahl auf die Grenze zielte.
- [x] **Der Sensorbezug wird ausdrücklich gesetzt, nicht Blender überlassen.**
      `kameras.bildwinkel` legt die Sensorbreite auf 36 mm fest; Blenders Vorgabe `AUTO`
      bezieht sie auf die **grössere** Bildkante. Für quer und quadratisch dasselbe — und
      alle bisherigen Läufe waren quer oder quadratisch, weshalb es nie auffiel. Im
      **Hochformat** gingen unser Bildwinkel und Blenders auseinander, still und in beide
      Richtungen. Der Hausstil ist quadratisch bis hochformatig; der Fall steht bevor.
      `sensor_fit = 'HORIZONTAL'` steht jetzt im Runner — **am Gerät ungeprüft**,
      `auf-20260823-33` Fall S4.
- [ ] **Was am Shift noch ungemessen ist: alles jenseits der Prozessgrenze.**
      Ob Blender `shift_y` so annimmt, wie wir es meinen, ob die Senkrechten im Bild
      wirklich senkrecht werden, ob der Umbau für den gekippten Modus wirklich bitgleich
      additiv war — `auf-20260823-33` fragt genau das, in fünf Fällen und ohne Bildmodell.
- [x] **`komposition.py` war ein halbes Jahr lang ungerufen — jetzt hängt es am Lauf.**
      1400 Zeilen fotografisches Regelwissen mit Belegstufen, Quellenangaben und 117
      eigenen Tests, und **kein einziger Produktivweg** hat je eine seiner Zahlen gesehen.
      Das ist die tote Kante dieses Projekts in ihrer bisher grössten Ausführung, und sie
      fällt nicht auf: Ein ungenutztes Modul ist grün wie jedes andere, seine Abdeckung
      sieht vorbildlich aus, die Suite meldet nichts.

      Angeschlossen über `beurteile_bericht`, das den Kamerablock des Multipass-Berichts
      liest — die Beurteilung läuft diesseits der Prozessgrenze, weil sie reine
      Arithmetik ist und im Runner eine Fähigkeit wäre, die ohne Blender niemand hat
      (Regel 4). Der Abholer hängt sie an **jede** Kamera.

      Die Wahrheitstafel, die dabei herauskommt, zeigt, dass die Prüfung wirklich
      unterscheidet: gekippt + unerklärter Boden → zwei Warnungen; gekippt + erklärter
      Boden → nur die Normverletzung; Shift + unerklärter Boden → nur der Bezugspunkt;
      Shift + erklärter Boden → **nichts zu melden**.
- [ ] **Drei weitere Module ruft nur ihr Test — aber aus anderem Grund.** `lora.py`,
      `stilstudie.py` und `varianten.py` (zusammen rund 1800 Zeilen) stehen ebenfalls in
      keinem Produktivpfad. Anders als `komposition.py` sind sie aber **absichtlich**
      Werkzeuge zum gezielten Aufruf — ein Trainingslauf, eine Kalibrierung, eine
      Vergleichsreihe —, und Regel 4 verlangt nur, dass sie aus Python heraus benutzbar
      sind. Sie sind also nicht dasselbe. Offen bleibt, ob sie es je werden.
- [x] **Die Seedauswahl behält das beste Bild — und sagt jetzt, ob der Vorsprung einer ist.**
      Behalten ist richtig: Man nimmt den besten Wurf, den man hat. Die *Behauptung*
      „Startwert X ist besser" hält aber nur, wenn der Abstand grösser ist als das
      Rauschen der Kette — und aus ihr folgt, dass man diesen Startwert künftig bevorzugt.

      Geprüft wird gegen den **unabhängig** gemessenen Boden (0,2269 aus neun Läufen),
      nicht gegen die Streuung derselben drei Werte: Wer den Bestwert einer Reihe an
      ihrer eigenen Streuung misst, misst im Kreis. Und gegen den **Zweiten**, nicht gegen
      den Letzten — sonst ist fast jeder Vorsprung „belegt".

      Unbequemes Ergebnis: Selbst der oft zitierte Fall ρ = −0,91 gegen −0,27 ist damit
      **nicht** belegt (Abstand 0,29 gegen eine Grenze von 0,454).
- [x] **0,2269 stand an neun Stellen in Prosa und an keiner als Wert.** Jetzt
      `varianten.GEMESSENE_SEED_STREUUNG`, mit Herkunft und mit der Grenze dazu: Sie ist
      an *einem* Aufbau gemessen und taugt als Grössenordnung, nicht als Naturkonstante.
      Eine gemessene Grösse, die nur in Kommentaren lebt, kann nicht rechnen und veraltet
      an acht Stellen gleichzeitig.
- [x] **Der Verdeckungstest trägt — und V3 hat keine Lücke (`auf-32`, am Gerät).**
      Alle vier vorhergesagten Fälle sind eingetroffen. Der Fall **ohne** Vorhersage —
      Kamera *in* der Wand — ist beantwortet: Blender meldet die Rückseite bei genau der
      halben Wandstärke, in **beide** Blickrichtungen. Rückseiten werden nicht
      übersprungen.

      **Meine notierte Grenze war falsch, und der Worker hat sie nachgemessen statt
      stehenzulassen.** Ich hatte vermutet, eine sehr dünne Wand könne durchrutschen (bei
      4 cm läge die Rückseite bei 2 cm, innerhalb der Toleranz von 5 cm). Gemessen von
      30 cm bis 2 cm: **jede** Stärke wird als verdeckt gemeldet. Der Grund ist die
      Semantik der Toleranz — sie misst gegen das **Ziel**, nicht gegen die Kamera. Bei
      einem Ziel in 14 m liegt ein Treffer nach 1 cm dreizehn Meter davor.

      Die Toleranz selbst ist nachgemessen: bis 4 cm im Bauteil frei, ab 5 cm verdeckt —
      wirksam ist also „echt kleiner als 5 cm". In allen sechs Fällen, in denen ein Ziel
      auf einer Fläche lag, wurde sie **gar nicht gebraucht**: Treffer und Ziel fielen
      exakt zusammen.
- [x] **`IfcSpace` steckte als massives Mesh in der glb — gefunden neben dem Auftrag.**
      Der wertvollste Teil von `auf-32` stand gar nicht im Auftrag: Der Verdeckungstest
      stiess darauf, weil sein getroffenes Objekt in einem Raum nicht die Wand war,
      sondern der **Raumkörper selbst**. Sieben Meshes in der glb, davon zwei `IfcSpace`.

      Ein `IfcSpace` ist Luft; als Mesh ist es ein massiver Quader, und eine
      Innenaufnahme steht mitten darin. Die Tiefenkarte sähe eine graue Fläche
      unmittelbar vor dem Objektiv — in **jedem** Raum, in dem je gerendert wird.
      Aufgefallen wäre das erst beim ersten Innenraum-Render, und dann als „das
      Bildmodell liefert Grau". Genau die Fehlerart, die dieses Projekt am teuersten
      bezahlt.

      `NICHT_GEBAUTE_SUBSTANZ` im Konversions-Runner überspringt jetzt fünf Typen, jeden
      mit eigenem Grund, und **zählt sie im Report**. Mit auf der Liste steht
      `IfcOpeningElement`, obwohl unsere Testgeometrie keinen hat: Er ist der
      *Ausschnitt*, nicht das Bauteil — wer ihn mitnimmt, mauert jedes Fenster mit einem
      Körper zu, der genau die Fensterform hat. In jeder echten IFC kommt er vor.

      Geprüft **ohne** `ifcopenshell` (die Liste ist eine Liste von Namen und eine reine
      Funktion darüber) — eine Regel, die sich nur dort prüfen liesse, wo die Bibliothek
      liegt, würde nie geprüft. Die Konversion selbst ist damit **nicht** geprüft:
      `auf-20260823-34`.
- [ ] **Über die Eck-Standpunkte sagt der Verdeckungstest wenig.** Ihr Blickziel liegt im
      offenen Raum, nicht auf einer Fläche: `getroffen=False`, und geprüft ist damit nur,
      dass *nichts* dazwischensteht. Beim frontalen Standpunkt liegt das Ziel auf der
      Wand und der Test greift voll. Kein Fehler, aber eine ungleiche Absicherung — und
      sie steht hier, damit niemand beide für gleich geprüft hält.
- [x] **`AUTO_RICHTUNGEN` steht auf drei Ansichten (Owner-Entscheid 23.08.2026).**
      `("s", "sSE", "nNW")` — eine frontale und zwei über Eck. Die beiden Eckansichten
      liegen **exakt 180° auseinander** (nachgerechnet, nicht geschätzt: 145° und 325°)
      und zeigen zusammen alle vier Fassaden. Das ist die eigentliche Aussage der Norm —
      ein Bauwerk wird nicht von einer Seite dokumentiert.

      Die vierte HABS-Ansicht (Umgebung) ist weggelassen: Sie zeigt ohne echtes Gelände
      wenig, und Gelände haben wir nicht. Für Messreihen bleibt die einzelne Richtung die
      saubere Wahl — `verarbeiter(auto_richtungen=("sSE",))`. Drei Standpunkte
      verdreifachen die Renderzeit je Auftrag; das war der Grund, warum die Entscheidung
      dem Owner gehörte.
- [x] **Arbeitsbrennweite steht auf 35 mm (Owner-Setzung 23.08.2026) — und die Recherche
      sagt etwas anderes.** Der HABS-Objektivsatz (umgerechnet 18/25/42/59 mm) und die
      heutige Ratgeberliteratur treffen sich unabhängig bei **24–25 mm**. Der Owner hat
      35 mm gewählt und es ausdrücklich als eigene Vorliebe benannt.

      **Der Widerspruch bleibt sichtbar statt weggeräumt.** `kameras.BRENNWEITE_MM` trägt
      die Setzung mit ihrem Datum und dem Gegenbeleg daneben;
      `komposition.ARBEITSBRENNWEITE_AUSSEN_MM` bleibt bei 24 mm, weil jenes Modul führt,
      was das Fach sagt, und nicht, was das Projekt entscheidet. Ein Modul, das seine
      Belege an die Vorgaben anpasst, ist kein Beleg mehr.

      **Nachgemessen, was der Wechsel kostet:** Die Kamera steht rund 19 % weiter weg
      (bei 15 m Bauhöhe 106 statt 90 m), der Füllgrad bleibt beim angeforderten Wert, der
      sichtbare Flächenanteil steigt sogar leicht (0.0623 → 0.0672), und kein Eckentest
      schlägt fehl.
- [x] **Einstellbar heisst bis an die Naht, nicht nur im Modul.** Die automatischen
      Richtungen fuhren bisher **ohne** Brennweitenangabe — die Zahl kam erst im Runner
      aus der Konstante, und ein Betreiber konnte sie je Lauf gar nicht setzen.
      `verarbeiter(brennweite_mm=…)` reicht sie jetzt durch; `None` heisst weiterhin
      „nicht angefasst", nicht „null".
- [x] **Zwei abgeschriebene 28er gefunden, die still auseinandergelaufen wären.**
      `kosmo_szene` setzte beim Umsetzen in den fremden Vertrag `28.0` als Rückfall — eine
      Kamera ohne eigene Brennweite wäre mit 28 mm hinausgegangen, während mit 35
      gerendert wird. Und ein Test hatte die 28 abgeschrieben statt die Konstante zu
      lesen. Beide lesen jetzt `kameras.BRENNWEITE_MM`. Abgeschriebene Zahlen veralten
      still — dasselbe Muster wie bei 0,2269 und bei den 9,46°.
- [x] **Drei Ansichten haben das Gate stiller verschärft, als irgendjemand entschieden
      hatte.** Das Geometrie-Urteil eines Auftrags ist das seiner **schwächsten** Kamera —
      gut begründet, denn ein Auftrag ist so gut wie sein schlechtestes Bild. Aber ein
      Minimum fällt mit der Zahl der Ziehungen: bei drei um **0,845 Streuungen**
      (Extremwertstatistik, simuliert und gegen die geschlossenen Werte für N ≤ 5
      geprüft).

      Wäre die Streuung zwischen Kameras so gross wie die einzige gemessene (0,2269 über
      Startwerte), kostete der Wechsel rund **0,19** — mehr als jeder Parametereffekt, den
      die Kette je gezeigt hat (0,10–0,14). Die Entscheidung galt der Renderzeit; diese
      Folge stand nicht zur Debatte, weil sie niemand gesehen hatte.

      **Die Regel bleibt, ihre Sichtbarkeit ändert sich:** `kameraspanne` hängt am
      Geometrie-Urteil und trägt n, bester, schlechtester, Spanne, Streuung und den
      Abschlag — samt dem Satz, dass ein Ergebnis aus drei Kameras nicht mit einem
      älteren aus einer verglichen werden kann.
- [x] **Alles Gemessene landete nirgends — jetzt gibt es `befund.json`.**
      Der fremde Vertrag führt genau `images`, `qa` und `timings`; alles Übrige streicht
      `nur_vertragsfelder` heraus, und das ist richtig so. Nur hiess das bis zum
      23.08.2026, dass **nichts davon irgendwo landete**: Kompositionsbefund je Kamera,
      Kameraspanne, Maskenbefund, Einordnung gegen den Nullanker, Sprachurteil über den
      Prompt, Warnungen des Auftrags — gerechnet, in ein Wörterbuch gelegt, mit dem
      Prozess vergessen. Geschrieben wurde einzig die Seedauswahl.

      `CLAUDE.md` sagt den Satz, um den es geht: **Was nicht in einer Datei steht, ist
      weg.** Er stand dort für die Sitzungsprotokolle; er gilt für Messwerte genauso.

      Der Befund liegt neben dem Vertragsergebnis, wird **nach** ihm geschrieben (die
      Reihenfolge, an der die fremde Oberfläche hängt, darf er nicht stören) und kostet
      den Lauf nicht, wenn er scheitert — dann steht es im Grund der Antwort, statt zu
      schweigen.
- [x] **Regel 3 wäre am ersten Befund wieder aufgegangen.** Er liegt im
      Auftragsverzeichnis der fremden Oberfläche, und ein absoluter Pfad trägt
      Rechnernamen und Benutzerkonto nach draussen. `_ohne_pfade` kürzt rekursiv durch
      Wörterbücher und Listen; ein Test liest die geschriebene Datei als **Text** und
      sucht nach `"/` — nicht nach einzelnen Feldern, denn geprüft gehört, was wirklich
      auf der Platte steht.
- [x] **Der Befund wird gelesen, nicht nur geschrieben — sonst wäre er die nächste tote
      Kante.** Eine Datei, die niemand liest, ist die geduldigste Form davon: Sie fällt
      nie auf, und wenn eines Tages jemand hinsieht, steht seit Monaten Unsinn darin.
      `tools/abholen.py` liest sie darum wirklich und zeigt dem Betreiber vier Dinge, die
      eine Entscheidung auslösen könnten — dass der Prompt übersetzt wurde (und ob ganz),
      die Kameraspanne samt der Zahl, aus wie vielen das Urteil das schlechteste ist,
      welche Kameras die Kompositionsprüfung beanstandet, und ob der Vorsprung des
      gewählten Startwerts belegt ist.

      **Zeilen ohne Inhalt entfallen ganz.** Eine Ausgabe, in der jede Zeile immer
      dasteht, liest sich nach dem dritten Mal wie eine leere — und dann übersieht man
      auch die eine, die zählt.

      Getrennt gehalten: „geprüft und beanstandet" gegen „gar nicht beurteilbar". Wer sie
      zusammenwirft, hält eine Lücke für ein Urteil.
- [x] **Das Auftragsurteil bleibt das der schwächsten Ansicht (Owner-Entscheid
      23.08.2026).** Zur Wahl standen der Median (fällt nicht mit N, lässt aber eine
      wirklich schlechte Ansicht hinter zwei guten verschwinden — und Halluzinationen
      zeigen sich oft nur aus einer Richtung) und eine an N angepasste Schwelle
      (rechnerisch sauber, praktisch nicht belastbar: Es hiesse, eine **nicht
      kalibrierte** Schwelle um eine **ungemessene** Streuung zu korrigieren; zwei
      unsichere Zahlen ergeben keine sichere).

      Am Code ändert das nichts. Was zählt, ist die Begründung: Die Regel ist innerhalb
      eines festen N vergleichbar, über ein wechselndes N erkennbar nicht — und seit
      heute trägt jedes Ergebnis mit, aus wie vielen Ansichten es das Minimum ist.
- [x] **Drei Startwerte je Kamera (Owner-Entscheid 23.08.2026), vorher einer.**
      Den Ausschlag gab die Kostenrechnung: Der Multipass kostet rund **97 s je Kamera**,
      ein Bild des Bildmodells rund **1,3 s**. Startwerte sind damit billig neben
      Ansichten — der Multipass wiederholt sich je Startwert *nicht*. Und die
      Seed-Streuung (0,2269) ist grösser als jeder Parametereffekt der Kette; die Auswahl
      ist der billigste Qualitätssprung, den es hier gibt.

      **Feste Werte `(0, 1, 2)`, nicht gewürfelt** — ein zufälliger Startwert machte jeden
      Lauf unwiederholbar, und ohne Wiederholbarkeit gibt es keine Vergleichsreihe.
- [x] **Eine Warnung, die immer feuert, ist kein Signal — am eigenen Ausgabetext
      gemessen.** Ohne Geländestand meldet die Kompositionsprüfung für **jede** Kamera
      dieselben zwei Warnungen: unzuverlässiger Bezugspunkt und Neigung. Nachgezählt:
      **zwölf von zwölf**, immer dieselben. Das ist dasselbe Versagen wie ein Wächter,
      der nie greift, nur von der anderen Seite — und es traf ausgerechnet die Zeile, die
      seit heute auf dem Terminal des Betreibers steht.

      Beide Warnungen sind **richtig**. Der Bezugspunkt ist aus einer glb gar nicht
      besser zu wissen (dort gibt es kein Gelände), und die Neigung bleibt, bis die
      Vorgabe auf `MODUS_SHIFT` wechselt. Sie sind keine Befunde über *diesen* Auftrag,
      sondern Eigenschaften der Eingabe — und gehören einmal genannt, nicht dreimal.

      Was **nur einen Teil** der Kameras betrifft, steht weiterhin einzeln da. Das ist
      die Zeile, die jemanden hinsehen lässt.
- [x] **Wieder ein Wächter, der nie greift — diesmal von mir, im selben Zug.** Der
      `if not beurteilt: return`-Vorbehalt in der Zusammenfassung überlebte die
      Mutationsprobe, weil die Rechnung darunter bei leerer Eingabe ohnehin nichts
      ergibt. Entfernt, die Tatsache steht als Test — dieselbe Entscheidung wie bei der
      einspringenden Ecke in `raumkamera`.
- [x] **Der Geländestand ist jetzt wenigstens SETZBAR — die Warnung war da, der Handgriff
      fehlte.** Die Kompositionsprüfung meldet bei jedem Auftrag den unzuverlässigen
      Bezugspunkt, zu Recht. Nur konnte ein Betreiber ihn bis zum 23.08.2026 gar nicht
      angeben: `verarbeiter` nahm ihn nicht entgegen, obwohl Naht und Runner ihn seit
      langem kennen. Eine Dauerwarnung ohne Handgriff ist keine Warnung mehr, sondern
      Möblierung.

      **Dieselbe Lücke wie bei der Brennweite:** im Modul längst einstellbar, auf dem
      Weg, den ein Auftrag nimmt, nicht. Zweimal am selben Tag dieselbe Form —
      offensichtlich ist „einstellbar" eine Zusage, die man an der Naht prüfen muss und
      nicht am Modul.

      Die Zeile auf dem Terminal nennt den Handgriff jetzt mit
      (`--gelaende-z setzen, dann entfällt das`). Aus der Klage wird ein Angebot.
- [ ] **Der Geländestand ist aus einer glb nicht zu ERFAHREN — nur zu sagen.** Der fremde Vertrag führt
      keine Geländeangabe, und in einer glb gibt es kein Gelände. Solange das so ist,
      rechnet `kamerasatz` mit der Hüllbox-Unterkante — bei einem Bauwerk mit
      Untergeschoss steht die Kamera damit im Keller. Aus der IFC wäre es zu haben; der
      Weg dorthin führt über den Vertrag und ist keine Programmfrage.
- [x] **Eine fremde Eichung hat unseren Umrissanteil erledigt — und unsere Fassung hatte
      denselben Defekt, nur halb verdeckt.** `docs/EICHUNG_2026-08-23.md` (HomeStation)
      prüfte dieselbe Idee in zwei Fassungen und zog sie zurück: In der relativen Fassung
      erreichen grau und ein Verlauf **100 %** — wo der Gradient überall gleich ist, ist
      „über dem 95. Perzentil" für jeden Punkt wahr. Das Mass belohnt dann
      Strukturlosigkeit, also genau die Krankheit von `geom_iou`.

      Nachgemessen an unseren drei Nullankern: grau meldete 100 % gegen einen Nullwert
      von 100 % (und fiel richtig durch), ein **Verlauf** aber 100 % gegen 93,9 % — und
      galt als „über Zufall". Rechnerisch richtig, inhaltlich nichts: Wo 94 % aller
      Bildpunkte als „stärkste 5 %" gelten, sagt ein Anteil von 100 % an der Grenze nichts.

      **Zwei Berichtigungen:**
      (1) Trennt die Schranke nicht (`zufall > MAX_ZUFALL_FAKTOR · verlangt`), ist das
      Mass **nicht messbar** und liefert `anteil = None`. Eine Zahl mit Fussnote wird
      ohne die Fussnote weitergereicht — `paarurteil` verglich sie mit 0.20, und ein
      reiner Verlauf bestand das zweite Bein.
      (2) „Über Zufall" verlangt jetzt **zwei Binomialstreuungen** Abstand statt eines
      strikten `>`. Bei 92 Grenzpunkten ist die Streuung rund 2,3 Prozentpunkte; 5,43
      gegen 5,06 war nichts.

      **Danach verhalten sich alle vier Anker richtig:** grau und Verlauf nicht messbar,
      **weisses Rauschen messbar und NICHT über Zufall** (vorher galt es als Signal), das
      perfekte Bild deutlich darüber.
- [x] **Variante F ist tot — und der Grund trifft die ganze Geometrie-QA.** Die HomeStation hat selbst darum gebeten (`auf-vis-20260823-06`): Bänder
      nur dort messen, wo das Soll Himmel führt, senkt den relativen Szenenabstand von
      42,4 % auf 11,3 %. Ihre Begründung ist präzise und darum prüfbar — die
      Szenenabhängigkeit kommt vom **Anteil Himmel hinter der Silhouette**.

      **Meine erste Vorgabe dazu war falsch, und die HomeStation hat es gemerkt, bevor
      ich es gemerkt habe.** Ich verlangte ein Extrem mit 90–100 % Himmel — das Argument
      (ein Extrem belastet stärker als eine weitere Mitte) war richtig, die Richtung
      falsch: **Bei 100 % Himmel hat F nichts einzuschränken, F *ist* dort A.** Genau das
      hat sie gemessen (+0.2710 für beide) und den Vorbehalt selbst dazugeschrieben.

      Ihre drei Szenen stehen und sind gut: F streut mit ±11 % halb so stark wie A mit
      ±26 %, die Schwelle 0.15 trennt auf allen dreien. Was sie **nicht** zeigen, ist der
      Fall, für den F gebaut wurde.

      `auf-36` ist darum neu geschrieben und fragt jetzt das Gegenteil: **wenig Himmel**
      (10–20 %), wo A am stärksten versagt und F am meisten leisten muss. Dazu eine
      Frage an die *Bauart*: Was tut F, wenn **gar kein** Himmel dahintersteht — dichter
      Hof, Nachbarwand, Mulde? Dann bleiben ihm kaum Grenzabschnitte, und die richtige
      Antwort ist vermutlich „nicht messbar" und nicht „eine Zahl aus sieben Punkten".
      Denselben Fehler haben wir heute an `kantenanteil` korrigiert.
      **Erledigt am 23.08.2026, und zwar anders als geplant** (`auf-vis-20260823-07`).
      Der Owner hatte entschieden, F erst an geneigtem Gelände zu prüfen — die richtige
      Reihenfolge, denn genau dort ist F durchgefallen. Drei Szenen, dieselbe Kamera,
      dasselbe Bauwerk, nur der Hintergrund verschieden:

          g0 flach        63,3 % Himmel     F +0,4227   A +0,4267
          g1 geneigt       0,0 %            F nicht rechenbar   A +0,1442
          g2 Nachbargebäude 0,0 %           F nicht rechenbar   A +0,0016

      F braucht Himmel hinter dem Umriss, und in beiden nicht-flachen Szenen gibt es
      keinen. Das ist keine Ungenauigkeit, sondern eine fehlende Grundlage — **und in der
      Stadt ist das der Normalfall.** F wird nicht gebaut; `auf-36` ist damit gegenstandslos.

      **Der grössere Befund liegt aber bei A, dem Mass, das wir benutzen.** In g2 misst A
      am perfekten Bild +0,0016 gegen einen Rauschanker von −0,0024 — es trennt dort ein
      perfektes Bild nicht mehr von weissem Rauschen. Der Mechanismus liegt nicht im Mass:
      Der Nachbar steht im Soll 15,05 m weiter hinten, der Schätzer legt beide nur 3,0 %
      der Kartenspanne auseinander. Ein monokularer Schätzer hat für zwei ähnliche
      Betonkörper in 34 und 49 m keinen Bildhinweis. Die Gegenprobe macht es endgültig:
      Der **wahre** Sprung ist in g2 am grössten, der **gemessene** dort am kleinsten —
      die Beziehung ist umgekehrt.

      Die HomeStation hat den Vorschlag ausdrücklich nicht als Empfehlung markiert und
      dazugesagt, dass sie für die Stadtfälle keinen guten Einfall hat. Das ist die
      richtige Auskunft: **ungemessen** ist, ob ein grösserer Schätzer die 15 m auflöst —
      dann wäre der ganze Befund eine Frage der Modellgrösse und keine des Masses.
- [x] **Das zweite Bein schweigt jetzt, wo es nichts messen kann** (23.08.2026).
      Umgesetzt ist genau der Vorschlag aus `auf-vis-20260823-07`: `himmel_hinter_umriss`
      liest **aus dem Soll** (nicht aus der Schätzung), wieviel des Umrisses Himmel hinter
      sich hat, und `paarurteil` fällt kein Urteil, wo dieser Anteil unter 10 % liegt —
      `zustaendig: False`, `bestanden: None`, mit benanntem Grund.

      **Warum aus dem Soll.** Eine Zuständigkeitsprüfung, die das Ergebnis der Messung
      braucht, ist keine. Die Soll-Karte liegt in dieser Kette immer vorher vor; die Frage
      *«kann hier überhaupt gemessen werden»* ist damit **vor** dem ersten Renderlauf
      beantwortbar.

      **Warum schweigen und nicht durchfallen.** Nicht messbar ist weder bestanden noch
      durchgefallen — dieselbe Unterscheidung wie heute schon zweimal (`kantenanteil`
      ohne trennende Schranke, `minimum_abschlag` jenseits der Tabelle). Ein grünes
      Abzeichen wäre hier in die **gefährliche** Richtung falsch, ein rotes bloss unfair.

      Die 10 % sind eine **Setzung**, kein Ablesewert: Zwischen 0 % (misst nichts) und
      63 % (misst) liegt nichts Gemessenes. Wer die Lücke füllt, ändert die Zahl.

      Und weil dieses Projekt dieselbe Fehlerart heute dreimal gefunden hat, steht die
      dritte Antwort auch im Kurzbefund: `befund_kurz` nennt die Kameras, deren Umrisstreue
      nicht messbar war. Ein „nicht zuständig", das niemand sieht, ist ein bestandenes Tor
      mit Extraschritt.

      **Offen bleibt die Stadtfrage.** Ist der Hintergrund verbaut, beantwortet heute
      *niemand* die Existenzfrage — ρ beantwortet die Richtigkeit und ersetzt sie nicht.
- [x] **Fünf Felder der Bestellung erreichen nichts — gezählt, gemeldet, nicht
      stillschweigend repariert** (23.08.2026). Anlass sind die zwei Fehler desselben
      Tages: Brennweite und Geländestand waren im Kern einstellbar und kamen an der
      Aussenkante nicht durch. Daraufhin umgedreht und abgezählt, welche Felder aus
      `kosmovis.render-scene/v1` unsere Kette wirklich erreichen — **zehn ja, fünf nein**:

      * `render.sun` — **der gefährlichste.** Die Sonne steht in `blender_depth_stage`
        fest auf 50°/35°. Wer einen Abendstand bestellt, bekommt ein sauber belichtetes,
        gut aussehendes, **falsches** Bild, und nichts daran sieht nach einem Fehler aus.
      * `vis.skip` — **der unangenehmste.** Gelesen und nicht beachtet: Wer etwas
        *abbestellt*, bekommt es geliefert.
      * `vis.upscale` — es gibt keinen Hochskalierer; `true` liefert dasselbe wie `false`.
      * `style.mode` / `style.refs` — die Stil-QA läuft nicht (kein eigenes Referenzset).
        Bei `refs` kommt dazu, dass der Betreiber eigene Dateien mitschickt, also Arbeit
        hineinsteckt, die verfällt.

      **Gebaut wurde der Wächter, nicht die Behebung.** `kosmo_szene.DURCHGEREICHT` und
      `STEHENGEBLIEBEN` führen **jedes** gelesene Feld in genau einer der beiden Listen;
      ein Test verhindert die dritte Möglichkeit — «steht nirgends» —, und die ist die
      bequemste. Jeder stehengebliebene Eintrag trägt **was fehlt**, nicht bloss *dass*
      etwas fehlt; mein erster Versuch schrieb dort «siehe oben», und der eigene Test hat
      ihn zurückgewiesen.

      Gemeldet wird nur, was auch wirklich gesetzt war — sonst wäre es die nächste
      Dauerwarnung, und die Lehre dazu ist von heute Vormittag.

      **Behoben ist nichts davon, und das ist Absicht.** Alle fünf verlangen eine
      Festlegung im *fremden* Vertrag: Wogegen wird `azimuth` gemessen? Was soll `skip`
      zurückgeben? Misst unsere QA vor oder nach dem Hochskalieren? Wie gelangen fremde
      Referenzbilder zu uns, ohne durch ein öffentliches Repo zu reisen? Das steht als
      `auf-37` beim **Cloud-Worker** — ein Vertragsauftrag an die HomeStation liefe ins
      Leere.
- [x] **Sieben von sieben Stilen führen einen negativen Prompt, und keiner erreicht je ein
      Bild — gemeldet, nicht angeschlossen** (23.08.2026). Zwei Wirkungslosigkeiten
      übereinander, und beide sehen wie Sorgfalt aus:

      1. **Kein Weg.** Gesetzt wird er von `prompts.komponiere`, und `komponiere` liegt
         nicht auf dem Weg, den ein Auftrag der Oberfläche nimmt. Dieselbe Fehlerart wie
         beim Bauteilwächter, nur an einem anderen Feld.
      2. **Auch mit Weg keine Wirkung.** `z-image-turbo` läuft mit `fuehrung = 0.0`;
         unterhalb von 1.0 ist die klassifikatorfreie Führung abgeschaltet, und dann gibt
         es nichts, wovon sich ein negativer Prompt abziehen liesse.

      **Der Hinweis dazu stand seit Monaten im Code** (`render.py`) — und ist nie jemandem
      begegnet, weil er nur feuert, *wenn* ein negativer Prompt gesetzt ist. Er war nie
      gesetzt. Eine Warnung, die von der Bedingung abhängt, die sie melden soll, ist keine.

      **Nicht angeschlossen, und das ist Absicht.** Ihn durchzureichen ergäbe den
      schlechtesten Zustand von allen: Er stünde im Protokoll, sähe nach Wirkung aus und
      änderte kein Bildpunkt. Gebaut ist stattdessen `render.negativ_wirksam` (drei
      Zustände — wirkt, wirkt nicht, **unbekannt**, weil bei unbestimmter Führung die
      Vorgabe von `diffusers` greift) und `abholer.negativ_lage`, das beide Gründe in
      **einer** Zeile des Kurzbefunds nennt. Wer nur den ersten liest, baut den Weg und
      wundert sich, dass sich nichts ändert.

      **Ob er sich überhaupt lohnt, ist ungemessen** — und das ist die eigentliche Frage.
      `auf-38` misst es auf einem Backbone mit Führung: A ohne / B mit negativem Prompt,
      dazu **C** (gleiche Führung ohne Prompt, damit wir nicht die Führung für den Prompt
      halten) und **D** (Prompt bei Führung 1.0, Gegenprobe zur Wirkungsgrenze), je drei
      Startwerte — weil die Seed-Streuung von 0,2269 grösser ist als jeder gemessene
      Parametereffekt.

      **Ein Ergebnis ist ausdrücklich mitgedacht:** Zeigt A gegen B nichts, gehören die
      sieben Negativ-Prompts **gelöscht** statt angeschlossen. Dann wären sie sieben
      Stellen, an denen etwas Wirkungsloses gepflegt wird.
- [ ] **`RAUSCHBODEN_UEBER_MASKE` ist keine Konstante — der Schätzer hat ein Ortsfeld.**
      Der schwerwiegendste Befund dieser Tage, und er sass **unter** dem Tor
      (`auf-vis-20260824-10`).

      Was `depth-anything-v2-small` auf einem leeren Bild ausgibt, ist zu **95,75 %** eine
      Funktion des **Ortes** — zirkelfrei gemessen (Feld aus 15 Rauschbildern, geprüft an
      15 anderen). Gestalt: Schüssel mit starkem Unterrand-Bonus. Dieselbe Rauschkarte,
      dieselbe Maske, nur verschoben:

          96 px hoch  ρ −0,6249 · Mitte ρ +0,5207 · 96 px runter ρ +0,6387 · rechts ρ +0,6513

      **Ausschlag 1,28 mit Vorzeichenwechsel.** Zwei Kontrollen schliessen das Mass als
      Ursache aus: Karte *und* Maske gemeinsam verschoben ändert nichts, und das mittlere
      Feld allein sagt den Boden an allen 13 Lagen vorher (Korrelation 0,9993).

      **Es trifft auch ihre eigene ρ-Eichung** — sie sagt es über ihre eigene Arbeit: In
      allen drei Szenen lag die Maske an derselben Stelle. Die schöne Übereinstimmung von
      0,4 % zeigt nicht, dass ρ szenenfest ist, sondern dass ρ **bei gleicher Maskenlage**
      szenenfest ist. Über verschiedene Lagen schwankt der Abstand der Schwelle 0,80 zum
      Boden zwischen **0,15 und 1,42**.

      **Und das Feld hängt an der BILDGRÖSSE, nicht am Seitenverhältnis** (`25c0800`): Zwei
      Felder derselben Grössenklasse stimmen zu 0,97 überein, auch bei 1,61:1 gegen
      quadratisch; 512 gegen 992 nur zu 0,85. Ein bei 512 bestimmtes Feld erklärt an
      Produktionsgrösse nur ~72 % — wer es dort abzieht, zieht **oben** am stärksten das
      Falsche ab, also genau dort, wo bei einer Aussenaufnahme der Himmel steht. Damit
      scheidet «Feld einmal bestimmen und herausrechnen» aus.

      **Umgesetzt ist ihre Empfehlung (a).** Der Boden wird je Lauf an der tatsächlichen
      Maskenlage *und* Bildgrösse gemessen — `_nullprobe` tat das ohnehin schon, **nur
      gelesen hat ihn nie jemand.** Das war die fünfte tote Kante dieser Woche und die
      teuerste, weil sie unter dem Tor sass. Neu:
      `geometrie_qa.rho_gegen_gemessenen_boden` vergleicht ρ gegen den **höchsten**
      Nullanker dieses Laufs, und `befund_kurz` meldet die Kameras, an deren Maskenlage
      **die Schwelle nichts mehr trennt** — ein Befund über die Kameralage, nicht über das
      Bild. Die Abhilfe steht in derselben Zeile: eine andere Lage, **keine** andere
      Schwelle.

      Offen bleibt, ob die Konstante überhaupt noch irgendwo als Vergleich dient; sie steht
      jetzt nur noch als Bezugspunkt für ältere Messungen, mit ihrer Widerlegung daneben.
- [ ] **Und daraus folgt etwas über zwei meiner eigenen Entscheidungen: Der Shift
      verschiebt die Maske genau dort, wo das Ortsfeld am stärksten wirkt.**
      Nachgerechnet für `MODUS_SHIFT` — die Vorgabe seit dem 23.08. — bei 1600 × 992:

          Flachbau  8 m auf 40 m   Shift  2,0 mm →  89 px senkrecht
          Wohnhaus 15 m auf 35 m   Shift  5,8 mm → 258 px
          Wohnhaus 15 m auf 25 m   Shift  8,1 mm → 361 px
          Grenze `MAX_SHIFT_MM` 12 mm          → 533 px

      Das Ortsfeld ist in Schritten von **96 px** vermessen worden, und dort drehte der
      Rauschboden um 1,28 **mit Vorzeichenwechsel**. Unsere Kameras liegen also ein bis
      fünf Schritte auseinander — **zwei Kameras desselben Auftrags vergleichen Zahlen auf
      verschiedenen Skalen.**

      Das ist kein Argument gegen den Shift: Senkrechte, die stürzen, sind ein echter
      Mangel, und die Alternative wäre nicht besser, sondern nur anders falsch. Es ist ein
      Argument dafür, dass der **je Lauf gemessene** Boden keine Feinheit ist, sondern die
      Voraussetzung dafür, dass die drei Ansichten überhaupt vergleichbar sind.

      **Gebaut ist die zweite Rechnung daneben, nicht die neue Regel.** `_bodenspanne`
      trifft dieselbe Auswahl noch einmal, aber nach ρ **minus dem gemessenen Boden dieser
      Kamera**. Stimmen beide überein, hat die Sache keine Folgen; weichen sie ab, meldet
      der Kurzbefund **KAMERAWAHL UNEINIG** und sagt dazu, dass weiterhin die rohe Zahl
      gilt — «schlechteste bleibt» ist ein Owner-Entscheid vom 22.08. und wird nicht
      nebenbei umgeschrieben. Ein Test prüft, dass die Nebenrechnung die Urteile nicht
      anfasst; eine stille Regeländerung ist in diesem Projekt schon einmal vorgekommen.

      **Offen und zu entscheiden:** Welche der beiden Zahlen das Urteil tragen soll. Erst
      messen, wie oft sie überhaupt auseinandergehen — das kostet keinen eigenen Lauf, es
      steht ab jetzt in jedem Befund.
- [x] **`auf-34` beantwortet: Der Rückfall auf Objektnamen ist der bessere Weg — und zwei
      Folgen davon sind gebaut** (`BEFUND_2026-08-24_IFC-LESER.md`, neun echte IFC, beide
      Leser, 9 von 9 ok).

      **Die Annahme des Plans fällt.** Wir hatten vermutet, der Maskenbildung fehlten die
      Materialien und sie müsse *notgedrungen* auf Objektnamen zurückfallen. Gemessen ist
      es umgekehrt: Der Knotenname `{IFC-Klasse}_{GUID}` überlebt das glb (im **Graphen**,
      nicht in den Geometrie-Schlüsseln) und kommt vollständig in Blender an — an 2 250
      Bauteilen geprüft. Ein Materialname wie `Stahlbeton_C25` steht dagegen an Wänden
      *und* Böden zugleich und trennt sie nicht; an 999 Bauteilen einer Datei fehlt er ganz.
      **`IfcWall` kann, was `Stahlbeton_C25` nicht kann.**

      **Damit fällt auch die Erwartung, das Zusammenführen der beiden Leser sei der
      schnellste Gewinn.** Geschoss, Materialschichten und `LoadBearing` haben in der
      Bildkette heute **keinen Abnehmer** — Geschoss bräuchte die Innenaufnahme, die es
      nicht gibt. Ein Zusammenbau transportierte Daten, die am anderen Ende niemand liest.

      **Zwei Folgen sind gebaut, beide an der Naht:**

      * **`gelaende_erwartet` reicht jetzt durch** (`verarbeiter` → `_maske_bauen` →
        `bauwerksmaske`, dazu `--kein-gelaende`). Ein reines Gebäude-IFC bringt gar kein
        Gelände mit: Der eine `IfcSite` darin trägt keine Geometrie. Die Maske meldete
        dann «kein Gelände erkannt» — ein **Fehlalarm**, es fehlt nichts. Der Schalter
        existierte seit jeher in `maske.py` und war von aussen nicht erreichbar; **das ist
        dieselbe Naht-Sache wie Brennweite und Geländestand, zum dritten Mal.** Die Vorgabe
        bleibt die strenge Lesart — ein Schalter, der voreingestellt wegschaut, wäre
        schlimmer als keiner.
      * **Die Ein-Eintrag-Tabelle wird gemeldet.** `Bestand_Kontext.ifc` (56 MB) kommt als
        **ein** namenloses Bauteil mit 502 002 Dreiecken an, bei beiden Lesern gleich. Die
        Warnung ist bewusst genauer als «unbrauchbar»: Vom **Himmel** trennt so eine Maske
        weiterhin richtig; was nicht geht, ist der Entwurf gegen seine **Nachbarschaft**.
        Wer im Kontext rendert, misst sonst den ganzen Klumpen und hält das für eine
        Aussage über sein Bauwerk. Die Maske wird darum **nicht** verworfen — das wäre
        Überbehauptung in die andere Richtung.

      **Und ein Befund über den fremden Leser, den unserer richtig macht:** Ein
      `IfcTransportElement` — ein Aufzug — landet dort in «Unbekannt» und geht verloren,
      wer stromabwärts filtert. Unser `ist_gebaute_substanz` behält ihn; das steht jetzt
      als Test.

      **Die echte Lücke bleibt und ist gemeinsam:** Belegt ist nur, dass die Konversion
      **durchläuft** — nicht, ob die Geometrie **stimmt**. Dazu kommt: **IFC2X3 aus
      ArchiCAD** — genau die auffällige Gruppe vom 18.08. — ist auf der Maschine nicht mehr
      vorhanden und bleibt ungemessen.
- [x] **Und dafür gibt es jetzt ein Mass: `konversionstreue.pruefe_konversion`.**
      Es liest den Bericht des Runners (`bbox`, `n_elements`, `n_triangles`) und vergleicht
      ihn mit der **bekannten** Wahrheit. Kein `ifcopenshell`, kein Runner-Import — es liest
      ein Wörterbuch (Regel 2, und ein Test prüft die Importliste, nachdem mir genau dieser
      Fehler am selben Tag schon einmal unterlaufen ist).

      **Der Ertrag ist nicht «stimmt / stimmt nicht», sondern die Diagnose.** Die zwei
      häufigsten IFC-Fehler sehen in einer reinen Zahlenabweichung gleich aus und sind es
      nicht:

      * **MASSSTAB** — alle drei Achsen um denselben Faktor daneben. 1000 heisst
        *«Millimeter als Meter gelesen, `IfcUnitAssignment` übergangen»*; 100, 10 und
        0,3048 (Fuss) sind ebenfalls benannt. **Ein Faktor, der zu keinem passt, wird
        nicht geraten** — eine erfundene Diagnose ist schlimmer als keine.
      * **ACHSEN VERTAUSCHT** — dieselben drei Kantenlängen in anderer Reihenfolge. Das
        Bauwerk ist dann nicht falsch *gross*, sondern falsch *gedreht*; wer das als «zwei
        Achsen daneben» liest, sucht am falschen Ort.

      **Warum synthetisch und nicht an ihren neun Dateien** — und das ist keine Bequemlichkeit:
      Bei einer echten IFC kennt niemand die Wahrheit; man müsste sie mit demselben Werkzeug
      ausrechnen, das man prüfen will. Bei `make_test_ifc.py` kennen wir jede Kante, weil wir
      sie geschrieben haben. **Regel 3 ist hier nicht bloss eingehalten, sie ist die
      Voraussetzung.**

      Was das Mass wert ist, steht mit im Modul: Läuft es am Testfall schief, läuft es
      überall schief. Läuft es richtig, ist über echte Dateien **nichts** bewiesen — nur
      etwas ausgeschlossen.

      **`auf-39` lässt es am Gerät laufen**, mit G3 (die gefälschten Berichte) **zuerst**:
      Wenn die drei Fälschungen nicht anschlagen, ist die Prüfung kaputt und alles Übrige
      wertlos. G2 ist der Millimeter-Fall — ohne ihn wäre G1 eine Vakuumprobe.

      **Offen und mitgefragt:** Reicht die Hüllbox? Eine Geometrie mit richtiger Hüllbox
      könnte innen völlig falsch sein — vertauschte Wände, fehlende Decke. Die Dreieckszahl
      fängt einen Teil davon; ob das genügt, ist ungemessen.
- [ ] **`null` im QA-Schema hält zwei fertige Bilder auf — und trifft genau das, was wir
      heute gebaut haben.** Der Befund ist ihrer, nicht unserer (`auf-orbit-20260823-04`):
      Die Oberfläche verwirft unser Ergebnis, weil `qa.geometry.geometry_fidelity` und
      `spearman` **null** sind und ihr Schema kein null annimmt. Zwei fertige Bilder liegen
      auf der Platte, ohne dass ein Nutzer sie sieht.

      **Eine Zahl zu erfinden kommt nicht in Frage.** `0.0` heisst *gemessen,
      katastrophal*; `null` heisst *nicht gemessen*. Die Verwechslung dieser beiden ist der
      Fehler, gegen den diese ganze QA gebaut ist — am 21.08. erreichte ein Bild **ohne
      Bauwerk** 0,9848 gegen 0,9703 für das perfekte.

      **Und es sind seit heute drei Zustände, nicht zwei:** gemessen · nicht gemessen ·
      **nicht zuständig**. Der dritte ist die Zuständigkeitsgrenze von heute Mittag, und er
      muss bei ihnen ankommen können, sonst ist er auf halbem Weg verloren — dieselbe tote
      Kante wie dreimal heute, nur über die Vertragsgrenze hinweg.

      In `auf-37` steht das jetzt als **F1** und mit drei Vorschlägen in dieser Reihenfolge:
      ein `status`-Feld je Messung (löst alle drei Zustände), `null` zulassen (löst den
      Stau, unterscheidet 2 von 3 nicht), oder — falls beides teuer ist — uns sagen, ob ihr
      Schema ein **fehlendes** Feld akzeptiert. Das dritte könnten wir sofort umsetzen; es
      ist unsere Seite und braucht nur die Auskunft.
- [ ] **LIZENZMELDUNG (Regel 1): Der naheliegende nächste Versuch ist gesperrt.** Die
      HomeStation hat gefragt, ob ein *grösserer* Tiefenschätzer die 15 m auflöst — dann
      wäre der ganze Befund eine Frage der Modellgrösse. **Das ist mit erlaubten Gewichten
      nicht zu beantworten:** `depth-anything-v2` in **base, large und giant** steht unter
      **CC-BY-NC-4.0**, also NonCommercial, und ist damit nach Regel 1 ausgeschlossen —
      dieselbe Sperre wie bei FLUX.1-dev. Zulässig ist allein `depth-anything-v2-small`
      (Apache-2.0). Die Registry führt das seit Phase 3 korrekt (`zulaessig: False`); neu
      ist, dass die Sperre jetzt eine **inhaltliche** Frage blockiert und nicht nur eine
      Bequemlichkeit.

      `auf-36` ist darum neu geschrieben und beantwortet dieselbe Frage ohne fremdes
      Gewicht: **denselben Fall mit wachsendem Abstand** (15 / 30 / 60 / 120 m). Trennt der
      kleine Schätzer bei 120 m, ist es eine Auflösungsgrenze in Metern und aufschreibbar.
      Trennt er nie, fehlt der **Bildhinweis** — dann hätte auch ein grösseres Modell
      nichts genützt, und die Sperre kostet uns nichts. Dazu die Stufung des
      Himmelanteils (5/10/20/30/45 %), die aus `MIN_HIMMELANTEIL` eine Messung macht statt
      einer Setzung.

      **Nachtrag am selben Abend: Die HomeStation ist unabhängig auf dieselbe Sperre
      gekommen — und hat die Frage danach besser gestellt** (`auf-vis-20260823-08`).
      Nachgerechnet an derselben Szene: Bauwerk 1,7124, Nachbar 1,6112. **Der Schätzer
      ordnet richtig**; er staucht nur den Betrag auf 3 % der Kartenspanne. Ein
      monokularer Schätzer liefert *relative* Tiefe, die absolute Skala ist willkürlich —
      und unser zweites Bein benutzt den Betrag. Es ist also gar keine Frage der
      Modellgrösse gewesen, sondern eine der Masskonstruktion. Die Abstandsreihe, die ich
      dafür angesetzt hatte, ist damit hinfällig und aus `auf-36` wieder entfernt.
- [x] **R2 ist gebaut, angeschlossen — und am 24.08.2026 wieder herausgenommen worden.**
      Owner-Freigabe zur Entscheidung am 23.08. («entscheide du»); zurückgenommen auf
      ausdrückliche Bitte der HomeStation und mit ihrem Beleg.** Je Grenzabschnitt Median innen
      gegen Median aussen im selben Fenster; gezählt wird der **Anteil der Abschnitte**,
      an denen das Bauwerk lokal näher liegt. Kein Betrag, keine Normierung.

          g0 flach 68,1 % · g1 geneigt 70,3 % · g2 Nachbar 67,0 % · s60 75,5 % · s29 82,5 %
          Anker: Rauschen 33,7 / 16,1 % · grau 0,0–0,4 % · Verlauf 0,2–0,4 %

      **In g2 trägt es, wo A und F ganz ausfallen.** Fünf Szenen, drei Gebäude, jeder
      echte Fall 52,6–82,5 %, jeder Anker höchstens 33,7 %.

      **Die HomeStation empfiehlt es mit Vorbehalt und benennt den Vorbehalt selbst:**
      Als *Anwesenheitsprüfung* taugt R2, als **Gütemass nicht** — die Versatzreihe fällt
      nicht monoton (auf s60 springt sie bei 0,5 m wieder hoch), und der Szenenabstand
      liegt bei 8,5 Punkten, wo ρ 0,4 % hat. Der Rauschwert hängt an der Szene (33,7
      gegen 16,1 %), die Schwelle 45 % braucht darum Luft.

      **Mein Entscheid, und die Begründung in zwei Teilen.**

      *Warum gebaut:* Es trägt dort, wo die beiden anderen ausfallen, und das ist in der
      Stadt der Normalfall. Es liegt jetzt als `geometrie_qa.anteil_naeher_am_rand` in der
      Bibliothek — **an einer** Stelle, nicht an zweien. Die HomeStation misst ab jetzt
      mit unserer Fassung; weichen ihre Zahlen davon ab, ist genau das der Befund.

      *Warum nicht als Ersatz:* Sie sagt selbst, R2 sei kein Gütemass. Ein Gütemass durch
      ein Anwesenheitsmass zu ersetzen hiesse, eine Frage **aufzugeben** statt eine zu
      beantworten. Damit ist auch ihre Rückfrage beantwortet: Es ist nicht mein Unwille,
      etwas wegzuwerfen — es sind zwei Fragen.

      *Warum es nichts entscheidet:* **streng additiv.** Kein Bild besteht durch R2, das
      ohne R2 durchgefallen wäre; es fügt Auskunft hinzu und nimmt keine weg.

      **24.08.2026 — wieder heraus, und mein Argument war zu kurz.** Die HomeStation hat
      R2 zum ersten Mal an **erzeugten** Bildern gemessen (`auf-vis-20260824-09`, zehn
      Bilder, unsere Fassung): **Sieben von zehn liegen über dem perfekten Blender-Bild
      derselben Szene**, sechs davon mit `|rho| < 0.32`. Das einzige Bild *unter* dem Band
      hat das zweitbeste ρ.

      Der Mechanismus lässt keine Rettung zu: Eine **in Y verschobene** Maske bekommt
      denselben Wert — 0,8405 gegen 0,8405, identisch; in X sehr wohl. **R2 beantwortet am
      Produktpfad nicht «steht da ein Bauwerk», sondern «liegt die Maske im unteren
      Bilddrittel».** Ihre Bitte: *nicht anzeigen, auch nicht als Beifahrer. Eine Zahl, die
      bei schlechteren Bildern höher ausfällt, ist schlimmer als keine.*

      **«Streng additiv» genügt nicht, und das ist mein Fehler.** Kein Bild bestand durch
      R2 — richtig. Übersehen habe ich, dass eine **angezeigte** Zahl den Menschen in die
      Irre führt, der das Urteil liest, und der gehört zum Tor. Die Funktion bleibt mit
      dem Befund im Docstring; ein Test hält fest, dass sie nicht mehr am Maskenweg hängt.

      **Ihre Schwelle hat sie selbst zurückgezogen** — mit einem Grund, der schwerer wiegt
      als der Anker: Eine Schwelle **unter** dem Zufallsniveau ist grundsätzlich unhaltbar,
      und über 0,50 bliebe zwischen 52,6 und 82,5 % ein Fenster von zwei Punkten. Beide
      Rauschanker waren übrigens richtig und massen Verschiedenes: Rauschen *als* Karte
      Median 0,4942 (mein Objekt, 160/200 über 0,45), *Schätzer auf* Rauschbildern Median
      0,1440 (ihr Objekt, 0/30). Die Frage, die ich von hier aus nicht trennen konnte, hat
      sie am Gerät getrennt.
- [ ] **DAS MUSTER hinter drei gefallenen Vorschlägen — und es ist eine Regel, keine
      Anekdote.** `kantenanteil`, Variante F und R2 sind alle drei gefallen, **alle drei
      an Blender-Renders geeicht und alle drei am Produktpfad gescheitert.** Die
      HomeStation hat es selbst benannt: *«Eine Eichung, die nur perfekte Renders und
      Nullanker kennt, sagt über erzeugte Bilder nichts.»*

      Daraus folgt für jedes künftige Mass dieses Projekts: **Ein Vorschlag wird an
      erzeugten Bildern gemessen, bevor er angeschlossen wird — nicht danach.** Renders
      und Nullanker sind die *Vorprüfung*; sie können ein Mass widerlegen, aber nicht
      tragen. Alle drei Male hat die Vorprüfung grün gezeigt.

      Dass alle drei fielen, **bevor jemand darauf gebaut hat**, ist kein Zufall, sondern
      das Verfahren — und das ist der Teil, der bleiben soll.
- [x] **Die vorgeschlagene R2-Schwelle liegt UNTER dem Zufallsniveau — gefunden beim
      Nachbauen, gemeldet vor der nächsten Messung, am 24.08. bestätigt und
      zurückgezogen.**

      **Das Zufallsniveau von R2 ist 50 % und folgt aus der Konstruktion.** Hat die
      Schätzung gar keinen Bezug zur Maske, sind Median innen und Median aussen zwei
      unabhängige Ziehungen aus derselben Verteilung; welcher grösser ausfällt, ist ein
      Münzwurf. Für eine symmetrische Werteverteilung gilt das exakt.

      **Nachgemessen** (200 Startwerte, synthetische Szene, 79 Abschnitte): Median
      **0,5063**, Spanne **0,228 bis 0,772**. Über der vorgeschlagenen Schwelle 0,45 liegen
      **138 von 200** — weisses Rauschen besteht sie in mehr als zwei Dritteln der Fälle.

      Ihr Rauschanker von 33,7 % ist **eine Ziehung** und liegt bequem in dieser Spanne.
      Das ist derselbe Fehler wie meine Kameraneigung von heute früh: *Eine Spanne aus
      einer Stichprobe ist eine Aussage über die Stichprobe.* Möglich bleibt, dass ihr
      Anker etwas anderes ist als meiner — sie messen vermutlich den *Schätzer auf einem
      Rauschbild*, ich das Rauschen selbst als Karte. Dann wären 33,7 % keine
      Münzwurfzahl, sondern eine Eigenschaft des Schätzers, und das wäre sogar
      interessanter. **In beiden Fällen braucht der Anker mehrere Startwerte.**

      **Und eine zweite Sache fiel beim Messen auf:** Die Fenster benachbarter Abschnitte
      überlappen (Radius 6, jeder dritte Punkt). Die Abschnitte sind also **nicht
      unabhängig**, und die binomiale Streuung ist zu klein — gemessen ist der Faktor 1,93
      bei `jeder_nte=3` und 1,34 bei 7, auf **einer** Szene, also nichts Belastbares. Die
      Funktion meldet `ueber_zufall` darum **nicht** als `True`, sondern gar nicht: Das
      wäre eine Behauptung über einen Abstand, den niemand kennt.

      Das steht als **G2** in `auf-36` und ist dort wichtiger geworden als die sechste
      Szene: Erst danach weiss überhaupt jemand, wo bei R2 der Zufall liegt.

      **Die eigentliche Lücke ist aber eine andere, und sie hat sie selbst benannt: Kein
      einziger R2-Wert stammt von einem erzeugten Bild.** Alle Zahlen kommen aus
      Blender-Renders und den drei Ankern; die Versatzreihe ist der *Ersatz* für
      schlechter werdende Geometrie. Die Schwelle 45 % entscheidet aber über unsere
      erzeugten Bilder. Liegt unser bestes (`auf-30`: Umrisstreue 24,3 %) darunter, ist
      sie unbrauchbar; liegt das ungeführte (6,4 %) darüber, ist sie zahnlos. Das steht
      als G1 in `auf-36` und ist wichtiger als eine sechste Szene.

      **Offene Frage an die HomeStation, nicht an uns:** Wenn R2 kein Gütemass ist —
      gehört es dann *neben* das Kantenmass statt an seine Stelle? R2 beantwortete
      «steht da etwas», das Kantenmass «wie gut», und wo kein Himmel steht, schweigt das
      zweite und das erste trägt allein. Das wäre ein **drittes Bein** und kein Ersatz.
      Ich habe ausdrücklich mitgefragt, ob das sauber ist oder bloss mein Unwille,
      etwas wegzuwerfen.

      **Und was daraus für heute folgt:** Die Zuständigkeitsgrenze aus
      `MIN_HIMMELANTEIL` gehört zum **Betragsmass**, nicht zur Frage. Kommt ein Rangmass
      als zweites Bein, muss sie mitgeprüft und vermutlich abgeschaltet werden — sonst
      brächte sie ein Mass zum Schweigen, das dort antworten kann. Das ist derselbe
      Fehler in der anderen Richtung und steht darum als Warnung im Code.

      Ein zweiter Schätzer bleibt erlaubt, **wenn seine Lizenz vorher genannt ist** und
      permissiv ausfällt. Eine ungeklärte Lizenz ist ein Befund und kein Hindernis.
- [x] **Der Bauteilwächter lief auf keinem einzigen echten Auftrag — bis 23.08.2026.**
      Er ist die direkte Antwort auf den teuersten Fehler dieses Projekts: „clean flat
      roof" für einen oben offenen Quader, und das Bildmodell lieferte ein Dach
      (`auf-20260818-09`). Gerufen wurde er nur von `komponiere` — und `komponiere` liegt
      **nicht** auf dem Weg, den ein Auftrag der Oberfläche nimmt. Der bringt seinen
      Prompt roh mit.

      Dieselbe Fehlerart wie bei `komposition.py` am selben Tag, und hier teurer: Es ist
      der Wächter gegen genau die Sorte Fehler, die das Projekt begründet hat.

      Angeschlossen in `lies_szene`, direkt neben der Sprachprüfung — und er prüft
      **beide** Fassungen. Die Begründung dafür ist keine Gründlichkeit, sondern zwei
      gemessene Fälle: `Flachdach` entgeht dem Wächter (Kompositum, und die Wortgrenzen
      sind Absicht — sonst schlüge „Betonung" bei „Beton" an), wird aber zu `flat roof`
      und **dort** gefunden. Umgekehrt wird `Laibung` zu `reveal`, das der Wächter nicht
      kennt — dort fängt es nur das Original. Es gibt genau zwei solche Wörter
      (`laibung`, `dächer`), und einer davon steht jetzt als Test.
- [ ] **Was `verarbeiter` NICHT durchreicht — systematisch nachgesehen.** Nach zweimal
      derselben Lücke an einem Tag (Brennweite, Geländestand) einmal alle Parameter
      verglichen. `glb_zu_multipass` kennt 17, elf werden gereicht; nicht gereicht sind
      `beauty`, `material_id`, `shift_y`, `timeout`, `herzschlag_takt_s`,
      `kamera_huellbox`. `RenderAuftrag` kennt zwölf Felder, fünf werden nicht gesetzt:
      `negativ_prompt`, `schritte`, `denoise`, `fuehrung`, `modell_wurzel`.

      **Nicht alle davon gehören durchgereicht** — `material_id=False` schaltete
      stillschweigend die Bauwerksmaske ab, an der die ganze QA hängt. Aber der
      Unterschied zwischen *bewusst nicht* und *vergessen* steht nirgends, und genau
      darin lagen die beiden gefundenen Lücken. Zu entscheiden je Parameter, und danach
      als Prüfung festzuhalten, damit der nächste hinzukommende nicht still in dasselbe
      Loch fällt.
- [ ] **Die Negativ-Prompts der Stile erreichen keinen Render.** `prompts.Stil.negativ`
      ist geschrieben und wird auf dem Produktivweg nie gelesen: `RenderAuftrag.negativ_prompt`
      setzt niemand, und der fremde Vertrag führt gar kein Feld dafür. Das ist eine
      Vertragsfrage und keine Programmfrage — aber es gehört benannt, statt als
      scheinbar wirksame Einstellung dazustehen.
- [ ] **Ob sich die beiden Auswahleffekte wirklich aufheben, ist NICHT gemessen.**
      Je Kamera wird das beste von drei genommen (hebt), über die Kameras das
      schlechteste von drei (senkt). Beide betragen rund 0,845 Streuungen — sie heben
      sich also auf, **sofern** die Streuung über Startwerte und die über Blickrichtungen
      ähnlich gross sind. 0,2269 stammt von Startwerten. Dass es sich ausgleicht, ist
      eine plausible Erwartung und kein Befund; die Kameraspanne im Befund sammelt jetzt
      die Zahlen, mit denen es entscheidbar wird.
- [ ] **Die Streuung ZWISCHEN Kameras ist ungemessen — und jetzt erstmals messbar.**
      0,2269 ist über Startwerte gemessen, nicht über Blickrichtungen. Verschiedene
      Richtungen zeigen verschieden viel Geometrie; die Streuung könnte grösser oder
      kleiner sein. Seit drei Kameras je Auftrag gefahren werden, fällt sie als Nebenprodukt
      an — `kameraspanne.streuung` sammelt sie ab drei gemessenen Kameras.
- [x] **`MODUS_SHIFT` ist die Vorgabe (23.08.2026) — die Bedingung des Owners ist
      erfüllt.** `auf-33` kam mit allen fünf Fällen wie erwartet zurück:

      * **Die Senkrechten werden senkrecht.** Gekippt weichen die senkrechten
        Gebäudekanten um **0,47°–0,98°** ab, geshiftet um **0,004°–0,016°** — der
        Rauschboden der Messung.
      * **Der Umbau war additiv, bis auf das letzte Bit.** Der Stand vor dem Umbau, der
        danach und HEAD mit `--brennweite=28` liefern bildpunktgleiche Ausgaben. Was sich
        änderte, war die Brennweite, nicht der Umbau. Jede vor heute gemessene Aufnahme
        bleibt mit `modus=MODUS_GEKIPPT` reproduzierbar.
      * **Die Rahmung bleibt** (0,02 %, 2,45 %, 5,05 % relativ) — und der Shift rahmt in
        allen drei Fällen *grosszügiger*, nicht enger.
      * **Blender bildet mit genau der Kamera ab, die wir meinen:** Eine unabhängige
        Lochkamera-Rechnung trifft die gekippten Kantenwinkel auf 0,004°.
      * **`shift_y = shift_mm / 36` ist richtig — aber nur, weil der Runner `sensor_fit`
        ausdrücklich stellt.** Im Hochformat: 36,595 gemessene Bildpunkte gegen 36,616
        vorhergesagte; die Alternative „Anteil der grösseren Bildkante" hätte 54,924
        verlangt und ist widerlegt. Mit Blenders Vorgabe `AUTO` wäre die Sensorbreite im
        Hochformat 24 statt 36 mm und der waagrechte Bildwinkel 37,8° statt 54,4°. Die
        Vorsichtsmassnahme war tragend, nicht überflüssig.

      **Folge im Betrieb:** Der Neigungs-Warner der Kompositionsprüfung verstummt
      vollständig. Übrig bleibt die eine Zeile, die eine echte Eigenschaft der Eingabe
      ist — der unbekannte Geländestand.

## (überholt) Kamerasetzung — was die Recherche vom 21.08. treffen muss

*Beim Lesen von `kameras.py` vor der Recherche aufgefallen. Der Befund steht hier, damit
die Recherche gegen einen bekannten Stand geprüft wird und nicht gegen ein Bauchgefühl.*

- [ ] **Es gibt gar keinen Innenraum-Modus. Nicht schwach, sondern gar nicht.**
      `kameras.py` rechnet ausschliesslich Aussenstandpunkte um eine Hüllbox herum. Die
      Konstanten machen Innenaufnahmen **rechnerisch unmöglich**: `WANDABSTAND_M = 10.0`
      (Mindestabstand zur Fassade) und `MIN_ZIEH_ABSTAND_M = 6.0` — in einem 4 m breiten
      Zimmer gibt es keinen zulässigen Standpunkt. Wer heute „Innenbild" sagt, bekommt
      eine Kamera zehn Meter ausserhalb der Wand.

      Zu bauen ist damit nicht eine Anpassung, sondern ein **zweiter Weg**: Raum finden
      (aus dem IFC, nicht aus der Hüllbox), Standpunkt im Raum, Verdeckung gegen Wände.
      Der Verdeckungstest steht ohnehin offen — für innen ist er nicht Kür, sondern
      Voraussetzung.
- [ ] **Das Seitenverhältnis ist kein Kompositionsentscheid, sondern ein Durchreicher.**
      Es kommt aus `render.resolution` des fremden Vertrags (Vorgabe 1600×1000 = 1.6:1)
      und geht unverändert in die Bildwinkelrechnung. **Keine Regel im Code verbindet die
      Proportion des Baukörpers mit der Proportion des Bildes.** Für einen 40 m breiten,
      15 m hohen Bau (8:3) heisst 1.6:1 zwangsläufig viel Vordergrund und Himmel — was
      der Owner am 21.08. so entschieden hat, aber eben nicht, weil es gerechnet wurde.
- [ ] **Die Aussen-Konstanten sind begründet, aber nicht belegt.** `BRENNWEITE_MM = 28`,
      `AUGENHOEHE_M = 1.70`, `DECKUNGSGRAD = 0.55`, `BIAS_GRAD = 35`,
      `ZIEL_ANTEIL_HOEHE = 0.20`. Jede trägt im Modul eine Begründung, und die meisten
      stammen aus dem Bestand (KosmoVis) statt aus der Fachliteratur. Die Recherche soll
      sie **prüfen, nicht bestätigen** — wo sie widerlegt werden, ist das ein Ergebnis.
- [ ] **`AUTO_RICHTUNGEN = ("sSE",)` ist eine einzige Richtung.** Eine, nicht zwölf, und
      das war eine Betriebsentscheidung (zwölf Standpunkte sind zwölf Renderläufe). Ob
      ausgerechnet Süd-Südost der richtige einzelne Blick ist, hängt an Sonnenstand und
      Fassadenlage und ist nie begründet worden.

- [x] **Der Maskenweg läuft jetzt im Betrieb (22.08.).** Vier Teile lagen fertig da, ohne
      dass ein einziger echter Lauf sie berührte — genau die tote Kante, wegen der es
      `tools/abholen.py` gibt. Jetzt: Der Abholer baut je Kamera die Bauwerksmaske aus dem
      Material-ID-Pass, `qa_gegen_soll` nimmt sie entgegen und liefert `rho_maske`,
      `kante` und `paarurteil` mit.

      **Zwei Entscheidungen, die man übersehen kann.** (1) Die Maske geht *hinein*, die
      Schätzkarte kommt nicht heraus — sie ist gross und wird danach nicht mehr gebraucht.
      (2) Beide Masse bekommen die **rohe** Schätzkarte, nicht die hintergrundmarkierte:
      Die Kante liest ausdrücklich auch *ausserhalb* der Maske, und dort verdürbe die
      Hintergrundmarke den Median.

      **Zwei eigene Fehler dabei, beide von der Mutationsprobe gefunden.** Erst hätte ich
      die Schätzkarte als Soll *und* als Ist übergeben — ρ wäre trivial 1.0 geworden und
      hätte wie ein glänzendes Ergebnis ausgesehen. Und mein Verdrahtungstest prüfte nur,
      dass das *Schlüsselwort* ankommt: `maske=None` bestand ihn. Beides behoben, der Test
      fängt jetzt auch `maske=None` und `maske=[]`.
- [x] **Die Nullprobe fährt den Maskenweg — geschlossen am 22.08., am selben Tag benannt.**
      Sie liefert jetzt **zwei Ankersätze aus einem Durchgang**: den Score über das ganze
      Bild und ρ/Kante über der Maske. Die Kontrollbilder werden dabei nur **einmal**
      geschrieben und einmal geschätzt — der erste Anlauf machte daraus zwei Durchgänge
      und hätte die Schätzerläufe verdoppelt, ohne eine einzige neue Zahl zu liefern.

      **Warum je Soll-Karte gemessen und nicht nachgeschlagen:**
      `RAUSCHBODEN_UEBER_MASKE` (−0.5207) stammt aus **einer** Szene, und die Schwelle des
      Paartests bezieht sich darauf. Eine feste Zahl für alle Szenen ist genau der Fehler,
      an dem die Geometrie-Schwelle 0.65 gescheitert ist.

      Der Test, der die Lücke offenhielt, ist **gelöscht** und nicht angepasst worden —
      so, wie es in seinem eigenen Docstring stand.
- [x] **Der Wächter für den teuersten Fehler des Projekts lief nicht — behoben 22.08.**
      `auf-20260822-28` hat gemessen: Nicht der Backbone war die Ursache für monatelang
      schlechte Bilder, sondern die **geklippte Tiefenkarte**. Ohne jede Führung −0.2558,
      mit der geklippten Karte und voller Führung −0.2540 — **Abstand 0.002.** Die
      Schablone war exakt so viel wert wie gar keine Konditionierung.

      Am selben Tag verschwanden `numpy` und `Pillow` aus dieser Umgebung, und die vier
      Tests, die genau diese Skalierung bewachen, setzten aus. Erst als Fehlschlag
      (`ModuleNotFoundError` sieht aus wie ein kaputtes Modul), dann als ehrliches
      Überspringen — und beides heisst: **der Wächter lief nicht.**

      Behoben: beide in `dev` deklariert, beide permissiv und bereits binärgeprüft.
      **Und nachgeprüft, dass der Wächter taugt:** Stellt man den alten Fehler wieder her
      (`bild.convert("RGB")` statt der Skalierung), fällt der Test. Ein Wächter, der nur
      läuft, wenn zufällig das richtige Paket da ist, bewacht nichts.
- [ ] **ERSTER BEOBACHTETER FEHLALARM des Stillstandswächters (22.08.).** Der echte
      Blender-Lauf in `test_kette.py` brach ab mit *„seit 10 s kein Fortschritt"* — und
      war kerngesund: Drei Wiederholungen danach liefen in 3,7 bis 8,2 s durch. Der
      Unterschied war die **Last**: Während des Fehlschlags lief im Hintergrund eine volle
      Suite.

      Die Zahlen: Blender startet auf dieser Maschine in 1,3 s (kalt) bzw. 0,4 s (warm),
      der ganze Lauf braucht im Leerlauf rund 4 s. Die Frist ist
      `HERZSCHLAG_TAKT_S × HERZSCHLAG_AUSFAELLE = 2,0 × 5 = 10 s` — also nur etwa das
      Zweieinhalbfache eines gesunden Laufs. **Das ist knapp**, und unter Last reicht es
      nicht: Der Herzschlag ist ein gewöhnlicher Python-Faden und wird bei Gedränge
      einfach nicht mehr eingeplant.

      **NICHT geändert.** Eine Sicherheitsschwelle nach einer einzigen Beobachtung in
      einem künstlich ausgelasteten Behälter zu lockern, wäre genau das Ablesen statt
      Kalibrieren, gegen das dieses Projekt seit Tagen antritt. Aber es gehört gemessen —
      auf der HomeStation, wo echte Aufträge laufen und die Maschine ohnehin belastet ist.
      **Ein Fehlalarm bricht einen gesunden Auftrag ab**, und das ist teurer als ein
      Stillstand, der ein paar Sekunden später auffällt.
- [ ] **Was die Kante kostet, gemessen: 0,94 s bei 1600×1000.** `_randpunkte` läuft in
      reinem Python über jeden Bildpunkt. Je Kamera fällt das viermal an (ein echtes Bild
      und drei Kontrollbilder), also rund vier Sekunden — gegen ~97 s Renderzeit je Kamera
      (erster vollständiger Lauf, 19.08.) vertretbar, aber nicht umsonst. **Nicht
      optimiert, weil nicht nötig; hier steht die Zahl, damit sie niemand raten muss.**
      Falls die Auflösung steigt, wächst das linear mit der Punktzahl.
- [ ] **Zwei Polaritäts-Schreibweisen im selben Projekt.** `tiefenschaetzer` führt sie als
      Zeichenkette, `geometrie_qa` als Vorzeichen. Übersetzt wird über die benannte Tabelle
      `POLARITAETSZEICHEN` — und **gemessen schlägt deklariert**: Die Zeichenkette gehört
      zum Schätzer, das Vorzeichen zum *Paar* aus Schätzer und unserer Soll-Konvention.
      Für `depth-anything-v2-small` stimmen beide überein; dass sie das tun, ist ein
      Befund und keine Regel. Ob die beiden Schreibweisen zusammengelegt gehören, ist
      offen.

- [x] **`auf-30` beantwortet: Die Kante misst weder Anwesenheit noch Schärfe, sondern die
      MEHRHEIT DES UMRISSES.** Beide von mir angebotenen Möglichkeiten sind widerlegt.

      Gegen *(b) Schätzer-Artefakt*: Weichzeichnen nimmt die Kante nur langsam — Radius 4
      liegt mit 0.0628 noch über der Schwelle, das Niveau der erzeugten Bilder wird erst
      bei Radius 12.1 erreicht. Gegen *(a) weiches Bild*: Bei ρ = −0.9059 müsste die Kante
      auf der Kurve 0.0349 sein, gemessen 0.0058 — Faktor 6 daneben, durch Unschärfe nicht
      herstellbar.

      **Die Ursache ist der Median.** Das Mass bildet ihn über das ganze Randband; zeichnet
      ein Bild nur ein Viertel seines Umrisses, sieht der Median **nichts**. Ohne jeden
      Schätzer nachgemessen — Anteil der Grenze, der eine Kante trägt:

      | perfekt | weichgezeichnet-8 | mit Führung | ohne Führung | qwen |
      |---|---|---|---|---|
      | 87.4 % | 43.8 % | 24.3 % | 6.4 % | **2.8 %** |
- [x] **Das zweite Bein ist gebaut (22.08.): `anteil_grenze_mit_kante`.** Es fällt
      allmählich statt zu kippen, braucht keinen Schätzer — und **bringt seinen eigenen
      Nullwert mit**: Werden die stärksten 5 % als Kante gewertet, trifft eine bezugslose
      Grenze ebenfalls rund 5 %. Keine andere Schwelle dieses Moduls hat das; überall
      sonst kostet der Nullwert eine eigene Nullprobe je Szene.

      **Eine Berichtigung beim Bauen, gefunden am eigenen Testbild:** Bei vielen
      Gleichständen sind die „stärksten 5 %" gar nicht 5 %. Gemeldet wird darum der
      **tatsächliche** Anteil über der Schranke, und gegen ihn wird gelesen. An einer
      Streifenkarte: roh 57.9 % der Grenze getroffen — sähe nach viel aus —, echter
      Nullwert 59.4 %, also **nicht mehr als Zufall**. Gegen die verlangten 5 % gelesen
      hätte das Mass ein Signal behauptet, wo keines ist.
- [ ] **DIE WARNUNG, die den Paartest überhaupt rechtfertigt.** Qwen erreicht ρ = −0.7406
      — ordentlich, deutlich über dem Rauschboden — und zeichnet den Umriss an **2.8 %**
      der Grenze, also **unter Zufall**. **Ein anständiges ρ ist ohne jede Umrisstreue
      erreichbar.** Wer ρ allein wertet, wertet ein Bild, das die Tiefen richtig staffelt
      und das Gebäude nicht zeichnet.
- [ ] **`PAAR_KANTENANTEIL_SCHWELLE = 0.20` ist abgelesen und unbequem.** Sie liegt beim
      Vierfachen des Zufalls und bei einem knappen Viertel des perfekten Bildes. Sie lässt
      unser bestes erzeugtes Bild durch (24.3 %) und weist das ungeführte ab (6.4 %) —
      aber sie liegt damit **sehr viel näher am Zufall als am Richtigen**. Welche
      Umrisstreue ein Bild haben *muss*, hat niemand entschieden. Die Zahl markiert die
      Lücke, sie behauptet nicht, dass 20 % genügen.
- [ ] **Verdacht gegen die frontale INNENANSICHT — ungemessen, und deshalb nicht
      abgeschaltet.** `auf-29` fand: Für ρ über der Maske muss der Blick **mehr als eine
      Fläche** zeigen, sonst misst man den Schätzer statt der Geometrie (frontal vor einer
      Langseite: −0.8305, +0.6509, +0.8159 — mit Vorzeichenwechsel).

      Eine frontale Innenaufnahme zeigt genau das: eine Wand senkrecht zur Blickachse.
      **Aber innen ist die Lage nicht dieselbe** — Boden, Decke und die anschneidenden
      Seitenwände liegen schräg im Bild und tragen Tiefe. Die Ansicht wird darum weiter
      geliefert; sie wegzulassen wäre ein Schluss von einer Messung auf einen Fall, den
      sie nicht enthält. Die Messung ist billig: dieselbe Szene, beide Blickarten, ρ und
      Kante vergleichen.
- [x] **`auf-29`: Die Kameraneigung stört den Schätzer NICHT.** Eckansicht, drei
      Ausrichtungen, alle innerhalb von 0.019 — die waagrechten sind sogar marginal
      schlechter. **Der Umbau von `kameras.py` bleibt richtig, weil die Fachnorm ihn
      verlangt, ist aber kein Beitrag zur Bildqualität.** Genau dafür war die Messung da:
      Ich wollte es wissen, *bevor* ich baue.
- [x] **`auf-28`: Nicht der Backbone war es, die Schablone war es.** Die Führung kommt an
      (z-image-turbo mit gegen ohne: Abstand 0.650). Ob qwen oder z-image-turbo besser
      ist, bleibt **unentschieden** — 0.165 Abstand entspricht etwa einer
      Standardabweichung der Seed-Streuung, und drei Bilder klären das nicht.

## Die gepaarte Reihe — die Methode, an der zwei Messungen gescheitert sind

- [x] **`gepaarte_reihe` und `zaehle_siege` gebaut (22.08.), auf Bitte der HomeStation.**
      Sie hat es zweimal an einem Tag erlebt: Bei `auf-28` war der Abstand zwischen zwei
      Backbones (0.165) etwa **eine Standardabweichung** der Startwert-Streuung — an drei
      Bildern nicht entscheidbar. Beim Sprachbefund trug n = 3 nicht (Abstand 25.5 gegen
      Streuung 20.7), **erst acht Paare entschieden**: bei gleichem Startwert gewann der
      englische Prompt 8 von 8 Mal.

      > Gleicher Startwert, eine Sache anders, zählen wer gewinnt.

      Der Grund, warum das so viel billiger ist: Die Streuung über Startwerte (0.2269) ist
      in diesem Projekt **grösser als jeder gemessene Parametereffekt** (0.10–0.14). Ein
      Mittelwertvergleich muss dagegen anmessen, ein Paarvergleich rechnet sie heraus.

      Die Sprachreihe ist als Test hinterlegt und wird nachgerechnet — 8 von 8, p = 0.78 %.
      **Zweiseitig gerechnet**, nicht einseitig: Einseitig zu rechnen, *nachdem* man das
      Ergebnis gesehen hat, halbiert die Zahl und die Ehrlichkeit gleich mit.
- [x] **Ein Wächter, der nur unter meinen Testbedingungen tot aussah.** Die
      Mutationsprobe überlebte `and n >= MIN_PAARE`. Grund: Bei **zwei** Werten ist die
      Schranke rechnerisch redundant (fünf Paare ergeben 6.25 %, sechs 3.1 % — die
      Fünfprozentmarke fällt genau bei `MIN_PAARE`). Bei **drei** Werten nicht: Ein
      Durchmarsch über drei Paare kommt in 3.7 % der Fälle vor und gälte ohne Schranke als
      belegt.

      **Der Unterschied zum Eckenwächter in `raumkamera.py` ist der Punkt:** Der griff
      wirklich nie und wurde entfernt. Dieser greift, nur nicht dort, wo ich zuerst
      hingesehen habe. Test nachgezogen statt Code entfernt.
- [ ] **DER SPRACHBEFUND TRIFFT DEN PRODUKTPFAD, und er ist ungelöst.** Die Oberfläche
      sammelt **deutsch** und legt es wörtlich in `style.prompt`; das Modell versteht
      **englisch**. Gemessen: `overcast sky` +0.3 gegen `bedeckter Himmel` +17.8
      Blauüberschuss. Verlangt war ein bedeckter Himmel, geliefert wurde blauer.

      Drei Auswege, und keiner ist bei uns allein zu haben: die Oberfläche sammelt
      englisch, wir übersetzen vor dem Rendern, oder das Modell bekommt beides. Das erste
      ist eine Frage an den Cloud-Worker, das zweite eine Entscheidung des Owners (eine
      Übersetzung ist eine stille Änderung am Prompt des Nutzers).
- [ ] **Vakuumprobe: 9 Treffer statt 6 — alle drei neuen sind gedeckt.** Zwei tragen ihre
      Gegenprobe **im selben Test** (`test_komposition.py`), die Probe sieht das nicht,
      weil sie je Zusicherung urteilt und nicht je Mechanismus. Der dritte
      (`test_maske.py`) hatte eine Gegenprobe, die aber eine **andere Zeichenfolge**
      prüfte — wäre der Warntext geändert worden, hätte der eine vakuum-wahr bestanden und
      der andere wäre gefallen. Zusammengezogen: dieselbe Zeichenfolge, einmal erwartet,
      einmal nicht.

## DAS TOR — offen, und der Weg zu, gefunden (auf-25 bis auf-27)

- [x] **`auf-27`: Der Prüfstein fällt, und die Antwort ist trotzdem da.** Verlangt war:
      Kante deutlich bei perfekt/H3/H4, keine bei H1/H2. Tatsächlich zeigen H1 (+0.0006)
      und H2 (+0.0007) wie erwartet keine — **aber H3 (+0.0066) und H4 (+0.0021) auch
      nicht**, alle vier um Faktor 25 bis 75 unter dem perfekten Bild (+0.1615).

      **Der Grund ist zwingend und war vorhersehbar, hätte ich gründlicher nachgedacht:
      Die Maske ist die Silhouette des RICHTIGEN Bauwerks.** Ein gedrehtes oder anders
      geformtes hat seine Kanten woanders; an der Maskengrenze steht dann Grund, genau wie
      bei Abwesenheit. Das Mass fragt nicht *„steht dort etwas"*, sondern *„steht dort das
      Richtige"*.
- [x] **UND DAMIT IST DIE LÜCKE GESCHLOSSEN — durch zwei Masse, nicht durch eines.**

      | Fall | ρ über der Maske | Kante | gefangen von |
      |---|---|---|---|
      | H1 · Bauwerk weg | −0.6861 ✗ | +0.0006 ✓ | **Kante** |
      | H2 · 20 m versetzt | −0.6854 ✗ | +0.0007 ✓ | **Kante** |
      | H3 · andere Kubatur | +0.3842 ✓ | +0.0066 ✗ | **ρ** |
      | H4 · 90° gedreht | −0.4546 ✓ | +0.0021 ✗ | **ρ** |

      **Jedes Mass fängt genau die Fälle, die das andere verfehlt.** Zusammen decken sie
      alle vier ab, einzeln keiner von beiden. Der Satz, auf den das hinausläuft, ist der
      Ertrag dieser ganzen Kette: **Existenz und Richtigkeit sind zwei Fragen und brauchen
      zwei Messungen.** Ein einzelner Score kann beides nicht leisten — und `geom_iou`, das
      es versuchte, belohnte am Ende die Abwesenheit.
- [ ] **Der Paartest — Vorschlag der HomeStation, ausdrücklich UNGEMESSEN.**
      `ρ ≤ −0.80 UND Kante ≥ 0.05` lässt von allen geprüften Fällen nur das perfekte Bild
      und den 1-m-Versatz durch. Trennschärfe der Kante unter der Lesart „richtige
      Silhouette besetzt": **0.0589, Faktor 10** — brauchbar. Wörtlich genommen nur 0.0014,
      unbrauchbar.

      **Es ist eine Ablesung an sieben Fällen aus einer Szene, keine Kalibrierung.** Das
      sagt die HomeStation selbst dazu, und es ist der Unterschied, an dem dieses Projekt
      seit Phase 0 arbeitet.
- [ ] **DIE UNBEQUEME FOLGERUNG, die niemand ausgesprochen hat: Der Paartest würde jedes
      Bild abweisen, das wir je erzeugt haben.** Der zweite Nachtrag zu `auf-24` hat
      gemessen, dass **alle fünf erzeugten Bilder über der Maske schlechter liegen als
      weisses Rauschen** (−0.5207). Eine Schwelle von −0.80 ist für sie unerreichbar.

      Das ist **kein Argument gegen den Paartest**, sondern der eigentliche Befund: Nicht
      die Schwelle ist zu streng, sondern unsere erzeugten Bilder sind geometrisch
      schlecht. Ein Tor, das sie durchlässt, wäre ein Tor ohne Aussage. Die Reihenfolge
      der nächsten Arbeit steht damit fest — **erst die Bilder, dann die Schwelle**, und
      die Kamera zuerst.
- [x] **Gebaut (22.08.): `kante_an_maskengrenze` und `paarurteil`.** Die Kante misst den
      Tiefensprung an der Silhouettengrenze — Median innen gegen Median aussen, geteilt
      durch die Spanne der ganzen Schätzkarte (sonst misst man die Skala des Schätzers
      statt der Kante). Gerichtet über die Polarität: ``gerichtet = −polaritaet · roh``,
      hergeleitet und an **beiden** Konventionen geprüft, weil ein verdrehtes Vorzeichen
      hier hiesse, dass ein Bild MIT Bauwerk durchfällt und eines ohne besteht.

      Das `paarurteil` **führt beide Zahlen und verrechnet sie nicht**. Ein Test prüft
      das am Verhalten statt am Quelltext: Zwei Paare mit gleichem Produkt, aber
      verschiedener Verteilung, gehen verschieden aus — ein Score könnte sie nicht
      unterscheiden. Fehlt eine der beiden Zahlen, ist das Urteil *nicht gemessen* und
      nicht „bestanden aufgrund der anderen".

      Nachgerechnet: Von den fünf gemessenen Fällen besteht nur das perfekte Bild.
      Mutationsprobe: sieben Kappungen, sieben Mal rot, jedes Muster nachweislich
      gegriffen.

      **Der Vorbehalt steht als Warnung im Docstring, nicht in einer Fussnote:** Dieser
      Paartest würde jedes Bild abweisen, das dieses Projekt je erzeugt hat. Wer die
      Schwelle senkt, weil sonst nichts besteht, hat nicht kalibriert, sondern aufgegeben.
- [ ] **Ein leeres Grundstück besteht die Geometrie-QA mit 0.95.** Gemessen
      (`auf-20260821-26`, `docs/GEOM_IOU_HALLUZINATION_2026-08-21.md`), Szene mit 59.8 %
      Bodenanteil:

      | | `geom_iou` | Score |
      |---|---|---|
      | perfektes Bild | 0.9703 | 0.9839 |
      | **H1 · Bauwerk ganz weg** | **0.9848** | **0.9530** |
      | H2 · 20 m versetzt | 0.9845 | 0.9526 |
      | weisses Rauschen | 0.5682 | 0.7217 |

      **`geom_iou` fängt die Abwesenheit nicht — es belohnt sie.** Das leere Grundstück hat
      eine *höhere* Überdeckung als das perfekte Bild und besteht die Schwelle 0.65 mit
      grossem Abstand. Die Erklärung ist einen Schritt schärfer als vermutet: Das Bauwerk
      war die einzige Stelle, an der Soll und Ist sich überhaupt unterscheiden konnten;
      nimmt man es weg, deckt sich fast alles.

      **Weder ρ noch `geom_iou` erkennt ein Bild ohne Bauwerk.** Mein eigener Satz
      „`geom_iou` darf nicht fallen" war zur Hälfte richtig (ρ allein genügt nicht) und zur
      Hälfte irreführend: Die Lücke ist damit **offen und nicht gefüllt**. Das ist der
      elementarste denkbare Fehlerfall — „das Bild zeigt das Gebäude nicht" —, und das Tor
      lässt ihn durch.
- [ ] **Übrig ist genau ein ungeprüfter Kandidat: die Tiefenkante an der Maskengrenze.**
      Ein Bauwerk erzeugt dort einen Tiefensprung, ein leeres Grundstück nicht. Frage 2 von
      `auf-26` blieb unbeantwortet; sie steht als `auf-20260821-27` neu.
- [ ] **Bis dahin gilt: Die Geometrie-QA darf kein „bestanden" aussprechen, ohne dazu zu
      sagen, dass sie Abwesenheit nicht erkennt.** Das ist keine Verfeinerung, sondern die
      Mindestehrlichkeit — ein Abzeichen, das ein leeres Grundstück durchlässt, behauptet
      etwas, das es nicht geprüft hat. In den Code zu bringen, sobald der laufende Agent
      `geometrie_qa.py` freigibt.

## Die Geometrie-QA neu bauen — der Stand, auf dem morgen anzufangen ist

- [ ] **Der Score wird `polaritaet * spearman` über der Bauwerksmaske.** Gemessen
      monoton, gemessen szenenunabhängig, ohne Normierung und ohne Anker-Arithmetik. Die
      Bausteine liegen: `polaritaet` seit 21.08. im Modul, die Maske aus dem
      Material-ID-Pass. Zu bauen sind der Maskenweg durch `abholer`/`seams` und die
      Ablösung des alten Scores — **nicht** durch stilles Ersetzen: Alle bisherigen Zahlen
      sind mit `sqrt(|ρ| · geom_iou)` entstanden und müssen unterscheidbar bleiben
      (`METHODE` gegen `METHODE_GERICHTET`, jetzt eine dritte Zeile dazu).
- [ ] **NICHT VERLIEREN: `geom_iou` war der Halluzinationsfänger.** Er fragt, ob das
      Gebäude **dort** ist, wo es hingehört; ρ fragt nur, ob die Tiefen **innerhalb** der
      Maske richtig gestaffelt sind. Ein erfundenes Gebäude an falscher Stelle könnte über
      der Maske eine hohe Rangkorrelation erreichen — das ist die Erpressbarkeit, gegen
      die `geom_iou` überhaupt eingeführt wurde.

      **Der Verdacht, dass es trotzdem gutgeht, ist eine Vermutung und keine Messung:**
      Weisses Rauschen erreicht über der Maske −0.5207 gegen −0.99 beim perfekten Bild,
      die Trennung ist also da. Ob eine *halluzinierte Kubatur* dort ebenfalls tief fällt,
      ist **nicht gemessen** — und genau dieser Fall ist der Grund für den zweiten Faktor.
      Nächster Auftrag: dieselbe Reihe, aber mit einem Bauwerk an falscher Stelle statt
      eines verschobenen. Erst danach darf `geom_iou` fallen.
- [ ] **Der Rauschboden über der Maske ist eine Zahl, keine Null.** −0.5207 in beiden
      Szenen — bemerkenswert genau gleich, was für sich schon einen Blick wert ist. Eine
      Schwelle muss darüber liegen; wo genau, ist die alte offene Frage in neuer Form.
- [ ] **(hinfällig) Eine feste Schwelle kann es nicht geben — welcher ANTEIL genügt, ist ungemessen.**
      Decke und Boden schwanken je Szene um mehr als das Doppelte; die szenenunabhängige
      Grösse ist `(score − rauschen) / (perfekt − rauschen)`. `einordnung()` rechnet sie,
      der Abholer misst die Anker selbst. **Welcher Anteil genügen soll, steht nirgends —
      weil es niemand gemessen hat.** Das ist die nächste Frage, und sie ist die letzte
      grosse offene an der Geometrie-QA.
- [ ] **Der Rest ist kein Rechenfehler, sondern ein echter Rückstand.** Der Deckel lag bei
      0.636, die erzeugten Bilder bei 0.265 — zwischen *bestmöglich* und *erreicht* klafft
      noch einmal derselbe Abstand. Beides ist wahr, und keines erklärt das andere weg.
      `auf-21` misst zum ersten Mal auf einer Szene, auf der die Schwelle überhaupt
      erreichbar ist; erst dort sagt ein Ergebnis etwas über das Bild.
- [x] **Das Lexikon prüft sich jetzt selbst** — 2026-08-20, `tests/test_lexikon.py`,
      13 Tests. Anlass: **Seed** stand zweimal darin, in zwei Fassungen, in zwei
      Abschnitten. Beim Nachzählen waren es sieben Begriffe mit Doppeleinträgen.
      Drei davon waren echte Dubletten (Seed, Prompt, Halluzination, Tote Kante) und sind
      zusammengeführt — bei *Tote Kante* trugen **beide** Fassungen eigenen Inhalt, der
      jetzt in einer steht. Vier sind ausgewiesene Bedeutungstrennungen und stehen als
      solche in einer Liste, die der Test gegenprüft: Wer dort etwas einträgt, muss es im
      Lexikon auch am Titel unterscheidbar machen.
      *Ein Lexikon, das denselben Begriff zweimal erklärt, veraltet an einer der beiden
      Stellen — und wer die falsche liest, liest die alte.*
- [x] **Fortschrittsgrenze für den Renderlauf** — 2026-08-20, `fortschritt.py`,
      25 Tests, reine stdlib, Uhr injizierbar.
      **Beim Nachbauen stellte sich heraus, dass wir es gar nicht schlechter hatten.**
      Der `no_progress_timeout` des Altbestands setzt bei `status in ("running",
      "queued")` die Uhr zurück und wartet weiter — also in genau den beiden Zuständen,
      in denen ein hängender Sampler steckt. Er feuert nur bei `unknown` und bei
      Statuswörtern, die das Programm nicht kennt; den Rest fängt der harte
      `max_seconds`, den wir schon haben.
      **Die Ursache ist kein Programmierfehler, sondern das Signal:** Ein Statuswort ist
      eine Behauptung, kein Beleg — aus einem unveränderten „running" lässt sich
      *langsam* nicht von *hängend* trennen. Unsere Wache löst das nicht durch eine
      klügere Frist, sondern indem sie die Frage dorthin verschiebt, wo sie beantwortbar
      ist: Ein **belegtes** Zeichen (Schrittzähler, wachsende Datei, neue Datei im
      Ausgabeordner) darf `error` melden, ein **behauptetes** höchstens `warn` — und sagt
      dazu, warum es nicht mehr kann. Dieselbe Regel wie beim Belichtungsrahmen.
      Die Wache **bricht nichts ab**: Abgebrochen wird eine Stufe höher, wo man weiss,
      was ein Abbruch kostet.
- [x] **Die Wache an die Blender-Naht gehängt** — 2026-08-20, `starter_mit_wache` in
      `seams.py`. **Als anderer Starter, nicht als Änderung am Vertrag:** Der
      Injektionspunkt `_starte(cmd, timeout)` gibt es seit Phase 1 für Tests; die
      Überwachung hat genau dieselbe Gestalt. Kein bestehender Test musste angefasst
      werden. Ausgaben laufen über temporäre **Dateien**, nicht über Pipes — wer bei
      `PIPE` pollt statt zu lesen, blockiert den Kindprozess, sobald der Puffer voll ist,
      und der Lauf bliebe durch genau die Wache stehen, die ihn retten soll.
- [x] **Blenders Ausgabetakt gemessen** — 2026-08-20,
      `docs/BLENDER_AUSGABETAKT_2026-08-20.md`. Zwei Läufe, übereinstimmend: Über 190 s
      wuchs die umgeleitete Standardausgabe **sechsmal** — bei 34, 66, 98, 130, 162 und
      190 Sekunden, also **exakt alle 32 Sekunden**, insgesamt um 937 Bytes.
      **Der Befund widerlegt die erste Vermutung**, Blender schreibe während des Renderns
      gar nichts: Es gibt ein Signal, es hat nur eine grobe Körnung. Und die Körnung ist
      die Untergrenze jeder Frist — `glb_zu_multipass` **weist** darum Fristen unter
      96 Sekunden (drei Takte) **ab**, mit den Messpunkten in der Fehlermeldung. Nicht im
      Docstring: *Ein Docstring ist keine Prüfung* (Lehre aus Sitzung 07).
      **Nebenbefund mit Folgen:** Mit adaptivem Sampling war derselbe Lauf mit *6000*
      Samples nach **12 Sekunden** fertig. Die Samplezahl unserer Aufträge ist eine
      Obergrenze und **keine** Angabe der Rechenzeit — wer daraus eine Dauer schliesst,
      liegt um mehr als eine Grössenordnung daneben.
- [x] **Hält der Takt auch auf der GPU? — NEIN, dort gibt es gar keinen.**
      `auf-20260820-18`, Blender 5.2.0 LTS, OptiX auf einer RTX 5090, zwei Läufe **auf
      die Zehntelsekunde identisch**: Die Ausgabe wächst **dreimal** — bei 1,0 s, 2,0 s
      und 177,0 s. Dazwischen **175 Sekunden Stille**, ohne eine einzige Fortschrittszeile
      in 739 Bytes.
      **Die Zahl 32 war ein Artefakt der CPU-Messung.** Die daraus abgeleitete Frist von
      96 s hätte auf der HomeStation *jeden gesunden Lauf über 98 Sekunden abgebrochen*.
      `glb_zu_multipass` **weist darum jeden Wert von `stillstand_frist_s` ab** — nicht
      mehr „zu kurz", sondern „es gibt keinen".
      *Eine Messung gilt so weit, wie gemessen wurde. Der Vorbehalt war nicht Höflichkeit,
      sondern die halbe Erkenntnis.*
- [x] **Ein Blender, das bei Dateiumleitung schweigend nichts tut** — derselbe Auftrag,
      und der gefährlichere Befund. Das Snap-Paket **Blender 5.2.0 LTS** (das einzige dort
      mit OptiX/CUDA) beendet sich bei `>` in eine Datei nach 1,3 s mit **Rückgabewert 0,
      ohne Ausgabe und ohne Bild**. An vier Ablageorten gegengeprüft. Über eine Pipe
      rendert dasselbe Blender einwandfrei.
      **Das traf Code vom selben Vormittag:** `starter_mit_wache` leitete `stdout` in eine
      temporäre Datei um und hätte auf der HomeStation nie ein Bild erzeugt. Behoben mit
      der Bauart der HomeStation — Pipe plus ein Faden, der sie **laufend** in die Datei
      giesst. Damit fällt beides weg: Der Puffer läuft nie voll, und die Datei wächst
      genau dann, wenn der Prozess schreibt.
- [x] **Eine tragende Quelle gefunden — gemessen, nicht geraten.** 2026-08-20, alle drei
      Kandidaten im selben Blender-Lauf geprüft: `bpy.app.handlers.render_stats` feuerte
      **null** Mal, `bpy.app.timers` **null** Mal, ein gewöhnlicher `threading.Thread`
      **61** Mal. **Cycles gibt während des Renderns die GIL frei** — die beiden
      dokumentierten Haken nützen nichts, ein einfacher Faden schon.
      Gebaut als `--herzschlag-s` im Runner (`<out>/herzschlag.txt`, **angehängt**, damit
      die Datei wächst) und `glb_zu_multipass(herzschlag_takt_s=…)` auf unserer Seite.
      An einem echten Lauf nachgewiesen: **22 Schläge über 42 s, längste Lücke 2,1 s.**
      Die Wache schlägt bei **fünf** ausgefallenen Schlägen an — bei 2 s Takt also nach
      10 s, *neunzigmal* früher als der Gesamt-Timeout von 900 s.
      **Die Einschränkung steht im Docstring und im Namen:** Das ist ein *Lebenszeichen*
      und kein *Fortschrittszeichen*. Ein festgefahrener Cycles-Kern schlägt weiter; die
      Wache schlägt nur auf Stille an, und nur darauf trägt der Schluss.
- [x] **Gibt Cycles auch bei OptiX die GIL frei? — JA.** `auf-20260820-19`, RTX 5090,
      Blender 5.2.0 LTS, zwei Läufe identisch: **88 Schläge über 175,3 s, längste Lücke
      2,10 s** bei 2,0 s Takt, Nummern lückenlos von 1 bis 88, **keine verhungerten
      Schläge**.
      **Der Kontrast ist der Beleg:** dieselbe Szene, dieselbe Dauer, derselbe Rechner wie
      in `auf-20260820-18` — dort schwieg die Standardausgabe 175 Sekunden am Stück. Der
      Unterschied liegt nicht am Renderer und nicht am Gerät, sondern daran, *wer* schreibt.
      **Der Herzschlag ist damit voreingestellt.** Die Frist von 10 s liegt fast beim
      Fünffachen der grössten je beobachteten Lücke; ein hängender Lauf fällt nach 10
      statt nach 900 Sekunden auf.
- [x] **Der Schrittzähler im Renderlauf** — 2026-08-20, `render.rendere(schrittzaehler=…)`
      über `callback_on_step_end`. **Das sauberste belegte Fortschrittszeichen, das dieses
      Projekt hat:** Er zählt Diffusionsschritte, die wirklich gerechnet wurden — im
      Unterschied zum Herzschlag des Blender-Laufs, der nur bezeugt, dass ein Prozess lebt.
      **Und er förderte sofort etwas zutage, das wir bisher nicht wussten:** Das Ergebnis
      trägt jetzt `schritte_gerechnet`, und im Bildbearbeitungsmodus rechnen viele
      Pipelines nur `schritte × denoise`. Der Parametersatz nennt die **bestellte** Zahl —
      wer zwei Läufe über die Schrittzahl vergleicht, verglich unter Umständen etwas
      anderes. Weicht die Zahl ab, steht die Rechnung als Hinweis im Ergebnis.
      Kennt eine Pipeline den Rückruf nicht, ist `schritte_gerechnet` **`None`** und heisst
      *ungemessen*, nicht null — und es wird ausdrücklich **keine** Abweichung behauptet.
      Nebenbei prüfbar geworden: `_pipeline_adapter` galt als „die einzige Stelle des
      Moduls, die hier nie ausgeführt werden kann". Mit einer klar benannten Pillow- und
      torch-Attrappe ist der Weg jetzt begehbar — die Attrappen ersetzen nichts, sie
      machen nur unsere eigene Verdrahtung sichtbar.
- [ ] **Ist die Abweichung `schritte × denoise` bei unseren Backbones real?** Die Regel ist
      aus der diffusers-Bauart abgeleitet und an einer Attrappe geprüft, **nicht am
      Gerät**. Wenn sie zutrifft, hat jede bisherige Messreihe über die Schrittzahl im
      Bildbearbeitungsmodus weniger Schritte gerechnet als protokolliert.
- [x] **Die Wache an den Abholer hängen — erledigt 21.08.** `fortschritt.Beobachter`
      fragt eine Wache in Abständen und merkt sich den **schlimmsten** Befund; der
      Abholer baut je Auftrag eine eigene (`wache_bauen`) und hält sie auch auf dem
      Fehlerweg an. Der längste Stillstand landet in `timings.stillstand_s` — einem
      **Vertragsfeld**, das `nur_vertragsfelder` übersteht. Damit ist ein Lauf, der
      1800 s brauchte und davon 1500 s stand, zum ersten Mal von einem unterscheidbar,
      der 1800 s gerechnet hat; bisher sahen beide gleich aus.

      Drei Dinge, die dabei entschieden wurden und nicht selbstverständlich sind:
      **(1)** Keine Wache heisst `wache is None` und **nicht** „lief durch" — ein
      unbeobachteter Lauf bekommt keine Null in die `timings`, denn eine Null hiesse
      „stand nie" und wäre eine Behauptung ohne Beleg. **(2)** `bei_stillstand` wird
      **einmal je Ereignis** gerufen, nicht bei jedem Blick; eine halbe Stunde
      Stillstand im Zweisekundentakt wären sonst neunhundert Rufe für eine Nachricht.
      **(3)** Eine Wache, die beim Bauen stolpert, verhindert den Lauf nicht — sie
      verschwindet aber auch nicht spurlos, sonst sähe ein unbeobachteter Lauf hinterher
      aus wie ein beobachteter ohne Befund.

      **Was NICHT geprüft ist:** ob eine Wache an einem echten Renderlauf das Richtige
      sieht. Alle 26 Tests laufen gegen Verzeichnisse, in die der Test selbst schreibt.
      Welcher Pfad sich während eines Multipass-Laufs wirklich bewegt und welche Frist
      dort trägt, ist am Gerät zu messen — die 32-s-Takt-Geschichte vom 20.08. ist die
      Warnung dazu.
- [x] **Die Wache läuft im Betrieb mit (21.08.).** `tools/abholen.py` baut sie je Auftrag
      auf dessen Ausgabeordner — dort, wo eine neue Datei ein **belegtes** Zeichen ist.
      Der Pfad gehört zum Betrieb und nicht zur Bibliothek, darum wird sie dort gebaut
      und nicht im Abholer. Schalter `--stillstand-frist-s` und `--ohne-wache`; der
      Bericht sagt je Auftrag „nicht beobachtet", „NICHT GEMESSEN" oder die längste Pause.
      Sechs Tests in `tests/test_abholen_cli.py`, alle drei Verdrahtungen an einer
      Mutationsprobe geprüft: Jede Kappung macht genau einen Test rot.
- [ ] **Welche Frist trägt am echten Lauf? — und die Messung kostet nichts mehr.**
      Die Frist ist geraten (aus dem Altbestand, nicht gemessen). **Erster Anhaltspunkt
      seit 19.08.:** Der erste vollständige Lauf brauchte 292,2 s für drei Kameras, rund
      97 s je Kamera. Die Vorgabe von 300 s wäre damit länger als der ganze Auftrag und
      bliebe wirkungslos.

      **Es braucht dafür keinen eigenen Auftrag mehr.** Der Bericht der Wache nennt die
      längste Pause auch dann, wenn nie ein Stillstand eintrat — unter lauter
      unauffälligen Befunden behält sie den mit der längsten Pause. Ein Lauf mit
      `--stillstand-frist-s 99999` misst sie also nebenbei und schlägt nirgends Alarm.
      Der Wert unterschätzt um bis zu einen Takt (2 s), weil an den Blicken gemessen wird
      und nicht an den Dateien — für eine Frist mit Sicherheitsabstand die harmlose
      Richtung.
      `FRIST_S = 300` ist aus dem Altbestand übernommen, ausdrücklich **nicht** gemessen.
      Zu kurz bricht gesunde Läufe ab, zu lang merkt nichts. Braucht die HomeStation:
      längste beobachtete Pause zwischen zwei neuen Dateien im Ausgabeordner, an CPU und
      GPU getrennt — wie beim Blender-Ausgabetakt, wo genau diese Unterscheidung den
      Unterschied zwischen 32 s und 175 s ausmachte.
- [ ] **Variantenreihen** — wir erzeugen ein Bild je Aufruf. Der alte Bestand fährt fünf
      Sampler mit `seed = basis + nummer` und kennt ein `locked_seed` für kontrollierte
      Reihen. Bei 1.4 s je Bild (`auf-13`) ist eine Reihe zum ersten Mal bezahlbar.
- [x] **Hat die Szene ohne Boden den `geom_iou`-Deckel verursacht? — JA, und die
      gestrige Vorgabe ist damit unbrauchbar.** `auf-20260819-15`, vier Szenen:

      | Szene | `wie_soll` | `ohne_randberuehrung` |
      |---|---|---|
      | ohne Boden | iou 0.256 | iou **0.406** |
      | Platte, endlich | iou 0.967 | **0 Punkte** |
      | Ebene bis Rand | iou 0.974 | **0 Punkte** |
      | Ebene mit Horizont | iou 1.000 | **0 Punkte** |

      **Sobald ein Boden da ist, berührt jede Fläche den Rand.** `ohne_randberuehrung`
      gewann in `auf-12`, *weil* die Szene keinen Boden hatte — dort verwarf sie eine
      Halluzination. Mit Gelände verwirft sie **richtige Geometrie**, und zwar restlos.
      Die Vorgabe ist auf `wie_soll` zurückgenommen; die Regel bleibt **wählbar** für den
      einen Fall, den sie löst — eine freigestellte Szene.
      *Der Vorbehalt stand im Docstring jener Regel, wörtlich. Er war die halbe
      Erkenntnis — dieselbe Lehre wie beim Blender-Takt am selben Tag.*
- [x] **Eine randlose Silhouette macht `geom_iou` bedeutungslos** — Nebenbefund derselben
      Messung, und niemand hatte danach gefragt. Bei *Ebene mit Horizont* war `geom_iou`
      **exakt 1.0000**, weil `n_soll` gleich der Bildpunktzahl war: 262 144 von 262 144.
      Es gab keinen Hintergrund mehr. Eine Silhouette, die das ganze Bild ist, überdeckt
      jede andere, die das ganze Bild ist — der Wert sieht nach perfekt getroffener Kontur
      aus und misst nichts; der Score ruht dort allein auf `spearman`.
      `geometrie_score` **meldet** das jetzt, verwirft es aber nicht: Welche der beiden
      Karten randlos ist, weiss der Aufrufer besser als die Funktion.
- [x] **ENTSCHIEDEN 21.08. (Owner): VORDERGRUND FÜLLEN.** Festes Bildformat, die Szene
      bekommt Vordergrund — Wiese, Bäume, Umgebung —, das Format folgt nicht dem
      Baukörper. Einheitlich über alle Aufträge und konventionell für
      Architekturvisualisierung.

      **Der Entscheid ging gegen meine Empfehlung, und die Folge gehört hierher, nicht in
      eine Fussnote:** Vordergrund füllen heisst bodenlastige Szenen als Regelfall. Genau
      dort war die Geometrie-QA am 20./21.08. stumpf — bei 59.8 % Bodenanteil erreichte
      weisses Rauschen den Score 0.72, und die Reihe war nicht monoton. **Damit ist die
      Bauwerksmaske keine Verbesserung mehr, sondern Voraussetzung:** Eine QA über das
      ganze Bild misst bei diesen Szenen zwei Bodenrampen gegeneinander. Was vorher eine
      Option war, ist jetzt der einzige Weg — und das ist ein sauberes Ergebnis, weil die
      Entscheidung die Technik bestimmt und nicht umgekehrt.
- [x] **Der Beauty-Pass trennt Bauwerk und Hintergrund — gemessen, und die Sorge trifft
      so nicht zu.** 2026-08-20, an zwei Szenen. Möglich wurde die Messung erst durch den
      farbfähigen Leser vom selben Tag und die Silhouette aus der Tiefen-EXR: Sie sagt
      Punkt für Punkt, was Bauwerk ist.

      | | Bauwerk | Hintergrund | Trennschärfe |
      |---|---|---|---|
      | Testbau (0 Materialien) | 0.676 ± 0.033 | 0.423 ± 0.003 | **13.9** |
      | Testszene (2 Materialien) | 0.660 ± 0.039 | 0.424 ± 0.007 | **10.2** |

      **Die Mittelwerte liegen weit auseinander**, nicht dicht beieinander. *Aber* die
      Wertebereiche **überlappen** — der hellste Hintergrundpunkt ist heller als der
      dunkelste Bauwerkspunkt. Wer eine Silhouette aus der Helligkeit gewinnen wollte,
      käme nicht durch; genau darum kommt sie bei uns aus der EXR.
- [x] **„Sehr wenig Zeichnung" — die Zeichnung hängt an den Materialien, nicht am Pass.**
      Dieselbe Messung: 90 % der Bauwerksfläche liegen bei **0 Materialien in 3** von 42
      Grauwerten, bei **2 Materialien in 18** von 39. Sechsmal so viele Töne, nur weil
      Materialien da sind — ein ungefärbter Körper hat drei sichtbare Flächen und darum
      drei Töne. Das ist eine Eigenschaft der Geometrie, die man dem Pass gibt, und keine
      des Passes.
      *Vorbehalt: Die Testszene rendert klein, rund 500 Bauwerkspunkte. Die Richtung ist
      belastbar, die Nachkommastelle nicht.*
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
- [x] **Die fünf Behauptungen der Stilanalyse gemessen** — erledigt 2026-08-18
      (`auf-20260818-14`, 74 Werke). **Eine trägt, zwei tragen nicht, eine ist in ihrer
      Schärfe falsch, eine ist nicht entscheidbar.**
      *Entsättigt* — nein: 0.193 gegen 0.197 bei gewöhnlichen Fotos. Aber die **Streuung**
      unterscheidet sich (0.072 gegen 0.162): Die Referenzen sind **einheitlicher**, nicht
      blasser. *Kaum ausgefressen* — nein: 7.5 % über 95 % Helligkeit, **sechsfach** mehr
      als gewöhnliche Fotos; zugelaufen sind sie dagegen kaum. *Nie 16:9* — zu scharf:
      41 von 74 sind hochformatig oder quadratisch, aber **30 leicht quer**; richtig ist
      allein, dass 16:9 die Ausnahme ist (3 von 74). *Heller Himmel* — **trägt**: 0.782
      gegen 0.574 im übrigen Bild. *Feines Korn* — nicht entscheidbar.
      Alle vier Befunde sind in `prompts.py` eingearbeitet, mit den Zahlen am Baustein.
      **Und die HomeStation hat eine Falle abgefangen**, in die ich gelaufen wäre: Die
      Vorlagen sind Bildschirmfotos, alle 2560×1440. Wer die Dateimasse misst, misst den
      Bildschirm und nicht die Arbeit.
- [ ] **(entfällt mit dem Stil-Entscheid vom 21.08.) Wie viele der 74 sind wirklich Architekturvisualisierungen?** Die HomeStation hat
      **strukturell** klassifiziert (heller Grund + eingebettetes Werk) und ausdrücklich
      gesagt, dass sie nur zwei Bilder wirklich angesehen hat. Wer die Zahl braucht, muss
      sie sehen — das ist ein eigener Durchgang, keine Nebenbemerkung.
- [ ] **(entfällt mit dem Stil-Entscheid vom 21.08. — der feste Stil braucht keins) Ein Referenzset, das uns gehört** — die andere Hälfte des Hausstils. Der Prompt
      sagt, wie man es macht; `stil_qa` prüft gegen ein Referenzset, ob es gelungen ist.
      Fremde Bilder können das nicht sein: Eine Einbettung ist eine Ableitung des Bildes.
      Es braucht eigene Renders oder eigene Arbeiten des Owners. **Erst danach ist der
      Hausstil prüfbar und nicht nur beschrieben.**
- [x] **ENTSCHIEDEN 21.08. (Owner): FESTER STIL, fest formuliert.** Der Hausstil steht
      als Prompt und als gemessener Belichtungsrahmen im Repo, **ohne Referenzset**. Was
      damit erledigt ist und was folgt:

      * Die Stil-QA misst gegen den **Belichtungsrahmen** (`belichtung.py`,
        `HAUSSTIL_RAHMEN`, Mittel ± 2σ aus `auf-20260818-14`) und nicht gegen
        Bildähnlichkeit. Das ist der Teil, der schon gemessen ist.
      * Damit entfällt der Grund, aus dem die Stil-QA im Abholer bewusst nicht lief: Sie
        war an ein Referenzset gebunden, das es nicht gibt. **Neu zu bauen:** die
        Stil-Prüfung im Abholer gegen den Rahmen statt gegen Einbettungen.
      * Die 74 gefundenen fremden Referenzen werden damit **nicht gebraucht** — und die
        lizenzrechtlich ungeklärte Frage nach ihnen erledigt sich, statt beantwortet zu
        werden. Das ist der angenehmste Weg, eine Rechtsfrage loszuwerden.
      * **Was der Entscheid NICHT löst:** Ein fest formulierter Stil ist beschrieben und
        nicht geprüft. Ob ein Prompt an einem Backbone wirklich landet, bleibt eine
        Messung am Gerät — und `stil_qa` mit SigLIP 2 behält seinen Wert für den
        Vergleich *unserer eigenen* Bilder untereinander.
- [ ] **(hinfällig) Owner-Entscheid: gelernter Hausstil oder fester Stil?** Der Owner hat beide Wege
      genannt — Referenzen in KosmoData hochladen („so sollen meine Renderings aussehen")
      oder ein festes Preset. **Es ist dieselbe Mechanik:** Ein Preset ist ein
      mitgeliefertes Referenzset. Der gelernte Weg braucht nur einen Ort, an dem die
      Bilder des Nutzers liegen, und die Messung ihres Bodens (`stil_qa.BODEN_MESSUNGEN`)
      — ein hochgeladenes Set hat einen anderen Boden als unser eigenes.
- [x] **Die Szenennaht gebaut** — erledigt 2026-08-19, `kosmo_szene.py`, 48 Tests.
      `kosmovis.render-scene/v1` und `render-result/v2`, **wörtlich aus den Schemadateien
      gelesen** statt aus einem Bericht abgeschrieben — ein erratener Feldname erzeugt in
      diesem Ökosystem keine Fehlermeldung, sondern eine tote Kante.
      **Drei Stellen, an denen wir dem fremden Vertrag bewusst nicht folgen:** ihre
      Stil-Schwelle 0.30 mit `dinov3` (gegen 0.30 besteht jedes beliebige Bildpaar,
      `auf-11`), ihre Backbone-Liste (kennt unser Vorgabemodell nicht — gemeldet, nicht
      geraten), und `faithful` als einzelner Regler (auf `controlnet_staerke` abgebildet,
      mit der Angabe, was dabei unter den Tisch fällt).
      *Von einem Test gefangen:* Der erste Entwurf behauptete im Docstring, zwei der vier
      fremden Einträge seien FLUX-Ableger. Falsch — `flux2-klein` ist Apache-2.0.
- [x] **Die Brückennaht gebaut** — erledigt 2026-08-19, `bruecke.py`, 28 Tests. Liest und
      schreibt das Auftragsverzeichnis der Designzentrale (`model.glb`,
      `render-scene.json`, `job.json` → `render-result.json`).
      **Der Befund, der aufhielt:** Ihr `create_job` prägt den Freigabe-Token selbst
      (`secrets.token_hex`). Jeder Auftrag kommt mit einer Freigabe an, **die kein Mensch
      erteilt hat** — und hebelt unseren Freeze-Schutz aus, ohne dass irgendwo etwas rot
      wird. `fremde_freigabe_gilt` ist darum als ausdrücklicher Schalter gebaut, Vorgabe
      `False`. **Owner-Entscheid, siehe unten.**
- [x] **ENTSCHIEDEN 21.08. (Owner): NEIN, der Token gilt nicht.** `--fremde-freigabe`
      bleibt ausgeschaltet. Aufträge der fremden Oberfläche bleiben liegen, mit
      Begründung im Bericht; wer rechnen will, gibt den Schalter bewusst mit.

      Die Begründung, die damit bestätigt ist: Die Brücke prägt ihren `approval_token`
      mit `secrets.token_hex` **selbst**. Er sieht aus wie unserer und bedeutet etwas
      anderes — nämlich „in der Oberfläche wurde auf Rendern geklickt", nicht „ein Mensch
      hat die Kosten freigegeben". Der Schalter bleibt als Schalter bestehen; die
      Voreinstellung ist jetzt ein Entscheid und keine Vorsichtsmassnahme mehr.
- [x] **Übergabeblatt an die Vis-Oberfläche** — erledigt 2026-08-19,
      `docs/UEBERGABE_VIS_2026-08-19.md`. **Eine Kehrtwende, keine weitere
      Bestandsaufnahme:** Nachdem der Owner mitteilte, dass der Cloud-Worker gerade an
      KosmoOrbit baut, ist klar, warum `Design/Vis` in keinem unserer Klone steht — die
      Oberfläche *entsteht gerade*. Einen bewegten Bestand rückwärts zu lesen ist
      verschwendete Arbeit, und je genauer man ihn nachbaut, desto sicherer baut man am
      selben Tag daneben. **Die wirtschaftliche Antwort ist nicht Nachbauen, sondern
      Zusagen** — Verträge halten, während sich Oberflächen ändern.
      Das Blatt beantwortet drei Fragen: was wir bekommen, was wir zurückgeben, und
      **woran man erkennt, dass eine Verbindung wirklich trägt**. Es nennt fünf offene
      Fragen an die Gegenseite (`fov`-Achse, Stil-Schwelle, wo ein Mensch bestätigt,
      welcher Weg zuerst, ob der Ausführen-Knopf prüfen soll).
- [ ] **Antwort auf das Übergabeblatt** — solange sie fehlt, wird **nichts gebaut, was an
      einer bestimmten Oberfläche hängt**. Verträge, QA und Bildkette tragen in jedem der
      drei Fälle und laufen weiter.
      *Stand 2026-08-20:* Das Blatt trägt **zwölf** Fragen und ein viertes Kapitel mit
      drei Befunden auf ihrer Seite — kein Abholer, ein Worker ohne Leerlauf-Tor, und eine
      Kamerahöhe mit zwei Bezugspunkten. Die dringendste Frage ist nicht mehr, welcher Weg
      zur Demo führt, sondern **ob sie unseren Abholer nehmen**.
- [x] **Der Ausführen-Knopf** — beantwortet 2026-08-19 durch einen Volldurchgang als
      Nutzer, und **zweimal berichtigt**. Er tut sehr wohl etwas, und er sagt sehr genau,
      was fehlt — die Meldung war von der Node-Palette *verdeckt*. Eine zweite Meldung
      trennt sogar sauber Erreichbarkeit von Berechtigung (`/health` 200, geschützte Route
      401 — gegengeprüft, sie stimmt aufs Wort).
      **Was bleibt, ist der Befund in schärferer Form:** Der Zustand meldet `bereit`
      **auch bei unverdrahteten Knoten**. Das ist wörtlich der Befund, mit dem dieses
      Projekt angefangen hat, nur an anderer Stelle — und genau dagegen sind
      `kette.pruefe_kette` und `graph.pruefe_bedarf` gebaut, mit drei Zuständen statt
      zwei: *ungeprüft* ist nicht *in Ordnung*.
- [x] **Die Naht ist keine Absicht mehr — sie liegt.** 2026-08-19: Nach Verdrahtung und
      Bridge-Token liegt ein echter Auftrag in `/tmp/kosmo-jobs/vis-1787123048-098c6e/` —
      `job.json` (queued, `approval_token`, `idle_window_only`), `model.glb` mit 110 KB
      echter Geometrie, `render-scene.json` nach `kosmovis.render-scene/v1` mit drei aus
      dem Modell gerechneten Kameras. **Wort für Wort das Verzeichnis, das `bruecke.py`
      liest** — am selben Tag gebaut, ohne dass eines vom anderen wusste. Ordnername,
      Kennung und Schema **nachgeprüft**, nicht angenommen.
- [x] **Warum wird der Auftrag nicht abgeholt? — ES LÄUFT KEIN ABHOLER.**
      `auf-20260819-17`: kein `blender_worker`, kein ComfyUI-Worker, kein systemd-Dienst;
      nur die Bridge selbst auf 8600. **Keine Schranke war im Weg** — 0 % Auslastung gegen
      eine Schwelle von 10 %. Der Auftrag lag seit 09:04 unberührt.
      **Damit ist die Lücke, in die unsere Lane gehört, nicht mehr argumentiert, sondern
      belegt** — und `abholer.py` vom selben Tag ist genau das fehlende Stück.
- [ ] **Der vorhandene `blender_worker` hat GAR KEIN Leerlauf-Tor** — Nebenbefund
      derselben Messung, und der unangenehmste. Wer ihn startet, umgeht `idle_window_only`
      **unbemerkt**: Der Auftrag trägt die Auflage, und niemand liest sie. Genau dagegen
      steht `abholer._karte_frei` fail-closed. **Das gehört der Gegenseite gemeldet**, es
      ist ihre Komponente und ihre Grafikkarte.
- [ ] **Die Kamerahöhe ist zweimal fest verdrahtet — mit zwei verschiedenen Bezugspunkten**
      (Hüllbox-Minimum gegen Geschosshöhe), beide auf 1600 mm. Wir und das Pflichtenheft
      rechnen mit 1700 mm **über Terrain**. Zwei Zahlen und zwei Bezugspunkte für dieselbe
      Grösse sind ein stiller Massstabsfehler — genau die Fehlerart, die uns bei der
      Augenhöhe schon drei Fehler gekostet hat, die kein Test fand. Steht als Frage 7 im
      Übergabeblatt.
- [x] **Der Abholer gebaut** — 2026-08-20, `abholer.py`, 28 Tests. **Kein neuer Baustein,
      sondern der Ablauf zwischen den vorhandenen:** `bruecke.py` hatte seit dem 19.08.
      alle Teile — `offene_auftraege`, `lies_auftrag`, `setze_status`,
      `schreibe_ergebnis` —, nur fasste sie niemand in der richtigen Reihenfolge an. Das
      war die Lücke, die die HomeStation empirisch gezeigt hat.
      **Das Rendern steckt ausdrücklich nicht darin**, sondern wird als `verarbeite`
      hereingereicht. Grund ist nicht Bequemlichkeit, sondern Prüfbarkeit: Die
      interessanten Fehler dieses Moduls sind Reihenfolge- und Entscheidungsfehler, und
      ein Abholer, der nur mit 20 GB Gewichten prüfbar wäre, wäre gar nicht geprüft.
      Fünf Entscheidungen fallen dort: keine Rechnung ohne menschliche Freigabe; bei
      `idle_window_only` **ohne Auskunft nicht rechnen** (fail-closed — das Loch hat
      Sitzung 07 viermal gefunden); Ergebnis vor Laufzettel; ein Fehler ist ein Ergebnis
      und keine Stille; und **Waisen werden gemeldet, nicht wiederbelebt**.
      Kein Dauerlauf, kein Schlaf: Wie oft nachgesehen wird, ist eine Betriebsfrage und
      gehört nicht in eine Bibliothek.
- [x] **Den Abholer an die echte Kette gehängt** — 2026-08-20, `abholer.verarbeiter`.
      **Je Kamera ein eigener Durchgang:** Multipass → Render → Geometrie-QA. Der echte
      Auftrag vom 19.08. mit seinen drei Kameras ergibt drei Bilder und drei Urteile.
      Der Grund für „je Kamera ein eigener Multipass": Die Tiefenkarte gilt nur für **den
      einen** Blickwinkel, aus dem sie entstand. Ein Bild gegen die Tiefenkarte einer
      anderen Kamera zu messen ergäbe eine Zahl, und die Zahl wäre Unsinn.
      Berichtet wird das Urteil der **schlechtesten** Kamera, kein Mittelwert — der liesse
      ein durchgefallenes Bild hinter zwei bestandenen verschwinden. Ein *ungemessenes*
      Urteil gilt dabei als das schlechteste von allen.
      Alle vier Schwergewichte (Multipass, Render, Soll-Karte, QA) sind injizierbar; ohne
      das wäre der Weg nur mit Blender, GPU und 20 GB Gewichten prüfbar, also faktisch
      gar nicht.
- [ ] **Welche Hochachse hat die `model.glb` der Brücke?** `render-scene/v1` hat **kein
      Feld dafür**. Wir nehmen `Y_UP` an (glTF-Spezifikation) und schreiben die Annahme
      als `ANGENOMMENE_HOCHACHSE` in den Code statt in einen Kopf. **Genau hier liegt der
      Phase-0-Befund**: Zwei Erzeuger des Ökosystems liefern beide ein `glb_path`, mit
      unterschiedlicher Orientierung — und eine verdrehte Hochachse fällt an einem
      einzelnen Bild nicht auf. Frage steht im Übergabeblatt.
- [x] **Die Stil-QA im Abholer läuft wieder — 22.08., mit dem Rahmen statt mit
      Einbettungen.** Der Owner-Entscheid vom 21.08. (fester Hausstil, kein Referenzset)
      hat die Blockade aufgelöst: Die Frage lautet nicht mehr *„ähnelt das unseren
      Referenzen"*, sondern *„liegt das im gemessenen Belichtungsrahmen"* — und die können
      wir beantworten. Es zählt die schwächste Kamera; eine einzige ungemessene macht das
      ganze Urteil ungemessen.

      **Die heikle Stelle war die Naht, nicht die Messung.** Ihr `style_score` meint eine
      Bildähnlichkeit; eine Belichtungsprüfung hat keinen natürlichen Skalar. Wir senden
      darum `style_score: null`, `threshold: null` und in `method` das Verfahren
      (`belichtungsrahmen/<stil>`). Eine Zahl zu erfinden — auch eine ehrlich gemeinte wie
      1.0 für „bestanden" — sähe drüben wie eine gemessene Ähnlichkeit aus. `method` und
      nicht `hinweise`, weil die Hinweise `nur_vertragsfelder` nicht überstehen.

      **Offen und an sie gestellt (Übergabeblatt Frage 13):** Nimmt ihr Schema `null` für
      `style_score` an? Ihre Schemadatei liegt uns nicht vor. Geht es nicht durch, ist das
      dort zu ändern und nicht hier durch eine erfundene Zahl.
- [x] **Die Belichtungsprüfung im Abholer** — 2026-08-20, `verarbeiter(stil=…)`, je Kamera.
      Sie **hält nichts auf**: Ein Bild, das die Belichtung reisst, ist ein Befund und
      kein Fehler — die Geometrie entscheidet über `passed`, die Belichtung erklärt.
      Ohne Stil wird gar nicht gemessen, und ein Stil ohne Rahmen bekommt **keinen
      untergeschoben**: *nicht verlangt*, *nicht gemessen* und *in Ordnung* sind drei
      verschiedene Dinge, und alle drei stehen unterscheidbar im Ergebnis.
- [x] **Die Vakuumprobe hat über-gemeldet — behoben mit einer Nullprobe.** Am selben Tag
      sprang sie von 6 auf **19 Treffer**: dreizehn Lexikon-Tests, die nur scheiterten,
      weil `docs/` nicht in die Arbeitskopie kam. Die erste Fassung zählte jeden roten
      Test mit, sobald irgendwo das Wort `VAKUUM` im Protokoll stand.
      Sie läuft jetzt **zweimal** — einmal unverändert, einmal umgeschrieben — und zählt
      nur, was *erst durch das Umschreiben* rot wird. *Ein Werkzeug, das schwache Tests
      sucht und selbst über-meldet, verliert seinen Zweck beim ersten Fehlalarm.*
- [ ] **Drei Zahlen laufen auseinander** (aus demselben Durchgang): Ihre Auto-Kamera setzt
      die Augenhöhe auf **1.30 m** (Eingang) und **1.60 m** (Innenraum); wir und das
      Pflichtenheft rechnen mit **1.70 m über Terrain**. `engine: cycles` und
      `style: lineart` stehen im Laufzettel, den wir durchreichen und **nicht lesen** — ob
      sie verbindlich sind, ist offen. Und ihre `Übersicht` steht auf 38 m, während unsere
      zwölf Standpunkte auf Augenhöhe stehen.
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
