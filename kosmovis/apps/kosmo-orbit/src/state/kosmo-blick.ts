/**
 * STELLVERTRETER (Visbox) (KI-Bedienung Stufe 6, 21.10.2026) fuer `state/kosmo-blick.ts` von
 * KosmoOrbit («Kosmo sieht mit»: je Station ein Fachbild fuer Kosmos Chat, 700 Zeilen mit
 * Viewport, Plan und Schnitt).
 *
 * KosmoBlick (`state/kosmo-blick-live.ts`, woertlich) liest daraus nur, welche Station offen ist —
 * fuer die Zeile «BEREICH». In Visbox gibt es eine: die Knotenansicht. Form wie dort.
 */
export type StationId = 'vis' | 'unbekannt';

export interface Station {
  id: StationId;
  titel: string;
}

/** Der Anker der Knotenansicht (wie `STATIONS` dort: `island-graph-root`). */
const ANKER = ['station-einstellungen-vis', 'island-graph-root', 'vis-island-fuellen'];

/** Welche Station offen ist — in Visbox die Knotenansicht, sobald ihr Anker steht. */
export function erkenneAktiveStation(): Station {
  if (typeof document === 'undefined') return { id: 'unbekannt', titel: 'Visbox' };
  for (const anker of ANKER) {
    if (document.querySelector(`[data-testid="${anker}"]`)) return { id: 'vis', titel: 'Knotenansicht' };
  }
  return { id: 'unbekannt', titel: 'Visbox' };
}
