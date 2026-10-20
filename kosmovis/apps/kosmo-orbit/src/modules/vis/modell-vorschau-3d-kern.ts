/**
 * **Kleines 3D-Fenster — der Kern** (Bauplan «Neue Knoten» vom 20.10.2026, gemeinsamer Baustein
 * für F1 Modell-Knoten, F2 Auto-Kamera und F4 Oberfläche; Entscheid 109 A: klein fest im
 * Modell-Knoten, Doppelklick gross).
 *
 * Reine Logik mit three, ohne React. Diese Datei wird **nur** über `import()` aus
 * `modell-vorschau-3d.tsx` geladen und bildet so einen eigenen Teil des Baus: wer kein
 * 3D-Fenster öffnet, lädt sie nie, und der Haupt-Teil wächst nicht.
 *
 * Was hier steht:
 *  - die **reinen Rechnungen** (ohne WebGL prüfbar): Rahmen auf die Hüllbox, Kegel je Kamera,
 *    Pixeldichte;
 *  - `erzeugeModellVorschau3d` — Zeichner, glb-Lader, Umkreisen (OrbitControls); gibt `null`
 *    zurück, wenn der Browser kein WebGL2 hergibt (dann zeigt die Hülle den Rückfall-Satz).
 *
 * **Achsen:** glb ist nach glTF-Regel Y oben, in Metern — wie three selbst. Darum wird das
 * Modell **nicht** gedreht, und die Kameraliste kommt in derselben Konvention
 * (`AutoKameraStandpunkt` in `derive/kamera.ts`: «Meter, glTF-Konvention (x, y-oben, z)»).
 *
 * **Blickfeld:** `fov` ist wie im Vertrag (`CameraSpec.fov`) der **waagrechte** Winkel in Grad.
 * Liegt der senkrechte vor (`fovVertikalGrad`, Kamera aus der 3D-Ansicht), gilt er.
 *
 * **Gezeichnet wird nur bei Bedarf** (nach Laden, Umkreisen, Grössenwechsel), nicht in einer
 * Dauerschleife — mehrere Fenster im Knotengraph sollen den Rechner nicht warm halten.
 *
 * **Hell wie ein Weissmodell** (Owner-Befund am Mac, 20.10.2026: «beim Drehen alles schwarz»).
 * Ursache: Ein Bauteil ohne Material bekommt vom glTF-Lader dessen Vorgabe-Material, und das
 * ist **ganz metallisch** (`metalness: 1`; glTF nennt `metallicFactor` 1, wenn nichts dasteht).
 * Metall zeigt nur, was es spiegelt — ohne Umgebung also fast nichts, ausser einem Glanzfleck
 * dort, wo die Sonne gerade spiegelt; dreht man, wandert der Fleck weg, und das Haus wird
 * schwarz. Die IFC-Umwandlung von Visbox lässt Bauteile ohne IFC-Stil genau so ohne Material.
 * Dagegen: eine Umgebung (`RoomEnvironment` aus three, MIT) als Licht von allen Seiten, Metall
 * auf höchstens `METALL_HOECHSTENS` begrenzt, schwarze Grundfarbe → Hellgrau, beide Seiten
 * jeder Fläche, fehlende Flächen-Richtungen nachgerechnet (`sichereMaterial`, `sichereNetz`),
 * und dünne Kanten ab `KANTEN_WINKEL_GRAD` Knick.
 *
 * **Kein Abschneiden beim Hineinzoomen** (gleicher Befund: «näher ranzoomt kommt ein
 * clipping»). Ursache: Die vordere Schnittebene (`near`) wurde einmal beim Rahmen gesetzt — auf
 * etwa zwei Modellradien vor der Kamera — und beim Zoomen nicht nachgeführt; wer näher kam,
 * schnitt das Haus vorne weg. Jetzt rechnet jedes Zeichnen `near`/`far` aus dem Abstand zur
 * Kugel um Modell und Kegel neu (`nahUndFern`).
 */
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';

export type Vec3 = readonly [number, number, number];

/** Eine Kamera aus der Liste (Standpunkt), in glTF-Achsen (Y oben, Meter). */
export interface VorschauKamera {
  readonly position: Vec3;
  readonly target: Vec3;
  /** Waagrechter Öffnungswinkel in Grad (wie `CameraSpec.fov`). */
  readonly fov: number;
  /** Senkrechter Öffnungswinkel in Grad, falls bekannt — er geht dann vor. */
  readonly fovVertikalGrad?: number;
  /** Breite durch Höhe des Bildes; fehlt es, gilt `KEGEL_SEITENVERHAELTNIS`. */
  readonly seitenverhaeltnis?: number;
  readonly name?: string;
}

