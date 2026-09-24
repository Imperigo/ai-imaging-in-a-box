import type { HTMLAttributes, ReactNode } from 'react';

/**
 * KKeyValue (v0.8.0B / P2, Spez §3 B-41) — Zeilenstapel für Label/Wert-Paare
 * (ersetzt die Inline-Label/Wert-Muster in Inspector/KennzahlenPanel/
 * DataWorkspace, Einsatz erst W6). Container `radius 10` + `--k-line-subtil`
 * als Zeilentrenner (1px-Lücke zwischen den `--k-surface`-Zeilen, Trick der
 * Hairline-statt-Kästen-Regel — Gesetz 8); Key Mono 11px faint, Wert Mono
 * 12px secondary; optionaler 4px-Fortschrittsbalken in Modusfarbe.
 *
 * `radius 10` ist ein wörtlicher Spec-Einzelwert (§3) zwischen den
 * bestehenden Stufen `--k-radius-sm` (8) und `--k-radius-md` (12) — keine
 * S-Stufe trifft ihn exakt, darum hartes literales `10px` (Ausnahme wie bei
 * `KPill`s `10px`-Innenabstand, Review-Hinweis dokumentiert statt still
 * gerundet).
 */
export interface KKeyValueZeile {
  key: string;
  wert: ReactNode;
  /** 0..1 — Anteil des optionalen 4px-Fortschrittsbalkens. */
  fortschritt?: number;
  /** Modusfarbe des Balkens (CSS-Farbwert/Token); Default `--k-accent`. */
  modusFarbe?: string;
  testid?: string;
}

export interface KKeyValueProps extends Omit<HTMLAttributes<HTMLDivElement>, 'children'> {
  zeilen: readonly KKeyValueZeile[];
  'data-testid'?: string;
}

export function KKeyValue({ zeilen, className, ...rest }: KKeyValueProps) {
  const klassen = ['k-keyvalue', className].filter(Boolean).join(' ');
  return (
    <div className={klassen} {...rest}>
      {zeilen.map((z, i) => {
        const anteil = z.fortschritt !== undefined ? Math.round(Math.max(0, Math.min(1, z.fortschritt)) * 100) : undefined;
        return (
          // Keys können sich wiederholen (z.B. mehrere "Status"-Zeilen) — der
          // Index gehört darum zur Identität.
          <div key={`${z.key}-${i}`} className="k-keyvalue-zeile" {...(z.testid !== undefined ? { 'data-testid': z.testid } : {})}>
            <span className="k-keyvalue-key">{z.key}</span>
            <span className="k-keyvalue-wert">{z.wert}</span>
            {anteil !== undefined && (
              <div className="k-keyvalue-fortschritt" aria-hidden="true">
                <div className="k-keyvalue-fortschritt-balken" style={{ width: `${anteil}%`, background: z.modusFarbe ?? 'var(--k-accent)' }} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
