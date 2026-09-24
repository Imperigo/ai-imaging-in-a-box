import type { TextareaHTMLAttributes } from 'react';

/**
 * KTextarea (P-f, Bausteine-Nachtrag) — **7** rohe `<textarea`-Stellen im
 * Produktcode ohne gestalteten Ersatz. Blaupause `field.tsx` `KInput`:
 * gleicher Rahmen/Radius/Fokus-Glow, `mono`-Variante für Code/Mass-Eingaben,
 * `size`-Klasse statt Inline-Werten (Muster `field.tsx:53`).
 */
export interface KTextareaProps extends Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, 'size'> {
  size?: 'sm' | 'md';
  /** Mono-Variante (`--k-font-mono`) für Code/Werte. */
  mono?: boolean;
  'data-testid'?: string;
}

export function KTextarea({ size = 'md', mono = false, className, ...rest }: KTextareaProps) {
  const klassen = ['k-textarea', `k-textarea--${size}`, mono ? 'k-textarea--mono' : '', className]
    .filter(Boolean)
    .join(' ');
  return <textarea className={klassen} {...rest} />;
}