/** Hüllbox in glTF-Achsen. */
export interface Huellbox {
  readonly min: Vec3;
  readonly max: Vec3;
}

/** Wohin die Kamera schaut und von wo — das Ergebnis der Rahmung. */
export interface Ansicht {
  readonly position: Vec3;
  readonly target: Vec3;
  readonly near: number;
  readonly far: number;
}

/** Seitenverhältnis eines Kegels, wenn die Kamera keines nennt (Bestellformat 3:2). */
export const KEGEL_SEITENVERHAELTNIS = 3 / 2;
/** Obergrenze der Pixeldichte: mehr bringt im kleinen Fenster nichts und kostet Speicher. */
export const PIXELDICHTE_OBERGRENZE = 2;
/** Untergrenze: weit herausgezoomt soll das Bild nicht in Klötzchen zerfallen. */
export const PIXELDICHTE_UNTERGRENZE = 0.5;
/** Senkrechter Öffnungswinkel der Vorschau-Kamera in Grad. */
export const VORSCHAU_FOV_GRAD = 35;
/** Aus welcher Richtung das Modell zuerst gezeigt wird: vorne rechts, leicht von oben. */
export const RAHMEN_RICHTUNG: Vec3 = [1, 0.62, 1.15];
/** Luft um das Modell (1 = Kugel berührt den Bildrand). */
export const RAHMEN_LUFT = 1.12;

/** Höchstens so metallisch darf ein Material im Fenster sein (Weissmodell, nicht Spiegel). */
export const METALL_HOECHSTENS = 0.2;
/** Grundfarbe für Flächen ohne Farbe oder mit (fast) schwarzer — ein ruhiges Hellgrau. */
export const GRUNDGRAU = 0xd8d6d0;
/** Unter dieser Helligkeit (0…1, linear) gilt eine Grundfarbe als «schwarz». */
export const SCHWARZ_SCHWELLE = 0.02;
/** Ab diesem Knick zwischen zwei Flächen wird eine Kante gezeichnet (Grad). */
export const KANTEN_WINKEL_GRAD = 30;
/** Über so vielen Dreiecken im ganzen Modell entfallen die Kanten (Rechenzeit beim Laden). */
export const KANTEN_HOECHSTENS_DREIECKE = 200_000;
/** Kleinster Abstand der vorderen Schnittebene, als Teil des Modellradius. */
export const NAH_ANTEIL_RADIUS = 1 / 1000;

const GRAD = Math.PI / 180;

function laenge(v: Vec3): number {
  return Math.hypot(v[0], v[1], v[2]);
}

function normiert(v: Vec3): Vec3 {
  const l = laenge(v);
  return l > 0 ? [v[0] / l, v[1] / l, v[2] / l] : [0, 0, 1];
}

function kreuz(a: Vec3, b: Vec3): Vec3 {
  return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
}

function istEndlich(v: Vec3): boolean {
  return v.every((x) => Number.isFinite(x));
}

/**
 * **Pixeldichte** des Zeichners: Bildschirmdichte mal Knotenzoom, nach oben begrenzt.
 *
 * Der Knotengraph vergrössert seine Knoten mit einer CSS-Skalierung; der Zeichner weiss davon
 * nichts. Ohne den Zoomfaktor würde ein vergrösserter Knoten ein unscharfes Bild zeigen, ohne
 * Obergrenze kostete ein grosser Zoom unnötig Speicher (vier Fenster × 4 × Fläche).
 */
export function pixeldichte(
  dpr: number,
  knotenZoom = 1,
  obergrenze = PIXELDICHTE_OBERGRENZE,
): number {
  const d = Number.isFinite(dpr) && dpr > 0 ? dpr : 1;
  const z = Number.isFinite(knotenZoom) && knotenZoom > 0 ? knotenZoom : 1;
  return Math.min(obergrenze, Math.max(PIXELDICHTE_UNTERGRENZE, d * z));
}

/**
 * **Vordere und hintere Schnittebene** aus dem Abstand der Kamera zur Mitte einer Kugel, die
 * alles Gezeichnete umschliesst (Modell und Kegel).
 *
 * Steht die Kamera ausserhalb, beginnt das Bild kurz vor der Kugel (`abstand − 1,5 · radius`,
 * die halbe Reserve schluckt Rundung) — so eng wie möglich, damit die Tiefe genau bleibt. Ist
 * sie nahe dran oder drin, gilt `radius / 1000`: man kann bis an eine Wand heran, ohne dass sie
 * abgeschnitten wird. Hinten endet das Bild hinter der Kugel (`abstand + 2 · radius`).
 * Kaputte Zahlen ergeben ein ruhiges `0,01 … 1000`.
 */
