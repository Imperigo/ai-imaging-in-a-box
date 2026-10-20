import { useKosmoStatus } from '../../../state/kosmo-status';
import { KosmoEckOrb } from '../../../shell/kosmo-eck-orb/KosmoEckOrb';
import { useKosmoGespraech } from '../../../shell/kosmo-gespraech';
import { useKosmoFragtNach } from '../../prepare/baum/kosmo-fragt';
import { KosmoFragtZahl } from '../../prepare/baum/KosmoFragtKarte';
import { useReduzierteBewegung } from './IslandShell';
import './island.css';

/**
 * Kosmo-Orb der Insel-Stationen (PD4 Abschluss, `docs/ISLAND-UI-SPEZ.md`
 * §1-Tabelle/§4.3 Zeile 5) — der Orb unten rechts. Bleibt bewusst AUSSERHALB
 * der vier Islands (§1: «Bleibt ausserhalb der vier Islands»).
 *
 * **Seit U1 (Welle B, 01.10.2026, Owner-Entscheid «der Orb wird zum
 * Fensterkopf», Entwurf A) ist er nur noch der Orb — keine Konversationskarte
 * mehr.** Bis dahin oeffnete Hover oder Fokus eine kleine Karte (`kosmo-orb-
 * karte`) mit dem letzten Satz, der Eingabe, der Motoranzeige, dem Verlauf,
 * «Kosmo fragt nach» und fuenf Chips (P-D, PB4 «Orb-Gesetz», v0.9.5 P-EK
 * «Ein Kosmo»). Das war ein zweites, kleineres Kosmo neben dem Fenster. Jetzt:
 *
 *  - **Klick oeffnet das Fenster.** Es waechst aus dem Orb; der Orb wandert in
 *    den Fensterkopf und spricht dort weiter (`shell/KosmoPanel.tsx`).
 *  - **Der letzte Satz, die Eingabe und «Kosmo fragt nach» wohnen im Fenster.**
 *    Von «Kosmo fragt nach» bleibt am Orb die Zahl der offenen Fragen (B13).
 *    Die Motoranzeige steht im Fensterkopf, der Verlauf im Fenster, «Feedback»
 *    und «Chatverlauf leeren» ebenfalls dort. Keine Faehigkeit ist weg — sie hat
 *    nur noch EINEN Ort.
 *  - **Die Karte am Orb gibt es nur mit laufendem Auftrag** (Name, Schritt N von
 *    M oder «arbeitet», «Abbrechen») — und die Blase fuer eine kurze Antwort
 *    (C22). Beides zeichnet der Baustein `KosmoEckOrb`; hier steht nur, was er
 *    nicht selbst wissen kann: die Zahl offener Fragen und den Fortschritt.
 *  - Hover oeffnet nichts mehr. Dass der Zeiger ueber einer Ecke ruht, ist kein
 *    Wunsch, ein Gespraech zu fuehren; es hat bisher die kleine Ansicht
 *    aufgerissen (und mit ihr die Leiste oben) und war die Quelle einer ganzen
 *    Reihe von Wachen («zehnte Fundstelle der Klasse», `kosmo-gespraech.ts`).
 *
 * `onKosmoOeffnen` ist weiterhin derselbe `requestKosmoFokus`/`setKosmoOpen`-
 * Callback aus `App.tsx` (K16 A6) — kein zweiter Oeffnen-Weg.
 */

export interface KosmoOrbProps {
  /** K16 A6/DesignWorkspace-Weg — optional, damit ein isoliert gemounteter Test die Komponente ohne Handoff prueft. */
  onKosmoOeffnen?: () => void;
}

export function KosmoOrb({ onKosmoOeffnen }: KosmoOrbProps) {
  const panelOffen = useKosmoGespraech((s) => s.ansicht === 'gross');
  const nachfrage = useKosmoFragtNach();
  const reduziert = useReduzierteBewegung();
  // Lauf-Fortschritt und offene Zahl reisen ueber den `zahl`-Platz des Orbs
  // (Lieferung 13 §2); die Marke `data-orb-fortschritt` steht an der Zahl.
  const zustand = useKosmoStatus((s) => s.zustand);
  const schritt = useKosmoStatus((s) => s.schritt);
  const schritteGesamt = useKosmoStatus((s) => s.schritteGesamt);
  const offenAnzahl = useKosmoStatus((s) => s.offenAnzahl);
  // Owner G6: Fortschritt nur aus gezaehlten Schritten. Ohne Schrittzahl gibt
  // es keinen Ring und keinen kreisenden Bogen (vorher «unbestimmt») — der
  // Zustand des Orbs und die Karte sagen «arbeitet», ohne eine Zahl zu erfinden.
  const hatFortschritt =
    zustand === 'dispatching' && typeof schritt === 'number' && typeof schritteGesamt === 'number' && schritteGesamt > 0;
  const laufZahl =
    zustand === 'dispatching' ? (
      hatFortschritt ? (
        <span
          className="kfn-zahl"
          data-testid="kosmo-orb-schritt-zahl"
          data-orb-fortschritt="schritt"
          aria-label={`Schritt ${schritt} von ${schritteGesamt}`}
        >
          {schritt}
        </span>
      ) : (
        <span data-orb-fortschritt="unbestimmt" hidden />
      )
    ) : zustand === 'idle' && offenAnzahl > 0 ? (
      <span className="kfn-zahl" data-testid="kosmo-orb-offen-zahl" aria-label={`${offenAnzahl} offen`}>
        {offenAnzahl}
      </span>
    ) : null;

  return (
    <div className="isl-orb-eck-huelle" data-testid="kosmo-orb-wurzel" data-reduziert={reduziert ? 'true' : 'false'}>
      <KosmoEckOrb
        onOeffnen={() => onKosmoOeffnen?.()}
        offen={panelOffen}
        {...(hatFortschritt ? { fortschritt: schritt! / schritteGesamt! } : {})}
        zahl={
          <>
            <KosmoFragtZahl anzahl={nachfrage.anzahl} />
            {laufZahl}
          </>
        }
      />
    </div>
  );
}
