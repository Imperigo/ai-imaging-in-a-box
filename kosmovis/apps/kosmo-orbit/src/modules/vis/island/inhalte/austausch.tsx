import { useState } from 'react';
import { KButton, KSwitch, melde, meldeFehler, Messrahmen } from '@kosmo/ui';
import type { VisGraph } from '@kosmo/kernel';
import { useProject } from '../../../../state/project-store';
import { useVisRuntime } from '../../vis-runtime';
import {
  sendeGraphRenderAuftrag,
  bescheideBridgeCatch,
  bildAufsBlatt,
  aufnahmeAufsBlatt,
  KEINE_GEOMETRIE_HINWEIS,
  szeneBauteileAnzahl,
} from '../../vis-jobs';
import { visInhaltsRegistry } from './registry';
import '../vis-island.css';

/**
 * AUSTAUSCH-Insel (PC1, `docs/V084-SPEZ.md` §5 W2, C-15) — «Render senden»/
 * «Aufs Plakat» als Stufe-2-Popups; «Kamera vorschlagen»/«Report»/«Manuell»
 * sind `hatPopup:false`-Sofort-Aktionen (`vis-island-katalog.ts`) und laufen
 * über `VisWorkspace.tsx`s `onWerkzeugAktion` — kein Registry-Eintrag nötig
 * (Muster design's 'manuell'-Werkzeug, `DesignWorkspace.tsx` Z.2247-2249).
 */

function RenderSendenStufe2() {
  const graphId = useVisRuntime((s) => s.aktiverGraphId);
  const laeufe = useVisRuntime((s) => s.laeufe);
  const renderStimmungPreset = useVisRuntime((s) => s.renderStimmungPreset);
  const runCommand = useProject((s) => s.runCommand);
  const revision = useProject((s) => s.revision);
  void revision;
  const doc = useProject.getState().doc;
  const graph = graphId ? doc.get<VisGraph>(graphId) : undefined;
  const renderNodes = graph?.nodes.filter((n) => n.typ === 'render') ?? [];
  // P-LEERSZENE (auftraege/von-homestation/auf-orbit-20260825-07.md Punkt 2):
  // dieser Knopf trug bisher GAR KEINE Sperre (nicht mal `laeuftNoch`/
  // `cloudLeer` wie sein NodeCanvas-Gegenstück) — Klick ohne Geometrie sendete
  // eine geometrielose GLB an die Bridge, unbemerkt vom Nutzer. Dieselbe Zahl,
  // dieselbe Meldung wie `NodeCanvas.tsx` (Kommentar an `szeneBauteileAnzahl`,
  // vis-jobs.ts) — EINE Quelle statt zweier Abschriften.
  const keineGeometrie = szeneBauteileAnzahl(doc) === 0;
  // v0.8.11 Z4 (`docs/V0810-SPEZ.md` §5, Ein-Quellen-Entscheid aus der
  // V0810-Z4-Schuld): Line-Art ist jetzt der PERSISTENTE Render-Node-
  // Parameter `params.lineart` (boolean), gesetzt über den bestehenden
  // `vis.nodeParametrieren`-Command (Anwendungs-Muster
  // `render-presets.ts`) — kein Insel-`useState` mehr. Der Schalter hängt
  // jetzt AM Node (nicht mehr global über der Liste), weil der Wert pro
  // Render-Node getrennt persistiert; `sendeGraphRenderAuftrag` liest
  // denselben Parameter direkt aus dem Doc (`vis-jobs.ts`) — kein zweiter
  // Übergabeweg, undo-bar, überlebt den Insel-Remount.
  const setzeLineArt = (nodeId: string, checked: boolean) => {
    try {
      runCommand('vis.nodeParametrieren', { graphId: graphId!, nodeId, params: { lineart: checked } });
    } catch (err) {
      meldeFehler(err);
    }
  };

  if (!graph || renderNodes.length === 0) {
    return (
      <div
        className="visisl-stufe2 visisl-render-senden-stufe2"
        data-testid="island-render-senden-stufe2"
        onClick={(e) => e.stopPropagation()}
      >
        {/* D-2: Messrahmen-Leerzustand (Vorbild `prepare/island/inhalte/
            bestand.tsx`), Wegweiser als Unterzeile (Auftrag §4.3). */}
        <Messrahmen height={100} caption="Kein Render-Node im aktiven Graphen" />
        <p className="visisl-hinweis">In der GRAPH-Insel einen «Render»-Node einfügen.</p>
      </div>
    );
  }

  return (
    <div
      className="visisl-stufe2 visisl-render-senden-stufe2"
      data-testid="island-render-senden-stufe2"
      onClick={(e) => e.stopPropagation()}
    >
      {renderNodes.map((n, i) => {
        const status = laeufe[n.id]?.status;
        // Bug-T4a-defensiv (NodeCanvas.tsx-Muster): ein Node OHNE `params`
        // (Hand-Edit/Fremd-Import/Yjs-Merge) darf hier nicht abstürzen.
        const lineArt = (n.params ?? {})['lineart'] === true;
        return (
          <div key={n.id} className="visisl-render-zeile">
            <span className="visisl-render-titel">Render {i + 1}</span>
            <span className="visisl-hinweis-klein">{status ?? 'bereit'}</span>
            <KSwitch
              label="Als Strichzeichnung (Line-Art)"
              data-testid={`island-render-lineart-${n.id}`}
              checked={lineArt}
              onChange={(e) => setzeLineArt(n.id, e.target.checked)}
            />
            <KButton
              size="touch"
              tone="accent"
              data-testid={`island-render-ausfuehren-${n.id}`}
              disabled={keineGeometrie}
              title={keineGeometrie ? KEINE_GEOMETRIE_HINWEIS : undefined}
              onClick={() =>
                sendeGraphRenderAuftrag(
                  graphId!,
                  n.id,
                  renderStimmungPreset ? { preset: renderStimmungPreset } : undefined,
                )
              }
            >
              Ausführen
            </KButton>
          </div>
        );
      })}
    </div>
  );
}

