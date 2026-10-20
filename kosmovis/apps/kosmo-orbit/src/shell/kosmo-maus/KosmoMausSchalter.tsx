/**
 * STELLVERTRETER (Visbox) (Kopfteile S2, Entscheide 115/116, 20.10.2026) fuer
 * `shell/kosmo-maus/KosmoMausSchalter.tsx` von KosmoOrbit.
 *
 * Die KosmoMaus — Claude klickt mit eigenem Zeiger — gibt es in Visbox nicht: Claude bedient die
 * Knotenansicht nur ueber Werkzeuge (Ausnahme «Maus-Ebene», `kosmovis/UI_AUSNAHMEN.json`). Was die
 * woertlichen Teile hier lesen, steht darum so:
 *
 *  - `eigen` und `bedienWechselKurz` — wortgleich (die Sperrzone der KosmoMaus als Attribut, die
 *    Kurzform eines Bedien-Wechsels; in Visbox wechselt «Bedienen» nie);
 *  - `KosmoMausFreigabeSchalter` — die Schalter «Mitschauen»/«Bedienen» zeichnet Visbox nicht. An der
 *    Marke steht stattdessen die Selbständigkeit, die der Wirt hereinreicht (`ausklapper` an
 * `ClaudeAnschluss`, `apps/visbox-knoten/src/kopf.tsx`). Ein Schalter hier waere
 *    ein Knopf ohne Wirkung — darum zeichnet er nichts.
 */
import type { BedienGrund, BedienWechsel } from '../../state/kosmo-maus-freigabe';
import './kosmo-maus.css';

/** Wie `EIGENE_EBENE_ATTR` dort (`state/kosmo-blick-live.ts`). */
const EIGENE_EBENE_ATTR = 'data-kosmo-maus-eigen';

export const eigen = (): Record<string, string> => ({ [EIGENE_EBENE_ATTR]: '' });

const BEDIEN_GRUND_KURZ: Record<BedienGrund, string> = {
  schalter: 'Schalter',
  esc: 'Esc',
  stopp: '«Stopp»',
  'alle-anhalten': '«Alle anhalten»',
  'anderes-fenster': 'anderes Fenster',
  agent: 'Agent selbst',
};

function uhrzeit(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleTimeString('de-CH', { hour: '2-digit', minute: '2-digit' });
}

/** Wortgleich wie dort. */
export function bedienWechselKurz(w: BedienWechsel | null, an: boolean): string | null {
  if (!w || w.an !== an) return null;
  const zeit = uhrzeit(w.zeit);
  return `${an ? 'an' : 'aus'} — ${BEDIEN_GRUND_KURZ[w.grund]}${zeit ? `, ${zeit}` : ''}`;
}

/** In Visbox ohne KosmoMaus: zeichnet nichts (s. Kopf). */
export function KosmoMausFreigabeSchalter(_props: { vorsatz: 'kosmo-maus' | 'kosmo-einstellungen' }) {
  return null;
}
