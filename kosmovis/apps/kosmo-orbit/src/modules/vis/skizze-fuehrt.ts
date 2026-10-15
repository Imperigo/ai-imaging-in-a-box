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
 *
 * **Folgeentscheide (Owner, 15.10.2026):** 96a — die ANWEISUNG ist die Bemerkung der Skizze; die
 * Stimmung tritt zurück (sie wird nicht als Anweisung gesendet), und ohne Bemerkung steht VOR dem
 * Klick da, dass nichts gesendet wird (`skizzeAnweisung`). 96b — das Bild entsteht vom STANDPUNKT
 * DES BILDES, auf das gezeichnet wurde; ohne Unterlage, oder wenn ihr Standpunkt nicht bekannt
 * ist, vom Standpunkt der Mappe (`skizzenStandpunkt`, die Bibliothek der Visbox entscheidet).
 */
import { BILDWERKZEUG_TEXTE, type Bildwerkzeug } from './vis-jobs';
import {
  SKIZZE_OHNE_BEMERKUNG_SATZ,
  skizzeHatBemerkung,
  skizzenName,
  skizzenStand,
  waehleSkizze,
  type Skizze,
} from './skizze-quelle';

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

/**
 * Entscheid 96b (Owner, 15.10.2026): das Bild aus einer Skizze entsteht vom Standpunkt des Bildes,
 * auf das gezeichnet wurde — die Bibliothek der Visbox nimmt dessen Kamera
 * (`projekt.standpunkt_fuer_skizze`). Ohne Unterlage, oder wenn von ihr nicht bekannt ist, von
 * wo sie gerechnet wurde, bleibt es beim Standpunkt der Mappe, und das steht am Ergebnis.
 */
export const SKIZZE_STANDPUNKT_BILD = 'Standpunkt: vom Bild unter der Skizze.';
/** 96b: keine Unterlage. */
export const SKIZZE_STANDPUNKT_OHNE_BILD = 'Standpunkt der Mappe — die Skizze ist auf kein Bild gezeichnet.';
/** 96b: eine Unterlage, deren Standpunkt nicht bekannt ist (ein Bild von vor dem 15.10.2026). */
export const SKIZZE_STANDPUNKT_UNBEKANNT = 'Standpunkt der Mappe — vom Bild unter der Skizze ist er nicht bekannt.';

/** Mit Skizze und Kamera-Standpunkten am Knoten — die gelten dann nicht. */
export const SKIZZE_KAMERAS_SATZ =
  'Die Kamera-Standpunkte gelten mit einer Skizze nicht: es entsteht EIN Bild, vom Standpunkt des Bildes unter der Skizze (sonst dem der Mappe).';

/** Mit Skizze und «nur Cycles»/«Strichzeichnung» — der Vertrag weist das ab. */
export const SKIZZE_OHNE_KI_ZEILE = 'Skizze geht nicht mit «nur Cycles» oder «Strichzeichnung» — abschalten.';

/** 96a: warum ohne Bemerkung nichts gesendet wird. */
export const SKIZZE_BEMERKUNG_GRUND =
  'Mit einer Skizze gilt ihre Bemerkung als Anweisung — die Stimmung tritt zurück. Ohne Bemerkung würde die Bildseite abweisen; darum wird nichts gesendet.';

/** 96b: von wo das Bild aus dieser Skizze entsteht — wie es die Bibliothek meldet, sonst aus `ueber`. */
export function skizzenStandpunkt(s: Skizze | null): string {
  if (!s) return SKIZZE_STANDPUNKT_BILD;
  const art = s.standpunkt ?? (s.ueber ? 'bild' : 'mappe');
  if (art === 'bild') return SKIZZE_STANDPUNKT_BILD;
  return s.ueber ? SKIZZE_STANDPUNKT_UNBEKANNT : SKIZZE_STANDPUNKT_OHNE_BILD;
}

