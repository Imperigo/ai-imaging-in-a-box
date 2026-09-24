// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { KButton } from '../src/components';
import { KChip, KField, KInput, KToolGruppe, KWerkzeugKreis } from '../src/field';
import { KTabs } from '../src/tabs';

/**
 * v0.8.0B / P2 (Spez §3) — Regressionsschutz für den Umbau bestehender
 * Komponenten: API/Props/testids/aria bleiben byte-gleich (geprüft über die
 * bestehenden Klassennamen/Struktur), nur Optik/CSS ändert sich. Die reine
 * CSS-Deklarationsebene (Farben/Radien) wird über `aura.css`-Textproben
 * geprüft (Muster `popup-layout.test.tsx`), da jsdom kein echtes Layout/CSS
 * auswertet.
 */

const auraCss = readFileSync(path.resolve(__dirname, '../src/aura.css'), 'utf8');

describe('KButton (Spez §3 B-34): Klassen-Vertrag bleibt byte-gleich, Grössen additiv', () => {
  it('tone-Klassen (k-btn-accent/-quiet/-ghost/-danger) unverändert benannt', () => {
    expect(renderToStaticMarkup(<KButton tone="accent">A</KButton>)).toContain('k-btn-accent');
    expect(renderToStaticMarkup(<KButton tone="quiet">A</KButton>)).toContain('k-btn-quiet');
    expect(renderToStaticMarkup(<KButton tone="ghost">A</KButton>)).toContain('k-btn-ghost');
    expect(renderToStaticMarkup(<KButton tone="danger">A</KButton>)).toContain('k-btn-danger');
  });

  it('NEU: size="lg" ist additiv wählbar (k-btn-lg), Default bleibt md', () => {
    expect(renderToStaticMarkup(<KButton size="lg">Gross</KButton>)).toContain('k-btn-lg');
    expect(renderToStaticMarkup(<KButton>Normal</KButton>)).toContain('k-btn-md');
  });

  it('data-testid/disabled bleiben unverändert durchgereicht', () => {
    const html = renderToStaticMarkup(
      <KButton data-testid="mein-knopf" disabled>
        X
      </KButton>,
    );
    expect(html).toContain('data-testid="mein-knopf"');
    expect(html).toContain('disabled=""');
  });

  it('aura.css: .k-btn-accent trägt Wash+Line+Text (1px-Border-Prinzip), keine Volltonfüllung', () => {
    expect(auraCss).toMatch(/\.k-btn-accent\s*{[^}]*background:\s*var\(--k-accent-wash\)/);
    expect(auraCss).toMatch(/\.k-btn-accent\s*{[^}]*color:\s*var\(--k-accent\)/);
  });

  it('aura.css: .k-btn-danger trägt 12%-Fill/45%-Stroke', () => {
    expect(auraCss).toMatch(/\.k-btn-danger\s*{[^}]*color-mix\(in srgb, var\(--k-danger\) 12%/);
    expect(auraCss).toMatch(/\.k-btn-danger\s*{[^}]*color-mix\(in srgb, var\(--k-danger\) 45%/);
  });

  it('aura.css: Grössen sm/md/lg = 32/40/48px', () => {
    expect(auraCss).toMatch(/\.k-btn-sm\s*{[^}]*height:\s*32px/);
    expect(auraCss).toMatch(/\.k-btn-md\s*{[^}]*height:\s*40px/);
    expect(auraCss).toMatch(/\.k-btn-lg\s*{[^}]*height:\s*48px/);
  });
});

describe('KField/KInput (Spez §3 B-35): sunken+line, Mono-Micro-Label, NEU command-Variante', () => {
  it('Default-Variante rendert weiterhin GENAU ein <input> ohne Wrapper (byte-gleich)', () => {
    const html = renderToStaticMarkup(<KInput data-testid="feld-1" />);
    expect(html).not.toContain('k-input-wrap');
    expect(html).toContain('<input');
    expect(html).toContain('data-testid="feld-1"');
  });

  it('KField-Label trägt weiterhin k-field-label (jetzt Mono-Micro per CSS)', () => {
    const html = renderToStaticMarkup(
      <KField label="Breite">
        <KInput />
      </KField>,
    );
    expect(html).toContain('k-field-label');
    expect(html).toContain('Breite');
  });

  it('NEU: variant="command" rendert einen Wrapper + optionalen Kbd-Chip', () => {
    const html = renderToStaticMarkup(<KInput variant="command" kbd="⌘K" data-testid="cmd" />);
    expect(html).toContain('k-input-wrap--command');
    expect(html).toContain('k-input-kbd');
    expect(html).toContain('⌘K');
    expect(html).toContain('data-testid="cmd"');
  });

  it('aura.css: .k-input steht auf --k-sunken (mit --k-field-Fallback für Papier)', () => {
    expect(auraCss).toMatch(/\.k-input\s*{[^}]*background:\s*var\(--k-sunken,\s*var\(--k-field\)\)/);
  });

  it('aura.css: .k-field-label ist Mono, uppercase, Tracking .14em', () => {
    expect(auraCss).toMatch(/\.k-field-label\s*{[^}]*font-family:\s*var\(--k-font-mono\)/);
    expect(auraCss).toMatch(/\.k-field-label\s*{[^}]*text-transform:\s*uppercase/);
    expect(auraCss).toMatch(/\.k-field-label\s*{[^}]*letter-spacing:\s*0\.14em/);
  });
});

describe('KTabs (Spez §3 B-36): Segmented-Pill-Anatomie, role/aria unverändert', () => {
  it('role=tablist/tab + aria-selected bleiben (Bestandsvertrag)', () => {
    const html = renderToStaticMarkup(
      <KTabs items={[{ id: 'a', label: 'A' }, { id: 'b', label: 'B' }]} aktiv="b" onChange={() => {}} />,
    );
    expect(html).toContain('role="tablist"');
    expect(html).toMatch(/role="tab"[^>]*aria-selected="true"[^>]*>[\s\S]*?B/);
  });

  it('aura.css: Container ist Segmented-Pill (radius 999, 2px-Innenpadding)', () => {
    expect(auraCss).toMatch(/\.k-tabs\s*{[^}]*border-radius:\s*var\(--k-radius-pill\)/);
    expect(auraCss).toMatch(/\.k-tabs\s*{[^}]*padding:\s*2px/);
  });

  it('aura.css: aktiver Tab trägt einen 5px-Akzent-Punkt (::before)', () => {
    expect(auraCss).toMatch(/\.k-tab--aktiv::before\s*{[^}]*width:\s*5px/);
    expect(auraCss).toMatch(/\.k-tab--aktiv::before\s*{[^}]*background:\s*var\(--k-accent\)/);
  });
});

describe('KChip (Spez §3 B-37): Default byte-gleich, NEU status/geschlossen', () => {
  it('Default-Variante rendert weiterhin exakt k-chip k-chip--{size} k-chip--{tone}', () => {
    const html = renderToStaticMarkup(
      <KChip size="sm" tone="fuellung">
        Rohbau
      </KChip>,
    );
    expect(html).toContain('k-chip k-chip--sm k-chip--fuellung');
  });

  it('NEU: variant="status" rendert k-status-chip', () => {
    const html = renderToStaticMarkup(<KChip variant="status">ONLINE</KChip>);
    expect(html).toContain('k-status-chip');
  });

  it('NEU: variant="geschlossen" rendert einen Knopf «+ NAME»', () => {
    const html = renderToStaticMarkup(
      <KChip variant="geschlossen" onClick={() => {}}>
        CHECKS
      </KChip>,
    );
    expect(html).toContain('<button');
    expect(html).toContain('k-chip-geschlossen');
    expect(html).toContain('+');
    expect(html).toContain('CHECKS');
  });

  /**
   * NACHGEFÜHRT in v0.9.29 / D-11 — und zwar auf Ansage.
   *
   * Bis v0.9.28 pinnte dieser Test `font-size: 9.5px` als wörtlichen
   * B-37-Spec-Einzelwert; der Kommentar in `aura.css` begründete ihn
   * damit, dass keine Stufe der Skala ihn treffe — «zwischen `--k-t-xs`
   * (10.5) und einem denkbaren kleineren Wert». **Mit Kanon E-9
   * existiert dieser kleinere Wert:** `--k-t-xxs` (9px). E-9 AUSNAHMEN (3)
   * hat den Chip darum ausdrücklich in die Migration eingeschlossen, mit
   * dem Satz «wer B-37 wörtlich halten will, braucht einen
   * Owner-Entscheid» — ein solcher liegt nicht vor, also gilt der Kanon.
   *
   * Die Zusicherung bleibt inhaltlich dieselbe: der Chip trägt die
   * FEINSTE Stufe der Skala. Sie steht jetzt nur nicht mehr als Literal
   * da, sondern als Name — was der Schriftgrad-Wächter aus demselben
   * Paket ohnehin erzwingt. Höhe und gestrichelter Rand sind unberührt.
   */
  it('aura.css: Closed-Chip ist 22px hoch, gestrichelt, Mono auf der feinsten Stufe (--k-t-xxs)', () => {
    expect(auraCss).toMatch(/\.k-chip-geschlossen\s*{[^}]*height:\s*22px/);
    expect(auraCss).toMatch(/\.k-chip-geschlossen\s*{[^}]*border:\s*1px dashed/);
    expect(auraCss).toMatch(/\.k-chip-geschlossen\s*{[^}]*font-size:\s*var\(--k-t-xxs\)/);
    // Gegenprobe: die feinste Stufe IST 9px — der Chip wird also nicht
    // stillschweigend grösser, weil jemand den Token verschiebt.
    expect(auraCss).toMatch(/--k-t-xxs:\s*9px/);
  });
});

describe('KWerkzeugKreis (Spez §3 B-39, `field.tsx`): 32px-Kreis-Werkzeug', () => {
  it('rendert einen Button mit aria-pressed, aktiv=false per Default', () => {
    const html = renderToStaticMarkup(<KWerkzeugKreis data-testid="werkzeug-1">X</KWerkzeugKreis>);
    expect(html).toContain('k-werkzeug-kreis');
    expect(html).toContain('aria-pressed="false"');
    expect(html).not.toContain('k-werkzeug-kreis-punkt');
  });

  it('aktiv=true (ohne invertiert) trägt Rand+4px-Rollenpunkt', () => {
    const html = renderToStaticMarkup(
      <KWerkzeugKreis aktiv rolle="var(--k-rolle-agent)">
        X
      </KWerkzeugKreis>,
    );
    expect(html).toContain('k-werkzeug-kreis--aktiv');
    expect(html).toContain('k-werkzeug-kreis-punkt');
    expect(html).toMatch(/--_rolle:\s*var\(--k-rolle-agent\)/);
  });

  it('aktiv+invertiert zeigt die invertierte Fläche statt Punkt', () => {
    const html = renderToStaticMarkup(
      <KWerkzeugKreis aktiv invertiert>
        X
      </KWerkzeugKreis>,
    );
    expect(html).toContain('k-werkzeug-kreis--invertiert');
    expect(html).not.toContain('k-werkzeug-kreis-punkt');
  });

  it('aura.css: 32px-Kreis mit radius-pill', () => {
    expect(auraCss).toMatch(/\.k-werkzeug-kreis\s*{[^}]*width:\s*32px/);
    expect(auraCss).toMatch(/\.k-werkzeug-kreis\s*{[^}]*height:\s*32px/);
    expect(auraCss).toMatch(/\.k-werkzeug-kreis\s*{[^}]*border-radius:\s*var\(--k-radius-pill\)/);
  });
});

describe('KToolGruppe (Bestand, unverändert)', () => {
  it('rendert weiterhin k-toolgruppe + optionales Label', () => {
    const html = renderToStaticMarkup(
      <KToolGruppe label="ANSICHT">
        <span>Kind</span>
      </KToolGruppe>,
    );
    expect(html).toContain('k-toolgruppe');
    expect(html).toContain('k-toolgruppe-label');
    expect(html).toContain('ANSICHT');
  });
});
