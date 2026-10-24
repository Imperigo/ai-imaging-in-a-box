import { describe, expect, it } from 'vitest';
import {
  kamerasAbweichend,
  modusAus,
  modusFuerKamera,
  modusMarkeArt,
  modusTooltip,
  modusZusatz,
  modusZusatzzeile,
  type ModusVermerk,
} from '../src/modules/vis/modus-marke';

const SATZ = 'KI-BILD OHNE GRUNDLAGENBILD: Bestellt war «Bild bearbeiten», das Vorgabemodell hat keinen Bildeingang.';

describe('modus-marke: Tabelle vom Blatt', () => {
  it('abweichung true, bestellt mit Bildeingang, gerechnet txt2img: Ohne Grundlagenbild, Satz und Werte im Tooltip', () => {
    const v: ModusVermerk = { bestellt: 'image_edit', gerechnet: 'txt2img', abweichung: true, satz: SATZ };
    expect(modusMarkeArt(v)).toBe('ohne-grundlagenbild');
    expect(modusTooltip(v)).toBe(`${SATZ}\nBestellt: Bild bearbeiten · gerechnet: nur aus dem Text`);
    expect(modusZusatz(v)).toBe(', ohne Grundlagenbild');
  });
  it('Form, die KosmoVis beim Satz ohne Werte liefert: Ohne Grundlagenbild, Tooltip ist der Satz', () => {
    const v = modusAus({ modus: { bestellt: null, gerechnet: null, abweichung: true, satz: SATZ.toLowerCase() } });
    expect(modusMarkeArt(v)).toBe('ohne-grundlagenbild');
    expect(modusTooltip(v)).toBe(SATZ.toLowerCase());
  });
  it('kein Rueckfall auf hinweise: ohne modus-Feld kein Vermerk, auch wenn der Satz da steht', () => {
    expect(modusAus({ hinweise: [SATZ] })).toBeUndefined();
    expect(modusAus({ qa: { verdict: { hinweise: [SATZ] } } })).toBeUndefined();
    expect(modusMarkeArt(modusAus({ hinweise: [SATZ] }))).toBeNull();
  });
  it('abweichung true, andere Paarung: Anders gerechnet', () => {
    const v: ModusVermerk = { bestellt: 'bild_und_tiefe', gerechnet: 'tiefe_als_bild', abweichung: true };
    expect(modusMarkeArt(v)).toBe('anders-gerechnet');
    expect(modusTooltip(v)).toBe('Bestellt: Bild und Tiefe · gerechnet: Tiefe als Bild');
    expect(modusZusatz(v)).toBe(', anders gerechnet');
  });
  it('bestellt txt2img und gerechnet txt2img mit abweichung true ist nie Ohne Grundlagenbild', () => {
    expect(modusMarkeArt({ bestellt: 'txt2img', gerechnet: 'txt2img', abweichung: true })).toBe('anders-gerechnet');
    expect(modusMarkeArt({ bestellt: null, gerechnet: 'txt2img', abweichung: true })).toBe('anders-gerechnet');
  });
  it('ohne Satz und ohne Werte: Standardsätze', () => {
    expect(modusTooltip({ bestellt: null, gerechnet: null, abweichung: true })).toBe('Das Bild wurde anders gerechnet als bestellt.');
    expect(modusTooltip({ bestellt: null, gerechnet: null, abweichung: true, kameras: { A: { gerechnet: null, abweichung: true, satz: SATZ.slice(0, 27) } } }, 'A')).toBe(
      SATZ.slice(0, 27),
    );
    const k: ModusVermerk = { bestellt: null, gerechnet: null, abweichung: null, kameras: { A: { gerechnet: null, abweichung: true } } };
    expect(modusTooltip(k, 'A')).toBe('Das Bild wurde anders gerechnet als bestellt.');
  });
  it('unbekannte Rohwerte bleiben roh', () => {
    expect(modusTooltip({ bestellt: 'xyz', gerechnet: 'abc', abweichung: true })).toBe('Bestellt: xyz · gerechnet: abc');
  });
  it('abweichung null: nicht gemeldet, nie wie false und keine Plakette-Art', () => {
    const v = modusAus({ modus: { bestellt: 'image_edit', gerechnet: null, abweichung: null } });
    expect(modusMarkeArt(v)).toBe('nicht-gemeldet');
    expect(modusMarkeArt(v)).not.toBeNull();
    expect(modusZusatz(v)).toBe('');
    expect(modusTooltip(v)).toContain('Das heisst nicht, dass es wie bestellt gerechnet hat.');
  });
  it('abweichung false oder kein Feld: nichts', () => {
    expect(modusMarkeArt(modusAus({ modus: { bestellt: 'a', gerechnet: 'a', abweichung: false } }))).toBeNull();
    expect(modusMarkeArt(modusAus({ status: 'fertig' }))).toBeNull();
    expect(modusMarkeArt(undefined)).toBeNull();
    expect(modusTooltip(undefined)).toBe('');
  });
  it('eine Ursache, eine Marke: Werte und Satz zugleich ergeben genau eine Art', () => {
    const v = modusAus({ modus: { bestellt: 'image_edit', gerechnet: 'txt2img', abweichung: true, satz: SATZ } });
    expect(modusMarkeArt(v)).toBe('ohne-grundlagenbild');
  });
});

