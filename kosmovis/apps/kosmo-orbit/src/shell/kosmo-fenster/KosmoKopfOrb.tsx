import { forwardRef } from 'react';
import { StationLogo, type KosmoZustand } from '@kosmo/ui';
import { KosmoOrbWort } from '../kosmo-eck-orb/kosmo-orb-wort';
import { kosmoName } from '../../state/kosmo-name';
import './kosmo-fenster.css';

/**
 * **Der Orb im Kopf des Kosmo-Fensters** (U1, Entwurf A «der Orb wird zum
 * Fensterkopf», 01.10.2026).
 *
 * Der Orb aus der Ecke ist beim Oeffnen hierher gewandert und spricht hier
 * weiter: dasselbe Kosmo-Zeichen mit demselben Zustand (ruhig, hoert zu, denkt,
 * spricht), und bei «spricht» schwingt es mit dem Pegel der Stimme, wenn es
 * einen gibt. Beim Oeffnen fliegt er von der Ecke an diesen Platz
 * (`kp-orb-wandert`, `kosmo-fenster.css`; die Verschiebung setzt
 * `orb-ursprung.ts` als `--kp-orb-dx/dy`); beim Schliessen zieht das ganze
 * Fenster samt Orb in die Ecke zurueck.
 *
 * **Waehrend Kosmo arbeitet, ist auch dieser Orb der Stopp-Knopf** (C21) — wie
 * der Orb in der Ecke. Sonst ist er ein Zeichen und kein Knopf: ein Bedienelement
 * ohne Wirkung ist genau die Sorte, die dieses Haus aus der Oberflaeche nimmt.
 *
 * **Ohne Bewegung lesbar** (Owner G1): bei «weniger Bewegung» steht der Zustand
 * als Kurzwort daneben.
 */

export interface KosmoKopfOrbProps {
  zustand: KosmoZustand;
  /** Pegel der Stimme (nur bei «spricht» wirksam); `undefined` = feste Animation. */
  pegel?: number | undefined;
  /** Kosmo arbeitet — der Orb ist dann der Stopp-Knopf. */
  arbeitet: boolean;
  /** Der Abbruch ist verlangt, hat aber noch nicht gewirkt. */
  abbruchVerlangt: boolean;
  onStopp: () => void;
  /** Der Orb fliegt gerade aus der Ecke her (volle Bewegung). */
  wandert: boolean;
}

export const KosmoKopfOrb = forwardRef<HTMLSpanElement, KosmoKopfOrbProps>(function KosmoKopfOrb(
  { zustand, pegel, arbeitet, abbruchVerlangt, onStopp, wandert },
  ref,
) {
  const logo = (
    <StationLogo
      logo="kosmo"
      size={32}
      beschriftung=""
      kosmoZustand={zustand}
      {...(zustand === 'spricht' && pegel !== undefined ? { pegel } : {})}
    />
  );
  return (
    <span className="kp-kopf-orb-huelle" ref={ref} data-testid="kosmo-kopf-orb-huelle" data-wandert={wandert ? 'ja' : 'nein'}>
      {arbeitet ? (
        <button
          type="button"
          className="kp-kopf-orb kp-kopf-orb--stopp"
          data-testid="kosmo-kopf-orb"
          data-zustand={zustand}
          data-stoppt="ja"
          aria-label={`${kosmoName()} ${abbruchVerlangt ? 'hält an' : 'anhalten'}`}
          disabled={abbruchVerlangt}
          onClick={onStopp}
        >
          {logo}
          <span className="kp-kopf-stopp-zeichen" aria-hidden="true" />
        </button>
      ) : (
        <span className="kp-kopf-orb" data-testid="kosmo-kopf-orb" data-zustand={zustand} data-stoppt="nein">
          {logo}
        </span>
      )}
      <KosmoOrbWort zustand={zustand} kennung="kosmo-kopf-orb-wort" className="kp-kopf-wort" />
    </span>
  );
});
