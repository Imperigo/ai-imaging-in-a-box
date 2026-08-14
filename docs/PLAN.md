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

- [ ] `KosmoDraw` lesen: Ausgabefelder von `kosmodraw_export_ifc`
- [ ] `kosmo-backend` lesen: wie ein MCP-Werkzeug bei Kosmo registriert wird
- [ ] Ergebnis als Feldnamen-Tabelle in `docs/EINBINDUNG_KOSMOORBIT_2026-08-14.md` nachtragen

**Fertig, wenn** die Namen belegt sind statt vermutet.

---

## Phase 1 · Das Skelett

**Aufwand:** mittel · **Zweck:** die Prozessgrenze beweisen, bevor etwas darauf steht

Der dünnste Pfad, der jede der vier Regeln einmal berührt. Fast ohne Funktionalität —
absichtlich. Bricht hier eine Annahme, ist es bei 500 Zeilen zu erfahren, nicht bei 5 000.

- [ ] **Synthetische Testgeometrie** — Skript, das eine kleine IFC im Repo erzeugt (Regel 3;
      macht alles Weitere überhaupt prüfbar)
- [ ] **IFC → glb** als Subprozess in eigenem `.venv-ifc`
      → *Praxistest des CGAL-Befunds: trägt die Grenze gegen GPL-Code?*
- [ ] **glb → Blender headless → Tiefenkarte** über `blender --background`
      → *Praxistest von Regel 2; zugleich die technisch heikelste Stelle (Compositor,
      EXR, Normalisierung auf nah = hell)*
- [ ] **Vertrag `render-scene.json`** mit JSON-Schema
- [ ] **Tests ab der ersten Zeile** (pytest)
- [ ] **`NOTICE`** — Blender GPL, IfcOpenShell LGPL, CGAL GPL

**Enthält bewusst nicht:** keine KI, kein Graph-Kern, kein MCP, keine QA.

**Fertig, wenn** aus Python heraus, ohne Oberfläche und ohne `import bpy`, aus einer
synthetischen IFC eine korrekte Tiefenkarte entsteht — und ein Test das festhält.

**Prüffragen der Phase:**
- Trägt die Prozessgrenze in der Praxis, nicht nur auf dem Papier?
- Ist der Tiefen-Pass geometrisch korrekt (nah = hell, Meter plausibel)?
- Bleibt das Produkt-venv frei von `bpy` und `ifcopenshell`?

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
