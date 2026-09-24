import { describe, expect, it } from 'vitest';
import { VIS_INSELN, VIS_ISLAND_REIHENFOLGE, VIS_WERKZEUG_KATALOG } from '../src/modules/vis/island/vis-island-katalog';

/**
 * PC1 (`docs/V084-SPEZ.md` §5 W2, C-15/E1) — der Vis-Island-Katalog, gebaut
 * GEGEN die generische `InselKonfig`/`IslandWerkzeug`-Schnittstelle aus
 * `design/island/island-katalog.ts` (E1, W1). Eigene, additive Testdatei.
 *
 * v0.8.9 §9 E11 (PBL2, `docs/V089-SPEZ.md`): fünfte Insel SONNE (unten-
 * links, EIN Werkzeug `sonnenstunden`) additiv dazugekommen — die vier
 * Bestandsinseln/-Werkzeuge bleiben unverändert, nur die Gesamtzahlen ziehen
 * nach (13→14 Werkzeuge, 4→5 Inseln).
 *
 * v0.8.10 E3-Nachtrag (Owner-Entscheid 20.07.2026, `docs/V0810-SPEZ.md` §2
 * E3, Matrix C-6): der prominente Insel-Rückweg 'manuell' (AUSTAUSCH) ist
 * entfallen — 14→13 Werkzeuge total, AUSTAUSCH 5→4. (v0.9.25 P-M: auch der
 * damalige Ersatz-Zugang, der Einstellungs-Schalter, ist mitsamt der
 * manuellen Vis-Ansicht entfernt — K15 aufgehoben.)
 *
 * v0.8.11 P-B1/E4 (Owner-Wahl E-Vis, `docs/V0811-SPEZ.md` §2 E4, Matrix
 * C-6): additiv +2 — ANSICHT bekommt 'ansichten' (Gespeicherte Ansichten)
 * und 'legende' (Porttyp-Legende), die letzten beiden P-B1-Audit-Funde ohne
 * Insel-Äquivalent — 13→15 Werkzeuge total, ANSICHT 4→6.
 */

