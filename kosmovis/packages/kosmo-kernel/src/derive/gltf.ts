/**
 * STELLVERTRETER für `packages/kosmo-kernel/src/derive/gltf.ts` (KosmoOrbit, 2 200 Zeilen).
 *
 * Warum ein Stellvertreter (E26, 24.09.2026): Das Original baut die glb aus dem
 * Bauwerksmodell von KosmoOrbit (`deriveAll`, Wände, Decken, Fenster …) und zieht damit den
 * halben Architekturkern nach. In Visbox gibt es dieses Modell nicht — das Gebäude kommt
 * als fertige glb aus der Mappe. Darum liefert `exportGlb` hier die glb, die der Gastgeber
 * mit `setzeModellGlb` hinterlegt hat.
 *
 * `pruefeGlasnaht` (mit `GlasnahtBefund` und der Konstante davor) ist WÖRTLICH aus dem
 * Original übernommen — eine reine Leseprüfung der glb ohne weitere Abhängigkeit.
 *
 * Bei der Rückkehr nach KosmoOrbit fällt diese Datei weg; das Original gilt wieder.
 */
import type { KosmoDoc } from '../model/doc';

const DURCHLASS_ERWEITERUNG = 'KHR_materials_transmission';

let modellGlb: ArrayBuffer | null = null;

/** Visbox: Der Gastgeber legt hier die glb der offenen Mappe ab. `null` räumt sie. */
export function setzeModellGlb(glb: ArrayBuffer | null): void {
  modellGlb = glb;
}

/** Visbox: Liegt eine glb bereit? */
export function modellGlbBereit(): boolean {
  return modellGlb !== null;
}

export interface AusfuhrWahl {
  /** Bildkarten einbetten — in Visbox ohne Wirkung: die glb kommt fertig aus der Mappe. */
  mitTexturen?: boolean;
}

export function exportGlb(
  _doc: KosmoDoc, _name = 'KosmoOrbit-Modell', _wahl: AusfuhrWahl = {},
): ArrayBuffer {
  if (!modellGlb) {
    throw new Error(
      'Kein Modell geladen: In Visbox kommt das Gebäude aus der offenen Mappe. ' +
      'Öffne zuerst eine Mappe mit Modell.',
    );
  }
  return modellGlb.slice(0);
}

/**
 * P-GLASNAHT — DER RIEGEL, DER AN DER AUSGEFÜHRTEN DATEI MISST.
 *
 * WARUM ES IHN GIBT. Am 02.09.2026 wurde gemessen, dass die Kette ihren
 * Modellstand an einer Datei prüfte, die zwar die richtige war, über die sie
 * aber nichts sagen konnte: die ausgeführte glb trug keinen Herkunftsvermerk,
 * das Urteil lautete «ungeprueft» — kein Bestehen, aber eben auch kein
 * Befund. Und die naheliegende Reparatur (einfach stempeln) wurde
 * NACHGESTELLT und verworfen: dieselbe glasfreie Datei, nur gestempelt, kam
 * als «traegt / bestanden» zurück, weil das einzige vorhandene Merkmal
 * «n_materialien > 0» lautet und drei Materialien vorhanden waren. Eine
 * Probe, die am vorliegenden Defekt nicht rot werden kann, ist keine Probe.
 *
 * DIESE HIER KANN ROT WERDEN, und zwar an genau dem Defekt: Trägt die Quelle
 * `IfcWindow`, muss die Ausfuhr mindestens ein Material führen, das Licht
 * durchlässt — `alphaMode: BLEND` ODER seit V7 einen Durchlassblock
 * (`KHR_materials_transmission` mit Faktor > 0). An der ausgeführten glb des
 * Demolaufs vom 02.09.2026 (700 IfcWindow, 3 Materialien, ausnahmslos
 * OPAQUE, keine Erweiterung) schlägt sie an — beide Zahlen sind dort 0.
 *
 * SIE MISST DIE DATEI, NICHT DIE ABSICHT. Eingabe ist der fertige
 * glb-Puffer, nicht das Dokument — genau deshalb, weil die drei stillen
 * Demoläufe zeigten, dass zwischen «das Dokument hat Fenster» und «die
 * gefahrene Datei zeigt Glas» vier Stellen lagen, an denen es verlorenging.
 *
 * SIE MELDET, SIE BRICHT NICHT AB — dieselbe Linie wie der Massstabs- und
 * der Modellstands-Befund auf der Bildseite, und aus demselben Grund: Wie
 * oft dieser Riegel an echten Projekten anschlägt, ist ungemessen. Ein
 * Riegel, der scharfgestellt wird, bevor seine Fehlalarmrate bekannt ist,
 * lehnt Aufträge ab, und niemand weiss welche. Wer ihn zum Abbruch machen
 * will, hat dann Zahlen dafür.
 */
