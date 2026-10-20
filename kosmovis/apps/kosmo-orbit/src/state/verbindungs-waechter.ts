/**
 * STELLVERTRETER (Visbox) (Kopfteile, Entscheide 115/116, 20.10.2026) fuer
 * `state/verbindungs-waechter.ts` von KosmoOrbit.
 *
 * Der Waechter haelt dort Sync, Bruecke und Sprachmodell am Leben. In Visbox fuehrt die Mac-App die
 * Leitung zum Heim-PC (`Heimleitung`) und meldet sie der Seite (`window.visboxWirt.lage`). Die
 * Zweitgruppe (`InselKopf.tsx`, woertlich) liest hier nur `lage` — fest «ruht».
 */
import { create } from 'zustand';
import type { WaechterLage } from './kopplung';

export const useVerbindungsWaechter = create<{ lage: WaechterLage }>(() => ({ lage: 'ruht' }));
