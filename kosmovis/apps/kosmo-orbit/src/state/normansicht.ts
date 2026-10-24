/**
 * Normansicht (Owner-Entscheid E157, «Normansichten ausblenden»): eigene,
 * winzige Datei ohne Abhängigkeiten, damit Ansichten wie `DataWorkspace.tsx`
 * die Marke setzen können, ohne den ganzen KosmoBlick zu laden.
 */

/**
 * Was als Normansicht gilt (geprüft am 06.10.2026 im Code, je mit Fundstelle):
 *
 *  - `[data-normansicht]` — die allgemeine Marke. Gesetzt an den Stellen, die
 *    Normtext-Wortlaut zeigen:
 *      · Wissenstreffer in KosmoData (`modules/data/DataWorkspace.tsx`,
 *        `wissen-hit`, bis 220 Zeichen Chunk-Text),
 *      · Wissenstreffer in der Insel «Wissen» (`modules/prepare/island/
 *        inhalte/wissen.tsx`, `island-knowledge-hit`, bis 160 Zeichen),
 *    jeweils nur, wenn der Treffer aus dem SIA-Normenwerk stammt
 *    (`istNormTreffer`). Neue Ansichten mit Normtext setzen dieselbe Marke.
 *  - `.prtafel-karte[data-art="norm"]` — Tafelkarten in KosmoPrepare, die die
 *    Erkennung als Norm einordnet (`modules/prepare/tafel/tafel-logik.ts`,
 *    `erkenneArt`, Herkunft `normen-sia` oder Merkmale im Namen/Text). Ihre
 *    Vorschau zeigt die erste PDF-Seite bzw. den Textanfang.
 *    NICHT darunter faellt `data-art="recht"` (Owner-Entscheid 21.10.2026,
 *    Wahl A): Gesetze, Verordnungen, BZO und Reglemente sind oeffentliches
 *    Recht, Claude darf sie lesen und daraus zitieren. Wohin ein Dokument
 *    kommt, entscheidet `erkenneArt` — im Zweifel `norm`
 *    (`tafel-logik.ts#imZweifelNorm`).
 *
 * Keine Normansicht, weil dort nur Namen und Zahlen stehen: die Listen
 * «SIA-Normenwerk geladen» (`prepare-sections.tsx`, Normnamen und Abschnitts-
 * zahlen), die Quellen-Chips im Kosmo-Chat (zeigen die Marke [Qn]; der
 * Auszug steht nur im `title`, und den liest der Blick nicht).
 */
export const NORMANSICHT_SELEKTOR = '[data-normansicht], .prtafel-karte[data-art="norm"]';

/** Stammt ein Wissenstreffer aus dem SIA-Normenwerk? (`knowledge.ts`: `normNummer`, Doc-Id `normenwerk-…`) */
export function istNormTreffer(h: { docId?: string; normNummer?: string }): boolean {
  return Boolean(h.normNummer) || (h.docId ?? '').startsWith('normenwerk-');
}

