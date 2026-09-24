import type { HTMLAttributes, ReactNode } from 'react';

/**
 * KPill (v0.8.0B / P2, Spez §3 B-40) — Rollen-Tag: 22px hoch, Mono 600 11px
 * uppercase Tracking .14em, radius 999, Rollenfarbe als Text + 12%-Fill +
 * Stroke, optionaler 6px-Dot; `solid` kehrt Text/Fläche um
 * (`--k-signal-tinte` auf der Rollenfarbe als Fläche). Blaupause: `_ds`
 * `components/core/Pill.jsx` + 0.7.6-Rollentönungen (`--k-rolle-*-fill/-line`
 * in aura.css) — auf die BESTEHENDEN, kanonischen `--k-rolle-*`-Tokens
 * gemappt, keine neuen Farbwerte.
 */
export type KPillRolle =
  | 'manuell'
  | 'pn'
  | 'pna'
  | 'agent'
  | 'memory'
  | 'generator'
  | 'ak'
  | 'office'
  | 'signal'
  | 'neutral';

interface RollenTon {
  farbe: string;
  fill: string;
  linie: string;
}

const ROLLEN_TON: Record<KPillRolle, RollenTon> = {
  manuell: { farbe: 'var(--k-rolle-manuell)', fill: 'var(--k-rolle-manuell-fill)', linie: 'var(--k-rolle-manuell-line)' },
  pn: { farbe: 'var(--k-rolle-pn)', fill: 'var(--k-rolle-pn-fill)', linie: 'var(--k-rolle-pn-line)' },
  pna: { farbe: 'var(--k-rolle-pna)', fill: 'var(--k-rolle-pna-fill)', linie: 'var(--k-rolle-pna-line)' },
  agent: { farbe: 'var(--k-rolle-agent)', fill: 'var(--k-rolle-agent-fill)', linie: 'var(--k-rolle-agent-line)' },
  memory: { farbe: 'var(--k-rolle-memory)', fill: 'var(--k-rolle-memory-fill)', linie: 'var(--k-rolle-memory-line)' },
  generator: {
    farbe: 'var(--k-rolle-generator)',
    fill: 'var(--k-rolle-generator-fill)',
    linie: 'var(--k-rolle-generator-line)',
  },
  ak: { farbe: 'var(--k-rolle-ak)', fill: 'var(--k-rolle-ak-fill)', linie: 'var(--k-rolle-ak-line)' },
  office: { farbe: 'var(--k-rolle-office)', fill: 'var(--k-rolle-office-fill)', linie: 'var(--k-rolle-office-line)' },
  signal: { farbe: 'var(--k-signal)', fill: 'var(--k-signal-fill)', linie: 'var(--k-signal-line)' },
  neutral: { farbe: 'var(--k-ink-faint)', fill: 'var(--k-hover)', linie: 'var(--k-line-strong)' },
};

export interface KPillProps extends Omit<HTMLAttributes<HTMLSpanElement>, 'children'> {
  children: ReactNode;
  rolle?: KPillRolle;
  /** 6px-Punkt vor dem Label (WER handelt, Regel 3/§0). */
  dot?: boolean;
  /** Fläche statt Rand — Text kehrt auf `--k-signal-tinte`. */
  solid?: boolean;
  'data-testid'?: string;
}

export function KPill({ children, rolle = 'neutral', dot = false, solid = false, className, style, ...rest }: KPillProps) {
  const ton = ROLLEN_TON[rolle];
  const klassen = ['k-pill', solid ? 'k-pill--solid' : '', className].filter(Boolean).join(' ');
  return (
    <span
      className={klassen}
      style={{ ['--_farbe' as string]: ton.farbe, ['--_fill' as string]: ton.fill, ['--_linie' as string]: ton.linie, ...style }}
      {...rest}
    >
      {dot && <span className="k-pill-punkt" aria-hidden="true" />}
      {children}
    </span>
  );
}
