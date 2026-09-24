import type { InputHTMLAttributes } from 'react';

/**
 * KSwitch (v0.8.0B / P2, Spez §9.14 B-127 — Matrix-Zeile, additiv zur
 * wörtlichen §3-Liste, «falls Toggle-Bedarf»). Blaupause: `_ds`
 * `components/forms/Switch.jsx` — Track 40×24, Thumb 18px, checked hebt den
 * Akzent an. Natives `<input type="checkbox">` bleibt das Bedienelement
 * (Tastatur/Screenreader/E2E `.check()` funktionieren unverändert).
 */
export interface KSwitchProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'size'> {
  label?: string;
  'data-testid'?: string;
}

export function KSwitch({ label, className, ...rest }: KSwitchProps) {
  const klassen = ['k-switch', className].filter(Boolean).join(' ');
  return (
    <label className={klassen}>
      <input type="checkbox" {...rest} />
      <span className="k-switch-strecke" aria-hidden="true">
        <span className="k-switch-daumen" />
      </span>
      {label !== undefined && <span className="k-switch-label">{label}</span>}
    </label>
  );
}
