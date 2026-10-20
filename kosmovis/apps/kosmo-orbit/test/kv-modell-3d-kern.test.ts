// @vitest-environment jsdom
import { describe, expect, it } from 'vitest';
import {
  KEGEL_SEITENVERHAELTNIS,
  PIXELDICHTE_OBERGRENZE,
  PIXELDICHTE_UNTERGRENZE,
  erzeugeModellVorschau3d,
  kegelLaenge,
  kegelLinien,
  pixeldichte,
  rahmeHuellbox,
  type Vec3,
} from '../src/modules/vis/modell-vorschau-3d-kern';

/**
 * Kleines 3D-Fenster, der Kern (Bauplan «Neue Knoten» 20.10.2026, gemeinsamer Baustein;
 * Entscheid 109). Geprüft wird, was ohne Grafikkarte geht: der Rückfall ohne WebGL und die
 * drei reinen Rechnungen (Rahmen, Kegel, Pixeldichte). Ob das Bild in einem echten Browser
 * erscheint, sagt diese Probe nicht — das misst die e2e-Probe mit dem Einbau (F1).
 */

const GRAD = Math.PI / 180;
const ab = (a: Vec3, b: Vec3): Vec3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const len = (v: Vec3) => Math.hypot(v[0], v[1], v[2]);
const punkt = (f: Float32Array, i: number): Vec3 => [f[i * 3]!, f[i * 3 + 1]!, f[i * 3 + 2]!];

describe('Kern ohne WebGL', () => {
  it('gibt null zurück, statt zu werfen (jsdom hat keinen Zeichenkontext)', () => {
    const canvas = document.createElement('canvas');
    const fenster = erzeugeModellVorschau3d({ canvas, pixeldichte: 1, breite: 248, hoehe: 140 });
    expect(fenster).toBeNull();
  });
});

describe('rahmeHuellbox — Rahmen auf die Hüllbox', () => {
  const box = { min: [-5, 0, -4] as Vec3, max: [5, 9, 4] as Vec3 };

  it('zielt auf die Mitte der Box und steht oberhalb (Y oben, wie glb)', () => {
    const a = rahmeHuellbox(box, 35, 248 / 140);
    expect(a.target).toEqual([0, 4.5, 0]);
    expect(a.position[1]).toBeGreaterThan(a.target[1]);
  });

  it('die Kugel um die Box passt in die engere Richtung, mit Luft', () => {
    const radius = len(ab(box.max, box.min)) / 2;
    for (const asp of [248 / 140, 1, 0.5]) {
      const a = rahmeHuellbox(box, 35, asp);
      const d = len(ab(a.position, a.target));
      const fovV = 35 * GRAD;
      const fovH = 2 * Math.atan(Math.tan(fovV / 2) * asp);
      const halb = Math.min(fovV, fovH) / 2;
      // Winkel, unter dem die Kugel erscheint, liegt innerhalb des halben Blickfelds.
      expect(Math.asin(radius / d)).toBeLessThan(halb);
      expect(Math.asin(radius / d)).toBeGreaterThan(halb * 0.8);
      expect(a.near).toBeLessThan(d - radius);
      expect(a.far).toBeGreaterThan(d + radius);
    }
  });

  it('ein hohes, schmales Fenster steht weiter weg als ein breites', () => {
    const breit = rahmeHuellbox(box, 35, 2);
    const schmal = rahmeHuellbox(box, 35, 0.5);
    expect(len(ab(schmal.position, schmal.target))).toBeGreaterThan(len(ab(breit.position, breit.target)));
  });

  it('eine leere oder kaputte Box ergibt einen ruhigen Würfel um den Nullpunkt', () => {
    const a = rahmeHuellbox({ min: [Number.NaN, 0, 0], max: [1, 1, 1] });
    expect(a.target).toEqual([0, 0, 0]);
    expect(a.position.every(Number.isFinite)).toBe(true);
    const verkehrt = rahmeHuellbox({ min: [2, 2, 2], max: [1, 1, 1] });
    expect(verkehrt.target).toEqual([0, 0, 0]);
  });
});