export function nahUndFern(abstand: number, radius: number): { near: number; far: number } {
  if (!Number.isFinite(abstand) || !Number.isFinite(radius) || radius <= 0 || abstand < 0) {
    return { near: 0.01, far: 1000 };
  }
  const kleinst = Math.max(radius * NAH_ANTEIL_RADIUS, 1e-4);
  const near = Math.max(abstand - radius * 1.5, kleinst);
  const far = abstand + radius * 2;
  return { near, far };
}

/** Kugel um eine Hüllbox und weitere Punkte (Kegel): Mitte der Box, Radius bis zum fernsten. */
export function huellkugel(box: Huellbox, punkte: readonly Vec3[] = []): { mitte: Vec3; radius: number } {
  const mitte: Vec3 = [
    (box.min[0] + box.max[0]) / 2,
    (box.min[1] + box.max[1]) / 2,
    (box.min[2] + box.max[2]) / 2,
  ];
  let radius = Math.max(laenge([box.max[0] - box.min[0], box.max[1] - box.min[1], box.max[2] - box.min[2]]) / 2, 0.05);
  for (const p of punkte) {
    if (!istEndlich(p)) continue;
    radius = Math.max(radius, laenge([p[0] - mitte[0], p[1] - mitte[1], p[2] - mitte[2]]));
  }
  return { mitte, radius };
}

/** Das Nötigste eines Materials, damit `sichereMaterial` auch an einer Attrappe prüfbar ist. */
export interface MaterialLike {
  metalness?: number;
  color?: { r: number; g: number; b: number; setHex(hex: number): unknown };
  map?: unknown;
  side?: number;
  vertexColors?: boolean;
  polygonOffset?: boolean;
  polygonOffsetFactor?: number;
  polygonOffsetUnits?: number;
  needsUpdate?: boolean;
}

/**
 * **Material für das Weissmodell absichern** — gibt zurück, was geändert wurde (für Proben).
 *
 *  - `metalness` höchstens `METALL_HOECHSTENS` (glTF-Vorgabe ist 1 = Spiegel → schwarz);
 *  - Grundfarbe (fast) schwarz und keine Bildtextur, keine Punktfarben → `GRUNDGRAU`;
 *  - beide Seiten jeder Fläche (IFC-Flächen sind nicht immer gleich herum);
 *  - leicht nach hinten versetzt, damit die Kanten darüber nicht flimmern.
 */
export function sichereMaterial(m: MaterialLike): { metall: boolean; farbe: boolean } {
  let metall = false;
  let farbe = false;
  if (typeof m.metalness === 'number' && !(m.metalness <= METALL_HOECHSTENS)) {
    m.metalness = METALL_HOECHSTENS;
    metall = true;
  }
  const c = m.color;
  if (c && !m.map && !m.vertexColors) {
    const hell = 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b;
    if (!(hell >= SCHWARZ_SCHWELLE)) {
      c.setHex(GRUNDGRAU);
      farbe = true;
    }
  }
  m.side = THREE.DoubleSide;
  m.polygonOffset = true;
  m.polygonOffsetFactor = 1;
  m.polygonOffsetUnits = 1;
  m.needsUpdate = true;
  return { metall, farbe };
}

/** Fehlen einem Netz die Flächen-Richtungen (Normalen), werden sie nachgerechnet — sonst ist
 *  jede Fläche gleich dunkel. Gibt `true` zurück, wenn nachgerechnet wurde. */
export function sichereNetz(g: THREE.BufferGeometry): boolean {
  if (g.getAttribute('normal') || !g.getAttribute('position')) return false;
  g.computeVertexNormals();
  return true;
}

/**
 * **Rahmen auf die Hüllbox**: Standpunkt so, dass die Kugel um die Box ganz ins Bild passt —
 * in der engeren der beiden Richtungen (bei einem hohen, schmalen Fenster ist es die Breite).
 *
 * `fovVertikalGrad` ist der senkrechte Öffnungswinkel der Vorschau-Kamera, `seitenverhaeltnis`
 * Breite durch Höhe des Fensters. Eine leere oder kaputte Box ergibt einen Würfel von 1 m um
 * den Nullpunkt — das Fenster zeigt dann nichts Falsches, nur nichts.
 */
