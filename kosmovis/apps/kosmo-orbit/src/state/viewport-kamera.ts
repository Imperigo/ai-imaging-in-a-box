import { create } from 'zustand';

/**
 * **Die LIVE-Kamera der 3D-Ansicht lesen (fuer den KosmoVis-Knoten
 * «Kamera aus 3D-Ansicht»).**
 *
 * Gelesen wird beim Aufruf von `aktuelleKamera()`, ohne Abo und ohne
 * Intervall. Die 3D-Ansicht (`modules/design/Viewport3D.tsx`) meldet beim
 * Aufbau einen Lieferanten an (eine Funktion, die die Kamera liest) und beim
 * Abbau wieder ab. Ohne Lieferant, also ohne offene 3D-Ansicht, ist die
 * Antwort `null`. Kein Modellzustand, nicht persistiert (Muster
 * `state/geschoss-eigenschaften-anfrage.ts`).
 *
 * RAHMEN `'welt-y-oben-m'`: Meter, y oben, x = Plan-x (Ost), z = -Plan-y
 * (Sued). Der Rahmen der three-Szene; derselbe wie in der GLB-Ausfuhr
 * (`exportGlb`), eine Umrechnung zwischen beiden ist nicht noetig.
 *
 * FOV IST VERTIKAL: `fovVertikalGrad` ist `camera.fov` von three, der
 * VERTIKALE Oeffnungswinkel, keine Brennweite. Der horizontale Winkel ist
 * `2 * atan(tan(fovV / 2) * seitenverhaeltnis)`; wer einen horizontalen
 * Winkel fuehrt (KosmoVis `CameraSpec.fov`), rechnet selbst um.
 *
 * OBJEKTIV-SHIFT: immer `null`, die Ansicht ist nur perspektivisch (kein
 * `setViewOffset`).
 *
 * GESCHOSS-ID: nur gesetzt, wenn die Ansicht auf ein Geschoss beschnitten
 * ist. Heute gibt es dafuer keine klare Quelle (der Schnitt-Regler schneidet
 * auf eine Hoehe, nicht auf ein Geschoss; das aktive Geschoss ist die
 * Plan-Auswahl und beschneidet die 3D-Ansicht nicht). Das Feld fehlt darum.
 */
export interface ViewportKamera {
  rahmen: 'welt-y-oben-m';
  position: [number, number, number];
  ziel: [number, number, number];
  oben: [0, 1, 0];
  fovVertikalGrad: number;
  seitenverhaeltnis: number;
  nah: number;
  fern: number;
  objektivShift: null;
  nordrichtungGrad: number;
  geschossId?: string;
}

export type KameraLieferant = () => ViewportKamera | null;

interface ViewportKameraZustand {
  lieferant: KameraLieferant | null;
  /** Meldet einen Lieferanten an; gibt die Abmeldung zurueck. Die Abmeldung
   *  wirkt nur, wenn noch derselbe Lieferant steht (ein spaeterer bleibt). */
  melde: (l: KameraLieferant) => () => void;
}

export const useViewportKamera = create<ViewportKameraZustand>((set, get) => ({
  lieferant: null,
  melde: (l) => {
    set({ lieferant: l });
    return () => {
      if (get().lieferant === l) set({ lieferant: null });
    };
  },
}));

/** Die jetzige Kamera der 3D-Ansicht, oder `null` ohne offene 3D-Ansicht. */
export function aktuelleKamera(): ViewportKamera | null {
  const l = useViewportKamera.getState().lieferant;
  return l ? l() : null;
}
