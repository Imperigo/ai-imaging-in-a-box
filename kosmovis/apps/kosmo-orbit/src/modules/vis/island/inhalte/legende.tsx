import { useState } from 'react';
import { Messrahmen } from '@kosmo/ui';
import { VIS_KATEGORIE_HUE, VIS_NODE_KATALOG, type VisGraph, type VisPort, type VisPortTyp } from '@kosmo/kernel';
import { useProject } from '../../../../state/project-store';
import { useVisRuntime } from '../../vis-runtime';
import { nodeParameterInfos, nodeZweck } from './legende-infos';
import { visInhaltsRegistry } from './registry';
import '../../vis-visual.css';
import '../vis-island.css';

/**
 * ANSICHT-Insel — Legende, NEUE Datei (P-B1/E4, `docs/V0811-SPEZ.md` §2 E4,
 * Owner-Wahl «Ansichten + Legende», Sanktion 4: kein Anbau an
 * `graph.tsx`/`austausch.tsx`).
 *
 * Insel-Äquivalent zum letzten P-B1-Audit-Fund: die Porttyp-Legende
 * existierte bisher NUR im Manuell-Chrome, zweimal inline in
 * `NodeCanvas.tsx` (Dock-Panel `visLegende` Z.941-953 + der
 * B-Modus-Minimap-Begleiter Z.1730-1739) — beide Stellen sind TABU
 * (Sanktion 4, `docs/V0811-SPEZ.md` §4, kein NodeCanvas.tsx-Edit). Ein
 * echter Re-Export der beiden dortigen Consts (`PORT_FARBE`/`PORT_TYP_NAME`)
 * wäre nur mit einem `export`-Zusatz an Ort und Stelle möglich — genau das
 * verbietet die Sanktion.
 *
 * Diese Datei importiert darum die tatsächliche FACHLOGIK — welche
 * Porttypen im aktuellen Graphen vorkommen — aus dem einzigen dafür
 * zuständigen, bereits exportierten Kernel-Katalog `VIS_NODE_KATALOG`
 * (`@kosmo/kernel`, `derive/visgraph.ts`, s. auch `inhalte/graph.tsx`s
 * NodePalette). Die distinct-Schleife unten ist Zeile für Zeile identisch
 * zu `NodeCanvas.tsx`s Original (geprüft) — eine gemeinsame Extraktion in
 * eine dritte Datei hätte NodeCanvas.tsx anfassen müssen, um von dort auf
 * die neue Stelle umzustellen, was ebenfalls TABU ist; die lokale Kopie
 * DIESER reinen Ableitungsschleife ist die einzige TABU-konforme Option.
 * `PORT_FARBE`/`PORT_TYP_NAME` selbst sind reine Präsentationsdaten (CSS-
 * Custom-Property-Namen aus `aura.css` bzw. deutsche Kurznamen, keine
 * Fachlogik) — sie erscheinen hier wortgleich, und die CSS-Klassen
 * (`vis-legende-panel`/`-zeile`/`-punkt`) kommen UNVERÄNDERT aus dem
 * gemeinsamen, nicht-TABU `vis-visual.css` — visuell identisch zum
 * Manuell-Chrome, ohne eine einzige TABU-Datei zu berühren.
 *
 * **K36 (Owner-Korrekturen 2026-07, S.14: «legende ist gut, erweitere sie an
 * infos und was der jeweilige node alles kann (infos)»):** unter der
 * Porttyp-Legende steht neu je Node-Typ des aktuellen Graphen eine
 * aufklappbare Fähigkeits-Info (Akkordeon, ein Typ offen, Kopf ≥44px Touch —
 * design-`island.css`-§4.2-Mass): Zweck (`hilfe`), Eingänge/Ausgänge
 * (`inputs`/`outputs` mit Porttyp-Punkt in der Legenden-Farbe) — beides
 * DIREKT aus `VIS_NODE_KATALOG` — plus Parameter-Sätze aus der neuen
 * Hilfsdatei `legende-infos.ts` (am Code-Verhalten geprüft, s. dort).
 * Datengetrieben wie die Porttyp-Legende selbst: nur Typen, die im Graphen
 * vorkommen. Das kompakte `vis-island-legende`-Overlay unten links
 * (NodeCanvas.tsx, K35) bleibt bewusst UNVERÄNDERT nur Porttypen.
 */

const PORT_FARBE: Record<VisPortTyp, string> = {
  szene: 'var(--k-port-szene)',
  bild: 'var(--k-port-bild)',
  prompt: 'var(--k-port-prompt)',
  zahl: 'var(--k-port-zahl)',
  material: 'var(--k-port-material)',
  kameras: 'var(--k-port-kameras)',
};

/** Deutsche Kurznamen je Porttyp — wortgleich zu `NodeCanvas.tsx`s Original. */
const PORT_TYP_NAME: Record<VisPortTyp, string> = {
  szene: 'Szene',
  bild: 'Bild',
  prompt: 'Prompt',
  zahl: 'Zahl',
  material: 'Material',
  kameras: 'Kameras',
};

/** Identische distinct-Porttypen-Schleife wie `NodeCanvas.tsx` (s. Kopfkommentar). */
function berechneLegendeTypen(graph: VisGraph | undefined): VisPortTyp[] {
  const legendeTypen: VisPortTyp[] = [];
  if (!graph) return legendeTypen;
  const gesehen = new Set<VisPortTyp>();
  for (const n of graph.nodes) {
    const k = VIS_NODE_KATALOG[n.typ];
    if (!k) continue;
    for (const p of [...k.inputs, ...k.outputs]) {
      if (!gesehen.has(p.typ)) {
        gesehen.add(p.typ);
        legendeTypen.push(p.typ);
      }
    }
  }
  return legendeTypen;
}

