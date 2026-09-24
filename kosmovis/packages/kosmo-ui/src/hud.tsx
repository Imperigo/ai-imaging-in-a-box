import type { HTMLAttributes, ReactNode } from 'react';

/**
 * KHud + KStatuszeile (v0.8.0B / P2, Spez §3 B-42/B-43) — die Viz-Anatomie
 * (0.7.5-Handoff, Owner-Entscheid 4: Theme-Paar statt eigener Dark-Shell).
 * Beide sind reine Chrome-Bausteine; Einsatz in echten Viewport-Ecken/der
 * Shell-Statuszeile ist W3/W5-Scope, hier nur die Komponente + Tests.
 */

// ── KHud ────────────────────────────────────────────────────────────

export interface KHudProps extends HTMLAttributes<HTMLDivElement> {
  /** Mono-Titel, immer mit vorangestelltem «●» (Status nie nur Farbe, Gesetz 10). */
  titel?: string;
  /** Modusfarbe für Titel-Punkt + optionales Kopf-Icon. */
  modusFarbe?: string;
  icon?: ReactNode;
  'data-testid'?: string;
}

/** Glass-HUD-Karte (`.k-glass`) für Kennzahlen/Modus-Badge/Achsenkreuz/Zoom —
 * NIE als Stationsfläche (Gesetz 7). */
export function KHud({ titel, modusFarbe, icon, children, className, ...rest }: KHudProps) {
  const klassen = ['k-hud', 'k-glass', className].filter(Boolean).join(' ');
  return (
    <div className={klassen} {...rest}>
      {(titel !== undefined || icon !== undefined) && (
        <div className="k-hud-kopf">
          {titel !== undefined && (
            <span className="k-hud-titel" style={modusFarbe !== undefined ? { color: modusFarbe } : undefined}>
              <span aria-hidden="true">●</span> {titel}
            </span>
          )}
          {icon !== undefined && (
            <span className="k-hud-icon" style={modusFarbe !== undefined ? { color: modusFarbe } : undefined}>
              {icon}
            </span>
          )}
        </div>
      )}
      {children}
    </div>
  );
}

// ── KStatuszeile ────────────────────────────────────────────────────

export interface KStatuszeileProps extends Omit<HTMLAttributes<HTMLDivElement>, 'children'> {
  links?: ReactNode;
  rechts?: ReactNode;
  'data-testid'?: string;
}

/** 30px-Statuszeile (`--k-statusbar`), Mono-11px-Chips beidseitig — Kopfbau
 * für die Shell-Statuszeile (Einsatz W3). */
export function KStatuszeile({ links, rechts, className, ...rest }: KStatuszeileProps) {
  const klassen = ['k-statuszeile', className].filter(Boolean).join(' ');
  return (
    <div className={klassen} {...rest}>
      <div className="k-statuszeile-seite">{links}</div>
      <div className="k-statuszeile-seite">{rechts}</div>
    </div>
  );
}
