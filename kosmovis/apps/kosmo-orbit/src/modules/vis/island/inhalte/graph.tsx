import { KButton, KIcon, Messrahmen } from '@kosmo/ui';
import { VIS_NODE_KATALOG, VIS_KATEGORIE_HUE, type VisGraph, type VisKategorie } from '@kosmo/kernel';
import { useProject } from '../../../../state/project-store';
import { useVisRuntime } from '../../vis-runtime';
import { nodeHinzufuegen, neuerGraphErstellen, graphLoeschen } from '../../vis-graph-aktionen';
import { visInhaltsRegistry } from './registry';
import '../vis-island.css';

/**
 * GRAPH-Insel (PC1, `docs/V084-SPEZ.md` §5 W2, C-15) — Stufe-2-Inhalte für
 * Node-Palette/Ausrichten/Verbinden. Reine Registry-Komponenten (kein Prop-
 * Pfad, Muster `design/island/inhalte/*.tsx`): sie lesen `vis-runtime.ts`
 * (`aktiverGraphId`/`canvasAuswahlGroesse`) + `useProject` direkt.
 *
 * **Node-Palette** übernimmt EXAKT die bisherige `visPalette`-Dock-Panel-
 * Kategorienliste (`NodeCanvas.tsx`s `visDockPanels`) — dieselbe
 * Kategorien-Reihenfolge/-Farbe/-Icons, nur der Klick geht jetzt über die
 * geteilte `nodeHinzufuegen()`-Funktion (`vis-graph-aktionen.ts`, dieselbe
 * Spiral-Platzsuche wie `VisWorkspace.tsx`s bisheriges `nodeHinzu`).
 *
 * **U-7** (`docs/BERICHT-FABLE-CODE-2026-08-18.md` B-3, Bauauftrag): die
 * Palette-Kopfzeile trägt jetzt zusätzlich den Graphnamen + einen «Graph
 * löschen»-Knopf — der bislang fehlende UI-Handgriff für den Kernel-Command
 * `vis.graphLoeschen` (fertig gebaut/getestet, aber 0 `runCommand`-Aufrufer
 * im App-Code). `graphLoeschen()` (`vis-graph-aktionen.ts`) fragt zuerst
 * über `bestaetigen()` nach (@kosmo/ui) — anders als `NodeCanvas.tsx`s
 * `vis.nodeLoeschen`-Vorbild, weil hier ein ganzer Graph unwiderruflich
 * sichtbar verschwindet, nicht nur ein einzelner Node.
 */

const KATEGORIE_REIHENFOLGE: readonly VisKategorie[] = ['quelle', 'wandler', 'render', 'ausgabe'];
const KATEGORIE_LABEL: Record<VisKategorie, string> = {
  quelle: 'Quelle',
  wandler: 'Wandler',
  render: 'Render',
  ausgabe: 'Ausgabe',
};

