/**
 * STELLVERTRETER für `apps/kosmo-orbit/src/modules/design/island/KosmoOrb.tsx` (KosmoOrbit).
 *
 * Warum (E26, 24.09.2026): Der Orb ist der Zugang zum Assistenten «Kosmo» von KosmoOrbit —
 * Gespräch, Sprachmodell, Einstellungen. Den Assistenten gibt es in Visbox nicht. Der
 * Stellvertreter zeichnet darum nichts; mit der Rückkehr im Februar steht das Original
 * wieder an dieser Stelle.
 */
export interface KosmoOrbProps {
  onKosmoOeffnen?: () => void;
}

export function KosmoOrb(_props: KosmoOrbProps) {
  return null;
}
