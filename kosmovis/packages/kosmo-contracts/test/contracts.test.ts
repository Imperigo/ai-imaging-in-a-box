import { describe, expect, it } from 'vitest';
import { KosmoProjectManifest, RenderJob, RenderResult, RenderScene, unbekannteFelder } from '../src';

describe('render-scene/v1', () => {
  it('akzeptiert das Minimum (geometry + out) und füllt Defaults', () => {
    const scene = RenderScene.parse({
      geometry: { path: 'model/model.glb', format: 'glb' },
      out: 'renders/job-001',
    });
    expect(scene.schema).toBe('kosmovis.render-scene/v1');
    expect(scene.cameras).toBe('auto');
    expect(scene.render.faithful).toBe(0.8);
    // HomeStation-Befund 12 (19.08.2026, am Geraet gemessen): `qwen-image-edit-2511`
    // ist ueber `QwenImageEditPlusPipeline` KEIN ControlNet — ihr `__call__` kennt
    // weder `control_image` noch `controlnet_conditioning_scale` noch `strength`.
    // Ein Auftrag mit diesem Backbone bekommt Bildbearbeitung statt
    // tiefenkonditioniertem Rendern. Die Vorgabe ist darum `z-image-turbo`.
    expect(scene.vis.backbone).toBe('z-image-turbo');
  });

  it('HomeStation-Befund 12: `z-image-turbo` ist ein gueltiger Backbone', () => {
    const scene = RenderScene.parse({
      geometry: { path: 'm.glb', format: 'glb' },
      out: 'x',
      vis: { skip: false, backbone: 'z-image-turbo', upscale: false },
    });
    expect(scene.vis.backbone).toBe('z-image-turbo');
  });

  it('die alten Backbones bleiben gueltig — bestehende Auftraege parsen weiter', () => {
    for (const backbone of ['qwen', 'flux2-klein', 'sdxl'] as const) {
      const scene = RenderScene.parse({
        geometry: { path: 'm.glb', format: 'glb' },
        out: 'x',
        vis: { skip: false, backbone, upscale: false },
      });
      expect(scene.vis.backbone).toBe(backbone);
    }
  });

  it('verweigert faithful ausserhalb 0..1', () => {
    expect(() =>
      RenderScene.parse({
        geometry: { path: 'm.glb', format: 'glb' },
        out: 'x',
        render: { faithful: 1.4 },
      }),
    ).toThrow();
  });

  it('Lizenz-Sanierung 11.08.2026: backbone «flux-krea» (non-commercial) OHNE research_only wird abgewiesen', () => {
    expect(() =>
      RenderScene.parse({
        geometry: { path: 'm.glb', format: 'glb' },
        out: 'x',
        vis: { skip: false, backbone: 'flux-krea', upscale: false },
      }),
    ).toThrow(/research_only/);
  });

  it('Lizenz-Sanierung 11.08.2026: backbone «flux-krea» MIT research_only: true bleibt gültig (research-Profil)', () => {
    const scene = RenderScene.parse({
      geometry: { path: 'm.glb', format: 'glb' },
      out: 'x',
      vis: { skip: false, backbone: 'flux-krea', upscale: false, research_only: true },
    });
    expect(scene.vis.backbone).toBe('flux-krea');
    expect(scene.vis.research_only).toBe(true);
  });

  it('Lizenz-Sanierung 11.08.2026: lizenzklare Backbones (qwen/sdxl) brauchen KEIN research_only — alte Payloads bleiben wortgleich gültig', () => {
    const scene = RenderScene.parse({
      geometry: { path: 'm.glb', format: 'glb' },
      out: 'x',
      vis: { skip: false, backbone: 'sdxl', upscale: false },
    });
    expect(scene.vis.backbone).toBe('sdxl');
    expect(scene.vis.research_only).toBeUndefined();
  });

  it('K20/A10: komposition ist optional (ohne Preset bleibt der Job wie bisher)', () => {
    const scene = RenderScene.parse({
      geometry: { path: 'm.glb', format: 'glb' },
      out: 'x',
    });
    expect(scene.komposition).toBeUndefined();
  });

  it('v0.8.4 E-HDRI: environment ist optional — alte Payloads bleiben wortgleich gültig', () => {
    const scene = RenderScene.parse({
      geometry: { path: 'm.glb', format: 'glb' },
      out: 'x',
      render: { sun: { azimuth: 180, elevation: 35 } },
    });
    expect(scene.render.environment).toBeUndefined();
    expect(scene.render.sun).toEqual({ azimuth: 180, elevation: 35 });
  });

  it('v0.8.4 E-HDRI: environment trägt Preset + optionale HDRI-Kennung mit Defaults', () => {
    const scene = RenderScene.parse({
      geometry: { path: 'm.glb', format: 'glb' },
      out: 'x',
      render: { environment: { preset: 'abend', hdri: 'homestation://hdri/abend-2k' } },
    });
    expect(scene.render.environment).toEqual({
      preset: 'abend',
      hdri: 'homestation://hdri/abend-2k',
      intensitaet: 1,
      rotationGrad: 0,
    });
    // Unbekannte Presets fallen hart durch — kein stilles Raten auf der Bridge.
    expect(() =>
      RenderScene.parse({
        geometry: { path: 'm.glb', format: 'glb' },
        out: 'x',
        render: { environment: { preset: 'nacht' } },
      }),
    ).toThrow();
  });

  it('v0.8.9 E9: style.mode nimmt "lineart" an', () => {
    const scene = RenderScene.parse({
      geometry: { path: 'm.glb', format: 'glb' },
      out: 'x',
      style: { mode: 'lineart' },
    });
    expect(scene.style.mode).toBe('lineart');
  });

  it('v0.8.9 E9: alte Payloads ohne style.mode parsen weiter mit Default (Rückwärtskompatibilität)', () => {
    const scene = RenderScene.parse({
      geometry: { path: 'm.glb', format: 'glb' },
      out: 'x',
    });
    expect(scene.style.mode).toBe('none');
    const sceneOhneStyleBlock = RenderScene.parse({
      geometry: { path: 'm.glb', format: 'glb' },
      out: 'x',
      style: undefined,
    });
    expect(sceneOhneStyleBlock.style.mode).toBe('none');
  });

  it('B97 A: eine alte Nutzlast mit dem zurueckgezogenen style.refs parst weiter', () => {
    // Owner-Entscheid 04.09.2026: `style.refs` ist ZURUECKGEZOGEN (genau ein
    // Erzeuger schrieb eine leere Liste, niemand las sie). Der Entscheid
    // stuetzte sich darauf, dass ein Rueckzug ALTE NUTZLASTEN NICHT BRICHT —
    // und das wird hier gemessen statt geglaubt: zod ist non-strict (kein
    // `.strict()`), das unbekannte Feld wird still abgestreift.
    const scene = RenderScene.parse({
      geometry: { path: 'model/model.glb', format: 'glb' },
      out: 'renders/job-001',
      style: { mode: 'none', refs: ['ref-a.png', 'ref-b.png'], prompt: 'x' },
    });
    expect(scene.style.mode).toBe('none');
    expect(scene.style.prompt).toBe('x');
    // Das Feld ist WEG, nicht leer — sonst wuerde es weiterhin etwas
    // versprechen, das niemand einloest.
    expect('refs' in scene.style).toBe(false);
  });

  it('verweigert einen unbekannten style.mode-Wert', () => {
    expect(() =>
      RenderScene.parse({
        geometry: { path: 'm.glb', format: 'glb' },
        out: 'x',
        style: { mode: 'realistisch' },
      }),
    ).toThrow();
  });

  it('K20/A10: komposition trägt Seitenverhältnis/Brennweite/Horizontlinie eines Cycles-Presets', () => {
    const scene = RenderScene.parse({
      geometry: { path: 'm.glb', format: 'glb' },
      out: 'x',
      cameras: [{ position: [5, 1.6, 8], target: [5, 1.2, -3], fov: 55, up_axis: 'y' }],
      komposition: { seitenverhaeltnis: 1.6, brennweiteMm: 50, horizontlinie: 0.42 },
    });
    expect(scene.komposition).toEqual({ seitenverhaeltnis: 1.6, brennweiteMm: 50, horizontlinie: 0.42 });
    expect(scene.cameras).toEqual([{ position: [5, 1.6, 8], target: [5, 1.2, -3], fov: 55, up_axis: 'y' }]);
  });

  describe('P-ACHSENRIEGEL (26.08.2026) — up_axis ist Pflicht, kein Default', () => {
    it('weist eine Kamera OHNE up_axis ab — Raten statt Ablehnen war der Vorfall', () => {
      const ergebnis = RenderScene.safeParse({
        geometry: { path: 'm.glb', format: 'glb' },
        out: 'x',
        cameras: [{ position: [29.388, 1.3, 76.723], target: [29.388, 8.22, -1.388], fov: 55 }],
      });
      expect(ergebnis.success).toBe(false);
    });

    it('nimmt dieselbe Kamera MIT up_axis an — einziger Unterschied: das eine Feld', () => {
      const scene = RenderScene.parse({
        geometry: { path: 'm.glb', format: 'glb' },
        out: 'x',
        cameras: [{ position: [29.388, 1.3, 76.723], target: [29.388, 8.22, -1.388], fov: 55, up_axis: 'y' }],
      });
      expect(scene.cameras).toEqual([
        { position: [29.388, 1.3, 76.723], target: [29.388, 8.22, -1.388], fov: 55, up_axis: 'y' },
      ]);
    });

    it('weist einen unbekannten up_axis-Wert ab (kein stilles Raten auf einen Dritten)', () => {
      const ergebnis = RenderScene.safeParse({
        geometry: { path: 'm.glb', format: 'glb' },
        out: 'x',
        cameras: [{ position: [1, 1, 1], target: [0, 0, 0], up_axis: 'x' }],
      });
      expect(ergebnis.success).toBe(false);
    });

    it('«auto»/«saved» bleiben unberührt — up_axis betrifft nur explizite CameraSpec-Listen', () => {
      const scene = RenderScene.parse({
        geometry: { path: 'm.glb', format: 'glb' },
        out: 'x',
      });
      expect(scene.cameras).toBe('auto');
    });
  });

  // Y3 P-IFC-BESTELLUNG (V0942-SPEZ §4, B-5/B-8): das Feld `innenansichten`
  // (Auslöser) und `geometry.format:'ifc'` (Geometrie) — bewusst getrennt
  // von `cameras`, s. Feld-Kommentar in render-scene.ts.
  it('v0.9.42 Y3: alte Payloads ohne `innenansichten` parsen weiter mit Default `false`', () => {
    const scene = RenderScene.parse({
      geometry: { path: 'model/model.glb', format: 'glb' },
      out: 'renders/job-001',
    });
    expect(scene.innenansichten).toBe(false);
  });

  it('v0.9.42 Y3: `geometry.format` nimmt weiterhin "ifc" an (B-5, unverändert seit v0.9.41)', () => {
    const scene = RenderScene.parse({
      geometry: { path: 'model/model.ifc', format: 'ifc' },
      out: 'renders/job-002',
    });
    expect(scene.geometry.format).toBe('ifc');
    expect(scene.innenansichten).toBe(false);
  });

  it('v0.9.42 Y3: `innenansichten:true` mit `geometry.format:"ifc"` ist gültig', () => {
    const scene = RenderScene.parse({
      geometry: { path: 'model/model.ifc', format: 'ifc' },
      out: 'renders/job-003',
      innenansichten: true,
    });
    expect(scene.innenansichten).toBe(true);
    expect(scene.geometry.format).toBe('ifc');
  });

  it('v0.9.42 Y3: `innenansichten:true` OHNE `geometry.format:"ifc"` wird abgewiesen (Ehrlichkeitsgrenze, aus glb gibt es keine Räume)', () => {
    const ergebnis = RenderScene.safeParse({
      geometry: { path: 'model/model.glb', format: 'glb' },
      out: 'renders/job-004',
      innenansichten: true,
    });
    expect(ergebnis.success).toBe(false);
    expect(ergebnis.success ? '' : ergebnis.error.issues[0]?.path).toEqual(['innenansichten']);
  });

  it('v0.9.42 Y3: der Vertrag bleibt eine BESTELLUNG — `cameras` bleibt unabhängig von `innenansichten` bestehen (kein Vermischen)', () => {
    const scene = RenderScene.parse({
      geometry: { path: 'model/model.ifc', format: 'ifc' },
      out: 'renders/job-005',
      innenansichten: true,
      cameras: [{ position: [1, 1, 1], target: [0, 0, 0], up_axis: 'y' }],
    });
    expect(scene.innenansichten).toBe(true);
    expect(scene.cameras).toEqual([{ position: [1, 1, 1], target: [0, 0, 0], fov: 50, up_axis: 'y' }]);
  });

  // P-INTERIOR (auftraege/von-homestation/auf-orbit-20260821-02.md, DREI):
  // `interior` wird kanonisch (seine Schluessel), `innenansichten` bleibt
  // geduldeter Zweitname — Faelle fahren seinen woertlichen Auftragskoerper,
  // nicht eine Nachbildung.
  it('P-INTERIOR: `interior: { rooms: "auto" }` mit IFC ist gültig — kein Default, ein Auftrag ohne `interior` bestellt nichts', () => {
    const ohneInterior = RenderScene.parse({
      geometry: { path: 'model/model.ifc', format: 'ifc' },
      out: 'renders/job-006',
    });
    expect(ohneInterior.interior).toBeUndefined();

    const scene = RenderScene.parse({
      geometry: { path: 'model/model.ifc', format: 'ifc' },
      out: 'renders/job-006',
      interior: { rooms: 'auto' },
    });
    expect(scene.interior).toEqual({ rooms: 'auto' });
  });

  it('P-INTERIOR: `interior: { rooms: [...] }` mit einer Raumliste und IFC ist gültig', () => {
    const scene = RenderScene.parse({
      geometry: { path: 'model/model.ifc', format: 'ifc' },
      out: 'renders/job-007',
      interior: { rooms: ['Wohnzimmer', 'Kueche'] },
    });
    expect(scene.interior).toEqual({ rooms: ['Wohnzimmer', 'Kueche'] });
  });

  it('P-INTERIOR: `interior` OHNE `geometry.format:"ifc"` wird hart abgewiesen — aus glb gibt es keine Räume', () => {
    const ergebnis = RenderScene.safeParse({
      geometry: { path: 'model/model.glb', format: 'glb' },
      out: 'renders/job-008',
      interior: { rooms: 'auto' },
    });
    expect(ergebnis.success).toBe(false);
    const meldung = ergebnis.success ? '' : ergebnis.error.issues[0]?.message;
    const pfad = ergebnis.success ? [] : ergebnis.error.issues[0]?.path;
    expect(pfad).toEqual(['interior', 'rooms']);
    expect(meldung).toBe(
      'Innenansichten (interior.rooms) sind nur mit geometry.format "ifc" bestellbar — aus glb/gltf/fbx/blend gibt es keine Raeume (docs/EINBAU_CLOUDWORKER_2026-08-22.md §2).',
    );
  });

  it('P-INTERIOR: `innenansichten: true` bleibt gültig und ist gleichbedeutend zu `interior: { rooms: "auto" }` (derselbe IFC-Riegel, beide Wege)', () => {
    const mitIfc = RenderScene.parse({
      geometry: { path: 'model/model.ifc', format: 'ifc' },
      out: 'renders/job-009',
      innenansichten: true,
    });
    expect(mitIfc.innenansichten).toBe(true);

    const ohneIfc = RenderScene.safeParse({
      geometry: { path: 'model/model.glb', format: 'glb' },
      out: 'renders/job-010',
      innenansichten: true,
    });
    expect(ohneIfc.success).toBe(false);
    const meldung = ohneIfc.success ? '' : ohneIfc.error.issues[0]?.message;
    expect(meldung).toBe(
      'Innenansichten sind nur mit geometry.format "ifc" bestellbar — aus glb/gltf/fbx/blend gibt es keine Raeume (docs/EINBAU_CLOUDWORKER_2026-08-22.md §2).',
    );
  });

  it('P-INTERIOR: kein `view`-Feld im Schema — ein mitgeschicktes `view` landet nicht im geparsten Auftrag (frontal/ueber Eck steht in keiner IFC, s. Feld-Kommentar)', () => {
    const scene = RenderScene.parse({
      geometry: { path: 'model/model.ifc', format: 'ifc' },
      out: 'renders/job-011',
      interior: { rooms: 'auto', view: 'frontal' },
    });
    expect(scene.interior).toEqual({ rooms: 'auto' });
    expect('view' in (scene.interior as object)).toBe(false);
  });

  // auf-20260901-67 (docs/auftraege-kosmovis/): `RenderScene` kannte keine
  // Aussage darueber, ob in der Szene Gelaende steht. Ohne sie bleibt die
  // Bauwerksmaske des Cloud-Workers strukturell leer (er kann eine leere
  // Maske nicht von einer falsch-negativen Namensregel unterscheiden) und
  // ein Lauf liefert Bilder ohne Urteil. Bislang behalf sich der Betrieb mit
  // einem PROZESSWEITEN CLI-Schalter (`--kein-gelaende`) fuer eine Aussage,
  // die JE SZENE gilt — der eigentliche Defekt, den dieses Feld beseitigt.
  //
  // Dreiwertig, nicht zweiwertig, nach demselben Muster wie P-NULLGEOMETRIE
  // oben («null heisst NICHT GEMESSEN»): `true`/`false` sind BEHAUPTUNGEN
  // ueber die Szene, `null`/fehlend ist die ehrliche Auskunft «unbekannt».
  // Kein `.default()` auf einen Wahrheitswert — ein stiller `false`-Default
  // waere eine Behauptung, die niemand aufgestellt hat, und wuerde auf jeder
  // Szene MIT Gelaende ein falsches, aber BESTANDENES Urteil erzeugen
  // (dieselbe Fehlerklasse wie die stillschweigende `visibility`-Pflicht aus
  // v0.9.58). Darum bleibt `gelaende` `nullable().optional()`, wortgleich
  // zum bestehenden Muster der `GeometryQA`-Zahlenfelder oben.
  describe('P-GELAENDEAUSKUNFT (auf-20260901-67): `gelaende` ist dreiwertig, kein Default', () => {
    it('ein Auftrag ohne `gelaende` bestellt keine Auskunft — das Feld bleibt undefined, kein stiller Default', () => {
      const scene = RenderScene.parse({
        geometry: { path: 'model/model.glb', format: 'glb' },
        out: 'renders/job-100',
      });
      expect(scene.gelaende).toBeUndefined();
      expect('gelaende' in scene).toBe(false);
    });

    it('`gelaende: true` — in dieser Szene steht Gelaende, findet die Maske keines ist das ein Fehlbefund', () => {
      const scene = RenderScene.parse({
        geometry: { path: 'model/model.glb', format: 'glb' },
        out: 'renders/job-101',
        gelaende: true,
      });
      expect(scene.gelaende).toBe(true);
    });

    it('`gelaende: false` — hier steht keines, die Maske gilt ohne Bodenabzug', () => {
      const scene = RenderScene.parse({
        geometry: { path: 'model/model.glb', format: 'glb' },
        out: 'renders/job-102',
        gelaende: false,
      });
      expect(scene.gelaende).toBe(false);
    });

    it('`gelaende: null` — explizit UNBEKANNT, nicht dasselbe wie false', () => {
      const scene = RenderScene.parse({
        geometry: { path: 'model/model.glb', format: 'glb' },
        out: 'renders/job-103',
        gelaende: null,
      });
      expect(scene.gelaende).toBeNull();
      expect(scene.gelaende).not.toBe(false);
    });

    it('verweigert einen Nicht-Wahrheitswert (kein stilles Raten, z.B. "unbekannt" als String)', () => {
      const ergebnis = RenderScene.safeParse({
        geometry: { path: 'model/model.glb', format: 'glb' },
        out: 'renders/job-104',
        gelaende: 'unbekannt',
      });
      expect(ergebnis.success).toBe(false);
    });
  });
});

