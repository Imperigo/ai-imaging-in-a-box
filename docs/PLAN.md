# Vorgehensplan

**Angelegt:** 2026-08-14 nach der ersten Sitzung · **Stand:** Phase 0 offen, nichts gebaut

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

- [x] **Synthetische Testgeometrie** — erledigt: 8x5x3 m, deterministisch, stdlib-only — Skript, das eine kleine IFC im Repo erzeugt (Regel 3;
      macht alles Weitere überhaupt prüfbar)
- [x] **IFC → glb** als Subprozess — erledigt und ausgeführt: 5 Bauteile, 60 Dreiecke in eigenem `.venv-ifc`
      → *Praxistest des CGAL-Befunds: trägt die Grenze gegen GPL-Code?*
- [x] **glb → Blender headless → Tiefenkarte** — erledigt und ausgeführt: EXR mit echten Meterwerten (27.3–39.5 m) über `blender --background`
      → *Praxistest von Regel 2; zugleich die technisch heikelste Stelle (Compositor,
      EXR, Normalisierung auf nah = hell)*
- [x] **Vertrag `render-scene.json`** — erledigt in `contracts.py` (up_axis Pflichtfeld) mit JSON-Schema
- [x] **Tests ab der ersten Zeile** — erledigt: 76 grün
- [x] **`NOTICE`** — erledigt: Blender GPL, IfcOpenShell LGPL, CGAL GPL — Blender GPL, IfcOpenShell LGPL, CGAL GPL

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

- [ ] **Graph-Kern**: typisierter DAG, topologische Sortierung, Artefakt-Cache mit
      Content-Hashing, serialisierbares Format. Klein halten — die Knoten rufen
      `diffusers`, sie bauen ComfyUIs Knoten-Zoo nicht nach.
- [ ] **Auftragsverwaltung**: Auftrag/Freigabe/Status (`awaiting_approval`), Muster aus
      KosmoVis `render_job_store.py`
- [ ] **MCP-Schicht**: `…_enqueue_render` + `…_query_render`, je mit `inputSchema` **und**
      `outputSchema`, Ergebnis in `structuredContent`, Feldnamen aus Phase 0
- [ ] Eingabe-Schemas **nicht** `additionalProperties: false`

**Fertig, wenn** KosmoOrbit unsere Werkzeuge sieht, verdrahten kann und
`pipelineReadiness` keine toten Kanten meldet.

---

## Phase 3 · Bildkette und QA

**Aufwand:** gross · **Setzt voraus:** Phase 2

- [ ] Multipass in Blender vollständig (Beauty, Material-ID, Depth)
- [ ] Backbone-Adapter — Modelltausch über die Depth-ControlNet-Naht als Vertrag
- [ ] Erster echter Render: Qwen-Image-Edit-2511 (Apache-2.0) mit ControlNet-Depth
- [ ] **Geometrie-Treue-QA** — der Forschungskern
- [ ] Stil-QA als zweites Gate
- [ ] Doppel-Gate: bestanden nur, wenn beide bestehen

**Fertig, wenn** ein Render gegen die Eingangsgeometrie messbar bewertet wird und eine
Halluzination nachweislich durchfällt.

---

## Phase 4 · Wissenschaftlicher Ausbau

- [ ] **Systematische Schwellenstudie** — die Schwellen 0.65 / 0.30 stammen aus wenigen
      Fällen. Eine ordentliche Kalibrierung ist das, was die Arbeit über einen
      Werkstattbericht hinaushebt.
- [ ] Connectors: ArchiCAD über IFC4, Rhino über glTF
- [ ] LoRA-Stiltraining über kohya oder ai-toolkit als Subprozess

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

- **Binärabhängigkeiten ungeprüft** — `torch`, `opencv` und alles weitere mit grossem
  Binäranteil kann wie `ifcopenshell` fremde Lizenzen statisch mitbringen. Die
  Wheel-Lizenzangabe sagt darüber nichts.
- **Rund ein Dutzend Lizenzen nur aus Sekundärquellen** — Liste in
  `LAGEBEURTEILUNG_2026-08-14.md`, Kapitel 9. Vor einer Auslieferung gegen die
  LICENSE-Datei zu prüfen.
- **Ökosystem grösstenteils ungelesen** — `KosmoPublish`, `KosmoDesign`, `KosmoPrepare`,
  `ArchitekturKosmos-Codex`, `architekturkosmos-control-hub`, `Architektur-Cosmos`.
- **KosmoVis' Reife nicht nachgeprüft** — alle Angaben stammen aus dessen eigener
  Dokumentation, die sich selbst bei ~60–65 % einordnet und einräumt, dass noch kein
  echtes Projekt durchgerendert war.
