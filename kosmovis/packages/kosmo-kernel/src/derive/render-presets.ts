/**
 * Cycles-Presets (Owner-Befund K20/A10) — benannte, regelbasierte Render-Presets
 * als reine Datentabelle. Kein «KI wählt» — ein Klick auf einen Namen setzt
 * exakt diese Werte (Samples, Auflösung, Licht-Setup) und die zugehörigen
 * Bildkompositions-Metadaten (Seitenverhältnis, Brennweiten-Äquivalent,
 * Horizontlinie), die unverändert in den render-scene/v1-Job einfliessen.
 * Angewandt wird ein Preset über den bestehenden `vis.nodeParametrieren`-Weg
 * (Render-Node-Param `preset`) — kein neuer Command nötig.
 *
 * 16.09.2026, ZEILE 4 der Abnahmeliste: vierter Eintrag «Innenraum
 * (Architektur)», dazu drei additive OPTIONALE Felder (`render.sun`-Details,
 * `render.himmel`, `bild`). Die drei alten Presets führen keines davon und
 * bleiben Zahl für Zahl unverändert — wer ohne Preset oder mit einem der
 * alten rendert, schickt weiterhin dieselbe Nutzlast wie zuvor.
 *
 * WER DIESE NEUEN FELDER LIEST: `derive/visgraph.ts` reicht unverändert nur
 * `samples`/`resolution`/`sun`/`komposition` weiter. Die neuen Felder werden
 * in der App gelesen (`apps/kosmo-orbit/src/modules/vis/vis-jobs.ts`,
 * `sendeGraphRenderAuftrag`) und von dort an den Auftrag gehängt. Das ist
 * bewusst und benannt: `visgraph.ts` gehört in dieser Bauwelle keinem Agenten,
 * und eine Datei, die einem nicht gehört, fasst man nicht an.
 */

export const VIS_PRESET_IDS = ['entwurf-schnell', 'praesentation', 'nacht', 'innenraum'] as const;

/**
 * Die vier Himmelsarten, die Blender 5.2 WIRKLICH hat — am Gerät nachgesehen
 * am 11.09.2026 (`docs/RENDERPROJEKT-2026-09-10/00-CHRONIK.md` §5): «Die
 * Himmelsart NISHITA gibt es nicht mehr. Vorhanden sind SINGLE_SCATTERING,
 * MULTIPLE_SCATTERING, PREETHAM, HOSEK_WILKIE.» Die Liste ist darum KEINE
 * Auswahl, die wir uns ausgedacht haben, sondern eine abgeschriebene — wer
 * sie erweitert, sieht vorher am Gerät nach, nicht in der Erinnerung.
 * Zugehöriger Befund derselben Stelle: das Streuungsfeld heisst
 * `aerosol_density`, nicht mehr `dust_density` — darum unten `aerosoldichte`.
 */
export const HIMMEL_ARTEN = ['SINGLE_SCATTERING', 'MULTIPLE_SCATTERING', 'PREETHAM', 'HOSEK_WILKIE'] as const;

export type HimmelArt = (typeof HIMMEL_ARTEN)[number];

export function istHimmelArt(v: unknown): v is HimmelArt {
  return typeof v === 'string' && (HIMMEL_ARTEN as readonly string[]).includes(v);
}

export type VisPresetId = (typeof VIS_PRESET_IDS)[number];

export function isVisPresetId(v: unknown): v is VisPresetId {
  return typeof v === 'string' && (VIS_PRESET_IDS as readonly string[]).includes(v);
}