describe('render-result/v2', () => {
  it('parst ein Doppel-QA-Resultat', () => {
    const res = RenderResult.parse({
      job_id: 'vis-1751400000-a1b2c3',
      images: ['renders/cam-01.png'],
      qa: {
        style: { style_score: 0.42, passed: true },
        geometry: {
          geometry_fidelity: 0.81,
          spearman: 0.9,
          geom_iou: 0.73,
          passed: true,
        },
        verdict: { passed: true },
      },
    });
    expect(res.qa.geometry?.threshold).toBe(0.65);
    expect(res.qa.style?.method).toBe('dinov3');
  });

  it('C-19 (V0939 §12, HomeStation-Fund A8): verdict führt `hinweise`, statt ins Leere zu verweisen', () => {
    // Vorher (H-A8, `docs/HOMESTATION-2026-08-19-ZUM-FESTEN-EINBAU.md`): das
    // Urteil verwies auf ein Feld, das der Vertrag nicht führte. Additiv,
    // optional — bestehende Records ohne `hinweise` bleiben gültig.
    const ohneHinweise = RenderResult.parse({
      job_id: 'vis-1751400000-a1b2c3',
      images: ['renders/cam-01.png'],
      qa: { verdict: { passed: true, reason: 'ohne Detailbefunde' } },
    });
    expect(ohneHinweise.qa.verdict.hinweise).toBeUndefined();

    const mitHinweisen = RenderResult.parse({
      job_id: 'vis-1751400000-a1b2c3',
      images: ['renders/cam-01.png'],
      qa: {
        verdict: {
          passed: false,
          reason: 'Geometrie-Gate nicht bestanden — siehe hinweise',
          hinweise: ['geom_iou 0.61 < Schwelle 0.65', 'Bauwerksmaske deckt nur 22 % des Bilds'],
        },
      },
    });
    expect(mitHinweisen.qa.verdict.hinweise).toEqual([
      'geom_iou 0.61 < Schwelle 0.65',
      'Bauwerksmaske deckt nur 22 % des Bilds',
    ]);
  });

  describe('F3 (Posten 1, auf-orbit-20260828-16.md, 01.09.2026): «uebersprungen» im Ergebnisvertrag', () => {
    /**
     * Vorlage der Gegenseite, woertlich: «Was soll skip:true zurueckgeben? Gar
     * kein Ergebnis, oder ein Ergebnis mit leerer Bildliste und einem Grund?
     * Euer Schema hat fuer <uebersprungen> derzeit kein Feld, und ein leeres
     * images ist von einem Fehlschlag NICHT zu unterscheiden.» Der regulaere
     * Weg, auf dem `vis.skip` wahr ist, existiert bereits (render-scene.ts:171,
     * die lineart-Kopplung) — ohne dieses Feld sieht er wie ein Fehlschlag aus.
     */
    it('lieferstatus trennt uebersprungen von geliefert und von fehlgeschlagen, mit Pflicht-Grund', () => {
      const uebersprungen = RenderResult.parse({
        job_id: 'vis-1756700000-a1b2c3',
        images: [],
        lieferstatus: 'uebersprungen',
        lieferstatus_grund: 'vis.skip:true bestellt (style.mode:"lineart") — kein KI-Veredelungsschritt gefahren.',
        qa: { verdict: { passed: true } },
      });
      expect(uebersprungen.lieferstatus).toBe('uebersprungen');
      expect(uebersprungen.images).toEqual([]);

      const fehlgeschlagen = RenderResult.parse({
        job_id: 'vis-1756700000-a1b2c3',
        images: [],
        lieferstatus: 'fehlgeschlagen',
        lieferstatus_grund: 'ComfyUI-Checkpoint nicht erreichbar.',
        qa: { verdict: { passed: false } },
      });
      expect(fehlgeschlagen.lieferstatus).toBe('fehlgeschlagen');

      // Dieselbe leere Bildliste, aber jetzt unterscheidbar — nicht mehr
      // dieselbe Aussage wie oben, weil `lieferstatus` sie trennt.
      expect(uebersprungen.lieferstatus).not.toBe(fehlgeschlagen.lieferstatus);
    });

    it('Default bleibt «geliefert» — bestehende Records ohne dieses Feld waren tatsaechlich Lieferungen', () => {
      const alt = RenderResult.parse({
        job_id: 'vis-1751400000-a1b2c3',
        images: ['renders/cam-01.png'],
        qa: { verdict: { passed: true } },
      });
      expect(alt.lieferstatus).toBe('geliefert');
      expect(alt.lieferstatus_grund).toBeUndefined();
    });

    it('verweigert uebersprungen/fehlgeschlagen OHNE Grund — ein leeres Feld waere keine Antwort', () => {
      expect(() =>
        RenderResult.parse({
          job_id: 'vis-1756700000-a1b2c3',
          images: [],
          lieferstatus: 'uebersprungen',
          qa: { verdict: { passed: true } },
        }),
      ).toThrow(/lieferstatus_grund/);
    });

    it('der bereits gekoppelte Weg (mode:lineart -> vis.skip:true) laesst sich jetzt im Ergebnis als uebersprungen melden', () => {
      // render-scene.ts:158-163: wer mode:'lineart' sendet, MUSS vis.skip:true
      // setzen. Das Ergebnis dieses regulaeren Wegs ist jetzt unterscheidbar.
      const scene = RenderScene.parse({
        geometry: { path: 'm.glb', format: 'glb' },
        out: 'x',
        style: { mode: 'lineart' },
        vis: { skip: true },
      });
      expect(scene.vis.skip).toBe(true);

      const ergebnis = RenderResult.parse({
        job_id: 'vis-1756700000-a1b2c3',
        images: ['renders/lineart-01.png'],
        lieferstatus: 'geliefert',
        qa: { verdict: { passed: true } },
      });
      // Lineart liefert Bilder (Cycles/Freestyle), nur der KI-Veredelungsschritt
      // entfaellt — darum bleibt lieferstatus hier 'geliefert', nicht
      // 'uebersprungen'. 'uebersprungen' meint: dieser Render-Schritt fand gar
      // nicht statt (Grund im -grund-Feld), nicht: ein Teilschritt entfiel.
      expect(ergebnis.lieferstatus).toBe('geliefert');
      expect(ergebnis.images.length).toBeGreaterThan(0);
    });
  });

  it('erzwingt das Job-ID-Format des HomeStation-Job-Stores', () => {
    expect(() =>
      RenderJob.parse({
        job_id: 'render-42',
        status: 'queued',
        scene: 's.json',
        created_at: '2026-07-02T08:00:00Z',
      }),
    ).toThrow();
    const job = RenderJob.parse({
      job_id: 'vis-1751400000-a1b2c3',
      status: 'awaiting_approval',
      scene: 's.json',
      created_at: '2026-07-02T08:00:00Z',
    });
    expect(job.idle_window_only).toBe(true);
  });

  describe('v0.9.42 P-QA-ZAHLEN — qa.geometry additiv, alte vier Felder optional', () => {
    it('die vier alten Zahlen bleiben gueltig, wenn sie allein vorliegen (bestehende Records)', () => {
      const res = RenderResult.parse({
        job_id: 'vis-1751400000-a1b2c3',
        images: ['renders/cam-01.png'],
        qa: {
          geometry: { geometry_fidelity: 0.81, spearman: 0.9, geom_iou: 0.73, passed: true },
          verdict: { passed: true },
        },
      });
      expect(res.qa.geometry?.geometry_fidelity).toBe(0.81);
      expect(res.qa.geometry?.rho_maske).toBeUndefined();
      expect(res.qa.geometry?.paarurteil).toBeUndefined();
    });

    it('rho_maske/kante/paarurteil werden additiv angenommen, ohne die alten vier zu verlangen', () => {
      const res = RenderResult.parse({
        job_id: 'vis-1751400000-a1b2c3',
        images: ['renders/cam-01.png'],
        qa: {
          geometry: {
            rho_maske: 0.93,
            kante: 0.4,
            paarurteil: { rho_maske: 0.93, kante: 0.4 },
            passed: true,
          },
          verdict: { passed: true },
        },
      });
      expect(res.qa.geometry?.geometry_fidelity).toBeUndefined();
      expect(res.qa.geometry?.spearman).toBeUndefined();
      expect(res.qa.geometry?.geom_iou).toBeUndefined();
      expect(res.qa.geometry?.rho_maske).toBe(0.93);
      expect(res.qa.geometry?.kante).toBe(0.4);
      // paarurteil traegt beide Zahlen NEBENEINANDER — nicht zu einer
      // Ersatzzahl verrechnet (EINBAU_CLOUDWORKER_2026-08-22 §1).
      expect(res.qa.geometry?.paarurteil).toEqual({ rho_maske: 0.93, kante: 0.4 });
    });

    it('alt und neu koennen gleichzeitig vorliegen (Uebergangszeit)', () => {
      const res = RenderResult.parse({
        job_id: 'vis-1751400000-a1b2c3',
        images: ['renders/cam-01.png'],
        qa: {
          geometry: {
            geometry_fidelity: 0.81,
            spearman: 0.9,
            geom_iou: 0.73,
            rho_maske: 0.93,
            kante: 0.4,
            paarurteil: { rho_maske: 0.93, kante: 0.4 },
            passed: true,
          },
          verdict: { passed: true },
        },
      });
      expect(res.qa.geometry?.geometry_fidelity).toBe(0.81);
      expect(res.qa.geometry?.paarurteil?.kante).toBe(0.4);
    });
  });

  describe('v0.9.42 P-NULL-EHRLICH — style_score/threshold nullable', () => {
    it('nimmt das Original-Beispiel des Cloud-Workers woertlich an (EINBAU_CLOUDWORKER_2026-08-22 §3)', () => {
      const res = RenderResult.safeParse({
        job_id: 'vis-1751400000-a1b2c3',
        images: ['renders/cam-01.png'],
        qa: {
          style: { style_score: null, threshold: null, passed: true, method: 'belichtungsrahmen/hausstil' },
          verdict: { passed: true },
        },
      });
      expect(res.success).toBe(true);
      if (res.success) {
        expect(res.data.qa.style?.style_score).toBeNull();
        expect(res.data.qa.style?.threshold).toBeNull();
        expect(res.data.qa.style?.method).toBe('belichtungsrahmen/hausstil');
      }
    });

    it('Gegentest: nullable ist nicht any — ein String-Wert scheitert weiterhin', () => {
      const res = RenderResult.safeParse({
        job_id: 'vis-1751400000-a1b2c3',
        images: ['renders/cam-01.png'],
        qa: {
          style: { style_score: '0.8', threshold: null, passed: true, method: 'belichtungsrahmen/hausstil' },
          verdict: { passed: true },
        },
      });
      expect(res.success).toBe(false);
    });

    it('der alte dinov3-Weg mit echter Zahl bleibt unveraendert gueltig', () => {
      const res = RenderResult.parse({
        job_id: 'vis-1751400000-a1b2c3',
        images: ['renders/cam-01.png'],
        qa: { style: { style_score: 0.42, passed: true }, verdict: { passed: true } },
      });
      expect(res.qa.style?.style_score).toBe(0.42);
      expect(res.qa.style?.threshold).toBe(0.3);
      expect(res.qa.style?.method).toBe('dinov3');
    });
  });

  // P6 (auftraege-kosmovis/auf-20260826-53.md, Zeilen 30-120, U7 — Zwischenspeicher-
  // Treffer erkennbar machen). U7a (erg-20260917-53-zwischenspeicher-und-
  // gelaendefrage.md): «je Kamera reicht als Datenquelle» — keine Aggregation je
  // Auftrag, die Anzeige rechnet aus den Kamera-Werten. Feldnamen woertlich aus dem
  // Auftragsblatt uebernommen, Struktur an der einzigen bestehenden Pro-Kamera-Stelle
  // des Ergebnisvertrags angebaut: `qa_je_kamera` (V2, auf-20260826-49).
  describe('P6 (auf-20260826-53, U7): zwischenspeicher je Kamera in qa_je_kamera', () => {
    it('nimmt zwischenspeicher.{treffer,schluessel,gerechnet_unter} je Kamera an — Feldnamen woertlich aus dem Auftragsblatt', () => {
      const res = RenderResult.parse({
        job_id: 'vis-1758100000-a1b2c3',
        images: ['renders/cam-s.png', 'renders/cam-nnw.png'],
        qa: { verdict: { passed: true } },
        qa_je_kamera: [
          {
            kamera: 's',
            zwischenspeicher: { treffer: true, schluessel: 'a'.repeat(64), gerechnet_unter: '4.2.1 LTS' },
          },
          {
            kamera: 'nnw',
            zwischenspeicher: { treffer: false, schluessel: 'b'.repeat(64), gerechnet_unter: '4.2.1 LTS' },
          },
        ],
      });
      expect(res.qa_je_kamera?.[0]?.zwischenspeicher).toEqual({
        treffer: true,
        schluessel: 'a'.repeat(64),
        gerechnet_unter: '4.2.1 LTS',
      });
      expect(res.qa_je_kamera?.[1]?.zwischenspeicher?.treffer).toBe(false);
    });

    it('verweigert einen falschen Werttyp bei treffer (kein stilles Raten)', () => {
      const payload = {
        job_id: 'vis-1758100000-a1b2c3',
        images: [] as string[],
        qa: { verdict: { passed: true } },
        qa_je_kamera: [
          { kamera: 's', zwischenspeicher: { treffer: 'ja', schluessel: 'x'.repeat(64), gerechnet_unter: '4.2.1 LTS' } },
        ],
      };
      const ergebnis = RenderResult.safeParse(payload);
      expect(ergebnis.success).toBe(false);
    });
  });

  // P7 (gleiche Quelle, Zeilen 86-88, U8 — die Gelaendefrage vorlegen statt
  // abverlangen). Dreiwertig wie `GeometryStatus`/`gelaende` in render-scene.ts, weil
  // die Regel «geprueft und nichts gefunden» von «nichts zu lesen gehabt» trennen muss
  // (dieselbe Nullgeometrie-Lehre wie oben). Angebaut an `GeometryQA`, weil die
  // Begruendung wortwoertlich die Geometrie-QA-Maskierung betrifft und `GeometryQA`
  // sowohl am Job (`qa.geometry`) als auch je Kamera (`qa_je_kamera[].geometry`)
  // wiederverwendet wird — die Granularitaet ist im Auftragsblatt nicht festgelegt,
  // dieser Anbau deckt beide Faelle ab, ohne eine Wahl zu erfinden.
  // ACHTUNG: `vis.kein_gelaende` (U8b) ist NICHT Teil dieses Ergebnisvertrags — laut
  // erg-20260917-53 gehoert die Rueckfrage-Antwort in den AUFTRAG
  // (kosmovis.render-scene), nicht ins Ergebnis, und ist dort nicht entschieden.
  describe('P7 (auf-20260826-53, U8): gelaende_befund/-geprueft/-begruendung in GeometryQA', () => {
    it('nimmt die drei Felder an — Feldnamen woertlich aus dem Auftragsblatt', () => {
      const res = RenderResult.parse({
        job_id: 'vis-1758100000-a1b2c3',
        images: ['renders/cam-s.png'],
        qa: {
          geometry: {
            passed: true,
            gelaende_befund: 'kein_gelaende_belegt',
            gelaende_geprueft: ['Beton_Decke', 'Beton_Kern', 'Glas_Fassade'],
            gelaende_begruendung: 'Keiner der elf geprueften Baustoffnamen deutet auf Gelaende.',
          },
          verdict: { passed: true },
        },
      });
      expect(res.qa.geometry?.gelaende_befund).toBe('kein_gelaende_belegt');
      expect(res.qa.geometry?.gelaende_geprueft).toEqual(['Beton_Decke', 'Beton_Kern', 'Glas_Fassade']);
      expect(res.qa.geometry?.gelaende_begruendung).toContain('Baustoffnamen');
    });

    it('nimmt alle drei Befund-Werte an: gelaende_gefunden, kein_gelaende_belegt, nicht_entscheidbar', () => {
      for (const befund of ['gelaende_gefunden', 'kein_gelaende_belegt', 'nicht_entscheidbar'] as const) {
        const res = RenderResult.parse({
          job_id: 'vis-1758100000-a1b2c3',
          images: [] as string[],
          qa: { geometry: { passed: true, gelaende_befund: befund }, verdict: { passed: true } },
        });
        expect(res.qa.geometry?.gelaende_befund).toBe(befund);
      }
    });

    it('verweigert einen unbekannten Befund-Wert (kein stilles Raten auf einen vierten Zustand)', () => {
      const payload = {
        job_id: 'vis-1758100000-a1b2c3',
        images: [] as string[],
        qa: { geometry: { passed: true, gelaende_befund: 'vielleicht' }, verdict: { passed: true } },
      };
      const ergebnis = RenderResult.safeParse(payload);
      expect(ergebnis.success).toBe(false);
    });

    it('ist auch je Kamera lesbar, weil GeometryQA in qa_je_kamera[].geometry wiederverwendet wird', () => {
      const res = RenderResult.parse({
        job_id: 'vis-1758100000-a1b2c3',
        images: [] as string[],
        qa: { verdict: { passed: true } },
        qa_je_kamera: [{ kamera: 's', geometry: { passed: true, gelaende_befund: 'gelaende_gefunden' } }],
      });
      expect(res.qa_je_kamera?.[0]?.geometry?.gelaende_befund).toBe('gelaende_gefunden');
    });

    it('U8b (erg-20260917-53): ein mitgeschicktes `kein_gelaende` wird still abgestreift — dieses Feld ist NICHT gebaut, es gehoert in den Auftrag', () => {
      const payload = {
        job_id: 'vis-1758100000-a1b2c3',
        images: [] as string[],
        qa: { geometry: { passed: true, kein_gelaende: true }, verdict: { passed: true } },
      };
      const res = RenderResult.parse(payload);
      expect('kein_gelaende' in (res.qa.geometry as object)).toBe(false);
    });
  });

  // Pflichtpruefung (Arbeitsregel 3): eine Nutzlast ganz ohne die additiven P6/P7-Felder
  // muss weiterhin safeParse mit success:true bestehen — sonst waeren die Felder nicht
  // wirklich optional.
  it('P6/P7 Rueckwaertsvertraeglichkeit: eine Nutzlast ohne zwischenspeicher/gelaende_* bleibt gueltig', () => {
    const ergebnis = RenderResult.safeParse({
      job_id: 'vis-1758100000-a1b2c3',
      images: ['renders/cam-01.png'],
      qa: { verdict: { passed: true } },
    });
    expect(ergebnis.success).toBe(true);
  });
});

