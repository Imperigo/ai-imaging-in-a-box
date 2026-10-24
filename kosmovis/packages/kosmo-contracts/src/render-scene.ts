import { z } from 'zod';

/**
 * kosmovis.render-scene/v1 — Eingabevertrag für einen KosmoVis-Render-Job.
 * Quelle: KosmoVis-ETH-Bericht §5.2 (docs/RENDER_SCENE_CONTRACT.md auf der
 * HomeStation). Minimum = geometry + out; alles andere hat Defaults.
 */

export const GeometryFormat = z.enum(['glb', 'gltf', 'fbx', 'blend', 'ifc']);

/**
 * P-ACHSENRIEGEL (26.08.2026, HomeStation-Befund, Beispielprojekt →
 * Vis-Station → Graph aus Modell → Auto-Kamera → Render → Aufs Blatt →
 * Ausführen): `up_axis` ist PFLICHT, KEIN Default. Der Vorfall, der das
 * erzwingt — `kamerahoehe_m (77.023) liegt ueber gebaeudehoehe_m (21.3)`,
 * Faktor 3,6 zu hoch — war kein Rechenfehler, sondern genau diese
 * Vertragslücke: `position`/`target` trugen bis hierhin NIRGENDS im
 * Vertrag, welche Achse "oben" ist. `derive/kamera.ts` (kosmo-kernel)
 * schreibt seit v0.6.3 glTF-Konvention (Y = oben, Meter) — belegt am
 * eigenen glTF-Exporter, `derive/gltf.ts:143-145`, byte-identische
 * Formel zu `kamera.ts`s `toGlb` —, ein unabhängig gemessener Wert
 * (`bbox_size_m`, vom Worker selbst berichtet, nicht Teil dieses
 * Vertrags) führte für dieselbe Szene Z als Höhe. Der Verbraucher hatte
 * keine Möglichkeit, das zu unterscheiden, und hat geraten (Index 2 statt
 * Index 1) — 76.723 m (die Tiefen-Koordinate) statt 1.3 m (die echte
 * Augenhöhe). Der Riegel jetzt: ABWEISEN statt raten. Ein Datensatz ohne
 * `up_axis` ist kein Rückwärtskompatibilitäts-Fall (`position`/`target`
 * waren VORHER schon mehrdeutig, es gibt keinen "alten, aber gültigen"
 * Sinn ohne diese Angabe) — jeder Erzeuger MUSS die Achse explizit
 * benennen. Alle eigenen Erzeuger dieser App senden `'y'` (s.
 * `vis-jobs.ts` `postRenderJob`, spiegelt `kamera.ts`s reale Konvention).
 */
/**
 * R2 (auf-20260901-68, Owner-Entscheid 03.09.2026) — der REFERENZPUNKT der
 * Kamera-Augenhoehe, additiv neben `position`/`target`. Hintergrund: die
 * Kamerarechnung in `packages/kosmo-kernel/src/derive/kamera.ts` misst die
 * Augenhoehe historisch ueber `b.minZ`, dem tiefsten Punkt IRGENDEINER
 * Geometrie — bei einer 300 mm dicken Bodenplatte kostete das 30 cm, bei
 * einem Projekt mit zwei Untergeschossen mehrere Meter, weil der Bezug
 * unbenannt blieb. Eine Hoehe ohne ihren Nullpunkt ist keine Hoehe.
 *
 * Owner-Entscheid: die vier Namen des Absenders werden 1:1 UEBERNOMMEN,
 * keine eigenen — es ist sein Vokabular, und ein eigener Satz Namen schuefe
 * eine Uebersetzungsstelle, an der spaeter jemand falsch abbiegt. Bedeutung
 * je Wert (aus dem Auftragsblatt, nicht selbst festgelegt):
 * - `terrain_an_kamera` — Gelaendehoehe an der Kameraposition (verlaesslich).
 * - `okff` — Oberkante Fertigfussboden des Bezugsgeschosses (verlaesslich).
 * - `huellbox_unterkante` — `b.minZ`, der tiefste Punkt irgendeiner Geometrie
 *   (NICHT verlaesslich — genau der bisherige, unbenannte Fallback).
 * - `weltnull` — der globale Koordinatenursprung (NICHT verlaesslich).
 *
 * KEIN Default. Ein fehlendes `referenzpunkt`-Feld heisst «kein Bezugspunkt
 * genannt», nicht `huellbox_unterkante` — ein stiller Default waere genau
 * die stillschweigende Festlegung, gegen die dieses Feld gebaut wurde.
 *
 * NUR der Vertrag ist hier gebaut. `packages/kosmo-kernel/src/derive/
 * kamera.ts` — der Erzeuger, der dieses Feld tatsaechlich SETZEN muesste —
 * liegt ausserhalb des Dateikreises dieses Pakets und ist NICHT angepasst.
 */
export const CameraReferenzpunkt = z.enum([
  'terrain_an_kamera',
  'okff',
  'huellbox_unterkante',
  'weltnull',
]);

export const CameraSpec = z.object({
  name: z.string().optional(),
  position: z.tuple([z.number(), z.number(), z.number()]),
  target: z.tuple([z.number(), z.number(), z.number()]),
  fov: z.number().min(10).max(120).default(50),
  /** 'y' = glTF-Konvention (Meter, Y oben) — was diese App tatsächlich
   * erzeugt. 'z' bleibt gültig für Erzeuger, die architektonisch/CAD-nativ
   * (Z oben) senden — der Verbraucher liest DIESES Feld, statt zu raten. */
  up_axis: z.enum(['y', 'z']),
  /** R2 — siehe Nachtrag oben. Additiv, optional, kein Default. */
  referenzpunkt: CameraReferenzpunkt.optional(),
  /**
   * Vorschlag V (Knoten «Kamera», Visbox-Entscheid 109 C, 21.10.2026): «senkrecht» haelt die
   * Senkrechten senkrecht (Zwei-Punkt-Perspektive, die Bildseite rechnet einen Objektiv-Shift
   * und blickt waagrecht), «frei» kippt die Kamera auf das Ziel. Fehlt das Feld, gilt wie
   * bisher «frei» (gekippt) — additiv, alte Bestellungen bleiben Zeichen fuer Zeichen gleich.
   */
  perspektive: z.enum(['senkrecht', 'frei']).optional(),
});

/**
 * Vorschlag V (Visbox-Entscheide 110 B / 113, 20.10.2026): die acht Stimmungen in der
 * Reihenfolge der Visbox (`aiimaging.stimmung.STIMMUNGEN`, Kern `VIS_STIMMUNGEN`). Die ersten
 * drei Werte von frueher (morgen, abend, weiss) bleiben gueltig.
 */
export const StimmungPreset = z.enum(['morgen', 'mittag', 'abend', 'blaue-stunde', 'bedeckt', 'nebel', 'winter', 'weiss']);
export type StimmungPreset = z.infer<typeof StimmungPreset>;

/**
 * Vorschlag V (Knoten «Kamera»): die zwoelf Richtungskuerzel des Heim-PCs
 * (`aiimaging.kameras.RICHTUNGEN`) — vier frontal, acht ueber Eck.
 */
export const AutoRichtung = z.enum(['n', 'e', 's', 'w', 'nNE', 'nNW', 'eEN', 'eES', 'sSE', 'sSW', 'wWS', 'wWN']);
export type AutoRichtung = z.infer<typeof AutoRichtung>;

/**
 * Vorschlag V (Visbox-Entscheide 109/113 (3), 20.10.2026): die Auto-Kamera rechnet der Heim-PC,
 * mit den Einstellungen des Knotens. Alles ausser `richtungen` optional und OHNE Vorgabe — der
 * Heim-PC setzt die Vorgaben (1,70 m, 35 mm, Haus fuellt 70 %, senkrecht) und nennt sie im
 * Ergebnis (`angewandt.cameras_auto.vorgaben`). Nur mit `cameras: 'auto'` (superRefine).
 */