function AufsPlakatStufe2() {
  const graphId = useVisRuntime((s) => s.aktiverGraphId);
  const laeufe = useVisRuntime((s) => s.laeufe);
  const aufnahmen = useVisRuntime((s) => s.aufnahmen);
  const revision = useProject((s) => s.revision);
  void revision;
  const doc = useProject.getState().doc;
  const graph = graphId ? doc.get<VisGraph>(graphId) : undefined;
  const [sendend, setSendend] = useState<string | null>(null);

  const fertigeRenderNodes = (graph?.nodes ?? []).filter((n) => n.typ === 'render' && laeufe[n.id]?.status === 'fertig');
  const aufnahmeListe = Object.values(aufnahmen);

  const aufsBlatt = async (nodeId: string, jobId: string, bild: string, titel: string) => {
    setSendend(nodeId);
    try {
      const name = await bildAufsBlatt(jobId, bild, titel);
      melde(`Render liegt auf «${name}» — im KosmoPublish weiterschieben`, { ton: 'erfolg' });
    } catch (err) {
      // P5b (v0.9.56): `bildAufsBlatt` holt das Bild per Bridge-Fetch — der
      // EINE Bridge-Uebersetzer statt des rohen `err.message` («Failed to
      // fetch»), s. `bescheideBridgeCatch` (vis-jobs.ts).
      await bescheideBridgeCatch(err);
    } finally {
      setSendend(null);
    }
  };

  const aufnahmeAufsBlattKlick = async (id: string, dataUrl: string) => {
    setSendend(id);
    try {
      const name = await aufnahmeAufsBlatt(dataUrl, 'Aufnahme');
      melde(`Aufnahme liegt auf «${name}» — im KosmoPublish weiterschieben`, { ton: 'erfolg' });
    } catch (err) {
      meldeFehler(err);
    } finally {
      setSendend(null);
    }
  };

  if (fertigeRenderNodes.length === 0 && aufnahmeListe.length === 0) {
    return (
      <div
        className="visisl-stufe2 visisl-aufs-plakat-stufe2"
        data-testid="island-aufs-plakat-stufe2"
        onClick={(e) => e.stopPropagation()}
      >
        {/* D-2: Messrahmen-Leerzustand (Vorbild bestand.tsx). */}
        <Messrahmen height={100} caption="Kein fertiger Render, keine Aufnahme — «Render senden» zuerst" />
      </div>
    );
  }

  return (
    <div
      className="visisl-stufe2 visisl-aufs-plakat-stufe2"
      data-testid="island-aufs-plakat-stufe2"
      onClick={(e) => e.stopPropagation()}
    >
      {fertigeRenderNodes.map((n) => {
        const lauf = laeufe[n.id]!;
        return (
          <div key={n.id} className="visisl-render-zeile">
            <span className="visisl-render-titel">Render (fertig)</span>
            <KButton
              size="touch"
              tone="quiet"
              disabled={sendend === n.id}
              data-testid={`island-aufs-plakat-${n.id}`}
              onClick={() => void aufsBlatt(n.id, lauf.jobId!, lauf.bild!, 'Visualisierung')}
            >
              Aufs Blatt
            </KButton>
          </div>
        );
      })}
      {aufnahmeListe.map((a) => (
        <div key={a.id} className="visisl-render-zeile">
          <span className="visisl-render-titel">Aufnahme</span>
          <KButton
            size="touch"
            tone="quiet"
            disabled={sendend === a.id}
            data-testid={`island-aufs-plakat-aufnahme-${a.id}`}
            onClick={() => void aufnahmeAufsBlattKlick(a.id, a.dataUrl)}
          >
            Aufs Blatt
          </KButton>
        </div>
      ))}
    </div>
  );
}

visInhaltsRegistry.registriere('render-senden', { Stufe2: RenderSendenStufe2, Stufe3: RenderSendenStufe2 });
visInhaltsRegistry.registriere('aufs-plakat', { Stufe2: AufsPlakatStufe2, Stufe3: AufsPlakatStufe2 });
