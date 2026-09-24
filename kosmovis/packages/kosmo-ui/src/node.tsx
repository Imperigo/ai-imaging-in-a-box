import type { HTMLAttributes, ReactNode } from 'react';
import { KPill, type KPillRolle } from './pill';

/**
 * KPipelineNode (v0.8.0B / P2, Spez §3 B-44) — der Blender/Pipeline-Knoten
 * (Blaupause: `_ds` `components/pipeline/PipelineNode.jsx`). min 220px,
 * 1.5px Rollenborder bei 55% Deckkraft, `radius-node` (18), running-Puls 2s.
 * Einsatz in NodeCanvas ist W5-Scope, hier nur Komponente + Tests.
 *
 * Der 1.5px-Rand ist ein wörtlicher Spec-Einzelwert (§3), bewusst NICHT die
 * generische B-135-Linienskala (`node 2px`) — dieselbe Präzedenz wie
 * `--k-radius-node` (18, Repo) vor der DS-Spanne (16–24): der spezifischere,
 * komponentenbezogene Spec-Wert sticht die generische Materialskala.
 */
export type KNodeRolle = KPillRolle;

const ROLLEN_LABEL: Record<KNodeRolle, string> = {
  manuell: 'MANUELL',
  pn: 'PN-MANUELL',
  pna: 'PNA',
  agent: 'KI-AGENT',
  memory: 'KI-ERINNERUNG',
  generator: 'KI-GENERATOR',
  ak: 'AK',
  office: 'BÜRO',
  signal: 'SYSTEM',
  neutral: 'NEUTRAL',
};

const ROLLEN_FARBE: Record<KNodeRolle, string> = {
  manuell: 'var(--k-rolle-manuell)',
  pn: 'var(--k-rolle-pn)',
  pna: 'var(--k-rolle-pna)',
  agent: 'var(--k-rolle-agent)',
  memory: 'var(--k-rolle-memory)',
  generator: 'var(--k-rolle-generator)',
  ak: 'var(--k-rolle-ak)',
  office: 'var(--k-rolle-office)',
  signal: 'var(--k-signal)',
  neutral: 'var(--k-ink-faint)',
};

export interface KPipelineNodeProps extends Omit<HTMLAttributes<HTMLDivElement>, 'title'> {
  rolle?: KNodeRolle;
  titel: string;
  beschreibung?: string;
  icon?: ReactNode;
  /** `laeuft` triggert zusätzlich den 2s-Glow-Puls (nur Info-Zustand, Gesetz 7). */
  status?: 'ruht' | 'aktiv' | 'laeuft';
  /** Drei Ports (ein gefüllter Eingang + zwei leere) — Standard an. */
  ports?: boolean;
  'data-testid'?: string;
}

export function KPipelineNode({
  rolle = 'signal',
  titel,
  beschreibung,
  icon,
  status = 'ruht',
  ports = true,
  className,
  ...rest
}: KPipelineNodeProps) {
  const farbe = ROLLEN_FARBE[rolle];
  const klassen = [
    'k-node',
    status === 'aktiv' ? 'k-node--aktiv' : '',
    status === 'laeuft' ? 'k-node--laeuft k-node--aktiv' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');
  return (
    <div className={klassen} style={{ ['--_rolle' as string]: farbe }} {...rest}>
      <div className="k-node-kopf">
        <KPill rolle={rolle} dot>
          {ROLLEN_LABEL[rolle]}
        </KPill>
        {icon !== undefined && (
          <span className="k-node-icon" aria-hidden="true">
            {icon}
          </span>
        )}
      </div>
      <div className="k-node-titel">{titel}</div>
      {beschreibung !== undefined && <div className="k-node-beschreibung">{beschreibung}</div>}
      {ports && (
        <div className="k-node-ports" aria-hidden="true">
          <span className="k-node-port k-node-port--gefuellt" />
          <span className="k-node-port" />
          <span className="k-node-port" />
        </div>
      )}
    </div>
  );
}
