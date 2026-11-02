/**
 * A0061 (Owner-Entscheid «Immer vom Render», 31.10.2026): jedes KI-Bild, das KosmoOrbit bestellt, startet vom
 * Beauty-Render derselben Kamera; Geometrie-Paesse allein (Tiefe, Kanten, Normalen) reichen nicht. Er schaerft den
 * Masstreue-Entscheid vom 30.10. (A0049, `freies-bild.ts`).
 *
 * Darum sind zwei Wahlen nicht mehr bestellbar: die Guete «Vorschau» (sie rechnet ohne das Grundbild als
 * Bildeingang, `GUETE_TEXTE.vorschau`) und jedes Bildwerkzeug ohne belegten Beauty-Eingang
 * (`BILDWERKZEUG_BEAUTY_EINGANG`, heute belegt nur Z-Image Turbo). Die Sperre sitzt im Kern (`vis.render`,
 * `vis.varianten`, Wahl am Knoten); dieses Modul ist die zweite Naht (Versand, Werkzeugsatz der Knotenansicht,
 * Knoten-Wähler) und fuehrt dieselben Saetze. Reine Logik, ohne React, ohne App-Verdrahtung (Kopie in die Visbox).
 */
import {
  BILDWERKZEUG_BEAUTY_EINGANG,
  VORSCHAU_ABSAGE,
  bildwerkzeugAbsage,
  bildwerkzeugVomRender,
  vomRenderAbsage,
} from '@kosmo/kernel';

export { BILDWERKZEUG_BEAUTY_EINGANG, VORSCHAU_ABSAGE, bildwerkzeugAbsage, bildwerkzeugVomRender, vomRenderAbsage };

/** Die kurze Marke am Wähler fuer ein gesperrtes Bildwerkzeug. */
export const BILDWERKZEUG_GESPERRT_MARKE = 'gesperrt bis Messung';

const BESTELL_BEFEHLE: ReadonlySet<string> = new Set(['vis.render']);
const PARAM_BEFEHLE: ReadonlySet<string> = new Set(['vis.nodeParametrieren', 'vis.nodeSetzen']);

/**
 * Verlangt dieser Befehl einen Weg ohne Beauty-Render? `vis.render` mit `guete: 'vorschau'` oder einem gesperrten
 * `backbone`, oder dieselbe Wahl als Knoten-Parameter (`vis.nodeParametrieren`, `vis.nodeSetzen`). Die Absage, sonst
 * `null`. Eine alte Wahl am Knoten prueft der Kern (er kennt das Dokument) und der Versand.
 */
export function vomRenderAbsageFuerBefehl(commandId: string, params: unknown): string | null {
  if (typeof params !== 'object' || params === null) return null;
  const p = params as { guete?: unknown; backbone?: unknown; params?: unknown };
  if (BESTELL_BEFEHLE.has(commandId)) return vomRenderAbsage(p);
  if (PARAM_BEFEHLE.has(commandId) && typeof p.params === 'object' && p.params !== null) {
    return vomRenderAbsage(p.params as { guete?: unknown; backbone?: unknown });
  }
  return null;
}
