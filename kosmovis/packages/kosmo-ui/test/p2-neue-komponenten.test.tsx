// @vitest-environment jsdom
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { KCard } from '../src/card';
import { KHud, KStatuszeile } from '../src/hud';
import { KKeyValue } from '../src/keyvalue';
import { KPipelineNode } from '../src/node';
import { KPill } from '../src/pill';
import { KSwitch } from '../src/switch';
import { KVariantenKarte } from '../src/variantenkarte';

/**
 * v0.8.0B / P2 (Spez §3) — Regressionsschutz für die sechs neuen
 * Komponenten (+ die matrixseitig additiven KCard/KSwitch, §9.14 B-126/
 * B-127). Muster wie `komponenten.test.tsx`: `renderToStaticMarkup` für
 * reine Struktur-/Klassen-Checks (keine Interaktion nötig).
 */

describe('KPill (Spez §3 B-40)', () => {
  it('rendert Kinder + 6px-Dot bei dot=true, k-pill-Basisklasse', () => {
    const html = renderToStaticMarkup(
      <KPill rolle="agent" dot data-testid="pill-1">
        KI-AGENT
      </KPill>,
    );
    expect(html).toContain('KI-AGENT');
    expect(html).toContain('k-pill');
    expect(html).toContain('k-pill-punkt');
    expect(html).toContain('data-testid="pill-1"');
  });

  it('solid=true trägt k-pill--solid', () => {
    const html = renderToStaticMarkup(<KPill solid>SYSTEM</KPill>);
    expect(html).toContain('k-pill--solid');
  });

  it('Default-Rolle ist neutral, setzt --_farbe/--_fill/--_linie als Inline-Style', () => {
    const html = renderToStaticMarkup(<KPill>NEUTRAL</KPill>);
    expect(html).toMatch(/--_farbe:\s*var\(--k-ink-faint\)/);
  });
});

describe('KKeyValue (Spez §3 B-41)', () => {
  it('rendert eine Zeile je Eintrag mit Key/Wert', () => {
    const html = renderToStaticMarkup(
      <KKeyValue
        zeilen={[
          { key: 'ANSICHT', wert: 'Perspektive' },
          { key: 'EINHEIT', wert: 'Meter', testid: 'kv-einheit' },
        ]}
      />,
    );
    expect(html).toContain('k-keyvalue');
    expect(html).toContain('ANSICHT');
    expect(html).toContain('Perspektive');
    expect(html).toContain('data-testid="kv-einheit"');
  });

  it('optionaler Fortschrittsbalken rendert Breite als Prozent', () => {
    const html = renderToStaticMarkup(<KKeyValue zeilen={[{ key: 'FORTSCHRITT', wert: '60%', fortschritt: 0.6 }]} />);
    expect(html).toContain('k-keyvalue-fortschritt-balken');
    expect(html).toMatch(/width:\s*60%/);
  });
});

describe('KHud + KStatuszeile (Spez §3 B-42/B-43)', () => {
  it('KHud rendert Mono-Titel mit vorangestelltem ● und trägt k-glass', () => {
    const html = renderToStaticMarkup(
      <KHud titel="Viewport" data-testid="hud-1">
        Inhalt
      </KHud>,
    );
    expect(html).toContain('k-hud');
    expect(html).toContain('k-glass');
    expect(html).toContain('●');
    expect(html).toContain('Viewport');
    expect(html).toContain('Inhalt');
  });

  it('KStatuszeile rendert links/rechts-Slots in getrennten Containern', () => {
    const html = renderToStaticMarkup(<KStatuszeile links={<span>Core verbunden</span>} rechts={<span>GPU 42%</span>} />);
    expect(html).toContain('k-statuszeile');
    expect(html).toContain('Core verbunden');
    expect(html).toContain('GPU 42%');
  });
});

