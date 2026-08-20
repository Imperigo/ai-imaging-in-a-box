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
      `kameras.py`, das 9,46° kippt.

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
- [ ] **Der Verdeckungstest fehlt weiterhin, und für innen ist er keine Kür.** Ob zwischen
      Kamera und Ziel ein Möbel, eine Stütze oder eine Brüstung steht, weiss nur die
      Szene. Was `raumkamera.py` prüft, ist die Lage im **Raumumriss** — notwendig, nicht
      hinreichend, und das steht in jedem Befund.
- [ ] **Die Zielwand wird nach LÄNGE gewählt, und das ist eine schwache Setzung.** Die
      Praxis wählt die Wand mit dem Motiv. Ein Kamin oder eine Küchenzeile ist ein Motiv
      und hat keine Öffnung; die längste Wand ist oft, aber nicht immer, die richtige. Der
      Hinweis steht bei jedem Standpunkt.
- [ ] **`AUTO_RICHTUNGEN = ("sSE",)` ist eine einzige Richtung — HABS verlangt drei.**
      Umgebungsansicht, Frontalansicht, und zwei Über-Eck-Ansichten auf **gegenüberliegenden**
      Diagonalen. Unsere Richtungstabelle kann das bereits abbilden; es ist eine
      Betriebsentscheidung über Renderzeit, keine technische.
- [ ] **Arbeitsbrennweite: 24–25 mm statt unserer 28.** Der HABS-Objektivsatz
      (65/90/150/210 mm auf 4×5 = 18/25/42/59 mm Kleinbild) und die heutige
      Ratgeberliteratur treffen sich **unabhängig** bei 24–25 mm. Kein grosser Unterschied,
      aber einer mit zwei Belegen gegen unsere eine Herleitung aus dem Bestand.

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