describe('vis-island-katalog — Aufbau', () => {
  it('fünf Inseln, Bühnenordnung links·oben·rechts·unten·sonne (v0.8.9: +SONNE)', () => {
    expect(VIS_ISLAND_REIHENFOLGE).toEqual(['graph', 'ansicht', 'stimmung', 'austausch', 'sonne']);
    expect(VIS_INSELN.map((k) => k.id)).toEqual(['graph', 'ansicht', 'stimmung', 'austausch', 'sonne']);
  });

  it('Orientierung + Randklasse folgen demselben Muster wie design (links/rechts vertikal, oben/unten horizontal); SONNE eigene Ecke', () => {
    const graph = VIS_INSELN.find((k) => k.id === 'graph')!;
    const ansicht = VIS_INSELN.find((k) => k.id === 'ansicht')!;
    const stimmung = VIS_INSELN.find((k) => k.id === 'stimmung')!;
    const austausch = VIS_INSELN.find((k) => k.id === 'austausch')!;
    const sonne = VIS_INSELN.find((k) => k.id === 'sonne')!;
    expect(graph.orientierung).toBe('vertikal');
    expect(graph.randKlasse).toBe('isl-rand-links');
    expect(ansicht.orientierung).toBe('horizontal');
    expect(ansicht.randKlasse).toBe('isl-rand-oben');
    expect(stimmung.orientierung).toBe('vertikal');
    expect(stimmung.randKlasse).toBe('isl-rand-rechts');
    expect(austausch.orientierung).toBe('horizontal');
    expect(austausch.randKlasse).toBe('isl-rand-unten');
    expect(sonne.orientierung).toBe('vertikal');
    // Eigene, additive Rand-Klasse (`vis-island.css`) — überlagert weder
    // `isl-rand-links` noch `isl-rand-unten` (s. Kopfkommentar dort).
    expect(sonne.randKlasse).toBe('isl-rand-sonne');
  });

  it('14 Werkzeuge total, jedes genau einer Insel zugeordnet (v0.8.11 P-B1/E4: +ansichten/+legende; K35: -minimap)', () => {
    expect(VIS_WERKZEUG_KATALOG).toHaveLength(14);
    const summe = VIS_INSELN.reduce((n, k) => n + k.werkzeuge.length, 0);
    expect(summe).toBe(14);
  });

  it('SONNE: genau EIN Werkzeug (Sonnenstunden, v0.8.9 §9 E11)', () => {
    const werkzeuge = VIS_INSELN.find((k) => k.id === 'sonne')!.werkzeuge;
    expect(werkzeuge.map((w) => w.id)).toEqual(['sonnenstunden']);
    expect(werkzeuge[0]!.hatPopup).toBe(true);
  });

  it('GRAPH: Node-Palette, Ausrichten, Verbinden (Owner-Auftrag §1)', () => {
    const ids = VIS_INSELN.find((k) => k.id === 'graph')!.werkzeuge.map((w) => w.id);
    expect(ids).toEqual(['palette', 'ausrichten', 'verbinden']);
  });

  it('ANSICHT: Zoom/Fit, Raster-Snap, Ortho/Kurve, Gespeicherte Ansichten, Legende (Owner-Auftrag §1 + v0.8.11 P-B1/E4; K35: -minimap)', () => {
    const ids = VIS_INSELN.find((k) => k.id === 'ansicht')!.werkzeuge.map((w) => w.id);
    expect(ids).toEqual(['zoom', 'raster', 'routing', 'ansichten', 'legende']);
  });

  it('STIMMUNG: genau EIN Werkzeug (die 3 Presets als Bild-Kacheln, Owner-Auftrag §1)', () => {
    const werkzeuge = VIS_INSELN.find((k) => k.id === 'stimmung')!.werkzeuge;
    expect(werkzeuge.map((w) => w.id)).toEqual(['stimmung']);
  });

  it('AUSTAUSCH: Render senden, Aufs Plakat, Kamera vorschlagen, Report (v0.8.10 E3-Nachtrag: -manuell, Owner-Auftrag §1)', () => {
    const ids = VIS_INSELN.find((k) => k.id === 'austausch')!.werkzeuge.map((w) => w.id);
    expect(ids).toEqual(['render-senden', 'aufs-plakat', 'kamera-vorschlagen', 'report']);
  });

  it('Raster/Routing/Kamera vorschlagen/Report sind hatPopup:false (Sofort-Aktion, Muster design achsen)', () => {
    for (const id of ['raster', 'routing', 'kamera-vorschlagen', 'report']) {
      const w = VIS_WERKZEUG_KATALOG.find((x) => x.id === id)!;
      expect(w.hatPopup).toBe(false);
    }
  });

  it('"manuell" ist kein Werkzeug mehr (v0.8.10 E3-Nachtrag: Zugang über Einstellungs-Schalter)', () => {
    expect(VIS_WERKZEUG_KATALOG.find((x) => x.id === 'manuell')).toBeUndefined();
  });

  it('"minimap" ist kein Werkzeug mehr (K35, Owner-Korrekturen 2026-07 S.14: «diese übersicht raus»)', () => {
    expect(VIS_WERKZEUG_KATALOG.find((x) => x.id === 'minimap')).toBeUndefined();
  });

  it('alle übrigen Werkzeuge haben hatPopup:true', () => {
    for (const id of [
      'palette',
      'ausrichten',
      'verbinden',
      'zoom',
      'stimmung',
      'render-senden',
      'aufs-plakat',
      'sonnenstunden',
      'ansichten',
      'legende',
    ]) {
      const w = VIS_WERKZEUG_KATALOG.find((x) => x.id === id)!;
      expect(w.hatPopup).toBe(true);
    }
  });

  it('kein Werkzeug trägt eine design-toolId (Vis hat keine Entsprechung)', () => {
    for (const w of VIS_WERKZEUG_KATALOG) {
      expect(w.toolId).toBeUndefined();
    }
  });

  it('jede Werkzeug-Id ist eindeutig (keine Doppelregistrierung möglich)', () => {
    const ids = VIS_WERKZEUG_KATALOG.map((w) => w.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});
