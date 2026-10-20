import { useEffect, useRef, type MouseEvent as ReactMouseEvent, type ReactNode } from 'react';
import { KIcon, StationLogo, type KosmoZustand } from '@kosmo/ui';
import {
  stoppeAuftrag,
  useKosmoStatus,
  type KosmoAuftrag,
  type KosmoZustand as StatusZustand,
} from '../../state/kosmo-status';
import { kosmoName } from '../../state/kosmo-name';
import { registriereKosmoFragen } from '../kosmo-fenster/kosmo-fragen';
import { merkeOrbPunkt } from '../kosmo-fenster/orb-ursprung';
import { KosmoOrbWort } from './kosmo-orb-wort';
import '@kosmo/ui/bewegung.css';
import './kosmo-eck-orb.css';

/**
 * **Kosmo-Orb rechts unten — immer, ueberall** (Owner 30.09.2026: «mach auch
 * das orb immer und überall rechts unten … ist klein wenn inaktiv und wenn man
 * draufhovert wird es etwas grösser, soll zusammenspielen mit ganzen
 * grafischen animationen und ux von kosmo und ui»).
 *
 * **Seit U1 (Welle B, 01.10.2026, Entwurf A «der Orb wird zum Fensterkopf»)**:
 *
 * * Der Orb ist der Anfang des Kosmo-Fensters. Ein Klick oeffnet es; es waechst
 *   aus dem Orb, der Orb wandert in den Fensterkopf und spricht dort weiter
 *   (`shell/KosmoPanel.tsx`, `shell/kosmo-fenster/`). Beim Schliessen zieht sich
 *   beides in die Ecke zurueck.
 * * **Die Karte am Orb gibt es nur mit einem laufenden Auftrag** (Owner:
 *   «Orb-Karte: nur, was Kosmo gerade tut»): Name, «Schritt N von M» oder
 *   «arbeitet», «Abbrechen». Ohne Auftrag keine Karte. Der letzte Satz, die
 *   Eingabe und «Kosmo fragt nach» stehen im Fenster; am Orb bleibt von «Kosmo
 *   fragt nach» die Zahl (B13).
 * * **Der Fortschrittsring zeigt nur gezaehlte Schritte** (Owner G6: Fortschritt
 *   nur aus echten Schritten). Ohne gezaehlte Schritte gibt es keinen Ring und
 *   keinen kreisenden Bogen — das ruhige Warten uebernimmt der Zustand des Orbs.
 * * **Waehrend Kosmo arbeitet, ist der Orb der Stopp-Knopf** (C21): ein Klick
 *   haelt Kosmo an; Esc tut dasselbe. Das Fenster oeffnet dann die Karte
 *   («Fenster oeffnen»). Der Abbruch ist ein eigener Zustand: «haelt an» heisst
 *   verlangt, noch nicht gewirkt.
 * * **Kurze Antworten erscheinen als Blase am Orb, lange oeffnen das Fenster**
 *   (C22) — die Entscheidung trifft das Panel (`antwort-blase.ts`), hier steht
 *   nur die Blase.
 * * **Ohne Bewegung lesbar** (Owner G1, Visbox): bei «weniger Bewegung» steht der
 *   Zustand als Kurzwort neben dem Orb («hört zu», «denkt», «spricht»).
 *
 * Das Logo ist Kosmo aus der Sammlung, Version A «Schallwelle»
 * (`StationLogo logo="kosmo"`), gelesen aus dem EINEN Kosmo-Zustand der Software
 * (`useKosmoStatus`): ruhig, hoert zu (Ringe laufen nach innen), denkt (ein Ring
 * kreist), spricht (Ringe laufen nach aussen, die Scheibe schlaegt — und folgt
 * dem Pegel der Stimme, wenn es einen gibt).
 *
 * Ein Baustein: eingesetzt wird er im Rahmen der App (`App.tsx`) und in den
 * Insel-Stationen (`modules/design/island/KosmoOrb.tsx`).
 */

