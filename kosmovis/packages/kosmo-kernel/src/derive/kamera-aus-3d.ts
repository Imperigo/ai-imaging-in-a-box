import type { AutoKameraStandpunkt } from './kamera';

/**
 * **Knoten «Kamera aus 3D-Ansicht»** (Owner-Entscheid 14.10.2026, über die Zentrale): die
 * Knotenansicht ist die einzige Arbeitsfläche zum Rendern; der Block «Rendern» in der 3D-Ansicht
 * wird zum Zulieferer. Dieser Knoten trägt den Blick, den der Architekt in der 3D-Ansicht
 * eingestellt hat, als Kamera-Standpunkt an den Render-Knoten.
 *
 * Diese Datei rechnet nur (Kern, kein Store): die App liest die Kamera aus
 * `state/viewport-kamera.ts` (`aktuelleKamera()`, KosmoDraw) und legt sie mit
 * `kameraAus3dParams` als gewöhnliche Knoten-Parameter ab — im Dokument, rückgängig machbar wie
 * jeder andere Parameter (`vis.nodeParametrieren`). Gelesen wird beim Anlegen und auf Knopfdruck,
 * nie laufend.
 *
 * RAHMEN: `'welt-y-oben-m'` — Meter, y oben, x = Plan-x, z = −Plan-y. Derselbe Rahmen wie das
 * `model.glb` der Bestellung (`derive/gltf.ts`) und wie `AutoKameraStandpunkt` (glTF-Konvention).
 * Die Position geht darum ohne Umrechnung durch.
 *
 * BLICKFELD: der Store liefert den VERTIKALEN Öffnungswinkel (three `camera.fov`). Der Vertrag
 * `CameraSpec.fov` wird drüben als HORIZONTALER Winkel gelesen (Visbox-Abholer,
 * `aiimaging.kosmo_szene.brennweite_zu_fov`). Umgerechnet wird mit `fovHorizontalGrad` — und
 * zwar mit dem Seitenverhältnis des BESTELLFORMATS (das Bild, das gerechnet wird), nicht dem der
 * Leinwand: so bleibt die Höhe des Blicks erhalten, und die Breite folgt dem Bild. Nur wo es kein
 * Bestellformat gibt (der Knoten hängt an keinem Render-Knoten), zeigt der Knoten den Winkel für
 * die Leinwand.
 *
 * OBJEKTIV-SHIFT: immer `null` (die 3D-Ansicht ist nur perspektivisch); `CameraSpec` kennt
 * keinen. Der Knoten sagt es leise dazu.
 */

/** Katalog-Typ des Knotens (`VIS_NODE_KATALOG`). */
export const KAMERA_AUS_3D_TYP = 'kameraAus3d';

/** Name des Standpunkts in der Bestellung (`CameraSpec.name`). */
export const KAMERA_AUS_3D_NAME = 'Kamera aus 3D-Ansicht';

/**
 * Bestellformat, wenn weder Voreinstellung noch Auflösung gewählt ist — dieselbe Zahl, die
 * `postRenderJob` (`vis-jobs.ts`) als `render.resolution` sendet. EINE Stelle, damit Knoten und
 * Bestellung dasselbe Seitenverhältnis rechnen.
 */
export const BESTELLFORMAT_VORGABE: readonly [number, number] = [1600, 1000];

/** Gültiger Bereich von `CameraSpec.fov` (`kosmo-contracts` `render-scene.ts`). */
export const FOV_GRENZEN_GRAD: readonly [number, number] = [10, 120];

/**
 * Horizontaler Öffnungswinkel aus dem vertikalen und dem Seitenverhältnis (Breite / Höhe):
 *
 *     horizontal = 2 · atan( tan(vertikal / 2) · seitenverhaeltnis )
 *
 * Grad hinein, Grad heraus. Rein; `NaN` bei unbrauchbaren Eingaben (kein stiller Ersatzwert).
 */
export function fovHorizontalGrad(fovVertikalGrad: number, seitenverhaeltnis: number): number {
  if (!(fovVertikalGrad > 0 && fovVertikalGrad < 180) || !(seitenverhaeltnis > 0) || !Number.isFinite(seitenverhaeltnis)) {
    return Number.NaN;
  }
  const halb = (fovVertikalGrad * Math.PI) / 360;
  return (2 * Math.atan(Math.tan(halb) * seitenverhaeltnis) * 180) / Math.PI;
}

/** Seitenverhältnis eines Bestellformats `[Breite, Höhe]` in Pixeln. */
export function seitenverhaeltnisAus(aufloesung: readonly [number, number]): number {
  return aufloesung[0] / aufloesung[1];
}

/** Die gespeicherte Kamera, wie der Knoten sie trägt (Rahmen `welt-y-oben-m`). */
export interface Kamera3dGespeichert {
  position: [number, number, number];
  ziel: [number, number, number];
  fovVertikalGrad: number;
  /** Seitenverhältnis der LEINWAND beim Übernehmen (Breite / Höhe). */
  seitenverhaeltnis: number;
  nah: number;
  fern: number;
  nordrichtungGrad: number;
}