export interface SkizzeFuehrtZeile {
  /** Die kurze Zeile im Knoten (höchstens vier Zeilen breit). */
  zeile: string;
  /** Der volle Satz (in der Kurzhilfe). */
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
  const gewaehlt = waehleSkizze(skizzenStand().liste, opts.skizze.wahl);
  // Entscheid 96a: ohne Bemerkung wird nichts gesendet — das steht VOR dem Klick da.
  if (gewaehlt && skizzeHatBemerkung(gewaehlt) === false) {
    return { zeile: SKIZZE_OHNE_BEMERKUNG_SATZ, satz: `${SKIZZE_OHNE_BEMERKUNG_SATZ} ${SKIZZE_BEMERKUNG_GRUND}`, warnung: true };
  }
  const werkzeug: Bildwerkzeug = opts.backbone ?? 'z-image-turbo';
  const name = BILDWERKZEUG_TEXTE[werkzeug].name;
  const welche = gewaehlt ? `«${skizzenName(gewaehlt)}»` : 'die gewählte Skizze';
  const ankunft = SKIZZE_KOMMT_AN[werkzeug];
  const standpunkt = skizzenStandpunkt(gewaehlt);
  const zeile =
    (ankunft.lage === 'nein'
      ? `Skizze führt · ${name}: darauf kommt sie gemessen nicht an.`
      : `Skizze führt · ${name}: ob sie ankommt, ist ungemessen.`) + ` ${standpunkt}`;
  const satz = [
    `${welche} führt das Bild; gerechnet wird mit ${name}.`,
    ankunft.lage === 'nein'
      ? `Auf diesem Modell kommt die Skizze gemessen nicht an (${ankunft.beleg}) — das Bild entsteht aus Tiefenkarte und Text, und am Ergebnis steht «SKIZZE NICHT ANGEKOMMEN». Ein anderes Bildwerkzeug wählen; ein Modell, auf dem sie gemessen ankommt, gibt es noch nicht.`
      : 'Ob die Skizze auf diesem Modell ankommt, ist noch nicht gemessen.',
    standpunkt,
    'Anweisung ist die Bemerkung der Skizze; die Stimmung tritt zurück.',
    ...(opts.mitKameras ? [SKIZZE_KAMERAS_SATZ] : []),
  ].join(' ');
  return { zeile, satz, warnung: ankunft.lage === 'nein' };
}

export interface SkizzeAnweisung {
  /** Die Zeile «Prompt» des Render-Knotens, solange eine Skizze am Eingang hängt. */
  text: string;
  /** Der volle Satz (am `title` der Zeile). */
  titel: string;
  warnung: boolean;
}

/**
 * Entscheid 96a: die Prompt-Zeile des Render-Knotens, solange eine Skizze am Eingang hängt. Die
 * Anweisung ist die BEMERKUNG DER SKIZZE; ein Prompt aus Stimmung/Formular tritt zurück (er wird
 * nicht als Anweisung gesendet), und das steht da.
 */
export function skizzeAnweisung(wahl: string, prompt: string): SkizzeAnweisung {
  const gewaehlt = waehleSkizze(skizzenStand().liste, wahl);
  const zurueck = prompt.trim() ? ' — Stimmung tritt zurück' : '';
  const zurueckSatz = prompt.trim() ? ` Die Stimmung «${prompt.trim()}» tritt zurück und wird nicht gesendet.` : '';
  const hat = gewaehlt ? skizzeHatBemerkung(gewaehlt) : null;
  if (hat === false) {
    return { text: SKIZZE_OHNE_BEMERKUNG_SATZ, titel: `${SKIZZE_OHNE_BEMERKUNG_SATZ} ${SKIZZE_BEMERKUNG_GRUND}`, warnung: true };
  }
  if (hat === true && gewaehlt?.bemerkung) {
    const bemerkung = gewaehlt.bemerkung.trim();
    return {
      text: `Anweisung: Bemerkung der Skizze «${bemerkung}»${zurueck}`,
      titel: `Anweisung ist die Bemerkung der Skizze: «${bemerkung}».${zurueckSatz}`,
      warnung: false,
    };
  }
  return {
    text: `Anweisung: Bemerkung der Skizze${zurueck}`,
    titel: `Anweisung ist die Bemerkung, die beim Zeichnen an der Skizze stand.${zurueckSatz}`,
    warnung: false,
  };
}
