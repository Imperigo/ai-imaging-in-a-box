import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import {
  ERZAEHL_HINDERNISSE,
  erzaehlLage,
  erzaehlungAus,
  naechsterWechsel,
  type ErzaehlEingang,
  type ErzaehlTaetigkeit,
} from './erzaehl-zeile';
import './ErzaehlZeile.css';

/** Wunschhöhe: unter dem Kopf (Kopfgruppe rechts gemessen bis y 60, plus Luft). */
const WUNSCH_OBEN = 70;

/**
 * Was die Erzählzeile vom Wirt braucht. KosmoOrbit füllt es aus seinen Stores
 * (`shell/claude-anschluss/ErzaehlZeile.tsx`), Visbox aus seiner Nachrichtenbrücke.
 */
export interface ErzaehlQuelle {
  /** Claude ist angeschlossen. */
  verbunden: boolean;
  /** Offene Claude-Karten (älteste zuerst). */
  offeneKarten: ErzaehlEingang['offeneKarten'];
  /** Jüngster Coop-Schritt mit seiner Kennung (die Uhr springt bei jedem neuen Schritt). */
  letzterSchritt: (NonNullable<ErzaehlEingang['letzterSchritt']> & { kennung: string }) | null;
  /** Zeit (ms) des letzten Werkzeugaufrufs von Claude. */
  zuletztAktiv: number | null;
  /** Jüngste Tätigkeit von Claude mit der Kennung des Aufrufs. */
  taetigkeit: (ErzaehlTaetigkeit & { id: string }) | null;
  /**
   * Klappt die Karten des Wirts auf (bei KosmoOrbit unten links an der Claude-Marke) und führt den
   * Fokus auf deren «Anwenden». Entschieden wird dort, nie in der Zeile. Fehlt der Rückruf, ist die
   * Zeile nur Text.
   */
  zeigeKarten?: () => void;
}

/**
 * Die Erzählzeile oben in der Mitte (Ableitung und Begründung: `erzaehl-zeile.ts`).
 * Fensterfest, unter dem Kopf; ohne Erzählung zeichnet sie nichts. Im Zustand
 * «wartet» ist sie selbst ein Knopf, der zu den Karten unten links führt: Claude-
 * Vorschläge werden nur dort entschieden, die Zeile zeigt nur, dass einer wartet (L5-18).
 */
export function ErzaehlZeile({ quelle }: { quelle: ErzaehlQuelle }) {
  const { verbunden, offeneKarten, letzterSchritt, zuletztAktiv, taetigkeit, zeigeKarten } = quelle;
  const [jetzt, setJetzt] = useState(() => Date.now());
  const zeileRef = useRef<HTMLDivElement | null>(null);

  const eingang: ErzaehlEingang = { jetzt, offeneKarten, letzterSchritt, zuletztAktiv, taetigkeit };
  const erzaehlung = erzaehlungAus(eingang);
  const wechsel = naechsterWechsel(eingang);

  // Neuer Schritt oder Aufruf: Uhr auf jetzt stellen; danach genau zum nächsten Wechsel aufwachen.
  useEffect(
    () => setJetzt(Date.now()),
    [letzterSchritt?.kennung, zuletztAktiv, offeneKarten.length, taetigkeit?.id, taetigkeit?.ende],
  );
  useEffect(() => {
    if (wechsel === null) return;
    const t = window.setTimeout(() => setJetzt(Date.now()), Math.max(0, wechsel - Date.now()) + 20);
    return () => window.clearTimeout(t);
  }, [wechsel]);

  const sichtbar = erzaehlung !== null;
  // Lage: mittig oben, ausser ein Bedienteil liegt dort (`erzaehlLage`). Nachgeführt, solange die Zeile
  // steht — Würfel und Regler kommen und gehen mit der Ansicht.
  useLayoutEffect(() => {
    const el = zeileRef.current;
    if (!sichtbar || !el) return undefined;
    const lege = () => {
      const hindernisse = ERZAEHL_HINDERNISSE.flatMap((sel) => Array.from(document.querySelectorAll(sel)))
        .filter((h) => !el.contains(h))
        .map((h) => h.getBoundingClientRect())
        .filter((r) => r.width > 0 && r.height > 0);
      const l = erzaehlLage(window.innerWidth, WUNSCH_OBEN, el.offsetWidth, el.offsetHeight, hindernisse);
      el.style.left = `${Math.round(l.left)}px`;
      el.style.top = `${Math.round(l.top)}px`;
    };
    lege();
    const t = window.setInterval(lege, 500);
    window.addEventListener('resize', lege);
    return () => {
      window.clearInterval(t);
      window.removeEventListener('resize', lege);
    };
  }, [sichtbar, erzaehlung?.text]);

  if (!erzaehlung) return null;
  // Kosmo-Schritte erzählen auch ohne Claude; Claude-Zeilen nur, wenn er da ist oder eine Karte offen hat.
  if (erzaehlung.urheber === 'claude' && erzaehlung.art !== 'wartet' && !verbunden && zuletztAktiv === null) return null;

  return (
    <div
      ref={zeileRef}
      className="erzaehl-zeile"
      data-testid="erzaehl-zeile"
      data-art={erzaehlung.art}
      data-urheber={erzaehlung.urheber}
      role="status"
      aria-live="polite"
    >
      {erzaehlung.art === 'wartet' && zeigeKarten ? (
        <button type="button" className="erzaehl-zeile-knopf" data-testid="erzaehl-zeile-karten" onClick={zeigeKarten}>
          <span className="erzaehl-zeile-punkt" aria-hidden="true" />
          <span className="erzaehl-zeile-text" data-testid="erzaehl-zeile-text">
            {erzaehlung.text}
          </span>
          <span className="erzaehl-zeile-zusatz" data-testid="erzaehl-zeile-zusatz">
            {erzaehlung.zusatz}
          </span>
          <span className="erzaehl-zeile-hinweis" data-testid="erzaehl-zeile-hinweis">
            unten links entscheiden
          </span>
        </button>
      ) : (
        <>
          <span className="erzaehl-zeile-punkt" aria-hidden="true" />
          <span className="erzaehl-zeile-text" data-testid="erzaehl-zeile-text">
            {erzaehlung.text}
          </span>
          {(erzaehlung.art === 'fehler' || erzaehlung.art === 'wartet') && (
            <span className="erzaehl-zeile-zusatz" data-testid="erzaehl-zeile-zusatz">
              {erzaehlung.zusatz}
            </span>
          )}
        </>
      )}
    </div>
  );
}
