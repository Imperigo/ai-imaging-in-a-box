import { useEffect, useRef, useState, type CSSProperties } from 'react';
import { bewegungJetzt } from './anzeige';

/**
 * **KZahl — eine Zahl, die kurz zum neuen Wert läuft** (U19, Owner C7,
 * 01.10.2026: «Zahlen zählen kurz hoch»).
 *
 * Ändert sich der Wert, zählt die Anzeige in 320 ms («setzen» der
 * Dauer-Leiter) vom alten zum neuen Wert, mit auslaufender Kurve. Man sieht
 * dadurch, **dass** sich etwas geändert hat und in welche Richtung.
 *
 * Drei Grenzen, alle aus der Abstimmung mit Visbox (G1, G6):
 *  - Beim **ersten Anzeigen** steht der Wert sofort da: nichts ist passiert,
 *    also bewegt sich nichts.
 *  - Mit **«weniger Bewegung»** (Gerät oder eigener Schalter «aus») springt der Wert.
 *  - **Vorgelesen** wird immer nur der echte Endwert (unsichtbarer Text), nie ein
 *    Zwischenwert; die laufenden Ziffern sind für die Sprachausgabe verborgen.
 *    Ein Zwischenwert ist keine Messung.
 */

export interface KZahlProps {
  wert: number;
  /** Darstellung, auch für die Zwischenwerte. Vorgabe: ganze Zahl. */
  format?: (n: number) => string;
  className?: string;
  style?: CSSProperties;
}

const DAUER_MS = 320;
const ganz = (n: number) => String(Math.round(n));

/** Auslaufend: schnell los, weich ans Ziel (kein Überschiessen — eine Zahl über dem Ziel wäre falsch). */
const auslaufen = (t: number) => 1 - Math.pow(1 - t, 3);

export function KZahl({ wert, format = ganz, className, style }: KZahlProps) {
  const [anzeige, setAnzeige] = useState(wert);
  const letzter = useRef(wert);
  const lauf = useRef<number | null>(null);

  useEffect(() => {
    const von = letzter.current;
    letzter.current = wert;
    if (lauf.current !== null) cancelAnimationFrame(lauf.current);
    lauf.current = null;
    if (von === wert || !Number.isFinite(von) || !Number.isFinite(wert) || bewegungJetzt() === 'aus') {
      setAnzeige(wert);
      return;
    }
    const start = performance.now();
    const schritt = (jetzt: number) => {
      const t = Math.min(1, (jetzt - start) / DAUER_MS);
      setAnzeige(t >= 1 ? wert : von + (wert - von) * auslaufen(t));
      lauf.current = t >= 1 ? null : requestAnimationFrame(schritt);
    };
    lauf.current = requestAnimationFrame(schritt);
    return () => {
      if (lauf.current !== null) cancelAnimationFrame(lauf.current);
      lauf.current = null;
    };
  }, [wert]);

  return (
    <span className={className ? `k-zahl ${className}` : 'k-zahl'} style={style}>
      <span data-kzahl-anzeige="" aria-hidden="true">
        {format(anzeige)}
      </span>
      <span className="k-nur-sr" data-kzahl-wert="">
        {format(wert)}
      </span>
    </span>
  );
}
