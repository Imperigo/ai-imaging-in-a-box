/**
 * STELLVERTRETER für `apps/kosmo-orbit/src/state/phasen-matrix.ts` (KosmoOrbit).
 *
 * Warum (E26, 24.09.2026): Die Phasen-Matrix blendet ZEICHNEN-Werkzeuge je SIA-Phase aus.
 * Die ZEICHNEN-Insel gibt es in Visbox nicht, und für jede andere Insel antwortet das
 * Original ohnehin «sichtbar» (unbekannte Id → `true`). Genau das tut der Stellvertreter
 * für alle Ids — die Vis-Inseln sehen also dasselbe wie im Original.
 */
import type { SiaPhase } from '@kosmo/kernel';

export function werkzeugInPhaseSichtbar(_werkzeugId: string, _phase: SiaPhase): boolean {
  return true;
}
