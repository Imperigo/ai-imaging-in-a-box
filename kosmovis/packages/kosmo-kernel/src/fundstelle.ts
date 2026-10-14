/**
 * B164 P72 (I3, Entscheid 13, `docs/V016-SPEZ.md` §14b) — Fundstellen-Modell:
 * jede erfasste Zahl traegt eine Fundstelle {dokumentId, seite, stelle,
 * auszug}; ohne Fundstelle gilt sie als Annahme, nie als Tatsache.
 *
 * Schnittstelle abgestimmt mit dem UI-Worker
 * (`auftraege/ergebnisse/erg-20260924-ui-an-integrator-b164-abstimmung.md`,
 * gespiegelt in `apps/kosmo-orbit/src/modules/prepare/baum/prepare-baum-typen.ts`)
 * und mit der Prepare-Engine
 * (`auftraege/ergebnisse/erg-20260924-b164-prepare.md`, P1/P2): die Engine
 * liefert `herkunft` (`dokument` · `vorlage` · `gezaehlt` · `auszug` ·
 * `fehlt`) und `annahme` (wahr, wenn keine Fundstelle) zu jedem Wert — beide
 * Felder stehen hier, auch wenn `ErfassteZahl` im UI-Vertrag heute nur
 * `fundstelle` fuehrt (Abweichung gemeldet, s. Ergebnis-Blatt dieses Pakets).
 *
 * NICHT Teil von P72: das Berechnen eines Werts aus dem Programm (I5/M3,
 * v0.1.6, `docs/AUFTRAG-B164-PREPARE-PAKET-WETTBEWERBS-VORBEREITUNG.md`
 * §8 L4). P72 nimmt nur den Platz dafuer auf.
 */

/** P72, Entscheid 13 — ohne Fundstelle gilt eine Zahl als Annahme. */
export interface Fundstelle {
  dokumentId: string;
  seite: number | null;
  stelle: string;
  auszug: string;
}

/**
 * Woher ein erfasster Wert stammt (Prepare-Engine, P1/P2 `erg-20260924-b164-prepare.md`):
 * `dokument` — woertlich aus einer Unterlage gelesen.
 * `vorlage` — eingebauter Richtwert der Kosmo-Vorlage (Entscheid 17), keine Fundstelle.
 * `gezaehlt` — aus anderen erfassten Werten abgeleitet/gezaehlt.
 * `auszug` — aus einem Auszug/Zitat entnommen, ohne eigene Fundstelle-Stelle.
 * `fehlt` — nichts erfasst; der Wert ist ein Platzhalter.
 *
 * Bewusst NICHT `Herkunft` genannt — `model/entities.ts` traegt bereits ein
 * `Herkunft { art, beleg }` fuer Baustandard-Belege (Owner-Entscheid/
 * Lehrheft/Hersteller/Branchenkatalog), ein anderes Konzept mit anderer
 * Form. Ein gleicher Name haette den Export in `index.ts` zweideutig
 * gemacht (`export *` beider Module).
 */
export type WertHerkunft = 'dokument' | 'vorlage' | 'gezaehlt' | 'auszug' | 'fehlt';

/**
 * Ein erfasster Wert mit Quellenpflicht (Entscheid 13). `annahme` folgt
 * IMMER aus `fundstelle`: `annahme === (fundstelle === null)`. Es gibt
 * bewusst keinen Weg, `annahme: false` ohne Fundstelle zu erzeugen —
 * `erfassterWert()` ist die einzige vorgesehene Bauweise.
 */
export interface ErfassterWert {
  wert: number;
  einheit: string;
  fundstelle: Fundstelle | null;
  herkunft: WertHerkunft;
  /** `true`, wenn `fundstelle === null` — nie als Tatsache angezeigt (Entscheid 13). */
  annahme: boolean;
}

/**
 * Baut einen `ErfassterWert` und leitet `annahme` aus `fundstelle` ab —
 * der einzige vorgesehene Weg, damit die beiden Felder nie auseinanderlaufen.
 */
export function erfassterWert(eingang: {
  wert: number;
  einheit: string;
  herkunft: WertHerkunft;
  fundstelle?: Fundstelle | null;
}): ErfassterWert {
  const fundstelle = eingang.fundstelle ?? null;
  return {
    wert: eingang.wert,
    einheit: eingang.einheit,
    herkunft: eingang.herkunft,
    fundstelle,
    annahme: fundstelle === null,
  };
}

/** Entscheid 13, wörtlich: ohne Fundstelle gilt ein Wert nie als Tatsache. */
export function istTatsache(w: Pick<ErfassterWert, 'annahme'>): boolean {
  return !w.annahme;
}

/** «6 400 m²» — Schweizer Tausender mit schmalem Leerschlag, Einheit dahinter.
 *  Gleiche Form wie `apps/kosmo-orbit/src/modules/prepare/baum/prepare-baum-typen.ts`
 *  `zahlText`, hier auf `ErfassterWert` — bewusst dupliziert statt importiert,
 *  s. Kopfkommentar der App-Datei («Bruecke, nicht Wahrheit»). */
export function zahlText(w: Pick<ErfassterWert, 'wert' | 'einheit'>): string {
  const t = new Intl.NumberFormat('de-CH', { maximumFractionDigits: 2 }).format(w.wert).replace(/[’']/g, ' ');
  return w.einheit ? `${t} ${w.einheit}` : t;
}

/** «Seite 4, Frage 14» — die Stelle so, wie ein Mensch sie sucht. */
export function stelleText(f: Fundstelle): string {
  return [f.seite !== null ? `Seite ${f.seite}` : null, f.stelle || null].filter(Boolean).join(', ');
}
