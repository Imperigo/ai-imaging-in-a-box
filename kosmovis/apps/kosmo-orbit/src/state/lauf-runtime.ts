/**
 * STELLVERTRETER (Visbox) (Plan UI-Gleichheit S3, 20.10.2026) fuer `state/lauf-runtime.ts` von
 * KosmoOrbit.
 *
 * Dort fuehrt diese Datei Kosmos mehrschrittige Laeufe (Plan, Schritte, Runner, Rueckkanal ans
 * Sprachmodell). `state/kosmo-status.ts` (woertlich) spiegelt einen laufenden Lauf in den Orb —
 * Schritt N von M, Ring, «arbeitet». **In Visbox gibt es keine Laeufe des Assistenten**: Er
 * schlaegt vor, ein Mensch wendet an, und gerechnet wird am Render-Knoten. Der Stellvertreter traegt
 * darum nur die Form, die der Spiegel liest, und bleibt fest «offen» — der Orb zeigt nie einen
 * Fortschritt, den es nicht gibt.
 */
import { create } from 'zustand';

/** Wortgleich wie `@kosmo/ai` (`lauf-runner.ts`). */
export type LaufGesamtStatus = 'offen' | 'laeuft' | 'fertig' | 'fehler' | 'abgebrochen';
export type LaufSchrittStatus = 'offen' | 'laeuft' | 'ok' | 'fehler';

export interface LaufSchrittZustand {
  status: LaufSchrittStatus;
}

/** Die Teilmenge, die `state/kosmo-status.ts` liest. */
export interface LaufRuntimeState {
  schritte: readonly LaufSchrittZustand[];
  status: LaufGesamtStatus;
}

export const useLaufRuntime = create<LaufRuntimeState>(() => ({ schritte: [], status: 'offen' }));
