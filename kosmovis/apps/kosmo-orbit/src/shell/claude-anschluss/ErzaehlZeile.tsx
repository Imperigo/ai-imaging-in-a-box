import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { KButton } from '@kosmo/ui';
import { entscheideClaudeVorschlag, useClaudeAnschluss } from '../../state/claude-anschluss';
import { useClaudeTaetigkeit } from '../../state/claude-taetigkeit';
import { useKosmoCoop } from '../../state/kosmo-coop';
import { ERZAEHL_HINDERNISSE, erzaehlLage, erzaehlungAus, naechsterWechsel, type ErzaehlEingang } from './erzaehl-zeile';

/** Wunschhöhe: unter dem Kopf (Kopfgruppe rechts gemessen bis y 60, plus Luft). */
const WUNSCH_OBEN = 70;

/**
 * Die Erzählzeile oben in der Mitte (Ableitung und Begründung: `erzaehl-zeile.ts`).
 * Fensterfest, unter dem Kopf; ohne Erzählung zeichnet sie nichts. Im Zustand
 * «wartet» trägt sie Anwenden/Ablehnen selbst — dieselbe Entscheidung wie die
 * Karte unten links, nur dort, wo man hinschaut (L5-18).
 */
export function ErzaehlZeile() {
  const verbunden = useClaudeAnschluss((z) => z.verbunden);
  const vorschlaege = useClaudeAnschluss((z) => z.vorschlaege);
  const zuletztAktiv = useClaudeAnschluss((z) => z.zuletztAktiv);
  const gruppen = useKosmoCoop((z) => z.gruppen);
  // L71: jüngste Tätigkeit von Claude (R37-Strom; Kosmo-Schritte kommen über die Coop-Gruppen).
  const taetigkeit = useClaudeTaetigkeit((z) => {
    for (let i = z.eintraege.length - 1; i >= 0; i--) if (z.eintraege[i]!.urheber === 'claude') return z.eintraege[i]!;
    return null;
  });
  const [jetzt, setJetzt] = useState(() => Date.now());
  const zeileRef = useRef<HTMLDivElement | null>(null);

  const letzte = gruppen.length > 0 ? gruppen[gruppen.length - 1]! : null;
  const eingang: ErzaehlEingang = {
    jetzt,
    offeneKarten: vorschlaege,
    letzterSchritt: letzte
      ? { urheber: letzte.urheber, zusammenfassung: letzte.zusammenfassung, zeit: Date.parse(letzte.zeit), zurueckgenommen: letzte.zurueckgenommen }
      : null,
    zuletztAktiv,
    taetigkeit,
  };
  const erzaehlung = erzaehlungAus(eingang);
  const wechsel = naechsterWechsel(eingang);

  // Neuer Schritt oder Aufruf: Uhr auf jetzt stellen; danach genau zum nächsten Wechsel aufwachen.
  useEffect(() => setJetzt(Date.now()), [letzte?.kennung, zuletztAktiv, vorschlaege.length, taetigkeit?.id, taetigkeit?.ende]);
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
      <span className="erzaehl-zeile-punkt" aria-hidden="true" />
      <span className="erzaehl-zeile-text" data-testid="erzaehl-zeile-text">
        {erzaehlung.text}
      </span>
      {erzaehlung.art === 'fehler' && (
        <span className="erzaehl-zeile-zusatz" data-testid="erzaehl-zeile-zusatz">
          {erzaehlung.zusatz}
        </span>
      )}
      {erzaehlung.art === 'wartet' && (
        <>
          <span className="erzaehl-zeile-zusatz" data-testid="erzaehl-zeile-zusatz">
            {erzaehlung.zusatz}
          </span>
          <span className="erzaehl-zeile-knoepfe">
            <KButton size="sm" tone="ghost" data-testid="erzaehl-zeile-ablehnen" onClick={() => entscheideClaudeVorschlag(erzaehlung.kennung, false)}>
              Ablehnen
            </KButton>
            <KButton size="sm" tone="accent" data-testid="erzaehl-zeile-anwenden" onClick={() => entscheideClaudeVorschlag(erzaehlung.kennung, true)}>
              Anwenden
            </KButton>
          </span>
        </>
      )}
    </div>
  );
}
