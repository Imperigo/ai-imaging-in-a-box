/**
 * «OHNE UMGEBUNG» AM RENDER-KNOTEN (Bitte des Integrators, Runde 29, 14.10.2026).
 *
 * Geht ein Splat nicht als Umgebung mit (etwa: aus dem Dateidialog ohne Pfad geladen), traegt
 * der Lauf `NodeLauf.umgebungFehlt` mit dem Grund. Der Render-Knoten zeigt dann, solange der
 * Lauf steht, eine Zeile «Ohne Umgebung: <Grund>». Fehlt das Feld, ging die Umgebung mit oder
 * es gab keinen Splat — keine Zeile.
 *
 * **Warum hier gelesen und nicht am Typ:** Das Feld kommt mit int-r29 in `NodeLauf`
 * (`vis-runtime.ts`); dieser Zweig baut auf `claude/kosmovis-modell-laden` auf, wo es noch
 * fehlt. Die Anzeige liest es darum duldsam — als Satz, als `{ grund }` oder als blosses
 * `true` — und faellt ohne Feld still weg. Steht es nach dem Einspielen am Typ, aendert sich
 * hier nichts.
 */
export function umgebungFehltSatz(lauf: unknown): string | null {
  if (!lauf || typeof lauf !== 'object') return null;
  const roh = (lauf as { umgebungFehlt?: unknown }).umgebungFehlt;
  if (typeof roh === 'string') return roh.trim() || 'Grund nicht genannt';
  if (roh === true) return 'Grund nicht genannt';
  if (roh && typeof roh === 'object') {
    const o = roh as { grund?: unknown; satz?: unknown };
    const text = typeof o.grund === 'string' ? o.grund : typeof o.satz === 'string' ? o.satz : '';
    return text.trim() || 'Grund nicht genannt';
  }
  return null;
}
