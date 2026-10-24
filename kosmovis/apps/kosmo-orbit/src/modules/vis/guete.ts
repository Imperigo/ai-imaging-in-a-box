/**
 * Entscheide 104/104a (Owner, 20.10.2026; Entwurfsflaeche Blatt 29 «Fortschritt und Vorschau») und
 * Entscheid 143 (Owner ueber die Zentrale, 24.10.2026, A).
 *
 * Am Render-Knoten waehlt der Schalter «Güte: Vorschau | Voll», wie der KI-Schritt einer Variante
 * rechnet. Die Vorschau ist schnell: z-image-turbo, ein Startwert, weniger Schritte und ein kleineres
 * KI-Bild, ohne das Grundbild als Bildeingang (so rechnet die Gegenseite eine Vorschau, egal welches
 * Bildwerkzeug am Knoten steht). Die Vorschau wird geprueft (104a) und traegt den Vermerk «Vorschau»
 * am Bild und im Verlauf — die Plakette baut der UI-Worker (`GueteMarke`); sie liest
 * `NodeLauf.guete`, also was das ERGEBNIS meldet (`result.guete`), nicht was bestellt war: eine
 * Gegenseite, die das Feld nicht kennt, rechnet voll, und dann steht auch kein Vermerk da.
 *
 * **Die Vorgabe je Bestellart (Entscheid 143).** Bis 143 galt ueberall Vorschau (104) — «Variante
 * erzeugen» bestellte darum ohne einen Klick die Vorschau, und die uebermalte am Testhaus ein
 * Fensterband (Visbox-Messung 346; voll mit Bildeingang 0,5 hielt es, Fenster 0,98). Seit 143
 * rechnen **Varianten** — «Variante erzeugen» am Render-Knoten und der Varianten-Knoten — mit der
 * Vorgabe **Voll** (vom Grundbild, Bildeingang 0,5 nach Entscheid 138). Die Vorschau bleibt
 * waehlbar; ausdruecklich gewaehlt bleibt sie Vorschau und traegt den Vorbehalt «Fenster und Form
 * nicht gesichert» (`GUETE_VORBEHALT`). Die Vorgabe des Render-Knotens (104, Vorschau) bleibt als
 * eigener Wert stehen (`GUETE_VORGABE`) — am Render-Knoten selbst bestellt heute nur «Variante
 * erzeugen» eine Guete, und das ist eine Variante; darum zeigt der Schalter dort Voll, solange
 * niemand Vorschau waehlt.
 *
 * Die Wahl ist ein flacher Parameter am Knoten (`vis.nodeParametrieren`) — sie ueberlebt ein
 * Neuladen und laesst sich zuruecknehmen. Fehlt er, gilt die Vorgabe der Bestellart. «Grundlage
 * rendern» hat keinen KI-Schritt (der Vertrag weist `vis.guete` mit `vis.skip` ab), und Kosmo und
 * die Insel bestellen wie bisher ohne Feld, also voll — ausser `vis.render` bestellt ausdruecklich
 * eine Guete.
 */

export type Guete = 'vorschau' | 'voll';

/** Der Parameter am Render-Knoten (und am Varianten-Knoten). */
export const GUETE_PARAM = 'guete';

/** Wofuer die Guete gilt: der Render-Knoten selbst (104) oder eine Variante (143). */
export type GueteArt = 'render' | 'variante';

/** Vorgabe des Render-Knotens (Entscheid 104) — unveraendert. */
export const GUETE_VORGABE: Guete = 'vorschau';

/** Vorgabe fuer Varianten (Entscheid 143): «Variante erzeugen» und der Varianten-Knoten. */
export const GUETE_VORGABE_VARIANTE: Guete = 'voll';

/** Die Vorgabe je Bestellart, an EINER Stelle. */
export const GUETE_VORGABE_JE_ART: Readonly<Record<GueteArt, Guete>> = {
  render: GUETE_VORGABE,
  variante: GUETE_VORGABE_VARIANTE,
};

/**
 * Die Wahl am Knoten fuer diese Bestellart: eine ausdrueckliche Wahl («vorschau» oder «voll») gilt;
 * fehlt sie oder ist sie unbekannt, die Vorgabe der Art (`GUETE_VORGABE_JE_ART`). Bis Entscheid 143
 * war alles ausser ausdruecklich «voll» Vorschau — darum kein Standardwert fuer `art`: wer fragt,
 * sagt, wofuer.
 */
export function gueteAmKnoten(params: Record<string, unknown> | undefined, art: GueteArt): Guete {
  const g = params?.[GUETE_PARAM];
  return g === 'vorschau' || g === 'voll' ? g : GUETE_VORGABE_JE_ART[art];
}

/** Was die zwei Stufen heissen und was sie tun — die Kurzhilfe am Schalter. Die Zeiten sind die der
 *  Visbox-Messung 346 am Testhaus (eine Kamera, 1600 × 1000, auf einer Grundlage): von «KI-Schritt»
 *  bis «fertig nach der Freigabe» — voll 33 bis 45 s, Vorschau 26 bis 36 s. Eine Spanne, keine
 *  Zusage; Warten auf die Grafikkarte ist nicht darin. */
export const GUETE_TEXTE: Record<Guete, { readonly name: string; readonly hinweis: string }> = {
  vorschau: {
    name: 'Vorschau',
    hinweis:
      'Vorschau: schneller (rund 26–36 s je Bild) — immer Z-Image Turbo, ein Startwert, weniger Schritte, kleineres KI-Bild, ohne das Grundbild als Bildeingang. Fenster und Form sind darum nicht gesichert. Wird geprüft; Bild und Verlauf tragen den Vermerk «Vorschau». Gefällt sie, rechnet «Voll» dieselbe Variante gross.',
  },
  voll: {
    name: 'Voll',
    hinweis:
      'Voll (Vorgabe für Varianten): das gewählte Bildwerkzeug in voller Grösse, vom Grundbild aus (Bildeingang 0,5, wo das Bildmodell ihn trägt) — hält Fenster und Form. Rund 33–45 s je Bild.',
  },
};

/** Vorerst: mit angehaengter Skizze rechnet der Heim-PC ohne Guete (Skizzen-Weg); die Owner-Frage
 *  dazu ist offen. Der Schalter steht dann grau mit diesem Satz, und es geht keine Guete hinaus. */
export const GUETE_OHNE_SKIZZE_SATZ = 'Vorschau gilt noch nicht für Skizzen';

/**
 * Die Guete, die ein Ergebnis meldet (`result.guete`), fuer den Lauf (`NodeLauf.guete`). Seit R40
 * (55fa86901) kennt der Vertrag das Feld; gelesen wird es trotzdem ohne den Vertragstyp, damit ein
 * unbekannter Wert nie als Vorschau gilt — fehlt oder unbekannt = voll, nie eine geratene Vorschau.
 */
export function gueteAusErgebnis(r: unknown): Guete | undefined {
  const g = typeof r === 'object' && r !== null ? (r as { guete?: unknown }).guete : undefined;
  return g === 'vorschau' || g === 'voll' ? g : undefined;
}