export interface GlasnahtBefund {
  /** 'zurueck' = benannter Mangel · 'ungeprueft' = nicht entscheidbar (KEIN
   *  Bestehen) · 'traegt' = die Datei zeigt, was die Quelle hergibt. */
  urteil: 'traegt' | 'zurueck' | 'ungeprueft';
  grund: string;
  gemessen: {
    nMaterialien: number;
    nBlend: number;
    /**
     * V7 «Materialweg»: Materialien mit `KHR_materials_transmission`.
     *
     * DIESE ZAHL ERWEITERT DAS URTEIL, SIE SCHWÄCHT ES NICHT. Rot ist der
     * Riegel jetzt, wenn die Ausfuhr WEDER Alpha-Mischung NOCH Durchlass
     * führt — an der gemessenen Demolauf-Datei (700 IfcWindow, 3 Materialien,
     * ausnahmslos OPAQUE, keine Erweiterung) sind beide Zahlen 0, sie schlägt
     * also unverändert an. Ohne diese Ergänzung wäre der Riegel genau dann
     * falsch rot geworden, wenn jemand das Glas sauber auf
     * `alphaMode: OPAQUE` + Durchlass umstellt — also beim nächsten richtigen
     * Schritt (s. `materialFor`, «WARUM DANN NICHT GLEICH OPAQUE»).
     */
    nDurchlass: number;
    ifcFenster: number | null;
  };
}

export function pruefeGlasnaht(glb: ArrayBuffer): GlasnahtBefund {
  let js: Record<string, unknown>;
  try {
    const dv = new DataView(glb);
    const jsonLen = dv.getUint32(12, true);
    js = JSON.parse(new TextDecoder().decode(new Uint8Array(glb, 20, jsonLen)));
  } catch {
    // Unlesbar ist ein Befund über die DATEI, keiner über die Glasnaht — darf
    // aber nicht als bestanden durchgehen, sonst wäre «kaputt» der bequemste
    // Weg an der Prüfung vorbei.
    return {
      urteil: 'ungeprueft',
      grund: 'Die Datei ist keine lesbare glb. Das ist kein Bestehen.',
      gemessen: { nMaterialien: 0, nBlend: 0, nDurchlass: 0, ifcFenster: null },
    };
  }
  const materialien =
    (js['materials'] as { alphaMode?: string; extensions?: Record<string, unknown> }[] | undefined) ?? [];
  const nBlend = materialien.filter((m) => m.alphaMode === 'BLEND').length;
  // Gezählt wird der BLOCK, nicht sein Wert: `transmissionFactor` darf per
  // Vorgabe fehlen (dann gilt 0). Ein Material mit leerem Block ist also
  // KEINE durchlässige Scheibe — darum die Prüfung auf eine Zahl > 0.
  const nDurchlass = materialien.filter((m) => {
    const block = m.extensions?.[DURCHLASS_ERWEITERUNG] as { transmissionFactor?: unknown } | undefined;
    return typeof block?.transmissionFactor === 'number' && block.transmissionFactor > 0;
  }).length;
  const asset = (js['asset'] as Record<string, unknown> | undefined) ?? {};
  const extras = (asset['extras'] as Record<string, unknown> | undefined) ?? {};
  const vermerk = extras['kosmo_modellstand'] as Record<string, unknown> | undefined;
  const traegt = (vermerk?.['traegt'] as Record<string, unknown> | undefined) ?? {};
  const klassen = traegt['ifc_klassen'] as Record<string, number> | undefined;
  const fenster = klassen && typeof klassen['IfcWindow'] === 'number' ? klassen['IfcWindow'] : null;
  const gemessen = { nMaterialien: materialien.length, nBlend, nDurchlass, ifcFenster: fenster };

  if (fenster === null) {
    return {
      urteil: 'ungeprueft',
      grund:
        'Die Datei sagt nicht, wie viele Fenster ihre Quelle trug (kein Herkunftsvermerk ' +
        'oder keine Klassenzählung darin). Ob eine fehlende Scheibe ein Mangel ist, ist ' +
        'damit nicht entscheidbar — und das zählt NICHT als bestanden.',
      gemessen,
    };
  }
  if (fenster > 0 && nBlend === 0 && nDurchlass === 0) {
    return {
      urteil: 'zurueck',
      grund:
        `Die Quelle trug ${fenster} Fenster, die Ausfuhr führt ${materialien.length} Material(ien) ` +
        'und darunter KEINES mit `alphaMode: BLEND` und KEINES mit Durchlass ' +
        '(`KHR_materials_transmission`). Im Bild ist dann jede Scheibe deckend — ' +
        'genau der Befund, der drei Demoläufen am 01./02.09.2026 unbemerkt geblieben ist.',
      gemessen,
    };
  }
  return {
    urteil: 'traegt',
    grund:
      fenster === 0
        ? 'Die Quelle trug keine Fenster; eine fehlende Scheibe ist hier kein Mangel.'
        : `${fenster} Fenster in der Quelle, ${nBlend} durchsichtige(s) und ${nDurchlass} ` +
          'lichtdurchlässige(s) Material(ien) in der Ausfuhr.',
    gemessen,
  };
}
