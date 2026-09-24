import type { InputHTMLAttributes } from 'react';

/**
 * KSlider (P-f, Bausteine-Nachtrag) — **7** rohe `type="range"`-Stellen im
 * Produktcode ohne gestalteten Ersatz. Natives `<input type="range">` bleibt
 * das Bedienelement (Tastatur-Pfeiltasten, Screenreader-Wertansage, E2E
 * `fill()`/`type()` funktionieren unverändert) — nur Spur/Griff sind
 * `::-webkit-slider-*`/`::-moz-range-*`-gestylt, dieselbe Technik, mit der
 * jeder native Slider im Web umgesetzt wird (kein `appearance:none`-Ersatz
 * durch einen künstlichen `<div>`-Griff, der Tastatur/Screenreader neu
 * nachbauen müsste).
 */
export interface KSliderProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'size'> {
  size?: 'sm' | 'md';
  'data-testid'?: string;
}

export function KSlider({ size = 'md', className, ...rest }: KSliderProps) {
  const klassen = ['k-slider', `k-slider--${size}`, className].filter(Boolean).join(' ');
  return <input type="range" className={klassen} {...rest} />;
}
