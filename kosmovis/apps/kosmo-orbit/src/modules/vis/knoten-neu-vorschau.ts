import type { VisStimmungId } from '@kosmo/kernel';

/**
 * Bauplan «Neue Knoten» (Blätter 32/33 der Entwurfsfläche): was die Knoten Stimmung und Material
 * zeigen, solange die Vorschaubilder nicht ausgeliefert sind.
 *
 * **Warum ohne Bilder:** Die Himmelsbilder (Poly Haven) und Texturen (ambientCG) sind CC0
 * (Entscheid 107) und liegen am Heim-PC. Verkleinerte Vorschauen sind zugelassen (Entscheid 113 (1)),
 * aber noch nicht geliefert (Schritt W: die HomeStation legt sie an, mit Quelle und Prüfsumme im
 * NOTICE). Bis dahin zeigt der Knoten den Farbverlauf des Blatts — gezeichnet, nicht fotografiert,
 * und so beschriftet.
 *
 * **Wenn die Bilder kommen:** Name in `VORSCHAUBILDER` eintragen (Pfad unter `public/`, wird in beiden
 * Programmen ausgeliefert); der Knoten zeigt dann das Bild über dem Verlauf. Nichts sonst ändert sich.
 */

/** Verlauf oben → unten je Stimmung (Blatt 32). */
export const STIMMUNG_VERLAUF: Record<VisStimmungId, readonly [string, string]> = {
  morgen: ['#f6d9a8', '#9fc3e6'],
  mittag: ['#eaf2fb', '#7fb0e0'],
  abend: ['#f3a96b', '#5b6f9a'],
  'blaue-stunde': ['#2c3e66', '#8aa0c8'],
  bedeckt: ['#cfd3d8', '#9aa1ab'],
  nebel: ['#e6e8ea', '#c3c8ce'],
  winter: ['#f1f5f9', '#b8c9da'],
  weiss: ['#ffffff', '#e9e9e9'],
};

/** Ausgelieferte Vorschaubilder (Schritt W), Pfad relativ zur Seite. Heute keine. */
export const VORSCHAUBILDER: { stimmungen: Partial<Record<VisStimmungId, string>>; materialien: Partial<Record<string, string>> } = {
  stimmungen: {},
  materialien: {},
};

/** Der Satz unter einem gezeichneten Verlauf — damit niemand ihn für das Himmelsbild hält. */
export const VERLAUF_SATZ = 'Farbverlauf — das Himmelsbild liegt am Heim-PC';

/** Wie eine Oberfläche in der Vorschau aussieht (Fläche): grob nach Stoff. */
export type MaterialMuster = 'beton' | 'holz' | 'ziegel' | 'stein' | 'putz' | 'latten' | 'platte' | 'lehm';

export const MATERIAL_MUSTER: Record<string, MaterialMuster> = {
  'sichtbeton-sandgestrahlt': 'beton',
  'sichtbeton-schalungsglatt': 'beton',
  fichte: 'holz',
  backstein: 'ziegel',
  klinker: 'ziegel',
  sandstein: 'stein',
  stampflehm: 'lehm',
  'verputz-weiss-glatt': 'putz',
  'verputz-weiss-rau': 'putz',
  'holzlattung-fichte': 'latten',
  dreischichtplatte: 'platte',
};

function kanal(hex: string, i: number): number {
  return parseInt(hex.slice(1 + 2 * i, 3 + 2 * i), 16);
}

/** Mischt `b` mit Anteil `t` in `a` (beide `#rrggbb`). */
export function mische(a: string, b: string, t: number): string {
  const k = Math.min(1, Math.max(0, t));
  const teil = (i: number) => Math.round(kanal(a, i) * (1 - k) + kanal(b, i) * k).toString(16).padStart(2, '0');
  return `#${teil(0)}${teil(1)}${teil(2)}`;
}

/** Heller (t > 0) oder dunkler (t < 0). */
export function hell(a: string, t: number): string {
  return t >= 0 ? mische(a, '#ffffff', t) : mische(a, '#000000', -t);
}

/** CSS-Hintergrund der Fläche je Muster — ruhig, nur als Andeutung des Stoffs. */
export function flaechenMuster(muster: MaterialMuster, farbe: string, massstab = 1): string {
  const d = hell(farbe, -0.12);
  const s = Math.max(4, Math.round(12 * Math.min(4, Math.max(0.25, massstab))));
  switch (muster) {
    case 'ziegel':
      return `repeating-linear-gradient(0deg, ${hell(farbe, 0.25)} 0 1px, transparent 1px ${s / 2}px), repeating-linear-gradient(90deg, ${d} 0 1px, ${farbe} 1px ${s}px)`;
    case 'holz':
      return `repeating-linear-gradient(90deg, ${farbe} 0 ${s / 3}px, ${hell(farbe, -0.06)} ${s / 3}px ${(s * 2) / 3}px)`;
    case 'latten':
      return `repeating-linear-gradient(90deg, ${farbe} 0 ${s / 2}px, ${hell(farbe, -0.35)} ${s / 2}px ${s / 2 + 2}px)`;
    case 'platte':
      return `repeating-linear-gradient(0deg, ${farbe} 0 ${s * 2}px, ${d} ${s * 2}px ${s * 2 + 1}px)`;
    case 'stein':
      return `repeating-linear-gradient(0deg, ${farbe} 0 ${s}px, ${hell(farbe, 0.2)} ${s}px ${s + 1}px)`;
    case 'putz':
    case 'lehm':
      return `repeating-linear-gradient(0deg, ${farbe} 0 ${Math.max(2, s / 4)}px, ${hell(farbe, muster === 'lehm' ? -0.08 : -0.03)} ${Math.max(2, s / 4)}px ${Math.max(3, s / 2)}px)`;
    default:
      return `radial-gradient(circle at 30% 30%, ${hell(farbe, 0.08)} 0 1px, transparent 1px) 0 0 / ${Math.max(4, s / 2)}px ${Math.max(4, s / 2)}px, ${farbe}`;
  }
}