describe('modus-marke: Kameras', () => {
  const v: ModusVermerk = {
    bestellt: 'image_edit',
    gerechnet: null,
    abweichung: null,
    kameras: {
      Nord: { gerechnet: 'image_edit', abweichung: false },
      Ost: { gerechnet: 'txt2img', abweichung: true },
      Sued: { gerechnet: 'image_edit', abweichung: false },
    },
  };
  it('Kamera-Eintrag gilt vor dem Ganzen', () => {
    expect(modusMarkeArt(v, 'Ost')).toBe('ohne-grundlagenbild');
    expect(modusMarkeArt(v, 'Nord')).toBeNull();
    expect(modusMarkeArt(v)).toBe('nicht-gemeldet');
    expect(modusMarkeArt(v, 'Unbekannt')).toBe('nicht-gemeldet');
    expect(modusTooltip(v, 'Ost')).toBe('Bestellt: Bild bearbeiten · gerechnet: nur aus dem Text');
    expect(modusZusatz(v, 'Ost')).toBe(', ohne Grundlagenbild');
  });
  it('Kamera mit Satz: Satz gilt', () => {
    const w: ModusVermerk = { bestellt: null, gerechnet: null, abweichung: null, kameras: { A: { gerechnet: null, abweichung: true, satz: SATZ } } };
    expect(modusMarkeArt(w, 'A')).toBe('ohne-grundlagenbild');
  });
  it('kamerasAbweichend und Zusatzzeile', () => {
    expect(kamerasAbweichend(v)).toEqual(['Ost']);
    expect(modusZusatzzeile(v)).toBe('1 von 3 Kameras ohne Grundlagenbild gerechnet (Ost)');
    const anders: ModusVermerk = { ...v, kameras: { A: { gerechnet: 'x', abweichung: true }, B: { gerechnet: 'y', abweichung: false } } };
    expect(modusZusatzzeile(anders)).toBe('1 von 2 Kameras anders gerechnet (A)');
  });
  it('Zusatzzeile nur bei gerechnet null, mehreren Kameras und einer Abweichung', () => {
    expect(modusZusatzzeile({ ...v, gerechnet: 'image_edit' })).toBeNull();
    expect(modusZusatzzeile({ ...v, kameras: { Ost: { gerechnet: 'txt2img', abweichung: true } } })).toBeNull();
    expect(modusZusatzzeile({ ...v, kameras: { A: { gerechnet: null, abweichung: false }, B: { gerechnet: null, abweichung: null } } })).toBeNull();
    expect(modusZusatzzeile(undefined)).toBeNull();
    expect(modusZusatzzeile({ bestellt: null, gerechnet: null, abweichung: null })).toBeNull();
  });
});

describe('modus-marke: kaputte Formen werfen nie', () => {
  it.each([null, undefined, 3, 'x', [], { modus: 5 }, { modus: 'x' }, { modus: [] }, { hinweise: 'x' }, { hinweise: [1, null] }, { qa: 5 }, { qa: { verdict: 7 } }])(
    'modusAus(%j) gibt undefined',
    (x) => {
      expect(() => modusAus(x)).not.toThrow();
      expect(modusAus(x)).toBeUndefined();
    },
  );
  it('falsch getypte Felder werden zu null, kaputte Kameras fallen weg', () => {
    const v = modusAus({ modus: { bestellt: 5, gerechnet: '', abweichung: 'ja', satz: 3, kameras: { A: 'x', B: { gerechnet: 1, abweichung: 'true' }, C: null } } });
    expect(v).toEqual({ bestellt: null, gerechnet: null, abweichung: null, kameras: { B: { gerechnet: null, abweichung: null } } });
    expect(modusMarkeArt(v, 'B')).toBe('nicht-gemeldet');
  });
  it('modusFuerKamera: Angabe der Kamera allein; fehlt sie im Verzeichnis, kein Vermerk; ohne Verzeichnis das Ganze', () => {
    const v: ModusVermerk = { bestellt: 'image_edit', gerechnet: null, abweichung: true, kameras: { Ost: { gerechnet: 'txt2img', abweichung: true }, West: { gerechnet: 'image_edit', abweichung: false } } };
    expect(modusMarkeArt(modusFuerKamera(v, ['Ost']))).toBe('ohne-grundlagenbild');
    expect(modusMarkeArt(modusFuerKamera(v, ['x', 'West']))).toBeNull();
    expect(modusFuerKamera(v, ['Nord'])).toBeUndefined();
    const ganz = { bestellt: 'image_edit', gerechnet: 'txt2img', abweichung: true } as const;
    expect(modusFuerKamera(ganz, ['Nord'])).toBe(ganz);
    expect(modusFuerKamera(undefined, ['Ost'])).toBeUndefined();
  });
});
