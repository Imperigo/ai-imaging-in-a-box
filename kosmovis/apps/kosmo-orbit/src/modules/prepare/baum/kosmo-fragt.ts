/**
 * STELLVERTRETER (Visbox) (Plan UI-Gleichheit S3, 20.10.2026) fuer `modules/prepare/baum/kosmo-fragt.ts`
 * von KosmoOrbit.
 *
 * Dort fragt Kosmo nach der Art von Dokumenten im Knotenbaum von KosmoPrepare; die Zahl der offenen
 * Fragen steht am Orb (`KosmoFragtZahl`, woertlich). **Visbox hat keinen Prepare-Knotenbaum** — es
 * fragt nie etwas, die Zahl bleibt weg (`KosmoFragtZahl` zeichnet bei 0 nichts). Form und Namen
 * wortgleich, damit `KosmoOrb.tsx` und `KosmoFragtKarte.tsx` unveraendert herueberkommen.
 */
import { create } from 'zustand';

export interface ArtFrage {
  readonly graphId: string;
  readonly nodeId: string;
  readonly dateiname: string;
}

export interface KosmoFragtZustand {
  readonly geschwiegen: readonly string[];
  readonly anfrage: string | null;
  readonly gezeigt: string | null;
  frage(nodeId: string): void;
  anfrageErledigt(): void;
  schweige(nodeIds: readonly string[]): void;
  zeige(nodeId: string | null): void;
  zuruecksetzen(): void;
}

export const useKosmoFragt = create<KosmoFragtZustand>((set) => ({
  geschwiegen: [],
  anfrage: null,
  gezeigt: null,
  frage: (nodeId) => set({ anfrage: nodeId }),
  anfrageErledigt: () => set({ anfrage: null }),
  schweige: (nodeIds) => set((z) => ({ geschwiegen: [...new Set([...z.geschwiegen, ...nodeIds])] })),
  zeige: (nodeId) => set({ gezeigt: nodeId }),
  zuruecksetzen: () => set({ geschwiegen: [], anfrage: null, gezeigt: null }),
}));

export interface KosmoFragtNach {
  readonly anzahl: number;
  readonly gesamt: number;
  readonly frage: ArtFrage | null;
  bestimmen(): void;
  spaeter(): void;
}

const NICHTS: KosmoFragtNach = { anzahl: 0, gesamt: 0, frage: null, bestimmen: () => undefined, spaeter: () => undefined };

/** In Visbox fragt nichts nach — ohne Knotenbaum gibt es keine unbekannten Dokumente. */
export function useKosmoFragtNach(): KosmoFragtNach {
  return NICHTS;
}
