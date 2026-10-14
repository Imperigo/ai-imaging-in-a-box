import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { OrbitKern, OrbitMark, ORBITKERN_BEWEGT_AB, ORBITKERN_KLEIN_BIS } from '../src/Logo';
import { moduleHue } from '../src/tokens';

/**
 * Owner-Abnahme 21.09.2026 («der kosmoorbit orb ist aktuell nicht derselbe
 * wie der in den tools selbst … und nicht soo gross wie jetzt») —
 * `OrbitKern` ist die EINE Orb-Zeichnung, und `OrbitMark module="kosmo"`
 * zeichnet seither nichts Eigenes mehr.
 *
 * Was dieser Test NICHT behauptet: dass `shell/KosmoOrb.tsx` (der lebende Orb
 * im Gespräch) dieselbe Zeichnung trägt. Er tut es nicht — s. den Bericht zum
 * Paket: sein Aussehen hängt an 28 `data-zustand`-Attributselektoren in
 * `apps/kosmo-orbit/src/shell/kosmo-feedback.css`, die auf `.kosmo-orb-kern`/
 * `-punkte`/`-ring` zeigen. Ein Zusammenlegen hätte sie still verwaisen
 * lassen.
 */

describe('OrbitKern — die eine Orb-Zeichnung', () => {
  it('zeichnet Schein, zwei Bahnen mit je ihrem Trabanten und den Kern', () => {
    const html = renderToStaticMarkup(
      <svg>
        <OrbitKern size={120} />
      </svg>,
    );
    // Bahn A + Trabant A (Akzentfarbe)
    expect(html).toContain('rx="40" ry="14.5"');
    expect(html).toContain('cx="90" cy="50" r="3.4"');
    // Bahn B + Trabant B (Kosmos Karmin-Rosé)
    expect(html).toContain('rx="29" ry="10"');
    expect(html).toContain(`cx="21" cy="50" r="2.6" fill="${moduleHue.kosmo}"`);
    // Schein und Kern
    expect(html).toContain('cx="50" cy="50" r="41"');
    expect(html).toContain('cx="50" cy="50" r="15"');
  });

  it('Bahn und Trabant liegen in DERSELBEN Gruppe — sonst liefe der Trabant der Bahn davon', () => {
    const html = renderToStaticMarkup(
      <svg>
        <OrbitKern size={120} />
      </svg>,
    );
    const gruppen = html.match(/<g[^>]*>.*?<\/g>/gs) ?? [];
    expect(gruppen).toHaveLength(2);
    expect(gruppen[0]).toContain('rx="40"');
    expect(gruppen[0]).toContain('cx="90"');
    expect(gruppen[1]).toContain('rx="29"');
    expect(gruppen[1]).toContain('cx="21"');
  });

  it('zwei Grössen, eine Zeichnung: gross dreht, klein steht still', () => {
    const gross = renderToStaticMarkup(
      <svg>
        <OrbitKern size={ORBITKERN_BEWEGT_AB} />
      </svg>,
    );
    expect(gross).toContain('k-orbitkern-bahn-a 34s');
    expect(gross).toContain('k-orbitkern-bahn-b 52s');
    expect(gross).toContain('k-orbitkern-atem 5.2s');
    expect(gross).toContain('k-orbitkern-schein 7s');
    expect(gross).toContain('transform-origin:50px 50px');

    const klein = renderToStaticMarkup(
      <svg>
        <OrbitKern size={ORBITKERN_BEWEGT_AB - 1} />
      </svg>,
    );
    expect(klein).not.toContain('animation');
    expect(klein).not.toContain('@keyframes');
    // Still heisst NICHT ungeneigt: die Bahnen behalten ihre Neigung.
    expect(klein).toContain('rotate(-24 50 50)');
    expect(klein).toContain('rotate(46 50 50)');
  });

  it('Klein-Variante: gröbere Striche und engerer Schein, damit die Bahnen bei 24 px nicht verschwinden', () => {
    const klein = renderToStaticMarkup(
      <svg>
        <OrbitKern size={ORBITKERN_KLEIN_BIS} />
      </svg>,
    );
    // Am Anstrich nachgemessen: 1.6 im 100er-Raster ist bei 24 px 0.38 px breit.
    expect(klein).toContain('stroke-width="4"');
    expect(klein).toContain('r="33"');
    expect(klein).toContain('r="5"');
    expect(klein).toContain('r="4"');
    // Die Konstruktion selbst bleibt Strich für Strich dieselbe.
    expect(klein).toContain('rx="40" ry="14.5"');
    expect(klein).toContain('rx="29" ry="10"');
    expect(klein).toContain('cx="50" cy="50" r="15"');

    const gross = renderToStaticMarkup(
      <svg>
        <OrbitKern size={ORBITKERN_KLEIN_BIS + 1} />
      </svg>,
    );
    expect(gross).toContain('stroke-width="1.6"');
    expect(gross).toContain('r="41"');
    expect(gross).toContain('r="3.4"');
    expect(gross).toContain('r="2.6"');
  });

  it('`bewegt` schlägt die Grössen-Vorgabe in beide Richtungen', () => {
    const kleinBewegt = renderToStaticMarkup(
      <svg>
        <OrbitKern size={20} bewegt />
      </svg>,
    );
    expect(kleinBewegt).toContain('k-orbitkern-bahn-a');
    const grossStill = renderToStaticMarkup(
      <svg>
        <OrbitKern size={200} bewegt={false} />
      </svg>,
    );
    expect(grossStill).not.toContain('animation');
  });

  it('keine eigene reduced-motion-Regel — der globale Riegel in aura.css ist die EINE Quelle', () => {
    const html = renderToStaticMarkup(
      <svg>
        <OrbitKern size={120} />
      </svg>,
    );
    expect(html).not.toContain('prefers-reduced-motion');
  });

  it('zwei Orbs auf derselben Seite nehmen sich die Verlaufs-IDs nicht weg', () => {
    const html = renderToStaticMarkup(
      <>
        <OrbitMark module="kosmo" size={24} />
        <OrbitMark module="kosmo" size={24} />
      </>,
    );
    const ids = [...html.matchAll(/<radialGradient id="([^"]+)"/g)].map((m) => m[1]!);
    expect(ids).toHaveLength(4);
    expect(new Set(ids).size).toBe(4);
    for (const id of ids) expect(id, id).toMatch(/^[A-Za-z0-9_-]+$/);
  });
});