/** Was die App aus dem Store hineinreicht — strukturell `ViewportKamera` (KosmoDraw). */
export interface Kamera3dQuelle {
  rahmen: 'welt-y-oben-m';
  position: readonly [number, number, number];
  ziel: readonly [number, number, number];
  fovVertikalGrad: number;
  seitenverhaeltnis: number;
  nah: number;
  fern: number;
  objektivShift: null;
  nordrichtungGrad: number;
}

const FELDER = ['posX', 'posY', 'posZ', 'zielX', 'zielY', 'zielZ', 'fovVertikalGrad', 'seitenverhaeltnis', 'nah', 'fern', 'nordrichtungGrad'] as const;

/**
 * Knoten-Parameter aus einer Store-Kamera. Flach, weil Knoten-Parameter nur Zahl, Text oder
 * Ja/Nein tragen (`VisNode.params`) — und flach mischt `vis.nodeParametrieren` sauber. Die
 * Umgebung (Splat) kommt als Satz dazu: `umgebung` sagt, was mitgeht oder warum nichts.
 */
export function kameraAus3dParams(
  k: Kamera3dQuelle,
  umgebung: { mit: boolean; satz: string } | null,
): Record<string, string | number | boolean> {
  return {
    posX: k.position[0],
    posY: k.position[1],
    posZ: k.position[2],
    zielX: k.ziel[0],
    zielY: k.ziel[1],
    zielZ: k.ziel[2],
    fovVertikalGrad: k.fovVertikalGrad,
    seitenverhaeltnis: k.seitenverhaeltnis,
    nah: k.nah,
    fern: k.fern,
    nordrichtungGrad: k.nordrichtungGrad,
    // Leerer Satz = kein Splat im Projekt; `umgebungMit` sagt, ob er als Umgebung mitgeht.
    umgebung: umgebung?.satz ?? '',
    umgebungMit: umgebung?.mit ?? false,
  };
}

/** Die gespeicherte Kamera aus den Knoten-Parametern — `null`, solange keine übernommen ist
 *  oder ein Feld fehlt (Fremdstand, Hand-Edit). */
export function kameraAus3dAusParams(params: Readonly<Record<string, string | number | boolean>> | undefined): Kamera3dGespeichert | null {
  if (!params) return null;
  const z: number[] = [];
  for (const f of FELDER) {
    const w = params[f];
    if (typeof w !== 'number' || !Number.isFinite(w)) return null;
    z.push(w);
  }
  return {
    position: [z[0]!, z[1]!, z[2]!],
    ziel: [z[3]!, z[4]!, z[5]!],
    fovVertikalGrad: z[6]!,
    seitenverhaeltnis: z[7]!,
    nah: z[8]!,
    fern: z[9]!,
    nordrichtungGrad: z[10]!,
  };
}

/**
 * Der Standpunkt für die Bestellung. `fov` ist HORIZONTAL für das gegebene Seitenverhältnis;
 * `fovVertikalGrad` reist mit, damit `postRenderJob` mit dem endgültigen Bestellformat (Auflösung
 * am Render-Knoten kann die Voreinstellung schlagen) neu rechnen kann. Kein `referenzpunkt`: die
 * 3D-Ansicht nennt keinen Bodenbezug, und einen zu behaupten wäre falsch (wie bei «Übersicht»).
 */
export function kameraAus3dStandpunkt(k: Kamera3dGespeichert, seitenverhaeltnis: number): AutoKameraStandpunkt {
  return {
    name: KAMERA_AUS_3D_NAME,
    position: [k.position[0], k.position[1], k.position[2]],
    target: [k.ziel[0], k.ziel[1], k.ziel[2]],
    fov: fovHorizontalGrad(k.fovVertikalGrad, seitenverhaeltnis),
    fovVertikalGrad: k.fovVertikalGrad,
    begruendung: 'Der Blick aus der 3D-Ansicht, übernommen auf Knopfdruck — kein Vorschlag, ohne Objektiv-Shift.',
  };
}

/**
 * Standpunkte für das ENDGÜLTIGE Bestellformat: wer `fovVertikalGrad` trägt (nur «Kamera aus
 * 3D-Ansicht»), bekommt `fov` horizontal für `aufloesung` neu gerechnet; alle anderen bleiben
 * Zahl für Zahl, wie sie sind. Rein — `postRenderJob` ruft es an der Stelle, an der die
 * Auflösung feststeht.
 */
export function kamerasFuerBestellformat(
  kameras: readonly AutoKameraStandpunkt[],
  aufloesung: readonly [number, number],
): AutoKameraStandpunkt[] {
  const a = seitenverhaeltnisAus(aufloesung);
  return kameras.map((k) => (k.fovVertikalGrad !== undefined ? { ...k, fov: fovHorizontalGrad(k.fovVertikalGrad, a) } : k));
}

/** Liegt ein Blickfeld im Bereich, den `CameraSpec.fov` annimmt? */
export function fovImVertrag(fovGrad: number): boolean {
  return Number.isFinite(fovGrad) && fovGrad >= FOV_GRENZEN_GRAD[0] && fovGrad <= FOV_GRENZEN_GRAD[1];
}