export const CamerasAuto = z.object({
  richtungen: z.array(AutoRichtung).min(1).max(8),
  /** Ueber dem Gelaende am Standpunkt, Meter. */
  augenhoehe_m: z.number().min(0.5).max(50).optional(),
  brennweite_mm: z.union([z.literal(24), z.literal(35), z.literal(50)]).optional(),
  abstand: z
    .discriminatedUnion('art', [
      z.object({ art: z.literal('auto'), fuellt: z.number().min(0.2).max(0.95).optional() }),
      z.object({ art: z.literal('fest'), meter: z.number().min(2).max(2000) }),
    ])
    .optional(),
  perspektive: z.enum(['senkrecht', 'frei']).optional(),
});
export type CamerasAuto = z.infer<typeof CamerasAuto>;

/**
 * Vorschlag V (Visbox-Entscheid 111, 20.10.2026): ein Material der Bibliothek fuer eine
 * Bauteil-Art. `id` ist die Kennung der Bibliothek; der Heim-PC prueft sie gegen seine Ablage
 * und weist Unbekanntes mit Satz ab (Entscheid 113 (2)). Keine Vorgaben hier — der Heim-PC
 * setzt sie (1 m, 0°, Relief 0,6) und nennt sie im Ergebnis.
 */
export const MaterialWahl = z.object({
  id: z.string().regex(/^[a-z0-9-]{1,48}$/),
  massstab_m: z.number().min(0.05).max(20).optional(),
  drehungGrad: z.number().min(0).max(360).optional(),
  relief: z.number().min(0).max(1).optional(),
  toenung: z
    .object({ farbe: z.string().regex(/^#[0-9a-fA-F]{6}$/), staerke: z.number().min(0).max(1) })
    .optional(),
});
export type MaterialWahl = z.infer<typeof MaterialWahl>;

/** Die fuenf Bauteil-Arten (Visbox `materialwahl.ARTEN`); Tueren zaehlen zu «uebrige» (113 (7)). */
export const BAUTEIL_ARTEN = ['fassade', 'dach', 'fenster', 'boden', 'uebrige'] as const;
export type BauteilArt = (typeof BAUTEIL_ARTEN)[number];

/** Ausdruecklich je Schluessel (kein `z.record(enum)`: zod 4 verlangt dort alle Schluessel). */
export const Materialien = z.object({
  fassade: MaterialWahl.optional(),
  dach: MaterialWahl.optional(),
  fenster: MaterialWahl.optional(),
  boden: MaterialWahl.optional(),
  uebrige: MaterialWahl.optional(),
});
export type Materialien = z.infer<typeof Materialien>;

/**
 * kv-ebenen (E124): die drei Ebenen, die die Gegenseite je Kamera liefern
 * kann (Blatt `erg-20260929-e124` §2). Gilt fuer die Bestellung
 * (`render.passes`) und fuer den Rueckweg (`RenderResult.ebenen[].art`).
 */
export const EbenenArt = z.enum(['schoenbild', 'tiefe', 'material-id']);
export type EbenenArt = z.infer<typeof EbenenArt>;

/** A1: die Hoechstlaenge eines Skizzennamens (Zeichen). */
export const SKIZZENNAME_HOECHSTENS = 255;

/**
 * Auflage A1 des Integrators (15.10.2026, beim Absegnen von `RenderScene.skizze`): der Name der
 * Skizze ist ein RELATIVER Pfad IN der Mappe — nie ein Weg hinaus. Die Bildseite schlaegt ihn in
 * ihrer Mappe nach und prueft das unabhaengig nochmals (Visbox `kosmo_szene.skizzenname_mangel`);
 * hier wird er schon beim Bau der Bestellung abgewiesen, damit ein Name wie `../../etc/passwd`
 * gar nicht erst reist.
 *
 * Abgewiesen: laenger als 255 Zeichen; Steuerzeichen (U+0000–U+001F, U+007F); ein Backslash
 * ueberhaupt (auch fuehrend); ein fuehrender `/`; ein Laufwerksbuchstabe wie `C:`; ein Segment
 * `.` oder `..`.
 *
 * @returns der Satz, warum der Name nicht geht — oder `null`, wenn er geht.
 */
export function skizzenNameMangel(name: string): string | null {
  if (name.length > SKIZZENNAME_HOECHSTENS) {
    return `Der Name der Skizze ist ${name.length} Zeichen lang — hoechstens ${SKIZZENNAME_HOECHSTENS}.`;
  }
  // eslint-disable-next-line no-control-regex
  if (/[\u0000-\u001f\u007f]/.test(name)) return 'Der Name der Skizze enthaelt ein Steuerzeichen.';
  if (name.includes('\\')) {
    return 'Der Name der Skizze enthaelt einen Backslash — er ist ein relativer Pfad in der Mappe, mit «/» getrennt.';
  }
  if (name.startsWith('/')) return 'Der Name der Skizze beginnt mit «/» — er ist ein relativer Pfad in der Mappe.';
  if (/^[A-Za-z]:/.test(name)) return 'Der Name der Skizze beginnt mit einem Laufwerk — er ist ein relativer Pfad in der Mappe.';
  if (name.split('/').some((teil) => teil === '.' || teil === '..')) {
    return 'Der Name der Skizze enthaelt «.» oder «..» als Teil — er bleibt in der Mappe.';
  }
  return null;
}

export const RenderScene = z.object({
  schema: z.literal('kosmovis.render-scene/v1').default('kosmovis.render-scene/v1'),
  geometry: z.object({
    path: z.string(),
    format: GeometryFormat,
  }),
  out: z.string(),
  cameras: z
    .union([z.literal('auto'), z.literal('saved'), z.array(CameraSpec).min(1)])
    .default('auto'),
  /** Vorschlag V: die Einstellungen der Auto-Kamera (`CamerasAuto`), nur mit `cameras: 'auto'`. */
  cameras_auto: CamerasAuto.optional(),
  /**
   * AUFTRAG DREI (auftraege/von-homestation/auf-orbit-20260821-02.md,
   * Abschnitt «DREI: INNENANSICHTEN SIND FERTIG UND BEI EUCH UNBESTELLBAR»):
   * `interior` ist KANONISCH, mit SEINEN Schluesseln — er liest den Auftrag,
   * also gewinnt sein Name (dieselbe Regel, die `kantenanteil` in
   * render-result.ts vor `kante` gerettet hat).
   *
   * `rooms`: `'auto'` oder eine Liste von Raum-Bezeichnern (IFC-Raumnamen/
   * GUIDs — mindestens einer, ein leeres Array waere eine Bestellung ohne
   * Inhalt).
   *
   * BEWUSST KEIN `view`-Feld (frontal vs. ueber Eck). Woertlich aus seinem
   * Blatt: «NICHT von euch gebraucht: die Entscheidung frontal gegen ueber
   * Eck. Die haengt daran, ob die Stirnwand ein Motiv traegt — Kamin,
   * Kuechenzeile — und das steht in keiner IFC. Es werden beide gerechnet
   * und beide geliefert.» Ein Feld dafuer zu bauen waere erfundene
   * Genauigkeit: wir haetten eine Wahl angeboten, die er nicht treffen kann
   * und nicht treffen will — er liefert ohnehin beide Standpunkte.
   *
   * KEIN Default, `interior` bleibt `optional()`: ein Auftrag ohne dieses
   * Feld bestellt nichts, genau wie seine eigene Vorgabe drueben («gerechnet
   * werden die Standpunkte immer, gerendert nur auf Bestellung» — ein Haus
   * mit zwanzig Raeumen waeren sonst vierzig Renderlaeufe).
   *
   * Der IFC-Riegel unten (superRefine) greift fuer `interior` genauso wie
   * fuer `innenansichten`: aus glb/gltf/fbx/blend gibt es keine Raeume,
   * das ist sein Befund, nicht unsere Vermutung.
   */
  interior: z
    .object({
      rooms: z.union([z.literal('auto'), z.array(z.string()).min(1)]),
    })
    .optional(),
  /**
   * Y3 P-IFC-BESTELLUNG (V0942-SPEZ §4, B-8) — der urspruengliche Ausloeser
   * fuer Innenansichten, seit P-INTERIOR GEDULDETER ZWEITNAME (Auftrag DREI
   * oben): kanonisch ist `interior` — dasselbe Zweitname-Muster wie
   * `kante`/`kantenanteil` in render-result.ts, nichts, was in v0.9.42
   * gegen dieses Feld gebaut wurde, bricht. `innenansichten: true` bedeutet
   * `interior: { rooms: 'auto' }` — beide Wege loesen denselben IFC-Riegel
   * aus (superRefine unten). Default `false` — additiv, jeder bestehende
   * Auftrag ohne dieses Feld bleibt unveraendert gueltig.
   */
  innenansichten: z.boolean().default(false),
  render: z
    .object({
      resolution: z.tuple([z.number().int().positive(), z.number().int().positive()]).default([1600, 1000]),
      samples: z.number().int().positive().default(128),
      /** 0..1 — ControlNet-Strength: wie streng folgt die KI der Geometrie. */
      faithful: z.number().min(0).max(1).default(0.8),
      /**
       * SONNENSTAND — die Konvention, 24.08.2026 nachgetragen (B63, ROADMAP
       * 1092). Sie stand nie hier, obwohl das Feld seit v0.8.x existiert;
       * der KosmoVis-Worker hat danach gefragt, weil sein Blender-Schritt
       * die Sonne fest auf 50/35 stellt und ein bestellter Abendstand
       * darum ein **schoenes, falsches** Bild ergibt (F2).
       *
       * Sie ist **nicht erfunden, sondern aus den eigenen Presets gelesen**
       * (`kosmo-kernel/src/derive/render-presets.ts`), die sie seit jeher
       * stillschweigend voraussetzen:
       *  - `entwurf-schnell` 180/45 heisst dort «Flaches Mittagslicht» →
       *    **180 Grad ist Sued**, also wird `azimuth` **im Uhrzeigersinn ab
       *    Nord** gemessen (0=N, 90=O, 180=S, 270=W). Nicht gegen die
       *    +Y-Achse der Szene.
       *  - `praesentation` 200/32 heisst «Warmes Nachmittagslicht» — 200
       *    Grad liegt knapp westlich von Sued, passt.
       *  - `nacht` 0/**-8** heisst «Sonne unter dem Horizont». Das ist der
       *    entscheidende Beleg: `elevation` ist der **Stand ueber dem
       *    Horizont**, negativ = darunter. Ein Einfallswinkel waere hier
       *    sinnlos.
       *
       * Wer diese Bedeutung aendert, aendert die drei Presets mit — sie
       * sind der einzige Ort, an dem die Konvention bisher gelebt hat.
       */
      sun: z
        .object({
          /**
           * Grad, im Uhrzeigersinn ab Nord: 0=N, 90=O, 180=S, 270=W.
           *
           * P3 — WELTSYSTEM-KONVENTION FESTGEHALTEN (reine Dokumentation,
           * keine Vertragsaenderung, keine neue Regel). Dieses Feld wird
           * ausdruecklich «nicht gegen die +Y-Achse der Szene» gemessen,
           * sondern ab Nord — das setzt voraus, WO die Szene «Nord» hat, und
           * genau das stand bisher nirgends im Vertrag, nur als Kommentar in
           * einer Kern-Ableitung. Nachgetragen, mit Beleg:
           *
           *   +Y = Norden, +X = Osten.
           *
           * Beleg (kosmo-kernel, NUR gelesen, nicht angefasst):
           * - `packages/kosmo-kernel/src/model/units.ts:28` — «2D-Punkt in mm
           *   (Weltkoordinaten: x nach Osten, y nach Norden).»
           * - `packages/kosmo-kernel/src/model/doc.ts:590-592` — «In welche
           *   Himmelsrichtung zeigt die +Y-Achse des Projekts. 0 = nach
           *   Norden (Vorgabe, der heutige Stand). 90 = nach Osten.»
           * - `packages/kosmo-kernel/src/derive/plankopf.ts:777-778` —
           *   «`nordrichtungGrad` sagt, wohin die +Y-Achse zeigt.»
           *
           * Alle drei Fundstellen sagen dasselbe — keine Abweichung von
           * «+Y = Norden» gefunden, darum hier ohne Ruecksprache nachgetragen.
           */
          azimuth: z.number().min(0).max(360),
          /** Grad ueber dem Horizont; negativ = unter dem Horizont. */
          elevation: z.number().min(-90).max(90),
          /**
           * ZEILE 4 (60-ABNAHMELISTE.md, 16.09.2026) — WIE HELL und WIE WARM
           * die Sonne ist, nicht nur WO sie steht. Bis hierhin trug der
           * Vertrag ausschliesslich den Stand; Staerke und Farbtemperatur
           * waren am fernen Renderer fest verdrahtet, und ein bestelltes
           * Innenraumlicht kam darum als Vorgabelicht an.
           *
           * Die Zahlen, die diese Felder tragen sollen, sind GEMESSEN, nicht
           * angenommen: `docs/RENDERPROJEKT-2026-09-10/00-CHRONIK.md` §6
           * haelt fuer das vom Owner angenommene Bild «Sonne Staerke 6,0 bei
           * 4900 Kelvin, Winkeldurchmesser 0,62 Grad» fest.
           *
           * ALLE DREI OPTIONAL, KEIN VORGABEWERT — dieselbe Regel wie bei
           * `referenzpunkt` und `gelaende` weiter unten: ein fehlendes Feld
           * heisst «nicht bestellt», nicht «Vorgabe». Ein stiller Vorgabewert
           * waere eine Behauptung ueber das Licht, die niemand aufgestellt hat.
           *
           * Blender-Namen dahinter: `staerke` = `sun.energy`, `kelvin` =
           * Schwarzkoerper-Farbtemperatur des Sonnenlichts, `winkelGrad` =
           * `sun.angle` (0,62 Grad ist etwas WEICHER als die echte Sonne mit
           * rund 0,53 Grad — der Wert ist so gewaehlt worden, nicht
           * abgemessen).
           *
           * WER DAS LIEST — BERICHTIGT AM 17.09.2026 (A15, Welle 5), und die
           * Berichtigung ist unangenehm. Hier stand: «der Cycles-Schritt auf
           * der HomeStation, und nur der.» **Gemessen ist das falsch: der
           * Cycles-Schritt auf der HomeStation liest diesen Vertrag gar
           * nicht.** `~/kosmo-render/werkzeug/render_lauf.py` — das Werkzeug,
           * mit dem das vom Owner angenommene Bild vom 10.09. gerechnet wurde
           * — hat zwar die passenden Schalter (`--sonne-staerke`,
           * `--sonne-farbe`), aber `grep -rl 'render-scene'` ueber jenen
           * Ordner findet NULL Treffer, und ausser der Datei selbst, ihrer
           * Anleitung und vier Laufprotokollen nennt sie niemand: sie wird von
           * Hand gestartet.
           *
           * Der einzige Leser dieses Vertrags ist der KosmoVis-Worker
           * (`ai-imaging-in-a-box`), und der reicht aus `sun` nachweislich NUR
           * `elevation` und `azimuth` weiter. Gemessen an der Naht: die
           * Nutzlast, die `vis-jobs.ts` heute baut, durch
           * `kosmo_szene.lies_szene` und weiter durch
           * `seams._multipass_argumente` — die Funktion, die Blenders
           * Befehlszeile baut. Dort stehen `--sonne-hoehe=32.0` und
           * `--sonne-azimut=200.0`; `staerke` (6.0), `kelvin` (4900) und
           * `winkelGrad` (0.62) stehen nicht, und `blender_depth_stage.py` hat
           * fuer keines davon einen Schalter. Die Probe kann widersprechen:
           * zwei der fuenf Werte KOMMEN in der Befehlszeile vor.
           *
           * Beim Sonnenwinkel kaeme selbst eine angeschlossene Naht nicht
           * weiter: `render_lauf.py` setzt ihn FEST auf 0.62 Grad
           * (`daten.angle = math.radians(0.62)`) — dort gibt es keinen
           * Schalter, den man bedienen koennte.
           *
           * **Der Satz, den dieser Abschnitt bis heute sagte, war zu
           * freundlich.** Nicht «bis der ferne Renderer diese Felder liest» —
           * es gibt keinen Renderer, dem sie je zugestellt werden. Der
           * Empfaenger fehlt nicht, er ist NICHT ANGESCHLOSSEN. Die drei
           * Felder bleiben trotzdem stehen (ein Rueckzug wie bei `style.refs`
           * waere hier falsch: die Gegenstuecke drueben EXISTIEREN, sie haengen
           * nur an keiner Leitung), gelten aber bis auf Weiteres als
           * UNBESTELLT. Die Frage ist gestellt:
           * `auftraege/von-homestation/auf-vis-20260917-01.md` — es traegt neben
           * der Sonne auch den Zustellweg-Befund, weil der beide erklaert. Wer hier liest und
           * die Blaetter beantwortet vorfindet, misst nach und berichtigt
           * diesen Abschnitt — der Stand steht zusaetzlich als Tabelle in
           * `apps/kosmo-orbit/src/modules/vis/vis-jobs.ts` (`FREMDNAHT`), und
           * die Oberflaeche rechnet ihren Hinweistext daraus.
           */
          staerke: z.number().min(0).optional(),
          kelvin: z.number().min(1000).max(12000).optional(),
          winkelGrad: z.number().min(0).max(90).optional(),
        })
        .optional(),
      /**
       * ZEILE 47 (60-ABNAHMELISTE.md) — «hintergrund basically weiss … ist es
       * irgendwie moeglich diesen einzubringen … das es nicht nur weiss ist
       * aber wir an der belichtung nichts verlieren?». Die Antwort im
       * Renderprojekt war KEIN HDRI-Bild, sondern der prozedurale Himmel von
       * Blender — darum steht dieses Feld NEBEN `environment` und nicht darin:
       * `environment` beschreibt eine Stimmungskachel bzw. eine HDRI-Kennung,
       * `himmel` beschreibt einen gerechneten Himmel mit Physikzahlen. Zwei
       * verschiedene Dinge, zwei Felder — ein gemeinsames waere ein Feld, das
       * je nach Nachbarwert etwas anderes bedeutet.
       *
       * `modell` fuehrt die VIER Arten, die Blender 5.2 wirklich hat (am
       * Geraet nachgesehen, 00-CHRONIK.md §5: «Die Himmelsart NISHITA gibt es
       * nicht mehr»). «NISHITA» faellt hart durch — sonst bestellte die App
       * eine Art, die der Renderer nicht mehr kennt, und bekaeme still etwas
       * anderes.
       *
       * `luftdichte`/`aerosoldichte` sind Blenders `air_density`/
       * `aerosol_density` (das zweite hiess vor 5.2 `dust_density` —
       * derselbe Befund). Die Werte des angenommenen Bildes: Staerke 1,0,
       * Luftdichte 0,40, Aerosoldichte 3,0 (00-CHRONIK.md §6).
       *
       * ZEILE 48 — «zeig vom hintergrundbild mehr die berge weniger das
       * wasser»: `drehungGrad` dreht den Himmel um die Hochachse. OPTIONAL
       * und ohne Vorgabewert, im Gegensatz zum `rotationGrad` in
       * `environment` oben: dort steht eine 0 als Vorgabe, hier bedeutet ein
       * fehlendes Feld «nicht gedreht bestellt» statt «auf 0 gestellt».
       *
       * Ganzes Feld optional: ohne es bleibt jede bestehende Nutzlast Zeichen
       * fuer Zeichen gueltig.
       *
       * BERICHTIGT AM 17.09.2026 (A15, Welle 5). Hier stand: «Leser ist wie
       * bei `sun` der Cycles-Schritt auf der HomeStation — in diesem Baum
       * liest es niemand.» Der zweite Halbsatz stimmt, der erste nicht: das
       * Cycles-Werkzeug der HomeStation liest diesen Vertrag ueberhaupt nicht
       * (Begruendung und Messung stehen bei `sun.staerke` oben). Der einzige
       * Leser, der KosmoVis-Worker, nimmt `himmel` nicht einmal entgegen — es
       * taucht in `kosmo_szene.lies_szene` nirgends auf, weil jene Seite
       * `render` feldweise mit `.get()` liest und Unbekanntes wortlos
       * uebergeht. Die Gegenstuecke drueben gaebe es
       * (`render_lauf.py --himmel-staerke/--luft/--staub`), sie haengen nur an
       * keiner Leitung. **Eine Himmelsbestellung aendert das Bild heute
       * NICHT.** Der Zustellweg-Befund, der beide Faelle erklaert, steht in
       * `auftraege/von-homestation/auf-vis-20260917-01.md` Abschnitt 3.
       */
      himmel: z
        .object({
          modell: z.enum(['SINGLE_SCATTERING', 'MULTIPLE_SCATTERING', 'PREETHAM', 'HOSEK_WILKIE']),
          staerke: z.number().min(0),
          luftdichte: z.number().min(0),
          aerosoldichte: z.number().min(0),
          drehungGrad: z.number().min(0).max(360).optional(),
        })
        .optional(),
      /**
       * ZEILE 4, zweite Haelfte — die Belichtung ist KEINE Rendereinstellung,
       * sondern Farbverwaltung (`scene.view_settings`): sie wirkt NACH dem
       * Rechnen und kostet keine Sekunde Rechenzeit. Genau darum gehoert sie
       * in den Auftrag: dasselbe gerechnete Bild wird damit heller oder
       * dunkler, ohne es neu zu rechnen.
       *
       * Gemessene Werte des angenommenen Bildes (00-CHRONIK.md §6):
       * Belichtung 2,70, Farbraum AgX, Anmutung «Base Contrast».
       *
       * Optional, kein Vorgabewert — s. `sun`-Details oben. `anmutung` ist
       * eine freie Zeichenkette, weil Blenders `look`-Liste vom Farbraum
       * abhaengt und wir sie nicht am Geraet gezaehlt haben; eine erfundene
       * Aufzaehlung waere hier schlechter als eine ehrliche Zeichenkette.
       */
      belichtung: z
        .object({
          belichtung: z.number(),
          farbraum: z.enum(['AgX', 'Filmic', 'Standard', 'Raw']),
          anmutung: z.string().optional(),
        })
        .optional(),
      /**
       * Cycles-Rauschschwelle (`adaptive_threshold`) — gehoert zu ZEILE 51
       * (Qualitaet gegen Zeit): sie entscheidet mit, wann Cycles vor dem
       * Erreichen der Abtastzahl aufhoert. Gemessener Wert des angenommenen
       * Bildes: 0,005 (00-CHRONIK.md §6). Optional, kein Vorgabewert.
       */
      rauschschwelle: z.number().min(0).max(1).optional(),
      /**
       * v0.8.4 W0 (docs/V084-SPEZ.md, E-HDRI): Umgebungslicht/Stimmung als
       * ADDITIVES Schwester-Feld von `sun` — zod ist non-strict, alte
       * Payloads bleiben wortgleich gültig, das Schema-Literal bleibt `/v1`.
       * `preset` spiegelt die drei bestehenden Stimmungs-Presets
       * (kosmo-kernel derive/visgraph.ts VIS_STIMMUNGEN); `hdri` ist eine
       * OPTIONALE URI/Kennung, die erst die HomeStation gegen ihre lokal
       * liegenden Voll-HDRIs auflöst — die App verschifft KEINE .hdr-Assets
       * (prozedurale Previews, ehrliche Container-Grenze).
       */
      //
      // Vorschlag V (Visbox-Entscheide 110/113, 20.10.2026): acht Stimmungen (`StimmungPreset`).
      // Sonst unveraendert. Gesendet wird das Objekt, wie es gebaut ist (nicht die Ausgabe von
      // `parse`): fehlt `rotationGrad` in der Bestellung, dreht der Heim-PC den Himmel zur Kamera
      // (`angewandt.environment.drehung_weg: 'zur_kamera'`); die Vorgabe 0 unten gilt nur fuer
      // die gelesene Form.
      environment: z
        .object({
          preset: StimmungPreset,
          hdri: z.string().optional(),
          intensitaet: z.number().min(0).max(10).default(1),
          rotationGrad: z.number().min(0).max(360).default(0),
        })
        .optional(),
      /**
       * Vorschlag V (Visbox-Entscheid 111): Materialien je Bauteil-Art aus dem Knoten
       * «Oberflaeche». Fehlt eine Art, behaelt sie das Material aus dem Modell. Ein leeres
       * Objekt wird abgewiesen (superRefine) — «nichts gewaehlt» heisst: Feld weglassen.
       */
      materialien: Materialien.optional(),
      /**
       * kv-ebenen (E124 Schritt 1, Owner-Entscheid 29.09.2026 «zwei
       * Schritte»): welche EBENEN je Kamera zurueckkommen sollen. Form nach
       * dem Beispiel der Gegenseite (`docs/auftraege-kosmovis/erg-20260929-
       * e124-beispiele-und-glas.md` §2): eine Liste aus `EbenenArt` ODER der
       * Text `"alle"`. Optional und OHNE Default: fehlt das Feld oder ist es
       * `[]`, liefert die Gegenseite keine Ebene und das Ergebnis traegt
       * kein `ebenen` (ihre Bedingung b). Ein unbekannter Name wird hier wie
       * drueben abgewiesen, statt eine Ebene zu raten. Unser Sender setzt
       * das Feld heute NICHT; die Anzeige kommt erst nach einem echten Lauf.
       */
      passes: z.union([z.array(EbenenArt), z.literal('alle')]).optional(),
    })
    .prefault({}),
  style: z
    .object({
      // v0.8.9 §9 E9/E10: 'lineart' additiv — eine Strichzeichnung ist kein
      // KI-Stil-Transfer, sondern Cycles/Freestyle- bzw. Grease-Pencil-
      // Rendering. Vertragskopplung (die Erzwingung selbst baut PBL2 in
      // vis-jobs.ts, hier wird nur der Vertrag dokumentiert): jeder Client,
      // der `mode:'lineart'` sendet, MUSS zugleich `vis.skip:true` setzen —
      // eine Strichzeichnung wartet nie auf einen KI-Veredelungs-Schritt.
      // Bedeutung je Wert, festgelegt 01.09.2026:
      // erg-20260901-16-drei-vertragsfragen.md (auftraege/ergebnisse/).
      // 'none' und 'lineart' sind gebaut (lineart-Kopplung s.o.). 'redux',
      // 'ipadapter', 'lora' sind bestellbar, wirken heute aber NICHT
      // anders als 'none' — es fehlt ein eigenes Referenzset fuer die
      // Stil-QA beim KosmoVis-Worker (Cloud), ausdruecklich entschieden,
      // nicht vergessen. Entscheid ueber das Referenzset: KosmoVis-Worker.
      mode: z.enum(['none', 'redux', 'ipadapter', 'lora', 'lineart']).default('none'),
      // ZURUECKGEZOGEN 04.09.2026 (Owner-Entscheid, B97 Posten A): das Feld
      // `refs` gab es hier von 01.09. bis 04.09.2026 und ist ENTFERNT, nicht
      // vergessen.
      //
      // Die Messung, die den Entscheid getragen hat (Vorlage:
      // `<repo>/auftraege/ergebnisse/erg-20260903-97a-entscheidungsvorlage-style-refs.md`,
      // eine Ebene UEBER `kosmo-orbit/`): im ganzen verfolgten Baum gab es
      // GENAU EINEN Erzeuger eines `style`-Objekts
      // (`apps/kosmo-orbit/src/modules/vis/vis-jobs.ts`), und der schrieb
      // `refs: []` fest verdrahtet. NIEMAND las das Feld, NIEMAND fuellte es.
      // Es gab also weder wartende Daten noch verfallende Nutzerarbeit.
      //
      // Warum ZURUECKGEZOGEN und nicht gebaut: ein Feld, das Zeichenketten
      // annimmt und nichts bewirkt, ist schlechter als kein Feld. Ein Job mit
      // gefuellten `refs` lief gruen durch und renderte ohne sie — ohne eine
      // einzige Fehlermeldung, die das gesagt haette.
      //
      // Was ein Rueckzug NICHT bricht: zod ist hier non-strict (kein
      // `.strict()`, zod 4.4.3), eine alte Nutzlast mit `style.refs` bleibt
      // also gueltig — das Feld wird beim Parsen still abgestreift, genau wie
      // jedes andere unbekannte.
      //
      // Wer Stilreferenzen WIRKLICH will, findet die Frage geprueft vor und
      // kann sie mit vollem Wissen neu entscheiden: es fehlt ein Zustellweg
      // fuer fremde Referenzbilder (z.B. Anhangsname statt Dateipfad, nach dem
      // Muster des `model`-GLB-Anhangs an POST /jobs) UND ein Leser auf der
      // Bildseite. Beides zusammen, sonst steht das Feld wieder leer da.
      // Entscheiden muessen KosmoOrbit UND KosmoVis-Worker gemeinsam.
      prompt: z.string().default(''),
    })
    .prefault({}),
  vis: z
    .object({
      /**
       * Nr. 85/83 (Demolauf 16.10.2026, Vertrag KosmoVis ↔ Integrator 20.10.2026):
       * `skip:true` heisst verbindlich «NUR GRUNDLAGE» — Cycles und Passes, KEIN
       * KI-Schritt. Geliefert wird das Cycles-Bild als Bild (`engine_used:
       * 'cycles'`), die Passes als `ebenen`, wenn `render.passes` sie bestellt.
       * Vom 26.08. bis 20.10.2026 las die Gegenseite `skip` als «gar nichts
       * rechnen», und das Haekchen «nur Cycles» bekam kein Bild. `lineart`
       * bleibt daran gekoppelt (siehe `style.mode`).
       */
      skip: z.boolean().default(false),
      /**
       * Nr. 85: Kennung einer frueher gerechneten Grundlage, wie sie ein
       * Ergebnis als `grundlage.id` gemeldet hat. Die Gegenseite nimmt deren
       * Kameras und Passes und rechnet nur den KI-Schritt — kein Blender, keine
       * Auto-Kamera neu. Sie lehnt laut ab, wenn die Kennung unbekannt ist oder
       * Aufloesung, Samples oder Kameras des Auftrags nicht zur Grundlage passen
       * (Auflage 4). Optional, kein Default.
       *
       * Vorschlag KosmoVis (Fehler-Nachgang 20.10.2026): mit `grundlage` darf die Anlage
       * (`POST /jobs`) OHNE Modelldatei kommen — die Gegenseite braucht sie fuer den
       * KI-Schritt nicht; `geometry.path` bleibt dann leer. Ohne `grundlage` bleibt `model`
       * Pflicht (422).
       */
      grundlage: z
        .string()
        .regex(/^gl-[0-9a-f]{16}$/)
        .optional(),
      /**
       * Nr. 84: fester Startwert des KI-Schritts — genau ein Bild je Kamera.
       * Ohne Feld waehlt die Gegenseite wie bisher aus mehreren. Spanne wie im
       * Werkzeugschema (Auflage 2): 0..2147483647.
       */
      seed: z.number().int().min(0).max(2147483647).optional(),
      /**
       * Owner-Auftrag 20.10.2026 (ueber LW, KosmoVis 0.3.2): Guete des
       * KI-Schritts. `'vorschau'` rechnet schnell und grob, `'voll'` wie bisher.
       * Fehlt das Feld, rechnet die Gegenseite voll — alte Auftraege bleiben
       * Zeichen fuer Zeichen gleich. Kein Default hier: die Vorgabe «Vorschau»
       * setzt der Schalter am Render-Knoten, nicht der Vertrag. Zusammen mit
       * `skip` abgewiesen (superRefine): ohne KI-Schritt gibt es keine Guete.
       */
      guete: z.enum(['vorschau', 'voll']).optional(),
      /**
       * Knoten «Umfeld» (Visbox-Owner-Wunsch 24.10.2026, Vorschlag KosmoVis an Int 1): Baeume,
       * Bueche, Wiese, Strasse und Autos um das Haus — freie 3D-Modelle (nur CC0), geladen und
       * gestellt am Heim-PC in der Blender-Grundlage: nie im Haus, nie im Blick der Kameras auf das
       * Haus; gemessen wird weiter nur am Haus (sie zaehlen als Umfeld). Bestellt wird nur der
       * WUNSCH; was wo steht, rechnet die Gegenseite. Eine ausgestattete und eine leere Grundlage
       * sind zwei (`vis.grundlage` passt nur zum selben `umfeld`). `.strict()` wie `context`: ein
       * falsch geschriebenes Feld waere sonst ein stiller Wunsch. Fehlt das Feld, alles wie bisher.
       */
      umfeld: z
        .object({
          kategorien: z.array(z.enum(['baeume', 'buesche', 'wiese', 'strasse', 'autos'])).min(1),
          dichte: z.enum(['wenig', 'mittel', 'viel']).optional(),
          seed: z.number().int().min(0).max(2147483647).optional(),
          anzahl: z
            .object({
              baeume: z.number().int().min(0).max(30).optional(),
              buesche: z.number().int().min(0).max(30).optional(),
              autos: z.number().int().min(0).max(30).optional(),
            })
            .strict()
            .optional(),
        })
        .strict()
        .optional(),
      /**
       * Modell-Lizenz-Sanierung 11.08.2026 (Advisor-Auftrag Phase 2, Audit
       * 10.08.): `'flux-krea'` (FLUX.1-Krea-dev, BFL-Lizenz NON-COMMERCIAL —
       * auch als GGUF-Variante) ist nur im research-Profil gueltig: das
       * superRefine unten verlangt dafuer `research_only: true`. Der
       * Enum-Wert bleibt (additiv, alte research-Payloads mit Flag parsen
       * weiter) — Produkt-Payloads ohne Flag werden abgewiesen.
       * Profile: docs/MODEL_DOWNLOAD_MANIFEST.md.
       *
       * HOMESTATION-BEFUND 12 (19.08.2026, `docs/HOMESTATION-2026-08-19-
       * PUBLISH-UND-KOSMO.md`): die Vorgabe war bis dahin `'qwen'` — und der
       * Vertrag nannte damit einen Backbone, der die Konditionierung gar
       * nicht kann. Am Geraet gemessen (Auftrag `auf-20260818-09`): die
       * `QwenImageEditPlusPipeline` von `qwen-image-edit-2511` ist KEIN
       * ControlNet, ihr `__call__` kennt weder `control_image` noch
       * `controlnet_conditioning_scale` noch `strength`. Ein Auftrag mit
       * `backbone: 'qwen'` bekommt, sobald ihn jemand abholt, BILDBEARBEITUNG
       * statt tiefenkonditioniertem Rendern — das erklaert die schwebenden
       * Drahtgitter des ersten vollstaendigen Laufs.
       *
       * `'z-image-turbo'` fehlte in dieser Aufzaehlung **ganz**, obwohl es in
       * der Bildlane der HomeStation seit dem 18.08. die Vorgabe ist. Es ist
       * jetzt aufgenommen UND Vorgabe: Lizenzlage geprueft (Apache-2.0, Basis
       * und ControlNet), und dass die ControlNet-Naht dieses Backbones
       * traegt, ist am Geraet belegt. **Additiv:** kein alter Wert entfaellt,
       * bestehende Auftraege parsen weiter — nur die Vorgabe wechselt, weil
       * die alte nachweislich das Falsche tat.
       *
       * E128 (ENTSCHEIDE-2026-09-22, P-QWEN21 am 30.09.2026): `'qwen-image-2.1'`
       * additiv aufgenommen, OHNE research_only-Pflicht — der Owner nimmt es
       * ins Produkt und loest die Lizenz vor der Veroeffentlichung. Am Geraet
       * gemessen (ROADMAP 1632): keine Tiefenfuehrung, darum NICHT Vorgabe.
       */
      backbone: z
        .enum(['z-image-turbo', 'qwen', 'flux2-klein', 'flux-krea', 'sdxl', 'qwen-image-2.1'])
        .default('z-image-turbo'),
      /**
       * Bedeutung festgelegt 01.09.2026 (erg-20260901-16-drei-vertragsfragen.md,
       * auftraege/ergebnisse/). Zwei Bedingungen gehoeren zwingend zu einer
       * `upscale:true`-Bestellung:
       * 1. Die Geometrie-QA (rho_maske/kantenanteil/geom_iou) misst IMMER
       *    auf dem urspruenglichen, NICHT auf dem hochskalierten Bild — ein
       *    Hochskalierer erfindet Bildinhalt, und wir messen Bildinhalt.
       *    ACHTUNG, Herkunft dieser Festlegung: sie ist UNSERE Konvention,
       *    neu gesetzt am 01.09.2026 — sie steht NICHT im Owner-Entscheid.
       *    ENTSCHEIDE-2026-08-23.md legt nur die Schwelle `rho_maske` 0.80
       *    fest und nennt als Eichgrundlage «drei Szenen», nicht die
       *    Bildaufloesung; einen Hochskalierer gab es damals nicht. Dass
       *    die Eichung faktisch an Originalbildern lief, ist damit
       *    hergeleitet, nicht entschieden — und darum ist diese Zeile hier
       *    eine Konvention, die der Owner noch bestaetigen kann.
       * 2. Der Hochskalierer braucht eine PERMISSIVE Lizenz (MIT,
       *    Apache-2.0, BSD, MPL-2.0) — kein GPL, keine NonCommercial-Lizenz.
       * Fundstelle der Geometriemessung: im Repo nicht auffindbar (nur
       * Fake-Stub-Werte in tools/homestation-bridge, kein Vergleichscode;
       * die reale Messung liegt vermutlich im fremden KosmoVis-Worker-Repo).
       * Implementierungsstand (kein Bedeutungsproblem mehr): kein
       * Hochskalierer angeschlossen, `true` liefert heute dasselbe wie
       * `false`.
       */
      upscale: z.boolean().default(false),
      /**
       * Explizites research-Flag (nie Default): erlaubt Non-Commercial-
       * Backbones fuer Forschungs-/Vergleichslaeufe. Der HomeStation-Worker
       * traegt dasselbe Gate am Checkpoint (`kosmo_worker_comfyui.py`,
       * `--research-only`) — dieses Feld dokumentiert die Bestellung, das
       * Worker-Flag erzwingt das Laden.
       */
      research_only: z.boolean().optional(),
    })
    .prefault({})
    .superRefine((v, ctx) => {
      if (v.grundlage !== undefined && v.skip) {
        ctx.addIssue({
          code: 'custom',
          message:
            'vis.grundlage und vis.skip zugleich: Die Grundlage ist schon gerechnet — ohne KI-Schritt entstuende nichts Neues.',
          path: ['grundlage'],
        });
      }
      if (v.guete !== undefined && v.skip) {
        ctx.addIssue({
          code: 'custom',
          message:
            'vis.guete und vis.skip zugleich: Die Guete betrifft nur den KI-Schritt — mit skip (nur Grundlage) gibt es keinen.',
          path: ['guete'],
        });
      }
      if (v.backbone === 'flux-krea' && v.research_only !== true) {
        ctx.addIssue({
          code: 'custom',
          message:
            'Backbone «flux-krea» (FLUX.1-Krea-dev) ist non-commercial und nur mit explizitem research_only: true bestellbar — Produkt-Wahl ist «z-image-turbo» (docs/MODEL_DOWNLOAD_MANIFEST.md).',
          path: ['backbone'],
        });
      }
    }),
  /**
   * Bildkomposition (Owner-Befund K20/A10) — Metadaten des angewandten
   * Cycles-Presets (kosmo-kernel derive/render-presets.ts), NUR gesetzt wenn
   * ein Preset aktiv ist. Ehrliche Transparenz statt Blackbox: Seitenverhältnis/
   * Brennweiten-Äquivalent/Horizontlinie fliessen so in den Render-Prompt/Job.
   */
  komposition: z
    .object({
      seitenverhaeltnis: z.number().positive(),
      brennweiteMm: z.number().positive(),
      horizontlinie: z.number().min(0).max(1),
    })
    .optional(),
  /**
   * P-GELAENDEAUSKUNFT (auf-20260901-67, docs/auftraege-kosmovis/): `RenderScene`
   * kannte keine Aussage darueber, ob in der Szene Gelaende steht. Die
   * Bauwerksmaske des KosmoVis-Workers trennt Bauwerk von Gelaende ueber eine
   * Namensregel; findet sie keines, ist das entweder ein Fehlbefund der Regel
   * oder es steht schlicht keines da — aus dem Bild allein NICHT zu
   * unterscheiden. Ohne diese Auskunft bleibt die Maske leer, ohne Maske gibt
   * es kein Paarurteil, keine Rangkorrelation ueber der Maske, keinen
   * Kantenanteil — Bilder ohne Urteil. Bislang behalf sich der Betrieb mit
   * einem PROZESSWEITEN CLI-Schalter (`--kein-gelaende` an der Kommandozeile
   * des Abholers, systemd-Einheit) fuer eine Aussage, die JE SZENE gilt —
   * eine Szene MIT Gelaende bekaeme damit eine falsche Erklaerung. Das war der
   * eigentliche Defekt, den dieses Feld beseitigt: die Aussage wandert an den
   * Auftrag, wo sie hingehoert; der Schalter wird ueberfluessig.
   *
   * DREIWERTIG, nicht zweiwertig — selbst begruendet, nicht vom Auftrag
   * uebernommen (der Auftrag nennt nur die Erklaerung des Absenders; geprueft
   * ist sie unten am eigenen Vertragsmuster):
   * - `true`  — in dieser Szene steht Gelaende. Findet die Maske keines, ist
   *             das ein Fehlbefund und wird als solcher gemeldet.
   * - `false` — hier steht keines. Die Maske gilt ohne Bodenabzug.
   * - `null`/FEHLEND — UNBEKANNT. Nicht `false`. Es wird nicht gemessen, und
   *             es wird gesagt, warum.
   *
   * `null` und ein fehlendes Feld bedeuten HIER dasselbe («unbekannt») —
   * kein `.default()` auf einen Wahrheitswert, aus zwei Gruenden:
   * 1. Ein stiller `false`-Default waere eine Behauptung, die niemand
   *    aufgestellt hat. Sie wuerde auf JEDER Szene MIT Gelaende ein falsches
   *    Urteil erzeugen — und zwar ein BESTANDENES: die Maske wuerde ohne
   *    Bodenabzug gerechnet, obwohl Boden im Bild steht. Der teuerste Fehler
   *    dieser Klasse (dieselbe wie die stillschweigende `visibility`-Pflicht
   *    aus v0.9.58 — ein Client, der etwas nicht sagt, bekommt keine
   *    erfundene Auskunft an seiner Stelle).
   * 2. Dasselbe Vertragsmuster steht bereits zweimal in diesem Paket:
   *    `GeometryQA` (render-result.ts, P-NULLGEOMETRIE) fuehrt `null` fuer
   *    JEDES Zahlen-Mass als «NICHT GEMESSEN», ausdruecklich «keine
   *    Ersatzzahl» — «eine erfundene Null saehe aus wie eine gemessene
   *    Null». Hier ist die Zahl durch einen Wahrheitswert ersetzt, die
   *    Lehre bleibt wortgleich: eine erfundene `false` saehe aus wie eine
   *    gemessene `false`.
   *
   * Additiv (ROADMAP 1062): ein neues, optionales Feld — kein bestehender
   * Absender bricht, wer es nicht sendet, bestellt weiterhin nichts anders
   * als vorher.
   */
  gelaende: z.boolean().nullable().optional(),
  /**
   * Owner-Entscheid 76 (Splat jetzt): der KONTEXT einer Bestellung — eine
   * Gauss-Splat-Aufnahme der Umgebung, in die das Modell gestellt und mit
   * ihr gerechnet wird. Festgelegt mit Integrator, prepare und HomeStation;
   * die App-Seite der HomeStation schaltet sich an `'context' in
   * RenderScene.shape` ein.
   *
   * - `kind`      — heute nur `'splat'`. Ein unbekannter Wert wird
   *                 abgewiesen, nicht still ignoriert.
   * - `ply`       — ABSOLUTER Pfad der Splat-Datei (.ply) AUF DER
   *                 HOMESTATION. Die Datei reist nicht mit; sie liegt dort.
   * - `verortung` — Pfad der Begleitdatei `<splat>.verortung.json` (wie der
   *                 Splat im Gelaende liegt), oder `null`, wenn es keine gibt.
   * - `transform` — 4x4-Matrix, ZEILENWEISE, 16 endliche Zahlen: die Lage des
   *                 Splats in der glTF-Welt des Modells (Meter, Y oben), so wie
   *                 `splatAnsichtsMatrix(ebene)` sie fuer die Ansicht rechnet.
   * - `fit`       — wie die Lage zustande kam: `'behelf'` heisst LAGE VON
   *                 HAND (eingepasst nach Augenmass, keine Messung);
   *                 `'passpunkte'` heisst aus Passpunkten bestimmt.
   * - `crs_note`  — Klartext zum Bezugssystem (z. B. LV95 und Ursprung), fuer
   *                 Menschen; kein Rechenwert.
   *
   * `.strict()`: ein Feld, das hier nicht steht, ist ein Schreibfehler und
   * wird abgewiesen — eine Lage mit falschem Feldnamen waere sonst still
   * verloren.
   *
   * OHNE `context` ist alles wie bisher: das Feld ist optional, ohne
   * Vorgabe, jede bestehende Szene bleibt byte-gleich gueltig und bestellt
   * nichts anders. Ob die Datei unter `ply` wirklich da und lesbar ist,
   * prueft der Abholer auf der HomeStation; fehlt sie, meldet er einen
   * SICHTBAREN Fehler am Auftrag, statt ohne Kontext zu rechnen.
   */
  context: z
    .object({
      kind: z.literal('splat'),
      ply: z.string().min(1),
      verortung: z.string().min(1).nullable(),
      transform: z.array(z.number().finite()).length(16),
      fit: z.enum(['behelf', 'passpunkte']),
      crs_note: z.string(),
    })
    .strict()
    .optional(),
  /**
   * Owner-Entscheid 96 der Visbox (15.10.2026): DIE SKIZZE FUEHRT DAS BILD.
   * Eine Skizze vom iPad, die in der Mappe der Visbox liegt, wird zum
   * Eingangsbild der Bestellung — derselbe Weg wie «aus Skizze rechnen» auf
   * der Visbox-Seite (`arbeitsgang.rechne_skizze`): die Skizze auf ihrer
   * Unterlage geht in ein Bildmodell, das das Bild bearbeitet, statt es aus
   * dem Modell neu zu rechnen.
   *
   * - `quelle`    — heute nur `'mappe'`: die Skizze liegt SCHON auf dem
   *                 Rechner, der rechnet (Visbox, Heim-PC); es reist nur ihr
   *                 Name, kein Bild. Ein Upload (etwa fuer KosmoOrbit ohne
   *                 Mappe) waere eine zweite Quelle mit eigenem Feld, nicht
   *                 diese hier umgedeutet. Ein unbekannter Wert wird
   *                 abgewiesen.
   * - `name`      — der Dateiname der Skizze in der Mappe, so wie der Wirt
   *                 ihn meldet (`GET ./mappe` → `skizzen[].name`). Schon
   *                 aufgeloest: «neueste» ist eine Wahl am Knoten, keine
   *                 Bestellung — die Bestellung nennt die eine Datei.
   *                 Auflage A1 (Integrator, 15.10.2026): ein RELATIVER Pfad
   *                 in der Mappe, hoechstens 255 Zeichen, ohne `.`/`..`,
   *                 ohne fuehrenden `/`, ohne Backslash, ohne Laufwerk, ohne
   *                 Steuerzeichen (`skizzenNameMangel` oben).
   * - `anweisung` — was sich am Bild aendern soll. Fehlt sie, nimmt die
   *                 Bildseite die Bemerkung, die beim Zeichnen an der Skizze
   *                 stand; fehlt auch die, weist sie mit Satz ab. Bewusst NICHT
   *                 `style.prompt` umgedeutet: der beschreibt, was entstehen
   *                 soll, diese hier, was sich aendern soll.
   *                 Entscheid 96a (Owner, 15.10.2026): die Knotenansicht
   *                 sendet sie NICHT — haengt eine Skizze am Render-Knoten,
   *                 gilt die Bemerkung der Skizze, und die Stimmung tritt
   *                 zurueck. Das Feld bleibt fuer andere Besteller.
   *
   * Was mit `skizze` NICHT zusammengeht (superRefine unten, abgewiesen statt
   * still uebergangen): eine Liste in `cameras` — eine Skizze ist EIN Bild
   * (Entscheid 96b: vom Standpunkt des Bildes, auf das sie gezeichnet wurde;
   * ohne ein solches vom Standpunkt der Mappe), nicht drei Standpunkte;
   * `interior` — dasselbe;
   * `vis.skip: true` — ohne Bildmodell gibt es nichts, das die Skizze lesen
   * koennte.
   *
   * `.strict()` wie `context`: ein falsch geschriebenes Feld waere sonst eine
   * still verlorene Anweisung.
   *
   * OHNE `skizze` ist alles wie bisher: optional, ohne Vorgabe, jede
   * bestehende Szene bleibt byte-gleich gueltig. Keine neue Schemakennung:
   * additiv wie `context` und `gelaende` (ROADMAP 1062). Wer das Feld nicht
   * kennt, weist ab (Visbox `kosmo_szene.unbekannte_felder`) — eine aeltere
   * Bildseite rechnet also nie still ohne die Skizze.
   */
  skizze: z
    .object({
      quelle: z.literal('mappe'),
      name: z.string().min(1).superRefine((name, ctx) => {
        const mangel = skizzenNameMangel(name);
        if (mangel) ctx.addIssue({ code: 'custom', message: mangel });
      }),
      anweisung: z.string().min(1).optional(),
    })
    .strict()
    .optional(),
})
  // Y3 P-IFC-BESTELLUNG (V0942-SPEZ §4): die gemessene Probe des Demohauses
  // (kosmo-orbit/abgabe/PROBE-DEMOHAUS.ifc, 26 IFCSPACE mit echter
  // Extrusionsgeometrie/Storey-Zuordnung) traegt eine Raumlesung — aus glb/
  // gltf/fbx/blend NICHT (docs/EINBAU_CLOUDWORKER_2026-08-22.md §2: «dort
  // sind Waende und Boeden Dreiecke ohne Raumbegriff»). Eine Bestellung von
  // Innenansichten ohne IFC-Geometrie waere darum keine Bestellung, die der
  // Cloud-Worker erfuellen kann — der Vertrag verweigert sie hart statt sie
  // stumm durchzureichen («Was ankommt, stimmt», V0942-SPEZ-Titel).
  //
  // P-INTERIOR Auftrag DREI: der Riegel greift jetzt fuer BEIDE Wege — den
  // kanonischen `interior` und den geduldeten Zweitnamen `innenansichten` —
  // unabhaengig voneinander, mit je eigenem Fehlerpfad, damit die Meldung
  // immer auf das tatsaechlich gesendete Feld zeigt.
  .superRefine((v, ctx) => {
    // Vorschlag V (Knoten «Kamera»): die Einstellungen der Auto-Kamera gelten nur, wenn die
    // Bildseite die Standpunkte selbst rechnet — nicht neben einer Liste, nicht mit einer Skizze
    // (EIN Bild vom Standpunkt der Skizze) und nicht mit Innenansichten.
    if (v.cameras_auto !== undefined) {
      if (v.cameras !== 'auto') {
        ctx.addIssue({
          code: 'custom',
          message: 'cameras_auto gilt nur mit cameras "auto" — die Bildseite rechnet die Standpunkte dann selbst.',
          path: ['cameras_auto'],
        });
      }
      if (v.skizze !== undefined || v.interior !== undefined) {
        ctx.addIssue({
          code: 'custom',
          message: 'cameras_auto geht nicht mit einer Skizze oder Innenansichten zusammen.',
          path: ['cameras_auto'],
        });
      }
    }
    if (v.render.materialien !== undefined && Object.keys(v.render.materialien).length === 0) {
      ctx.addIssue({
        code: 'custom',
        message: 'render.materialien ohne eine einzige Bauteil-Art — das Feld weglassen, wenn nichts gewaehlt ist.',
        path: ['render', 'materialien'],
      });
    }
    // Owner-Entscheid 96 (Visbox, 15.10.2026) — s. Kommentar an `skizze`.
    if (v.skizze !== undefined) {
      if (Array.isArray(v.cameras)) {
        ctx.addIssue({
          code: 'custom',
          message:
            'Mit einer Skizze entsteht EIN Bild vom Standpunkt des Bildes unter der Skizze (sonst dem der Mappe) — eine Kameraliste geht dazu nicht (cameras weglassen oder "auto").',
          path: ['cameras'],
        });
      }
      if (v.interior !== undefined) {
        ctx.addIssue({
          code: 'custom',
          message: 'Eine Skizze und eine Innenansicht gehen nicht in einer Bestellung — die Skizze ist EIN Bild.',
          path: ['interior'],
        });
      }
      if (v.vis.skip) {
        ctx.addIssue({
          code: 'custom',
          message:
            'Eine Skizze braucht das Bildmodell — mit vis.skip (nur Cycles, Strichzeichnung) gibt es nichts, das sie liest.',
          path: ['vis', 'skip'],
        });
      }
      if (v.vis.grundlage !== undefined) {
        ctx.addIssue({
          code: 'custom',
          message: 'Eine Skizze fuehrt ihr Bild selbst und rechnet keine Blender-Grundlage — vis.grundlage geht dazu nicht.',
          path: ['vis', 'grundlage'],
        });
      }
    }
    if (v.innenansichten && v.geometry.format !== 'ifc') {
      ctx.addIssue({
        code: 'custom',
        message:
          'Innenansichten sind nur mit geometry.format "ifc" bestellbar — aus glb/gltf/fbx/blend gibt es keine Raeume (docs/EINBAU_CLOUDWORKER_2026-08-22.md §2).',
        path: ['innenansichten'],
      });
    }
    if (v.interior !== undefined && v.geometry.format !== 'ifc') {
      ctx.addIssue({
        code: 'custom',
        message:
          'Innenansichten (interior.rooms) sind nur mit geometry.format "ifc" bestellbar — aus glb/gltf/fbx/blend gibt es keine Raeume (docs/EINBAU_CLOUDWORKER_2026-08-22.md §2).',
        path: ['interior', 'rooms'],
      });
    }
  });

export type RenderScene = z.infer<typeof RenderScene>;
export type CameraSpec = z.infer<typeof CameraSpec>;
