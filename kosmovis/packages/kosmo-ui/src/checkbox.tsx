import { useEffect, useRef, type InputHTMLAttributes } from 'react';
import { KIcon } from './icons';

/**
 * KCheckbox (P-f, Bausteine-Nachtrag) — **46** rohe `type="checkbox"`-Stellen
 * im Produktcode hatten kein Gegenstück: `KSwitch` ist ausdrücklich ein
 * UMSCHALTER, kein Kontrollkästchen (`switch.tsx:4-9`, «Toggle-Bedarf»,
 * Track/Daumen-Optik) — ein Kontrollkästchen mit dritten (unbestimmten)
 * Zustand passt in diese Form nicht hinein, es braucht eine eigene.
 *
 * Blaupause: `switch.tsx` (natives `<input>` bleibt das Bedienelement,
 * Tastatur/Screenreader/E2E `.check()` funktionieren unverändert) — hier
 * ein Quadrat statt einer Strecke, mit Haken-Icon aus der bestehenden
 * `KIcon`-Registry statt einem neuen Glyphen.
 *
 * `unbestimmt` (indeterminate) ist ein DOM-Property, kein HTML-Attribut —
 * JSX kann es nicht direkt setzen, darum der Ref-Effekt. CSS `:indeterminate`
 * greift danach automatisch (steuert `.k-checkbox-minus` unten).
 */
export interface KCheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'size'> {
  size?: 'sm' | 'md';
  label?: string;
  /**
   * Erklärtext am **sichtbaren** Teil (dem `<label>`), nicht am Eingabefeld.
   *
   * **Warum eine eigene Eigenschaft und nicht das durchgereichte `title`:** Das
   * `<input>` ist hier absolut positioniert und durchsichtig (s. `aura.css`
   * `.k-checkbox input`). Ein `title` darauf erscheint zwar, aber nur über seinem
   * kleinen, unsichtbaren Kästchen — nicht über Kasten und Beschriftung, wo der Zeiger
   * wirklich ist. *Ein Hinweis, den man nur trifft, wenn man weiss wo, ist keiner.*
   *
   * Der Anlass ist gemessen (19.09.2026): Zwei Schalter in den Einstellungen erklären
   * per Erklärtext, **warum** sie gesperrt sind («nur in der Desktop-App»). Ohne diese
   * Eigenschaft hätte die Umstellung auf `KCheckbox` genau diese Erklärung verkleinert.
   */
  titel?: string;
  /** Weder an noch aus, z.B. "einige der Kinder sind ausgewählt". */
  unbestimmt?: boolean;
  'data-testid'?: string;
}

export function KCheckbox({ size = 'md', label, titel, unbestimmt = false, className, ...rest }: KCheckboxProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (inputRef.current) inputRef.current.indeterminate = unbestimmt;
  }, [unbestimmt]);

  const klassen = ['k-checkbox', `k-checkbox--${size}`, className].filter(Boolean).join(' ');

  return (
    <label className={klassen} {...(titel !== undefined ? { title: titel } : {})}>
      <input type="checkbox" ref={inputRef} {...rest} />
      <span className="k-checkbox-box" aria-hidden="true">
        <KIcon name="haken" size={14} className="k-checkbox-haken" />
        <KIcon name="minus" size={14} className="k-checkbox-minus" />
      </span>
      {label !== undefined && <span className="k-checkbox-label">{label}</span>}
    </label>
  );
}