describe('KPipelineNode (Spez §3 B-44)', () => {
  it('rendert Rollen-Pill, Titel, Beschreibung und drei Ports', () => {
    const html = renderToStaticMarkup(<KPipelineNode rolle="agent" titel="Fassadengenerator" beschreibung="Erzeugt Varianten" />);
    expect(html).toContain('k-node');
    expect(html).toContain('KI-AGENT');
    expect(html).toContain('Fassadengenerator');
    expect(html).toContain('Erzeugt Varianten');
    expect(html).toMatch(/k-node-port k-node-port--gefuellt/);
  });

  it('status=laeuft trägt k-node--laeuft + k-node--aktiv (Puls, Gesetz 7)', () => {
    const html = renderToStaticMarkup(<KPipelineNode titel="Render" status="laeuft" />);
    expect(html).toContain('k-node--laeuft');
    expect(html).toContain('k-node--aktiv');
  });

  it('ports=false unterdrückt die Port-Punkte', () => {
    const html = renderToStaticMarkup(<KPipelineNode titel="Ohne Ports" ports={false} />);
    expect(html).not.toContain('k-node-ports');
  });
});

describe('KVariantenKarte (Spez §3 B-45)', () => {
  it('zeigt die ID-Pill, aber KEIN Badge ohne laeuft/favorit', () => {
    const html = renderToStaticMarkup(<KVariantenKarte id="V-04" />);
    expect(html).toContain('k-variantenkarte-id');
    expect(html).toContain('V-04');
    expect(html).not.toContain('k-variantenkarte-badge');
  });

  it('laeuft=true zeigt RENDERT-Badge + Scan-Streifen; favorit tritt zurück', () => {
    const html = renderToStaticMarkup(<KVariantenKarte id="V-01" laeuft favorit />);
    expect(html).toContain('RENDERT');
    expect(html).not.toContain('FAVORIT');
    expect(html).toContain('k-variantenkarte-scan');
  });

  it('favorit=true (ohne laeuft) zeigt FAVORIT-Badge, kein Scan', () => {
    const html = renderToStaticMarkup(<KVariantenKarte id="V-02" favorit />);
    expect(html).toContain('FAVORIT');
    expect(html).not.toContain('k-variantenkarte-scan');
  });

  it('gewaehlt=true trägt k-variantenkarte--gewaehlt', () => {
    const html = renderToStaticMarkup(<KVariantenKarte id="V-03" gewaehlt />);
    expect(html).toContain('k-variantenkarte--gewaehlt');
  });

  it('onVerwerfen/onInsProjekt rendern die zwei Aktions-Knöpfe', () => {
    const html = renderToStaticMarkup(<KVariantenKarte id="V-05" onVerwerfen={() => {}} onInsProjekt={() => {}} />);
    expect(html).toContain('Verwerfen');
    expect(html).toContain('Ins Projekt');
  });
});

describe('KCard (Spez §9.14 B-126, additiv)', () => {
  it('Default solid, kein Rollenakzent ohne rolle-Prop', () => {
    const html = renderToStaticMarkup(<KCard data-testid="card-1">Inhalt</KCard>);
    expect(html).toContain('k-card k-card--solid');
    expect(html).not.toContain('k-card-akzent');
  });

  it('rolle-Prop rendert den 2px-Hairline-Akzent', () => {
    const html = renderToStaticMarkup(<KCard rolle="agent">Inhalt</KCard>);
    expect(html).toContain('k-card-akzent');
  });

  it('variante=glass/sunken + interaktiv/aktiv setzen die erwarteten Klassen', () => {
    const html = renderToStaticMarkup(
      <KCard variante="glass" interaktiv aktiv>
        Inhalt
      </KCard>,
    );
    expect(html).toContain('k-card--glass');
    expect(html).toContain('k-card--interaktiv');
    expect(html).toContain('k-card--aktiv');
  });
});

describe('KSwitch (Spez §9.14 B-127, additiv)', () => {
  it('rendert ein natives checkbox-Input + Label', () => {
    const html = renderToStaticMarkup(<KSwitch label="Motion" data-testid="switch-1" />);
    expect(html).toContain('type="checkbox"');
    expect(html).toContain('k-switch');
    expect(html).toContain('Motion');
    expect(html).toContain('data-testid="switch-1"');
  });

  it('checked=true reicht das native Attribut durch', () => {
    const html = renderToStaticMarkup(<KSwitch checked onChange={() => {}} />);
    expect(html).toMatch(/type="checkbox"[^>]*checked=""/);
  });
});