describe('OrbitMark — der kosmo-Zweig ist jetzt OrbitKern, der Rest der Familie bleibt', () => {
  it('module="kosmo" zeichnet den Orb im 100er-Raster, API und a11y-Vertrag unverändert', () => {
    const html = renderToStaticMarkup(<OrbitMark module="kosmo" size={24} title="Kosmo" />);
    expect(html).toContain('viewBox="0 0 100 100"');
    expect(html).toContain('width="24"');
    expect(html).toContain('role="img"');
    expect(html).toContain('aria-label="Kosmo"');
    expect(html).toContain('<title>Kosmo</title>');
    expect(html).toContain(moduleHue.kosmo);
    // Die alte Kosmo-Konstruktion (Halo r 6.8 im 32er-Raster) ist weg.
    expect(html).not.toContain('r="6.8"');
  });

  it('GEGENPROBE — die übrigen Module behalten Ring, Achskreuz und ihre eigene Bahnposition', () => {
    for (const modul of ['design', 'data', 'publish', 'orbit'] as const) {
      const html = renderToStaticMarkup(<OrbitMark module={modul} size={18} />);
      expect(html, modul).not.toContain('viewBox="0 0 100 100"');
      expect(html, modul).not.toContain('k-orbitkern');
    }
    // Bahnposition: design und data sitzen auf verschiedenen Winkeln.
    const design = renderToStaticMarkup(<OrbitMark module="design" size={18} />);
    const data = renderToStaticMarkup(<OrbitMark module="data" size={18} />);
    expect(design).toContain('M16 3.4v4.2M16 24.4v4.2M3.4 16h4.2M24.4 16h4.2');
    expect(design).not.toEqual(data);
  });
});