/** Distinct Node-Typen in Graph-Reihenfolge — dieselbe Skip-Regel für
 *  katalogfremde Typen wie `berechneLegendeTypen` (Fremd-Graph-Robustheit). */
function berechneNodeTypen(graph: VisGraph | undefined): string[] {
  const typen: string[] = [];
  if (!graph) return typen;
  const gesehen = new Set<string>();
  for (const n of graph.nodes) {
    if (!VIS_NODE_KATALOG[n.typ] || gesehen.has(n.typ)) continue;
    gesehen.add(n.typ);
    typen.push(n.typ);
  }
  return typen;
}

/** Ein-/Ausgangs-Liste einer Fähigkeits-Info — Porttyp-Punkt in derselben
 *  Farbe wie die Legende darüber (`vis-legende-punkt`, `vis-visual.css`). */
function PortListe({ titel, ports, leer }: { titel: string; ports: readonly VisPort[]; leer: string }) {
  return (
    <div>
      <p className="visisl-legende-info-titel k-label k-label-eng">{titel}</p>
      {ports.length === 0 ? (
        <p className="visisl-hinweis-klein">{leer}</p>
      ) : (
        ports.map((p) => (
          <div key={p.name} className="vis-legende-zeile">
            <span aria-hidden className="vis-legende-punkt" style={{ ['--_farbe' as string]: PORT_FARBE[p.typ] }} />
            <span>
              {p.label} · {PORT_TYP_NAME[p.typ]}
            </span>
          </div>
        ))
      )}
    </div>
  );
}

/** K36 — aufklappbare Fähigkeits-Info je Node-Typ des Graphen (s. Kopfkommentar). */
function NodeInfos({ typen }: { typen: readonly string[] }) {
  const [offen, setOffen] = useState<string | null>(null);
  return (
    <div data-testid="visisl-legende-nodes">
      <p className="visisl-legende-abschnitt k-label k-label-eng">Node-Infos</p>
      {typen.map((typ) => {
        const k = VIS_NODE_KATALOG[typ];
        if (!k) return null;
        const istOffen = offen === typ;
        const parameter = nodeParameterInfos(typ);
        return (
          <div key={typ} className="visisl-legende-node">
            <button
              type="button"
              className="k-druck visisl-legende-node-kopf"
              data-testid={`visisl-legende-node-${typ}`}
              aria-expanded={istOffen}
              onClick={() => setOffen(istOffen ? null : typ)}
            >
              <span
                aria-hidden
                className="visisl-palette-kat-strich"
                style={{ ['--_farbe' as string]: VIS_KATEGORIE_HUE[k.kategorie] }}
              />
              <span className="visisl-legende-node-name">{k.label}</span>
              <span aria-hidden className="visisl-legende-node-pfeil">
                {istOffen ? '−' : '+'}
              </span>
            </button>
            {istOffen && (
              <div className="visisl-legende-node-info" data-testid={`visisl-legende-node-info-${typ}`}>
                <p className="visisl-hinweis">{nodeZweck(typ)}</p>
                <PortListe titel="Eingänge" ports={k.inputs} leer="keine — dieser Node braucht keinen Eingang" />
                <PortListe titel="Ausgänge" ports={k.outputs} leer="keine — Endstation des Graphen" />
                {parameter.length > 0 && (
                  <div>
                    <p className="visisl-legende-info-titel k-label k-label-eng">Parameter</p>
                    {parameter.map((p) => (
                      <p key={p.name} className="visisl-hinweis-klein">
                        <strong>{p.name}</strong> — {p.info}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function LegendeStufe2() {
  const graphId = useVisRuntime((s) => s.aktiverGraphId);
  const revision = useProject((s) => s.revision);
  void revision;
  const doc = useProject.getState().doc;
  const graph = graphId ? doc.get<VisGraph>(graphId) : undefined;
  const legendeTypen = berechneLegendeTypen(graph);
  const nodeTypen = berechneNodeTypen(graph);

  return (
    <div
      className="visisl-stufe2 visisl-legende"
      data-testid="island-legende-stufe2"
      onClick={(e) => e.stopPropagation()}
    >
      {legendeTypen.length === 0 ? (
        <>
          {/* D-2: Messrahmen-Leerzustand (Vorbild bestand.tsx),
              erklärender Satz als Unterzeile. */}
          <Messrahmen height={100} caption="Noch kein Porttyp im Graphen" />
          <p className="visisl-hinweis">Die Legende füllt sich mit dem ersten Node.</p>
        </>
      ) : (
        <>
          <p className="visisl-legende-abschnitt k-label k-label-eng">Porttypen</p>
          <div data-testid="vis-legende" className="vis-legende-panel">
            {legendeTypen.map((t) => (
              <div key={t} className="vis-legende-zeile">
                <span aria-hidden className="vis-legende-punkt" style={{ ['--_farbe' as string]: PORT_FARBE[t] }} />
                <span>{PORT_TYP_NAME[t]}</span>
              </div>
            ))}
          </div>
        </>
      )}
      {nodeTypen.length > 0 && <NodeInfos typen={nodeTypen} />}
    </div>
  );
}

visInhaltsRegistry.registriere('legende', { Stufe2: LegendeStufe2, Stufe3: LegendeStufe2 });