describe('kosmo.project/v1', () => {
  it('setzt Review-Gates konservativ (Owner-Kultur: nichts ungefragt nach aussen)', () => {
    const m = KosmoProjectManifest.parse({
      // schema seit auf-orbit-20260828-16 Posten 11 PFLICHT (kein `.default()`
      // mehr) — dieser Test baute vorher ein Manifest ohne `schema` und
      // profitierte unbemerkt vom (falschen) Lese-Default. Befund im Bericht.
      schema: 'kosmo.project/v1',
      id: 'testobjekt-lichthof',
      name: 'Testobjekt Lichthof',
      created_at: '2026-07-02T08:00:00Z',
      updated_at: '2026-07-02T08:00:00Z',
    });
    expect(m.review_gates.public_release.enabled).toBe(false);
    expect(m.review_gates.paid_cloud_job.requires_human_approval).toBe(true);
    expect(m.contents.model).toBe('model/model.json');
  });
});

describe('bridge embed (E3)', () => {
  it('validiert Request/Response und weist Leeres ab', async () => {
    const { EmbedRequest, EmbedResponse, bridgeRoutes } = await import('../src');
    expect(bridgeRoutes.embed).toBe('/embed');
    expect(EmbedRequest.parse({ texts: ['Beton nach SIA'] }).texts).toHaveLength(1);
    expect(() => EmbedRequest.parse({ texts: [] })).toThrow();
    const res = EmbedResponse.parse({ vectors: [[0.1, 0.2]], model: 'bge-m3' });
    expect(res.vectors[0]).toHaveLength(2);
    expect(() => EmbedResponse.parse({ vectors: [] })).toThrow();
  });
});