export function rahmeHuellbox(
  box: Huellbox,
  fovVertikalGrad = VORSCHAU_FOV_GRAD,
  seitenverhaeltnis = 1,
  richtung: Vec3 = RAHMEN_RICHTUNG,
): Ansicht {
  const gueltig =
    istEndlich(box.min) && istEndlich(box.max) &&
    box.max[0] >= box.min[0] && box.max[1] >= box.min[1] && box.max[2] >= box.min[2];
  const min: Vec3 = gueltig ? box.min : [-0.5, -0.5, -0.5];
  const max: Vec3 = gueltig ? box.max : [0.5, 0.5, 0.5];
  const mitte: Vec3 = [(min[0] + max[0]) / 2, (min[1] + max[1]) / 2, (min[2] + max[2]) / 2];
  // Halbe Raumdiagonale; ein Punkt (alle Masse null) bekommt trotzdem eine kleine Kugel.
  const radius = Math.max(laenge([max[0] - min[0], max[1] - min[1], max[2] - min[2]]) / 2, 0.05);
  const fovV = Math.min(Math.max(fovVertikalGrad, 1), 179) * GRAD;
  const asp = Number.isFinite(seitenverhaeltnis) && seitenverhaeltnis > 0 ? seitenverhaeltnis : 1;
  const fovH = 2 * Math.atan(Math.tan(fovV / 2) * asp);
  const halberWinkel = Math.min(fovV, fovH) / 2;
  const abstand = (radius / Math.sin(halberWinkel)) * RAHMEN_LUFT;
  const r = normiert(richtung);
  return {
    position: [mitte[0] + r[0] * abstand, mitte[1] + r[1] * abstand, mitte[2] + r[2] * abstand],
    target: mitte,
    near: Math.max(abstand - radius * 1.5, abstand / 1000, 0.01),
    far: abstand + radius * 4,
  };
}

/**
 * **Kegel einer Kamera** als Linien-Pyramide: Spitze im Standpunkt, Grundfläche `laengeM` Meter
 * entfernt in Blickrichtung, so breit und hoch wie das Bild der Kamera.
 *
 * Rückgabe: Paare von Punkten (je Linie zwei, je Punkt drei Zahlen) — 4 Kanten von der Spitze
 * zu den Ecken, 4 Kanten der Grundfläche und ein kleines Dreieck über der Oberkante, das «oben»
 * zeigt (2 Kanten). Zusammen **10 Linien, 60 Zahlen**. `null`, wenn Standpunkt und Ziel
 * zusammenfallen oder Zahlen fehlen.
 *
 * «Oben» ist die Welt-Y-Achse (Senkrechte gerade, Entscheid 109 C). Schaut die Kamera genau
 * senkrecht, gilt -Z als oben (wie three es bei einer Draufsicht hält).
 */
export function kegelLinien(kamera: VorschauKamera, laengeM: number): Float32Array | null {
  if (!istEndlich(kamera.position) || !istEndlich(kamera.target) || !(laengeM > 0)) return null;
  const blick: Vec3 = [
    kamera.target[0] - kamera.position[0],
    kamera.target[1] - kamera.position[1],
    kamera.target[2] - kamera.position[2],
  ];
  if (laenge(blick) < 1e-9) return null;
  const v = normiert(blick);
  const asp = kamera.seitenverhaeltnis !== undefined && kamera.seitenverhaeltnis > 0
    ? kamera.seitenverhaeltnis
    : KEGEL_SEITENVERHAELTNIS;
  let halbB: number;
  let halbH: number;
  if (kamera.fovVertikalGrad !== undefined && kamera.fovVertikalGrad > 0 && kamera.fovVertikalGrad < 180) {
    halbH = laengeM * Math.tan((kamera.fovVertikalGrad * GRAD) / 2);
    halbB = halbH * asp;
  } else {
    const fov = Math.min(Math.max(kamera.fov, 1), 179);
    halbB = laengeM * Math.tan((fov * GRAD) / 2);
    halbH = halbB / asp;
  }
  // Rechts und oben der Kamera, Welt-Y als Senkrechte.
  let rechts = kreuz(v, [0, 1, 0]);
  if (laenge(rechts) < 1e-6) rechts = kreuz(v, [0, 0, -1]);
  rechts = normiert(rechts);
  const oben = normiert(kreuz(rechts, v));
  const p = kamera.position;
  const mitte: Vec3 = [p[0] + v[0] * laengeM, p[1] + v[1] * laengeM, p[2] + v[2] * laengeM];
  const ecke = (sr: number, so: number): Vec3 => [
    mitte[0] + rechts[0] * halbB * sr + oben[0] * halbH * so,
    mitte[1] + rechts[1] * halbB * sr + oben[1] * halbH * so,
    mitte[2] + rechts[2] * halbB * sr + oben[2] * halbH * so,
  ];
  const ol = ecke(-1, 1);
  const or = ecke(1, 1);
  const ur = ecke(1, -1);
  const ul = ecke(-1, -1);
  const giebel = ecke(0, 1.45);
  const linien: Vec3[] = [
    p, ol, p, or, p, ur, p, ul,
    ol, or, or, ur, ur, ul, ul, ol,
    ol, giebel, giebel, or,
  ];
  const out = new Float32Array(linien.length * 3);
  linien.forEach((q, i) => {
    out[i * 3] = q[0];
    out[i * 3 + 1] = q[1];
    out[i * 3 + 2] = q[2];
  });
  return out;
}