export interface VisPreset {
  readonly id: VisPresetId;
  /** Deutscher Anzeigename fürs UI. */
  readonly name: string;
  readonly render: {
    readonly samples: number;
    readonly resolution: readonly [number, number];
    /** Sonnenstand (Azimut/Elevation, Grad) — Elevation < 0 = Sonne unter dem Horizont (Nacht). */
    readonly sun: {
      readonly azimuth: number;
      readonly elevation: number;
      /**
       * ZEILE 4 (Abnahmeliste, 10.09.2026) — die Lichtdetails, additiv und
       * OPTIONAL: die drei bestehenden Presets haben sie nicht und bleiben
       * darum Zahl für Zahl unverändert. Nur `innenraum` führt sie, und zwar
       * mit den Werten, mit denen das vom Owner ANGENOMMENE Bild wirklich
       * gerechnet wurde (00-CHRONIK.md §6 «Die Zahlen am Ende»).
       * Blender-Namen dahinter: `staerke` = `sun.energy`, `kelvin` =
       * Schwarzkörper-Farbtemperatur, `winkelGrad` = `sun.angle`.
       */
      readonly staerke?: number;
      readonly kelvin?: number;
      readonly winkelGrad?: number;
    };
    /**
     * Himmel als Lichtquelle (ZEILE 47). Optional — ohne dieses Feld bleibt
     * der Auftrag wie bisher ohne jede Himmelsangabe.
     */
    readonly himmel?: {
      readonly modell: HimmelArt;
      readonly staerke: number;
      /** Blender `air_density`. */
      readonly luftdichte: number;
      /** Blender `aerosol_density` (hiess vor 5.2 `dust_density`). */
      readonly aerosoldichte: number;
    };
    /** Cycles-Rauschschwelle (`adaptive_threshold`). Optional, kein Vorgabewert. */
    readonly rauschschwelle?: number;
  };
  /**
   * Bildseite des Presets (ZEILE 4, zweite Hälfte «und Licht»): Belichtung und
   * Farbraum sind KEINE Render-Einstellung, sondern die Farbverwaltung
   * (`scene.view_settings`). Optional aus demselben Grund wie die Lichtdetails
   * oben — die drei alten Presets führen sie nicht.
   */
  readonly bild?: {
    /** `view_settings.exposure`. */
    readonly belichtung: number;
    /** `view_settings.view_transform`. */
    readonly farbraum: 'AgX' | 'Filmic' | 'Standard' | 'Raw';
    /** `view_settings.look`, z.B. «Base Contrast». */
    readonly anmutung: string;
  };
  readonly komposition: {
    /** Breite/Höhe, z.B. 1.6 = 16:10. */
    readonly seitenverhaeltnis: number;
    /** Brennweiten-Äquivalent (Kleinbild, 36 mm Sensorbreite) in mm. */
    readonly brennweiteMm: number;
    /** Horizontlinie als Anteil der Bildhöhe von oben (0 = oberer Rand, 1 = unterer Rand). */
    readonly horizontlinie: number;
  };
  /** Ehrliche Kurzbeschreibung des Licht-Setups fürs UI und den Render-Prompt. */
  readonly licht: string;
}

