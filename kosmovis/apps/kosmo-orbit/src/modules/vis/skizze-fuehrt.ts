/**
 * DIE SKIZZE FUEHRT DAS BILD — der Satz am Render-Knoten (Owner-Entscheid 96 der Visbox, 15.10.2026).
 *
 * Hängt eine «Skizze vom iPad» am Eingang «Skizze», geht sie als Eingangsbild in die Bestellung
 * (`RenderScene.skizze`), und die Bildseite rechnet sie wie «aus Skizze rechnen» auf der Visbox-Seite.
 * Ob sie beim Bildmodell ANKOMMT, hängt am Modell — und das ist gemessen, nicht vermutet:
 *
 * - **Z-Image Turbo** (Vorgabe): kommt NICHT an. Die Pipeline hat keinen Bildeingang; das Bild
 *   entsteht aus Tiefenkarte und Text (Visbox `auf-20260919-123`, sieben Läufe, eine Prüfsumme).
 * - **Qwen-Image-Edit** (`qwen`, 2511): kommt NICHT an. Die Pipeline hat genau einen Bildeingang,
 *   und den bekommt die Tiefenkarte (Visbox `auf-20260818-09`).
 * - **Qwen-Image 2.1, SDXL, FLUX.2 [klein], FLUX.1-Krea**: UNGEMESSEN — weder ja noch nein.
 *
 * Darum sagt der Knoten, welches Modell rechnet und was darüber bekannt ist. Ein Modell, auf dem
 * die Skizze gemessen ankommt, gibt es am 15.10.2026 noch nicht; die Bildseite rechnet trotzdem
 * und schreibt den Satz «SKIZZE NICHT ANGEKOMMEN» ans Ergebnis (Visbox
 * `kette.HINWEIS_SKIZZE_NICHT_ANGEKOMMEN`). Das Modell wird NIE von selbst umgestellt: Qwen-Image
 * 2.1 hat eine offene Lizenz (E128) und ist nie Vorgabe.
 */
import { BILDWERKZEUG_TEXTE, type Bildwerkzeug } from './vis-jobs';
import { skizzenName, skizzenStand, waehleSkizze } from './skizze-quelle';

/** Was über das Ankommen der Skizze auf einem Bildwerkzeug bekannt ist — mit Beleg. */
export const SKIZZE_KOMMT_AN: Record<Bildwerkzeug, { readonly lage: 'nein' | 'ungemessen'; readonly beleg?: string }> = {
  'z-image-turbo': { lage: 'nein', beleg: 'auf-20260919-123' },
  qwen: { lage: 'nein', beleg: 'auf-20260818-09' },
  'qwen-image-2.1': { lage: 'ungemessen' },
  sdxl: { lage: 'ungemessen' },
  'flux2-klein': { lage: 'ungemessen' },
  'flux-krea': { lage: 'ungemessen' },
};

/** Ohne Skizze am Eingang (nur mit Wirt sichtbar). */
export const SKIZZE_KEINE_ZEILE = 'Ohne Skizze: das Bild entsteht aus dem Modell.';

/** Mit Skizze und Kamera-Standpunkten am Knoten — die gelten dann nicht. */
export const SKIZZE_KAMERAS_SATZ =
  'Die Kamera-Standpunkte gelten mit einer Skizze nicht: es entsteht EIN Bild vom Standpunkt der Mappe.';

/** Mit Skizze und «nur Cycles»/«Strichzeichnung» — der Vertrag weist das ab. */
export const SKIZZE_OHNE_KI_ZEILE = 'Skizze geht nicht mit «nur Cycles» oder «Strichzeichnung» — abschalten.';

export interface SkizzeFuehrtZeile {
  /** Die kurze Zeile im Knoten (höchstens drei Zeilen breit). */
  zeile: string;
  /** Der volle Satz (am `title`). */
  satz: string;
  /** Warnfarbe: die Skizze kommt so nicht an, oder die Bestellung wird abgewiesen. */
  warnung: boolean;
}

/**
 * Die Zeile «Skizze» am Render-Knoten.
 *
 * @param skizze die Wahl am Skizzen-Knoten (`VisRenderAuftrag.skizze`), oder `undefined`
 * @param backbone das gewählte Bildwerkzeug; `undefined` heisst die Vorgabe Z-Image Turbo
 */
export function skizzeFuehrtZeile(opts: {
  skizze: { wahl: string } | undefined;
  backbone: Bildwerkzeug | undefined;
  ohneKi: boolean;
  mitKameras: boolean;
}): SkizzeFuehrtZeile {
  if (!opts.skizze) return { zeile: SKIZZE_KEINE_ZEILE, satz: SKIZZE_KEINE_ZEILE, warnung: false };
  if (opts.ohneKi) return { zeile: SKIZZE_OHNE_KI_ZEILE, satz: SKIZZE_OHNE_KI_ZEILE, warnung: true };
  const werkzeug: Bildwerkzeug = opts.backbone ?? 'z-image-turbo';
  const name = BILDWERKZEUG_TEXTE[werkzeug].name;
  const gewaehlt = waehleSkizze(skizzenStand().liste, opts.skizze.wahl);
  const welche = gewaehlt ? `«${skizzenName(gewaehlt)}»` : 'die gewählte Skizze';
  const ankunft = SKIZZE_KOMMT_AN[werkzeug];
  const zeile =
    ankunft.lage === 'nein'
      ? `Skizze führt · ${name}: darauf kommt sie gemessen nicht an.`
      : `Skizze führt · ${name}: ob sie ankommt, ist ungemessen.`;
  const satz = [
    `${welche} führt das Bild; gerechnet wird mit ${name}.`,
    ankunft.lage === 'nein'
      ? `Auf diesem Modell kommt die Skizze gemessen nicht an (${ankunft.beleg}) — das Bild entsteht aus Tiefenkarte und Text, und am Ergebnis steht «SKIZZE NICHT ANGEKOMMEN». Ein anderes Bildwerkzeug wählen; ein Modell, auf dem sie gemessen ankommt, gibt es noch nicht.`
      : 'Ob die Skizze auf diesem Modell ankommt, ist noch nicht gemessen.',
    ...(opts.mitKameras ? [SKIZZE_KAMERAS_SATZ] : []),
  ].join(' ');
  return { zeile, satz, warnung: ankunft.lage === 'nein' };
}