export function kosmoZustandAusStatus(z: StatusZustand): KosmoZustand {
  switch (z) {
    case 'listening':
      return 'hoert';
    case 'speaking':
      return 'spricht';
    case 'thinking':
    case 'writing':
    case 'dispatching':
    case 'takeover':
      return 'denkt';
    default:
      return 'ruhig';
  }
}

const ZUSTAND_WORT: Readonly<Record<KosmoZustand, string>> = {
  ruhig: 'bereit',
  hoert: 'hört zu',
  denkt: 'denkt nach',
  spricht: 'spricht',
};

/** Wie lange eine kurze Antwort als Blase stehen bleibt, wenn niemand sie beruehrt. */
export const BLASE_STEHT_MS = 12_000;

/** «Schritt N von M» — nur bei gezaehlten Schritten, sonst ehrlich «arbeitet». */
export function auftragStand(a: KosmoAuftrag): string {
  if (typeof a.schritt === 'number' && typeof a.schritteGesamt === 'number' && a.schritteGesamt > 0) {
    return `Schritt ${a.schritt} von ${a.schritteGesamt}`;
  }
  return 'arbeitet';
}

export interface KosmoEckOrbProps {
  /** Klick: das Kosmo-Fenster oeffnen bzw. schliessen. Waehrend eines Auftrags haelt der Klick Kosmo an. */
  onOeffnen: () => void;
  /** Ist das Kosmo-Fenster offen? */
  offen?: boolean;
  /** Eine Zahl am Orb (z. B. `<KosmoFragtZahl …/>`). */
  zahl?: ReactNode;
  /** Eine zusaetzliche Karte ueber dem Orb — erscheint beim Darueberfahren und mit dem Tastaturfokus. */
  karte?: ReactNode;
  /**
   * Fortschritt eines laufenden Auftrags als Ring um den Orb: ein Anteil 0…1.
   * **Nur bei gezaehlten Schritten** (Owner G6) — kennt Kosmo keine Zahl, wird
   * nichts uebergeben, und es gibt keinen Ring und keinen kreisenden Bogen.
   */
  fortschritt?: number;
  /** Testkennung des Knopfs (Vorgabe `kosmo-eck-orb`); die Zentrale reicht `kosmo-symbol` durch. */
  kennung?: string;
  /** Rechtsklick auf den Orb (Zentrale: das Stationen-Menue). */
  onKontextmenue?: (e: ReactMouseEvent<HTMLButtonElement>) => void;
  /** Doppelklick auf den Orb. */
  onDoppelklick?: (e: ReactMouseEvent<HTMLButtonElement>) => void;
}

/** Umfang des Rings (r = 30 im 64er-Raster). */
const RING_UMFANG = 2 * Math.PI * 30;

function Fortschrittsring({ wert }: { wert: number }) {
  const anteil = Math.min(1, Math.max(0, wert));
  const strich = RING_UMFANG * anteil;
  return (
    <svg className="keo-ring" viewBox="0 0 64 64" aria-hidden="true" data-testid="kosmo-eck-orb-ring" data-fortschritt={String(anteil)}>
      <circle className="keo-ring-spur" cx="32" cy="32" r="30" />
      <circle className="keo-ring-bogen" data-bogen cx="32" cy="32" r="30" strokeDasharray={`${strich} ${RING_UMFANG - strich}`} />
    </svg>
  );
}

