/**
 * Bitte des UI-Workers «Modus-Marke» (21.10.2026, Blatt «Ohne Grundlagenbild / Anders gerechnet»;
 * Vertrag C17 A1). Wie das KI-Bild entstand — bestellt gegen gerechnet — fuer den Lauf
 * (`NodeLauf.modus`), gelesen aus dem ERGEBNIS wie `NodeLauf.guete`. Die Marke baut der UI-Worker
 * (`ModusMarke`); diese Datei liefert nur die Angabe.
 *
 * Zwei Quellen, in dieser Reihenfolge:
 *  1. `angewandt.modus {bestellt, gerechnet, abweichung, kameras}` (C17 A1). «Nicht gemeldet» ist
 *     `null`, nie `false` — `null` heisst UNBEKANNT, nicht «wie bestellt».
 *  2. Der Satz in `qa.verdict.hinweise`, der mit «KI-BILD OHNE GRUNDLAGENBILD» beginnt (Visbox-Kern
 *     `kosmo_szene.SATZ_OHNE_GRUNDLAGENBILD`, auf-20261021-312 B3). Er nennt die Kamera als
 *     `Kamera '<name>'`. Fehlt A1, aber der Satz steht da, gilt
 *     `{bestellt: null, gerechnet: null, abweichung: true, satz}` — das Bild IST anders gerechnet,
 *     nur die Werte meldet das Ergebnis nicht.
 * Ohne beides: kein Feld (`undefined`).
 *
 * Gelesen ohne den Vertragstyp (wie `gueteAusErgebnis`), damit ein unbekannter Wert nie als
 * Angabe gilt.
 */

/** Je Kamera: was gerechnet wurde, ob es abwich, und der Satz dazu, wenn es einen gibt. */
export interface LaufModusKamera {
  gerechnet: string | null;
  abweichung: boolean | null;
  satz?: string;
}

/** `NodeLauf.modus` — die Form, die die Modus-Marke liest. */
export interface LaufModus {
  bestellt: string | null;
  gerechnet: string | null;
  /** `true` sobald eine Kamera abwich; `null` = nicht gemeldet (nie wie `false` zeigen). */
  abweichung: boolean | null;
  /** Die Saetze «KI-BILD OHNE GRUNDLAGENBILD …» aus `qa.verdict.hinweise`, mit Leerzeichen verbunden. */
  satz?: string;
  kameras?: Record<string, LaufModusKamera>;
}

/** Der Anfang des Satzes — wortgleich mit dem Visbox-Kern (`SATZ_OHNE_GRUNDLAGENBILD`). */
export const SATZ_OHNE_GRUNDLAGENBILD = 'KI-BILD OHNE GRUNDLAGENBILD';

const KAMERA_IM_SATZ = /Kamera (?:'([^']+)'|"([^"]+)")/;

function obj(v: unknown): Record<string, unknown> | undefined {
  return typeof v === 'object' && v !== null && !Array.isArray(v) ? (v as Record<string, unknown>) : undefined;
}
const textOderNull = (v: unknown): string | null => (typeof v === 'string' ? v : null);
const jaNeinOderNull = (v: unknown): boolean | null => (typeof v === 'boolean' ? v : null);

/** Die Saetze «KI-BILD OHNE GRUNDLAGENBILD …» aus `qa.verdict.hinweise`. */
export function modusSaetze(r: unknown): string[] {
  const hinweise = obj(obj(obj(r)?.qa)?.verdict)?.hinweise;
  if (!Array.isArray(hinweise)) return [];
  return hinweise.filter((h): h is string => typeof h === 'string' && h.startsWith(SATZ_OHNE_GRUNDLAGENBILD));
}

/** Die Kamera, die ein Satz nennt (`Kamera 'sSE'`), sonst `undefined`. */
export function kameraImSatz(satz: string): string | undefined {
  const m = KAMERA_IM_SATZ.exec(satz);
  return m ? (m[1] ?? m[2]) : undefined;
}

/** `NodeLauf.modus` aus einem Ergebnis — oder `undefined`, wenn es nichts dazu sagt. */
export function modusAusErgebnis(r: unknown): LaufModus | undefined {
  const saetze = modusSaetze(r);
  const satzJeKamera = new Map<string, string>();
  for (const s of saetze) {
    const k = kameraImSatz(s);
    if (k !== undefined && !satzJeKamera.has(k)) satzJeKamera.set(k, s);
  }
  const satz = saetze.length > 0 ? saetze.join(' ') : undefined;

  const a1 = obj(obj(obj(r)?.angewandt)?.modus);
  if (a1) {
    const modus: LaufModus = {
      bestellt: textOderNull(a1.bestellt),
      gerechnet: textOderNull(a1.gerechnet),
      abweichung: jaNeinOderNull(a1.abweichung),
      ...(satz !== undefined ? { satz } : {}),
    };
    const kam = obj(a1.kameras);
    if (kam) {
      const kameras: Record<string, LaufModusKamera> = {};
      for (const [name, roh] of Object.entries(kam)) {
        const k = obj(roh);
        if (!k) continue;
        const eigen = typeof k.satz === 'string' ? k.satz : satzJeKamera.get(name);
        kameras[name] = {
          gerechnet: textOderNull(k.gerechnet),
          abweichung: jaNeinOderNull(k.abweichung),
          ...(eigen !== undefined ? { satz: eigen } : {}),
        };
      }
      if (Object.keys(kameras).length > 0) modus.kameras = kameras;
    }
    return modus;
  }

  if (satz === undefined) return undefined;
  // Nur der Satz: das Bild ist anders gerechnet, die Werte meldet das Ergebnis nicht.
  const modus: LaufModus = { bestellt: null, gerechnet: null, abweichung: true, satz };
  // Je Kamera: die im Satz genannten weichen ab; die uebrigen Kameras des Ergebnisses
  // (`qa_je_kamera[].kamera`) sind NICHT GEMELDET (`null`), nicht «wie bestellt» — so zaehlt die
  // Zusatzzeile der Marke («1 von 2 Kameras …») gegen alle Kameras, nicht nur gegen die genannten.
  if (satzJeKamera.size > 0) {
    const kameras: Record<string, LaufModusKamera> = {};
    const jeKamera = obj(r)?.qa_je_kamera;
    for (const e of Array.isArray(jeKamera) ? jeKamera : []) {
      const name = obj(e)?.kamera;
      if (typeof name === 'string' && !satzJeKamera.has(name)) kameras[name] = { gerechnet: null, abweichung: null };
    }
    for (const [name, s] of satzJeKamera) kameras[name] = { gerechnet: null, abweichung: true, satz: s };
    modus.kameras = kameras;
  }
  return modus;
}
