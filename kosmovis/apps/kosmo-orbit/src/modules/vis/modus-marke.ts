/**
 * Rechenweg-Vermerk am Bild: «Ohne Grundlagenbild» / «Anders gerechnet» (Blatt vom 21.10.2026).
 * Reine Logik, ohne bpy und ohne React. Gelesen wird NUR, was der Lauf meldet: `NodeLauf.modus` (KosmoVis fuellt
 * es aus `angewandt.modus` bzw. dem Hinweissatz; ein Rueckfall auf `hinweise` steht hier bewusst nicht).
 * Eine Ursache, eine Marke: «Ohne Grundlagenbild» ist der Sonderfall von «anders gerechnet» und ersetzt es.
 * `abweichung: null` heisst «nicht gemeldet» und wird nie wie `false` («wie bestellt») gezeigt.
 */
import type { LaufModus, LaufModusKamera } from './modus';

export type ModusKamera = LaufModusKamera;
/** Dieselbe Form wie `NodeLauf.modus` (`LaufModus`), nicht neu erfunden. */
export type ModusVermerk = LaufModus;
export type ModusMarkeArt = 'ohne-grundlagenbild' | 'anders-gerechnet' | 'nicht-gemeldet';

export const MODUS_MARKE_TEXT: Record<'ohne-grundlagenbild' | 'anders-gerechnet', string> = {
  'ohne-grundlagenbild': 'Ohne Grundlagenbild',
  'anders-gerechnet': 'Anders gerechnet',
};
export const MODUS_NICHT_GEMELDET_TEXT = 'Rechenweg nicht gemeldet';
export const MODUS_NICHT_GEMELDET_HINWEIS =
  'Das Bildmodell hat nicht gemeldet, wie es gerechnet hat. Das heisst nicht, dass es wie bestellt gerechnet hat.';

const SATZ_ANFANG = 'KI-BILD OHNE GRUNDLAGENBILD';
const ROH_TEXT: Record<string, string> = {
  txt2img: 'nur aus dem Text',
  image_edit: 'Bild bearbeiten',
  tiefe_als_bild: 'Tiefe als Bild',
  bild_und_tiefe: 'Bild und Tiefe',
};

const istObjekt = (x: unknown): x is Record<string, unknown> => typeof x === 'object' && x !== null && !Array.isArray(x);
const textOderNull = (x: unknown): string | null => (typeof x === 'string' && x.trim() !== '' ? x : null);
const jaNeinNull = (x: unknown): boolean | null => (typeof x === 'boolean' ? x : null);
const beginntMitOhneBild = (s: string | undefined): boolean => typeof s === 'string' && s.trim().toUpperCase().startsWith(SATZ_ANFANG);

/** Liest `modus` vom Lauf (oder Verlaufseintrag, Kuratier-Quelle). Ohne `modus` kein Vermerk. */
export function modusAus(lauf: unknown): ModusVermerk | undefined {
  try {
    if (!istObjekt(lauf)) return undefined;
    const m = lauf['modus'];
    if (istObjekt(m)) {
      const v: ModusVermerk = {
        bestellt: textOderNull(m['bestellt']),
        gerechnet: textOderNull(m['gerechnet']),
        abweichung: jaNeinNull(m['abweichung']),
      };
      const satz = textOderNull(m['satz']);
      if (satz) v.satz = satz;
      const k = m['kameras'];
      if (istObjekt(k)) {
        const kameras: Record<string, ModusKamera> = {};
        for (const [name, e] of Object.entries(k)) {
          if (!istObjekt(e)) continue;
          const ke: ModusKamera = { gerechnet: textOderNull(e['gerechnet']), abweichung: jaNeinNull(e['abweichung']) };
          const ks = textOderNull(e['satz']);
          if (ks) ke.satz = ks;
          kameras[name] = ke;
        }
        if (Object.keys(kameras).length > 0) v.kameras = kameras;
      }
      return v;
    }
    return undefined;
  } catch {
    return undefined;
  }
}

