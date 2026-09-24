import type { HTMLAttributes } from 'react';

/**
 * KCard (v0.8.0B / P2, Spez §9.14 B-126 — Matrix-Zeile, additiv zur
 * wörtlichen §3-Liste: der Digest-Vollständigkeitsabgleich (§9) ordnet KCard
 * ausdrücklich W2 zu). Blaupause: `_ds` `components/core/Card.jsx` — solide/
 * Glass/sunken Fläche, optionaler Rollenakzent als 2px-Hairline LINKS,
 * NIE eine gefärbte Box («never a colored box»).
 */
export type KCardRolle = 'manuell' | 'pn' | 'pna' | 'agent' | 'memory' | 'generator' | 'ak' | 'office';

const ROLLEN_FARBE: Record<KCardRolle, string> = {
  manuell: 'var(--k-rolle-manuell)',
  pn: 'var(--k-rolle-pn)',
  pna: 'var(--k-rolle-pna)',
  agent: 'var(--k-rolle-agent)',
  memory: 'var(--k-rolle-memory)',
  generator: 'var(--k-rolle-generator)',
  ak: 'var(--k-rolle-ak)',
  office: 'var(--k-rolle-office)',
};

export interface KCardProps extends HTMLAttributes<HTMLDivElement> {
  variante?: 'solid' | 'glass' | 'sunken';
  pad?: 'sm' | 'md' | 'lg';
  interaktiv?: boolean;
  aktiv?: boolean;
  rolle?: KCardRolle;
  'data-testid'?: string;
}

export function KCard({
  variante = 'solid',
  pad = 'md',
  interaktiv = false,
  aktiv = false,
  rolle,
  className,
  style,
  children,
  ...rest
}: KCardProps) {
  const klassen = [
    'k-card',
    `k-card--${variante}`,
    pad !== 'md' ? `k-card--pad-${pad}` : '',
    interaktiv ? 'k-card--interaktiv' : '',
    aktiv ? 'k-card--aktiv' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');
  const stil = rolle !== undefined ? { ['--_rolle' as string]: ROLLEN_FARBE[rolle], ...style } : style;
  return (
    <div className={klassen} style={stil} {...rest}>
      {rolle !== undefined && <span className="k-card-akzent" aria-hidden="true" />}
      {children}
    </div>
  );
}