describe('kegelLinien — Kameras als Linien-Pyramide', () => {
  const kamera = { position: [0, 1.6, 20] as Vec3, target: [0, 1.6, 0] as Vec3, fov: 60 };

  it('zehn Linien: vier zur Spitze, vier Grundkanten, zwei für «oben»', () => {
    const f = kegelLinien(kamera, 2)!;
    expect(f).toHaveLength(60);
    for (const i of [0, 2, 4, 6]) expect(punkt(f, i)).toEqual([0, 1.6, 20].map(Math.fround));
  });

  it('Grundfläche in Blickrichtung, so breit wie das waagrechte Blickfeld', () => {
    const L = 2;
    const f = kegelLinien(kamera, L)!;
    const ol = punkt(f, 1);
    const or = punkt(f, 3);
    const ur = punkt(f, 5);
    // In Blickrichtung (hier -Z) um L vor dem Standpunkt.
    expect(ol[2]).toBeCloseTo(20 - L, 5);
    // Breite = 2 L tan(fov/2); Höhe = Breite / Seitenverhältnis.
    expect(len(ab(or, ol))).toBeCloseTo(2 * L * Math.tan(30 * GRAD), 5);
    expect(len(ab(or, ur))).toBeCloseTo((2 * L * Math.tan(30 * GRAD)) / KEGEL_SEITENVERHAELTNIS, 5);
    // Oben ist oben: die Oberkante liegt höher als die Unterkante (Senkrechte gerade).
    expect(or[1]).toBeGreaterThan(ur[1]);
    expect(or[0]).toBeCloseTo(ur[0], 5);
    // Der Giebel steht über der Oberkante.
    const giebel = punkt(f, 17);
    expect(giebel[1]).toBeGreaterThan(ol[1]);
  });

  it('der senkrechte Winkel geht vor, wenn er bekannt ist', () => {
    const f = kegelLinien({ ...kamera, fov: 90, fovVertikalGrad: 40, seitenverhaeltnis: 2 }, 1)!;
    const or = punkt(f, 3);
    const ur = punkt(f, 5);
    const ol = punkt(f, 1);
    expect(len(ab(or, ur))).toBeCloseTo(2 * Math.tan(20 * GRAD), 5);
    expect(len(ab(or, ol))).toBeCloseTo(4 * Math.tan(20 * GRAD), 5);
  });

  it('senkrecht nach unten: kein Bruch, endliche Punkte', () => {
    const f = kegelLinien({ position: [0, 30, 0], target: [0, 0, 0], fov: 50 }, 3)!;
    expect(Array.from(f).every(Number.isFinite)).toBe(true);
    expect(punkt(f, 1)[1]).toBeCloseTo(27, 5);
  });

  it('Standpunkt gleich Ziel oder fehlende Zahlen: kein Kegel', () => {
    expect(kegelLinien({ position: [1, 1, 1], target: [1, 1, 1], fov: 50 }, 1)).toBeNull();
    expect(kegelLinien({ position: [Number.NaN, 1, 1], target: [0, 0, 0], fov: 50 }, 1)).toBeNull();
    expect(kegelLinien(kamera, 0)).toBeNull();
  });

  it('Kegellänge folgt der Modellgrösse', () => {
    expect(kegelLaenge({ min: [0, 0, 0], max: [30, 0, 40] })).toBeCloseTo(10);
    expect(kegelLaenge({ min: [0, 0, 0], max: [0, 0, 0] })).toBe(1);
  });
});

describe('pixeldichte — Bildschirmdichte mal Knotenzoom, begrenzt', () => {
  it('rechnet DPR × Zoom', () => {
    expect(pixeldichte(1, 1.5)).toBe(1.5);
    expect(pixeldichte(2, 0.5)).toBe(1);
  });
  it('nach oben und unten begrenzt', () => {
    expect(pixeldichte(2, 3)).toBe(PIXELDICHTE_OBERGRENZE);
    expect(pixeldichte(1, 0.1)).toBe(PIXELDICHTE_UNTERGRENZE);
    expect(pixeldichte(3, 1, 1.25)).toBe(1.25);
  });
  it('kaputte Eingaben gelten als 1', () => {
    expect(pixeldichte(Number.NaN, Number.NaN)).toBe(1);
    expect(pixeldichte(0, -2)).toBe(1);
  });
});
