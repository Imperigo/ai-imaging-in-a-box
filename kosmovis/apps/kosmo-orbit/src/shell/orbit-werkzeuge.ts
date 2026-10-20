/**
 * STELLVERTRETER (Visbox) (Kopfteile, Entscheide 115/116, 20.10.2026) fuer
 * `shell/orbit-werkzeuge.ts` von KosmoOrbit.
 *
 * Die Palette am Logo (`shell/werkzeug-palette/werkzeug-palette.ts`, woertlich) rechnet in KosmoOrbit
 * die Stationen aus dieser Liste. In Visbox meldet der Wirt seine eigenen Ziele an
 * (`registrierePalettenQuelle`: «Knoten», «Visbox-Seite»), die Liste wird darum nie gelesen — sie ist
 * leer, mit denselben Typen wie dort.
 */
import type { ModuleId } from '@kosmo/ui';

export type HauptwerkzeugId = 'design' | 'spez' | 'data' | 'kosmo' | 'office';

export interface OrbitUntertool {
  readonly id: string;
  readonly titel: string;
  readonly moduleId?: ModuleId;
  readonly kommend?: boolean;
}

export interface OrbitHauptwerkzeug {
  readonly id: HauptwerkzeugId;
  readonly titel: string;
  readonly untertools: readonly OrbitUntertool[];
}

export const ORBIT_HAUPTWERKZEUGE: OrbitHauptwerkzeug[] = [];