type Sicht = { gerechnet: string | null; abweichung: boolean | null; satz?: string | undefined; bestellt: string | null };
function sicht(v: ModusVermerk, kamera?: string): Sicht {
  const k = kamera !== undefined ? v.kameras?.[kamera] : undefined;
  if (k) return { bestellt: v.bestellt, gerechnet: k.gerechnet, abweichung: k.abweichung, satz: k.satz };
  return { bestellt: v.bestellt, gerechnet: v.gerechnet, abweichung: v.abweichung, satz: v.satz };
}

export function modusMarkeArt(v: ModusVermerk | undefined, kamera?: string): ModusMarkeArt | null {
  if (!v) return null;
  const s = sicht(v, kamera);
  if (s.abweichung === null) return 'nicht-gemeldet';
  if (s.abweichung !== true) return null;
  const mitBildeingang = s.bestellt !== null && s.bestellt !== 'txt2img';
  if ((s.gerechnet === 'txt2img' && mitBildeingang) || beginntMitOhneBild(s.satz)) return 'ohne-grundlagenbild';
  return 'anders-gerechnet';
}

const roh = (x: string): string => ROH_TEXT[x] ?? x;

export function modusTooltip(v: ModusVermerk | undefined, kamera?: string): string {
  const art = modusMarkeArt(v, kamera);
  if (!v || art === null) return '';
  if (art === 'nicht-gemeldet') return MODUS_NICHT_GEMELDET_HINWEIS;
  const s = sicht(v, kamera);
  const zeilen: string[] = [];
  if (s.satz) zeilen.push(s.satz);
  if (s.bestellt !== null && s.gerechnet !== null) zeilen.push(`Bestellt: ${roh(s.bestellt)} · gerechnet: ${roh(s.gerechnet)}`);
  if (zeilen.length === 0) {
    zeilen.push(art === 'ohne-grundlagenbild' ? 'Das Bildmodell hatte keinen Bildeingang und hat nur aus dem Text gerechnet.' : 'Das Bild wurde anders gerechnet als bestellt.');
  }
  return zeilen.join('\n');
}

/** Zusatz für Knopfnamen und Alternativtexte. */
export function modusZusatz(v: ModusVermerk | undefined, kamera?: string): string {
  const art = modusMarkeArt(v, kamera);
  if (art === 'ohne-grundlagenbild') return ', ohne Grundlagenbild';
  if (art === 'anders-gerechnet') return ', anders gerechnet';
  return '';
}

export function kamerasAbweichend(v: ModusVermerk | undefined): string[] {
  if (!v?.kameras) return [];
  return Object.entries(v.kameras)
    .filter(([, k]) => k.abweichung === true)
    .map(([name]) => name);
}

/** «1 von 3 Kameras ohne Grundlagenbild gerechnet (Ost)»: nur wenn das Ganze nichts meldet und die Kameras sich unterscheiden. */
export function modusZusatzzeile(v: ModusVermerk | undefined): string | null {
  if (!v || v.gerechnet !== null || !v.kameras) return null;
  const alle = Object.keys(v.kameras);
  if (alle.length <= 1) return null;
  const ab = kamerasAbweichend(v);
  if (ab.length === 0) return null;
  const ohneBild = ab.every((n) => modusMarkeArt(v, n) === 'ohne-grundlagenbild');
  const wie = ohneBild ? 'ohne Grundlagenbild' : 'anders';
  return `${ab.length} von ${alle.length} Kameras ${wie} gerechnet (${ab.join(', ')})`;
}

/**
 * Der Vermerk fuer EIN Bild einer Kamera (Varianten-Zelle): ohne Verzeichnis je Kamera gilt der Vermerk des
 * Ganzen; hat der Lauf eines und kennt eine der `namen` (Standpunktname, Kuerzel), gilt deren Angabe allein.
 * Kennt er keine davon, gibt es keinen Vermerk, sonst truege das Bild die Marke einer anderen Kamera.
 */
export function modusFuerKamera(v: ModusVermerk | undefined, namen: readonly string[]): ModusVermerk | undefined {
  if (!v?.kameras) return v;
  const treffer = namen.find((n) => v.kameras?.[n] !== undefined);
  const k = treffer !== undefined ? v.kameras[treffer] : undefined;
  if (!k) return undefined;
  const aus: ModusVermerk = { bestellt: v.bestellt, gerechnet: k.gerechnet, abweichung: k.abweichung };
  if (k.satz) aus.satz = k.satz;
  return aus;
}