function NodePaletteStufe2() {
  const graphId = useVisRuntime((s) => s.aktiverGraphId);
  const revision = useProject((s) => s.revision);
  void revision;
  const graphen = useProject.getState().doc.byKind<VisGraph>('visgraph');

  if (!graphId || !graphen.some((g) => g.id === graphId)) {
    return (
      <div className="visisl-stufe2" data-testid="island-palette-stufe2" onClick={(e) => e.stopPropagation()}>
        {/* D-2: Messrahmen-Leerzustand (Vorbild bestand.tsx), der
            Erstellen-Knopf bleibt unverändert darunter. */}
        <Messrahmen height={100} caption="Noch kein Render-Graph" />
        <KButton size="touch" tone="quiet" data-testid="visisl-graph-erstellen" onClick={() => neuerGraphErstellen()}>
          + Graph erstellen
        </KButton>
      </div>
    );
  }

  const graph = graphen.find((g) => g.id === graphId);

  return (
    <div className="visisl-stufe2 visisl-palette" data-testid="island-palette-stufe2" onClick={(e) => e.stopPropagation()}>
      {/* U-7 (`docs/BERICHT-FABLE-CODE-2026-08-18.md` B-3) — der fehlende
          UI-Handgriff für `vis.graphLoeschen`. Kopfzeile über der Palette
          (Muster `visisl-render-zeile`/`visisl-render-titel`, AUSTAUSCH-
          Insel, `austausch.tsx`): Graphname links, Lösch-Knopf rechts.
          `graphLoeschen()` (`vis-graph-aktionen.ts`) fragt selbst über
          `bestaetigen()` nach — ein Graph verschwindet unwiderruflich
          sichtbar, anders als ein einzelner Node (`NodeCanvas.tsx`s
          `vis.nodeLoeschen`, das Vorbild-Muster, ohne Rückfrage). */}
      <div className="visisl-render-zeile">
        <span className="visisl-render-titel">{graph?.name ?? 'Graph'}</span>
        <KButton
          size="touch"
          tone="danger"
          data-testid="visisl-graph-loeschen"
          onClick={() => void graphLoeschen(graphId)}
        >
          Graph löschen
        </KButton>
      </div>
      {KATEGORIE_REIHENFOLGE.map((kat) => {
        const eintraege = Object.values(VIS_NODE_KATALOG).filter((t) => t.kategorie === kat);
        if (eintraege.length === 0) return null;
        return (
          <div key={kat}>
            <div className="visisl-palette-kat-kopf">
              <span aria-hidden className="visisl-palette-kat-strich" style={{ ['--_farbe' as string]: VIS_KATEGORIE_HUE[kat] }} />
              <span className="visisl-palette-kat-label k-label k-label-eng">{KATEGORIE_LABEL[kat]}</span>
            </div>
            <div className="visisl-palette-kat-liste">
              {eintraege.map((t) => (
                <button
                  key={t.typ}
                  type="button"
                  className="k-druck visisl-palette-eintrag"
                  data-testid={`island-palette-eintrag-${t.typ}`}
                  title={t.hilfe}
                  onClick={() => nodeHinzufuegen(graphId, t.typ)}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function AusrichtenStufe2() {
  const auswahlGroesse = useVisRuntime((s) => s.canvasAuswahlGroesse);
  const sendeCanvasBefehl = useVisRuntime((s) => s.sendeCanvasBefehl);
  return (
    <div className="visisl-stufe2" data-testid="island-ausrichten-stufe2" onClick={(e) => e.stopPropagation()}>
      {auswahlGroesse < 2 ? (
        <>
          {/* D-2: Messrahmen-Leerzustand — der Wortlaut «Mindestens 2
              Nodes …» bleibt als Unterzeile (E2E `vis-editor.spec.ts`
              prüft containText). */}
          <Messrahmen height={100} caption="Keine Node-Auswahl" />
          <p className="visisl-hinweis">Mindestens 2 Nodes auswählen (Shift-Klick oder Marquee auf dem Canvas).</p>
        </>
      ) : (
        <div className="visisl-reihe">
          <KButton size="touch" tone="ghost" data-testid="island-ausrichten-links" onClick={() => sendeCanvasBefehl('ausrichten-x')}>
            Links
          </KButton>
          <KButton size="touch" tone="ghost" data-testid="island-ausrichten-oben" onClick={() => sendeCanvasBefehl('ausrichten-y')}>
            Oben
          </KButton>
          <KButton size="touch" tone="ghost" data-testid="island-vertikal-verteilen" onClick={() => sendeCanvasBefehl('vertikal-verteilen')}>
            Verteilen
          </KButton>
        </div>
      )}
    </div>
  );
}

function VerbindenStufe2() {
  return (
    <div className="visisl-stufe2" data-testid="island-verbinden-stufe2" onClick={(e) => e.stopPropagation()}>
      <p className="visisl-hinweis">
        Von einem Ausgangs-Port (rechts an einem Node) auf einen passenden Eingangs-Port (links, gleiche Farbe)
        ziehen — eine bestehende Verbindung am Ziel wird ersetzt.
      </p>
      <div className="visisl-reihe">
        <KIcon name="pfeil-rechts" size={14} />
        <span className="visisl-hinweis-klein">Ziehen verbindet — kein separater Modus nötig.</span>
      </div>
    </div>
  );
}

visInhaltsRegistry.registriere('palette', { Stufe2: NodePaletteStufe2, Stufe3: NodePaletteStufe2 });
visInhaltsRegistry.registriere('ausrichten', { Stufe2: AusrichtenStufe2, Stufe3: AusrichtenStufe2 });
visInhaltsRegistry.registriere('verbinden', { Stufe2: VerbindenStufe2, Stufe3: VerbindenStufe2 });
