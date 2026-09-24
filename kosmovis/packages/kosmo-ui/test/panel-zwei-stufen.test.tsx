// @vitest-environment jsdom
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { KPanelZweiStufen, type KPanelZweiStufenTab } from '../src/panel-zwei-stufen';

/**
 * v0.8.1 Welle 4 / Paket P5b (Spez §2.1 «C» / §2.2 / §2.3) — Regressions-
 * schutz für `KPanelZweiStufen`, die neue Komponente, die die KennzahlenPanel-
 * /DrawPanel-Halbmuster ersetzt. `renderToStaticMarkup` genügt (Muster
 * `p2-neue-komponenten.test.tsx`) — reine Struktur-/Klassen-/Attribut-Checks,
 * keine Interaktionssimulation nötig (die läuft über die E2E-Suiten).
 */

const EIN_TAB: readonly KPanelZweiStufenTab[] = [{ id: 'a', label: 'Übersicht', inhalt: <span>Inhalt-A</span> }];

const DREI_TABS: readonly KPanelZweiStufenTab[] = [
  { id: 'baum', label: 'Modellbaum', inhalt: <span>Baum-Inhalt</span>, testid: 'draw-tab-baum' },
  { id: 'mengen', label: 'Mengen', inhalt: <span>Mengen-Inhalt</span>, testid: 'draw-tab-mengen' },
  { id: 'ausmass', label: 'Ausmass', inhalt: <span>Ausmass-Inhalt</span>, testid: 'draw-tab-ausmass' },
];

describe('KPanelZweiStufen — Kopf (§2.2: Titel + genau eine Kernkennzahl)', () => {
  it('rendert Titel und Kernkennzahl immer, unabhängig von der Stufe', () => {
    const htmlKompakt = renderToStaticMarkup(
      <KPanelZweiStufen
        titel="Kennzahlen"
        kernkennzahl="128 m² NGF"
        stufe="kompakt"
        onStufeUmschalten={() => {}}
        tabs={EIN_TAB}
        aktiverTab="a"
        onTabWechseln={() => {}}
      />,
    );
    expect(htmlKompakt).toContain('k-panel-zwei-titel');
    expect(htmlKompakt).toContain('Kennzahlen');
    expect(htmlKompakt).toContain('k-panel-zwei-kernkennzahl');
    expect(htmlKompakt).toContain('128 m² NGF');
  });

  it('trägt die Stufen-Modifikatorklasse und aria-expanded korrekt', () => {
    const kompakt = renderToStaticMarkup(
      <KPanelZweiStufen
        titel="X"
        kernkennzahl="Y"
        stufe="kompakt"
        onStufeUmschalten={() => {}}
        tabs={EIN_TAB}
        aktiverTab="a"
        onTabWechseln={() => {}}
      />,
    );
    expect(kompakt).toContain('k-panel-zwei--kompakt');
    expect(kompakt).toContain('aria-expanded="false"');

    const offen = renderToStaticMarkup(
      <KPanelZweiStufen
        titel="X"
        kernkennzahl="Y"
        stufe="offen"
        onStufeUmschalten={() => {}}
        tabs={EIN_TAB}
        aktiverTab="a"
        onTabWechseln={() => {}}
      />,
    );
    expect(offen).toContain('k-panel-zwei--offen');
    expect(offen).toContain('aria-expanded="true"');
  });

  it('additive Kopf-testid: `<testid>-umschalten` nur wenn data-testid gesetzt ist', () => {
    const mitTestid = renderToStaticMarkup(
      <KPanelZweiStufen
        titel="X"
        kernkennzahl="Y"
        stufe="offen"
        onStufeUmschalten={() => {}}
        tabs={EIN_TAB}
        aktiverTab="a"
        onTabWechseln={() => {}}
        data-testid="kennzahlen"
      />,
    );
    expect(mitTestid).toContain('data-testid="kennzahlen"');
    expect(mitTestid).toContain('data-testid="kennzahlen-umschalten"');

    const ohneTestid = renderToStaticMarkup(
      <KPanelZweiStufen
        titel="X"
        kernkennzahl="Y"
        stufe="offen"
        onStufeUmschalten={() => {}}
        tabs={EIN_TAB}
        aktiverTab="a"
        onTabWechseln={() => {}}
      />,
    );
    expect(ohneTestid).not.toContain('-umschalten');
  });
});

describe('KPanelZweiStufen — Stufe kompakt (§2.1: nur Kopf/Kerninfos)', () => {
  it('rendert WEDER Tabs noch Körper in der Stufe kompakt', () => {
    const html = renderToStaticMarkup(
      <KPanelZweiStufen
        titel="Draw"
        kernkennzahl="Modellbaum"
        stufe="kompakt"
        onStufeUmschalten={() => {}}
        tabs={DREI_TABS}
        aktiverTab="baum"
        onTabWechseln={() => {}}
      />,
    );
    expect(html).not.toContain('k-panel-zwei-koerper');
    expect(html).not.toContain('role="tablist"');
    expect(html).not.toContain('Baum-Inhalt');
  });
});

describe('KPanelZweiStufen — Stufe offen (§2.1: Kopf+Tabs+Körper)', () => {
  it('rendert Tabs (>1 Eintrag) + NUR den Inhalt des aktiven Tabs', () => {
    const html = renderToStaticMarkup(
      <KPanelZweiStufen
        titel="Draw"
        kernkennzahl="Mengen"
        stufe="offen"
        onStufeUmschalten={() => {}}
        tabs={DREI_TABS}
        aktiverTab="mengen"
        onTabWechseln={() => {}}
      />,
    );
    expect(html).toContain('role="tablist"');
    expect(html).toContain('data-testid="draw-tab-baum"');
    expect(html).toContain('data-testid="draw-tab-mengen"');
    expect(html).toContain('data-testid="draw-tab-ausmass"');
    expect(html).toContain('Mengen-Inhalt');
    expect(html).not.toContain('Baum-Inhalt');
    expect(html).not.toContain('Ausmass-Inhalt');
  });

  it('unterdrückt die Tab-Leiste, wenn nur EIN Tab existiert (KennzahlenPanel-Fall)', () => {
    const html = renderToStaticMarkup(
      <KPanelZweiStufen
        titel="Kennzahlen"
        kernkennzahl="128 m² NGF"
        stufe="offen"
        onStufeUmschalten={() => {}}
        tabs={EIN_TAB}
        aktiverTab="a"
        onTabWechseln={() => {}}
      />,
    );
    expect(html).not.toContain('role="tablist"');
    expect(html).toContain('Inhalt-A');
  });

  it('fällt bei unbekannter aktiverTab-ID auf den ersten Tab zurück (kein Crash)', () => {
    const html = renderToStaticMarkup(
      <KPanelZweiStufen
        titel="Draw"
        kernkennzahl="Modellbaum"
        stufe="offen"
        onStufeUmschalten={() => {}}
        tabs={DREI_TABS}
        aktiverTab="unbekannt"
        onTabWechseln={() => {}}
      />,
    );
    expect(html).toContain('Baum-Inhalt');
  });
});
