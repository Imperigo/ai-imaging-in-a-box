// @vitest-environment jsdom
import { act, createRef } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import { KButton, Panel } from '../src/components';

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/**
 * **Knopf und Flaeche waren von aussen nicht ansprechbar.**
 *
 * Gemeldet als «forwardRef fehlt». Das klingt nach einer Feinheit und ist
 * keine: wer den Fokus gezielt setzen will — zurueck auf den Ausloeser,
 * nachdem ein Fenster zugegangen ist; auf das erste Element einer Gruppe;
 * auf ein Feld nach einer Fehlermeldung — braucht eine Handhabe auf das
 * echte DOM-Element. Ohne sie bleibt genau die Sorte Tastaturarbeit
 * unmoeglich, an der dieses Vorhaben gerade baut.
 *
 * **Die Antwort ist kein `forwardRef`.** In React 19 ist `ref` fuer
 * Funktionskomponenten eine gewoehnliche Prop. Diese Probe haelt das
 * VERHALTEN fest, nicht den Mechanismus: sie fragt, ob am Ende das echte
 * Element in der Hand liegt — und bleibt damit richtig, falls die Umsetzung
 * eines Tages doch wieder ueber einen Umweg laeuft.
 *
 * ## Der Befund war anders, als er gemeldet wurde — gemessen, nicht vermutet
 *
 * Gemeldet war «forwardRef fehlt», also ein Laufzeitproblem. **Es war ein
 * reines TYP-Problem.** Gegen die alte Fassung gemessen:
 *
 *     npx vitest run … ref-durchreiche.test.tsx   → 5 passed
 *     npx tsc --noEmit -p packages/kosmo-ui       → exit 2, 4 Fehler
 *
 * React 19 hat den `ref` schon immer ueber `...rest` an den `<button>`
 * durchgereicht — zur Laufzeit funktionierte es. Der Compiler wies ihn ab
 * («Property 'ref' does not exist»), und **damit konnte ihn kein einziger
 * Aufrufer schreiben.** Die Luecke war echt, ihre Ursache war es nicht.
 *
 * **Rot-vor-Gruen liegt hier deshalb im TYPECHECK, nicht im Testlauf**, und
 * diese Datei ist selbst das Beweismittel: sie uebersetzt gegen die alte
 * Fassung nicht. Ein Test, der gegen beide Fassungen gruen laeuft, waere
 * hier kein Fehler der Probe, sondern die Aussage des Befunds.
 *
 * (Nebenbei und der Ehrlichkeit halber: mein erster Messbefehl lautete
 * `npx tsc … | head -6; echo $?` und meldete 0, obwohl vier Fehler
 * dastanden — `$?` gehoerte `head`. Genau die Falle, die dieses Repo seit
 * v0.9.45 in jedem Gate als Urteilszeile behandelt, und ich bin beim
 * Aufschreiben der Disziplin hineingelaufen.)
 */

let root: Root | null = null;
let wirt: HTMLDivElement | null = null;

function baue(el: React.ReactElement): void {
  wirt = document.createElement('div');
  document.body.appendChild(wirt);
  root = createRoot(wirt);
  act(() => root!.render(el));
}

afterEach(() => {
  if (root) act(() => root!.unmount());
  wirt?.remove();
  root = null;
  wirt = null;
});

describe('KButton/Panel sind von aussen ansprechbar', () => {
  it('KONTROLLFALL: der Knopf rendert ueberhaupt — bleibt in beiden Laeufen gruen', () => {
    baue(<KButton data-testid="knopf">Los</KButton>);
    expect(wirt!.querySelector('[data-testid="knopf"]')).not.toBeNull();
  });

  it('der `ref` eines KButton zeigt auf das ECHTE <button>, nicht auf eine Huelle', () => {
    const r = createRef<HTMLButtonElement>();
    baue(<KButton ref={r}>Los</KButton>);
    expect(r.current, 'ref bleibt null — der Knopf reicht ihn nicht durch').not.toBeNull();
    expect(r.current!.tagName).toBe('BUTTON');
    expect(r.current!.className, 'die Klassen der Komponente fehlen — falsches Element').toContain('k-btn');
  });

  it('und damit laesst sich der Fokus wirklich setzen — der Grund fuer das Ganze', () => {
    // Ohne diesen Fall bewiese der vorige nur, dass irgendein Objekt ankommt.
    const r = createRef<HTMLButtonElement>();
    baue(<KButton ref={r}>Los</KButton>);
    act(() => r.current!.focus());
    expect(document.activeElement).toBe(r.current);
  });

  it('der `ref` eines Panel zeigt auf das echte <div>', () => {
    const r = createRef<HTMLDivElement>();
    baue(<Panel ref={r}>Inhalt</Panel>);
    expect(r.current).not.toBeNull();
    expect(r.current!.tagName).toBe('DIV');
    expect(r.current!.textContent).toBe('Inhalt');
  });

  it('ein ausgeschalteter Knopf ist trotzdem ansprechbar — sonst koennte man ihn nicht messen', () => {
    // Der Fall, der bei einer Umsetzung ueber Bedingungen gern durchfaellt.
    const r = createRef<HTMLButtonElement>();
    baue(<KButton ref={r} disabled>Los</KButton>);
    expect(r.current).not.toBeNull();
    expect((r.current as HTMLButtonElement).disabled).toBe(true);
  });
});
