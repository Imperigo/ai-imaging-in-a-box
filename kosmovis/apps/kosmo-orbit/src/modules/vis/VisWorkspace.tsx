import { useEffect, useRef } from 'react';
import { KButton, KFehlerzone, Messrahmen } from '@kosmo/ui';
import type { VisGraph } from '@kosmo/kernel';
import { useProject } from '../../state/project-store';
import { NodeCanvas } from './NodeCanvas';
import { sendeGraphRenderAuftrag } from './vis-jobs';
import { VisReportDossier } from './VisReportDossier';
import { useVisRuntime, waehleGezeigtenGraphen } from './vis-runtime';
import { kameraVorschlagenAktion } from './vis-graph-aktionen';
// PC1 (`docs/V084-SPEZ.md` §5 W2, C-15) — der Vis-Island-Katalog (eigener
// Namensraum, s. `island/inhalte/registry.ts`-Kopfkommentar) + die
// Registrierung seiner Stufe-2/3-Inhalte als Import-Seiteneffekt (Muster
// `design/island/IslandShell.tsx`s Kopfimporte).
import { VIS_INSELN, visInhaltsRegistry } from './island';
// PD2/E1 (`docs/V084-SPEZ.md` §5 W2) — NUR IMPORTIEREN, design/island/**
// bleibt fremder Dateibesitz (Sanktion 2 gilt spiegelbildlich: PC1 fasst
// keine design-Datei an). `IslandBuehne`/`KosmoOrb` sind die generische
// PC0-Bühne bzw. das E2-Orb-Vorbild — beide bereits stationsagnostisch
// gebaut (`IslandBuehne` nimmt `inseln`+`registry`, `KosmoOrb` kennt gar
// keine Station).
import { IslandBuehne, type IslandBuehneHandle } from '../design/island/IslandShell';
import { KosmoOrb } from '../design/island/KosmoOrb';
import type { IslandWerkzeug } from '../design/island/island-katalog';
import './vis-visual.css';

/**
 * KosmoVis — Render-Jobs an die HomeStation (Toolkit 2 der Vision):
 * Modell → GLB → Bridge (/jobs, render-scene/v1) → Job-Store → Scheduler
 * rendert im GPU-Leerlauf → Ergebnis mit Doppel-QA-Verdikt zurück.
 *
 * **v0.9.25 P-M (Owner-Ausnahme zu K15, 10.08.2026, `docs/V0925-SPEZ.md`
 * §3 P-M): die Island-UI ist die EINZIGE Vis-Oberfläche.** Der frühere
 * Manuell-Codepfad — VisTabs-Werkzeugzeile (Graph/Einfach/Ansichten-Tabs),
 * `EinfachAnsicht` (lineare Bridge-Job-Liste), `VisOnboarding` und die
 * `DockFlaeche station="vis"` in `NodeCanvas.tsx` — ist ersatzlos entfernt;
 * die 0.8.11-Planung (`docs/V0811-SPEZ.md` §E4) hatte die Löschung bereits
 * inventarisiert, K15 hat sie gestoppt, der Owner hat K15 am 10.08.2026
 * aufgehoben. Jede Funktion mit Bestandswert lebt als Insel weiter
 * (`island/inhalte/`): Graph bauen (GRAPH-Insel, `nodeHinzufuegen()`/
 * `neuerGraphErstellen()` in `vis-graph-aktionen.ts`), Ansichten
 * (`inhalte/ansichten.tsx`), Legende (`inhalte/legende.tsx` + Overlay in
 * `NodeCanvas.tsx`), Render/Plakat/Report (AUSTAUSCH-Insel). Das frühere
 * `visOberflaeche`-Feld ist aus `state/ui-zustand.ts` entfallen.
 */
export interface VisWorkspaceProps {
  /**
   * PC1 (`docs/V084-SPEZ.md` §5 W2) — Muster `DesignWorkspace.tsx`s gleich-
   * namiges Prop: der Kosmo-Orb-Zugang im Island-Modus (`island/KosmoOrb.tsx`,
   * NUR importiert). Optional — nur `App.tsx` kennt den Weg zum Kosmo-Panel.
   */
  onKosmoOeffnen?: () => void;
}