describe('V2-Technik Block 1 — Job-Lebenszyklus (additiv, kein Breaking Change)', () => {
  it('parst eine HEUTIGE Bridge-Job-Antwort unverändert (keine neuen Pflichtfelder)', () => {
    // Fixture aus einem Live-Lauf der Fake-Bridge (POST /jobs):
    const heute = RenderJob.parse({
      job_id: 'vis-1783414811-ab095c',
      status: 'queued',
      scene: '/tmp/kosmo-jobs/vis-1783414811-ab095c/render-scene.json',
      approval_token: 'CONFIRMED_RENDER_1c214b97',
      idle_window_only: true,
      created_at: '2026-07-07T08:00:00Z',
    });
    expect(heute.worker).toBeUndefined();
    expect(heute.progress).toBeUndefined();
    expect(heute.requested_engine).toBeUndefined();
  });

  it('parst einen done-Record MIT eingebettetem Ergebnis (GET /jobs/{id})', () => {
    // Form des Fake-Workers (main.py: record + eingebettetes render-result.json):
    const done = RenderJob.parse({
      job_id: 'vis-1783414811-ab095c',
      status: 'done',
      scene: 's.json',
      created_at: '2026-07-07T08:00:00Z',
      updated_at: '2026-07-07T08:00:03Z',
      worker: 'fake-worker',
      result: {
        schema: 'kosmovis.render-result/v2',
        job_id: 'vis-1783414811-ab095c',
        images: ['cam-01.png'],
        ai_variant: 'cam-01.png',
        qa: {
          style: { style_score: 0.42, threshold: 0.3, passed: true, method: 'dinov3' },
          geometry: {
            geometry_fidelity: 0.87,
            spearman: 0.93,
            geom_iou: 0.81,
            threshold: 0.65,
            passed: true,
            method: 'fake-worker',
          },
          verdict: { passed: true, reason: 'Fake-Worker (Demo ohne GPU)' },
        },
      },
    });
    // Ohne das `result`-Feld hätte zod es stumm gestrippt (Fable-Review-1):
    expect(done.result?.qa.verdict.passed).toBe(true);
    expect(done.result?.qa.geometry?.method).toBe('fake-worker');
  });

  it('nimmt die neuen Lebenszyklus-Felder an (worker/progress/requested_engine/message)', () => {
    const job = RenderJob.parse({
      job_id: 'vis-1783414811-ab095c',
      status: 'running',
      scene: 's.json',
      created_at: '2026-07-07T08:00:00Z',
      worker: 'fake-worker',
      progress: { phase: 'rendern', pct: 0.5 },
      requested_engine: 'cycles',
      message: 'läuft',
    });
    expect(job.progress?.pct).toBe(0.5);
    expect(job.requested_engine).toBe('cycles');
  });

  it('v0.8.9 E9: requested_style ist additiv und optional', () => {
    const ohne = RenderJob.parse({
      job_id: 'vis-1783414811-ab095c',
      status: 'queued',
      scene: 's.json',
      created_at: '2026-07-07T08:00:00Z',
    });
    expect(ohne.requested_style).toBeUndefined();
    const mit = RenderJob.parse({
      job_id: 'vis-1783414811-ab095c',
      status: 'queued',
      scene: 's.json',
      created_at: '2026-07-07T08:00:00Z',
      requested_style: 'lineart',
    });
    expect(mit.requested_style).toBe('lineart');
    expect(() =>
      RenderJob.parse({
        job_id: 'vis-1-abcdef',
        status: 'queued',
        scene: 's.json',
        created_at: 'x',
        requested_style: 'unbekannt',
      }),
    ).toThrow();
  });

  it('weist ungültigen Fortschritt (pct > 1) und unbekannte Engine ab', async () => {
    const { RenderJobProgress } = await import('../src');
    expect(() => RenderJobProgress.parse({ phase: 'x', pct: 1.4 })).toThrow();
    expect(() =>
      RenderJob.parse({
        job_id: 'vis-1-abcdef',
        status: 'queued',
        scene: 's.json',
        created_at: 'x',
        requested_engine: 'blender',
      }),
    ).toThrow();
  });

  it('kennt approve/cancel/blender-sim-Routen', async () => {
    const { bridgeRoutes } = await import('../src');
    expect(bridgeRoutes.jobApprove('vis-1-abcdef')).toBe('/jobs/vis-1-abcdef/approve');
    expect(bridgeRoutes.jobCancel('vis-1-abcdef')).toBe('/jobs/vis-1-abcdef/cancel');
    expect(bridgeRoutes.jobsBlenderSim).toBe('/jobs/blender-sim');
  });

  it('BridgeHealth parst mit UND ohne embed-Service (rückwärtskompatibel)', async () => {
    const { BridgeHealth } = await import('../src');
    const mit = BridgeHealth.parse({
      ok: true,
      version: '1.0.0',
      services: { jobstore: true, ollama: false, stt: true, tts: true, embed: true },
    });
    expect(mit.services.embed).toBe(true);
    const ohne = BridgeHealth.parse({
      ok: true,
      version: '1.0.0',
      services: { jobstore: true, ollama: false, stt: true, tts: true },
    });
    expect(ohne.services.embed).toBeUndefined();
  });
});

