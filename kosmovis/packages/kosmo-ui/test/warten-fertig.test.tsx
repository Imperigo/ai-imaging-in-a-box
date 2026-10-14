// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import { KFertigPuls, KWarteOrt } from '../src/warten-fertig';

/**
 * U13, Owner-Entscheide B2/B3 (01.10.2026):
 *  - «Warten am Ort»: dort, wo das Ergebnis erscheinen wird, steht ein
 *    Platzhalter, der sich füllt — kein Drehrad irgendwo am Rand.
 *  - «Fertig-Puls am Ort»: ein kleiner Puls in der Farbe des Elements,
 *    keine Meldung zum Wegklicken.
 *
 * Rot vor gruen: vorher gibt es `warten-fertig` nicht.
 */

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
let root: Root | null = null;
let halter: HTMLDivElement | null = null;
function render(el: React.ReactElement): HTMLDivElement {
  halter = document.createElement('div');
  document.body.appendChild(halter);
  root = createRoot(halter);
  act(() => root!.render(el));
  return halter;
}
afterEach(() => {
  act(() => root?.unmount());
  halter?.remove();
});

describe('KWarteOrt — Warten dort, wo das Ergebnis erscheint', () => {
  it('ohne Fortschritt: Status, beschäftigt, mit Wortlaut zum Vorlesen', () => {
    const h = render(<KWarteOrt text="Bild wird gerechnet" style={{ height: 120 }} />);
    const ort = h.querySelector('.k-warten')!;
    expect(ort.getAttribute('role')).toBe('status');
    expect(ort.getAttribute('aria-busy')).toBe('true');
    expect(ort.textContent).toContain('Bild wird gerechnet');
    expect(ort.getAttribute('data-art')).toBe('unbestimmt');
    expect(h.querySelector('.k-warten-fuellung')).toBeNull();
  });

  it('mit Fortschritt: füllt sich, als Fortschrittsbalken lesbar', () => {
    const h = render(<KWarteOrt text="Bild wird gerechnet" fortschritt={0.4} />);
    const ort = h.querySelector('.k-warten')!;
    expect(ort.getAttribute('role')).toBe('progressbar');
    expect(ort.getAttribute('aria-valuenow')).toBe('40');
    expect(ort.getAttribute('data-art')).toBe('bestimmt');
    const f = h.querySelector<HTMLElement>('.k-warten-fuellung')!;
    expect(f.style.transform).toBe('scaleX(0.4)');
  });

  it('Form «Leiste» (06.10.2026): dieselbe Wahrheit, schmal — Vorgabe bleibt die Fläche', () => {
    const flaeche = render(<KWarteOrt text="x" />).querySelector('.k-warten')!;
    expect(flaeche.getAttribute('data-form')).toBe('flaeche');
    const leiste = render(<KWarteOrt text="Video wird übergeben · 34 MB von 192 MB" fortschritt={0.18} form="leiste" />).querySelector('.k-warten')!;
    expect(leiste.getAttribute('data-form')).toBe('leiste');
    expect(leiste.getAttribute('role')).toBe('progressbar');
    expect(leiste.getAttribute('aria-valuenow')).toBe('18');
    const unbestimmt = render(<KWarteOrt text="Brücke rechnet" form="leiste" />).querySelector('.k-warten')!;
    expect(unbestimmt.getAttribute('data-art')).toBe('unbestimmt');
    expect(unbestimmt.querySelector('.k-warten-fuellung')).toBeNull();
  });

  it('Fortschritt wird auf 0…1 begrenzt', () => {
    const h = render(<KWarteOrt text="x" fortschritt={3} />);
    expect(h.querySelector('.k-warten')!.getAttribute('aria-valuenow')).toBe('100');
  });
});

describe('KFertigPuls — ein Puls am Ort, keine Meldung', () => {
  it('pulst erst, wenn «fertig» von nein auf ja springt — nicht beim ersten Anzeigen', () => {
    const h = render(
      <KFertigPuls fertig>
        <span>Ergebnis</span>
      </KFertigPuls>,
    );
    expect(h.querySelector('.k-fertig-puls')!.getAttribute('data-puls')).toBeNull();
  });

  it('nein → ja setzt den Puls; jedes neue Fertig pulst neu', () => {
    const h = render(
      <KFertigPuls fertig={false}>
        <span>Ergebnis</span>
      </KFertigPuls>,
    );
    const el = () => h.querySelector('.k-fertig-puls')!;
    expect(el().getAttribute('data-puls')).toBeNull();
    act(() =>
      root!.render(
        <KFertigPuls fertig>
          <span>Ergebnis</span>
        </KFertigPuls>,
      ),
    );
    const erster = el().getAttribute('data-puls');
    expect(erster).not.toBeNull();
    act(() =>
      root!.render(
        <KFertigPuls fertig={false}>
          <span>Ergebnis</span>
        </KFertigPuls>,
      ),
    );
    act(() =>
      root!.render(
        <KFertigPuls fertig>
          <span>Ergebnis</span>
        </KFertigPuls>,
      ),
    );
    expect(el().getAttribute('data-puls')).not.toBe(erster);
    expect(h.textContent).toBe('Ergebnis');
  });

  it('die Farbe ist die des Elements, wenn nichts anderes gesagt ist', () => {
    const h = render(
      <KFertigPuls fertig={false} farbe="var(--k-station-vis)">
        <span>x</span>
      </KFertigPuls>,
    );
    expect(h.querySelector<HTMLElement>('.k-fertig-puls')!.style.getPropertyValue('--k-puls-farbe')).toBe('var(--k-station-vis)');
  });

  it('rund für Bedienung, eckig für Inhalt (B8): nur `rund` setzt die Pille', () => {
    const h = render(
      <KFertigPuls fertig={false} rund>
        <span>x</span>
      </KFertigPuls>,
    );
    expect(h.querySelector<HTMLElement>('.k-fertig-puls')!.style.getPropertyValue('--k-puls-rundung')).toBe('var(--k-radius-pill)');
  });
});