export const RENDER_PRESETS: readonly VisPreset[] = [
  {
    id: 'entwurf-schnell',
    name: 'Entwurf schnell',
    render: {
      samples: 32,
      resolution: [960, 600],
      sun: { azimuth: 180, elevation: 45 },
    },
    komposition: { seitenverhaeltnis: 1.6, brennweiteMm: 35, horizontlinie: 0.5 },
    licht: 'Flaches Mittagslicht — schnelle Vorschau, keine Stimmung.',
  },
  {
    id: 'praesentation',
    name: 'Präsentation',
    render: {
      samples: 256,
      resolution: [1920, 1200],
      sun: { azimuth: 200, elevation: 32 },
    },
    komposition: { seitenverhaeltnis: 1.6, brennweiteMm: 50, horizontlinie: 0.42 },
    licht: 'Warmes Nachmittagslicht mit Schlagschatten — für Präsentationsbilder.',
  },
  {
    id: 'nacht',
    name: 'Nacht',
    render: {
      samples: 192,
      resolution: [1920, 1200],
      sun: { azimuth: 0, elevation: -8 },
    },
    komposition: { seitenverhaeltnis: 1.6, brennweiteMm: 40, horizontlinie: 0.55 },
    licht: 'Nachtszene — Sonne unter dem Horizont, Fenster-/Kunstlicht dominiert.',
  },
  /**
   * ZEILE 4 der Abnahmeliste, Zuruf vom 10.09.2026: «bitte recherchiere noch
   * kamera und lichteinstellungen online fuer architektur innenraumbilder».
   *
   * DIE QUELLE IST BESSER ALS EINE RECHERCHE. Die Werte unten sind nicht aus
   * dem Netz zusammengelesen, sondern aus dem Renderprojekt abgeschrieben, in
   * dem dieser Zuruf fiel: es sind die Zahlen, mit denen das Bild entstanden
   * ist, das der Owner am Ende ANGENOMMEN hat
   * (`docs/RENDERPROJEKT-2026-09-10/00-CHRONIK.md`, §6 «Die Zahlen am Ende»).
   *
   * GEMESSEN — Zahl für Zahl aus §6 übernommen:
   *   Auflösung 4000×2667 · Abtastungen 2048 bei Rauschschwelle 0,005 ·
   *   Belichtung 2,70, Farbraum AgX, Anmutung «Base Contrast» ·
   *   Sonne Stärke 6,0 bei 4900 K, Winkeldurchmesser 0,62 Grad ·
   *   Himmel Stärke 1,0, Luftdichte 0,40, Aerosoldichte 3,0.
   *
   * NICHT GEMESSEN, und darum hier ausdrücklich benannt statt still gesetzt:
   * - `sun.azimuth`/`sun.elevation`: die Chronik hält für das angenommene Bild
   *   KEINEN Sonnenstand in Zahlen fest. Übernommen ist deshalb der Stand von
   *   «Präsentation» (200/32, warmes Nachmittagslicht) — ein bestehender Wert
   *   dieser Tabelle, keine neue Erfindung. Der Stand selbst gehört ohnehin
   *   ZEILE 3 (Datum/Uhrzeit, «ca. 18:00 Sommerzeit»), nicht dieser Zeile.
   * - `komposition.brennweiteMm` 24: die Kamera kam von Hand aus ArchiCAD
   *   (Zeile 1), ihre Brennweite steht nirgends. 24 mm ist die übliche
   *   Weitwinkel-Brennweite der Architektur-Innenaufnahme — eine KONVENTION,
   *   und genau das, wonach der Zuruf gefragt hat. Kein gemessener Wert.
   * - `komposition.horizontlinie` 0,5: folgt der Augenhöhe von 1,30 m, die in
   *   diesem Repo schon als Kamerahöhe geführt wird
   *   (`kosmo-contracts/src/render-scene.ts`, P-ACHSENRIEGEL) — in einem Raum
   *   von rund 2,6 m liegt sie auf halber Bildhöhe. Hergeleitet, nicht gemessen.
   * - `seitenverhaeltnis` 1,5: gerundet aus 4000/2667 (= 1,49981…).
   * - `himmel.modell` MULTIPLE_SCATTERING: die Chronik nennt die vier
   *   VORHANDENEN Arten und die drei Himmelszahlen, aber nicht, welche Art
   *   gewählt war. GESCHLOSSEN, nicht abgelesen: Luftdichte und Aerosoldichte
   *   sind Felder der beiden Streuungsmodelle — PREETHAM und HOSEK_WILKIE
   *   kennen sie nicht, die rechnen über Trübung. Ein Himmel, der mit diesen
   *   beiden Zahlen eingestellt war, kann darum nur eines der beiden
   *   Streuungsmodelle gewesen sein. Zwischen einfacher und mehrfacher
   *   Streuung entscheidet dieser Schluss NICHT — die Wahl ist hier gesetzt,
   *   und wer sie umstellen will, hat keinen Widerspruch zu befürchten.
   */
  {
    id: 'innenraum',
    name: 'Innenraum (Architektur)',
    render: {
      samples: 2048,
      rauschschwelle: 0.005,
      resolution: [4000, 2667],
      sun: { azimuth: 200, elevation: 32, staerke: 6.0, kelvin: 4900, winkelGrad: 0.62 },
      himmel: { modell: 'MULTIPLE_SCATTERING', staerke: 1.0, luftdichte: 0.4, aerosoldichte: 3.0 },
    },
    bild: { belichtung: 2.7, farbraum: 'AgX', anmutung: 'Base Contrast' },
    komposition: { seitenverhaeltnis: 1.5, brennweiteMm: 24, horizontlinie: 0.5 },
    licht:
      'Innenraum wie im angenommenen Bild: Sonne 6,0 bei 4900 K (Winkel 0,62°), ' +
      'Himmel 1,0 mit Luftdichte 0,40 und Aerosoldichte 3,0, Belichtung 2,70 in AgX.',
  },
];

export function visPresetById(id: VisPresetId): VisPreset {
  const hit = RENDER_PRESETS.find((p) => p.id === id);
  if (!hit) throw new Error(`Unbekanntes Vis-Preset «${id}»`);
  return hit;
}

/**
 * Horizontales Blickfeld (Grad) aus dem Brennweiten-Äquivalent, Kleinbild-Sensor
 * (36 mm Breite) — Standardformel FOV = 2·atan(Sensorbreite / (2·Brennweite)).
 * Rein rechnerisch, keine Schätzung.
 */
export function fovFromBrennweite(brennweiteMm: number, sensorbreiteMm = 36): number {
  const rad = 2 * Math.atan(sensorbreiteMm / (2 * brennweiteMm));
  return Math.round((rad * 180) / Math.PI);
}