describe('V2-Technik Block 1 — video-splat (eigenes Schema, kein-sfm-worker ehrlich)', () => {
  it('parst den ehrlichen kein-sfm-worker-Record', async () => {
    const { VideoSplatJob } = await import('../src');
    const job = VideoSplatJob.parse({
      job_id: 'vsplat-1783414062-a2c3b1',
      status: 'kein-sfm-worker',
      created_at: '2026-07-07T08:00:00Z',
      message: 'Video→Splat braucht einen SfM-Worker auf der HomeStation.',
    });
    expect(job.kind).toBe('video-splat');
    expect(job.status).toBe('kein-sfm-worker');
  });

  it('weist die vis-/bsim-Job-ID beim video-splat-Record ab', async () => {
    const { VideoSplatJob } = await import('../src');
    expect(() =>
      VideoSplatJob.parse({ job_id: 'vis-1-abcdef', status: 'queued', created_at: 'x' }),
    ).toThrow();
  });

  it('nimmt awaiting_approval + approval_token an (Freigabe-Pflicht, HS3-Auflage 4)', async () => {
    const { VideoSplatJob } = await import('../src');
    const job = VideoSplatJob.parse({
      job_id: 'vsplat-1783414062-a2c3b1',
      status: 'awaiting_approval',
      approval_token: 'CONFIRMED_SPLAT_1c214b97',
      created_at: '2026-07-07T08:00:00Z',
    });
    expect(job.status).toBe('awaiting_approval');
    expect(job.approval_token).toBe('CONFIRMED_SPLAT_1c214b97');
  });
});

describe('kosmo.blender-sim/v1 — Physik wird nie gefakt', () => {
  it('akzeptiert eine Wind-Simulationsszene und füllt Defaults', async () => {
    const { BlenderSimScene } = await import('../src');
    const s = BlenderSimScene.parse({
      art: 'wind',
      geometry: { path: 'model/model.glb' },
      out: 'sims/bsim-001',
    });
    expect(s.schema).toBe('kosmo.blender-sim/v1');
    expect(s.geometry.format).toBe('glb');
    expect(s.params).toEqual({});
  });

  it('verweigert eine unbekannte Simulationsart', async () => {
    const { BlenderSimScene } = await import('../src');
    expect(() =>
      BlenderSimScene.parse({ art: 'erdbeben', geometry: { path: 'm.glb' }, out: 'x' }),
    ).toThrow();
  });

  it('parst den kein-blender-worker-Record und erzwingt das bsim-Präfix', async () => {
    const { BlenderSimJob } = await import('../src');
    const job = BlenderSimJob.parse({
      job_id: 'bsim-1783414062-a2c3b1',
      status: 'kein-blender-worker',
      art: 'sonnenstunden',
      scene: 'blender-sim.json',
      created_at: '2026-07-07T08:00:00Z',
      message: 'Braucht Blender headless auf der HomeStation.',
    });
    expect(job.status).toBe('kein-blender-worker');
    expect(() =>
      BlenderSimJob.parse({
        job_id: 'vis-1-abcdef',
        status: 'queued',
        art: 'wind',
        scene: 's.json',
        created_at: 'x',
      }),
    ).toThrow();
  });

  it('nimmt awaiting_approval + approval_token an (Freigabe-Pflicht, HS3-Auflage 4)', async () => {
    const { BlenderSimJob } = await import('../src');
    const job = BlenderSimJob.parse({
      job_id: 'bsim-1783414062-a2c3b1',
      status: 'awaiting_approval',
      approval_token: 'CONFIRMED_SIM_1c214b97',
      art: 'wind',
      scene: 'blender-sim.json',
      created_at: '2026-07-07T08:00:00Z',
    });
    expect(job.status).toBe('awaiting_approval');
    expect(job.approval_token).toBe('CONFIRMED_SIM_1c214b97');
  });

  it('v0.8.9 E9: SonnenstundenResult parst und BlenderSimJob.result nimmt es an', async () => {
    const { SonnenstundenResult, BlenderSimJob } = await import('../src');
    const result = SonnenstundenResult.parse({
      stunden: 3.5,
      kriteriumErfuellt: true,
      methode: 'blender-cycles-sun-sampling',
    });
    expect(result.schema).toBe('kosmo.sonnenstunden-result/v1');
    const job = BlenderSimJob.parse({
      job_id: 'bsim-1783414062-a2c3b1',
      status: 'done',
      art: 'sonnenstunden',
      scene: 'blender-sim.json',
      created_at: '2026-07-07T08:00:00Z',
      result,
    });
    expect(job.result?.stunden).toBe(3.5);
    expect(job.result?.kriteriumErfuellt).toBe(true);
  });

  it('v0.8.9 E9: SonnenstundenResult verweigert fehlende Pflichtfelder', async () => {
    const { SonnenstundenResult } = await import('../src');
    expect(() => SonnenstundenResult.parse({ stunden: 3.5 })).toThrow();
  });
});

describe('kosmo.bake-job/v1 — Geometrie-Klasse mit Optimierungs-Behauptung (v0.8.9 §9 E9)', () => {
  it('akzeptiert eine Bake-Szene und füllt Defaults (unwrap smart-uv)', async () => {
    const { BakeJobScene } = await import('../src');
    const scene = BakeJobScene.parse({
      geometry: { path: 'model/model.glb' },
      params: {},
      out: 'bakes/bake-001',
    });
    expect(scene.schema).toBe('kosmo.bake-job/v1');
    expect(scene.geometry.format).toBe('glb');
    expect(scene.params.unwrap).toBe('smart-uv');
  });

  it('verweigert eine unbekannte unwrap-Strategie', async () => {
    const { BakeJobScene } = await import('../src');
    expect(() =>
      BakeJobScene.parse({
        geometry: { path: 'm.glb' },
        params: { unwrap: 'marching-cubes' },
        out: 'x',
      }),
    ).toThrow();
  });

  it('verweigert eine Szene ohne geometry', async () => {
    const { BakeJobScene } = await import('../src');
    expect(() =>
      BakeJobScene.parse({
        params: {},
        out: 'x',
      }),
    ).toThrow();
  });

  it('parst den kein-blender-worker-Record und erzwingt das bake-Präfix', async () => {
    const { BakeJob } = await import('../src');
    const job = BakeJob.parse({
      job_id: 'bake-1783414062-a2c3b1',
      status: 'kein-blender-worker',
      scene: 'bake-job.json',
      created_at: '2026-07-07T08:00:00Z',
      message: 'Braucht Blender headless auf der HomeStation.',
    });
    expect(job.kind).toBe('bake');
    expect(job.status).toBe('kein-blender-worker');
    expect(() =>
      BakeJob.parse({
        job_id: 'bsim-1-abcdef',
        status: 'queued',
        scene: 's.json',
        created_at: 'x',
      }),
    ).toThrow();
  });

  it('nimmt awaiting_approval + CONFIRMED_BAKE_-Token an (Freigabe-Pflicht-Symmetrie)', async () => {
    const { BakeJob } = await import('../src');
    const job = BakeJob.parse({
      job_id: 'bake-1783414062-a2c3b1',
      status: 'awaiting_approval',
      approval_token: 'CONFIRMED_BAKE_1c214b97',
      scene: 'bake-job.json',
      created_at: '2026-07-07T08:00:00Z',
    });
    expect(job.status).toBe('awaiting_approval');
    expect(job.approval_token).toBe('CONFIRMED_BAKE_1c214b97');
    expect(() =>
      BakeJob.parse({
        job_id: 'bake-1783414062-a2c3b1',
        status: 'awaiting_approval',
        approval_token: 'CONFIRMED_SIM_1c214b97',
        scene: 'bake-job.json',
        created_at: '2026-07-07T08:00:00Z',
      }),
    ).toThrow();
  });

  it('parst ein done-Ergebnis mit BakeResult (triangles_before/after optional)', async () => {
    const { BakeJob } = await import('../src');
    const job = BakeJob.parse({
      job_id: 'bake-1783414062-a2c3b1',
      status: 'done',
      scene: 'bake-job.json',
      created_at: '2026-07-07T08:00:00Z',
      worker: 'echter-worker',
      result: {
        baked_glb: 'out/baked.glb',
        method: 'blender-smart-uv-ao-bake',
        triangles_before: 120000,
        triangles_after: 45000,
      },
    });
    expect(job.result?.schema).toBe('kosmo.bake-result/v1');
    expect(job.result?.triangles_after).toBe(45000);
  });

  it('bridgeRoutes.jobsBake ist additiv verankert', async () => {
    const { bridgeRoutes } = await import('../src');
    expect(bridgeRoutes.jobsBake).toBe('/jobs/bake');
  });
});

