// @vitest-environment jsdom
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { VIS_GLYPHEN } from '../src/modules/vis/island/vis-glyphen';
import { VIS_WERKZEUG_KATALOG } from '../src/modules/vis/island/vis-island-katalog';

/**
 * `vis-glyphen.tsx` — Regressionsschutz (PA4, `docs/V085-SPEZ.md` §3 E6 +
 * §7 C-13): rendert alle Vis-Werkzeug-Icons, prüft leeren `textContent`,
 * GENAU EINEN Akzentpunkt je Icon, `currentColor`-Striche (keine
 * hartkodierte Farbe ausser dem Akzent-Token) und die vollständige
 * Abdeckung von `VIS_WERKZEUG_KATALOG` — kein Katalog-Werkzeug trägt mehr
 * einen Text-Kürzel-Fallback als `glyphe`. Muster: `island-glyphen.test.tsx`.
 *
 * v0.8.9 §9 E11 (PBL2, `docs/V089-SPEZ.md`): die Zahl 13→14 zieht mit der
 * neuen SONNE-Insel (`vis-island-katalog.ts`, EIN zusätzliches Werkzeug
 * `sonnenstunden`) nach — die Tests selbst bleiben inhaltlich unverändert,
 * nur die hartkodierten Fundament-Zahlen.
 *
 * v0.8.10 E3-Nachtrag (Owner-Entscheid 20.07.2026, `docs/V0810-SPEZ.md` §2
 * E3, Matrix C-6): 14→13 — der Insel-Rückweg 'manuell' (AUSTAUSCH) und sein
 * Icon sind entfallen, der Zugang läuft jetzt über den Einstellungs-Schalter.
 *
 * v0.8.11 P-B1/E4 (Owner-Wahl E-Vis, `docs/V0811-SPEZ.md` §2 E4, Matrix
 * C-6): 13→15 — additiv 2 neue Icons für die ANSICHT-Insel-Werkzeuge
 * 'ansichten' (Gespeicherte Ansichten) und 'legende' (Porttyp-Legende).
 */

function alsDom(html: string): HTMLDivElement {
  const div = document.createElement('div');
  div.innerHTML = html;
  return div;
}

function zaehleAkzentpunkte(html: string): number {
  return (html.match(/r="1\.13"/g) ?? []).length;
}

describe('vis-glyphen: 14 Werkzeug-Icons decken den kompletten Vis-Katalog ab', () => {
  it('VIS_WERKZEUG_KATALOG hat 14 Einträge (v0.8.11 P-B1/E4: +ansichten/+legende; K35: -minimap)', () => {
    expect(VIS_WERKZEUG_KATALOG).toHaveLength(14);
  });

  it('VIS_GLYPHEN deckt exakt die 14 Katalog-Ids ab (K35: kein minimap-Icon mehr)', () => {
    const erwartet = VIS_WERKZEUG_KATALOG.map((w) => w.id).sort();
    const tatsaechlich = Object.keys(VIS_GLYPHEN).sort();
    expect(tatsaechlich).toEqual(erwartet);
    expect(tatsaechlich).toHaveLength(14);
  });

  it('kein Vis-Katalog-Werkzeug trägt mehr einen Text-Kürzel-Fallback als `glyphe` (alle 14 sind ComponentType)', () => {
    for (const w of VIS_WERKZEUG_KATALOG) {
      expect(typeof w.glyphe, w.id).not.toBe('string');
    }
  });
});

describe('vis-glyphen: Bauvorschrift je Icon (werkzeug-icons.tsx:1-31, 24er-Norm)', () => {
  const NAMEN = Object.keys(VIS_GLYPHEN);

  it('jedes Icon rendert ein SVG mit viewBox 0 0 24 24, strokeWidth 1.75, runden Kappen/Joins, aria-hidden', () => {
    for (const name of NAMEN) {
      const Icon = VIS_GLYPHEN[name]!;
      const html = renderToStaticMarkup(<Icon />);
      expect(html, name).toContain('<svg');
      expect(html, name).toContain('viewBox="0 0 24 24"');
      expect(html, name).toContain('stroke-width="1.75"');
      expect(html, name).toContain('stroke-linecap="round"');
      expect(html, name).toContain('stroke-linejoin="round"');
      expect(html, name).toContain('aria-hidden="true"');
    }
  });

  it('jedes Icon trägt GENAU EINEN Akzentpunkt-Kreis (r=1.13, var(--k-accent))', () => {
    for (const name of NAMEN) {
      const Icon = VIS_GLYPHEN[name]!;
      const html = renderToStaticMarkup(<Icon />);
      expect(zaehleAkzentpunkte(html), name).toBe(1);
      expect((html.match(/fill="var\(--k-accent\)"/g) ?? []).length, name).toBe(1);
    }
  });

  it('jedes Icon ist ansonsten currentColor-only — keine hartkodierte Farbe ausser dem Akzent-Token', () => {
    for (const name of NAMEN) {
      const Icon = VIS_GLYPHEN[name]!;
      const html = renderToStaticMarkup(<Icon />);
      expect(html, name).toContain('stroke="currentColor"');
      const ohneAkzent = html.replace(/var\(--k-accent\)/g, '');
      expect(ohneAkzent, name).not.toMatch(/#[0-9a-fA-F]{3,8}/);
      expect(ohneAkzent, name).not.toMatch(/rgb[a]?\(/);
    }
  });

  it('jedes Icon hat einen leeren textContent (kein <text>-Kind)', () => {
    for (const name of NAMEN) {
      const Icon = VIS_GLYPHEN[name]!;
      const html = renderToStaticMarkup(<Icon />);
      const dom = alsDom(html);
      expect(dom.textContent, name).toBe('');
      expect(html, name).not.toContain('<text');
    }
  });

  it('`size` steuert die gerenderte Kantenlänge, die ViewBox bleibt 24', () => {
    const Icon = VIS_GLYPHEN.zoom!;
    const html = renderToStaticMarkup(<Icon size={40} />);
    expect(html).toContain('width="40"');
    expect(html).toContain('height="40"');
    expect(html).toContain('viewBox="0 0 24 24"');
  });

  it('die 15 Zeichnungen sind paarweise verschieden (kein Copy-Paste-Duplikat)', () => {
    const markup = NAMEN.map((name) => renderToStaticMarkup(VIS_GLYPHEN[name]!({})));
    expect(new Set(markup).size).toBe(NAMEN.length);
  });
});
