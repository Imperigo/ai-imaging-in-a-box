// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import { KSelect } from '../src/select';

// Gleiches Muster wie komponenten.test.tsx/select-scroll.test.tsx: ohne
// dieses Flag warnt React bei jedem `act()` in dieser jsdom-Umgebung.
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/**
 * P-PORTALRIEGEL (24.08.2026) — der Riegel unter einer Messung, nicht unter
 * einem Fehler.
 *
 * `docs/MESSUNG-AUSWAHLKREIS-2026-08-24.md` hat alle **96** produktiven
 * KSelect-Verwendungen eingeordnet und kommt auf **0 betroffen**. Diese Zahl
 * ruht auf EINER Invariante, und nur auf ihr: `select.tsx` portalt das Popup
 * nach `document.body`. Weil ein React-Portal den **echten** DOM-Knoten
 * verschiebt, ist für die Frage «welcher Vorfahre spannt den enthaltenden
 * Block für `position:fixed` auf» nicht der Vorfahre des Triggers
 * massgeblich, sondern allein `<body>`/`<html>`/`#root`. Genau darum sind
 * echte Transform-Vorfahren wie `.prtafel-welt` (`PrepareTafel.tsx:694`) oder
 * `.dw-eigenschaften-float` (die vierzehn `Inspector.tsx`-Stellen) für das
 * Popup folgenlos.
 *
 * **Kippt diese Invariante, kippt die Messung** — und zwar lautlos: das Popup
 * würde weiterhin erscheinen, weiterhin bedienbar sein, und erst unter einem
 * transformierten Vorfahren an der falschen Stelle landen. Kein bestehender
 * Test hätte das bemerkt; die Messung selbst ist eine Momentaufnahme und
 * bewacht nichts. Dieser Riegel macht aus ihr eine stehende Zusage.
 *
 * Das ist die Empfehlung aus §5 des Messberichts, ausgeführt statt notiert.
 *
 * **Was dieser Test NICHT beweist** (dieselbe Ehrlichkeit wie in
 * `select-scroll.test.tsx`): jsdom hat kein Layout und keine enthaltenden
 * Blöcke. Geprüft wird die **Baumzugehörigkeit** des Popups, nicht seine
 * geometrische Richtigkeit unter einem echten Transform-Vorfahren. Der
 * Riegel sagt «das Popup hängt an `document.body`» — er sagt nicht «das
 * Popup sitzt richtig». Für die Geometrie ist `e2e/p-anker-*.spec.ts`
 * zuständig.
 *
 * Schlägt dieser Test an, ist die richtige Reaktion **nicht**, ihn
 * anzupassen: dann muss `docs/MESSUNG-AUSWAHLKREIS-2026-08-24.md` neu
 * gemessen werden, bevor irgendetwas anderes geschieht.
 */

let root: Root | null = null;
let host: HTMLElement | null = null;

function montiere(knoten: Parameters<Root['render']>[0], hostElement?: HTMLElement): HTMLElement {
  host = hostElement ?? document.createElement('div');
  if (!host.isConnected) document.body.appendChild(host);
  root = createRoot(host);
  act(() => {
    root!.render(knoten);
  });
  return host;
}

afterEach(() => {
  if (root) {
    act(() => root!.unmount());
    root = null;
  }
  if (host && host.isConnected) host.remove();
  host = null;
});

describe('P-PORTALRIEGEL — das Popup hängt an document.body, nicht am Trigger-Vorfahren', () => {
  it('portalt nach document.body, auch wenn der Trigger tief in einem transformierten Vorfahren sitzt', () => {
    // Der Nachbau des schärfsten gemessenen Falls: `.dw-eigenschaften-float`
    // trägt sein `transform` NUR nach einem Ziehvorgang (DesignWorkspace.tsx:5988).
    // Genau dieser Zustand wird hier hergestellt — er ist der einzige, in dem
    // die Fehlerklasse überhaupt entstehen könnte.
    const schwebend = document.createElement('div');
    schwebend.className = 'dw-eigenschaften-float';
    schwebend.style.transform = 'translate(120px, 80px)';
    document.body.appendChild(schwebend);

    try {
      montiere(
        <KSelect data-testid="portal-select" value="a" onChange={() => {}}>
          <option value="a">Alpha</option>
          <option value="b">Beta</option>
        </KSelect>,
        schwebend,
      );

      const trigger = schwebend.querySelector('[data-testid="portal-select"]') as HTMLButtonElement;
      expect(trigger).not.toBeNull();
      // Gegenprobe zur Voraussetzung: der Trigger sitzt WIRKLICH unter dem
      // transformierten Vorfahren. Ohne diese Zeile wäre der Test auch dann
      // grün, wenn die Verschachtelung gar nicht zustande käme.
      expect(schwebend.contains(trigger)).toBe(true);

      act(() => {
        trigger.dispatchEvent(new MouseEvent('click', { bubbles: true }));
      });

      const popup = document.querySelector('[data-testid="portal-select-popup"]') as HTMLElement | null;
      // Zweite Gegenprobe: das Popup ist wirklich offen — sonst wäre «hängt
      // nicht unter dem Vorfahren» ein Fehlalarm aus einem geschlossenen Popup.
      expect(popup, 'Popup ist gar nicht offen — die folgenden Zusagen wären leer').not.toBeNull();

      expect(popup!.parentElement).toBe(document.body);
      expect(schwebend.contains(popup)).toBe(false);
    } finally {
      schwebend.remove();
    }
  });

  it('portalt auch ohne besonderen Vorfahren nach document.body — es gibt keinen zweiten Codepfad', () => {
    montiere(
      <KSelect data-testid="schlicht-select" value="a" onChange={() => {}}>
        <option value="a">Alpha</option>
        <option value="b">Beta</option>
      </KSelect>,
    );

    const trigger = host!.querySelector('[data-testid="schlicht-select"]') as HTMLButtonElement;
    act(() => {
      trigger.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });

    const popup = document.querySelector('[data-testid="schlicht-select-popup"]') as HTMLElement | null;
    expect(popup, 'Popup ist gar nicht offen').not.toBeNull();
    expect(popup!.parentElement).toBe(document.body);
    // Der Trigger-Host ist ein gewöhnliches div direkt unter body — das Popup
    // darf trotzdem nicht IN ihm liegen, sondern daneben.
    expect(host!.contains(popup)).toBe(false);
  });
});
