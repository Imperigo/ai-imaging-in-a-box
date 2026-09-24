import type { HTMLAttributes } from 'react';

/**
 * KTable (P-f, Bausteine-Nachtrag) — **7** rohe `<table`-Stellen im
 * Produktcode ohne gestalteten Ersatz. Reiner Klassen-Wrapper um das native
 * `<table>` (Blaupause `KToolbar`, `field.tsx:146-149`: EINE Zeile ersetzt
 * eine wiederholte lokale Style-Konstante) — `<thead>`/`<tbody>`/`<tr>`/
 * `<td>`/`<th>` bleiben die bestehenden, nativen Elemente der Aufrufstelle;
 * `aura.css` stylt sie darunter über Nachfahren-Selektoren
 * (`.k-table th`/`.k-table td`), kein eigener Kopf/Zeile/Zelle-Baustein
 * nötig.
 */
export interface KTableProps extends HTMLAttributes<HTMLTableElement> {
  /** Kompakteres Zellen-Padding für dichte Listen. */
  dicht?: boolean;
  'data-testid'?: string;
}

export function KTable({ dicht = false, className, ...rest }: KTableProps) {
  const klassen = ['k-table', dicht ? 'k-table--dicht' : '', className].filter(Boolean).join(' ');
  return <table className={klassen} {...rest} />;
}
