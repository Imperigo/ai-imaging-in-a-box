import { useCallback, useRef, useState, type CSSProperties, type KeyboardEvent, type PointerEvent, type ReactNode } from 'react';

/**
 * **KVergleich — zwei Varianten übereinander, ein Regler teilt sie** (C45,
 * Owner-Wahl «B — Regler mit Sprung», 01.10.2026; Entwurfsfläche Blatt C45).
 *
 * Links liegt Variante A, rechts darüber Variante B, von links bis zum Regler
 * verdeckt (`clip-path`). Ziehen mit Maus, Finger oder Stift verschiebt die
 * Linie; Pfeiltasten in 5er-Schritten, Pos1/Ende an den Rand. Darunter der
 * Umschalter «A · A | B · B»: ein Tipp springt ganz auf eine Variante und
 * zurück zum Teilbild. Gleich wie der Wischregler in Visbox (Nr. 17,
 * Abstimmung G1–G10).
 *
 * Bewegung nur, wenn etwas passiert (G1): beim Ziehen folgt die Linie dem
 * Zeiger ohne Verzögerung; nur der Sprung gleitet (`k-vergleich--gleitet`,
 * bewegung.css), bei «weniger Bewegung» springt er.
 */

export interface KVergleichSeite {
  name: string;
  inhalt: ReactNode;
}

export interface KVergleichProps {
  links: KVergleichSeite;
  rechts: KVergleichSeite;
  /** Startlage in Prozent (0 = ganz B, 100 = ganz A). Vorgabe 50. */
  start?: number;
  className?: string;
  style?: CSSProperties;
}

const begrenze = (n: number) => Math.min(100, Math.max(0, Math.round(n)));

export function KVergleich({ links, rechts, start = 50, className, style }: KVergleichProps) {
  const [anteil, setAnteil] = useState(begrenze(start));
  const [gleitet, setGleitet] = useState(false);
  const flaeche = useRef<HTMLDivElement>(null);
  const ziehtRef = useRef(false);

  const ausZeiger = useCallback((clientX: number) => {
    const el = flaeche.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    if (r.width <= 0) return;
    setGleitet(false);
    setAnteil(begrenze(((clientX - r.left) / r.width) * 100));
  }, []);

  const springe = (ziel: number) => {
    setGleitet(true);
    setAnteil(ziel);
  };

  const taste = (e: KeyboardEvent<HTMLDivElement>) => {
    const neu =
      e.key === 'ArrowRight' || e.key === 'ArrowUp'
        ? anteil + 5
        : e.key === 'ArrowLeft' || e.key === 'ArrowDown'
          ? anteil - 5
          : e.key === 'Home'
            ? 0
            : e.key === 'End'
              ? 100
              : null;
    if (neu === null) return;
    e.preventDefault();
    setGleitet(false);
    setAnteil(begrenze(neu));
  };

  const runter = (e: PointerEvent<HTMLDivElement>) => {
    ziehtRef.current = true;
    e.currentTarget.setPointerCapture?.(e.pointerId);
    ausZeiger(e.clientX);
  };
  const ziehen = (e: PointerEvent<HTMLDivElement>) => {
    if (ziehtRef.current) ausZeiger(e.clientX);
  };
  const hoch = () => {
    ziehtRef.current = false;
  };

  const sprung = anteil === 100 ? 'a' : anteil === 0 ? 'b' : 'ab';
  return (
    <div className={className ? `k-vergleich ${className}` : 'k-vergleich'} style={style}>
      <div
        ref={flaeche}
        className={`k-vergleich-flaeche${gleitet ? ' k-vergleich--gleitet' : ''}`}
        onPointerDown={runter}
        onPointerMove={ziehen}
        onPointerUp={hoch}
        onPointerCancel={hoch}
      >
        <div className="k-vergleich-links">{links.inhalt}</div>
        <div className="k-vergleich-rechts" style={{ clipPath: `inset(0 0 0 ${anteil}%)` }}>
          {rechts.inhalt}
        </div>
        <span className="k-vergleich-name k-vergleich-name--links">{links.name}</span>
        <span className="k-vergleich-name k-vergleich-name--rechts">{rechts.name}</span>
        <div
          className="k-vergleich-linie"
          style={{ left: `${anteil}%` }}
          role="slider"
          tabIndex={0}
          aria-label={`Vergleich: links ${links.name}, rechts ${rechts.name}`}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={anteil}
          aria-valuetext={`${anteil} % ${links.name}`}
          onKeyDown={taste}
        >
          <span className="k-vergleich-griff" aria-hidden="true">
            ⇆
          </span>
        </div>
      </div>
      <div className="k-vergleich-sprung" role="group" aria-label="Ganz auf eine Variante springen">
        <button type="button" aria-pressed={sprung === 'a'} onClick={() => springe(100)}>
          A
        </button>
        <button type="button" aria-pressed={sprung === 'ab'} onClick={() => springe(50)}>
          A | B
        </button>
        <button type="button" aria-pressed={sprung === 'b'} onClick={() => springe(0)}>
          B
        </button>
      </div>
    </div>
  );
}