/** Länge der Kegel: ein Fünftel der Modellgrösse, damit sie das Haus nicht überdecken. */
export function kegelLaenge(box: Huellbox): number {
  const d = laenge([box.max[0] - box.min[0], box.max[1] - box.min[1], box.max[2] - box.min[2]]);
  return Number.isFinite(d) && d > 0 ? Math.max(d / 5, 0.3) : 1;
}

/** Ein kleines Bild aus einer Kamera, Zeilen von oben nach unten, RGBA. */
export interface Blickvorschau {
  readonly breite: number;
  readonly hoehe: number;
  readonly daten: Uint8ClampedArray;
}

export interface ModellVorschau3dOptionen {
  readonly canvas: HTMLCanvasElement;
  readonly pixeldichte: number;
  /** Fenstergrösse in CSS-Pixeln. */
  readonly breite: number;
  readonly hoehe: number;
  /** Farbe der Kegel (CSS-Farbe); Vorgabe ein ruhiges Orange. */
  readonly kegelFarbe?: string;
  /** Der Browser hat den Zeichenkontext entzogen (`webglcontextlost`). */
  readonly onKontextVerloren?: () => void;
  /** … und wieder gegeben; das Bild ist schon neu gezeichnet. */
  readonly onKontextZurueck?: () => void;
}

export interface ModellVorschau3d {
  /** Liest die glb-Bytes, ersetzt das vorige Modell und rahmt neu. */
  ladeGlb(bytes: ArrayBuffer): Promise<void>;
  setzeKameras(kameras: readonly VorschauKamera[]): void;
  setzeGroesse(breite: number, hoehe: number): void;
  setzePixeldichte(dichte: number): void;
  /** Ran oder weg vom Ziel (Pinch in WebKit kommt nicht als Rad). `faktor > 1` = näher. */
  zoome(faktor: number): void;
  /** Wieder auf die Hüllbox rahmen. */
  rahmen(): void;
  /** Aktueller Standpunkt — damit ein neu aufgebautes Fenster dort weitermacht. */
  ansicht(): Ansicht;
  setzeAnsicht(a: Pick<Ansicht, 'position' | 'target'>): void;
  /** Hilfsrender aus Kamera `index` in ein kleines Ziel; `null` ohne Modell oder Kamera. */
  blickvorschau(index: number, breite?: number, hoehe?: number): Blickvorschau | null;
  /** Hält an: kein Zeichnen mehr, bis `fortsetzen`. */
  pausiere(): void;
  fortsetzen(): void;
  zeichne(): void;
  dispose(): void;
}

/**
 * Baut das Fenster. **`null`, wenn es kein WebGL2 gibt** (jsdom, abgeschaltete
 * Beschleunigung in WebKitGTK, Xvfb): three wirft dann beim Anlegen des Zeichners, und die
 * Hülle zeigt «Kein 3D in diesem Fenster».
 */
