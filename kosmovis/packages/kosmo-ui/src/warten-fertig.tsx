import { useEffect, useRef, useState, type CSSProperties, type ReactNode } from 'react';

/**
 * **Warten und Fertig am Ort** — U13, Owner-Entscheide B2/B3 (01.10.2026).
 *
 * * **Warten** heisst: dort, wo das Ergebnis erscheinen wird, steht schon ein
 *   Platzhalter in seiner Grösse. Ohne bekannten Fortschritt atmet er leise;
 *   mit Fortschritt füllt er sich von links. Kein Drehrad am Rand, keine
 *   Meldung oben rechts — das Auge bleibt, wo das Ergebnis kommt.
 * * **Fertig** heisst: ein einziger Puls in der Farbe des Elements, am Element.
 *   Keine Meldung zum Wegklicken (Owner: «keine Meldung zum Wegklicken»).
 *
 * Die Bewegung steht in `bewegung.css` (`.k-warten`, `.k-fertig-puls`), mit
 * eigenem Zweig für «weniger Bewegung»: dann steht der Platzhalter still und
 * der Puls entfällt — der Fortschritt bleibt sichtbar, nur ohne Weg.
 */

export interface KWarteOrtProps {
  /** Was gerade entsteht, in Worten («Bild wird gerechnet»). Steht im Platzhalter und wird vorgelesen. */
  text: string;
  /** 0…1, wenn bekannt. Ohne Angabe: unbestimmt (leises Atmen). */
  fortschritt?: number;
  /**
   * `flaeche` (Vorgabe): der Platzhalter in der Grösse des Ergebnisses. `leiste`: eine Textzeile mit einem dünnen
   * Balken darunter — für Karten, Listen und Knoten, in denen kein Platz für eine Fläche ist (Owner 06.10.2026:
   * «für sämtliche dinge … für prozesse und z.b downloads eine progressbar»). Dieselbe Regel G6: gefüllt wird nur
   * aus echtem Fortschritt, sonst atmet der Balken.
   */
  form?: 'flaeche' | 'leiste';
  className?: string;
  style?: CSSProperties;
}

export function KWarteOrt({ text, fortschritt, form = 'flaeche', className, style }: KWarteOrtProps) {
  const bestimmt = fortschritt !== undefined && Number.isFinite(fortschritt);
  const anteil = bestimmt ? Math.min(1, Math.max(0, fortschritt)) : 0;
  return (
    <div
      className={className ? `k-warten ${className}` : 'k-warten'}
      style={style}
      data-art={bestimmt ? 'bestimmt' : 'unbestimmt'}
      data-form={form}
      aria-busy="true"
      aria-label={text}
      {...(bestimmt
        ? { role: 'progressbar', 'aria-valuemin': 0, 'aria-valuemax': 100, 'aria-valuenow': Math.round(anteil * 100) }
        : { role: 'status' })}
    >
      {bestimmt ? <span className="k-warten-fuellung" aria-hidden="true" style={{ transform: `scaleX(${anteil})` }} /> : null}
      <span className="k-warten-text">{text}</span>
    </div>
  );
}

export interface KFertigPulsProps {
  /** Springt dieser Wert von `false` auf `true`, pulst das Element einmal. */
  fertig: boolean;
  /** Farbe des Pulses; ohne Angabe die Schriftfarbe des Elements (`currentColor`). */
  farbe?: string;
  /** Rund für Bedienelemente (Knopf, Pille, Orb), sonst eckig wie Inhalt (Owner B8). */
  rund?: boolean;
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
}

export function KFertigPuls({ fertig, farbe, rund = false, children, className, style }: KFertigPulsProps) {
  // Nur der Wechsel pulst, nicht das erste Anzeigen: wer eine Station mit
  // fertigen Ergebnissen öffnet, soll kein Feuerwerk sehen.
  const vorher = useRef(fertig);
  const [puls, setPuls] = useState(0);
  useEffect(() => {
    if (fertig && !vorher.current) setPuls((n) => n + 1);
    vorher.current = fertig;
  }, [fertig]);
  return (
    <div
      className={className ? `k-fertig-puls ${className}` : 'k-fertig-puls'}
      style={{
        ...style,
        ...(farbe ? ({ '--k-puls-farbe': farbe } as CSSProperties) : {}),
        ...(rund ? ({ '--k-puls-rundung': 'var(--k-radius-pill)' } as CSSProperties) : {}),
      }}
      {...(puls > 0 ? { 'data-puls': String(puls) } : {})}
    >
      {children}
      {/* Der Schlüssel startet die Animation bei jedem neuen Fertig neu. */}
      {puls > 0 ? <span key={puls} className="k-fertig-puls-ring" aria-hidden="true" /> : null}
    </div>
  );
}