describe('kosmodev.workorder/v1 (Block 2 / AB1)', () => {
  const auftrag = {
    id: 'auftrag-abc123-x1',
    ts: '2026-07-07T09:00:00Z',
    text: 'Der Wand-Dialog soll den letzten Aufbau vorschlagen',
    quelle: 'getippt',
    station: 'KosmoDesign',
  };

  it('parst eine Workorder und füllt das Schema-Literal als Default', async () => {
    const { Workorder } = await import('../src');
    const wo = Workorder.parse({
      projekt: 'Testobjekt Lichthof',
      erzeugt_um: '2026-07-07T09:05:00Z',
      auftraege: [auftrag, { ...auftrag, id: 'auftrag-abc123-x2', quelle: 'kosmo', ort: 'Werkzeugleiste' }],
    });
    expect(wo.schema).toBe('kosmodev.workorder/v1');
    expect(wo.auftraege).toHaveLength(2);
    expect(wo.auftraege[1]?.ort).toBe('Werkzeugleiste');
  });

  it('verweigert eine leere Workorder (min 1 Auftrag) und unbekannte Quellen', async () => {
    const { Workorder } = await import('../src');
    expect(() =>
      Workorder.parse({ projekt: 'P', erzeugt_um: 'x', auftraege: [] }),
    ).toThrow();
    expect(() =>
      Workorder.parse({
        projekt: 'P',
        erzeugt_um: 'x',
        auftraege: [{ ...auftrag, quelle: 'telepathisch' }],
      }),
    ).toThrow();
  });

  it('erzwingt das dev-Präfix am Job-Record (kein Vermischen mit vis-/bsim-)', async () => {
    const { DevJob } = await import('../src');
    const job = DevJob.parse({
      job_id: 'dev-1783414062-a2c3b1',
      status: 'queued',
      created_at: '2026-07-07T09:05:00Z',
      anzahl_auftraege: 2,
    });
    expect(job.kind).toBe('dev-workorder');
    expect(() =>
      DevJob.parse({
        job_id: 'vis-1783414062-a2c3b1',
        status: 'queued',
        created_at: 'x',
        anzahl_auftraege: 1,
      }),
    ).toThrow();
  });

  it('kennt bewusst KEIN awaiting_approval — Absenden ist die Owner-Handlung (E2)', async () => {
    const { DevJobStatus } = await import('../src');
    expect(DevJobStatus.options).toEqual(['queued', 'running', 'done', 'error', 'cancelled']);
    expect(DevJobStatus.safeParse('awaiting_approval').success).toBe(false);
  });

  it('Result verlangt den Worker-Namen — «Simulation» bleibt sichtbar (E5)', async () => {
    const { DevJobResult } = await import('../src');
    expect(() =>
      DevJobResult.parse({
        abgeschlossen_um: '2026-07-07T10:00:00Z',
        ergebnisse: [{ auftrag_id: 'a1', umgesetzt: false }],
      }),
    ).toThrow();
    const fake = DevJobResult.parse({
      worker: 'fake-worker',
      abgeschlossen_um: '2026-07-07T10:00:00Z',
      ergebnisse: [
        { auftrag_id: 'a1', umgesetzt: false, notiz: 'Simulation — keine echte Umsetzung' },
      ],
    });
    expect(fake.ergebnisse[0]?.commit).toBeUndefined();
  });

  it('ein echtes Ergebnis trägt den Commit-Beleg', async () => {
    const { DevJob } = await import('../src');
    const job = DevJob.parse({
      job_id: 'dev-1783414062-a2c3b1',
      status: 'done',
      created_at: '2026-07-07T09:05:00Z',
      updated_at: '2026-07-07T11:00:00Z',
      anzahl_auftraege: 1,
      worker: 'claude-code@homestation',
      result: {
        worker: 'claude-code@homestation',
        abgeschlossen_um: '2026-07-07T11:00:00Z',
        ergebnisse: [
          { auftrag_id: 'a1', umgesetzt: true, commit: 'ab12cd3', notiz: 'Dialog merkt sich den Aufbau' },
        ],
      },
    });
    expect(job.result?.ergebnisse[0]?.umgesetzt).toBe(true);
    expect(job.result?.ergebnisse[0]?.commit).toBe('ab12cd3');
  });

  it('die Dev-Routen sind additiv in bridgeRoutes verankert', async () => {
    const { bridgeRoutes } = await import('../src');
    expect(bridgeRoutes.jobsDev).toBe('/jobs/dev');
    expect(bridgeRoutes.jobDev('dev-1-abcdef')).toBe('/jobs/dev/dev-1-abcdef');
    expect(bridgeRoutes.jobDevClaim('x')).toBe('/jobs/dev/x/claim');
    expect(bridgeRoutes.jobDevResult('x')).toBe('/jobs/dev/x/result');
    expect(bridgeRoutes.jobDevCancel('x')).toBe('/jobs/dev/x/cancel');
  });
});

describe('P-KANTENANTEIL (22.08., demo-kritisch) — SEIN Name, nicht meine Abkuerzung', () => {
  /**
   * In v0.9.42 habe ich den Feldnamen aus dem Blatt des Cloud-Workers zu
   * `kante` abgekuerzt. Er schickt `kantenanteil`. Der Owner hat am 21.08.
   * entschieden, dass die Geometrie-QA in der Demo SICHTBAR ist (Weg A) —
   * damit ist dieser Name demo-kritisch.
   *
   * Die Faelle unten fahren SEINEN woertlichen Auftragskoerper aus
   * `auftraege/von-homestation/auf-orbit-20260821-02.md`, nicht eine
   * Nachbildung davon.
   */
  const seinKoerper = {
    schema: 'kosmovis.render-result/v2' as const,
    job_id: 'vis-1787245160-895ba3',
    status: 'done' as const,
    images: ['ssE.png'],
    qa: {
      geometry: {
        rho_maske: -0.9059,
        kantenanteil: 0.874,
        paarurteil: { rho_maske: -0.9059, kantenanteil: 0.874 },
        passed: true,
      },
      style: {
        style_score: null,
        threshold: null,
        passed: true,
        method: 'belichtungsrahmen/hausstil',
      },
      verdict: { passed: true, reason: 'Belichtungsrahmen Hausstil' },
    },
  };

  it('sein woertlicher Koerper wird angenommen, und BEIDE Zahlen kommen an', () => {
    const r = RenderResult.safeParse(seinKoerper);
    expect(r.success).toBe(true);
    if (!r.success) return;
    expect(r.data.qa?.geometry?.rho_maske).toBe(-0.9059);
    expect(r.data.qa?.geometry?.kantenanteil).toBe(0.874);
    // Das Paar bleibt ein Paar — nicht zu einer Zahl verrechnet.
    expect(r.data.qa?.geometry?.paarurteil).toEqual({ rho_maske: -0.9059, kantenanteil: 0.874 });
  });

  it('der Zweitname `kante` aus v0.9.42 bleibt zulaessig — nichts Gebautes bricht', () => {
    const mitZweitname = {
      ...seinKoerper,
      qa: {
        ...seinKoerper.qa,
        geometry: { rho_maske: 0.93, kante: 0.4, paarurteil: { rho_maske: 0.93, kante: 0.4 }, passed: true },
      },
    };
    const r = RenderResult.safeParse(mitZweitname);
    expect(r.success).toBe(true);
    if (!r.success) return;
    expect(r.data.qa?.geometry?.kante).toBe(0.4);
  });

  /**
   * UEBERHOLT seit P-EICHUNG (23.08., `auftraege/von-homestation/
   * auf-orbit-20260823-03.md`, Commit `de13dca6`): dieser Test prüfte bis
   * hierhin die Pflicht-Kantenzahl im `superRefine` — genau die Pflicht,
   * die der Cloud-Worker heute zurückzieht (`kantenanteil` "haelt an neun
   * [Bildern] nicht"). Der `superRefine` ist entfernt; ein `paarurteil` mit
   * NUR `rho_maske` ist jetzt ein vollstaendiges, gueltiges Urteil. Siehe
   * den neuen Block P-EICHUNG unten fuer den Rot-vor-Gruen-Beleg.
   */
  it('ein `paarurteil` OHNE Kantenzahl besteht jetzt — die Pflicht ist zurueckgezogen (P-EICHUNG 23.08.)', () => {
    const nurRhoMaske = {
      ...seinKoerper,
      qa: {
        ...seinKoerper.qa,
        geometry: { rho_maske: 0.93, paarurteil: { rho_maske: 0.93 }, passed: true },
      },
    };
    const r = RenderResult.safeParse(nurRhoMaske);
    expect(r.success).toBe(true);
    if (!r.success) return;
    expect(r.data.qa?.geometry?.paarurteil).toEqual({ rho_maske: 0.93 });
  });
});

/**
 * P-EICHUNG (23.08.2026, demo-kritisch, `auftraege/von-homestation/
 * auf-orbit-20260823-03.md`, Commit `de13dca6`): der Cloud-Worker hat seinen
 * eigenen `kantenanteil`-Vorschlag aus `auf-20260822-30` EICHUNGSHALBER
 * zurueckgezogen ("Relativ gerechnet erreichen GRAU UND VERLAUF 100 % ... der
 * Vorschlag war an drei Bildern plausibel und haelt an neun nicht.") und
 * `rho_maske` als geeicht bestaetigt (Schwelle 0.80, groesster Abstand
 * zwischen zwei Szenen 0.0049, streng monoton im Versatz). `paarurteil`
 * MUSS darum OHNE Kantenzahl bestehen koennen — sonst weist unser eigener
 * Vertrag die einzige Form ab, die der Worker jetzt noch schickt.
 *
 * Die Probe unten ist der woertliche `RenderJob`-Koerper (nicht nur
 * `RenderResult`) — job_id nach dem Muster `^vis-\d+-[0-9a-f]{6}$`, `scene`
 * als STRING, `result` eingebettet wie ihn `GET /jobs/{id}` liefert. Das ist
 * dieselbe Form, an der `parseJob` (vis-jobs.ts) tatsaechlich prueft.
 */