export function erzeugeModellVorschau3d(opt: ModellVorschau3dOptionen): ModellVorschau3d | null {
  // F1: ohne WebGL2 gar nicht erst versuchen — three schriebe sonst bei jedem Knoten einen
  // Fehler in die Konsole (jsdom: in jeder Probe, die einen Modell-Knoten zeigt).
  if (typeof WebGL2RenderingContext === 'undefined') return null;
  let renderer: THREE.WebGLRenderer;
  try {
    renderer = new THREE.WebGLRenderer({
      canvas: opt.canvas,
      antialias: true,
      alpha: true,
      powerPreference: 'low-power',
    });
  } catch {
    return null;
  }
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  // Neutral statt ACES: ACES dunkelt Weiss ab und zieht es ins Gelbliche; ein Weissmodell soll
  // weiss bleiben. AgX täte dasselbe gedämpfter.
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.toneMappingExposure = 1;
  renderer.setClearColor(0x000000, 0);
  renderer.setPixelRatio(opt.pixeldichte);
  renderer.setSize(Math.max(1, opt.breite), Math.max(1, opt.hoehe), false);

  const szene = new THREE.Scene();
  // Licht von allen Seiten (Umgebung) plus Himmel/Boden und eine Sonne für die Schattierung:
  // jede Seite des Hauses bleibt hell, die Flächen unterscheiden sich trotzdem.
  let umgebung: THREE.WebGLRenderTarget | null = null;
  const setzeUmgebung = () => {
    umgebung?.dispose();
    umgebung = null;
    try {
      const pmrem = new THREE.PMREMGenerator(renderer);
      const raum = new RoomEnvironment();
      umgebung = pmrem.fromScene(raum, 0.04);
      raum.traverse((o) => {
        const m = o as THREE.Mesh;
        m.geometry?.dispose();
        (m.material as THREE.Material | undefined)?.dispose?.();
      });
      pmrem.dispose();
      szene.environment = umgebung.texture;
    } catch {
      szene.environment = null; // ohne Umgebung tragen Himmel und Sonne allein
    }
  };
  setzeUmgebung();
  szene.environmentIntensity = 0.9;
  szene.add(new THREE.HemisphereLight(0xffffff, 0x8a8d94, 1.1));
  const sonne = new THREE.DirectionalLight(0xffffff, 1.5);
  sonne.position.set(0.6, 1, 0.45);
  szene.add(sonne);

  let seitenverhaeltnis = Math.max(1, opt.breite) / Math.max(1, opt.hoehe);
  const kamera = new THREE.PerspectiveCamera(VORSCHAU_FOV_GRAD, seitenverhaeltnis, 0.1, 1000);
  kamera.up.set(0, 1, 0);

  const steuerung = new OrbitControls(kamera, opt.canvas);
  steuerung.enableDamping = false;
  steuerung.screenSpacePanning = true;

  const modellGruppe = new THREE.Group();
  szene.add(modellGruppe);
  const kegelGruppe = new THREE.Group();
  szene.add(kegelGruppe);
  const kegelMaterial = new THREE.LineBasicMaterial({ color: new THREE.Color(opt.kegelFarbe ?? '#e0873a') });
  const kantenMaterial = new THREE.LineBasicMaterial({ color: 0x4a4d55, transparent: true, opacity: 0.55 });
  const geteilt = new Set<THREE.Material>([kegelMaterial, kantenMaterial]);

  let box: Huellbox | null = null;
  let kameras: readonly VorschauKamera[] = [];
  let pausiert = false;
  let entsorgt = false;
  let kontextWeg = false;
  let hilfsZiel: THREE.WebGLRenderTarget | null = null;
  /** Kugel um Modell und Kegel — daraus `near`/`far` bei jedem Zeichnen. */
  let kugel: { mitte: THREE.Vector3; radius: number } | null = null;

  const setzeKugel = () => {
    if (!box) {
      kugel = null;
      return;
    }
    const punkte: Vec3[] = [];
    for (const k of kameras) if (istEndlich(k.position)) punkte.push(k.position);
    // Die Kegel reichen eine Kegellänge über den Standpunkt hinaus.
    const h = huellkugel(box, punkte);
    const r = punkte.length > 0 ? h.radius + kegelLaenge(box) * 1.5 : h.radius;
    kugel = { mitte: new THREE.Vector3(h.mitte[0], h.mitte[1], h.mitte[2]), radius: r };
  };

  /** `near`/`far` einer Kamera aus ihrem Abstand zur Kugel — vor jedem Zeichnen. */
  const fuehreSchnittNach = (k: THREE.PerspectiveCamera) => {
    if (!kugel) return;
    const { near, far } = nahUndFern(k.position.distanceTo(kugel.mitte), kugel.radius);
    if (k.near !== near || k.far !== far) {
      k.near = near;
      k.far = far;
      k.updateProjectionMatrix();
    }
  };

  const zeichne = () => {
    if (pausiert || entsorgt || kontextWeg) return;
    fuehreSchnittNach(kamera);
    renderer.render(szene, kamera);
  };
  steuerung.addEventListener('change', zeichne);

  const leere = (gruppe: THREE.Group) => {
    for (const kind of [...gruppe.children]) {
      gruppe.remove(kind);
      kind.traverse((o) => {
        const m = o as THREE.Mesh;
        m.geometry?.dispose();
        const mat = m.material as THREE.Material | THREE.Material[] | undefined;
        for (const x of Array.isArray(mat) ? mat : mat ? [mat] : []) {
          for (const wert of Object.values(x)) {
            if (wert instanceof THREE.Texture) wert.dispose();
          }
          if (!geteilt.has(x)) x.dispose();
        }
      });
    }
  };

  const setzeKegel = () => {
    leere(kegelGruppe);
    if (!box) return;
    const l = kegelLaenge(box);
    for (const k of kameras) {
      const punkte = kegelLinien(k, l);
      if (!punkte) continue;
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.BufferAttribute(punkte, 3));
      kegelGruppe.add(new THREE.LineSegments(g, kegelMaterial));
    }
    setzeKugel();
  };

  /** Materialien absichern, Normalen nachrechnen, Kanten anhängen (siehe Kopf). */
  const bereiteModell = (wurzel: THREE.Object3D) => {
    const netze: THREE.Mesh[] = [];
    let dreiecke = 0;
    wurzel.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh || !m.geometry) return;
      netze.push(m);
      sichereNetz(m.geometry);
      const idx = m.geometry.getIndex();
      const pos = m.geometry.getAttribute('position');
      dreiecke += (idx ? idx.count : pos ? pos.count : 0) / 3;
      const mats = Array.isArray(m.material) ? m.material : [m.material];
      for (const mat of mats) if (mat) sichereMaterial(mat as unknown as MaterialLike);
    });
    if (dreiecke > KANTEN_HOECHSTENS_DREIECKE) return;
    for (const m of netze) {
      try {
        const kanten = new THREE.LineSegments(new THREE.EdgesGeometry(m.geometry, KANTEN_WINKEL_GRAD), kantenMaterial);
        kanten.name = 'kanten';
        kanten.raycast = () => {};
        m.add(kanten);
      } catch {
        // Ein Netz ohne brauchbare Flächen bekommt keine Kanten; das Modell zeigt es trotzdem.
      }
    }
  };

  const setzeAnsicht = (a: Pick<Ansicht, 'position' | 'target'>) => {
    kamera.position.set(a.position[0], a.position[1], a.position[2]);
    steuerung.target.set(a.target[0], a.target[1], a.target[2]);
    kamera.lookAt(steuerung.target);
    steuerung.update();
  };

  const rahmen = () => {
    if (!box) return;
    const a = rahmeHuellbox(box, VORSCHAU_FOV_GRAD, seitenverhaeltnis);
    const radius = laenge([box.max[0] - box.min[0], box.max[1] - box.min[1], box.max[2] - box.min[2]]) / 2;
    steuerung.minDistance = Math.max(radius * 0.05, 0.05);
    steuerung.maxDistance = Math.max(radius * 20, 5);
    setzeAnsicht(a);
    zeichne();
  };

  // three ruft beim Verlust selbst `preventDefault` (sonst käme der Kontext nie zurück) und baut
  // nach `webglcontextrestored` seinen Zustand neu auf; hier nur: nicht zeichnen, Bescheid geben,
  // danach einmal neu zeichnen.
  const beiVerlust = (e: Event) => {
    e.preventDefault();
    kontextWeg = true;
    opt.onKontextVerloren?.();
  };
  const beiRueckkehr = () => {
    kontextWeg = false;
    // Die Umgebung lag im verlorenen Kontext; ohne sie wäre das Haus wieder dunkel.
    setzeUmgebung();
    zeichne();
    opt.onKontextZurueck?.();
  };
  opt.canvas.addEventListener('webglcontextlost', beiVerlust);
  opt.canvas.addEventListener('webglcontextrestored', beiRueckkehr);

  const lader = new GLTFLoader();

  return {
    ladeGlb(bytes) {
      return new Promise<void>((ok, fehler) => {
        lader.parse(
          bytes,
          '',
          (gltf) => {
            if (entsorgt) {
              ok();
              return;
            }
            leere(modellGruppe);
            bereiteModell(gltf.scene);
            modellGruppe.add(gltf.scene);
            const b3 = new THREE.Box3().setFromObject(gltf.scene);
            box = b3.isEmpty()
              ? null
              : { min: [b3.min.x, b3.min.y, b3.min.z], max: [b3.max.x, b3.max.y, b3.max.z] };
            setzeKegel();
            rahmen();
            ok();
          },
          (e) => fehler(e instanceof Error ? e : new Error(String(e))),
        );
      });
    },
    setzeKameras(neu) {
      kameras = neu;
      setzeKegel();
      zeichne();
    },
    setzeGroesse(breite, hoehe) {
      const b = Math.max(1, Math.round(breite));
      const h = Math.max(1, Math.round(hoehe));
      seitenverhaeltnis = b / h;
      kamera.aspect = seitenverhaeltnis;
      kamera.updateProjectionMatrix();
      renderer.setSize(b, h, false);
      zeichne();
    },
    setzePixeldichte(dichte) {
      if (renderer.getPixelRatio() === dichte) return;
      renderer.setPixelRatio(dichte);
      const groesse = renderer.getSize(new THREE.Vector2());
      renderer.setSize(groesse.x, groesse.y, false);
      zeichne();
    },
    zoome(faktor) {
      if (!(faktor > 0) || !Number.isFinite(faktor)) return;
      const versatz = kamera.position.clone().sub(steuerung.target).divideScalar(faktor);
      const l = Math.min(Math.max(versatz.length(), steuerung.minDistance), steuerung.maxDistance);
      versatz.setLength(l);
      kamera.position.copy(steuerung.target).add(versatz);
      steuerung.update();
    },
    rahmen,
    ansicht() {
      return {
        position: [kamera.position.x, kamera.position.y, kamera.position.z],
        target: [steuerung.target.x, steuerung.target.y, steuerung.target.z],
        near: kamera.near,
        far: kamera.far,
      };
    },
    setzeAnsicht(a) {
      setzeAnsicht(a);
      zeichne();
    },
    blickvorschau(index, breite = 96, hoehe = 64) {
      const k = kameras[index];
      if (!k || !box || entsorgt || kontextWeg) return null;
      const b = Math.max(1, Math.round(breite));
      const h = Math.max(1, Math.round(hoehe));
      if (!hilfsZiel || hilfsZiel.width !== b || hilfsZiel.height !== h) {
        hilfsZiel?.dispose();
        hilfsZiel = new THREE.WebGLRenderTarget(b, h, { colorSpace: THREE.SRGBColorSpace });
      }
      const asp = b / h;
      const fovV = k.fovVertikalGrad !== undefined && k.fovVertikalGrad > 0
        ? k.fovVertikalGrad
        : (2 * Math.atan(Math.tan((Math.min(Math.max(k.fov, 1), 179) * GRAD) / 2) / asp)) / GRAD;
      const hilfsKamera = new THREE.PerspectiveCamera(fovV, asp, kamera.near, kamera.far);
      hilfsKamera.up.set(0, 1, 0);
      hilfsKamera.position.set(k.position[0], k.position[1], k.position[2]);
      hilfsKamera.lookAt(k.target[0], k.target[1], k.target[2]);
      fuehreSchnittNach(hilfsKamera);
      const kegelSichtbar = kegelGruppe.visible;
      kegelGruppe.visible = false;
      renderer.setRenderTarget(hilfsZiel);
      renderer.render(szene, hilfsKamera);
      const roh = new Uint8Array(b * h * 4);
      renderer.readRenderTargetPixels(hilfsZiel, 0, 0, b, h, roh);
      renderer.setRenderTarget(null);
      kegelGruppe.visible = kegelSichtbar;
      // WebGL liest von unten nach oben; ein Bild läuft von oben nach unten.
      const daten = new Uint8ClampedArray(b * h * 4);
      const zeile = b * 4;
      for (let y = 0; y < h; y++) daten.set(roh.subarray((h - 1 - y) * zeile, (h - y) * zeile), y * zeile);
      zeichne();
      return { breite: b, hoehe: h, daten };
    },
    pausiere() {
      pausiert = true;
    },
    fortsetzen() {
      if (!pausiert) return;
      pausiert = false;
      zeichne();
    },
    zeichne,
    dispose() {
      if (entsorgt) return;
      entsorgt = true;
      steuerung.removeEventListener('change', zeichne);
      steuerung.dispose();
      opt.canvas.removeEventListener('webglcontextlost', beiVerlust);
      opt.canvas.removeEventListener('webglcontextrestored', beiRueckkehr);
      leere(modellGruppe);
      leere(kegelGruppe);
      kegelMaterial.dispose();
      kantenMaterial.dispose();
      umgebung?.dispose();
      szene.environment = null;
      hilfsZiel?.dispose();
      renderer.dispose();
      // Den Kontext ausdrücklich zurückgeben: Browser verwerfen ab etwa 16 Kontexten den
      // ältesten, und ein entsorgtes Fenster soll nicht mitzählen.
      renderer.forceContextLoss();
    },
  };
}
