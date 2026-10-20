import type { KosmoZustand } from '@kosmo/ui';
import { useBewegung } from '@kosmo/ui';

/**
 * **Der Orb sagt seinen Zustand auch ohne Bewegung** (Owner G1, Abstimmung mit
 * Visbox 01.10.2026: «eine Aussage steckt nie nur in der Bewegung»).
 *
 * «Hoert zu», «denkt» und «spricht» unterscheiden sich am Orb nur durch die Art
 * der Bewegung: Ringe nach innen, ein kreisender Ring, Ringe nach aussen. Wer
 * «weniger Bewegung» eingestellt hat (Geraet ODER eigener Schalter `ruhig` /
 * `aus`), sieht davon nichts — dann steht der Zustand als Kurzwort neben dem
 * Orb. In Ruhe («bereit») steht nichts: auch das ist eine Aussage, die man
 * nicht zusaetzlich hinschreiben muss.
 *
 * Mit voller Bewegung bleibt das Wort weg; die Bewegung sagt es dann schon,
 * und ein Wort daneben wuerde doppelt sagen, was man sieht.
 */
export const KURZWORT: Readonly<Record<KosmoZustand, string | null>> = {
  ruhig: null,
  hoert: 'hört zu',
  denkt: 'denkt',
  spricht: 'spricht',
};

/** Das Kurzwort, das jetzt zu zeigen ist — oder `null` (Ruhe, oder die Bewegung sagt es). */
export function useOrbKurzwort(zustand: KosmoZustand): string | null {
  const bewegung = useBewegung();
  return bewegung === 'voll' ? null : KURZWORT[zustand];
}

export interface KosmoOrbWortProps {
  zustand: KosmoZustand;
  /** Testkennung (Vorgabe `kosmo-orb-wort`); der Fensterkopf nimmt eine eigene. */
  kennung?: string;
  className?: string;
}

/** Das Kurzwort als kleines Schild neben dem Orb; rendert nichts, wenn keines zu zeigen ist. */
export function KosmoOrbWort({ zustand, kennung = 'kosmo-orb-wort', className = 'keo-wort' }: KosmoOrbWortProps) {
  const wort = useOrbKurzwort(zustand);
  if (!wort) return null;
  // `role="status"` ist hier bewusst NICHT gesetzt: der Zustand steht schon im
  // Namen des Orb-Knopfs (`aria-label`); eine Live-Region liesse jede Aenderung
  // doppelt ansagen.
  return (
    <span className={className} data-testid={kennung} data-zustand={zustand}>
      {wort}
    </span>
  );
}