export function KosmoEckOrb({
  onOeffnen,
  offen = false,
  zahl,
  karte,
  fortschritt,
  kennung = 'kosmo-eck-orb',
  onKontextmenue,
  onDoppelklick,
}: KosmoEckOrbProps) {
  const status = useKosmoStatus((s) => s.zustand);
  const auftrag = useKosmoStatus((s) => s.auftrag);
  const abbruchVerlangt = useKosmoStatus((s) => s.abbruchVerlangt);
  const blase = useKosmoStatus((s) => s.antwortBlase);
  const pegel = useKosmoStatus((s) => s.pegel);
  const zustand = kosmoZustandAusStatus(status);
  const aktiv = zustand !== 'ruhig';
  const fehler = status === 'error';
  const wort = ZUSTAND_WORT[zustand];
  // Waehrend Kosmo arbeitet UND das Fenster zu ist, ist der Orb der Stopp-Knopf.
  // Ist das Fenster offen, haelt der Fensterkopf den Stopp (dort steht der Orb dann).
  const stoppt = auftrag !== null && !offen;
  const knopfRef = useRef<HTMLButtonElement | null>(null);

  // Den Ort merken, solange der Orb sichtbar ist: das Fenster waechst aus ihm,
  // und im Moment des Oeffnens ist er schon ausgeblendet (`orb-ursprung.ts`).
  useEffect(() => {
    merkeOrbPunkt(knopfRef.current);
    const messen = () => merkeOrbPunkt(knopfRef.current);
    window.addEventListener('resize', messen);
    return () => window.removeEventListener('resize', messen);
  }, []);

  // U16 (Owner B10 «Fehler kurz + ‹Kosmo fragen›»): der Orb steht in jeder
  // Station, auch wenn das Fenster zu ist — dann gibt es das Panel (und mit ihm
  // seine Anmeldung) nicht. Ohne diese Anmeldung zeigte keine Fehlermeldung den
  // Knopf, ausgerechnet im Normalfall (Kosmo zu). Die Anmeldung zaehlt mit:
  // Panel und Orb koennen beide da sein, der Knopf bleibt, bis der letzte geht.
  useEffect(() => registriereKosmoFragen(), []);

  // Eine Blase, die das Fenster oeffnet, ist beantwortet — sie verschwindet.
  useEffect(() => {
    if (offen && blase) useKosmoStatus.getState().setzeAntwortBlase(null);
  }, [offen, blase]);

  // Eine Blase bleibt nur kurz stehen; wer sie anfasst (Zeiger, Tastaturfokus), behaelt sie.
  const blasenTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const haltBlase = () => {
    if (blasenTimer.current !== null) {
      clearTimeout(blasenTimer.current);
      blasenTimer.current = null;
    }
  };
  const startBlasenTimer = () => {
    haltBlase();
    blasenTimer.current = setTimeout(() => useKosmoStatus.getState().setzeAntwortBlase(null), BLASE_STEHT_MS);
  };
  useEffect(() => {
    if (!blase) return undefined;
    startBlasenTimer();
    return haltBlase;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [blase?.id]);

  const fortschrittWort =
    fortschritt === undefined ? '' : `, ${Math.round(Math.min(1, Math.max(0, fortschritt)) * 100)} % erledigt`;
  // Der Name aus der Nahtstelle (`state/kosmo-name.ts`): in KosmoOrbit «Kosmo», in einem Wirt mit
  // eigenem Assistenten dessen Name.
  const name = kosmoName();
  const knopfName = stoppt
    ? abbruchVerlangt
      ? `${name} hält an — ${wort}`
      : `${name} anhalten — ${wort}${fortschrittWort}`
    : `${name} ${offen ? 'schliessen' : 'öffnen'} — ${wort}${fortschrittWort}`;

  return (
    <div
      className={['keo-wurzel', aktiv ? 'keo-aktiv' : '', offen ? 'keo-offen' : '', fehler ? 'keo-fehler' : '', stoppt ? 'keo-stoppt' : '']
        .filter(Boolean)
        .join(' ')}
      data-testid="kosmo-eck-orb-wurzel"
      data-zustand={zustand}
      data-auftrag={auftrag ? 'laeuft' : 'keiner'}
    >
      {/* Reihenfolge im Aufbau = Tab-Folge: erst der Knopf, dann die Karten
          (Rueckgabe Int 20, 30.09.2026 — stand die Karte vorn, fiel Tab vom
          Orb aus ihm heraus, und die Karte schloss sich). Oben stehen die
          Karten trotzdem: `column-reverse` in der CSS. */}
      <div className="keo-reihe">
        <button
          ref={knopfRef}
          type="button"
          className="keo-knopf"
          data-testid={kennung}
          data-stoppt={stoppt ? 'ja' : 'nein'}
          aria-label={knopfName}
          aria-expanded={offen}
          onClick={() => {
            // Vor dem Oeffnen merken: gleich danach blendet die App den Orb aus.
            merkeOrbPunkt(knopfRef.current);
            if (stoppt) {
              if (!abbruchVerlangt) stoppeAuftrag();
              return;
            }
            onOeffnen();
          }}
          {...(onKontextmenue ? { onContextMenu: onKontextmenue } : {})}
          {...(onDoppelklick ? { onDoubleClick: onDoppelklick } : {})}
        >
          <StationLogo
            logo="kosmo"
            size={56}
            beschriftung=""
            kosmoZustand={zustand}
            {...(zustand === 'spricht' && pegel !== undefined ? { pegel } : {})}
          />
          {fortschritt !== undefined ? <Fortschrittsring wert={fortschritt} /> : null}
          {stoppt ? <span className="keo-stopp-zeichen" data-testid="kosmo-eck-orb-stopp-zeichen" aria-hidden="true" /> : null}
        </button>
        <KosmoOrbWort zustand={zustand} />
      </div>
      {zahl ? <span className="keo-zahl">{zahl}</span> : null}
      {karte ? <div className="keo-karte">{karte}</div> : null}
      {auftrag && !offen ? (
        <div className="keo-auftrag k-ankommen" data-testid="kosmo-auftrag-karte" role="status" aria-label={`${name} arbeitet`}>
          <div className="keo-auftrag-name" data-testid="kosmo-auftrag-name">
            {auftrag.name}
          </div>
          <div className="keo-auftrag-stand" data-testid="kosmo-auftrag-stand" data-gezaehlt={typeof auftrag.schritt === 'number' ? 'ja' : 'nein'}>
            {abbruchVerlangt ? 'hält an …' : auftragStand(auftrag)}
          </div>
          <div className="keo-auftrag-knoepfe">
            <button type="button" className="keo-auftrag-knopf" data-testid="kosmo-auftrag-oeffnen" onClick={onOeffnen}>
              Fenster öffnen
            </button>
            <button
              type="button"
              className="keo-auftrag-knopf keo-auftrag-knopf--stopp"
              data-testid="kosmo-auftrag-abbrechen"
              disabled={abbruchVerlangt}
              onClick={() => {
                stoppeAuftrag();
              }}
            >
              {abbruchVerlangt ? 'Hält an' : 'Abbrechen'}
            </button>
          </div>
        </div>
      ) : null}
      {blase && !offen && !auftrag ? (
        <div
          className="keo-blase k-ankommen"
          data-testid="kosmo-antwort-blase"
          role="status"
          onMouseEnter={haltBlase}
          onMouseLeave={startBlasenTimer}
          onFocus={haltBlase}
          onBlur={startBlasenTimer}
          onKeyDown={(e) => {
            if (e.key === 'Escape') useKosmoStatus.getState().setzeAntwortBlase(null);
          }}
        >
          <button
            type="button"
            className="keo-blase-text"
            data-testid="kosmo-antwort-blase-text"
            aria-label={`${name} hat geantwortet: ${blase.text} — Fenster öffnen`}
            onClick={() => {
              useKosmoStatus.getState().setzeAntwortBlase(null);
              onOeffnen();
            }}
          >
            {blase.text}
          </button>
          <button
            type="button"
            className="keo-blase-zu"
            data-testid="kosmo-antwort-blase-zu"
            aria-label="Antwort schliessen"
            onClick={() => useKosmoStatus.getState().setzeAntwortBlase(null)}
          >
            <KIcon name="schliessen" size={14} />
          </button>
        </div>
      ) : null}
    </div>
  );
}