// D-5 (docs/design/UNTERAUFTRAG-D5-BESTAETIGEN.md §4.4): Fehlerzone an der
// Workspace-Wurzel — dünne Hülle um `VisWorkspaceInner`, additiv zur
// bestehenden Fehlerzone, die `App.tsx` schon um den Screen legt.
export function VisWorkspace(props: VisWorkspaceProps = {}) {
  return (
    <KFehlerzone bereich="KosmoVis">
      <VisWorkspaceInner {...props} />
    </KFehlerzone>
  );
}

function VisWorkspaceInner({ onKosmoOeffnen }: VisWorkspaceProps = {}) {
  const revision = useProject((s) => s.revision);
  void revision;
  const doc = useProject.getState().doc;
  const graphen = doc.byKind<VisGraph>('visgraph');
  // Der aktive Graph kommt aus `vis-runtime.ts` (`aktiverGraphId`, von
  // `NodeCanvas.tsx` gepflegt) — Laufzeit ≠ Modell, kein Doc-Feld.
  const aktiverGraphIdInsel = useVisRuntime((s) => s.aktiverGraphId);
  // P-BUEHNE (14.08.2026) — Formel jetzt in `vis-runtime.ts` (testbar ohne
  // isolierten Component-Mount, s. dortiger Kopfkommentar), Verhalten
  // mechanisch unverändert.
  const islandGraphId = waehleGezeigtenGraphen(graphen, aktiverGraphIdInsel);
  const islandReportOffen = useVisRuntime((s) => s.reportOffen);
  const setIslandReportOffen = useVisRuntime((s) => s.setReportOffen);

  /**
   * v0.8.4 PC2 (`docs/V084-SPEZ.md` E6/C-18) — Executor für den `vis.render`-
   * Kernel-Command: beobachtet `doc.settings.visRenderAuftrag` (SettingsPatch,
   * `commands/vis.ts`) und stösst `sendeGraphRenderAuftrag()` an, sobald ein
   * FRISCHER Auftrag erscheint. «frisch» heisst: eine neue Objekt-Referenz
   * gegenüber dem zuletzt gesehenen Auftrag — jeder `vis.render`-Lauf liefert
   * ein neues Literal, auch bei identischen Parametern (bewusst, s.
   * `VisRenderWunsch`-Kommentar in `model/doc.ts`: ein Kernel-Command darf
   * keinen Zeitstempel in die Nutzlast schreiben). Der Ref-Vergleich startet
   * beim ERSTEN Mount mit dem AKTUELLEN Wert (nicht `null`) — ein aus einem
   * gespeicherten Projekt geladener, bereits abgeschlossener Auftrag löst
   * beim Öffnen darum KEINEN Render erneut aus (ehrliche Grenze: ein
   * Auftrag, der zwischen zwei Sitzungen nie verarbeitet wurde — z.B.
   * Tab-Schliessen mitten im Senden —, bleibt unverarbeitet stehen, bis der
   * nächste `vis.render`-Lauf ihn überschreibt; reine Laufzeit-Entscheidung,
   * kein Kernel-Bezug).
   *
   * Damit ist `window.__kosmo.run('vis.render', …)` — und über
   * `commandTools()` jeder Kosmo-Tool-Call — der GENAU GLEICHE Auslöser wie
   * der bestehende «Ausführen»-Knopf am Node (`NodeCanvas.tsx`, UNVERÄNDERT):
   * beide Wege enden bei `sendeGraphRenderAuftrag()`, der Node zeigt Status/
   * Bild aus `vis-runtime.ts`s `laeufe` wie bisher — kein NodeCanvas-Edit
   * nötig (DATEIKREIS PC2).
   */
  const letzterRenderAuftrag = useRef(doc.settings.visRenderAuftrag ?? null);
  useEffect(() => {
    const auftrag = doc.settings.visRenderAuftrag ?? null;
    if (auftrag === letzterRenderAuftrag.current) return;
    letzterRenderAuftrag.current = auftrag;
    if (!auftrag) return;
    sendeGraphRenderAuftrag(
      auftrag.graphId,
      auftrag.nodeId,
      auftrag.stimmungPreset ? { preset: auftrag.stimmungPreset } : undefined,
      {
        kameraWahl: auftrag.kameraWahl,
        ...(auftrag.backbone !== undefined ? { backbone: auftrag.backbone } : {}),
        ...(auftrag.aufloesung !== undefined ? { aufloesung: auftrag.aufloesung } : {}),
      },
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [revision]);

  /**
   * PD2-Muster (`DesignWorkspace.tsx`s `aktiviereIslandWerkzeug()`): Aktion
   * für JEDE Erst-Aktivierung eines Insel-Werkzeugs. `hatPopup:true`-
   * Werkzeuge (Palette/Ausrichten/Verbinden/Zoom/Stimmung/Render
   * senden/Aufs Plakat) brauchen hier nichts — ihre echte Aktion lebt in der
   * Registry (`island/inhalte/*.tsx`, liest globale Stores direkt). Die
   * vier `hatPopup:false`-Sofort-Aktionen (Raster/Routing/Kamera vorschlagen/
   * Report) schalten hier real — IslandShell zeigt danach selbst den Toast.
   */
  const aktiviereVisIslandWerkzeug = (w: IslandWerkzeug): void => {
    switch (w.id) {
      case 'raster':
        useVisRuntime.getState().toggleCanvasSnap();
        return;
      case 'routing':
        useVisRuntime.getState().toggleCanvasRouting();
        return;
      case 'kamera-vorschlagen':
        kameraVorschlagenAktion(islandGraphId || undefined);
        return;
      case 'report':
        setIslandReportOffen(true);
        return;
      default:
        return;
    }
  };

/**
 * B144 (12.09.2026, Sichtlauf-Befund 4) — der Leerzustand nennt eine Insel,
 * die nirgends beschriftet ist. **Gemessen:** in KosmoVis, KosmoPublish und
 * KosmoSpez kommt das Wort, auf das der Satz zeigt (GRAPH / BLATT / STUDIE),
 * ausser im Satz selbst **NULL mal sichtbar** auf dem Bildschirm vor — die
 * Insel-Pillen tragen ihren Namen nur als `aria-label`, sichtbar ist ein
 * Symbol oder zwei Buchstaben. Wer liest «die GRAPH-Insel (links) legt einen
 * an», sieht links kleine, unbeschriftete Kreise.
 *
 * Der Knopf hier traegt denselben Namen und oeffnet dieselbe Insel — der
 * Verweis wird vom Text zum Weg. Er legt NICHTS an: er oeffnet das Werkzeug,
 * dessen Stufe 2 den Anlege-Knopf traegt. Nichts entsteht hinter dem Ruecken
 * des Nutzers, und es gibt keinen zweiten Anlege-Weg mit eigenen Vorgaben
 * (Format, Datum), der irgendwann von der Insel abweicht.
 */
  const buehneRef = useRef<IslandBuehneHandle>(null);

  return (
    <div className="vis-workspace-fuellen" data-testid="vis-island-fuellen">
      <div className="vis-workspace-buehne">
        {islandGraphId ? (
          <NodeCanvas key={islandGraphId} graphId={islandGraphId} />
        ) : (
          <div className="vis-workspace-buehne-zentriert">
            <Messrahmen height={200} caption="Noch kein Render-Graph" />
            {/* Zielgroessen-Gate (Befund 17.09.2026): die Groesse stand auf
                der 44px-Stufe (touch-Groesse), steht jetzt auf der
                32px-Stufe (sm-Groesse), weil B89 (02.09.2026) ausserhalb
                von island/** 32px verlangt — diese Datei liegt nicht unter
                island/**. Eine Ausnahme fuer Leerzustaende waere ein
                Owner-Entscheid ueber B89 selbst, kein Handgriff.
                (Absichtlich OHNE die wortgetreue size=…-Schreibweise im
                Kommentar — die Wache zaehlt Kommentartext mit, s.
                tools/zielgroessen-gate.mjs Kopfkommentar.) */}
            <KButton
              size="sm"
              tone="quiet"
              data-testid="vis-leer-graph-insel-oeffnen"
              onClick={() => buehneRef.current?.oeffnePopupFuerWerkzeug('palette')}
            >
              GRAPH-Insel öffnen
            </KButton>
          </div>
        )}
      </div>
      <IslandBuehne ref={buehneRef} inseln={VIS_INSELN} registry={visInhaltsRegistry} onWerkzeugAktion={aktiviereVisIslandWerkzeug} />
      <KosmoOrb {...(onKosmoOeffnen ? { onKosmoOeffnen } : {})} />
      {islandReportOffen && <VisReportDossier onClose={() => setIslandReportOffen(false)} />}
    </div>
  );
}