describe('P-EICHUNG (23.08., demo-kritisch) — rho_maske geeicht, kantenanteil zurueckgezogen', () => {
  const jobMitNurRhoMaske = {
    job_id: 'vis-1787245160-895ba3',
    status: 'done' as const,
    scene: '/tmp/kosmo-jobs/vis-1787245160-895ba3/render-scene.json',
    created_at: '2026-08-23T09:00:00Z',
    result: {
      schema: 'kosmovis.render-result/v2' as const,
      job_id: 'vis-1787245160-895ba3',
      images: ['ssE.png'],
      qa: {
        geometry: {
          rho_maske: 0.8437,
          // KEIN kantenanteil, KEIN kante — genau die Form, die der Worker
          // seit dem 23.08. noch sendet.
          paarurteil: { rho_maske: 0.8437 },
          passed: true,
        },
        verdict: { passed: true },
      },
    },
  };

  it('PROBE ohne kantenanteil: besteht jetzt (vorher ABGEWIESEN am superRefine)', () => {
    const r = RenderJob.safeParse(jobMitNurRhoMaske);
    expect(r.success).toBe(true);
    if (!r.success) return;
    expect(r.data.result?.qa.geometry?.rho_maske).toBe(0.8437);
    expect(r.data.result?.qa.geometry?.paarurteil).toEqual({ rho_maske: 0.8437 });
  });

  it('Gegenprobe MIT kantenanteil: bestand schon vorher und besteht weiter (einziger Unterschied: das eine Feld)', () => {
    const jobMitKantenanteil = {
      ...jobMitNurRhoMaske,
      result: {
        ...jobMitNurRhoMaske.result,
        qa: {
          ...jobMitNurRhoMaske.result.qa,
          geometry: {
            ...jobMitNurRhoMaske.result.qa.geometry,
            kantenanteil: 0.243,
            paarurteil: { rho_maske: 0.8437, kantenanteil: 0.243 },
          },
        },
      },
    };
    const r = RenderJob.safeParse(jobMitKantenanteil);
    expect(r.success).toBe(true);
    if (!r.success) return;
    expect(r.data.result?.qa.geometry?.kantenanteil).toBe(0.243);
  });

  it('kante_an_maskengrenze ist ein BOOLEAN (ja/nein bei Schwelle 0.01) — keine Zahl', () => {
    const mitFlag = {
      ...jobMitNurRhoMaske,
      result: {
        ...jobMitNurRhoMaske.result,
        qa: {
          ...jobMitNurRhoMaske.result.qa,
          geometry: { ...jobMitNurRhoMaske.result.qa.geometry, kante_an_maskengrenze: true },
        },
      },
    };
    const r = RenderJob.safeParse(mitFlag);
    expect(r.success).toBe(true);
    if (!r.success) return;
    expect(r.data.result?.qa.geometry?.kante_an_maskengrenze).toBe(true);
  });

  it('kante_an_maskengrenze als Zahl (die alte, abgelehnte Guetemass-Form) wird abgewiesen', () => {
    const mitZahl = {
      ...jobMitNurRhoMaske,
      result: {
        ...jobMitNurRhoMaske.result,
        qa: {
          ...jobMitNurRhoMaske.result.qa,
          geometry: { ...jobMitNurRhoMaske.result.qa.geometry, kante_an_maskengrenze: 0.0575 },
        },
      },
    };
    const r = RenderJob.safeParse(mitZahl);
    expect(r.success).toBe(false);
  });
});

describe('P-NULLGEOMETRIE (23.08., demo-kritisch): null heisst NICHT GEMESSEN', () => {
  /**
   * Der Auftragskoerper, den der lokale Worker am 23.08. gemessen hat
   * (auf-orbit-20260823-04). Vor P-NULLGEOMETRIE wies ihn `RenderJob`
   * wortgleich so ab, wie er es gemeldet hat:
   *   result.qa.geometry.geometry_fidelity: Invalid input; spearman: Invalid input
   * Zwei fertige Bilder lagen dabei auf der Platte, die kein Nutzer je sah.
   */
  function auftragMitGeometrie(geometry: Record<string, unknown>) {
    return {
      job_id: 'vis-1755950000-a1b2c3',
      status: 'done',
      created_at: '2026-08-23T17:00:00.000Z',
      scene: '{"schema":"kosmovis.render-scene/v1"}',
      result: {
        schema: 'kosmovis.render-result/v2',
        job_id: 'vis-1755950000-a1b2c3',
        images: ['Eingang.png', 'Uebersicht.png'],
        qa: { geometry, verdict: { passed: false } },
      },
    };
  }

  it('geometry_fidelity und spearman duerfen null sein — der gemessene Fall', () => {
    const r = RenderJob.safeParse(
      auftragMitGeometrie({ geometry_fidelity: null, spearman: null, passed: false }),
    );
    expect(r.success).toBe(true);
  });

  it('auch threshold darf null sein — beim Stil-Zwilling wurde genau das erst mit dem ZWEITEN Feld sichtbar', () => {
    const r = RenderJob.safeParse(
      auftragMitGeometrie({ geometry_fidelity: null, threshold: null, passed: false }),
    );
    expect(r.success).toBe(true);
  });

  it('jedes weitere Zahlen-Mass der Geometrie-QA darf null sein', () => {
    const r = RenderJob.safeParse(
      auftragMitGeometrie({
        geom_iou: null,
        rho_maske: null,
        kantenanteil: null,
        kante: null,
        paarurteil: { rho_maske: null },
        passed: false,
      }),
    );
    expect(r.success).toBe(true);
  });

  it('Gegenprobe: eine echte Zahl bleibt eine echte Zahl, ein Text wird weiter abgewiesen', () => {
    expect(RenderJob.safeParse(auftragMitGeometrie({ rho_maske: 0.9874, passed: true })).success).toBe(true);
    expect(RenderJob.safeParse(auftragMitGeometrie({ rho_maske: 'viel', passed: true })).success).toBe(false);
  });

  it('passed bleibt PFLICHT — ein fehlendes Urteil ist kein fehlendes Mass', () => {
    const r = RenderJob.safeParse(auftragMitGeometrie({ geometry_fidelity: null }));
    expect(r.success).toBe(false);
  });

  /**
   * F1 (c) — die dringendste Auskunft aus `auf-orbit-20260824-05.md`
   * («SECHS VERTRAGSFRAGEN»), woertlich: «Akzeptiert euer Schema ein
   * FEHLENDES Feld? Dann lassen wir den Schluessel weg statt null zu
   * schicken.» Antwort, hier verifiziert statt behauptet: JA — `nullable()`
   * UND `optional()` heisst, der Schluessel darf komplett FEHLEN, nicht nur
   * `null` tragen. Nicht neu gebaut (das Schema oben ist seit `f228c684`
   * unveraendert) — dieser Fall stand nur noch nicht als eigene Probe da.
   */
  it('F1 (c): geometry_fidelity/spearman duerfen als Schluessel GANZ FEHLEN, nicht nur null sein', () => {
    const r = RenderJob.safeParse(auftragMitGeometrie({ passed: false }));
    expect(r.success).toBe(true);
    if (r.success) {
      expect(r.data.result?.qa.geometry?.geometry_fidelity).toBeUndefined();
      expect(r.data.result?.qa.geometry?.spearman).toBeUndefined();
      expect('geometry_fidelity' in (r.data.result?.qa.geometry ?? {})).toBe(false);
    }
  });
});

// Vier Owner-Entscheide vom 03.09.2026 (kosmo-orbit/docs/auftraege-kosmovis/,
// Antworten in auftraege/ergebnisse/) — alle additiv, alle .optional(), kein
// Schema-Literal-Wechsel. Dasselbe Muster wie `komposition`/`environment`/
// `interior`/`gelaende` oben.
describe('F1b (auf-20260823-37, Owner-Entscheid 03.09.2026): status im GeometryQA', () => {
  // Vorlage der Gegenseite (auf-20260823-37.md, F1b): «Seit heute unterscheiden
  // wir drei Zustaende: GEMESSEN, NICHT GEMESSEN, NICHT ZUSTAENDIG. [...] Ein
  // gruenes Abzeichen waere dort in die gefaehrliche Richtung falsch, ein rotes
  // bloss unfair. Also schweigen wir — und das muss bei euch ankommen koennen.»
  it('status nimmt measured/not_measured/not_applicable an', () => {
    for (const status of ['measured', 'not_measured', 'not_applicable'] as const) {
      const res = RenderResult.parse({
        job_id: 'vis-1757000000-a1b2c3',
        images: ['renders/cam-01.png'],
        qa: { geometry: { status, passed: status === 'measured' }, verdict: { passed: true } },
      });
      expect(res.qa.geometry?.status).toBe(status);
    }
  });

  it('ein Rekord ohne status bleibt gueltig — das Feld bleibt undefined, kein stiller Default', () => {
    const res = RenderResult.parse({
      job_id: 'vis-1757000000-a1b2c3',
      images: ['renders/cam-01.png'],
      qa: { geometry: { rho_maske: 0.91, passed: true }, verdict: { passed: true } },
    });
    expect(res.qa.geometry?.status).toBeUndefined();
    expect('status' in (res.qa.geometry ?? {})).toBe(false);
  });

  it('weist einen unbekannten status-Wert ab (kein stilles Raten auf einen vierten Zustand)', () => {
    const ergebnis = RenderResult.safeParse({
      job_id: 'vis-1757000000-a1b2c3',
      images: [],
      qa: { geometry: { status: 'unklar', passed: false }, verdict: { passed: false } },
    });
    expect(ergebnis.success).toBe(false);
  });

  it('not_applicable erlaubt weiterhin null-Zahlenfelder — der dritte Zustand, der bisher fehlte', () => {
    // Der HomeStation-Fall aus dem Blatt: Nachbargebaeude statt Himmel hinter
    // dem Bauwerk trennt das Umrissmass ein PERFEKTES Bild nicht mehr von
    // weissem Rauschen (+0.0016 gegen -0.0024) — status macht sichtbar, WARUM
    // hier geschwiegen wird, statt eines falschen gruenen oder roten Urteils.
    const res = RenderResult.parse({
      job_id: 'vis-1757000000-a1b2c3',
      images: ['renders/nachbar-01.png'],
      qa: {
        geometry: { status: 'not_applicable', rho_maske: null, passed: true },
        verdict: { passed: true },
      },
    });
    expect(res.qa.geometry?.status).toBe('not_applicable');
    expect(res.qa.geometry?.rho_maske).toBeNull();
  });
});

describe('R2 (auf-20260901-68, Owner-Entscheid 03.09.2026): referenzpunkt an CameraSpec', () => {
  // Owner-Entscheid: die vier Namen des Absenders werden 1:1 uebernommen —
  // keine eigenen Namen, das ist sein Vokabular (auf-20260901-68.md §4, V1).
  it('nimmt alle vier vom Absender vorgeschlagenen Namen an', () => {
    for (const referenzpunkt of [
      'terrain_an_kamera',
      'okff',
      'huellbox_unterkante',
      'weltnull',
    ] as const) {
      const scene = RenderScene.parse({
        geometry: { path: 'm.glb', format: 'glb' },
        out: 'x',
        cameras: [{ position: [5, 1.6, 8], target: [5, 1.2, -3], up_axis: 'y', referenzpunkt }],
      });
      const kamera = scene.cameras as Array<{ referenzpunkt?: string }>;
      expect(kamera[0]?.referenzpunkt).toBe(referenzpunkt);
    }
  });

  it('eine Kamera ohne referenzpunkt bleibt gueltig — kein Bezugspunkt genannt, kein stiller Default', () => {
    const scene = RenderScene.parse({
      geometry: { path: 'm.glb', format: 'glb' },
      out: 'x',
      cameras: [{ position: [5, 1.6, 8], target: [5, 1.2, -3], up_axis: 'y' }],
    });
    const kamera = (scene.cameras as Array<Record<string, unknown>>)[0]!;
    expect(kamera.referenzpunkt).toBeUndefined();
    expect('referenzpunkt' in kamera).toBe(false);
  });

  it('weist einen unbekannten referenzpunkt-Wert ab (kein eigener Name statt seiner vier)', () => {
    const ergebnis = RenderScene.safeParse({
      geometry: { path: 'm.glb', format: 'glb' },
      out: 'x',
      cameras: [{ position: [1, 1, 1], target: [0, 0, 0], up_axis: 'y', referenzpunkt: 'egal-welcher-boden' }],
    });
    expect(ergebnis.success).toBe(false);
  });
});

describe('V2 (auf-20260826-49, Owner-Entscheid 03.09.2026): qa_je_kamera additiv neben qa', () => {
  it('qa_je_kamera traegt je Kamera ein eigenes geometry/style-Urteil, der bestehende qa-Block bleibt unveraendert', () => {
    const res = RenderResult.parse({
      job_id: 'vis-1757000000-a1b2c3',
      images: ['Eingang.png', 'Garten.png', 'Nachbar.png'],
      qa: { verdict: { passed: false } },
      qa_je_kamera: [
        { kamera: 'Eingang', geometry: { rho_maske: 0.91, passed: true } },
        { kamera: 'Garten', geometry: { rho_maske: 0.88, passed: true } },
        { kamera: 'Nachbar', geometry: { status: 'not_applicable', passed: true } },
      ],
    });
    expect(res.qa_je_kamera).toHaveLength(3);
    expect(res.qa_je_kamera?.[2]?.kamera).toBe('Nachbar');
    expect(res.qa_je_kamera?.[2]?.geometry?.status).toBe('not_applicable');
    // Der Verlust, den das Blatt beschreibt: «Wer drei Ansichten bestellt und
    // eine davon faellt durch, sieht heute 'durchgefallen' und nicht, WELCHE.»
    // qa_je_kamera behebt das, OHNE den bestehenden Block zu ersetzen.
    expect(res.qa.verdict.passed).toBe(false);
    expect(res.qa.geometry).toBeUndefined();
  });

  it('ein Ergebnis ohne qa_je_kamera bleibt gueltig — der bestehende qa-Block traegt weiterhin allein', () => {
    const res = RenderResult.parse({
      job_id: 'vis-1751400000-a1b2c3',
      images: ['renders/cam-01.png'],
      qa: { geometry: { rho_maske: 0.9, passed: true }, verdict: { passed: true } },
    });
    expect(res.qa_je_kamera).toBeUndefined();
    expect('qa_je_kamera' in res).toBe(false);
  });

  it('verweigert einen Eintrag ohne Kameranamen — sonst ist nicht erkennbar, WELCHE Kamera durchfiel', () => {
    const ergebnis = RenderResult.safeParse({
      job_id: 'vis-1757000000-a1b2c3',
      images: [],
      qa: { verdict: { passed: false } },
      qa_je_kamera: [{ geometry: { passed: false } }],
    });
    expect(ergebnis.success).toBe(false);
  });
});

describe('R4 (auf-20260822-31, Owner-Entscheid 03.09.2026): Nullproben-Anker in GeometryQA', () => {
  // Owner-Entscheid: NUR der Nullproben-Anker, NICHT die Startwert-Auswahl —
  // siehe der Code-Kommentar bei `nullprobe` in render-result.ts fuer die
  // Abgrenzung. «Ohne diese Zahl ist kein Score einzuordnen» (auf-20260822-31.md).
  it('nullprobe traegt die Werte, die ein Bild OHNE jede Geometrie auf dieser Szene erreicht', () => {
    const res = RenderResult.parse({
      job_id: 'vis-1757000000-a1b2c3',
      images: ['renders/cam-01.png'],
      qa: {
        geometry: {
          geom_iou: 0.9703,
          nullprobe: { geom_iou: 0.9848 },
          passed: true,
        },
        verdict: { passed: true },
      },
    });
    // Der Fall, der diesen Anker ausgeloest hat: ein leeres Grundstueck
    // erreichte 0.9848 gegen 0.9703 fuers perfekte Bild (ROADMAP 1062) — ohne
    // den Anker war die Zahl 0.9703 allein nicht einzuordnen.
    expect(res.qa.geometry?.nullprobe?.geom_iou).toBe(0.9848);
    expect(res.qa.geometry?.geom_iou).toBe(0.9703);
  });

  it('ein Rekord ohne nullprobe bleibt gueltig — kein Anker genannt, kein stiller Default', () => {
    const res = RenderResult.parse({
      job_id: 'vis-1751400000-a1b2c3',
      images: ['renders/cam-01.png'],
      qa: { geometry: { rho_maske: 0.9, passed: true }, verdict: { passed: true } },
    });
    expect(res.qa.geometry?.nullprobe).toBeUndefined();
    expect('nullprobe' in (res.qa.geometry ?? {})).toBe(false);
  });

  it('nullprobe-Zahlen duerfen null sein — dieselbe NICHT-GEMESSEN-Lehre wie bei den Hauptfeldern (P-NULLGEOMETRIE)', () => {
    const res = RenderResult.parse({
      job_id: 'vis-1757000000-a1b2c3',
      images: ['renders/cam-01.png'],
      qa: {
        geometry: { nullprobe: { rho_maske: null }, passed: false },
        verdict: { passed: false },
      },
    });
    expect(res.qa.geometry?.nullprobe?.rho_maske).toBeNull();
  });
});

describe('E76 (Owner-Entscheid 19.09.2026, auf-20260919-104): unbekannteFelder() — die Messung, nicht das Urteil', () => {
  // Zusicherung A: der Normalfall bleibt still — eine gueltige Nutzlast ohne
  // Fremdfelder ergibt eine LEERE Liste.
  it('A — eine gueltige Nutzlast ohne Fremdfelder ergibt eine leere Liste', () => {
    const roh = {
      job_id: 'vis-1757000000-a1b2c3',
      status: 'done',
      scene: '/tmp/kosmo-jobs/vis-1757000000-a1b2c3/render-scene.json',
      created_at: '2026-09-19T10:00:00Z',
      result: {
        job_id: 'vis-1757000000-a1b2c3',
        images: ['renders/cam-01.png'],
        qa: {
          geometry: { passed: true },
          verdict: { passed: true },
        },
        qa_je_kamera: [{ kamera: 'Eingang', geometry: { passed: true } }],
      },
    };
    const geprueft = RenderJob.parse(roh);
    expect(unbekannteFelder(roh, geprueft)).toEqual([]);
  });

  // Zusicherung B: ein Fremdfeld wird gefunden, auch tief verschachtelt und
  // auch in einer Liste — mit dem RICHTIGEN Pfad, nicht nur der Anzahl.
  it('B — ein tief verschachteltes Fremdfeld UND eines in einer Liste werden mit dem richtigen Pfad gefunden', () => {
    const roh = {
      job_id: 'vis-1757000000-a1b2c3',
      status: 'done',
      scene: '/tmp/kosmo-jobs/vis-1757000000-a1b2c3/render-scene.json',
      created_at: '2026-09-19T10:00:00Z',
      result: {
        job_id: 'vis-1757000000-a1b2c3',
        images: ['renders/cam-01.png'],
        qa: {
          // tief verschachtelt: qa.geometry.neues_feld
          geometry: { passed: true, neues_feld: 123 },
          verdict: { passed: true },
        },
        qa_je_kamera: [
          { kamera: 'Eingang', geometry: { passed: true } },
          // in einer Liste, zweiter Eintrag: qa_je_kamera.1.fremdfeld
          { kamera: 'Uebersicht', geometry: { passed: true }, fremdfeld: 'unbekannt' },
        ],
      },
    };
    const geprueft = RenderJob.parse(roh);
    // Gegenprobe zum eigenen Bau: das stille Abstreifen bleibt GEWOLLT
    // (Owner-Entscheid) — der Job selbst bleibt gueltig geparst.
    expect(geprueft.result?.qa.geometry).not.toHaveProperty('neues_feld');
    expect(unbekannteFelder(roh, geprueft)).toEqual([
      'result.qa.geometry.neues_feld',
      'result.qa_je_kamera.1.fremdfeld',
    ]);
  });

  // Zusicherung C: ein `.default()`-Feld ist KEIN Befund — die Zusicherung,
  // an der eine naive Umsetzung (z. B. "alle Schluessel von geprueft minus
  // roh" andersrum gedacht) scheitern wuerde.
  it('C — ein von zod per .default() ergaenztes Feld (idle_window_only) ist KEIN Befund', () => {
    const roh: Record<string, unknown> = {
      job_id: 'vis-1757000000-a1b2c3',
      status: 'done',
      scene: '/tmp/kosmo-jobs/vis-1757000000-a1b2c3/render-scene.json',
      created_at: '2026-09-19T10:00:00Z',
      // idle_window_only bewusst WEGGELASSEN — RenderJob.idle_window_only
      // traegt .default(true).
    };
    expect('idle_window_only' in roh).toBe(false);
    const geprueft = RenderJob.parse(roh);
    // zod hat das Feld ERGAENZT, nicht aus roh uebernommen:
    expect(geprueft.idle_window_only).toBe(true);
    const befunde = unbekannteFelder(roh, geprueft);
    expect(befunde).not.toContain('idle_window_only');
    expect(befunde).toEqual([]);
  });

  // Dasselbe nochmal am RenderResult-Feld `lieferstatus` (ebenfalls
  // .default('geliefert')), damit die Zusicherung nicht an einem einzigen
  // Vertrag haengt.
  it('C (Zwilling) — lieferstatus (RenderResult, .default("geliefert")) ist ebenfalls KEIN Befund', () => {
    const roh = {
      job_id: 'vis-1757000000-a1b2c3',
      images: ['renders/cam-01.png'],
      qa: { verdict: { passed: true } },
      // lieferstatus bewusst WEGGELASSEN.
    };
    const geprueft = RenderResult.parse(roh);
    expect(geprueft.lieferstatus).toBe('geliefert');
    expect(unbekannteFelder(roh, geprueft)).toEqual([]);
  });

  // Zusicherung E: Gegenprobe, dass die Messung ueberhaupt beissen kann —
  // derselbe Aufruf ohne Fremdfeld meldet nichts. Ohne diese Zeile beweist B
  // nichts (E76-Auftrag, Abschnitt «Die Zusicherungen»).
  it('E — Gegenprobe zu B: derselbe Job ohne das Fremdfeld meldet nichts', () => {
    const roh = {
      job_id: 'vis-1757000000-a1b2c3',
      status: 'done',
      scene: '/tmp/kosmo-jobs/vis-1757000000-a1b2c3/render-scene.json',
      created_at: '2026-09-19T10:00:00Z',
      result: {
        job_id: 'vis-1757000000-a1b2c3',
        images: ['renders/cam-01.png'],
        qa: {
          geometry: { passed: true },
          verdict: { passed: true },
        },
        qa_je_kamera: [{ kamera: 'Uebersicht', geometry: { passed: true } }],
      },
    };
    const geprueft = RenderJob.parse(roh);
    expect(unbekannteFelder(roh, geprueft)).toEqual([]);
  });
});
